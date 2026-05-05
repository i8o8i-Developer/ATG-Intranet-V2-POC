import React, { useState } from "react";
import { ChevronDown, ChevronRight, X } from "lucide-react";

import { isCompleted } from "./ScreenUtils.jsx";

export function Panel({ title, subtitle, right, children }) {
  return <section className="panel glass fade-in"><header><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{right}</header><div>{children}</div></section>;
}

export function Disclosure({ title, subtitle, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return <section className="panel disclosure glass fade-in"><header onClick={() => setOpen(!open)}><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{open ? <ChevronDown /> : <ChevronRight />}</header>{open && <div>{children}</div>}</section>;
}

export function Tabs({ value, onChange, items }) {
  return <div className="tabs">{items.map(([id, label]) => <button key={id} className={value === id ? "active" : ""} onClick={() => onChange(id)}>{label}</button>)}</div>;
}

export function Modal({ title, children, onClose, wide }) {
  return <div className="modal-backdrop"><section className={wide ? "modal wide" : "modal"}><header><h1>{title}</h1><button className="icon-button" onClick={onClose}><X /></button></header>{children}</section></div>;
}

export function StatCard({ label, value }) {
  return <section className="stat-card"><span>{label}</span><strong>{value}</strong></section>;
}

export function StatusPill({ children, tone = "neutral" }) {
  return <span className={`status-pill ${tone}`}>{children}</span>;
}

export function EmptyState({ label }) {
  return <div className="empty-state">{label}</div>;
}

export function SimpleTable({ columns, rows }) {
  return <table className="erp-table"><thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}</tr>)}</tbody></table>;
}

export function MilestoneRail({ milestones }) {
  const visible = milestones.length ? milestones : [{ id: "empty-1", status: "Open" }, { id: "empty-2", status: "Completed" }, { id: "empty-3", status: "Delayed" }];
  return <div className="milestone-rail">{visible.slice(0, 12).map((milestone) => <span key={milestone.id} className={isCompleted(milestone.status) ? "done" : milestone.status === "Delayed" ? "late" : "open"} />)}</div>;
}

export function Progress({ value }) {
  return <div className="progress"><span style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }} /></div>;
}