import React from "react";

import { Panel, SimpleTable } from "./Shared/ScreenComponents.jsx";
import { employeeName, formatDate, money, projectName } from "./Shared/ScreenUtils.jsx";

export function TasksScreen({ data }) {
  return <Panel title="Tasks Dashboard"><SimpleTable columns={["Task", "Project", "Owner", "Status", "Due", "Bounty"]} rows={(data.tasks || []).map((task) => [task.title, projectName(data, task.project), employeeName(data, task.owner), task.status, formatDate(task.due_at), Math.round(Number(task.bounty || 0))])} /></Panel>;
}