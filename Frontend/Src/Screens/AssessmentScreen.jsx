import React from "react";
import { ChevronDown, Search, X } from "lucide-react";

import { StatusPill, Tabs } from "./Shared/ScreenComponents.jsx";
import { isCompleted } from "./Shared/ScreenUtils.jsx";

export function AssessmentScreen({ data }) {
  const rows = data.assessmentRows?.length ? data.assessmentRows : data.assessmentAssignments || [];
  return <section className="assessment-screen"><Tabs value="results" onChange={() => {}} items={[["results", "Assessment Results"], ["assign", "Assign Assessment"]]} /><div className="toolbar-row"><div className="search-box"><input placeholder="Search Here..." /><Search size={17} /><X size={17} /></div><select><option>All Roles</option></select><button className="outline-button">Sort By</button></div><table className="erp-table"><thead><tr><th>Intern Name</th><th>Week Since Joining</th><th>Latest Assessment</th><th>Assessment Number</th><th>Status</th></tr></thead><tbody>{rows.map((row, index) => <tr key={row.id || index}><td><ChevronDown size={15} />{row.employee_name || row.employee || row.name}</td><td>{row.weeks_since_join || row.week_since_join || "-"} Weeks</td><td>{row.assessment_title || row.latest_assessment || row.assessment}</td><td>{row.assessment_sequence_number || row.assessment_number || row.attempts_count || 1}</td><td><StatusPill tone={isCompleted(row.status || row.note) ? "green" : "gold"}>{row.note || row.status || "Incomplete"}</StatusPill></td></tr>)}</tbody></table></section>;
}