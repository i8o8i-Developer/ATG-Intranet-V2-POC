import React, { useState } from "react";
import { ChevronDown, ChevronRight, X } from "lucide-react";

import { isCompleted } from "./ScreenUtils.jsx";

export function Panel({ title, subtitle, right, children, className = "" }) {
  return <section className={`Panel Glass Fade-In ${className}`}><header><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{right}</header><div>{children}</div></section>;
}

export function Disclosure({ title, subtitle, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return <section className="Panel Disclosure Glass Fade-In"><header onClick={() => setOpen(!open)} style={{ cursor: "pointer" }}><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{open ? <ChevronDown size={18} /> : <ChevronRight size={18} />}</header>{open && <div>{children}</div>}</section>;
}

export function Tabs({ value, onChange, items = [] }) {
  return <div className="Tabs">{items.map(([id, label]) => <button key={id} className={value === id ? "Active" : ""} onClick={() => onChange(id)}>{label}</button>)}</div>;
}

export function Modal({ title, children, onClose, wide }) {
  return (
    <div className="Modal-Backdrop">
      <section className={wide ? "Modal Wide" : "Modal"}>
        <header>
          <h1>{title}</h1>
          <button className="Modal-Close-Btn" onClick={onClose} title="Close"><X size={18} /></button>
        </header>
        <div className="Modal-Body">{children}</div>
      </section>
    </div>
  );
}

export function StatCard({ label, value, icon }) {
  return <section className="Stat-Card">{icon && <div className="Stat-Icon">{icon}</div>}<div><span>{label}</span><strong>{value}</strong></div></section>;
}

export function StatusPill({ children, tone = "Neutral" }) {
  const toneMap = {
    neutral: "Slate", green: "Green", red: "Red", gold: "Gold", blue: "Blue",
    slate: "Slate", Neutral: "Slate", Green: "Green", Red: "Red", Gold: "Gold", Blue: "Blue", Slate: "Slate",
    info: "Blue", warning: "Gold", error: "Red", success: "Green",
  };
  const cssTone = toneMap[tone] || "Slate";
  return <span className={`Status-Pill ${cssTone}`}>{children}</span>;
}

export function EmptyState({ label }) {
  return <div className="Empty-State">{label}</div>;
}

export function SimpleTable({ columns = [], rows = [] }) {
  return (
    <div className="Table-Wrap">
      <table className="Erp-Table">
        <thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
        <tbody>{rows.map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}

export function MilestoneRail({ milestones = [] }) {
  if (!milestones.length) return null;
  return <div className="Milestone-Rail">{milestones.slice(0, 12).map((milestone) => <span key={milestone.id} className={isCompleted(milestone.status) ? "done" : milestone.status === "Delayed" ? "late" : "open"} />)}</div>;
}

export function Progress({ value }) {
  return <div className="progress"><span style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }} /></div>;
}
