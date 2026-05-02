import React, { useState } from "react";
import { BriefcaseBusiness, CircleDot, Megaphone, RefreshCw, Search, Send } from "lucide-react";

import { apiPost } from "../Api/Client.js";
import { EmptyState, SimpleTable, StatusPill } from "./Shared/ScreenComponents.jsx";
import {
  formatDateTime,
  getLeadRows,
  groupBy,
  leadNoteCount,
  leadOwnerName,
  leadSource,
  leadStage,
  marketingRecentEvents,
  marketingSourceCards,
  money,
  numberOrNull,
  priorityTone,
  uniqueOptions,
} from "./Shared/ScreenUtils.jsx";

export function MarketingProjectScreen({ data, reload }) {
  const leads = getLeadRows(data);
  const [search, setSearch] = useState("");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [form, setForm] = useState({ company_name: "", source: "Banao Website", priority: "Normal", owner: "", estimated_value: "0", contact_name: "", contact_email: "", contact_phone: "" });
  const [result, setResult] = useState(null);
  const sourceOptions = uniqueOptions(leads.map(leadSource));
  const filteredLeads = leads.filter((lead) => {
    const leadText = `${lead.company_name} ${leadSource(lead)} ${leadStage(lead)} ${leadOwnerName(data, lead)}`.toLowerCase();
    const sourceText = leadSource(lead).toLowerCase();
    const activeSource = sourceFilter.toLowerCase();
    const matchesSource = sourceFilter === "all" || sourceText.includes(activeSource) || activeSource.includes(sourceText);
    return (!search || leadText.includes(search.toLowerCase())) && matchesSource;
  });
  const stageGroups = groupBy(filteredLeads, (lead) => leadStage(lead));
  const orderedStages = uniqueOptions(["New", "Contacted", "Qualified", "Proposal Sent", "Won", ...filteredLeads.map(leadStage)]);
  const marketingProjects = (data.projects || []).filter((project) => /marketing|banao|lead|sales/i.test(`${project.name} ${project.project_type} ${project.code}`));
  const totalValue = filteredLeads.reduce((sum, lead) => sum + Number(lead.estimated_value || 0), 0);
  const activeOwners = new Set(filteredLeads.map((lead) => lead.owner_id || lead.owner).filter(Boolean));
  const highIntent = filteredLeads.filter((lead) => /high|urgent|hot/i.test(`${lead.priority} ${leadStage(lead)}`)).length;
  const recentEvents = marketingRecentEvents(data, leads).slice(0, 8);
  const sourceCards = marketingSourceCards(leads);

  const createLead = async () => {
    const response = await apiPost("/Lms/api/add_lead/", { ...form, owner: numberOrNull(form.owner), estimated_value: form.estimated_value || 0 });
    setResult(response);
    setForm({ ...form, company_name: "", contact_name: "", contact_email: "", contact_phone: "" });
    reload();
  };

  return (
    <section className="marketing-screen">
      <section className="marketing-command">
        <div>
          <span className="section-kicker">Banao Growth</span>
          <h1>Marketing Project</h1>
          <div className="marketing-pulse"><span>{filteredLeads.length} Active Leads</span><span>{activeOwners.size} Owners</span><span>{highIntent} High Intent</span></div>
        </div>
        <div className="marketing-actions">
          <div className="marketing-search"><Search size={18} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search Leads, Stages, Owners" /></div>
          <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)}><option value="all">All Sources</option>{sourceOptions.map((source) => <option key={source} value={source}>{source}</option>)}</select>
          <button className="icon-button" onClick={reload} title="Refresh Marketing Data"><RefreshCw size={16} /></button>
        </div>
      </section>

      <section className="marketing-kpi-grid">
        <section><span>Total Pipeline</span><strong>{money(totalValue)}</strong><small>{filteredLeads.length} Leads In View</small></section>
        <section><span>Lead Sources</span><strong>{sourceOptions.length}</strong><small>{(data.leadContacts || []).length} Contacts Stored</small></section>
        <section><span>Open Notes</span><strong>{(data.leadNotes || []).length}</strong><small>{(data.leadActivities || []).length} Activities Logged</small></section>
        <section><span>Proposals</span><strong>{(data.leadProposals || []).length}</strong><small>{(data.leadAudits || []).length} Audits Attached</small></section>
      </section>

      <section className="marketing-workspace">
        <aside className="campaign-intake">
          <header><Megaphone size={19} /><div><h2>New Lead</h2><span>{form.source}</span></div></header>
          <div className="campaign-form">
            <label>Company<input value={form.company_name} onChange={(event) => setForm({ ...form, company_name: event.target.value })} /></label>
            <label>Source<select value={form.source} onChange={(event) => setForm({ ...form, source: event.target.value })}><option>Banao Website</option><option>Instagram</option><option>Client Website</option><option>LinkedIn</option><option>Referral</option></select></label>
            <label>Priority<select value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value })}><option>Low</option><option>Normal</option><option>High</option><option>Urgent</option></select></label>
            <label>Owner<select value={form.owner} onChange={(event) => setForm({ ...form, owner: event.target.value })}><option value="">Unassigned</option>{(data.employees || []).map((employee) => <option key={employee.id} value={employee.id}>{employee.display_name}</option>)}</select></label>
            <label>Value<input type="number" value={form.estimated_value} onChange={(event) => setForm({ ...form, estimated_value: event.target.value })} /></label>
            <label>Contact<input value={form.contact_name} onChange={(event) => setForm({ ...form, contact_name: event.target.value })} /></label>
            <label>Email<input value={form.contact_email} onChange={(event) => setForm({ ...form, contact_email: event.target.value })} /></label>
            <label>Phone<input value={form.contact_phone} onChange={(event) => setForm({ ...form, contact_phone: event.target.value })} /></label>
          </div>
          <button className="primary-button" onClick={createLead} disabled={!form.company_name}><Send size={16} /> Create Lead</button>
          {result && <pre className="inline-result">{JSON.stringify(result, null, 2)}</pre>}
        </aside>

        <main className="campaign-main">
          <section className="source-performance">
            {sourceCards.map((card) => <button key={card.label} className={sourceFilter === card.label ? "active" : ""} onClick={() => setSourceFilter(sourceFilter === card.label ? "all" : card.label)}><span className={`source-logo ${card.tone}`}>{card.logo}</span><strong>{card.count}</strong><small>{card.label}</small></button>)}
          </section>
          <section className="growth-funnel">
            {orderedStages.map((stage) => {
              const rows = stageGroups.get(stage) || [];
              return (
                <section className="growth-lane" key={stage}>
                  <header><span>{stage}</span><b>{rows.length}</b></header>
                  {rows.slice(0, 6).map((lead) => <article className="growth-lead" key={lead.id}><div><strong>{lead.company_name}</strong><StatusPill tone={priorityTone(lead.priority)}>{lead.priority || "Normal"}</StatusPill></div><p>{leadSource(lead)} / {leadOwnerName(data, lead)}</p><footer><span>{money(lead.estimated_value)} {lead.currency || "INR"}</span><span>{leadNoteCount(data, lead)} Notes</span></footer></article>)}
                  {!rows.length && <EmptyState label="No Leads" />}
                </section>
              );
            })}
          </section>
        </main>
      </section>

      <section className="marketing-bottom-grid">
        <section className="growth-card"><header><h2>Recent Lead Movement</h2><CircleDot size={18} /></header>{recentEvents.map((event) => <div className="movement-row" key={event.id}><div><strong>{event.title}</strong><span>{event.lead}</span></div><time>{formatDateTime(event.when)}</time></div>)}{!recentEvents.length && <EmptyState label="No Lead Movement Yet" />}</section>
        <section className="growth-card"><header><h2>Marketing Work Links</h2><BriefcaseBusiness size={18} /></header><SimpleTable columns={["Project", "Health", "Team", "Tasks"]} rows={marketingProjects.map((project) => [project.name, project.health || project.status, (data.teamAssignments || []).filter((item) => String(item.project) === String(project.id)).length, (data.tasks || []).filter((task) => String(task.project) === String(project.id)).length])} /></section>
      </section>
    </section>
  );
}