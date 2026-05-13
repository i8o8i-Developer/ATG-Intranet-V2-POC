import React, { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CalendarDays,
  ChevronRight,
  ExternalLink,
  FileText,
  Flag,
  GitBranch,
  GitPullRequest,
  Link as LinkIcon,
  Pencil,
  Plus,
  Share2,
  Trash2,
  UserCheck,
  UserX,
  X,
} from "lucide-react";

import { apiGet, apiPost, PUBLIC_BASE_URL } from "../Api/Client.js";
import { Disclosure, EmptyState, Modal, Panel, Progress, SimpleTable, StatusPill } from "./Shared/ScreenComponents.jsx";
import "../Styles/ProjectScreen.css";
import "../Styles/HrmsModal.css";
import {
  avatar,
  employeeContact,
  employeeName,
  findById,
  formatDate,
  isCompleted,
  isoDate,
  money,
  progressForTask,
  projectName,
} from "./Shared/ScreenUtils.jsx";

export function ProjectDashboardScreen({ data, route, reload, navigate, kind = "project" }) {
  const routeParts = (route || "").split("?")[0].split("/").filter(Boolean);
  const routeProjectId = routeParts[2] && /^\d+$/.test(routeParts[2]) ? routeParts[2] : "";
  const routeBase = kind === "marketing" ? "/marketing-project/dashboard" : "/project/dashboard";
  const [selectedProjectId, setSelectedProjectId] = useState(routeProjectId || String(data.projects?.[0]?.id || ""));
  const [dashboard, setDashboard] = useState(null);
  const [taskFilter, setTaskFilter] = useState("pending");
  const [selectedTask, setSelectedTask] = useState(null);

  // Modals
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [editProject, setEditProject] = useState(false);
  const [flagOpen, setFlagOpen] = useState(false);
  const [documentOpen, setDocumentOpen] = useState(false);
  const [reposOpen, setReposOpen] = useState(false);
  const [milestoneToEdit, setMilestoneToEdit] = useState(null);
  const [eodEmployee, setEodEmployee] = useState(null);
  const [addMilestoneOpen, setAddMilestoneOpen] = useState(false);
  const [addTaskFor, setAddTaskFor] = useState(null); 
  const [addMemberOpen, setAddMemberOpen] = useState(false);

  useEffect(() => {
    if (!selectedProjectId && data.projects?.length) setSelectedProjectId(String(data.projects[0].id));
  }, [data.projects, selectedProjectId]);

  useEffect(() => {
    if (!selectedProjectId) return;
    apiGet(`/Project/dashboard/${selectedProjectId}/${encodeURIComponent(projectName(data, selectedProjectId) || "project")}/`)
      .then(setDashboard)
      .catch(() => setDashboard(null));
  }, [selectedProjectId, data.projects]);

  const project = dashboard?.project || findById(data.projects, selectedProjectId) || {};
  const rawTasks = dashboard?.tasks?.length ? dashboard.tasks : (data.tasks || []).filter((task) => String(task.project) === String(selectedProjectId));
  const tasks = rawTasks.map((task) => ({ ...(findById(data.tasks, task.id) || {}), ...task, project: task.project || task.project_id || selectedProjectId }));
  const milestones = dashboard?.milestones?.length ? dashboard.milestones : (data.milestones || []).filter((item) => String(item.project) === String(selectedProjectId));
  const team = dashboard?.team?.length ? dashboard.team : (data.teamAssignments || []).filter((item) => String(item.project) === String(selectedProjectId));
  const docs = dashboard?.documents?.length ? dashboard.documents : (data.projectDocuments || []).filter((item) => String(item.project) === String(selectedProjectId));
  const repos = (data.repositories || []).filter((repo) => String(repo.project) === String(selectedProjectId));
  const alerts = (dashboard?.alerts || data.alerts || []).filter((item) => !selectedProjectId || String(item.project) === String(selectedProjectId) || !item.project).slice(0, 10);
  const completedMilestones = milestones.filter((item) => String(item.status).toLowerCase() === "completed").length;
  const milestoneProgress = milestones.length ? Math.round((completedMilestones / milestones.length) * 100) : 0;

  const refresh = () => {
    reload();
    if (selectedProjectId) {
      apiGet(`/Project/dashboard/${selectedProjectId}/${encodeURIComponent(projectName(data, selectedProjectId) || "project")}/`).then(setDashboard).catch(() => {});
    }
  };

  const addDelay = async (milestoneId) => {
    if (!milestoneId) return;
    await apiPost("/Project/api/add-delay/", { milestone_id: milestoneId, delayed_days: 1 });
    refresh();
  };

  const completeMilestone = async (milestoneId) => {
    if (!milestoneId) return;
    await apiPost(`/Project/DeliveryMilestones/${milestoneId}/complete/`, {});
    refresh();
  };

  const createDefaultMilestones = async () => {
    if (!selectedProjectId) return;
    await apiPost(`/Project/ProjectWorkspaces/${selectedProjectId}/create-default-milestones/`, {});
    refresh();
  };

  const markAbsent = async (assignment) => {
    const employeeId = assignment.employee_id || assignment.employee;
    if (!employeeId) return;
    await apiPost("/Project/mark_absent/", { project: selectedProjectId, employee: employeeId, is_absent: !assignment.is_absent });
    refresh();
  };

  const removeMember = async (assignment) => {
    const employeeId = assignment.employee_id || assignment.employee;
    if (!employeeId) return;
    await apiPost("/Project/removeMember/", { project: selectedProjectId, employee: employeeId, reason: "Removed From Dashboard" });
    refresh();
  };

  const deleteTask = async (taskId) => {
    await apiPost("/Project/delete-task/", { task_id: taskId });
    refresh();
  };

  const shareProject = async () => {
    const url = `${PUBLIC_BASE_URL}${routeBase}/${selectedProjectId}/${encodeURIComponent(project.name || "project")}/`;
    if (navigator.clipboard) await navigator.clipboard.writeText(url);
  };

  const tasksByMilestone = useMemo(() => {
    const map = new Map();
    milestones.forEach((m) => map.set(String(m.id), []));
    map.set("__unassigned__", []);
    tasks.forEach((task) => {
      if (task.parent) return; 
      const ms = task.metadata?.milestone_id || task.milestone || task.metadata?.milestone;
      const key = ms && map.has(String(ms)) ? String(ms) : "__unassigned__";
      map.get(key).push(task);
    });
    return map;
  }, [tasks, milestones]);

  const subtasksOf = (taskId) => tasks.filter((task) => String(task.parent) === String(taskId));

  const filterTask = (task) => {
    if (taskFilter === "all") return true;
    const status = String(task.status || "").toLowerCase();
    if (taskFilter === "pending") return !["completed", "done", "closed"].includes(status);
    if (taskFilter === "completed") return ["completed", "done", "closed"].includes(status);
    return true;
  };

  const TaskRow = ({ task, depth = 0 }) => {
    const subs = subtasksOf(task.id);
    const visible = filterTask(task);
    const visibleSubs = subs.filter(filterTask);
    if (!visible && !visibleSubs.length) return null;
    return (
      <>
        {visible && (
          <tr className="Project-Task-Row" style={{ background: depth ? "#fafbff" : undefined }}>
            <td onClick={() => setSelectedTask(task)} style={{ cursor: "pointer", paddingLeft: 14 + depth * 22 }}>
              {depth > 0 ? <span className="Subtask-Arrow">↳</span> : <ChevronRight size={15} />}
              {task.title}
            </td>
            <td><Progress value={progressForTask(task, data.tasks)} /></td>
            <td>{avatar(employeeName(data, task.owner || task.owner_id))}</td>
            <td className={task.due_at && !isCompleted(task.status) && new Date(task.due_at) < new Date() ? "Danger-Text" : ""}>{formatDate(task.due_at)}</td>
            <td><AlertTriangle size={16} /> {task.priority || "Normal"}</td>
            <td>{Math.round(Number(task.bounty || 0))}</td>
            <td>
              <span className="Table-Actions">
                <button className="Soft-Button Small" onClick={() => setAddTaskFor({ parentTaskId: task.id, milestoneId: task.metadata?.milestone_id || null })} title="Add Sub Task"><Plus size={12} /></button>
                <button className="Soft-Button Small Danger" onClick={() => deleteTask(task.id)} title="Delete"><Trash2 size={12} /></button>
              </span>
            </td>
          </tr>
        )}
        {visibleSubs.map((sub) => <TaskRow key={sub.id} task={sub} depth={depth + 1} />)}
      </>
    );
  };

  return (
    <section className="Project-Screen Screen-Stack">
      <Disclosure title="Notifications" defaultOpen={false}>
        {alerts.map((item) => <div className="Notice-RowCompact" key={item.id}>{item.title || item.severity}</div>)}
        {!alerts.length && <EmptyState label="No Project Alerts Returned." />}
      </Disclosure>

      <section className="Project-Title-Bar">
        <div>
          <StatusPill>{project.priority || "P3"}</StatusPill>
          <strong>{project.name || "Project"}</strong>
          <StatusPill tone="green">{project.health || "On Track"}</StatusPill>
        </div>
        <select value={selectedProjectId} onChange={(event) => { setSelectedProjectId(event.target.value); navigate(`${routeBase}/${event.target.value}/${encodeURIComponent(projectName(data, event.target.value) || "project")}/`); }}>
          {(data.projects || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
        <div>
          <button className="Primary-Button Small" onClick={() => setCreateProjectOpen(true)}><Plus size={14} /> New Project</button>
          <button className="Outline-Button" onClick={() => setEditProject(true)}><Pencil size={16} /> Edit Details</button>
          <button className="Outline-Button" onClick={() => setFlagOpen(true)}><Flag size={16} /> Flag</button>
          <button className="Outline-Button" onClick={() => setDocumentOpen(true)}><FileText size={16} /> Documents</button>
          <button className="Outline-Button" onClick={() => setReposOpen(true)}><GitBranch size={16} /> Repositories ({repos.length})</button>
          <button className="Icon-Button" onClick={shareProject} title="Copy Project Link"><Share2 size={17} /></button>
        </div>
      </section>

      <Disclosure title="Key Project Details" defaultOpen>
        <SimpleTable columns={["Code", "Type", "Status", "Start", "End", "Milestones"]} rows={[[project.code, project.project_type, project.status, formatDate(project.starts_on), formatDate(project.ends_on), `${completedMilestones}/${milestones.length} (${milestoneProgress}%)`]]} />
      </Disclosure>

      <Panel
        title="Tasks (Grouped By Milestone)"
        right={
          <div className="Table-Actions">
            <select value={taskFilter} onChange={(event) => setTaskFilter(event.target.value)}>
              <option value="pending">Pending Tasks</option>
              <option value="completed">Completed Tasks</option>
              <option value="all">All Tasks</option>
            </select>
            <button className="Soft-Button Small" onClick={createDefaultMilestones}>Create Default Milestones</button>
            <button className="Primary-Button Small" onClick={() => setAddMilestoneOpen(true)}><Plus size={14} /> New Milestone</button>
          </div>
        }
      >
        {!milestones.length && (
          <EmptyState label="No Milestones Yet. Create Default Milestones Or Add A New One." />
        )}
        {[...milestones, { id: "__unassigned__", title: "Not Assigned", status: "Open" }].map((milestone) => {
          const list = tasksByMilestone.get(String(milestone.id)) || [];
          if (!list.length && milestone.id === "__unassigned__") return null;
          const done = list.filter((task) => ["completed", "done", "closed"].includes(String(task.status).toLowerCase())).length;
          return (
            <div className="Milestone-Block" key={milestone.id}>
              <div className="Milestone-Block-Head">
                <div>
                  <strong>{milestone.title}</strong>
                  <span className="Muted-Text"> ({done}/{list.length})</span>
                  {milestone.status && milestone.id !== "__unassigned__" && <StatusPill tone={String(milestone.status).toLowerCase() === "completed" ? "green" : "gold"}>{milestone.status}</StatusPill>}
                  {milestone.due_on && <span className="Muted-Text"> Due {formatDate(milestone.due_on)}</span>}
                </div>
                {milestone.id !== "__unassigned__" && (
                  <span className="Table-Actions">
                    <button className="Soft-Button Small" onClick={() => setAddTaskFor({ milestoneId: milestone.id })}><Plus size={13} /> Add Task</button>
                    <button className="Soft-Button Small" onClick={() => setMilestoneToEdit(milestone)}>Edit</button>
                    <button className="Soft-Button Small" onClick={() => completeMilestone(milestone.id)}>Complete</button>
                    <button className="Soft-Button Small Danger" onClick={() => addDelay(milestone.id)}>+1 Delay</button>
                  </span>
                )}
              </div>
              <table className="Erp-Table Project-Task-Table">
                <thead>
                  <tr>
                    <th>Task</th><th>Progress</th><th>Assignee</th><th>Due</th><th>Priority</th><th>Bounty</th><th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((task) => <TaskRow key={task.id} task={task} />)}
                </tbody>
              </table>
              {!list.length && milestone.id !== "__unassigned__" && (
                <div className="Milestone-Empty">
                  <span>No Tasks Yet.</span>
                  <button className="Soft-Button Small" onClick={() => setAddTaskFor({ milestoneId: milestone.id })}><Plus size={12} /> Add Task</button>
                </div>
              )}
            </div>
          );
        })}
      </Panel>

      <Disclosure title="Team Members" defaultOpen>
        <div className="Table-Actions Top-Actions">
          <button className="Soft-Button Small" onClick={() => setAddMemberOpen(true)}><Plus size={13} /> Add Member</button>
        </div>
        <SimpleTable
          columns={["Name", "Role", "Availability", "Contact", "Repos / GitHub", "Action", "EOD"]}
          rows={team.map((assignment) => {
            const empId = assignment.employee_id || assignment.employee;
            const upcomingLeave = (data.leaveRequests || []).find((lr) => {
              const match = String(lr.employee || lr.employee_id) === String(empId);
              const approved = String(lr.status || "").toLowerCase() === "approved";
              const future = lr.starts_on && new Date(lr.starts_on) >= new Date(new Date().toDateString());
              return match && approved && future;
            });
            return [
              <span key="name" className="Member-Name-Wrap">
                {upcomingLeave && <span className="Leave-Dot" title={`Leave: ${upcomingLeave.starts_on}`}><CalendarDays size={12} /></span>}
                {assignment.employee_name || employeeName(data, empId)}
              </span>,
              assignment.role,
              assignment.is_absent ? "Absent" : assignment.status === "Active" ? "Available" : assignment.status,
              employeeContact(data, empId),
              <MemberRepoIcon key="repo" assignment={assignment} repos={repos} data={data} />,
              <span className="Table-Actions" key="action">
                <button className="Soft-Button Small" onClick={() => markAbsent(assignment)}>{assignment.is_absent ? <UserCheck size={13} /> : <UserX size={13} />}{assignment.is_absent ? " Mark Available" : " Mark Absent"}</button>
                <button className="Soft-Button Small Danger" onClick={() => removeMember(assignment)}><X size={13} /></button>
              </span>,
              <button className="Primary-Button Small" key="eod" onClick={() => setEodEmployee(assignment)}><CalendarDays size={13} /> View</button>,
            ];
          })}
        />
      </Disclosure>

      <Disclosure title="Documents" defaultOpen={false}>
        <SimpleTable
          columns={["Title", "Type", "Pinned", "Reference"]}
          rows={docs.map((doc) => [doc.title, doc.document_type, doc.is_pinned ? "Yes" : "No", doc.storage_reference || doc.file_id || doc.metadata?.url || "-"])}
        />
        {!docs.length && <EmptyState label="No Project Documents Returned." />}
      </Disclosure>

      {selectedTask && <TaskDetailModal task={selectedTask} data={data} onClose={() => setSelectedTask(null)} reload={refresh} />}
  {createProjectOpen && <CreateProjectModal defaultProjectType={kind === "marketing" ? "Marketing" : "Development"} data={data} onClose={() => setCreateProjectOpen(false)} reload={(newId, newName) => { refresh(); if (newId) { setSelectedProjectId(String(newId)); navigate(`${routeBase}/${newId}/${encodeURIComponent(newName || "project")}/`); } }} />}
      {editProject && <EditProjectModal project={project} onClose={() => setEditProject(false)} reload={refresh} />}
      {flagOpen && <FlagProjectModal project={project} onClose={() => setFlagOpen(false)} reload={refresh} />}
      {documentOpen && <DocumentModal project={project} onClose={() => setDocumentOpen(false)} reload={refresh} />}
      {reposOpen && <RepositoriesModal project={project} repos={repos} onClose={() => setReposOpen(false)} reload={refresh} />}
      {milestoneToEdit && <MilestoneEditModal milestone={milestoneToEdit} onClose={() => setMilestoneToEdit(null)} reload={refresh} />}
      {addMilestoneOpen && <AddMilestoneModal project={project} onClose={() => setAddMilestoneOpen(false)} reload={refresh} />}
      {addTaskFor && <AddTaskModal project={project} team={team} milestones={milestones} data={data} initial={addTaskFor} onClose={() => setAddTaskFor(null)} reload={refresh} />}
      {addMemberOpen && <AddMemberModal project={project} data={data} onClose={() => setAddMemberOpen(false)} reload={refresh} />}
      {eodEmployee && <TeamEodModal assignment={eodEmployee} data={data} onClose={() => setEodEmployee(null)} />}
    </section>
  );
}

function MemberRepoIcon({ assignment, repos, data }) {
  const [open, setOpen] = useState(false);
  const employeeId = assignment.employee_id || assignment.employee;
  const githubUser = (data.employees || []).find((emp) => String(emp.id) === String(employeeId))?.github_username || "";
  const memberRepos = repos.filter((repo) => {
    const allowed = repo.metadata?.assigned_employees || [];
    return allowed.length === 0 || allowed.map(String).includes(String(employeeId));
  });
  // No-PushesSignal: FromGitActivitySnapshotsCommit_Count===0ForAnyRepoToday
  const todayStr = isoDate(new Date());
  const noPushRepos = memberRepos.filter((repo) => {
    const Activity = (data.gitActivitySnapshots || []).find((snap) => String(snap.repository) === String(repo.id) && String(snap.snapshot_date) === todayStr);
    return Activity && Number(Activity.commit_count || 0) === 0;
  });

  return (
    <span className="Member-Repo-Icon" onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <GitBranch size={14} className={noPushRepos.length ? "Danger-Text" : ""} />
      {open && (
        <span className="Member-Repo-Tooltip">
          {githubUser && <small>@{githubUser}</small>}
          {memberRepos.length ? memberRepos.map((repo) => <span key={repo.id}>{repo.name}</span>) : <span>No Repositories Linked.</span>}
          {noPushRepos.length > 0 && <small className="Danger-Text">No GitHub Pushes Today.</small>}
        </span>
      )}
    </span>
  );
}

function CreateProjectModal({ data, onClose, reload, defaultProjectType = "Development" }) {
  const [form, setForm] = useState({ name: "", code: "", project_type: defaultProjectType, priority: "P3", status: "Active", health: "On Track", starts_on: isoDate(new Date()), ends_on: "" });
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      const response = await apiPost("/Project/ProjectWorkspaces/", form);
      reload(response?.id, response?.name || form.name);
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="Create New Project" onClose={onClose} wide>
      <div className="Form-Grid Two Modal-Form">
        <label>Name<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
        <label>Code<input value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value })} placeholder="PRJ-001" /></label>
        <label>Type<select value={form.project_type} onChange={(event) => setForm({ ...form, project_type: event.target.value })}><option>Development</option><option>Marketing</option><option>Operations</option><option>Internal</option></select></label>
        <label>Priority<select value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value })}><option>P1</option><option>P2</option><option>P3</option><option>P4</option></select></label>
        <label>Status<select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}><option>Active</option><option>On Hold</option><option>Completed</option></select></label>
        <label>Health<select value={form.health} onChange={(event) => setForm({ ...form, health: event.target.value })}><option>On Track</option><option>At Risk</option><option>Blocked</option></select></label>
        <label>Starts On<input type="date" value={form.starts_on} onChange={(event) => setForm({ ...form, starts_on: event.target.value })} /></label>
        <label>Ends On<input type="date" value={form.ends_on} onChange={(event) => setForm({ ...form, ends_on: event.target.value })} /></label>
      </div>
      <button className="Primary-Button" onClick={save} disabled={busy || !form.name || !form.code}>Create Project</button>
    </Modal>
  );
}

function EditProjectModal({ project, onClose, reload }) {
  const [form, setForm] = useState({
    name: project.name || "",
    code: project.code || "",
    project_type: project.project_type || "Development",
    status: project.status || "Active",
    health: project.health || "On Track",
    priority: project.priority || "P3",
    starts_on: project.starts_on || "",
    ends_on: project.ends_on || "",
  });

  const save = async () => {
    await apiPost("/Project/update_details/", { project_id: project.id, ...form });
    reload();
    onClose();
  };

  return (
    <Modal title="Edit Project Details" onClose={onClose} wide>
      <div className="Form-Grid Two Modal-Form">
        <label>Name<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>
        <label>Code<input value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value })} /></label>
        <label>Type<input value={form.project_type} onChange={(event) => setForm({ ...form, project_type: event.target.value })} /></label>
        <label>Priority<input value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value })} /></label>
        <label>Status<input value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })} /></label>
        <label>Health<input value={form.health} onChange={(event) => setForm({ ...form, health: event.target.value })} /></label>
        <label>Starts On<input type="date" value={form.starts_on || ""} onChange={(event) => setForm({ ...form, starts_on: event.target.value })} /></label>
        <label>Ends On<input type="date" value={form.ends_on || ""} onChange={(event) => setForm({ ...form, ends_on: event.target.value })} /></label>
      </div>
      <button className="Primary-Button" onClick={save} disabled={!form.name}>Save Project</button>
    </Modal>
  );
}

function AddTaskModal({ project, team, milestones, data, initial, onClose, reload }) {
  const firstEmployee = team[0]?.employee_id || team[0]?.employee || "";
  const [form, setForm] = useState({
    title: "",
    owner: firstEmployee,
    due_at: isoDate(new Date()),
    priority: "Normal",
    bounty: 0,
    description: "",
    milestone_id: initial?.milestoneId ? String(initial.milestoneId) : "",
    parent: initial?.parentTaskId ? String(initial.parentTaskId) : "",
  });
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      const created = await apiPost("/Project/add_task/", {
        project: project.id,
        title: form.title,
        owner: form.owner || null,
        parent: form.parent || null,
        description: form.description,
        priority: form.priority,
        bounty: Number(form.bounty) || 0,
      });
      const taskId = created?.task?.id || created?.id;
      if (taskId && (form.due_at || form.milestone_id)) {
        await apiPost("/Project/update-task/", {
          task_id: taskId,
          due_at: form.due_at || null,
          metadata: { milestone_id: form.milestone_id || null },
        });
      }
      reload();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title={initial?.parentTaskId ? "Add Sub Task" : "Add Task"} onClose={onClose} wide>
      <div className="Form-Grid Two Modal-Form">
        <label>Title<input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></label>
        <label>Assignee<select value={form.owner} onChange={(event) => setForm({ ...form, owner: event.target.value })}><option value="">Not Assigned</option>{team.map((item) => <option key={item.id} value={item.employee_id || item.employee}>{item.employee_name || employeeName(data, item.employee_id || item.employee)}</option>)}</select></label>
        <label>Milestone<select value={form.milestone_id} onChange={(event) => setForm({ ...form, milestone_id: event.target.value })}><option value="">Not Assigned</option>{milestones.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
        <label>Due Date<input type="date" value={form.due_at} onChange={(event) => setForm({ ...form, due_at: event.target.value })} /></label>
        <label>Priority<select value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value })}><option>Low</option><option>Normal</option><option>High</option><option>Urgent</option></select></label>
        <label>Bounty<input type="number" value={form.bounty} onChange={(event) => setForm({ ...form, bounty: event.target.value })} /></label>
      </div>
      <label>Description<textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
      <button className="Primary-Button" onClick={save} disabled={busy || !form.title}>{initial?.parentTaskId ? "Create Sub Task" : "Create Task"}</button>
    </Modal>
  );
}

function FlagProjectModal({ project, onClose, reload }) {
  const [form, setForm] = useState({ severity: "High", title: "Project Risk", description: "" });

  const save = async () => {
    await apiPost(`/Project/ProjectWorkspaces/${project.id}/raise-alert/`, form);
    reload();
    onClose();
  };

  return (
    <Modal title="Flag Project Risk" onClose={onClose}>
      <div className="Form-Grid Two Modal-Form">
        <label>Severity<select value={form.severity} onChange={(event) => setForm({ ...form, severity: event.target.value })}><option>Low</option><option>Medium</option><option>High</option><option>Critical</option></select></label>
        <label>Title<input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></label>
      </div>
      <label>Description<textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
      <button className="Primary-Button" onClick={save} disabled={!form.title}>Create Alert</button>
    </Modal>
  );
}

function DocumentModal({ project, onClose, reload }) {
  const [form, setForm] = useState({ title: "", document_type: "General", storage_reference: "" });

  const save = async () => {
    await apiPost("/Project/create-document/", { project: project.id, ...form });
    reload();
    onClose();
  };

  return (
    <Modal title="Create Project Document" onClose={onClose}>
      <label>Title<input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></label>
      <label>Type<input value={form.document_type} onChange={(event) => setForm({ ...form, document_type: event.target.value })} /></label>
      <label>Reference Or URL<input value={form.storage_reference} onChange={(event) => setForm({ ...form, storage_reference: event.target.value })} /></label>
      <button className="Primary-Button" onClick={save} disabled={!form.title}>Save Document</button>
    </Modal>
  );
}

function RepositoriesModal({ project, repos, onClose, reload }) {
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ name: "", owner: "", default_branch: "main", provider: "GitHub" });
  const [busy, setBusy] = useState(false);

  const create = async () => {
    setBusy(true);
    try {
      await apiPost("/Project/create-repo/", { project: project.id, ...form });
      reload();
      setCreating(false);
      setForm({ name: "", owner: "", default_branch: "main", provider: "GitHub" });
    } finally {
      setBusy(false);
    }
  };

  const revoke = async (repo) => {
    await apiPost("/Project/revoke-repo/", { repository_id: repo.id });
    reload();
  };

  return (
    <Modal title="Repositories" onClose={onClose} wide>
      {!creating && (
        <>
          <ul className="Repo-List">
            {repos.map((repo) => (
              <li key={repo.id}>
                <span><GitBranch size={13} /> {repo.full_name || `${repo.owner}/${repo.name}` || repo.name}</span>
                <span className="Muted-Text">{repo.access_status}</span>
                <span className="Table-Actions">
                  {repo.full_name && <a className="Soft-Button Small" href={`https://github.com/${repo.full_name}`} target="_blank" rel="noreferrer"><ExternalLink size={12} /></a>}
                  <button className="Soft-Button Small Danger" onClick={() => revoke(repo)}>Revoke</button>
                </span>
              </li>
            ))}
            {!repos.length && <li className="Muted-Text">No Repositories Yet.</li>}
          </ul>
          <div className="Modal-Actions">
            <button className="Primary-Button" onClick={() => setCreating(true)}><Plus size={14} /> Create New Repository</button>
            <button className="Soft-Button" onClick={onClose}>Close</button>
          </div>
        </>
      )}
      {creating && (
        <>
          <div className="Form-Grid Two Modal-Form">
            <label>Provider<select value={form.provider} onChange={(event) => setForm({ ...form, provider: event.target.value })}><option>GitHub</option><option>GitLab</option><option>Bitbucket</option></select></label>
            <label>Owner / Organization<input value={form.owner} onChange={(event) => setForm({ ...form, owner: event.target.value })} placeholder="atgworld" /></label>
            <label>Repository Name<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="Intranet-V2" /></label>
            <label>Default Branch<input value={form.default_branch} onChange={(event) => setForm({ ...form, default_branch: event.target.value })} /></label>
          </div>
          <div className="Modal-Actions">
            <button className="Primary-Button" onClick={create} disabled={busy || !form.name}>Create</button>
            <button className="Soft-Button" onClick={() => setCreating(false)}>Back</button>
          </div>
        </>
      )}
    </Modal>
  );
}

function MilestoneEditModal({ milestone, onClose, reload }) {
  const [form, setForm] = useState({ title: milestone.title || "", status: milestone.status || "Open", due_on: milestone.due_on || "", delayed_days: milestone.delayed_days || 0 });

  const save = async () => {
    await apiPost("/Project/update_milestone/", { milestone_id: milestone.id, ...form });
    reload();
    onClose();
  };

  return (
    <Modal title="Edit Milestone" onClose={onClose}>
      <label>Title<input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></label>
      <label>Status<select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}><option>Open</option><option>In Progress</option><option>Completed</option><option>Delayed</option></select></label>
      <label>Due On<input type="date" value={form.due_on || ""} onChange={(event) => setForm({ ...form, due_on: event.target.value })} /></label>
      <label>Delayed Days<input type="number" value={form.delayed_days} onChange={(event) => setForm({ ...form, delayed_days: event.target.value })} /></label>
      <button className="Primary-Button" onClick={save} disabled={!form.title}>Save Milestone</button>
    </Modal>
  );
}

function AddMilestoneModal({ project, onClose, reload }) {
  const [form, setForm] = useState({ title: "", status: "Open", due_on: "", project: project.id });
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      await apiPost("/Project/DeliveryMilestones/", form);
      reload();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="New Milestone" onClose={onClose}>
      <label>Title<input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="M1, 1st Vertical, Etc." /></label>
      <label>Status<select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}><option>Open</option><option>In Progress</option><option>Completed</option><option>Delayed</option></select></label>
      <label>Due On<input type="date" value={form.due_on} onChange={(event) => setForm({ ...form, due_on: event.target.value })} /></label>
      <button className="Primary-Button" onClick={save} disabled={busy || !form.title}>Create Milestone</button>
    </Modal>
  );
}

function AddMemberModal({ project, data, onClose, reload }) {
  const [form, setForm] = useState({ employee: "", role: "Member", allocation_percent: 100 });
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      await apiPost("/Project/addMember/", { project: project.id, ...form });
      reload();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="Add Team Member" onClose={onClose}>
      <label>Employee<select value={form.employee} onChange={(event) => setForm({ ...form, employee: event.target.value })}><option value="">Select Employee</option>{(data.employees || []).map((emp) => <option key={emp.id} value={emp.id}>{emp.display_name}</option>)}</select></label>
      <label>Role<input value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })} /></label>
      <label>Allocation %<input type="number" value={form.allocation_percent} onChange={(event) => setForm({ ...form, allocation_percent: event.target.value })} /></label>
      <button className="Primary-Button" onClick={save} disabled={busy || !form.employee}>Add Member</button>
    </Modal>
  );
}

function TeamEodModal({ assignment, data, onClose }) {
  const employeeId = assignment.employee_id || assignment.employee;
  const rows = (data.dailyStatus || []).filter((item) => String(item.employee) === String(employeeId)).slice(0, 20);

  return (
    <Modal title={`${assignment.employee_name || employeeName(data, employeeId)} EOD Reports`} onClose={onClose} wide>
      <SimpleTable columns={["Date", "Summary"]} rows={rows.map((item) => [formatDate(item.status_date), item.summary || "No Summary Text."])} />
      {!rows.length && <EmptyState label="No EOD Entries Returned For This Team Member." />}
    </Modal>
  );
}

function TaskDetailModal({ task, data, onClose, reload }) {
  const [description, setDescription] = useState(task.description || "");
  const [linkUrl, setLinkUrl] = useState(task.metadata?.task_link || "");
  const [prForm, setPrForm] = useState({ name: "", url: "" });
  const [status, setStatus] = useState(task.status || "Open");
  const [dueDate, setDueDate] = useState(task.due_at ? task.due_at.split("T")[0] : "");
  const [priority, setPriority] = useState(task.priority || "Normal");
  const [bounty, setBounty] = useState(task.bounty || 0);
  const [assignee, setAssignee] = useState(task.owner || task.owner_id || "");
  const team = (data.teamAssignments || []).filter((item) => String(item.project) === String(task.project));
  const activities = (data.taskActivities || []).filter((item) => String(item.work_item) === String(task.id));
  const prLinks = useMemo(() => (Array.isArray(task.metadata?.prs) ? task.metadata.prs : []), [task.metadata]);
  const subs = (data.tasks || []).filter((item) => String(item.parent) === String(task.id));

  const saveDescription = async () => {
    await apiPost(`/Project/update-description/${task.id}/`, { description });
    reload();
  };

  const saveStatus = async () => {
    await apiPost("/Project/update-task/", { task_id: task.id, status });
    reload();
  };

  const saveLink = async () => {
    if (!linkUrl) return;
    await apiPost("/Project/task/save_link/", { task_id: task.id, url: linkUrl });
    reload();
  };

  const savePr = async () => {
    if (!prForm.url) return;
    await apiPost("/Project/update-task/", {
      task_id: task.id,
      metadata: { ...(task.metadata || {}), prs: [...prLinks, { name: prForm.name || prForm.url, url: prForm.url, state: "Manual" }] },
    });
    setPrForm({ name: "", url: "" });
    reload();
  };

  const saveDueDate = async () => {
    await apiPost("/Project/update-duedate/", { task_id: task.id, due_date: dueDate });
    reload();
  };

  const saveAssignee = async () => {
    await apiPost("/Project/save-assignee/", { task_id: task.id, employee: assignee || null });
    reload();
  };

  const savePriority = async () => {
    await apiPost("/Project/update-priority/", { task_id: task.id, priority });
    reload();
  };

  const saveBounty = async () => {
    await apiPost("/Project/update-bounty/", { task_id: task.id, bounty: Number(bounty) || 0 });
    reload();
  };

  return (
    <Modal onClose={onClose} wide title={<><a>{projectName(data, task.project) || "Project"}</a> / Task</>}>
      <div className="Task-Modal-Grid">
        <section>
          <StatusPill tone="blue">Task</StatusPill>
          <h2>{task.title}</h2>
          <dl className="Details-Grid">
            <div><dt>Status</dt><dd>
              <span className="Inline-Form-Row">
                <select value={status} onChange={(event) => setStatus(event.target.value)}><option>Open</option><option>In Progress</option><option>Blocked</option><option>Completed</option></select>
                <button className="Soft-Button Small" onClick={saveStatus}>Save</button>
              </span>
            </dd></div>
            <div><dt>Created</dt><dd>{formatDate(task.created_at)}</dd></div>
            <div><dt>Due Date</dt><dd>
              <span className="Inline-Form-Row">
                <input type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
                <button className="Soft-Button Small" onClick={saveDueDate}>Save</button>
              </span>
            </dd></div>
            <div><dt>Assignee</dt><dd>
              <span className="Inline-Form-Row">
                <select value={assignee} onChange={(event) => setAssignee(event.target.value)}>
                  <option value="">Not Assigned</option>
                  {team.map((item) => (
                    <option key={item.id} value={item.employee_id || item.employee}>
                      {item.employee_name || employeeName(data, item.employee_id || item.employee)}
                    </option>
                  ))}
                </select>
                <button className="Soft-Button Small" onClick={saveAssignee}>Save</button>
              </span>
            </dd></div>
            <div><dt>Priority</dt><dd>
              <span className="Inline-Form-Row">
                <select value={priority} onChange={(event) => setPriority(event.target.value)}>
                  <option>Low</option><option>Normal</option><option>High</option><option>Urgent</option>
                </select>
                <button className="Soft-Button Small" onClick={savePriority}>Save</button>
              </span>
            </dd></div>
            <div><dt>Bounty</dt><dd>
              <span className="Inline-Form-Row">
                <input type="number" value={bounty} onChange={(event) => setBounty(event.target.value)} style={{ width: "80px" }} />
                <button className="Soft-Button Small" onClick={saveBounty}>Save</button>
              </span>
            </dd></div>
          </dl>
          <label>Description<textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Add A Description..." /></label>
          <button className="Primary-Button" onClick={saveDescription}>Save Description</button>

          <h4>Sub Tasks ({subs.length})</h4>
          {subs.length ? subs.map((sub) => <div className="Pr-Row" key={sub.id}><span>↳ {sub.title}</span> <span>({sub.status})</span></div>) : <EmptyState label="No Sub Tasks." />}

          <h4>Links</h4>
          <div className="Inline-Form-Row">
            <input value={linkUrl} onChange={(event) => setLinkUrl(event.target.value)} placeholder="https://..." />
            <button className="Primary-Button Small" onClick={saveLink}><LinkIcon size={13} /> Add Link</button>
          </div>
          {task.metadata?.task_link && <a className="Pr-Row" href={task.metadata.task_link} target="_blank" rel="noreferrer"><ExternalLink size={13} /> {task.metadata.task_link}</a>}

          <h4>Pull Requests</h4>
          <div className="Inline-Form-Row">
            <input value={prForm.name} onChange={(event) => setPrForm({ ...prForm, name: event.target.value })} placeholder="PR Title" />
            <input value={prForm.url} onChange={(event) => setPrForm({ ...prForm, url: event.target.value })} placeholder="PR URL" />
            <button className="Primary-Button Small" onClick={savePr}><GitPullRequest size={13} /> Add PR</button>
          </div>
          {prLinks.map((pr) => <div className="Pr-Row" key={pr.url}><a href={pr.url} target="_blank" rel="noreferrer">{pr.name}</a> <span>({pr.state})</span></div>)}
        </section>
        <aside>
          <h3>Activity</h3>
          {activities.map((item) => <div className="Activity-Row" key={item.id}><span>{item.message || item.Activity_type}</span><time>{formatDate(item.created_at)}</time></div>)}
          {!activities.length && <EmptyState label="No Task Activity Returned." />}
        </aside>
      </div>
    </Modal>
  );
}
