import React, { useState } from "react";
import { BarChart3, BookOpen, ListChecks, MoreHorizontal, RefreshCw, Search, Users } from "lucide-react";

import { apiPatch, apiPost } from "../Api/Client.js";
import { EmptyState, Modal, SimpleTable, StatusPill } from "./Shared/ScreenComponents.jsx";
import {
  formatDate,
  getLeadRows,
  groupBy,
  leadContactSummary,
  leadOwnerName,
  leadSource,
  leadStage,
  marketingSourceCards,
  money,
  priorityTone,
  toggleSet,
  uniqueOptions,
} from "./Shared/ScreenUtils.jsx";

export function LmsScreen({ data, reload }) {
  const leads = getLeadRows(data);
  const [search, setSearch] = useState("");
  const [tag, setTag] = useState("all");
  const [priority, setPriority] = useState("all");
  const [owner, setOwner] = useState("all");
  const [stage, setStage] = useState("all");
  const [source, setSource] = useState("all");
  const [selected, setSelected] = useState(new Set());
  const [assignOpen, setAssignOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const refresh = () => reload(["leadAccounts", "leadActivities", "learningAssignments", "leadQueueSnapshots"]);

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
  const filtered = leads.filter((lead) => {
    const term = `${lead.company_name} ${leadSource(lead)} ${leadOwnerName(data, lead)}`.toLowerCase();
    const tagNames = (lead.tags || []).map((item) => String(item.name || item)).join(" ");
    return (!search || term.includes(search.toLowerCase())) && (tag === "all" || tagNames.includes(tag)) && (priority === "all" || String(lead.priority) === priority) && (owner === "all" || String(lead.owner_id || lead.owner || "") === owner) && (stage === "all" || leadStage(lead) === stage) && (source === "all" || leadSource(lead) === source);
  });
  const sourceCards = marketingSourceCards(leads);
  const stageGroups = groupBy(filtered, leadStage);
  const stageList = uniqueOptions(["New", "Contacted", "Qualified", "Proposal Sent", "Won", ...filtered.map(leadStage)]);
  const leadValue = filtered.reduce((sum, lead) => sum + Number(lead.estimated_value || 0), 0);

  return (
    <section className="lms-screen lms-command-center">
      <section className="lms-command-bar">
        <div><span className="section-kicker">Revenue Learning Ops</span><h1>LMS / Banao</h1><p>Lead Queue, Learning Assignments, Revenue Snapshots, And Sales Operations In One Workspace.</p></div>
        <div className="lms-command-actions"><div className="lms-search"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search Lead, Owner, Source" /></div><button className="outline-button" onClick={refresh}><RefreshCw size={16} /> Refresh</button></div>
      </section>

      <section className="lms-kpi-grid">
        <section><span>Lead Queue</span><strong>{filtered.length}</strong><small>{selected.size} Selected</small></section>
        <section><span>Pipeline Value</span><strong>{money(leadValue)}</strong><small>{sourceCards.length} Sources</small></section>
        <section><span>Learning Paths</span><strong>{(data.learningPaths || []).length}</strong><small>{(data.learningModules || []).length} Modules</small></section>
        <section><span>Assignments</span><strong>{(data.learningAssignments || []).length}</strong><small>{(data.leadQueueSnapshots || []).length} Queue Snapshots</small></section>
      </section>

      <section className="lms-source-strip">
        {sourceCards.map((card) => <button key={card.label} className={source === card.label ? "active" : ""} onClick={() => setSource(source === card.label ? "all" : card.label)}><span className={`source-logo ${card.tone}`}>{card.logo}</span><strong>{card.count}</strong><small>{card.label}</small></button>)}
        {!sourceCards.length && <EmptyState label="No Lead Sources Returned." />}
      </section>

      <section className="lms-workspace-grid">
        <aside className="lms-filter-rail">
          <header><ListChecks size={18} /><div><h2>Queue Filters</h2><span>{filtered.length} Of {leads.length} Leads</span></div></header>
          <label>Tags<select value={tag} onChange={(event) => setTag(event.target.value)}><option value="all">All Tags</option>{(data.leadTags || []).map((item) => <option key={item.id} value={item.name}>{item.name}</option>)}</select></label>
          <label>Priority<select value={priority} onChange={(event) => setPriority(event.target.value)}><option value="all">All Priorities</option>{uniqueOptions(leads.map((lead) => lead.priority)).map((value) => <option key={value}>{value}</option>)}</select></label>
          <label>Owner<select value={owner} onChange={(event) => setOwner(event.target.value)}><option value="all">All Owners</option>{(data.employees || []).map((employee) => <option key={employee.id} value={employee.id}>{employee.display_name}</option>)}</select></label>
          <label>Workflow<select value={stage} onChange={(event) => setStage(event.target.value)}><option value="all">All Stages</option>{uniqueOptions(leads.map(leadStage)).map((value) => <option key={value}>{value}</option>)}</select></label>
          <label>Origin<select value={source} onChange={(event) => setSource(event.target.value)}><option value="all">All Origins</option>{uniqueOptions(leads.map(leadSource)).map((value) => <option key={value}>{value}</option>)}</select></label>
        </aside>

        <main className="lms-lead-console">
          <section className="lms-queue-head"><div><h2>Lead Queue</h2><span>{selected.size} Selected</span></div><div><button className="icon-button" title="Assign Selected" onClick={() => setAssignOpen(true)} disabled={!selected.size}><Users size={16} /></button><button className="icon-button" title="More Actions" onClick={() => setMoreOpen(true)} disabled={!selected.size}><MoreHorizontal size={16} /></button></div></section>
          <section className="lms-stage-board">{stageList.map((stageName) => { const rows = stageGroups.get(stageName) || []; return <section className="lms-stage" key={stageName}><header><span>{stageName}</span><b>{rows.length}</b></header>{rows.slice(0, 5).map((lead) => <article key={lead.id} className="lms-lead-card"><label><input type="checkbox" checked={selected.has(lead.id)} onChange={() => setSelected(toggleSet(selected, lead.id))} /> <strong>{lead.company_name}</strong></label><p>{leadSource(lead)} / {leadOwnerName(data, lead)}</p><footer><span>{leadContactSummary(data, lead, "email")}</span><StatusPill tone={priorityTone(lead.priority)}>{lead.priority || "Normal"}</StatusPill></footer></article>)}{!rows.length && <EmptyState label="No Leads" />}</section>; })}</section>
        </main>
      </section>

      <section className="lms-bottom-grid">
        <section className="lms-ops-card"><header><h2>Learning Paths</h2><BookOpen size={18} /></header><SimpleTable columns={["Path", "Status", "Modules"]} rows={(data.learningPaths || []).slice(0, 6).map((path) => [path.title || path.name, path.status || "Active", (data.learningModules || []).filter((item) => String(item.path) === String(path.id)).length])} /></section>
        <section className="lms-ops-card"><header><h2>Revenue Snapshots</h2><BarChart3 size={18} /></header><SimpleTable columns={["Snapshot", "Leads", "Revenue", "Created"]} rows={(data.revenueSnapshots || data.leadQueueSnapshots || []).slice(0, 6).map((item) => [item.title || item.name || item.id, item.lead_count || item.queue_count || "-", item.revenue || item.estimated_revenue || "-", formatDate(item.created_at)])} /></section>
      </section>
      {assignOpen && <AssignLeadModal data={data} count={selected.size} busy={busy} onClose={() => setAssignOpen(false)} onSubmit={assignSelected} />}
      {moreOpen && <BulkStageModal count={selected.size} busy={busy} onClose={() => setMoreOpen(false)} onSubmit={bulkMoveStage} />}
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

function BulkStageModal({ count, busy, onClose, onSubmit }) {
  const [stage, setStage] = useState("Contacted");
  const stages = ["New", "Contacted", "Qualified", "ProposalSent", "Won", "Lost"];
  return (
    <Modal title={`Move ${count} Leads To Stage`} onClose={onClose}>
      <label>Stage<select value={stage} onChange={(event) => setStage(event.target.value)}>{stages.map((value) => <option key={value}>{value}</option>)}</select></label>
      <button className="primary-button" disabled={busy} onClick={() => onSubmit(stage)}>Apply Stage</button>
    </Modal>
  );
}