import React, { useMemo, useState } from "react";
import { Bot, FileCheck2, KeyRound, Plus, ShieldCheck, Wrench } from "lucide-react";

import { apiPost } from "../Api/Client.js";
import { EmptyState, Modal, Panel, SimpleTable, StatCard, StatusPill, Tabs } from "./Shared/ScreenComponents.jsx";
import { findById, formatDateTime } from "./Shared/ScreenUtils.jsx";

export function McpScreen({ data, reload }) {
  const [tab, setTab] = useState("agents");
  const [createAgentOpen, setCreateAgentOpen] = useState(false);
  const [grantOpen, setGrantOpen] = useState(false);
  const [invokeAgent, setInvokeAgent] = useState(null);
  const [draftFor, setDraftFor] = useState(null);

  const agents = data.agentPrincipals || [];
  const tools = data.mcpToolDefinitions || [];
  const resources = data.mcpResourceDefinitions || [];
  const grants = data.mcpAccessGrants || [];
  const audits = data.mcpInvocationAudits || [];
  const drafts = data.draftAgentActions || [];

  const refresh = () => reload(["agentPrincipals", "mcpToolDefinitions", "mcpResourceDefinitions", "mcpAccessGrants", "mcpInvocationAudits", "draftAgentActions"]);

  const approveDraft = async (action) => {
    await apiPost(`/McpAccessLayer/DraftAgentActions/${action.id}/`, { ...action, status: "Approved" });
    reload(["draftAgentActions"]);
  };

  const stats = useMemo(() => ({
    agents: agents.length,
    tools: tools.length,
    resources: resources.length,
    grants: grants.length,
    audits: audits.length,
    drafts: drafts.filter((draft) => draft.status === "Pending" || draft.status === "Draft").length,
  }), [agents, tools, resources, grants, audits, drafts]);

  return (
    <section className="Mcp-Screen Screen-Stack">
      <section className="Screen-Header">
        <div>
          <span className="Section-Kicker">Model Context Protocol</span>
          <h1>MCP Agents & Access</h1>
          <p>Govern Agent Principals, Tool Definitions, Resources, And Audit Trails.</p>
        </div>
        <div className="Table-Actions">
          <button className="Primary-Button Small" onClick={() => setCreateAgentOpen(true)}><Plus size={14} /> New Agent</button>
          <button className="Outline-Button" onClick={() => setGrantOpen(true)}><KeyRound size={14} /> Grant Access</button>
        </div>
      </section>

      <div className="Stat-Grid Four">
        <StatCard label="Agent Principals" value={stats.agents} />
        <StatCard label="Tool Definitions" value={stats.tools} />
        <StatCard label="Resources" value={stats.resources} />
        <StatCard label="Access Grants" value={stats.grants} />
        <StatCard label="Invocation Audits" value={stats.audits} />
        <StatCard label="Pending Drafts" value={stats.drafts} />
      </div>

      <Tabs
        value={tab}
        onChange={setTab}
        items={[
          ["agents", "Agents"],
          ["tools", "Tools"],
          ["resources", "Resources"],
          ["grants", "Access Grants"],
          ["audits", "Invocation Audits"],
          ["drafts", "Draft Actions"],
        ]}
      />

      {tab === "agents" && (
        <Panel title="Agent Principals">
          <table className="Erp-Table">
            <thead><tr><th>Agent</th><th>Owner</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead>
            <tbody>
              {agents.map((agent) => (
                <tr key={agent.id}>
                  <td><Bot size={14} /> <strong>{agent.display_name || agent.name}</strong><div className="Muted-Text">{agent.principal_type || "Agent"}</div></td>
                  <td>{agent.owner_name || agent.owner || "-"}</td>
                  <td><StatusPill tone={agent.status === "Active" ? "green" : "gold"}>{agent.status || "Inactive"}</StatusPill></td>
                  <td>{formatDateTime(agent.created_at)}</td>
                  <td className="Table-Actions">
                    <button className="Soft-Button Small" onClick={() => setInvokeAgent(agent)}>Invoke</button>
                    <button className="Soft-Button Small" onClick={() => setDraftFor(agent)}>Draft Action</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!agents.length && <EmptyState label="No Agent Principals Yet." />}
        </Panel>
      )}

      {tab === "tools" && (
        <Panel title="Tool Definitions">
          <SimpleTable
            columns={["Tool", "Provider", "Permission", "Status"]}
            rows={tools.map((tool) => [tool.display_name || tool.name, tool.provider || "Internal", tool.permission || "Read", <StatusPill key={tool.id} tone={tool.is_active ? "green" : "gold"}>{tool.is_active ? "Active" : "Inactive"}</StatusPill>])}
          />
          {!tools.length && <EmptyState label="No Tools Registered." />}
        </Panel>
      )}

      {tab === "resources" && (
        <Panel title="Resource Definitions">
          <SimpleTable
            columns={["Resource", "Type", "Owner", "Visibility"]}
            rows={resources.map((res) => [res.display_name || res.name, res.resource_type || "-", res.owner_name || "-", res.visibility || "Tenant"])}
          />
          {!resources.length && <EmptyState label="No Resources Registered." />}
        </Panel>
      )}

      {tab === "grants" && (
        <Panel title="Access Grants" right={<button className="Primary-Button Small" onClick={() => setGrantOpen(true)}><Plus size={13} /> New Grant</button>}>
          <SimpleTable
            columns={["Agent", "Tool", "Resource", "Permission", "Expires"]}
            rows={grants.map((grant) => [findById(agents, grant.agent)?.display_name || grant.agent, findById(tools, grant.tool)?.display_name || grant.tool || "*", findById(resources, grant.resource)?.display_name || grant.resource || "*", grant.permission || "Read", grant.expires_at ? formatDateTime(grant.expires_at) : "Never"])}
          />
          {!grants.length && <EmptyState label="No Grants Yet." />}
        </Panel>
      )}

      {tab === "audits" && (
        <Panel title="Recent Invocations">
          <SimpleTable
            columns={["When", "Agent", "Action", "Decision", "Reason"]}
            rows={audits.slice(0, 50).map((row) => [formatDateTime(row.created_at), findById(agents, row.agent)?.display_name || row.agent, row.action, <StatusPill key={row.id} tone={row.decision === "Allowed" ? "green" : "red"}>{row.decision}</StatusPill>, row.reason || "-"])}
          />
          {!audits.length && <EmptyState label="No Invocation Audits Yet." />}
        </Panel>
      )}

      {tab === "drafts" && (
        <Panel title="Draft Agent Actions">
          <table className="Erp-Table">
            <thead><tr><th>Agent</th><th>Action Type</th><th>Target</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead>
            <tbody>
              {drafts.map((draft) => (
                <tr key={draft.id}>
                  <td>{findById(agents, draft.agent)?.display_name || draft.agent}</td>
                  <td><FileCheck2 size={13} /> {draft.action_type}</td>
                  <td>{draft.target_resource_type} {draft.target_resource_id && `#${draft.target_resource_id}`}</td>
                  <td><StatusPill tone={draft.status === "Approved" ? "green" : draft.status === "Rejected" ? "red" : "gold"}>{draft.status || "Pending"}</StatusPill></td>
                  <td>{formatDateTime(draft.created_at)}</td>
                  <td className="Table-Actions">
                    {draft.status !== "Approved" && <button className="Soft-Button Small" onClick={() => approveDraft(draft)}>Approve</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!drafts.length && <EmptyState label="No Draft Actions." />}
        </Panel>
      )}

      {createAgentOpen && <CreateAgentModal data={data} onClose={() => setCreateAgentOpen(false)} reload={refresh} />}
      {grantOpen && <CreateGrantModal data={data} onClose={() => setGrantOpen(false)} reload={refresh} />}
      {invokeAgent && <InvokeAgentModal agent={invokeAgent} data={data} onClose={() => setInvokeAgent(null)} reload={refresh} />}
      {draftFor && <DraftActionModal agent={draftFor} onClose={() => setDraftFor(null)} reload={refresh} />}
    </section>
  );
}

function CreateAgentModal({ data, onClose, reload }) {
  const [form, setForm] = useState({ name: "", display_name: "", principal_type: "ServiceAccount", status: "Active", owner: "" });
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      await apiPost("/McpAccessLayer/AgentPrincipals/", form);
      reload();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="New Agent Principal" onClose={onClose} wide>
      <div className="Form-Grid Two Modal-Form">
        <label>Name<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Agent-Bot" /></label>
        <label>Display Name<input value={form.display_name} onChange={(event) => setForm({ ...form, display_name: event.target.value })} /></label>
        <label>Type<select value={form.principal_type} onChange={(event) => setForm({ ...form, principal_type: event.target.value })}><option>ServiceAccount</option><option>User</option><option>System</option></select></label>
        <label>Status<select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}><option>Active</option><option>Suspended</option></select></label>
        <label>Owner<select value={form.owner} onChange={(event) => setForm({ ...form, owner: event.target.value })}><option value="">No Owner</option>{(data.employees || []).map((emp) => <option key={emp.id} value={emp.id}>{emp.display_name}</option>)}</select></label>
      </div>
      <button className="Primary-Button" onClick={save} disabled={busy || !form.name}>Create Agent</button>
    </Modal>
  );
}

function CreateGrantModal({ data, onClose, reload }) {
  const [form, setForm] = useState({ agent: "", tool: "", resource: "", permission: "Read", expires_at: "" });
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      const payload = { ...form };
      if (!payload.tool) delete payload.tool;
      if (!payload.resource) delete payload.resource;
      if (!payload.expires_at) delete payload.expires_at;
      await apiPost("/McpAccessLayer/McpAccessGrants/", payload);
      reload();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="New Access Grant" onClose={onClose} wide>
      <div className="Form-Grid Two Modal-Form">
        <label>Agent<select value={form.agent} onChange={(event) => setForm({ ...form, agent: event.target.value })}><option value="">Select</option>{(data.agentPrincipals || []).map((agent) => <option key={agent.id} value={agent.id}>{agent.display_name || agent.name}</option>)}</select></label>
        <label>Tool<select value={form.tool} onChange={(event) => setForm({ ...form, tool: event.target.value })}><option value="">Any Tool</option>{(data.mcpToolDefinitions || []).map((tool) => <option key={tool.id} value={tool.id}>{tool.display_name || tool.name}</option>)}</select></label>
        <label>Resource<select value={form.resource} onChange={(event) => setForm({ ...form, resource: event.target.value })}><option value="">Any Resource</option>{(data.mcpResourceDefinitions || []).map((res) => <option key={res.id} value={res.id}>{res.display_name || res.name}</option>)}</select></label>
        <label>Permission<select value={form.permission} onChange={(event) => setForm({ ...form, permission: event.target.value })}><option>Read</option><option>Write</option><option>Admin</option></select></label>
        <label>Expires At<input type="Datetime-Local" value={form.expires_at} onChange={(event) => setForm({ ...form, expires_at: event.target.value })} /></label>
      </div>
      <button className="Primary-Button" onClick={save} disabled={busy || !form.agent}>Grant Access</button>
    </Modal>
  );
}

function InvokeAgentModal({ agent, data, onClose, reload }) {
  const [form, setForm] = useState({ tool: "", resource: "", action: "Invoke", reason: "" });
  const [decision, setDecision] = useState(null);
  const [busy, setBusy] = useState(false);

  const checkPermission = async () => {
    setBusy(true);
    try {
      const res = await apiPost(`/McpAccessLayer/AgentPrincipals/${agent.id}/can-invoke/`, { tool: form.tool || null, resource: form.resource || null, permission: "Read" });
      setDecision(res?.allowed === true ? "Allowed" : "Denied");
    } finally {
      setBusy(false);
    }
  };

  const recordInvocation = async () => {
    setBusy(true);
    try {
      await apiPost(`/McpAccessLayer/AgentPrincipals/${agent.id}/record-invocation/`, {
        tool: form.tool || null,
        resource: form.resource || null,
        action: form.action,
        decision: decision || "Allowed",
        reason: form.reason,
      });
      reload();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title={`Invoke As ${agent.display_name || agent.name}`} onClose={onClose} wide>
      <div className="Form-Grid Two Modal-Form">
        <label>Tool<select value={form.tool} onChange={(event) => setForm({ ...form, tool: event.target.value })}><option value="">Any</option>{(data.mcpToolDefinitions || []).map((tool) => <option key={tool.id} value={tool.id}>{tool.display_name || tool.name}</option>)}</select></label>
        <label>Resource<select value={form.resource} onChange={(event) => setForm({ ...form, resource: event.target.value })}><option value="">Any</option>{(data.mcpResourceDefinitions || []).map((res) => <option key={res.id} value={res.id}>{res.display_name || res.name}</option>)}</select></label>
        <label>Action<input value={form.action} onChange={(event) => setForm({ ...form, action: event.target.value })} /></label>
        <label>Reason<input value={form.reason} onChange={(event) => setForm({ ...form, reason: event.target.value })} /></label>
      </div>
      <div className="Table-Actions">
        <button className="Soft-Button Small" onClick={checkPermission} disabled={busy}><ShieldCheck size={13} /> Check Permission</button>
        {decision && <StatusPill tone={decision === "Allowed" ? "green" : "red"}>{decision}</StatusPill>}
      </div>
      <button className="Primary-Button" onClick={recordInvocation} disabled={busy}><Wrench size={13} /> Record Invocation</button>
    </Modal>
  );
}

function DraftActionModal({ agent, onClose, reload }) {
  const [form, setForm] = useState({ action_type: "Create", target_resource_type: "WorkItem", target_resource_id: "", payload: "{}" });
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      let payload = {};
      try { payload = JSON.parse(form.payload || "{}"); } catch { payload = { raw: form.payload }; }
      await apiPost(`/McpAccessLayer/AgentPrincipals/${agent.id}/draft-action/`, {
        action_type: form.action_type,
        target_resource_type: form.target_resource_type,
        target_resource_id: form.target_resource_id,
        payload,
      });
      reload();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title={`Draft Action For ${agent.display_name || agent.name}`} onClose={onClose} wide>
      <div className="Form-Grid Two Modal-Form">
        <label>Action Type<input value={form.action_type} onChange={(event) => setForm({ ...form, action_type: event.target.value })} /></label>
        <label>Target Type<input value={form.target_resource_type} onChange={(event) => setForm({ ...form, target_resource_type: event.target.value })} /></label>
        <label>Target Id<input value={form.target_resource_id} onChange={(event) => setForm({ ...form, target_resource_id: event.target.value })} /></label>
      </div>
      <label>Payload (JSON)<textarea rows={6} value={form.payload} onChange={(event) => setForm({ ...form, payload: event.target.value })} /></label>
      <button className="Primary-Button" onClick={save} disabled={busy}>Create Draft</button>
    </Modal>
  );
}
