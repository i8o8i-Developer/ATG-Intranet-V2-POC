import React, { useEffect, useState } from "react";
import { AlertTriangle, ChevronRight, FileText, Share2 } from "lucide-react";

import { apiGet, apiPost } from "../Api/Client.js";
import { Disclosure, EmptyState, Modal, Panel, Progress, SimpleTable, StatusPill } from "./Shared/ScreenComponents.jsx";
import {
  avatar,
  employeeContact,
  employeeName,
  findById,
  formatDate,
  money,
  progressForTask,
  projectName,
} from "./Shared/ScreenUtils.jsx";

export function ProjectDashboardScreen({ data, route, reload, navigate }) {
  const routeParts = route.split("?")[0].split("/").filter(Boolean);
  const routeProjectId = routeParts[2] && /^\d+$/.test(routeParts[2]) ? routeParts[2] : "";
  const [selectedProjectId, setSelectedProjectId] = useState(routeProjectId || String(data.projects?.[0]?.id || ""));
  const [dashboard, setDashboard] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);

  useEffect(() => {
    if (!selectedProjectId && data.projects?.length) setSelectedProjectId(String(data.projects[0].id));
  }, [data.projects, selectedProjectId]);

  useEffect(() => {
    if (!selectedProjectId) return;
    apiGet(`/Project/dashboard/${selectedProjectId}/${encodeURIComponent(projectName(data, selectedProjectId) || "project")}/`).then(setDashboard).catch(() => setDashboard(null));
  }, [selectedProjectId, data]);

  const project = dashboard?.project || findById(data.projects, selectedProjectId) || {};
  const tasks = dashboard?.tasks?.length ? dashboard.tasks : (data.tasks || []).filter((task) => String(task.project) === String(selectedProjectId));
  const milestones = dashboard?.milestones?.length ? dashboard.milestones : (data.milestones || []).filter((item) => String(item.project) === String(selectedProjectId));
  const team = dashboard?.team?.length ? dashboard.team : (data.teamAssignments || []).filter((item) => String(item.project) === String(selectedProjectId));
  const docs = dashboard?.documents?.length ? dashboard.documents : (data.projectDocuments || []).filter((item) => String(item.project) === String(selectedProjectId));

  const addDelay = async () => {
    const milestone = milestones[0];
    if (!milestone) return;
    await apiPost("/Project/api/add-delay/", { milestone_id: milestone.id, delayed_days: 1 });
    reload();
  };

  return (
    <section className="project-screen screen-stack">
      <Disclosure title="Notifications" defaultOpen={false}>
        {(dashboard?.alerts || data.alerts || []).filter((item) => !selectedProjectId || String(item.project) === String(selectedProjectId) || !item.project).slice(0, 10).map((item) => <div className="notice-row compact" key={item.id}>{item.title || item.severity}</div>)}
      </Disclosure>
      <section className="project-title-bar"><div><StatusPill>{project.priority || "P3"}</StatusPill><strong>{project.name || "Project"}</strong><StatusPill tone="green">{project.health || "On Track"}</StatusPill></div><select value={selectedProjectId} onChange={(event) => { setSelectedProjectId(event.target.value); navigate(`/project/dashboard/${event.target.value}/${encodeURIComponent(projectName(data, event.target.value) || "project")}/`); }}>{(data.projects || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><div><button className="outline-button"><FileText size={16} /> Documents</button><button className="icon-button"><Share2 size={17} /></button></div></section>
      <Disclosure title="Key Project Details" defaultOpen={false}><SimpleTable columns={["Code", "Type", "Status", "Start", "End"]} rows={[[project.code, project.project_type, project.status, formatDate(project.starts_on), formatDate(project.ends_on)]]} /></Disclosure>
      <Panel title="Tasks" right={<select><option>Pending Tasks</option><option>All Tasks</option></select>}>
        <table className="erp-table project-task-table"><thead><tr><th>M1</th><th>Progress</th><th>Assignee</th><th>Due Date</th><th>Priority</th><th>Bounties</th></tr></thead><tbody>{tasks.map((task) => <tr key={task.id} onClick={() => setSelectedTask(task)}><td><ChevronRight size={15} />{task.title}</td><td><Progress value={progressForTask(task, data.tasks)} /></td><td>{avatar(employeeName(data, task.owner || task.owner_id))}</td><td className={task.due_at ? "danger-text" : ""}>{formatDate(task.due_at)}</td><td><AlertTriangle size={16} /></td><td>{money(task.bounty)}</td></tr>)}</tbody></table>
      </Panel>
      <button className="black-button" onClick={addDelay}>Add Delay Form</button>
      <Disclosure title="Team Members" defaultOpen>
        <SimpleTable columns={["Name", "Role", "Work Availability", "Contact Details", "Action", "EOD Report"]} rows={team.map((assignment) => [assignment.employee_name || employeeName(data, assignment.employee), assignment.role, assignment.status === "Active" ? "Available" : assignment.status, employeeContact(data, assignment.employee_id || assignment.employee), "...", <button className="primary-button small" key="eod">View EOD</button>])} />
      </Disclosure>
      <Disclosure title="Documents" defaultOpen={false}><SimpleTable columns={["Title", "Type", "Pinned", "Reference"]} rows={docs.map((doc) => [doc.title, doc.document_type, doc.is_pinned ? "Yes" : "No", doc.storage_reference || doc.file_id])} /></Disclosure>
      {selectedTask && <TaskDetailModal task={selectedTask} data={data} onClose={() => setSelectedTask(null)} reload={reload} />}
    </section>
  );
}

function TaskDetailModal({ task, data, onClose, reload }) {
  const [description, setDescription] = useState(task.description || "");
  const activities = (data.taskActivities || []).filter((item) => String(item.work_item) === String(task.id));
  const prLinks = Array.isArray(task.metadata?.prs) ? task.metadata.prs : [];

  const saveDescription = async () => {
    await apiPost(`/Project/update-description/${task.id}/`, { description });
    reload();
    onClose();
  };

  return (
    <Modal onClose={onClose} wide title={<><a>{projectName(data, task.project) || "Project"}</a> / M1</>}>
      <div className="task-modal-grid"><section><StatusPill tone="blue">Task</StatusPill><h2>{task.title}</h2><dl className="details-grid"><div><dt>Status</dt><dd>{task.status}</dd></div><div><dt>Creation Date</dt><dd>{formatDate(task.created_at)}</dd></div><div><dt>Due Date</dt><dd>{formatDate(task.due_at)}</dd></div><div><dt>Assignee</dt><dd>{employeeName(data, task.owner)}</dd></div></dl><label>Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Add A Description..." /></label><button className="primary-button" onClick={saveDescription}>Save</button><h4>Links</h4><button className="primary-button small">+ Add Link</button><h4>Pull Requests</h4><button className="primary-button small">+ Add PR</button>{prLinks.map((pr) => <div className="pr-row" key={pr.url}><a href={pr.url} target="_blank" rel="noreferrer">{pr.name}</a> <span>({pr.state})</span></div>)}</section><aside><h3>Activity</h3>{activities.map((item) => <div className="activity-row" key={item.id}><span>{item.message || item.activity_type}</span><time>{formatDate(item.created_at)}</time></div>)}{!activities.length && <EmptyState label="No Task Activity Returned." />}</aside></div>
    </Modal>
  );
}