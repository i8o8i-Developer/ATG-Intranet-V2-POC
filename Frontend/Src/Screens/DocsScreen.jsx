import React, { useCallback, useEffect, useMemo, useState } from "react";
import { ExternalLink, File, FileText, FolderOpen, Plus, Search, Trash, Upload } from "lucide-react";

import { apiGet, apiPost, unpackList } from "../Api/Client.js";
import { Modal, Panel, SimpleTable, StatusPill } from "./Shared/ScreenComponents.jsx";
import "../Styles/DocsScreen.css";
import { employeeName, formatDate, formatDateTime } from "./Shared/ScreenUtils.jsx";

const TABS = ["Library", "My Documents"];

export function DocsScreen({ data, reload, navigate }) {
  const [tab, setTab] = useState("Library");
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState({ title: "", body: "", department: "", visibility: "private", uploadToDrive: false });
  const [search, setSearch] = useState("");

  const loadDocs = async () => {
    setLoading(true);
    try {
      let list;
      if (tab === "Library") {
        const resp = await apiGet("/AtgDocs/KnowledgeDocuments/library/");
        list = resp?.groups || [];
      } else {
        list = await apiGet("/AtgDocs/KnowledgeDocuments/my-documents/");
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
    if (tab === "Library") {
      return (docs || []).map((g) => ({
        ...g,
        documents: (g.documents || []).filter((d) => String(d.title || "").toLowerCase().includes(q)),
      })).filter((g) => g.documents.length > 0);
    }
    if (Array.isArray(docs)) return docs.filter((d) => String(d.title || "").toLowerCase().includes(q));
    return docs;
  }, [docs, search, tab]);

  const createDocument = async (e) => {
    e.preventDefault();
    const payload = {
      title: createForm.title,
      body: createForm.body,
      status: "Draft",
      visibility: createForm.visibility,
    };
    if (createForm.department) payload.department = Number(createForm.department);
    payload.upload_to_drive = createForm.uploadToDrive;
    try {
      await apiPost("/AtgDocs/KnowledgeDocuments/create-document/", payload);
      setCreateOpen(false);
      setCreateForm({ title: "", body: "", department: "", visibility: "private", uploadToDrive: false });
      loadDocs();
      reload(["docs", "docPermissions", "docVersions"]);
    } catch (err) {
      /* silent */
    }
  };

  const openDoc = (id) => navigate(`/docs/post-detail/${id}/`);

  const deleteDocument = async (id) => {
    if (!window.confirm("Are You Sure You Want To Delete This Document?")) return;
    try {
      await apiPost(`/AtgDocs/KnowledgeDocuments/${id}/delete-document/`, {});
      loadDocs();
      reload(["docs"]);
    } catch (err) {
      alert("Failed To Delete Document");
    }
  };

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
        {!loading && tab === "Library" && Array.isArray(filtered) && filtered.map((group) => (
          <div key={group.departmentId} className="Docs-Group">
            <h3 className="Docs-Group-Title"><FolderOpen size={16} /> {group.departmentName} ({(group.documents || []).length})</h3>
            <div className="Docs-Card-Grid">
              {(group.documents || []).map((doc) => (
                <div key={doc.id} className="Docs-Card" onClick={() => openDoc(doc.id)}>
                  <div className="Docs-Card-Icon"><FileText size={24} /></div>
                  <div className="Docs-Card-Body">
                    <strong>{doc.title}</strong>
                    <div className="Docs-Card-Meta">
                      <StatusPill tone={doc.status === "Published" ? "green" : doc.status === "Draft" ? "gold" : "slate"}>{doc.status}</StatusPill>
                      <span>{doc.departmentName}</span>
                      <button className="Icon-Button" onClick={(e) => { e.stopPropagation(); deleteDocument(doc.id); }} style={{ marginLeft: "auto", color: "var(--Danger)", background: "transparent", border: "none", cursor: "pointer", display: "flex", padding: 0 }}><Trash size={16} /></button>
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
                    <button className="Icon-Button" onClick={(e) => { e.stopPropagation(); deleteDocument(doc.documentId || doc.id); }} style={{ marginLeft: "auto", color: "var(--Danger)", background: "transparent", border: "none", cursor: "pointer", display: "flex", padding: 0 }}><Trash size={14} /></button>
                  </div>
                  <small>{doc.ownerName || ""} {doc.visitedAt ? formatDateTime(doc.visitedAt) : formatDateTime(doc.updatedAt)}</small>
                </div>
              </div>
            ))}
          </div>
        )}
        {!loading && tab !== "Library" && Array.isArray(filtered) && filtered.length === 0 && <p className="Docs-Empty">No Documents Found.</p>}
        {!loading && tab === "Library" && (!Array.isArray(filtered) || filtered.length === 0) && <p className="Docs-Empty">No Documents Found.</p>}
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
            <label style={{ flexDirection: "row", alignItems: "center", gap: 8, marginTop: 4 }}><input type="checkbox" checked={createForm.uploadToDrive} onChange={(e) => setCreateForm({ ...createForm, uploadToDrive: e.target.checked })} /> Create In Google Drive</label>
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

function isRealGoogleUrl(url) {
  if (!url || typeof url !== "string") return false;
  if (url.startsWith("https://drive.local")) return false;
  return url.startsWith("https://docs.google.com/") || url.startsWith("https://drive.google.com/");
}

export function DocsDetailScreen({ data, route, reload, navigate }) {
  const docId = (route || "").split("?")[0].split("/").filter(Boolean).pop();
  const [doc, setDoc] = useState(null);
  const [body, setBody] = useState("");
  const [title, setTitle] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [permissions, setPermissions] = useState([]);
  const [history, setHistory] = useState([]);
  const [permOpen, setPermOpen] = useState(false);
  const [permForm, setPermForm] = useState({ employee_id: "", permission: "Read" });
  const [permLoading, setPermLoading] = useState(false);
  const [tab, setTab] = useState("editor");

  const loadPermissions = useCallback(async () => {
    try {
      const list = await apiGet("/AtgDocs/KnowledgePermissions/");
      setPermissions(unpackList(list).filter((p) => String(p.document) === String(docId) && p.subject_type === "user"));
    } catch (err) {
      console.error("Failed To Load Permissions", err);
    }
  }, [docId]);

  useEffect(() => {
    if (!docId) return;
    apiGet(`/AtgDocs/KnowledgeDocuments/${docId}/open/`).then((d) => {
      setDoc(d);
      setTitle(d.title || "");
      setBody(d.body || "");
    }).catch(() => {});
    loadPermissions();
    apiGet(`/AtgDocs/KnowledgeDocuments/${docId}/history/`).then(setHistory).catch(() => {});
  }, [docId, loadPermissions]);

  const refreshDoc = useCallback(async () => {
    const d = await apiGet(`/AtgDocs/KnowledgeDocuments/${docId}/open/`);
    setDoc(d);
    setTitle(d.title || "");
    setBody(d.body || "");
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
    await refreshDoc();
    reload(["docs"]);
  };

  const uploadToDrive = async () => {
    setUploading(true);
    try {
      const result = await apiPost(`/AtgDocs/KnowledgeDocuments/${docId}/upload-to-drive/`, { folder_name: "Documents" });
      if (result) await refreshDoc();
      reload(["docs", "driveFiles"]);
    } catch (err) {
      /* silent */
    } finally {
      setUploading(false);
    }
  };

  const deleteDoc = async () => {
    if (!window.confirm("Are You Sure You Want To Delete This Document?")) return;
    try {
      await apiPost(`/AtgDocs/KnowledgeDocuments/${docId}/delete-document/`, {});
      reload(["docs"]);
      navigate("/docs/");
    } catch (err) {
      alert("Failed To Delete Document");
    }
  };

  const grantPermission = async (e) => {
    e.preventDefault();
    const emp = (data.employees || []).find((e) => String(e.id) === String(permForm.employee_id));
    if (!emp) return alert("Please Select An Employee");
    if (!emp.user) return alert("This Employee has No Associated User Account");
    
    setPermLoading(true);
    try {
      await apiPost(`/AtgDocs/KnowledgeDocuments/${docId}/grant-permission/`, {
        user_id: Number(emp.user),
        permission: permForm.permission,
        email: emp.email || "",
      });
      setPermOpen(false);
      setPermForm({ employee_id: "", permission: "Read" });
      await loadPermissions();
    } catch (err) {
      alert(err.message || "Failed to grant permission");
    } finally {
      setPermLoading(false);
    }
  };

  const revokePermission = async (userId) => {
    if (!window.confirm("Are you sure you want to revoke this permission?")) return;
    setPermLoading(true);
    try {
      await apiPost(`/AtgDocs/KnowledgeDocuments/${docId}/revoke-permission/`, { user_id: userId });
      await loadPermissions();
    } catch (err) {
      alert(err.message || "Failed to revoke permission");
    } finally {
      setPermLoading(false);
    }
  };

  const execCmd = (cmd, val = null) => {
    document.execCommand(cmd, false, val);
  };

  const execHeading = (tag) => {
    document.execCommand("formatBlock", false, `<${tag}>`);
  };

  const execLink = () => {
    const url = prompt("Enter URL:");
    if (url) document.execCommand("createLink", false, url);
  };

  const execColor = (color) => {
    document.execCommand("foreColor", false, color);
  };

  const execHighlight = (color) => {
    document.execCommand("hiliteColor", false, color);
  };

  const execFontSize = (e) => {
    if (!e.target.value) return;
    document.execCommand("fontSize", false, e.target.value);
  };

  const execFont = (e) => {
    if (!e.target.value) return;
    document.execCommand("fontName", false, e.target.value);
  };

  const hasGoogleDoc = isRealGoogleUrl(doc?.openUrl);

  if (!doc) return <section className="Screen-Stack" style={{ padding: 32 }}><p>Loading Document...</p></section>;

  return (
    <section className="Docs-Detail Screen-Stack">
      <section className="Page-Heading">
        <div>
          <span><button className="Atg-Link-Btn" onClick={() => navigate("/docs/")} style={{ fontSize: 13 }}>&larr; Back to Documents</button></span>
          <h1><input value={title} onChange={(e) => setTitle(e.target.value)} readOnly={!doc.canEdit} style={{ fontSize: 20, fontWeight: 700, border: "none", background: "transparent", width: "100%", padding: 0, fontFamily: "inherit", cursor: doc.canEdit ? "text" : "default" }} /></h1>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <StatusPill tone={doc.status === "Published" ? "green" : "gold"}>{doc.status}</StatusPill>
          <button className="Soft-Button Small" onClick={() => setPermOpen(true)}>Permissions</button>
          {!hasGoogleDoc && doc.canEdit && <button className="Soft-Button Small" onClick={uploadToDrive} disabled={uploading}><Upload size={14} /> {uploading ? "Uploading..." : "Upload to Drive"}</button>}
          {!hasGoogleDoc && doc.canEdit && <button className="Primary-Button Small" onClick={save} disabled={saving}>{saving ? "Saving..." : "Save"}</button>}
          {!hasGoogleDoc && doc.canEdit && doc.status !== "Published" && <button className="Primary-Button Small" onClick={publish}>Publish</button>}
          {hasGoogleDoc && <a className="Primary-Button Small" href={doc.openUrl} target="_blank" rel="noopener noreferrer" style={{ textDecoration: "none" }}><ExternalLink size={14} /> Open In Google Docs</a>}
          {doc.canEdit && <button className="Soft-Button Small" onClick={deleteDoc} style={{ color: "var(--Danger)" }}><Trash size={14} /> Delete</button>}
        </div>
      </section>

      <div className="Docs-Detail-Tabs">
        <button className={tab === "editor" ? "Docs-Tab Active" : "Docs-Tab"} onClick={() => setTab("editor")}>{hasGoogleDoc ? "Google Docs" : "Editor"}</button>
        <button className={tab === "versions" ? "Docs-Tab Active" : "Docs-Tab"} onClick={() => setTab("versions")}>Version History ({history.length})</button>
        <button className={tab === "permissions" ? "Docs-Tab Active" : "Docs-Tab"} onClick={() => setTab("permissions")}>Permissions ({permissions.length})</button>
      </div>

      {tab === "editor" && hasGoogleDoc && (
        <div style={{ width: "100%", height: "80vh", border: "1px solid #e2e8f0", borderRadius: 8, overflow: "hidden" }}>
          <iframe src={doc.openUrl} title={doc.title} style={{ width: "100%", height: "100%", border: "none" }} sandbox="allow-scripts allow-forms allow-same-origin allow-popups" />
        </div>
      )}

      {tab === "editor" && !hasGoogleDoc && (
        <div className="Docs-Editor-Wrapper">
          {doc.canEdit && <div className="Docs-Toolbar">
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("undo"); }} title="Undo">&#x21A9;</button>
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("redo"); }} title="Redo">&#x21AA;</button>
            <span className="Docs-Toolbar-Sep" />
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("bold"); }} title="Bold"><b>B</b></button>
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("italic"); }} title="Italic"><i>I</i></button>
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("underline"); }} title="Underline"><u>U</u></button>
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("strikeThrough"); }} title="Strikethrough"><s>S</s></button>
            <span className="Docs-Toolbar-Sep" />
            <button type="button" className="Docs-Toolbar-Btn Docs-Toolbar-Btn-Wide" onMouseDown={(e) => { e.preventDefault(); execHeading("h1"); }} title="Heading 1">H1</button>
            <button type="button" className="Docs-Toolbar-Btn Docs-Toolbar-Btn-Wide" onMouseDown={(e) => { e.preventDefault(); execHeading("h2"); }} title="Heading 2">H2</button>
            <button type="button" className="Docs-Toolbar-Btn Docs-Toolbar-Btn-Wide" onMouseDown={(e) => { e.preventDefault(); execHeading("h3"); }} title="Heading 3">H3</button>
            <button type="button" className="Docs-Toolbar-Btn Docs-Toolbar-Btn-Wide" onMouseDown={(e) => { e.preventDefault(); execHeading("p"); }} title="Paragraph">P</button>
            <span className="Docs-Toolbar-Sep" />
            <select className="Docs-Toolbar-Select Docs-Toolbar-Select-Wide" onChange={execFont} title="Font Family"><option value="">Font</option><option value="Arial">Arial</option><option value="Times New Roman">Times New Roman</option><option value="Courier New">Courier New</option><option value="Georgia">Georgia</option><option value="Verdana">Verdana</option><option value="Tahoma">Tahoma</option><option value="Trebuchet MS">Trebuchet MS</option><option value="Comic Sans MS">Comic Sans MS</option></select>
            <select className="Docs-Toolbar-Select" onChange={execFontSize} title="Font Size"><option value="">Size</option><option value="1">XS</option><option value="2">S</option><option value="3">M</option><option value="4">L</option><option value="5">XL</option><option value="6">XXL</option></select>
            <input type="color" className="Docs-Toolbar-Color" title="Text Color" onChange={(e) => execColor(e.target.value)} />
            <input type="color" className="Docs-Toolbar-Color" title="Highlight Color" onChange={(e) => execHighlight(e.target.value)} value="#ffff00" />
            <span className="Docs-Toolbar-Sep" />
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("justifyLeft"); }} title="Align Left">&#x2190;</button>
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("justifyCenter"); }} title="Center">&#x2194;</button>
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("justifyRight"); }} title="Align Right">&#x2192;</button>
            <span className="Docs-Toolbar-Sep" />
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("insertUnorderedList"); }} title="Bullet List">&#x2022;</button>
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("insertOrderedList"); }} title="Numbered List">#</button>
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("indent"); }} title="Indent">&#x21B7;</button>
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("outdent"); }} title="Outdent">&#x21B6;</button>
            <span className="Docs-Toolbar-Sep" />
            <button type="button" className="Docs-Toolbar-Btn Docs-Toolbar-Btn-Wide" onMouseDown={(e) => { e.preventDefault(); execLink(); }} title="Insert Link">Link</button>
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("insertHorizontalRule"); }} title="Horizontal Line">&mdash;</button>
            <button type="button" className="Docs-Toolbar-Btn" onMouseDown={(e) => { e.preventDefault(); execCmd("removeFormat"); }} title="Remove Formatting">&#x2716;</button>
          </div>}
          <div
            className="Docs-Editor"
            contentEditable={doc.canEdit}
            suppressContentEditableWarning
            dangerouslySetInnerHTML={{ __html: body }}
            onBlur={(e) => setBody(e.currentTarget.innerHTML)}
            style={{ minHeight: 400, padding: 24, border: "1px solid #e2e8f0", borderRadius: 8, background: "#fff", fontSize: 14, lineHeight: 1.6, outline: "none", cursor: doc.canEdit ? "text" : "default" }}
          />
          {!doc.canEdit && <div style={{ fontSize: 12, color: "#94a3b8", padding: "8px 12px", textAlign: "center", borderTop: "1px solid #e2e8f0" }}>Read-Only View</div>}
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
          {permLoading && <p>Updating Permissions...</p>}
          <SimpleTable
            columns={["User", "Permission", "Actions"]}
            rows={permissions.map((p) => [
              employeeName(data, p.subject_id) || `User #${p.subject_id}`,
              <StatusPill key={p.id} tone={p.permission === "Write" || p.permission === "Owner" ? "green" : "slate"}>{p.permission}</StatusPill>,
              <button key={`rev-${p.id}`} className="Icon-Button" onClick={() => revokePermission(p.subject_id)} style={{ color: "var(--Danger)" }} title="Revoke Permission"><Trash size={14} /></button>
            ])}
          />
          <button className="Soft-Button Small" onClick={() => setPermOpen(true)} style={{ marginTop: 12 }} disabled={permLoading}><Plus size={14} /> Add Permission</button>
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
              <button className="Primary-Button" type="submit" disabled={permLoading}>{permLoading ? "Granting..." : "Grant"}</button>
              <button className="Outline-Button" type="button" onClick={() => setPermOpen(false)} disabled={permLoading}>Cancel</button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
