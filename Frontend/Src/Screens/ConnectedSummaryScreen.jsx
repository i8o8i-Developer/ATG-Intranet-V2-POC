import React from "react";

import { Panel, StatCard } from "./Shared/ScreenComponents.jsx";

function formatResourceLabel(value) {
  return String(value)
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

export function ConnectedSummaryScreen({ data, title, resources }) {
  return <section className="screen-stack"><h1>{title}</h1><div className="stat-grid three">{resources.map((key) => <StatCard key={key} label={formatResourceLabel(key)} value={(data[key] || []).length} />)}</div><Panel title="Backend Records"><pre>{JSON.stringify(resources.reduce((acc, key) => ({ ...acc, [key]: (data[key] || []).slice(0, 5) }), {}), null, 2)}</pre></Panel></section>;
}