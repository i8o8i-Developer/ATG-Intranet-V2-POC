import React, { useEffect, useMemo, useState } from "react";
import { File, FileText, FolderOpen, Plus, Search } from "lucide-react";

import { apiGet, apiPost } from "../Api/Client.js";
import { Modal, Panel, SimpleTable, StatusPill } from "./Shared/ScreenComponents.jsx";
import "../Styles/DocsScreen.css";
import { employeeName, formatDate, formatDateTime } from "./Shared/ScreenUtils.jsx";

const TABS = ["Library", "My Documents", "History"];

export function DocsScreen({ data, reload, navigate }) {
  const [tab, setTab] = useState("Library");
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState({ title: "", body: "", department: "", visibility: "private" });
  const [search, setSearch] = useState("");

  const loadDocs = async () => {
    setLoading(true);
    try {
      let list;
      if (tab === "Library") {
        const resp = await apiGet("/AtgDocs/KnowledgeDocuments/library/");
        list = resp?.groups || [];
      } else if (tab === "My Documents") {
        list = await apiGet("/AtgDocs/KnowledgeDocuments/my-documents/");
      } else {
        list = await apiGet("/AtgDocs/KnowledgeDocuments/visit-history/");
      }
      setDocs(list);
    } catch {
      setDocs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadDocs(); }, [tab]);

  const filtered = useMemo(() => {
    if (!search.trim()) return docs;
    const q = search.toLowerCase();
    if (Array.isArray(docs)) return docs.filter((d) => String(d.title || "").toLowerCase().includes(q));
    if (docs.groups) {
      return {
        ...docs,
        groups: docs.groups.map((g) => ({
          ...g,
          documents: (g.documents || []).filter((d) => String(d.title || "").toLowerCase().includes(q)),
        })).filter((g) => g.documents.length > 0),
      };
    }
    return docs;
  }, [docs, search]);

  const createDocument = async (e) => {
    e.preventDefault();
    const payload = {
      title: createForm.title,
      body: createForm.body,
      status: "Draft",
      visibility: createForm.visibility,
    };
    if (createForm.department) payload.department = Number(createForm.department);
    try {
      await apiPost("/AtgDocs/KnowledgeDocuments/create-document/", payload);
      setCreateOpen(false);
      setCreateForm({ title: "", body: "", department: "", visibility: "private" });
      loadDocs();
      reload(["docs", "docPermissions", "docVersions"]);
    } catch (err) {
      /* silent */
    }
  };

  const openDoc = (id) => navigate(`/docs/post-detail/${id}/`);

  return (
    <section className="Docs-Screen Screen-Stack">
      <section className="Page-Heading">
        <div><span>Main App / Documents</span><h1>Documents</h1></div>
        <button className="Primary-Button" onClick={() => setCreateOpen(true)}><Plus size={16} /> New Document</button>
      </section>

      <div className="Docs-Tabs">
        {TABS.map((t) => (
          <button key={t} className={tab === t ? "Docs-Tab Active" : "Docs-Tab"} onClick={() => setTab(t)}>{t}</button>
        ))}
        <div className="Docs-Search">
          <Search size={15} />
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search Documents..." />
        </div>
      </div>

      <div className="Docs-Content">
        {loading && <div className="Docs-Loading">Loading...</div>}
        {!loading && tab === "Library" && Array.isArray(filtered?.groups) && filtered.groups.map((group) => (
          <div key={group.departmentId} className="Docs-Group">
            <h3 className="Docs-Group-Title"><FolderOpen size={16} /> {group.departmentName} ({group.documents.length})</h3>
            <div className="Docs-Card-Grid">
              {group.documents.map((doc) => (
                <div key={doc.id} className="Docs-Card" onClick={() => openDoc(doc.id)}>
                  <div className="Docs-Card-Icon"><FileText size={24} /></div>
                  <div className="Docs-Card-Body">
                    <strong>{doc.title}</strong>
                    <div className="Docs-Card-Meta">
                      <StatusPill tone={doc.status === "Published" ? "green" : doc.status === "Draft" ? "gold" : "slate"}>{doc.status}</StatusPill>
                      <span>{doc.departmentName}</span>
                    </div>
                    <small>{doc.ownerName} &middot; {formatDateTime(doc.updatedAt)}</small>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
        {!loading && tab !== "Library" && Array.isArray(filtered) && (
          <div className="Docs-Card-Grid">
            {filtered.map((doc) => (
              <div key={doc.documentId || doc.id} className="Docs-Card" onClick={() => openDoc(doc.documentId || doc.id)}>
                <div className="Docs-Card-Icon"><FileText size={24} /></div>
                <div className="Docs-Card-Body">
                  <strong>{doc.title}</strong>
                  <div className="Docs-Card-Meta">
                    <StatusPill tone={doc.status === "Published" ? "green" : doc.status === "Draft" ? "gold" : "slate"}>{doc.status || "Viewed"}</StatusPill>
                    <span>{doc.departmentName}</span>
                  </div>
                  <small>{doc.ownerName || ""} {doc.visitedAt ? formatDateTime(doc.visitedAt) : formatDateTime(doc.updatedAt)}</small>
                </div>
              </div>
            ))}
          </div>
        )}
        {!loading && tab !== "Library" && Array.isArray(filtered) && filtered.length === 0 && <p className="Docs-Empty">No Documents Found.</p>}
        {!loading && tab === "Library" && (!Array.isArray(filtered?.groups) || filtered.groups.length === 0) && <p className="Docs-Empty">No Documents Found.</p>}
      </div>

      {createOpen && (
        <Modal title="Create Document" onClose={() => setCreateOpen(false)}>
          <form onSubmit={createDocument}>
            <div className="Form-Grid Two" style={{ marginBottom: 12 }}>
              <label>Title<input value={createForm.title} onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })} required /></label>
              <label>Visibility<select value={createForm.visibility} onChange={(e) => setCreateForm({ ...createForm, visibility: e.target.value })}>
                <option value="private">Private</option>
                <option value="authenticated">Authenticated Users</option>
                <option value="link">Anyone With Link</option>
              </select></label>
            </div>
            <label>Department<select value={createForm.department} onChange={(e) => setCreateForm({ ...createForm, department: e.target.value })}>
              <option value="">General</option>{(data.departments || []).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select></label>
            <label>Body<textarea value={createForm.body} onChange={(e) => setCreateForm({ ...createForm, body: e.target.value })} rows={8} style={{ fontFamily: "monospace", fontSize: 13 }} /></label>
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <button className="Primary-Button" type="submit">Create</button>
              <button className="Outline-Button" type="button" onClick={() => setCreateOpen(false)}>Cancel</button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}

export function DocsDetailScreen({ data, route, reload, navigate }) {
  const docId = (route || "").split("?")[0].split("/").filter(Boolean).pop();
  const [doc, setDoc] = useState(null);
  const [body, setBody] = useState("");
  const [title, setTitle] = useState("");
  const [saving, setSaving] = useState(false);
  const [permissions, setPermissions] = useState([]);
  const [history, setHistory] = useState([]);
  const [permOpen, setPermOpen] = useState(false);
  const [permForm, setPermForm] = useState({ employee_id: "", permission: "Read" });
  const [tab, setTab] = useState("editor");

  useEffect(() => {
    if (!docId) return;
    apiGet(`/AtgDocs/KnowledgeDocuments/${docId}/open/`).then((d) => {
      setDoc(d);
      setTitle(d.title || "");
      setBody(d.body || "");
    }).catch(() => {});
    apiGet("/AtgDocs/KnowledgePermissions/").then((list) => {
      setPermissions((list || []).filter((p) => String(p.document) === String(docId)));
    }).catch(() => {});
    apiGet(`/AtgDocs/KnowledgeDocuments/${docId}/history/`).then(setHistory).catch(() => {});
  }, [docId]);

  const save = async () => {
    setSaving(true);
    try {
      const resp = await apiPost(`/AtgDocs/KnowledgeDocuments/${docId}/update-content/`, { title, body });
      if (resp) setDoc(resp);
      reload(["docs"]);
    } catch (err) {
      /* silent */
    } finally {
      setSaving(false);
    }
  };

  const publish = async () => {
    await apiPost(`/AtgDocs/KnowledgeDocuments/${docId}/publish/`, {});
    const d = await apiGet(`/AtgDocs/KnowledgeDocuments/${docId}/open/`);
    setDoc(d);
    reload(["docs"]);
  };

  const grantPermission = async (e) => {
    e.preventDefault();
    const emp = (data.employees || []).find((e) => String(e.id) === String(permForm.employee_id));
    if (!emp || !emp.user_email) return;
    await apiPost(`/AtgDocs/KnowledgeDocuments/${docId}/grant-permission/`, {
      subject_type: "employee",
      subject_id: String(permForm.employee_id),
      permission: permForm.permission,
      email: emp.user_email,
    });
    setPermOpen(false);
    setPermForm({ employee_id: "", permission: "Read" });
    const list = await apiGet("/AtgDocs/KnowledgePermissions/");
    setPermissions((list || []).filter((p) => String(p.document) === String(docId)));
  };

  const execCmd = (cmd, val = null) => {
    document.execCommand(cmd, false, val);
  };

  if (!doc) return <section className="Screen-Stack" style={{ padding: 32 }}><p>Loading Document...</p></section>;

  return (
    <section className="Docs-Detail Screen-Stack">
      <section className="Page-Heading">
        <div>
          <span><button className="Atg-Link-Btn" onClick={() => navigate("/docs/")} style={{ fontSize: 13 }}>&larr; Back to Documents</button></span>
          <h1><input value={title} onChange={(e) => setTitle(e.target.value)} style={{ fontSize: 20, fontWeight: 700, border: "none", background: "transparent", width: "100%", padding: 0, fontFamily: "inherit" }} /></h1>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <StatusPill tone={doc.status === "Published" ? "green" : "gold"}>{doc.status}</StatusPill>
          <button className="Soft-Button Small" onClick={() => setPermOpen(true)}>Permissions</button>
          <button className="Primary-Button Small" onClick={save} disabled={saving}>{saving ? "Saving..." : "Save"}</button>
          {doc.status !== "Published" && <button className="Primary-Button Small" onClick={publish}>Publish</button>}
        </div>
      </section>

      <div className="Docs-Detail-Tabs">
        <button className={tab === "editor" ? "Docs-Tab Active" : "Docs-Tab"} onClick={() => setTab("editor")}>Editor</button>
        <button className={tab === "versions" ? "Docs-Tab Active" : "Docs-Tab"} onClick={() => setTab("versions")}>Version History ({history.length})</button>
        <button className={tab === "permissions" ? "Docs-Tab Active" : "Docs-Tab"} onClick={() => setTab("permissions")}>Permissions ({permissions.length})</button>
      </div>

      {tab === "editor" && (
        <div className="Docs-Editor-Wrapper">
          <div className="Docs-Toolbar">
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("bold"); }} title="Bold"><b>B</b></button>
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("italic"); }} title="Italic"><i>I</i></button>
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("underline"); }} title="Underline"><u>U</u></button>
            <span className="Docs-Toolbar-Sep" />
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("insertUnorderedList"); }} title="Bullet List">&bull; List</button>
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("insertOrderedList"); }} title="Numbered List">1. List</button>
          </div>
          <div
            className="Docs-Editor"
            contentEditable
            suppressContentEditableWarning
            dangerouslySetInnerHTML={{ __html: body }}
            onBlur={(e) => setBody(e.currentTarget.innerHTML)}
            style={{ minHeight: 400, padding: 24, border: "1px solid #e2e8f0", borderRadius: 8, background: "#fff", fontSize: 14, lineHeight: 1.6, outline: "none" }}
          />
        </div>
      )}

      {tab === "versions" && (
        <Panel title="Version History">
          {history.length === 0 && <p style={{ color: "#94a3b8" }}>No Versions Yet.</p>}
          <SimpleTable columns={["Version", "Title", "Date"]} rows={history.map((v) => [v.version, v.title || doc.title, formatDateTime(v.created_at)])} />
        </Panel>
      )}

      {tab === "permissions" && (
        <Panel title="Permissions">
          <SimpleTable columns={["Subject Type", "Subject ID", "Permission"]} rows={permissions.map((p) => [p.subject_type, p.subject_type === "employee" ? employeeName(data, p.subject_id) : p.subject_id, <StatusPill key={p.id} tone={p.permission === "Write" ? "green" : "slate"}>{p.permission}</StatusPill>])} />
          <button className="Soft-Button Small" onClick={() => setPermOpen(true)} style={{ marginTop: 12 }}><Plus size={14} /> Add Permission</button>
        </Panel>
      )}

      {permOpen && (
        <Modal title="Grant Permission" onClose={() => setPermOpen(false)}>
          <form onSubmit={grantPermission}>
            <div className="Form-Grid Two" style={{ marginBottom: 12 }}>
              <label>Employee<select value={permForm.employee_id} onChange={(e) => setPermForm({ ...permForm, employee_id: e.target.value })} required><option value="">Select Employee</option>{(data.employees || []).map((e) => <option key={e.id} value={e.id}>{e.display_name}</option>)}</select></label>
              <label>Permission<select value={permForm.permission} onChange={(e) => setPermForm({ ...permForm, permission: e.target.value })}><option value="Read">Read</option><option value="Write">Write</option></select></label>
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <button className="Primary-Button" type="submit">Grant</button>
              <button className="Outline-Button" type="button" onClick={() => setPermOpen(false)}>Cancel</button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
