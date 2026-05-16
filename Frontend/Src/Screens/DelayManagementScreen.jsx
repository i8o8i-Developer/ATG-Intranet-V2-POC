import React, { useState, useEffect, useMemo } from "react";
import { AlertTriangle, Clock, Users } from "lucide-react";
import "../Styles/DelayScreen.css";

import { EmptyState, Modal, Panel, StatCard, StatusPill, Tabs } from "./Shared/ScreenComponents.jsx";
import { apiPost } from "../Api/Client.js";
import { formatDate } from "./Shared/ScreenUtils.jsx";

/* ─── DelayManagementScreen ─────────────────────────────────────── */
export function DelayManagementScreen({ data, reload }) {
  const me = data.me?.user || data.me?.account || data.me || {};
  const [tab, setTab] = useState("all");
  const [showAddModal, setShowAddModal] = useState(false);
  const [delayType, setDelayType] = useState("Project");
  const [selectedItem, setSelectedItem] = useState("");
  const [days, setDays] = useState("");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState({ ok: false, message: "" });

  const employees = data.employees || [];
  const projects = data.projects || [];
  const tasks = data.tasks || [];
  const delays = data.delays || [];

  //
  const canResolve = useMemo(() => {
    if (me.is_superuser || me.is_staff) return true;
    const myProfile = employees.find((e) => String(e.user) === String(me.id));
    if (!myProfile) return false;
    return projects.some((p) =>
      String(p.associate_project_manager) === String(myProfile.id) ||
      String(p.project_manager) === String(myProfile.id)
    );
  }, [me, employees, projects]);
  
  useEffect(() => {
    if (!showAddModal && reload && showAddModal !== undefined) {
      reload(["delays"]);
    }
  }, [showAddModal]);

  // Stats
  const totalDelays = delays.length;
  const activeDelays = delays.filter(d => d.status === "Active").length;
  const resolvedDelays = delays.filter(d => d.status === "Resolved").length;
  const avgDelayDays = delays.length > 0 
    ? (delays.reduce((sum, d) => sum + (d.days || 0), 0) / delays.length).toFixed(1)
    : 0;

  // Filter Delays By Tab
  const filteredDelays = tab === "all" 
    ? delays 
    : tab === "active"
    ? delays.filter(d => d.status === "Active")
    : delays.filter(d => d.status === "Resolved");

  const handleSubmitDelay = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await apiPost("/Project/ProjectDelays/", {
        delay_type: delayType,
        item_id: parseInt(selectedItem),
        days: parseInt(days),
        reason: reason,
        status: "Active",
      });

      setShowAddModal(false);
      setDelayType("Project");
      setSelectedItem("");
      setDays("");
      setReason("");
      
      if (reload) {
        await reload(["delays", "employees", "projects", "tasks"]);
      }
      
      setFeedback({ ok: true, message: "Delay Submitted Successfully." });
    } catch (error) {
      setFeedback({ ok: false, message: error?.message || "Failed To Submit Delay " });
    } finally {
      setLoading(false);
    }
  };

  const getDelayItems = () => {
    if (delayType === "Project") return projects;
    if (delayType === "Task") return tasks;
    if (delayType === "Employee") return employees;
    return [];
  };

  const getItemName = (delay) => {
    if (delay.delay_type === "Project") {
      const project = projects.find(p => p.id === delay.item_id);
      return project?.name || "Unknown Project";
    }
    if (delay.delay_type === "Task") {
      const task = tasks.find(t => t.id === delay.item_id);
      return task?.title || "Unknown Task";
    }
    if (delay.delay_type === "Employee") {
      const employee = employees.find(e => e.id === delay.item_id);
      return employee?.display_name || "Unknown Employee";
    }
    return "Unknown";
  };

  const getProjectName = (delay) => {
    const p = projects.find((pr) => String(pr.id) === String(delay.project));
    return p?.name || "—";
  };

  const getTaskTitle = (delay) => {
    const t = tasks.find((tk) => String(tk.id) === String(delay.task));
    return t?.title || "—";
  };

  const getReporterName = (delay) => {
    const e = employees.find((emp) => String(emp.id) === String(delay.reported_by));
    return e?.display_name || "—";
  };

  return (
    <div className="DelayPage">
      <Panel
        title="Delay Management System"
        subtitle="Track And Manage Delays Across Projects, Tasks, And Team Members"
        right={
          <button className="ButtonPrimary" onClick={() => setShowAddModal(true)}>
            Add Delay Form
          </button>
        }
      >
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }}>
          <StatCard label="Total Delays" value={totalDelays} />
          <StatCard label="Active Delays" value={activeDelays} />
          <StatCard label="Resolved Delays" value={resolvedDelays} />
          <StatCard label="Avg. Delay Days" value={avgDelayDays} />
        </div>

        <Tabs
          value={tab}
          onChange={setTab}
          items={[
            ["all", `All Delays (${totalDelays})`],
            ["active", `Active (${activeDelays})`],
            ["resolved", `Resolved (${resolvedDelays})`],
          ]}
        />

        <div style={{ marginTop: "1.5rem" }}>
          {filteredDelays.length === 0 ? (
            <EmptyState label={`No ${tab} Delays Found`} />
          ) : (
            <table className="Erp-Table">
              <thead>
                <tr>
                  <th>Project</th>
                  <th>Task</th>
                  <th>Type</th>
                  <th>Days</th>
                  <th>Reason</th>
                  <th>Reported By</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredDelays.map((delay) => (
                  <tr key={delay.id}>
                    <td style={{ fontWeight: 500 }}>{getProjectName(delay)}</td>
                    <td>{getTaskTitle(delay)}</td>
                    <td>
                      <StatusPill tone={
                        delay.delay_type === "Project" ? "info" :
                        delay.delay_type === "Task" ? "warning" :
                        "neutral"
                      }>
                        {delay.delay_type}
                      </StatusPill>
                    </td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <Clock size={16} />
                        {delay.days} {delay.days === 1 ? "day" : "days"}
                      </div>
                    </td>
                    <td style={{ maxWidth: "250px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {delay.reason || "N/A"}
                    </td>
                    <td>{getReporterName(delay)}</td>
                    <td>
                      <StatusPill tone={delay.status === "Active" ? "error" : "success"}>
                        {delay.status}
                      </StatusPill>
                    </td>
                    <td>{formatDate(delay.created_at)}</td>
                    <td>
                      {delay.status === "Active" && canResolve && (
                        <button
                          className="ButtonSmall"
                          onClick={async () => {
                            try {
                              await apiPost(`/Project/ProjectDelays/${delay.id}/resolve/`, {});
                              if (reload) {
                                await reload(["delays"]);
                              }
                              setFeedback({ ok: true, message: "Delay Resolved." });
                            } catch (error) {
                              setFeedback({ ok: false, message: error?.payload?.detail || error?.message || "Failed To Resolve Delay." });
                            }
                          }}
                        >
                          Resolve
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Panel>

      <Panel title="Team Members" subtitle="View Team Member Status And Delays">
        {employees.length === 0 ? (
          <EmptyState label="No Team Members Found" />
        ) : (
          <table className="Erp-Table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Role</th>
                <th>Email</th>
                <th>Status</th>
                <th>Active Delays</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((employee) => {
                const employeeDelays = delays.filter(
                  d => d.delay_type === "Employee" && d.item_id === employee.id && d.status === "Active"
                );

                return (
                  <tr key={employee.id}>
                    <td>{employee.display_name || "N/A"}</td>
                    <td>{employee.role_name || employee.position_name || "N/A"}</td>
                    <td>{employee.email || "N/A"}</td>
                    <td>
                      <StatusPill tone={employee.status === "Active" ? "success" : "neutral"}>
                        {employee.status || "Unknown"}
                      </StatusPill>
                    </td>
                    <td>
                      {employeeDelays.length > 0 ? (
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                          <AlertTriangle size={16} color="#ef4444" />
                          {employeeDelays.length} {employeeDelays.length === 1 ? "delay" : "delays"}
                        </div>
                      ) : (
                        <span style={{ color: "#10b981" }}>No Delays</span>
                      )}
                    </td>
                    <td>
                      <button className="ButtonSmall" onClick={() => {
                        setDelayType("Employee");
                        setSelectedItem(employee.id);
                        setShowAddModal(true);
                      }}>
                        Add Delay
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Panel>

      {showAddModal && (
        <Modal title="Add Delay" onClose={() => setShowAddModal(false)}>
          <form onSubmit={handleSubmitDelay}>
            <div className="Form-Grid Two">
              <label>Type<select className="Mini-Inp" value={delayType} onChange={(e) => { setDelayType(e.target.value); setSelectedItem(""); }} required><option value="Project">Project</option><option value="Task">Task</option><option value="Employee">Employee</option></select></label>
              <label>Item<select className="Mini-Inp" value={selectedItem} onChange={(e) => setSelectedItem(e.target.value)} required><option value="">—</option>{getDelayItems().map((item) => <option key={item.id} value={item.id}>{item.name || item.title || item.display_name || "Unknown"}</option>)}</select></label>
              <label>Days<input type="number" min="1" className="Mini-Inp" value={days} onChange={(e) => setDays(e.target.value)} required placeholder="2" /></label>
            </div>
            <label>Reason<textarea className="Mini-Inp" value={reason} onChange={(e) => setReason(e.target.value)} required placeholder="Supplier Issue" rows={3} /></label>
            {feedback.message && <div className={feedback.ok ? "Auth-AlertOk" : "Auth-Alert"}>{feedback.message}</div>}
            <div className="Modal-Actions">
              <button className="Primary-Button" type="submit" disabled={loading}>{loading ? "Submitting..." : "Submit Delay"}</button>
              <button className="Soft-Button" type="button" onClick={() => setShowAddModal(false)}>Cancel</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
