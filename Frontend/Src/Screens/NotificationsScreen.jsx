import React, { useMemo, useState } from "react";
import { Bell, CheckCheck, Filter, Search } from "Lucide-React";
import { apiPost } from "../Api/Client.js";
import { Panel } from "./Shared/ScreenComponents.jsx";
import { formatDate } from "./Shared/ScreenUtils.jsx";

export function NotificationsScreen({ data, reload, navigate }) {
  const all = data.notifications || [];
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);

  const categories = useMemo(() => {
    const set = new Set();
    all.forEach((item) => set.add(String(item.category || item.resource_type || "general")));
    return ["all", "unread", ...Array.from(set)];
  }, [all]);

  const visible = useMemo(() => {
    return all
      .filter((item) => {
        if (filter === "unread") return !item.is_read;
        if (filter !== "all") return String(item.category || item.resource_type || "general") === filter;
        return true;
      })
      .filter((item) => {
        if (!query) return true;
        const haystack = `${item.title || ""} ${item.message || ""} ${item.description || ""}`.toLowerCase();
        return haystack.includes(query.toLowerCase());
      })
      .sort((left, right) => new Date(right.created_at || 0) - new Date(left.created_at || 0));
  }, [all, filter, query]);

  const unread = all.filter((item) => !item.is_read);

  const markRead = async (item) => {
    setBusy(true);
    try {
      await apiPost(`/MainApp/Notifications/${item.id}/read/`, {});
      if (reload) reload(["notifications"]);
    } finally { setBusy(false); }
  };
  const markAllRead = async () => {
    setBusy(true);
    try {
      await Promise.allSettled(unread.map((item) => apiPost(`/MainApp/Notifications/${item.id}/read/`, {})));
      if (reload) reload(["notifications"]);
    } finally { setBusy(false); }
  };
  const open = (item) => {
    if (!item.is_read) markRead(item);
    const resourceType = String(item.resource_type || item.category || "").toLowerCase();
    const resourceId = item.resource_id || item.metadata?.project || item.metadata?.project_id;
    if (resourceType.includes("project") && resourceId) navigate(`/project/dashboard/${resourceId}/project/`);
    else if (resourceType.includes("leave")) navigate("/leave/apply/");
    else if (resourceType.includes("assessment")) navigate("/assessment/");
  };

  return (
    <Panel
      title={<span><Bell size={18} /> Notifications</span>}
      subtitle={`${all.length} total · ${unread.length} unread`}
      right={(
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ position: "relative" }}>
            <Search size={14} style={{ position: "absolute", left: 8, top: 9, opacity: 0.5 }} />
            <input className="Mini-Inp" style={{ paddingLeft: 26 }} placeholder="Search" value={query} onChange={(e) => setQuery(e.target.value)} />
          </span>
          <span style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <Filter size={14} />
            <select className="Mini-Inp" value={filter} onChange={(e) => setFilter(e.target.value)}>
              {categories.map((category) => <option key={category} value={category}>{category}</option>)}
            </select>
          </span>
          <button className="Soft-ButtonSmall" onClick={markAllRead} disabled={busy || !unread.length}>
            <CheckCheck size={14} /> Mark All Read
          </button>
        </div>
      )}
    >
      <div className="Notification-List" style={{ maxHeight: "none" }}>
        {visible.map((item) => (
          <div key={item.id} className={item.is_read ? "Notification-Item" : "Notification-ItemUnread"}>
            <div onClick={() => open(item)} style={{ cursor: "pointer", flex: 1 }}>
              <strong>{item.title || item.category || "Notification"}</strong>
              <p>{item.message || item.description || "(NoContent)"}</p>
              <small>{formatDate(item.created_at)} · {item.category || item.resource_type || "general"}</small>
            </div>
            {!item.is_read && (
              <button className="Soft-ButtonSmall" onClick={() => markRead(item)} disabled={busy}>Mark Read</button>
            )}
          </div>
        ))}
        {!visible.length && <div className="Notification-Empty">No Notifications Match.</div>}
      </div>
    </Panel>
  );
}
