import React, { useState } from "react";
import { ChevronDown, ChevronRight, X } from "lucide-react";

import { isCompleted } from "./ScreenUtils.jsx";

export function Panel({ title, subtitle, right, children }) {
  return <section className="Panel Glass Fade-In"><header><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{right}</header><div>{children}</div></section>;
}

export function Disclosure({ title, subtitle, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return <section className="Panel Disclosure Glass Fade-In"><header onClick={() => setOpen(!open)}><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{open ? <ChevronDown /> : <ChevronRight />}</header>{open && <div>{children}</div>}</section>;
}

export function Tabs({ value, onChange, items }) {
  return <div className="Tabs">{items.map(([id, label]) => <button key={id} className={value === id ? "Active" : ""} onClick={() => onChange(id)}>{label}</button>)}</div>;
}

export function Modal({ title, children, onClose, wide }) {
  return <div className="Modal-Backdrop"><section className={wide ? "Modal Wide" : "Modal"}><header><h1>{title}</h1><button className="Icon-Button" onClick={onClose}><X /></button></header>{children}</section></div>;
}

export function StatCard({ label, value }) {
  return <section className="Stat-Card"><span>{label}</span><strong>{value}</strong></section>;
}

export function StatusPill({ children, tone = "Neutral" }) {
  const toneMap = {
    neutral: "Slate",
    green: "Green",
    red: "Red",
    gold: "Gold",
    blue: "Blue",
    slate: "Slate",
    Neutral: "Slate",
    Green: "Green",
    Red: "Red",
    Gold: "Gold",
    Blue: "Blue",
    Slate: "Slate"
  };
  const cssTone = toneMap[tone] || "Slate";
  return <span className={`Status-Pill ${cssTone}`}>{children}</span>;
}

export function EmptyState({ label }) {
  return <div className="Empty-State">{label}</div>;
}

export function SimpleTable({ columns, rows }) {
  return <table className="Erp-Table"><thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}</tr>)}</tbody></table>;
}

export function MilestoneRail({ milestones }) {
  const visible = milestones.length ? milestones : [{ id: "Empty-1", status: "Open" }, { id: "Empty-2", status: "Completed" }, { id: "Empty-3", status: "Delayed" }];
  return <div className="Milestone-Rail">{visible.slice(0, 12).map((milestone) => <span key={milestone.id} className={isCompleted(milestone.status) ? "done" : milestone.status === "Delayed" ? "late" : "open"} />)}</div>;
}

export function Progress({ value }) {
  return <div className="progress"><span style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }} /></div>;
}