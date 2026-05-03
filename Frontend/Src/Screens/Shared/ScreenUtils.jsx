import React from "react";

export function groupBy(items, getKey) {
  const map = new Map();
  (items || []).forEach((item) => {
    const key = getKey(item) || "Other";
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(item);
  });
  return map;
}

export function indexById(items = []) {
  return new Map(items.map((item) => [String(item.id), item]));
}

export function findById(items = [], id) {
  return items.find((item) => String(item.id) === String(id));
}

export function filterForEmployee(tasks = [], employeeId) {
  if (!employeeId) return tasks;
  return tasks.filter((task) => String(task.owner) === String(employeeId) || String(task.owner_id) === String(employeeId) || String(task.assignee) === String(employeeId));
}

export function projectName(data, id) {
  return findById(data.projects || [], id)?.name || "";
}

export function employeeName(data, id) {
  return findById(data.employees || [], id)?.display_name || findById(data.employees || [], id)?.username || "-";
}

export function employeeContact(data, id) {
  const employee = findById(data.employees || [], id);
  return employee ? `${employee.email || ""} ${employee.contact_number || ""}` : "";
}

export function avatar(name = "?") {
  return <span className="avatar">{String(name).trim().charAt(0).toUpperCase() || "?"}</span>;
}

export function isCompleted(status = "") {
  return ["completed", "complete", "done", "passed", "submitted", "closed"].includes(String(status).toLowerCase());
}

function boundedProgress(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return null;
  return Math.min(Math.max(number, 0), 100);
}

function progressFromStatus(status = "") {
  const normalized = String(status || "").toLowerCase();
  if (isCompleted(normalized)) return 100;
  if (normalized.includes("review") || normalized.includes("submit")) return 85;
  if (normalized.includes("progress") || normalized.includes("working")) return 60;
  if (normalized.includes("block") || normalized.includes("delay") || normalized.includes("hold")) return 30;
  if (normalized.includes("open") || normalized.includes("assign") || normalized.includes("sent")) return 20;
  return 0;
}

export function progressForTask(task, allTasks = []) {
  const explicitProgress = boundedProgress(task?.metadata?.progress ?? task?.progress_percent ?? task?.progress ?? task?.percentage);
  if (explicitProgress !== null) return explicitProgress;
  const subtasks = allTasks.filter((item) => String(item.parent) === String(task.id));
  if (!subtasks.length) return progressFromStatus(task?.status);
  return subtasks.reduce((sum, item) => sum + progressForTask(item, allTasks), 0) / subtasks.length;
}

export function findDailyStatus(statuses = [], employeeId, iso) {
  return statuses.find((item) => String(item.employee) === String(employeeId) && String(item.status_date).slice(0, 10) === iso);
}

export function lastDays(count) {
  const today = new Date();
  return Array.from({ length: count }, (_, index) => {
    const date = new Date(today);
    date.setDate(today.getDate() - (count - index - 1));
    return { iso: isoDate(date), label: String(date.getDate()) };
  });
}

export function calendarDays(monthDate) {
  const first = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1);
  const last = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0);
  const days = Array.from({ length: first.getDay() }, () => null);
  for (let day = 1; day <= last.getDate(); day += 1) {
    const date = new Date(monthDate.getFullYear(), monthDate.getMonth(), day);
    days.push({ day, iso: isoDate(date), future: date > new Date() });
  }
  return days;
}

export function isoDate(value) {
  return value.toISOString().slice(0, 10);
}

export function formatDate(value) {
  if (!value) return "None";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "2-digit" });
}

export function formatDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export function humanDate(value) {
  return value.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
}

export function money(value) {
  const number = Number(value || 0);
  return Number.isInteger(number) ? String(number) : number.toFixed(2);
}

export function toggleSet(source, value) {
  const next = new Set(source);
  if (next.has(value)) next.delete(value);
  else next.add(value);
  return next;
}

export function numberOrNull(value) {
  return value === undefined || value === null || value === "" ? null : Number(value);
}

export function getLeadRows(data) {
  const lmsRows = data.leadRows || [];
  if (lmsRows.length) return lmsRows;
  return (data.leadAccounts || []).map((lead) => ({
    ...lead,
    owner_id: lead.owner,
    owner_name: employeeName(data, lead.owner),
    notes_count: (data.leadNotes || []).filter((note) => String(note.lead) === String(lead.id)).length,
  }));
}

export function leadSource(lead = {}) {
  return lead.source || lead.origin || lead.metadata?.origin || "Unknown";
}

export function leadStage(lead = {}) {
  return lead.stage || lead.workflow_status || lead.status || "New";
}

export function leadOwnerName(data, lead = {}) {
  return lead.owner_name || employeeName(data, lead.owner_id || lead.owner) || "Unassigned";
}

export function leadNoteCount(data, lead = {}) {
  if (lead.notes_count !== undefined) return lead.notes_count;
  return (data.leadNotes || []).filter((note) => String(note.lead) === String(lead.id)).length;
}

export function leadContactSummary(data, lead = {}, field) {
  const contacts = (data.leadContacts || []).filter((item) => String(item.lead) === String(lead.id));
  const direct = field === "email" ? lead.email || lead.contact_email : lead.phone || lead.contact_phone;
  return direct || contacts.map((item) => item[field]).filter(Boolean).join(", ") || "-";
}

export function sourceTone(label = "") {
  if (/banao|website/i.test(label)) return "banao";
  if (/instagram|insta/i.test(label)) return "instagram";
  if (/client/i.test(label)) return "client";
  if (/linkedin|linked/i.test(label)) return "linkedin";
  return "dynamic";
}

export function priorityTone(value = "") {
  if (/urgent|high|hot/i.test(String(value))) return "red";
  if (/normal|medium/i.test(String(value))) return "gold";
  return "green";
}

export function marketingRecentEvents(data, leads = []) {
  const leadMap = indexById(leads);
  const activityRows = (data.leadActivities || []).map((item) => ({
    id: `activity-${item.id}`,
    title: item.activity_type || item.title || "Activity",
    lead: leadMap.get(String(item.lead))?.company_name || item.lead_name || "Lead",
    when: item.created_at || item.updated_at,
  }));
  const noteRows = (data.leadNotes || []).map((item) => ({
    id: `note-${item.id}`,
    title: item.title || "Lead Note",
    lead: leadMap.get(String(item.lead))?.company_name || item.lead_name || "Lead",
    when: item.created_at || item.updated_at,
  }));
  const proposalRows = (data.leadProposals || []).map((item) => ({
    id: `proposal-${item.id}`,
    title: item.title || "Proposal Artifact",
    lead: leadMap.get(String(item.lead))?.company_name || item.lead_name || "Lead",
    when: item.created_at || item.updated_at,
  }));
  return [...activityRows, ...noteRows, ...proposalRows].sort((left, right) => new Date(right.when || 0) - new Date(left.when || 0));
}

export function marketingSourceCards(leads = []) {
  const rowsBySource = groupBy(leads, leadSource);
  return Array.from(rowsBySource.entries()).map(([label, rows]) => ({
    label,
    count: rows.length,
    logo: String(label || "?").slice(0, 2).toUpperCase(),
    tone: sourceTone(label),
  }));
}

export function leadSourceCards(data, leads = []) {
  const counts = data.leadOriginCounts || {};
  const fromRows = (aliases) => leads.filter((lead) => aliases.some((alias) => leadSource(lead).toLowerCase().includes(alias))).length;
  const fromCounts = (aliases) => Object.entries(counts).reduce((sum, [source, count]) => sum + (aliases.some((alias) => String(source).toLowerCase().includes(alias)) ? Number(count || 0) : 0), 0);
  const countFor = (aliases) => fromCounts(aliases) || fromRows(aliases);
  return [
    { label: "Banao Website", logo: "B", tone: "banao", count: countFor(["banao", "website", "w"]) },
    { label: "Instagram", logo: "◎", tone: "instagram", count: countFor(["instagram", "insta"]) },
    { label: "Client Website", logo: "⌾", tone: "client", count: countFor(["client"]) },
    { label: "LinkedIn", logo: "in", tone: "linkedin", count: countFor(["linkedin", "linked"]) },
  ];
}

export function uniqueOptions(values) {
  return Array.from(new Set((values || []).filter(Boolean).map((value) => String(value))));
}

export function toPascalCase(value) {
  return String(value || "")
    .replace(/[_\-]+/g, " ")
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join("");
}

export function downloadCsv(filename, columns, rows) {
  const headers = (columns || []).map((column) => toPascalCase(column));
  const safeName = filename && filename.endsWith(".csv") ? filename : `${toPascalCase(filename || "Export")}.csv`;
  const csv = [headers, ...rows].map((row) => row.map(csvValue).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = safeName;
  link.click();
  URL.revokeObjectURL(url);
}

export function csvValue(value) {
  const text = String(value ?? "");
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}