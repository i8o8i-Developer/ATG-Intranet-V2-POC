import React, { useEffect, useMemo, useState } from "react";
import { ArrowDown, ArrowLeft, ArrowUp, Globe, Mail, MoreHorizontal, PhoneCall, Plus, RefreshCw, Save, Search, Star, Trash2, Users } from "lucide-react";

import { apiPatch, apiPost } from "../Api/Client.js";
import { EmptyState, Modal, StatusPill } from "./Shared/ScreenComponents.jsx";
import "../Styles/LmsScreen.css";
import {
  formatDate,
  formatDateTime,
  getLeadRows,
  leadContactSummary,
  leadOwnerName,
  leadSourceCards,
  leadSource,
  leadStage,
  priorityTone,
  sourceTone,
  toggleSet,
  uniqueOptions,
} from "./Shared/ScreenUtils.jsx";

const SORT_FIELDS = {
  leadName: (row) => String(row.leadName || "").toLowerCase(),
  companyName: (row) => String(row.companyName || "").toLowerCase(),
  notesCount: (row) => Number(row.notesCount || 0),
  createdAt: (row) => new Date(row.createdAt || 0).getTime(),
  updatedAt: (row) => new Date(row.updatedAt || 0).getTime(),
};

const CALL_STATUS_OPTIONS = [
  ["", "Call Status"],
  ["call_failed", "Call Failed"],
  ["call_connected", "Call Connected"],
  ["call_didnot_pickup", "Call Didn't Pickup"],
];

const NOTE_CHANNELS = [
  { key: "meeting", label: "Meeting", placeholder: "Meeting Recorder Link", options: [["", "Meeting Recorder Link"], ["google_meet", "Google Meet"], ["zoom", "Zoom"], ["microsoft_teams", "Microsoft Teams"], ["other", "Other"]] },
  { key: "call", label: "Phone Call", placeholder: "Call Status", options: CALL_STATUS_OPTIONS },
  { key: "email", label: "Email", placeholder: "Email Status", options: [["", "Email Status"], ["EmailSent", "Email Sent"], ["Email Delivered", "Email Delivered"], ["Email Opened", "Email Opened"], ["Link Clicked", "Link Clicked"], ["Replied", "Replied"], ["Bounced", "Bounced"], ["Pending", "Pending"]] },
  { key: "whatsapp", label: "Whatsapp", placeholder: "Whatsapp Status", options: [["", "Whatsapp Status"], ["MessageSent", "Message Sent"], ["Message Delivered", "Message Delivered"], ["Message Read", "Message Read"], ["Lead Replied", "Lead Replied"], ["CallInitiated(ViaWhatsappCall)", "Call Initiated (Via Whatsapp Call)"], ["NotDelivered / Blocked", "Not Delivered / Blocked"]] },
  { key: "linkedin", label: "LinkedIn", placeholder: "LinkedIn Status", options: [["", "LinkedIn Status"], ["ConnectionRequestSent", "Connection Request Sent"], ["Request Pending", "Request Pending"], ["Connected", "Connected"], ["Message Sent", "Message Sent"], ["Message Seen", "Message Seen"], ["Lead Replied", "Lead Replied"], ["ProfileUnavailable / Restricted", "Profile Unavailable / Restricted"], ["Follow-UpScheduled", "Follow-Up Scheduled"]] },
];

function stageTone(value = "") {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("won") || normalized.includes("confirmed")) return "green";
  if (normalized.includes("proposal") || normalized.includes("discovery") || normalized.includes("demo")) return "gold";
  if (normalized.includes("lost") || normalized.includes("negative")) return "red";
  return "slate";
}

function sourceLogoNode(label = "") {
  const tone = sourceTone(label);
  if (tone === "client") return <Globe size={16} />;
  if (tone === "linkedin") return <Users size={16} />;
  if (tone === "instagram") return <span>IG</span>;
  if (tone === "banao") return <span>B</span>;
  return <span>{String(label || "?").slice(0, 2).toUpperCase()}</span>;
}

function compareRows(left, right, field, direction) {
  const getValue = SORT_FIELDS[field] || SORT_FIELDS.createdAt;
  const leftValue = getValue(left);
  const rightValue = getValue(right);
  if (leftValue === rightValue) return 0;
  return (leftValue > rightValue ? 1 : -1) * (direction === "asc" ? 1 : -1);
}

function routeLeadId(route = "") {
  const path = String(route || "").split("?")[0];
  const match = path.match(/^\/lms\/([^/]+)\/?$/);
  return match ? match[1] : "";
}

function toDateInput(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toISOString().slice(0, 10);
}

function toDateTimePayload(value) {
  return value ? `${value}T00:00:00` : null;
}

function tagIdsForLead(tags = [], options = []) {
  const byName = new Map(options.map((item) => [String(item.name), String(item.id)]));
  return (tags || []).map((item) => {
    if (item && typeof item === "object" && item.id !== undefined) return String(item.id);
    const text = String(item);
    return byName.get(text) || text;
  });
}

function payloadIds(values = []) {
  return values.map((value) => {
    const number = Number(value);
    return Number.isNaN(number) ? value : number;
  });
}

function parseChecklist(value = "") {
  return String(value || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => ({
      id: `task-${index}-${line}`,
      done: /^\[(x|X)\]\s*/.test(line),
      label: line.replace(/^\[(x|X| )\]\s*/, "").trim(),
    }));
}

function serializeChecklist(items = []) {
  return (items || [])
    .filter((item) => String(item.label || "").trim())
    .map((item) => `[${item.done ? "x" : " "}] ${String(item.label || "").trim()}`)
    .join("\n");
}

function currentEmployeeId(data) {
  return String(data.me?.employees?.[0]?.id || (data.employees || []).find((item) => String(item.user) === String(data.me?.user?.id))?.id || "");
}

function leadTypeLabel(lead) {
  return lead.metadata?.lead_type || lead.metadata?.type || lead.metadata?.service_type || "Not Gathered";
}

function buildLeadDraft(lead, tagOptions) {
  return {
    stageLabel: lead.stageLabel || "New Lead",
    ownerId: String(lead.ownerId || ""),
    tagIds: tagIdsForLead(lead.tags || [], tagOptions),
    nextFollowUpAt: toDateInput(lead.nextFollowUpAt),
    lastUpdateNote: lead.lastUpdateNote === "-" ? "" : lead.lastUpdateNote,
    callStatus: lead.callStatus || "",
    callUpdatedAt: toDateInput(lead.callUpdatedAt),
    important: Boolean(lead.important),
    checklist: parseChecklist(lead.actionItem),
    message: lead.message === "-" ? "" : lead.message,
    typeLabel: lead.typeLabel || "Not Gathered",
  };
}

function buildLeadPayload(lead, draft) {
  return {
    owner: draft.ownerId || null,
    stage: draft.stageLabel || lead.stageLabel || "New Lead",
    tags: payloadIds(draft.tagIds),
    next_follow_up_at: toDateTimePayload(draft.nextFollowUpAt),
    latest_comment: draft.lastUpdateNote || "",
    action_item: serializeChecklist(draft.checklist),
    metadata: {
      ...(lead.metadata || {}),
      call_status: draft.callStatus || "",
      call_updated_at: draft.callUpdatedAt || null,
      is_important: draft.important,
      source_message: draft.message || "",
      lead_type: draft.typeLabel || "",
    },
  };
}

export function LmsScreen({ data, reload, navigate, route }) {
  const rawLeads = getLeadRows(data);
  const [search, setSearch] = useState("");
  const [tag, setTag] = useState("all");
  const [priority, setPriority] = useState("all");
  const [owner, setOwner] = useState("all");
  const [stage, setStage] = useState("all");
  const [source, setSource] = useState("all");
  const [moreFilter, setMoreFilter] = useState("all");
  const [sortField, setSortField] = useState("createdAt");
  const [sortDirection, setSortDirection] = useState("desc");
  const [selected, setSelected] = useState(new Set());
  const [assignOpen, setAssignOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [addLeadOpen, setAddLeadOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const activeLeadId = routeLeadId(route);

  const refresh = () => reload(["lmsLeads", "leadAccounts", "leadContacts", "leadNotes", "leadProposals", "leadAudits", "leadActivities", "leadTags", "employees", "learningAssignments", "leadQueueSnapshots", "revenueSnapshots"]);

  const leads = useMemo(() => {
    const accountMap = new Map((data.leadAccounts || []).map((item) => [String(item.id), item]));
    const contactsByLead = new Map();
    (data.leadContacts || []).forEach((item) => {
      const key = String(item.lead);
      if (!contactsByLead.has(key)) contactsByLead.set(key, []);
      contactsByLead.get(key).push(item);
    });
    const notesByLead = new Map();
    (data.leadNotes || []).forEach((item) => {
      const key = String(item.lead);
      if (!notesByLead.has(key)) notesByLead.set(key, []);
      notesByLead.get(key).push(item);
    });
    const proposalsByLead = new Map();
    (data.leadProposals || []).forEach((item) => {
      const key = String(item.lead);
      if (!proposalsByLead.has(key)) proposalsByLead.set(key, []);
      proposalsByLead.get(key).push(item);
    });
    const auditsByLead = new Map();
    (data.leadAudits || []).forEach((item) => {
      const key = String(item.lead);
      if (!auditsByLead.has(key)) auditsByLead.set(key, []);
      auditsByLead.get(key).push(item);
    });

    return rawLeads.map((row) => {
      const account = accountMap.get(String(row.id)) || row;
      const contacts = contactsByLead.get(String(row.id)) || [];
      const primaryContact = contacts.find((item) => item.is_primary) || contacts[0] || {};
      const notes = [...(notesByLead.get(String(row.id)) || [])].sort((left, right) => new Date(right.created_at || right.updated_at || 0) - new Date(left.created_at || left.updated_at || 0));
      const latestNote = notes[0] || null;
      const tags = account.tags || row.tags || [];
      const sourceLabel = leadSource(account);
      const ownerId = row.owner_id || account.owner || row.owner;
      const metadata = account.metadata || {};
      const proposals = proposalsByLead.get(String(row.id)) || [];
      const audits = auditsByLead.get(String(row.id)) || [];

      return {
        id: row.id,
        leadName: account.metadata?.full_name || account.metadata?.contact_name || primaryContact.name || account.company_name || row.company_name || "-",
        companyName: account.company_name || row.company_name || "-",
        sourceLabel,
        stageLabel: leadStage(account),
        notesCount: row.notes_count ?? notes.length,
        ownerId: ownerId ? String(ownerId) : "",
        ownerName: row.owner_name || leadOwnerName(data, { owner_id: ownerId, owner_name: row.owner_name }) || "-",
        priority: row.priority || account.priority || "Normal",
        email: leadContactSummary(data, account, "email") || primaryContact.email || account.metadata?.email || account.metadata?.contact_email || "-",
        phone: leadContactSummary(data, account, "phone") || primaryContact.phone || account.metadata?.phone || account.metadata?.contact_phone || "-",
        createdAt: account.created_at || row.created_at || null,
        updatedAt: account.updated_at || row.updated_at || null,
        nextFollowUpAt: account.next_follow_up_at || row.next_follow_up_at || null,
        lastUpdateNote: account.latest_comment || latestNote?.title || latestNote?.body || "-",
        industry: account.industry || "-",
        tagNames: tags.map((item) => String(item.name || item)),
        actionItem: account.action_item || "",
        tagIds: tagIdsForLead(tags, data.leadTags || []),
        tags,
        account,
        contacts,
        notes,
        proposals,
        audits,
        metadata,
        websiteUrl: account.website_url || account.source_page_url || metadata.website_url || "",
        callStatus: metadata.call_status || "",
        callUpdatedAt: metadata.call_updated_at || null,
        important: Boolean(metadata.is_important),
        typeLabel: leadTypeLabel({ metadata }),
        message: metadata.source_message || metadata.message || metadata.lead_message || latestNote?.body || "-",
      };
    });
  }, [rawLeads, data.leadAccounts, data.leadContacts, data.leadNotes, data.leadProposals, data.leadAudits, data]);

  const assignSelected = async (employeeId) => {
    if (!employeeId || !selected.size) return;
    setBusy(true);
    try {
      await Promise.all(Array.from(selected).map((leadId) => apiPatch(`/Banao/LeadAccounts/${leadId}/`, { owner: employeeId })));
      setSelected(new Set());
      refresh();
      setAssignOpen(false);
    } finally {
      setBusy(false);
    }
  };

  const bulkMoveStage = async (toStage) => {
    if (!toStage || !selected.size) return;
    setBusy(true);
    try {
      await Promise.all(Array.from(selected).map((leadId) => apiPost(`/Banao/LeadAccounts/${leadId}/move-stage/`, { to_stage: toStage, reason: "Bulk Update" })));
      setSelected(new Set());
      refresh();
      setMoreOpen(false);
    } finally {
      setBusy(false);
    }
  };

  const addLead = async (formData) => {
    if (!formData.company_name?.trim()) {
      alert("Company Name Is Required");
      return;
    }
    setBusy(true);
    try {
      await apiPost("/Banao/LeadAccounts/capture/", formData);
      refresh();
      setAddLeadOpen(false);
    } catch (error) {
      alert(error?.data?.detail || error?.message || "Unable To Create Lead.");
    } finally {
      setBusy(false);
    }
  };

  const filtered = useMemo(() => leads.filter((lead) => {
    const term = `${lead.leadName} ${lead.companyName} ${lead.sourceLabel} ${lead.ownerName} ${lead.email} ${lead.phone} ${lead.lastUpdateNote}`.toLowerCase();
    const followUpAt = lead.nextFollowUpAt ? new Date(lead.nextFollowUpAt) : null;
    const isOverdue = followUpAt && followUpAt < new Date();
    const followUpMatches = moreFilter === "all"
      || (moreFilter === "scheduled" && Boolean(followUpAt))
      || (moreFilter === "missing" && !followUpAt)
      || (moreFilter === "overdue" && Boolean(isOverdue))
      || (moreFilter === "action" && Boolean(String(lead.actionItem || "").trim()));
    return (!search || term.includes(search.toLowerCase()))
      && (tag === "all" || lead.tagNames.includes(tag))
      && (priority === "all" || String(lead.priority) === priority)
      && (owner === "all" || String(lead.ownerId || "") === owner)
      && (stage === "all" || lead.stageLabel === stage)
      && (source === "all" || lead.sourceLabel === source)
      && followUpMatches;
  }).sort((left, right) => compareRows(left, right, sortField, sortDirection)), [leads, search, tag, priority, owner, stage, source, moreFilter, sortField, sortDirection]);

  const sourceCards = useMemo(() => leadSourceCards(data, leads), [data, leads]);
  const stageOptions = useMemo(() => uniqueOptions(["New Lead", "Contact Attempted", "Discovery / Demo Scheduled", "Discovery / Demo Completed", "Proposal Sent", "Closed - Won", "Closed - Lost", "Nurture / Recycle", ...leads.map((lead) => lead.stageLabel)]), [leads]);
  const selectedVisibleCount = filtered.filter((lead) => selected.has(lead.id)).length;
  const allVisibleSelected = filtered.length > 0 && filtered.every((lead) => selected.has(lead.id));
  const activeLead = activeLeadId ? leads.find((lead) => String(lead.id) === String(activeLeadId)) : null;

  const resetFilters = () => {
    setSearch("");
    setTag("all");
    setPriority("all");
    setOwner("all");
    setStage("all");
    setSource("all");
    setMoreFilter("all");
    setSelected(new Set());
    setSortField("createdAt");
    setSortDirection("desc");
  };

  const toggleAllVisible = () => {
    const next = new Set(selected);
    if (allVisibleSelected) {
      filtered.forEach((lead) => next.delete(lead.id));
    } else {
      filtered.forEach((lead) => next.add(lead.id));
    }
    setSelected(next);
  };

  const toggleSort = (field) => {
    if (sortField === field) {
      setSortDirection((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSortField(field);
    setSortDirection(field === "leadName" ? "asc" : "desc");
  };

  const renderSortIcon = (field) => {
    if (sortField !== field) return null;
    return sortDirection === "asc" ? <ArrowUp size={13} /> : <ArrowDown size={13} />;
  };

  if (activeLeadId && !activeLead) {
    return (
      <section className="Lms-Screen Lms-Detail-Screen">
        <div className="Lms-Breadcrumb">
          <strong>Intranet</strong>
          <button onClick={() => navigate?.("/home/")}>Home</button>
          <span>/</span>
          <button onClick={() => navigate?.("/lms/")}>Banao</button>
          <span>/</span>
          <b>{activeLeadId}</b>
        </div>
        <section className="Lms-Detail-Shell">
          <div className="Lms-Detail-Topbar">
            <button className="Outline-Button" onClick={() => navigate?.("/lms/")}><ArrowLeft size={16} /> Back To Leads</button>
            <button className="Outline-Button" onClick={refresh}><RefreshCw size={16} /> Refresh</button>
          </div>
          <EmptyState label="Lead Not Found In The Current Workspace." />
        </section>
      </section>
    );
  }

  if (activeLead) {
    return <LeadDetailWorkspace data={data} lead={activeLead} navigate={navigate} refresh={refresh} stageOptions={stageOptions} />;
  }

  return (
    <section className="Lms-Screen">
      <div className="Lms-Breadcrumb">
        <strong>Intranet</strong>
        <button onClick={() => navigate?.("/home/")}>Home</button>
        <span>/</span>
        <button onClick={() => navigate?.("/lms/")}>Banao</button>
        <span>/</span>
        <b>LMS</b>
      </div>

      <h1>Lead Overview</h1>
      <section className="Lms-Source-Strip">
        {sourceCards.map((card) => (
          <button key={card.label} className={source === card.label ? "active" : ""} onClick={() => setSource(source === card.label ? "all" : card.label)}>
            <span className={`source-logo ${card.tone}`}>{sourceLogoNode(card.label)}</span>
            <strong>{card.count}</strong>
            <small>{card.label}</small>
          </button>
        ))}
        {!sourceCards.length && <EmptyState label="No Lead Sources Returned." />}
      </section>

      <div className="Lms-Search-Row">
        <div className="Lms-Search">
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search Name" />
          <Search size={18} />
        </div>
      </div>

      <section className="Lms-Leads-Panel">
        <header>
          <div>
            <h2>Leads <span>{selectedVisibleCount} of {filtered.length} Selected</span></h2>
          </div>
          <button className="Icon-Button" title="Reset Filters" onClick={resetFilters}>
            <RefreshCw size={18} />
          </button>
        </header>

        <div className="Lead-Tools">
          <button className="Icon-Action" title="Add Lead" onClick={() => setAddLeadOpen(true)}><Plus size={16} /></button>
          <button className="Icon-Action" title="Bulk Move Stage" onClick={() => setMoreOpen(true)} disabled={!selected.size}><MoreHorizontal size={16} /></button>
          <button className="Icon-Action" title="Clear Selection" onClick={() => setSelected(new Set())} disabled={!selected.size}><Trash2 size={16} /></button>
          <button className="Icon-Action" title="Assign Selected" onClick={() => setAssignOpen(true)} disabled={!selected.size}><Users size={16} /></button>
        </div>

        <div className="Lms-Filters">
          <select value={tag} onChange={(event) => setTag(event.target.value)}>
            <option value="all">By Tags</option>
            {(data.leadTags || []).map((item) => <option key={item.id} value={item.name}>{item.name}</option>)}
          </select>
          <select value={priority} onChange={(event) => setPriority(event.target.value)}>
            <option value="all">By Mark Imp</option>
            {uniqueOptions(leads.map((lead) => lead.priority)).map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
          <select value={owner} onChange={(event) => setOwner(event.target.value)}>
            <option value="all">By Assigned To</option>
            {(data.employees || []).map((employee) => <option key={employee.id} value={employee.id}>{employee.display_name}</option>)}
          </select>
          <select value={stage} onChange={(event) => setStage(event.target.value)}>
            <option value="all">By Workflow Status</option>
            {stageOptions.map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
          <select value={source} onChange={(event) => setSource(event.target.value)}>
            <option value="all">By Lead Origin</option>
            {uniqueOptions(leads.map((lead) => lead.sourceLabel)).map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
          <select value={moreFilter} onChange={(event) => setMoreFilter(event.target.value)}>
            <option value="all">More Filters</option>
            <option value="scheduled">Has Follow Up</option>
            <option value="missing">No Follow Up</option>
            <option value="overdue">Overdue Follow Up</option>
            <option value="action">Action Pending</option>
          </select>
        </div>

        <div className="Lead-Table-Scroll">
          <table className="Erp-Table Lms-Lead-Table">
            <thead>
              <tr>
                <th><input type="checkbox" checked={allVisibleSelected} onChange={toggleAllVisible} aria-label="Select All Visible Leads" /></th>
                <th>
                  <button className="Lms-Sort-Head" onClick={() => toggleSort("leadName")}>Lead / Client Name {renderSortIcon("leadName")}</button>
                </th>
                <th>Origin</th>
                <th>Workflow Status</th>
                <th>
                  <button className="Lms-Sort-Head" onClick={() => toggleSort("notesCount")}>Lead Note Count {renderSortIcon("notesCount")}</button>
                </th>
                <th>
                  <button className="Lms-Sort-Head" onClick={() => toggleSort("companyName")}>Company Name {renderSortIcon("companyName")}</button>
                </th>
                <th>Email</th>
                <th>Phone Nos</th>
                <th>Assigned To</th>
                <th>
                  <button className="Lms-Sort-Head" onClick={() => toggleSort("createdAt")}>Created At {renderSortIcon("createdAt")}</button>
                </th>
                <th>Last Update Note</th>
                <th>
                  <button className="Lms-Sort-Head" onClick={() => toggleSort("updatedAt")}>Last Updated {renderSortIcon("updatedAt")}</button>
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((lead) => (
                <tr key={lead.id}>
                  <td><input type="checkbox" checked={selected.has(lead.id)} onChange={() => setSelected(toggleSet(selected, lead.id))} aria-label={`Select ${lead.leadName}`} /></td>
                  <td>
                    <div className="Lms-Row-Name">
                      <button className="Lms-Lead-Open" onClick={() => navigate?.(`/lms/${lead.id}/`)}>
                        <strong>{lead.leadName}</strong>
                      </button>
                      <StatusPill tone={priorityTone(lead.priority)}>{lead.priority || "Normal"}</StatusPill>
                    </div>
                  </td>
                  <td>
                    <span className={`lms-origin-icon ${sourceTone(lead.sourceLabel)}`} title={lead.sourceLabel}>{sourceLogoNode(lead.sourceLabel)}</span>
                  </td>
                  <td><span className={`lms-stage-chip ${stageTone(lead.stageLabel)}`}>{lead.stageLabel}</span></td>
                  <td>{lead.notesCount ? lead.notesCount : "N/A"}</td>
                  <td>{lead.companyName || "-"}</td>
                  <td>{lead.email || "-"}</td>
                  <td>{lead.phone || "-"}</td>
                  <td>{lead.ownerName || "-"}</td>
                  <td>{formatDate(lead.createdAt)}</td>
                  <td className="Lms-Last-Note">{lead.lastUpdateNote || "-"}</td>
                  <td>{formatDate(lead.updatedAt)}</td>
                </tr>
              ))}
              {!filtered.length && (
                <tr>
                  <td colSpan={12}>
                    <div className="Lms-Empty-Wrap"><EmptyState label="No Leads Match The Current Filters." /></div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {addLeadOpen && <AddLeadModal data={data} sources={sourceCards} busy={busy} onClose={() => setAddLeadOpen(false)} onSubmit={addLead} />}
      {assignOpen && <AssignLeadModal data={data} count={selected.size} busy={busy} onClose={() => setAssignOpen(false)} onSubmit={assignSelected} />}
      {moreOpen && <BulkStageModal count={selected.size} busy={busy} options={stageOptions} onClose={() => setMoreOpen(false)} onSubmit={bulkMoveStage} />}
    </section>
  );
}

function LeadDetailWorkspace({ data, lead, navigate, refresh, stageOptions }) {
  const [draft, setDraft] = useState(() => buildLeadDraft(lead, data.leadTags || []));
  const [checklistInput, setChecklistInput] = useState("");
  const [note, setNote] = useState(() => ({ title: "", body: "", channelEnabled: { meeting: false, call: false, email: false, whatsapp: false, linkedin: false }, channelStatus: { meeting: "", call: "", email: "", whatsapp: "", linkedin: "" } }));
  const [saving, setSaving] = useState(false);
  const [noteBusy, setNoteBusy] = useState(false);
  const [flash, setFlash] = useState("");
  const actorId = currentEmployeeId(data);

  useEffect(() => {
    setDraft(buildLeadDraft(lead, data.leadTags || []));
    setChecklistInput("");
    setNote({ title: "", body: "", channelEnabled: { meeting: false, call: false, email: false, whatsapp: false, linkedin: false }, channelStatus: { meeting: "", call: "", email: "", whatsapp: "", linkedin: "" } });
    setFlash("");
  }, [lead, data.leadTags]);

  const saveLead = async (nextDraft = draft, successMessage = "Lead Updated.") => {
    setSaving(true);
    try {
      await apiPatch(`/Banao/LeadAccounts/${lead.id}/`, buildLeadPayload(lead, nextDraft));
      setDraft(nextDraft);
      setFlash(successMessage);
      refresh();
    } catch (error) {
      setFlash(error?.data?.detail || error?.message || "Unable To Save Lead Details.");
    } finally {
      setSaving(false);
    }
  };

  const updateChecklist = async (nextChecklist, message) => {
    const nextDraft = { ...draft, checklist: nextChecklist };
    setDraft(nextDraft);
    await saveLead(nextDraft, message);
  };

  const addChecklistItem = async () => {
    const label = checklistInput.trim();
    if (!label) return;
    const nextChecklist = [...draft.checklist, { id: `task-${Date.now()}`, label, done: false }];
    setChecklistInput("");
    await updateChecklist(nextChecklist, "Checklist Updated.");
  };

  const submitNote = async () => {
    if (!note.body.trim()) {
      setFlash("Add A Note Description Before Saving.");
      return;
    }
    setNoteBusy(true);
    try {
      const channelStatus = Object.fromEntries(Object.entries(note.channelStatus).filter(([, value]) => value));
      const enabledChannels = Object.entries(note.channelEnabled).filter(([, value]) => value).map(([key]) => key);
      const nextDraft = { ...draft, lastUpdateNote: note.title.trim() ? `${note.title.trim()}: ${note.body.trim()}` : note.body.trim() };
      await apiPost(`/Banao/LeadAccounts/${lead.id}/add-note/`, {
        title: note.title.trim() || "General Update",
        body: note.body.trim(),
        author: actorId || undefined,
        metadata: {
          channels: enabledChannels,
          channel_status: channelStatus,
          call_status: draft.callStatus || "",
          call_updated_at: draft.callUpdatedAt || null,
          next_follow_up_at: toDateTimePayload(draft.nextFollowUpAt),
        },
      });
      await apiPatch(`/Banao/LeadAccounts/${lead.id}/`, buildLeadPayload(lead, nextDraft));
      setDraft(nextDraft);
      setNote({ title: "", body: "", channelEnabled: { meeting: false, call: false, email: false, whatsapp: false, linkedin: false }, channelStatus: { meeting: "", call: "", email: "", whatsapp: "", linkedin: "" } });
      setFlash("Note Added.");
      refresh();
    } catch (error) {
      setFlash(error?.data?.detail || error?.message || "Unable To Save Note.");
    } finally {
      setNoteBusy(false);
    }
  };

  const latestProposal = lead.proposals[0];
  const latestAudit = lead.audits[0];

  return (
    <section className="Lms-Screen Lms-Detail-Screen">
      <div className="Lms-Breadcrumb">
        <strong>Intranet</strong>
        <button onClick={() => navigate?.("/home/")}>Home</button>
        <span>/</span>
        <button onClick={() => navigate?.("/lms/")}>Banao</button>
        <span>/</span>
        <button onClick={() => navigate?.("/lms/")}>LMS</button>
        <span>/</span>
        <b>{lead.id}</b>
      </div>

      <section className="Lms-Detail-Shell">
        <div className="Lms-Detail-Topbar">
          <button className="Outline-Button" onClick={() => navigate?.("/lms/")}><ArrowLeft size={16} /> Back To Leads</button>
          <button className="Primary-Button" disabled={saving} onClick={() => saveLead()}><Save size={16} /> {saving ? "Saving…" : "Save Lead"}</button>
        </div>

        <header className="Lms-Detail-Header">
          <div className="Lms-Detail-Profile">
            <div className="Lms-Detail-Avatar">{String(lead.leadName || lead.companyName || "?").trim().charAt(0).toUpperCase() || "?"}</div>
            <div>
              <h1>{lead.leadName}</h1>
              <p>Origin <span className={`lms-origin-inline ${sourceTone(lead.sourceLabel)}`}>{sourceLogoNode(lead.sourceLabel)}</span> {lead.sourceLabel}</p>
              <small>Created At: {formatDate(lead.createdAt)} | Updated At: {formatDate(lead.updatedAt)}</small>
            </div>
          </div>
          <div className="Lms-Detail-Actions">
            <button className={draft.important ? "Lms-Detail-ActionActive" : "Lms-Detail-Action"} onClick={() => saveLead({ ...draft, important: !draft.important }, draft.important ? "Lead Unmarked As Important." : "Lead Marked As Important.")}><Star size={17} /> <span>Mark As Important</span></button>
            <a className="Lms-Detail-Action" href={lead.email && lead.email !== "-" ? `mailto:${lead.email}` : undefined} onClick={(event) => { if (!lead.email || lead.email === "-") event.preventDefault(); }}><Mail size={17} /> <span>Email</span></a>
            <a className="Lms-Detail-Action" href={lead.phone && lead.phone !== "-" ? `tel:${String(lead.phone).replace(/\s+/g, "")}` : undefined} onClick={(event) => { if (!lead.phone || lead.phone === "-") event.preventDefault(); }}><PhoneCall size={17} /> <span>Call</span></a>
          </div>
        </header>

        <section className="Lms-Detail-Tags-Strip">
          <strong>Tags:</strong>
          <div className="Lms-Detail-Tags">
            {draft.tagIds.length ? draft.tagIds.map((id) => <span key={id} className="Lms-Tag-Chip">{(data.leadTags || []).find((item) => String(item.id) === String(id))?.name || id}</span>) : <span className="Lms-Muted">No Tags Assigned</span>}
          </div>
        </section>

        {flash && <div className="Lms-Flash">{flash}</div>}

        <div className="Lms-Detail-Form-Row">
          <label className="Lms-Field-Stack">Call Updated At
            <input type="date" value={draft.callUpdatedAt} onChange={(event) => setDraft({ ...draft, callUpdatedAt: event.target.value })} />
          </label>
          <label className="Lms-Field-Stack">Workflow Status
            <select value={draft.stageLabel} onChange={(event) => setDraft({ ...draft, stageLabel: event.target.value })}>
              {stageOptions.map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
          </label>
          <label className="Lms-Field-Stack">Call Status
            <select value={draft.callStatus} onChange={(event) => setDraft({ ...draft, callStatus: event.target.value })}>
              {CALL_STATUS_OPTIONS.map(([value, label]) => <option key={value || "blank"} value={value}>{label}</option>)}
            </select>
          </label>
          <label className="Lms-Field-Stack">Assigned To
            <select value={draft.ownerId} onChange={(event) => setDraft({ ...draft, ownerId: event.target.value })}>
              <option value="">No One Assigned</option>
              {(data.employees || []).map((employee) => <option key={employee.id} value={employee.id}>{employee.display_name}</option>)}
            </select>
          </label>
          <label className="Lms-Field-Stack">Tags
            <select multiple value={draft.tagIds} onChange={(event) => setDraft({ ...draft, tagIds: Array.from(event.target.selectedOptions).map((option) => option.value) })}>
              {(data.leadTags || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
            <small>Press Ctrl + Click</small>
          </label>
        </div>

        <div className="Lms-Detail-Grid">
          <section className="Lms-Detail-Card Lms-Detail-Main">
            <h3>Add New Note</h3>
            <div className="Lms-Note-Editor">
              <input value={note.title} onChange={(event) => setNote({ ...note, title: event.target.value })} placeholder="Note Title (Call, Meeting, Objection, Negotiation, General Update)" />
              <textarea rows={6} value={note.body} onChange={(event) => setNote({ ...note, body: event.target.value })} placeholder="Note Description" />
              <div className="Lms-Note-Channels">
                {NOTE_CHANNELS.map((channel) => (
                  <div key={channel.key} className="Lms-Note-Channel">
                    <label><input type="checkbox" checked={note.channelEnabled[channel.key]} onChange={(event) => setNote({ ...note, channelEnabled: { ...note.channelEnabled, [channel.key]: event.target.checked } })} /> {channel.label}</label>
                    <select value={note.channelStatus[channel.key]} disabled={!note.channelEnabled[channel.key]} onChange={(event) => setNote({ ...note, channelStatus: { ...note.channelStatus, [channel.key]: event.target.value } })}>
                      {channel.options.map(([value, label]) => <option key={value || `${channel.key}-blank`} value={value}>{label}</option>)}
                    </select>
                  </div>
                ))}
              </div>
              <div className="Lms-Note-Footer">
                <div className="Lms-Field-Stack Compact">Next Follow Up
                  <input type="date" value={draft.nextFollowUpAt} onChange={(event) => setDraft({ ...draft, nextFollowUpAt: event.target.value })} />
                  <small>{draft.nextFollowUpAt ? formatDate(draft.nextFollowUpAt) : "Next Follow Up Date Not Set"}</small>
                </div>
                <button className="Primary-Button" disabled={noteBusy} onClick={submitNote}>{noteBusy ? "Saving…" : "Add Note"}</button>
              </div>
            </div>

            <div className="Lms-Note-Stream">
              {(lead.notes || []).map((item) => (
                <article key={item.id} className="Lms-Note-Card">
                  <header>
                    <strong>{item.title || "General Update"}</strong>
                    <span>{formatDateTime(item.created_at || item.updated_at)}</span>
                  </header>
                  <p>{item.body}</p>
                </article>
              ))}
              {!((lead.notes) || []).length && <EmptyState label="No Notes On This Lead Yet." />}
            </div>
          </section>

          <aside className="Lms-Detail-Card Lms-Detail-Side">
            <h3>Lead Information</h3>
            <div className="Lms-Info-Block">
              <label>Email</label>
              <p>{lead.email || "N/A"}</p>
              <label>Phone No.</label>
              <p>{lead.phone || "N/A"}</p>
              <label>URL</label>
              <p>{lead.websiteUrl ? <a href={lead.websiteUrl} target="_blank" rel="noreferrer">{lead.websiteUrl}</a> : "N/A"}</p>
            </div>

            <div className="Lms-Checklist-Card">
              <label>Action Checklist</label>
              <div className="Lms-Checklist-List">
                {draft.checklist.map((item) => (
                  <div key={item.id} className="Lms-Checklist-Row">
                    <label><input type="checkbox" checked={item.done} onChange={() => updateChecklist(draft.checklist.map((entry) => entry.id === item.id ? { ...entry, done: !entry.done } : entry), "Checklist Updated.")} /> {item.label}</label>
                    <button className="Icon-Action" onClick={() => updateChecklist(draft.checklist.filter((entry) => entry.id !== item.id), "Checklist Updated.")}><Trash2 size={14} /></button>
                  </div>
                ))}
                {!draft.checklist.length && <p className="Lms-Muted">No Tasks Yet.</p>}
              </div>
              <div className="Lms-Checklist-Input-Row">
                <input value={checklistInput} onChange={(event) => setChecklistInput(event.target.value)} placeholder="Add New Task..." />
                <button className="Primary-Button Small" onClick={addChecklistItem}><Plus size={14} /></button>
              </div>
            </div>

            <label>Messages</label>
            <textarea rows={4} value={draft.message} onChange={(event) => setDraft({ ...draft, message: event.target.value })} />

            <label>Type</label>
            <input value={draft.typeLabel} onChange={(event) => setDraft({ ...draft, typeLabel: event.target.value })} />

            <label>Origin</label>
            <p className="Lms-Readonly-Field">{lead.sourceLabel}</p>

            <label>Company Name</label>
            <p className="Lms-Readonly-Field">{lead.companyName}</p>

            <label>Industry</label>
            <p className="Lms-Readonly-Field">{lead.industry}</p>

            <label>Assigned To</label>
            <p className="Lms-Readonly-Field">{lead.ownerName}</p>

            <label>Latest Proposal</label>
            <p className="Lms-Readonly-Field">{latestProposal ? `${latestProposal.title || "Proposal"} · ${latestProposal.status || "Draft"}` : "N/A"}</p>

            <label>Latest Audit</label>
            <p className="Lms-Readonly-Field">{latestAudit ? `${latestAudit.title || "Audit"} · ${latestAudit.status || "Open"}` : "N/A"}</p>
          </aside>
        </div>
      </section>
    </section>
  );
}

function AddLeadModal({ data, sources, busy, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    company_name: "",
    contact_name: "",
    contact_email: "",
    contact_phone: "",
    source: "",
    priority: "Normal",
    owner: "",
    estimated_value: "",
    currency: "INR",
    metadata: {},
  });

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = () => {
    if (!formData.source.trim()) {
      alert("Origin Is Required");
      return;
    }
    const payload = {
      company_name: formData.company_name.trim(),
      source: formData.source.trim(),
      priority: formData.priority || "Normal",
      currency: formData.currency || "INR",
    };
    if (formData.contact_name.trim()) payload.contact_name = formData.contact_name.trim();
    if (formData.contact_email.trim()) payload.contact_email = formData.contact_email.trim();
    if (formData.contact_phone.trim()) payload.contact_phone = formData.contact_phone.trim();
    if (formData.owner) payload.owner = Number(formData.owner);
    if (formData.estimated_value) payload.estimated_value = Number(formData.estimated_value);
    onSubmit(payload);
  };

  return (
    <Modal title="Add New Lead" onClose={onClose}>
      <div className="Form-Grid">
        <label>Company Name *
          <input type="text" value={formData.company_name} onChange={(e) => handleChange("company_name", e.target.value)} placeholder="Enter Company Name" />
        </label>
        <label>Priority
          <select value={formData.priority} onChange={(e) => handleChange("priority", e.target.value)}>
            <option value="Low">Low</option>
            <option value="Normal">Normal</option>
            <option value="High">High</option>
          </select>
        </label>
        <label>Contact Name
          <input type="text" value={formData.contact_name} onChange={(e) => handleChange("contact_name", e.target.value)} placeholder="Enter Contact Name" />
        </label>
        <label>Origin *
          <select value={formData.source} onChange={(e) => handleChange("source", e.target.value)}>
            <option value="">Select Origin</option>
            {(sources || []).map((src) => <option key={src.label} value={src.label}>{src.label}</option>)}
          </select>
        </label>
        <label>Email
          <input type="email" value={formData.contact_email} onChange={(e) => handleChange("contact_email", e.target.value)} placeholder="Enter Email" />
        </label>
        <label>Assigned To
          <select value={formData.owner} onChange={(e) => handleChange("owner", e.target.value)}>
            <option value="">Select Owner</option>
            {(data.employees || []).map((emp) => <option key={emp.id} value={emp.id}>{emp.display_name}</option>)}
          </select>
        </label>
        <label>Phone
          <input type="tel" value={formData.contact_phone} onChange={(e) => handleChange("contact_phone", e.target.value)} placeholder="Enter Phone Number" />
        </label>
        <label>Estimated Value
          <input type="number" step="0.01" value={formData.estimated_value} onChange={(e) => handleChange("estimated_value", e.target.value)} placeholder="0.00" />
        </label>
      </div>
      <div className="Modal-Actions">
        <button className="Outline-Button" onClick={onClose}>Cancel</button>
        <button className="Primary-Button" disabled={busy || !formData.company_name.trim() || !formData.source.trim()} onClick={handleSubmit}>{busy ? "Creating..." : "Create Lead"}</button>
      </div>
    </Modal>
  );
}

function AssignLeadModal({ data, count, busy, onClose, onSubmit }) {
  const [employeeId, setEmployeeId] = useState("");
  return (
    <Modal title={`Assign ${count} Leads To Owner`} onClose={onClose}>
      <label>Owner
        <select value={employeeId} onChange={(event) => setEmployeeId(event.target.value)}>
          <option value="">Select Owner</option>
          {(data.employees || []).map((emp) => <option key={emp.id} value={emp.id}>{emp.display_name}</option>)}
        </select>
      </label>
      <button className="Primary-Button" disabled={busy || !employeeId} onClick={() => onSubmit(employeeId)}>Assign</button>
    </Modal>
  );
}

function BulkStageModal({ count, busy, onClose, onSubmit, options }) {
  const [stage, setStage] = useState("Contacted");
  const stages = options?.length ? options : ["New Lead", "Contact Attempted", "Discovery / Demo Scheduled", "Proposal Sent", "Closed - Won", "Closed - Lost"];
  return (
    <Modal title={`Move ${count} Leads To Stage`} onClose={onClose}>
      <label>Stage
        <select value={stage} onChange={(event) => setStage(event.target.value)}>
          {stages.map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
      </label>
      <button className="Primary-Button" disabled={busy} onClick={() => onSubmit(stage)}>Apply Stage</button>
    </Modal>
  );
}