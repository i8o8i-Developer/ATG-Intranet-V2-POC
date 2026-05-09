import React, { useState, useEffect } from "react";
import { AlertTriangle, Clock, Users } from "lucide-react";

import { EmptyState, Modal, Panel, StatCard, StatusPill, Tabs } from "./Shared/ScreenComponents.jsx";
import { apiGet, apiPost } from "../Api/Client.js";
import { formatDate } from "./Shared/ScreenUtils.jsx";

/* ─── DelayManagementScreen ─────────────────────────────────────── */
export function DelayManagementScreen({ data, reload }) {
  const [tab, setTab] = useState("all");
  const [showAddModal, setShowAddModal] = useState(false);
  const [delayType, setDelayType] = useState("Project");
  const [selectedItem, setSelectedItem] = useState("");
  const [days, setDays] = useState("");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);

  const employees = data.employees || [];
  const projects = data.projects || [];
  const tasks = data.tasks || [];
  const delays = data.delays || [];
  
  // Auto-Reload Delays When Modal Closes
  useEffect(() => {
    if (!showAddModal && reload) {
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
      
      // Reload Delays Data
      if (reload) {
        await reload(["delays", "employees", "projects", "tasks"]);
      }
      
      alert("Delay Submitted Successfully!");
    } catch (error) {
      console.error("Failed To Submit Delay:", error);
      alert(`Failed to submit delay: ${error.message || "Please Try Again."}`);
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

  return (
    <>
      {/* Header */}
      <Panel
        title="Delay Management System"
        subtitle="Track And Manage Delays Across Projects, Tasks, And Team Members"
        right={
          <button className="ButtonPrimary" onClick={() => setShowAddModal(true)}>
            Add Delay Form
          </button>
        }
      >
        {/* Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }}>
          <StatCard label="Total Delays" value={totalDelays} />
          <StatCard label="Active Delays" value={activeDelays} />
          <StatCard label="Resolved Delays" value={resolvedDelays} />
          <StatCard label="Avg. Delay Days" value={avgDelayDays} />
        </div>

        {/* Tabs */}
        <Tabs
          value={tab}
          onChange={setTab}
          items={[
            ["all", `All Delays (${totalDelays})`],
            ["active", `Active (${activeDelays})`],
            ["resolved", `Resolved (${resolvedDelays})`],
          ]}
        />

        {/* Delays Table */}
        <div style={{ marginTop: "1.5rem" }}>
          {filteredDelays.length === 0 ? (
            <EmptyState label={`No ${tab} Delays Found`} />
          ) : (
            <table className="Erp-Table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Item</th>
                  <th>Days</th>
                  <th>Reason</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredDelays.map((delay) => (
                  <tr key={delay.id}>
                    <td>
                      <StatusPill tone={
                        delay.delay_type === "Project" ? "info" :
                        delay.delay_type === "Task" ? "warning" :
                        "neutral"
                      }>
                        {delay.delay_type}
                      </StatusPill>
                    </td>
                    <td>{getItemName(delay)}</td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <Clock size={16} />
                        {delay.days} {delay.days === 1 ? "day" : "days"}
                      </div>
                    </td>
                    <td style={{ maxWidth: "300px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {delay.reason || "N/A"}
                    </td>
                    <td>
                      <StatusPill tone={delay.status === "Active" ? "error" : "success"}>
                        {delay.status}
                      </StatusPill>
                    </td>
                    <td>{formatDate(delay.created_at)}</td>
                    <td>
                      {delay.status === "Active" && (
                        <button
                          className="ButtonSmall"
                          onClick={async () => {
                            try {
                              await apiPost(`/Project/ProjectDelays/${delay.id}/resolve/`, {});
                              if (reload) {
                                await reload(["delays"]);
                              }
                              alert("Delay Resolved Successfully!");
                            } catch (error) {
                              console.error("Failed To Resolve Delay:", error);
                              alert(`Failed to resolve delay: ${error.message || "Please Try Again"}`);
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

      {/* Team Members Section */}
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

      {/* Add Delay Modal */}
      {showAddModal && (
        <Modal title="Add Delay" onClose={() => setShowAddModal(false)}>
          <form onSubmit={handleSubmitDelay} style={{ padding: "1.5rem" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
              {/* Select Type */}
              <div>
                <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                  Select Type
                </label>
                <select
                  value={delayType}
                  onChange={(e) => {
                    setDelayType(e.target.value);
                    setSelectedItem("");
                  }}
                  required
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    border: "1px solid #E5e7eb",
                    borderRadius: "0.375rem",
                    fontSize: "0.875rem",
                  }}
                >
                  <option value="Project">Project</option>
                  <option value="Task">Task</option>
                  <option value="Employee">Employee</option>
                </select>
              </div>

              {/* Select Item */}
              <div>
                <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                  Select Item
                </label>
                <select
                  value={selectedItem}
                  onChange={(e) => setSelectedItem(e.target.value)}
                  required
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    border: "1px solid #E5e7eb",
                    borderRadius: "0.375rem",
                    fontSize: "0.875rem",
                  }}
                >
                  <option value="">—</option>
                  {getDelayItems().map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name || item.title || item.display_name || "Unknown"}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Days */}
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                Days
              </label>
              <input
                type="number"
                min="1"
                value={days}
                onChange={(e) => setDays(e.target.value)}
                required
                placeholder="2"
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #E5e7eb",
                  borderRadius: "0.375rem",
                  fontSize: "0.875rem",
                }}
              />
            </div>

            {/* Reason */}
            <div style={{ marginBottom: "1.5rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                Reason
              </label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                required
                placeholder="Supplier Issue"
                rows="3"
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #E5e7eb",
                  borderRadius: "0.375rem",
                  fontSize: "0.875rem",
                  resize: "vertical",
                }}
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%",
                padding: "0.75rem",
                backgroundColor: "#000",
                color: "#fff",
                border: "none",
                borderRadius: "0.375rem",
                fontSize: "0.875rem",
                fontWeight: 500,
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.6 : 1,
              }}
            >
              {loading ? "Submitting..." : "Submit Delay"}
            </button>
          </form>
        </Modal>
      )}
    </>
  );
}
