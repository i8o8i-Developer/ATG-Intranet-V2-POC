import React, { useEffect, useState } from "react";
import { Clock, Plus, Share2, Upload } from "lucide-react";
import "../Styles/DocsScreen.css";

import { apiGet, apiPost } from "../Api/Client.js";
import { EmptyState, Modal, StatusPill, Tabs } from "./Shared/ScreenComponents.jsx";
import { findById, formatDateTime } from "./Shared/ScreenUtils.jsx";

export function DocsScreen({ data, navigate, reload }) {
  const [type, setType] = useState("all");
  const [tab, setTab] = useState("all");
  const [search, setSearch] = useState("");
  const [newOpen, setNewOpen] = useState(false);
  const [myDocs, setMyDocs] = useState(null);
  const [history, setHistory] = useState(null);

  useEffect(() => {
    if (tab === "mine" && !myDocs) apiGet("/AtgDocs/KnowledgeDocuments/my-documents/").then(setMyDocs).catch(() => setMyDocs([]));
    if (tab === "history" && !history) apiGet("/AtgDocs/KnowledgeDocuments/visit-history/").then(setHistory).catch(() => setHistory([]));
  }, [tab, myDocs, history]);

  const allDocs = data.docs || [];
  let docs = allDocs;
  if (tab === "mine") docs = Array.isArray(myDocs) ? myDocs : (myDocs?.documents || myDocs?.results || []);
  else if (tab === "history") docs = Array.isArray(history) ? history : (history?.history || history?.results || []);
  docs = docs.filter((doc) => {
    const typeMatch = type === "all" || String(doc.document_type) === type;
    const term = `${doc.title} ${doc.document_type} ${doc.visibility}`.toLowerCase();
    return typeMatch && (!search || term.includes(search.toLowerCase()));
  });
  const types = ["all", ...new Set(allDocs.map((doc) => doc.document_type).filter(Boolean))];

  return (
    <section className="Docs-Layout">
      <aside className="Docs-Side">
        {types.map((item) => (
          <button key={item} className={item === type ? "active" : ""} onClick={() => setType(item)}>
            {item === "all" ? "All Documents" : item}
          </button>
        ))}
      </aside>
      <main>
        <nav className="Docs-Nav">
          <strong>Across The Globe</strong>
          <span>
            <button onClick={() => navigate("/home/")}>Home</button>
            <button className="Primary-Button Small" onClick={() => setNewOpen(true)}><Plus size={14} /> New Doc</button>
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search For Docs..." />
          </span>
        </nav>
        <Tabs
          value={tab}
          onChange={setTab}
          items={[
            ["all", "All Documents"],
            ["mine", "My Docs"],
            ["history", "History"],
          ]}
        />
        <h1 style={{ marginTop: 12 }}>{type === "all" ? "Documents" : type}</h1>
        <table className="Docs-List">
          <tbody>
            {docs.map((doc) => (
              <tr key={doc.id} onClick={() => navigate(`/docs/post-detail/${doc.id}`)}>
                <td>{doc.title}</td>
                <td><StatusPill tone={doc.visibility === "Private" ? "red" : "green"}>{doc.visibility || "Authenticated User"}</StatusPill></td>
                <td>{doc.document_type}</td>
                <td><Clock size={12} /> {formatDateTime(doc.updated_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!docs.length && <EmptyState label="No Documents Returned From Backend." />}
      </main>
      {newOpen && <NewDocModal onClose={() => setNewOpen(false)} reload={() => { reload(); setMyDocs(null); }} />}
    </section>
  );
}

export function DocsDetailScreen({ data, route, navigate, reload }) {
  const id = route.split("/").filter(Boolean).pop();
  const doc = findById(data.docs, id) || {};
  const [editOpen, setEditOpen] = useState(false);
  const [permOpen, setPermOpen] = useState(false);

  const publish = async () => {
    await apiPost(`/AtgDocs/KnowledgeDocuments/${id}/publish/`, {});
    reload();
  };
  const uploadToDrive = async () => {
    await apiPost(`/AtgDocs/KnowledgeDocuments/${id}/upload-to-drive/`, { folder_name: "Documents", make_public: false });
    reload();
  };

  return (
    <section className="Docs-Detail">
      <nav className="Docs-Nav Dark">
        <strong>Across The Globe</strong>
        <span>
          <button onClick={() => navigate("/docs/")}>Home</button>
          <button onClick={() => setEditOpen(true)}>Edit Doc</button>
          <button onClick={publish}>Publish</button>
          <button onClick={uploadToDrive}><Upload size={13} /> Upload To Drive</button>
          <button onClick={() => setPermOpen(true)}><Share2 size={13} /> Grant Permission</button>
        </span>
      </nav>
      <article>
        <h1>{doc.title || "Document"}</h1>
        <p>Created By {doc.owner_name || ""}</p>
        <p>Last Updated By: {formatDateTime(doc.updated_at)}</p>
        <StatusPill tone={doc.status === "Published" ? "green" : "gold"}>{doc.status || "Draft"}</StatusPill>
        <hr />
        <div className="Doc-Body" dangerouslySetInnerHTML={{ __html: doc.body || doc.metadata?.body || "" }} />
        {!doc.body && !doc.metadata?.body && <p className="Doc-Body">{doc.description || "Document Content Has Not Been Populated Yet."}</p>}
      </article>
      {editOpen && <EditDocModal doc={doc} onClose={() => setEditOpen(false)} reload={reload} />}
      {permOpen && <GrantPermissionModal docId={id} data={data} onClose={() => setPermOpen(false)} reload={reload} />}
    </section>
  );
}

function NewDocModal({ onClose, reload }) {
  const [form, setForm] = useState({ title: "", document_type: "Article", visibility: "Authenticated", status: "Draft", body: "", upload_to_drive: false });
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      await apiPost("/AtgDocs/KnowledgeDocuments/create-document/", form);
      reload();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="New Document" onClose={onClose} wide>
      <div className="Form-Grid Two Modal-Form">
        <label>Title<input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></label>
        <label>Type<input value={form.document_type} onChange={(event) => setForm({ ...form, document_type: event.target.value })} /></label>
        <label>Visibility<select value={form.visibility} onChange={(event) => setForm({ ...form, visibility: event.target.value })}><option>Private</option><option>Authenticated</option><option>Public</option></select></label>
        <label>Status<select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}><option>Draft</option><option>In Review</option><option>Published</option></select></label>
      </div>
      <label>Body<textarea rows={10} value={form.body} onChange={(event) => setForm({ ...form, body: event.target.value })} /></label>
      <label className="Inline-Checkbox"><input type="checkbox" checked={form.upload_to_drive} onChange={(event) => setForm({ ...form, upload_to_drive: event.target.checked })} /> Upload To Drive</label>
      <button className="Primary-Button" onClick={save} disabled={busy || !form.title}>Create Document</button>
    </Modal>
  );
}

function EditDocModal({ doc, onClose, reload }) {
  const [form, setForm] = useState({ title: doc.title || "", body: doc.body || doc.metadata?.body || "", visibility: doc.visibility || "Authenticated", status: doc.status || "Draft", document_type: doc.document_type || "Article" });

  const save = async () => {
    await apiPost(`/AtgDocs/KnowledgeDocuments/${doc.id}/update-content/`, form);
    reload();
    onClose();
  };

  return (
    <Modal title="Edit Document" onClose={onClose} wide>
      <div className="Form-Grid Two Modal-Form">
        <label>Title<input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></label>
        <label>Type<input value={form.document_type} onChange={(event) => setForm({ ...form, document_type: event.target.value })} /></label>
        <label>Visibility<select value={form.visibility} onChange={(event) => setForm({ ...form, visibility: event.target.value })}><option>Private</option><option>Authenticated</option><option>Public</option></select></label>
        <label>Status<select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}><option>Draft</option><option>In Review</option><option>Published</option></select></label>
      </div>
      <label>Body<textarea rows={12} value={form.body} onChange={(event) => setForm({ ...form, body: event.target.value })} /></label>
      <button className="Primary-Button" onClick={save} disabled={!form.title}>Save Document</button>
    </Modal>
  );
}

function GrantPermissionModal({ docId, data, onClose, reload }) {
  const [form, setForm] = useState({ subject_type: "Employee", subject_id: "", permission: "Read", email: "" });
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      await apiPost(`/AtgDocs/KnowledgeDocuments/${docId}/grant-permission/`, form);
      reload();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="Grant Permission" onClose={onClose}>
      <div className="Form-Grid Two Modal-Form">
        <label>Subject Type<select value={form.subject_type} onChange={(event) => setForm({ ...form, subject_type: event.target.value })}><option>Employee</option><option>Department</option><option>Email</option></select></label>
        {form.subject_type === "Email" ? (
          <label>Email<input value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></label>
        ) : form.subject_type === "Department" ? (
          <label>Department<select value={form.subject_id} onChange={(event) => setForm({ ...form, subject_id: event.target.value })}><option value="">Select</option>{(data.departments || []).map((dept) => <option key={dept.id} value={dept.id}>{dept.name}</option>)}</select></label>
        ) : (
          <label>Employee<select value={form.subject_id} onChange={(event) => setForm({ ...form, subject_id: event.target.value })}><option value="">Select</option>{(data.employees || []).map((emp) => <option key={emp.id} value={emp.id}>{emp.display_name}</option>)}</select></label>
        )}
        <label>Permission<select value={form.permission} onChange={(event) => setForm({ ...form, permission: event.target.value })}><option>Read</option><option>Edit</option><option>Manage</option></select></label>
      </div>
      <button className="Primary-Button" onClick={save} disabled={busy || (!form.subject_id && !form.email)}>Grant</button>
    </Modal>
  );
}
