import React, { useMemo } from "react";
import { ProjectDashboardScreen } from "./ProjectDashboardScreen.jsx";


function isMarketingProject(project) {
  const metadata = project.metadata || {};
  const tags = Array.isArray(metadata.tags) ? metadata.tags.join(" ") : "";
  const channels = Array.isArray(metadata.channels) ? metadata.channels.join(" ") : "";
  const blob = `${project.project_type || ""} ${project.category || ""} ${project.client_name || ""} ${project.name || ""} ${project.code || ""} ${project.description || ""} ${tags} ${channels}`.toLowerCase();
  return /marketing|growth|campaign|sales|lead/.test(blob);
}


export function MarketingProjectScreen(props) {
  const filteredData = useMemo(() => {
    const all = props.data?.projects || [];
    return { ...props.data, projects: all.filter(isMarketingProject) };
  }, [props.data]);
  return <ProjectDashboardScreen {...props} data={filteredData} kind="marketing" />;
}
