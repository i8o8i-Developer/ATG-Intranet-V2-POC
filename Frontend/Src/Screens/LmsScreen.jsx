import React, { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, Globe, Linkedin, MoreHorizontal, RefreshCw, Search, Trash2, Users } from "lucide-react";

import { apiPatch, apiPost } from "../Api/Client.js";
import { EmptyState, Modal, StatusPill } from "./Shared/ScreenComponents.jsx";
import {
  formatDate,
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
  if (tone === "linkedin") return <Linkedin size={16} />;
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

export function LmsScreen({ data, reload, navigate }) {
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
  const [busy, setBusy] = useState(false);

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

    return rawLeads.map((row) => {
      const account = accountMap.get(String(row.id)) || row;
      const contacts = contactsByLead.get(String(row.id)) || [];
      const primaryContact = contacts.find((item) => item.is_primary) || contacts[0] || {};
      const notes = notesByLead.get(String(row.id)) || [];
      const latestNote = notes[0] || null;
      const tags = account.tags || row.tags || [];
      const sourceLabel = leadSource(account);
      const ownerId = row.owner_id || account.owner || row.owner;

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
      };
    });
  }, [rawLeads, data.leadAccounts, data.leadContacts, data.leadNotes, data]);

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

  return (
    <section className="lms-screen">
      <div className="lms-breadcrumb">
        <strong>Intranet</strong>
        <button onClick={() => navigate?.("/home/")}>Home</button>
        <span>/</span>
        <button onClick={() => navigate?.("/lms/")}>Banao</button>
        <span>/</span>
        <b>LMS</b>
      </div>

      <h1>Lead Overview</h1>
      <section className="lms-source-strip">
        {sourceCards.map((card) => (
          <button key={card.label} className={source === card.label ? "active" : ""} onClick={() => setSource(source === card.label ? "all" : card.label)}>
            <span className={`source-logo ${card.tone}`}>{sourceLogoNode(card.label)}</span>
            <strong>{card.count}</strong>
            <small>{card.label}</small>
          </button>
        ))}
        {!sourceCards.length && <EmptyState label="No Lead Sources Returned." />}
      </section>

      <div className="lms-search-row">
        <div className="lms-search">
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search name" />
          <Search size={18} />
        </div>
      </div>

      <section className="lms-leads-panel">
        <header>
          <div>
            <h2>Leads <span>{selectedVisibleCount} of {filtered.length} Selected</span></h2>
          </div>
          <button className="icon-button" title="Reset Filters" onClick={resetFilters}>
            <RefreshCw size={18} />
          </button>
        </header>

        <div className="lead-tools">
          <button className="icon-action" title="Bulk Move Stage" onClick={() => setMoreOpen(true)} disabled={!selected.size}><MoreHorizontal size={16} /></button>
          <button className="icon-action" title="Clear Selection" onClick={() => setSelected(new Set())} disabled={!selected.size}><Trash2 size={16} /></button>
          <button className="icon-action" title="Assign Selected" onClick={() => setAssignOpen(true)} disabled={!selected.size}><Users size={16} /></button>
        </div>

        <div className="lms-filters">
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

        <div className="lead-table-scroll">
          <table className="erp-table lms-lead-table">
            <thead>
              <tr>
                <th><input type="checkbox" checked={allVisibleSelected} onChange={toggleAllVisible} aria-label="Select all visible leads" /></th>
                <th>
                  <button className="lms-sort-head" onClick={() => toggleSort("leadName")}>Lead/Client Name {renderSortIcon("leadName")}</button>
                </th>
                <th>Origin</th>
                <th>Work flow status</th>
                <th>
                  <button className="lms-sort-head" onClick={() => toggleSort("notesCount")}>Lead note count {renderSortIcon("notesCount")}</button>
                </th>
                <th>
                  <button className="lms-sort-head" onClick={() => toggleSort("companyName")}>Company name {renderSortIcon("companyName")}</button>
                </th>
                <th>Email</th>
                <th>Phone No's</th>
                <th>Assigned To</th>
                <th>
                  <button className="lms-sort-head" onClick={() => toggleSort("createdAt")}>Created At {renderSortIcon("createdAt")}</button>
                </th>
                <th>Last Update note</th>
                <th>
                  <button className="lms-sort-head" onClick={() => toggleSort("updatedAt")}>Last Updated {renderSortIcon("updatedAt")}</button>
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((lead) => (
                <tr key={lead.id}>
                  <td><input type="checkbox" checked={selected.has(lead.id)} onChange={() => setSelected(toggleSet(selected, lead.id))} aria-label={`Select ${lead.leadName}`} /></td>
                  <td>
                    <div className="lms-row-name">
                      <strong>{lead.leadName}</strong>
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
                  <td className="lms-last-note">{lead.lastUpdateNote || "-"}</td>
                  <td>{formatDate(lead.updatedAt)}</td>
                </tr>
              ))}
              {!filtered.length && (
                <tr>
                  <td colSpan={12}>
                    <div className="lms-empty-wrap"><EmptyState label="No Leads Match The Current Filters." /></div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {assignOpen && <AssignLeadModal data={data} count={selected.size} busy={busy} onClose={() => setAssignOpen(false)} onSubmit={assignSelected} />}
      {moreOpen && <BulkStageModal count={selected.size} busy={busy} options={stageOptions} onClose={() => setMoreOpen(false)} onSubmit={bulkMoveStage} />}
    </section>
  );
}

function AssignLeadModal({ data, count, busy, onClose, onSubmit }) {
  const [employeeId, setEmployeeId] = useState("");
  return (
    <Modal title={`Assign ${count} Leads To Owner`} onClose={onClose}>
      <label>Owner<select value={employeeId} onChange={(event) => setEmployeeId(event.target.value)}><option value="">Select Owner</option>{(data.employees || []).map((emp) => <option key={emp.id} value={emp.id}>{emp.display_name}</option>)}</select></label>
      <button className="primary-button" disabled={busy || !employeeId} onClick={() => onSubmit(employeeId)}>Assign</button>
    </Modal>
  );
}

function BulkStageModal({ count, busy, onClose, onSubmit, options }) {
  const [stage, setStage] = useState("Contacted");
  const stages = options?.length ? options : ["New Lead", "Contact Attempted", "Discovery / Demo Scheduled", "Proposal Sent", "Closed - Won", "Closed - Lost"];
  return (
    <Modal title={`Move ${count} Leads To Stage`} onClose={onClose}>
      <label>Stage<select value={stage} onChange={(event) => setStage(event.target.value)}>{stages.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
      <button className="primary-button" disabled={busy} onClick={() => onSubmit(stage)}>Apply Stage</button>
    </Modal>
  );
}