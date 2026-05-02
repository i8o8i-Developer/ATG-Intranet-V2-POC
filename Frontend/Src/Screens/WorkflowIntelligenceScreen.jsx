import React, { useState } from "react";
import { BarChart3, FileText, RefreshCw } from "lucide-react";

import { apiPost } from "../Api/Client.js";
import { EmptyState, Progress } from "./Shared/ScreenComponents.jsx";
import { formatDate } from "./Shared/ScreenUtils.jsx";

export function WorkflowIntelligenceScreen({ data, reload }) {
  const summaryRows = Array.isArray(data.workflowSummary) ? data.workflowSummary : [];
  const topRows = Array.isArray(data.topWorkflows) ? data.topWorkflows : [];
  const workflowMaps = data.businessWorkflows || [];
  const reports = data.workflowReports || [];
  const totalHits = summaryRows.reduce((sum, row) => sum + Number(row.hit_count || 0), 0);
  const [form, setForm] = useState({ title: "Workflow Intelligence Report", report_type: "Manual", start_date: "", end_date: "" });
  const [report, setReport] = useState(null);

  const generateReport = async () => {
    const response = await apiPost("/WorkflowIntelligence/api/workflow-reports/generate/", form);
    setReport(response);
    reload();
  };

  return (
    <section className="workflow-screen intelligence-screen">
      <section className="intelligence-command">
        <div>
          <span className="section-kicker">AI Ops Center</span>
          <h1>Workflow Intelligence</h1>
          <p>Route Usage, Workflow Maps, Reports, And MCP Readiness In One Operations View.</p>
        </div>
        <div className="intelligence-actions"><button className="outline-button" onClick={reload}><RefreshCw size={16} /> Refresh</button><button className="primary-button" onClick={generateReport}><BarChart3 size={16} /> Generate Report</button></div>
      </section>

      <section className="intelligence-kpi-grid">
        <section><span>Route Hits</span><strong>{totalHits}</strong><small>{summaryRows.length} Tracked Routes</small></section>
        <section><span>Workflow Maps</span><strong>{workflowMaps.length}</strong><small>{workflowMaps.reduce((sum, item) => sum + (Array.isArray(item.route_patterns) ? item.route_patterns.length : 0), 0)} Mapped Paths</small></section>
        <section><span>Reports</span><strong>{reports.length}</strong><small>{reports.filter((item) => item.status === "Generated").length} Generated</small></section>
        <section><span>Top Workflow</span><strong>{topRows[0]?.hit_count || 0}</strong><small>{topRows[0]?.workflow_name || "No Traffic Yet"}</small></section>
      </section>

      <section className="intelligence-grid">
        <section className="report-builder">
          <header><FileText size={18} /><div><h2>Report Builder</h2><span>Persisted WorkflowReport Output</span></div></header>
          <div className="report-form"><label>Title<input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></label><label>Type<select value={form.report_type} onChange={(event) => setForm({ ...form, report_type: event.target.value })}><option>Manual</option><option>Weekly</option><option>Audit</option><option>MCP Readiness</option></select></label><label>Start Date<input type="date" value={form.start_date} onChange={(event) => setForm({ ...form, start_date: event.target.value })} /></label><label>End Date<input type="date" value={form.end_date} onChange={(event) => setForm({ ...form, end_date: event.target.value })} /></label></div>
          {report && <pre className="inline-result">{JSON.stringify(report, null, 2)}</pre>}
        </section>
        <section className="workflow-radar">
          <header><h2>Workflow Heat</h2><span>{topRows.length} Active Flows</span></header>
          {topRows.map((row) => <div className="radar-row" key={row.workflow_name}><div><strong>{row.workflow_name || "Unnamed"}</strong><span>{row.hit_count || 0} Route Hits</span></div><Progress value={totalHits ? (Number(row.hit_count || 0) / totalHits) * 100 : 0} /></div>)}
          {!topRows.length && <EmptyState label="No Workflow Usage Rows Returned Yet." />}
        </section>
      </section>

      <section className="workflow-map-grid">
        {workflowMaps.map((item) => <article className="workflow-map-tile" key={item.id || `${item.owning_module}-${item.workflow_name}`}><header><span>{item.owning_module}</span><b>{Array.isArray(item.route_patterns) ? item.route_patterns.length : 0} Routes</b></header><h2>{item.workflow_name}</h2><p>{item.description}</p><div>{(item.route_patterns || []).slice(0, 3).map((route) => <code key={route}>{route}</code>)}</div></article>)}
        {!workflowMaps.length && <EmptyState label="No Workflow Maps Returned." />}
      </section>

      <section className="intelligence-bottom-grid">
        <section className="report-feed"><header><h2>Reports</h2><span>{reports.length} Records</span></header>{reports.slice(0, 6).map((item) => <article key={item.id}><div><strong>{item.title}</strong><span>{item.report_type} / {item.status}</span></div><time>{formatDate(item.generated_for || item.created_at)}</time></article>)}{!reports.length && <EmptyState label="No Reports Generated Yet." />}</section>
        <section className="route-usage-feed"><header><h2>Route Usage</h2><span>{summaryRows.length} Rows</span></header>{summaryRows.map((item) => <article key={`${item.workflow_name}-${item.route_pattern}-${item.username}`}><div><strong>{item.workflow_name}</strong><code>{item.route_pattern}</code></div><span>{item.username || "All Users"}</span><b>{item.hit_count}</b></article>)}</section>
      </section>
    </section>
  );
}