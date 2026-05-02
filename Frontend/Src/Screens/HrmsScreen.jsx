import React, { useEffect, useState } from "react";
import { AlertTriangle, ChevronDown, ChevronRight, Menu, MoreHorizontal, Search } from "lucide-react";

import {
  Disclosure,
  MilestoneRail,
  Modal,
  Panel,
  SimpleTable,
  StatusPill,
  Tabs,
} from "./Shared/ScreenComponents.jsx";
import {
  calendarDays,
  filterForEmployee,
  findDailyStatus,
  formatDate,
  groupBy,
  indexById,
  isCompleted,
  isoDate,
  lastDays,
  money,
  projectName,
  toggleSet,
} from "./Shared/ScreenUtils.jsx";

export function HrmsScreen({ data, reload }) {
  const [tab, setTab] = useState("team");
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState(new Set());
  const [eodEmployee, setEodEmployee] = useState(null);
  const employees = (data.employees || []).filter((employee) => employee.display_name?.toLowerCase().includes(search.toLowerCase()) || employee.department_name?.toLowerCase().includes(search.toLowerCase()));
  const departments = groupBy(employees, (employee) => employee.department_name || "Unassigned");

  useEffect(() => {
    if (!expanded.size && departments.size) setExpanded(new Set([departments.keys().next().value]));
  }, [departments, expanded.size]);

  const toggleAll = () => {
    if (expanded.size === departments.size) setExpanded(new Set());
    else setExpanded(new Set(Array.from(departments.keys())));
  };

  return (
    <section className="legacy-screen hrms-screen">
      <Disclosure title="Notifications" defaultOpen={false}>
        {(data.notifications || []).slice(0, 4).map((item) => <div className="notice-row compact" key={item.id}>{item.title}</div>)}
      </Disclosure>
      <Tabs value={tab} onChange={setTab} items={[["team", "Team"], ["sanity", "Project Sanity"], ["finance", "Project Finance"]]} />
      {tab === "team" && (
        <>
          <div className="toolbar-row"><div className="search-box"><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search Here..." /><Search size={20} /></div><button className="outline-button" onClick={toggleAll}><Menu size={15} /> Expand All</button></div>
          <div className="department-stack">
            {Array.from(departments.entries()).map(([departmentName, rows]) => {
              const assigned = rows.filter((item) => item.status === "Active").length;
              const bench = rows.filter((item) => item.status === "OnBench").length;
              const isOpen = expanded.has(departmentName);
              return (
                <section className="department-card" key={departmentName}>
                  <button className="department-head" onClick={() => setExpanded(toggleSet(expanded, departmentName))}>
                    <strong>{departmentName} ({rows.length})</strong>
                    <span><StatusPill tone="green">Assigned: {assigned}</StatusPill><StatusPill tone="red">Not Assigned: {Math.max(rows.length - assigned - bench, 0)}</StatusPill><StatusPill tone="slate">On-Bench: {bench}</StatusPill>{isOpen ? <ChevronDown /> : <ChevronRight />}</span>
                  </button>
                  {isOpen && <HrmsTeamTable rows={rows} data={data} setEodEmployee={setEodEmployee} />}
                </section>
              );
            })}
          </div>
        </>
      )}
      {tab === "sanity" && <ProjectSanity data={data} />}
      {tab === "finance" && <ProjectFinance data={data} />}
      {eodEmployee && <EodSummaryModal employee={eodEmployee} data={data} onClose={() => setEodEmployee(null)} reload={reload} />}
    </section>
  );
}

function HrmsTeamTable({ rows, data, setEodEmployee }) {
  const days = lastDays(7);
  const projectMap = indexById(data.projects);
  return (
    <div className="table-wrap tint">
      <table className="erp-table hrms-table">
        <thead><tr><th>Name / Joining Date</th><th>Skill Level</th><th>Project</th><th>Remarks</th><th>BA</th><th>BC (This Month)</th><th>EOD Summary & Attendance</th><th /></tr></thead>
        <tbody>
          {rows.map((employee) => {
            const assignments = (data.teamAssignments || []).filter((item) => String(item.employee) === String(employee.id));
            const skills = (data.userSkills || []).filter((item) => String(item.employee) === String(employee.id));
            const employeeProjects = assignments.map((item) => projectMap.get(String(item.project))?.name).filter(Boolean);
            return (
              <tr key={employee.id}>
                <td><div className="plain-name"><strong>{employee.display_name}</strong><small>{formatDate(employee.joined_on)}</small></div></td>
                <td><span className="skill-badge"><AlertTriangle size={12} />{skills[0]?.proficiency > 2 ? "Advanced" : "Basic"}</span></td>
                <td>{employeeProjects.length ? employeeProjects.slice(0, 4).map((name) => <span className="stacked" key={name}>{name}</span>) : "-"}</td>
                <td><textarea defaultValue={employee.profile_payload?.remarks || ""} /></td>
                <td>0</td><td>0</td>
                <td><div className="attendance-mini">{days.map((day) => {
                  const status = findDailyStatus(data.dailyStatus, employee.id, day.iso);
                  return <button key={day.iso} className={status ? "green" : "gold"} onClick={() => setEodEmployee({ ...employee, selectedDate: day.iso })}>{day.label}</button>;
                })}</div><button className="view-more" onClick={() => setEodEmployee(employee)}>View More <ChevronDown size={17} /></button></td>
                <td><button className="icon-button"><MoreHorizontal size={18} /></button></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function EodSummaryModal({ employee, data, onClose }) {
  const [tab, setTab] = useState("calendar");
  const statuses = (data.dailyStatus || []).filter((item) => String(item.employee) === String(employee.id));
  const tasks = filterForEmployee(data.tasks, employee.id);
  const month = new Date(2026, 4, 1);
  const monthDays = calendarDays(month);
  return (
    <Modal onClose={onClose} wide title={`${employee.display_name}'s EOD Summary`}>
      <Tabs value={tab} onChange={setTab} items={[["calendar", "Calendar"], ["bounties", "Bounties"], ["summaries", "EOD Summaries"]]} />
      {tab === "calendar" && <div className="calendar-grid"><div className="calendar-nav"><button className="outline-button">Previous</button><h3>May 2026</h3><button className="outline-button">Next</button></div>{["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => <strong key={day}>{day}</strong>)}{monthDays.map((day, index) => day ? <button key={index} className={findDailyStatus(statuses, employee.id, day.iso) ? "submitted" : day.future ? "future" : "empty"}>{day.day}<small>{day.iso === isoDate(new Date()) ? "Today" : ""}</small></button> : <span key={index} />)}</div>}
      {tab === "bounties" && <SimpleTable columns={["Date", "Project", "Task", "Status", "Bounty"]} rows={tasks.slice(0, 10).map((task) => [formatDate(task.updated_at || task.created_at), projectName(data, task.project), task.title, task.status, money(task.bounty)])} />}
      {tab === "summaries" && <SimpleTable columns={["Date", "Project Name", "EOD Summary"]} rows={lastDays(7).map((day) => { const status = findDailyStatus(statuses, employee.id, day.iso); return [day.iso, status?.metadata?.project || "-", status ? status.summary : "No EOD Submitted Today"]; })} />}
    </Modal>
  );
}

function ProjectSanity({ data }) {
  const milestonesByProject = groupBy(data.milestones || [], (item) => String(item.project));
  return (
    <div className="sanity-list">
      {(data.projects || []).map((project) => {
        const milestones = milestonesByProject.get(String(project.id)) || [];
        return <section className="sanity-row" key={project.id}><button><ChevronDown size={18} /></button><StatusPill>{project.priority}</StatusPill><strong>{project.name}</strong><span>{project.project_type || project.status}</span><MilestoneRail milestones={milestones} /><b className={project.health === "Escalated" ? "danger-text" : ""}>{project.health || "Null"}</b></section>;
      })}
    </div>
  );
}

function ProjectFinance({ data }) {
  return <Panel title="Project Finance"><SimpleTable columns={["Project", "Health", "Team", "Tasks", "Bounty"]} rows={(data.projects || []).map((project) => [project.name, project.health, (data.teamAssignments || []).filter((item) => item.project === project.id).length, (data.tasks || []).filter((task) => task.project === project.id).length, money((data.tasks || []).filter((task) => task.project === project.id).reduce((sum, task) => sum + Number(task.bounty || 0), 0))])} /></Panel>;
}