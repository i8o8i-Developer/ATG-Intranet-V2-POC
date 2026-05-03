import React, { useMemo } from "react";
import { ProjectDashboardScreen } from "./ProjectDashboardScreen.jsx";


export function MarketingProjectScreen(props) {
  const filteredData = useMemo(() => {
    const all = props.data?.projects || [];
    const marketing = all.filter((project) => {
      const blob = `${project.project_type || ""} ${project.category || ""} ${project.name || ""} ${project.code || ""}`.toLowerCase();
      return /marketing|growth|campaign|sales|lead/.test(blob);
    });
    return { ...props.data, projects: marketing.length ? marketing : all };
  }, [props.data]);
  return <ProjectDashboardScreen {...props} data={filteredData} kind="marketing" />;
}
