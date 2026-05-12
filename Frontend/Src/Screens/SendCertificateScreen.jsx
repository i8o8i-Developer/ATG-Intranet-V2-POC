import React, { useMemo, useState } from "react";
import { Award, FileSignature, Plus, Save, ShieldCheck } from "lucide-react";

import { apiPost } from "../Api/Client.js";
import "../Styles/CertScreen.css";
import { Modal, Panel, Tabs } from "./Shared/ScreenComponents.jsx";
import { findById } from "./Shared/ScreenUtils.jsx";

const CERTIFICATE_TYPES = [
  { id: "Completion", label: "Internship / EngagementCompletion", color: "#7a5a1f", subtitle: "OFCOMPLETION" },
  { id: "Experience", label: "ExperienceLetter", color: "#1d4e89", subtitle: "OFEXPERIENCE" },
  { id: "Achievement", label: "Achievement / Award", color: "#a4133c", subtitle: "OFACHIEVEMENT" },
  { id: "Recognition", label: "Recognition", color: "#0f766e", subtitle: "OFRECOGNITION" },
  { id: "Custom", label: "Custom (UseTemplate)", color: "#4b5563", subtitle: "" },
];

function fmtDate(value) {
  return value ? new Date(value).toLocaleDateString("en-GB", { day: "2-digit", month: "long", year: "numeric" }) : "—";
}

function applyTemplate(template, vars) {
  if (!template) return "";
  return String(template).replace(/\{\{\s*([\w.]+)\s*\}\}/g, (_, key) => (vars[key] ?? `{{${key}}}`));
}

function defaultBody(typeId, vars) {
  if (typeId === "Experience") {
    return `<p>This Is To Certify That <strong>${vars.name}</strong> Has Been Associated With Us As <strong>${vars.position}</strong> From <strong>${vars.joined}</strong> To <strong>${vars.completion}</strong>.</p><p>During This Tenure, Key Contributions Included <strong>${vars.responsibilities || "—"}</strong>. We Wish Them Success In Future Endeavours.</p>`;
  }
  if (typeId === "Achievement") {
    return `<p>Awarded To <strong>${vars.name}</strong> In Recognition Of Outstanding Achievement In <strong>${vars.responsibilities || vars.position}</strong> On   <strong>${vars.completion}</strong>.</p>`;
  }
  if (typeId === "Recognition") {
    return `<p>We Hereby Recognise <strong>${vars.name}</strong> For Exceptional Contribution As <strong>${vars.position}</strong>. ${vars.responsibilities ? `Highlights: <strong>${vars.responsibilities}</strong>.` : ""}</p>`;
  }
  return `<p>This Is To Certify That <strong>${vars.name}</strong> Has Successfully Served As <strong>${vars.position}</strong> With Major Responsibilities Including <strong>${vars.responsibilities || "—"}</strong>, From <strong>${vars.joined}</strong> To <strong>${vars.completion}</strong>.</p><p>We Acknowledge The Dedication, Commitment And Contribution Made During This Engagement.</p>`;
}

function buildCertificateHtml({ typeId, body, vars, accent }) {
  const type = CERTIFICATE_TYPES.find((item) => item.id === typeId) || CERTIFICATE_TYPES[0];
  const accentColor = accent || type.color;
  return `<!doctype html><html><head><meta charset='Utf-8'><style>
    body{margin:0;padding:28px;background:#ffffff;color:#111827;font-family:Georgia,'TimesNewRoman',serif}
    .certificate-shell{max-width:860px;margin:0 auto;border:2px solid ${accentColor};padding:34px 42px 48px;background:#fff}
    .certificate-logo{text-align:center;margin-bottom:18px;font-size:30px;font-weight:700;color:${accentColor};letter-spacing:2px}
    .certificate-date{text-align:right;font-size:14px;margin-bottom:18px}
    .certificate-heading{text-align:center;font-size:24px;font-weight:700;text-decoration:underline;margin-bottom:24px}
    .certificate-type{text-align:center;font-size:13px;letter-spacing:2px;color:${accentColor};margin:-12px 0 22px}
    .certificate-copy{font-size:15px;line-height:1.8;text-align:justify;color:#111827}
    .certificate-copy p{margin:0 0 14px}
    .certificate-signature{margin-top:26px;font-size:15px;line-height:1.7}
    .certificate-footer{text-align:center;font-size:10px;margin-top:34px;color:#475467}
  </style></head><body><div class='Certificate-Shell'>
    <div class='Certificate-Logo'>ATG</div>
    <div class='Certificate-Date'><strong>${new Date().toLocaleDateString("en-GB", { day: "2-digit", month: "long", year: "numeric" })}</strong></div>
    <div class='Certificate-Heading'>TO WHOMSOEVER IT MAY CONCERN</div>
    <div class='Certificate-Type'>${type.subtitle || (typeId || "").toUpperCase()}</div>
    <div class='Certificate-Copy'>${body}</div>
    <div class='Certificate-Signature'>${vars.issuer || "SaurabhBassi"}<br/>Across The Globe (ATG)</div>
    <div class='Certificate-Footer'>Across The Globe (ATG)<br/>ATGWorld Networks Pvt. Ltd.<br/>809/1, Ferns Paradise, Doddanekundi, Bengaluru, KA, India - 560048</div>
  </div></body></html>`;
}

export function SendCertificateScreen({ data, reload }) {
  const [tab, setTab] = useState("issue");
  const employees = data.employees || [];
  const templates = (data.contentTemplates || []).filter((tpl) => /certificate|experience|achievement|completion/i.test(`${tpl.code || ""} ${tpl.title || ""} ${tpl.category || ""}`));

  const [form, setForm] = useState({
    typeId: "Completion",
    selectedEmployees: [],
    joined_on: "",
    completion_date: "",
    position: "",
    responsibilities: "",
    issuer: "BanaoHR",
    accent: "",
    templateId: "",
    customBody: "",
    send: true,
  });
  const [showPreview, setShowPreview] = useState(false);
  const [busy, setBusy] = useState(false);
  const [results, setResults] = useState([]);
  const [createTemplateOpen, setCreateTemplateOpen] = useState(false);

  const previewEmployee = findById(employees, form.selectedEmployees[0]) || employees[0] || {};
  const previewVars = {
    name: previewEmployee.display_name || previewEmployee.candidate_name || previewEmployee.username || "Recipient",
    position: form.position || previewEmployee.position_title || "TeamMember",
    responsibilities: form.responsibilities,
    joined: fmtDate(form.joined_on || previewEmployee.joined_on),
    completion: fmtDate(form.completion_date),
    issuer: form.issuer,
  };
  const selectedTemplate = templates.find((tpl) => String(tpl.id) === String(form.templateId));
  const body = useMemo(() => {
    if (form.typeId === "Custom" && form.customBody) return applyTemplate(form.customBody, previewVars);
    if (selectedTemplate?.body) return applyTemplate(selectedTemplate.body, previewVars);
    return defaultBody(form.typeId, previewVars);
  }, [form.typeId, form.customBody, selectedTemplate, previewVars]);

  const html = buildCertificateHtml({ typeId: form.typeId, body, vars: previewVars, accent: form.accent });

  const toggleEmployee = (id) => {
    setForm((prev) => prev.selectedEmployees.includes(id)
      ? { ...prev, selectedEmployees: prev.selectedEmployees.filter((value) => value !== id) }
      : { ...prev, selectedEmployees: [...prev.selectedEmployees, id] });
  };

  const submit = async () => {
    if (!form.selectedEmployees.length) return;
    setBusy(true);
    const issued = [];
    try {
      for (const id of form.selectedEmployees) {
        const employee = findById(employees, id);
        if (!employee) continue;
        const vars = {
          name: employee.display_name || employee.candidate_name || employee.username || "Recipient",
          position: form.position || employee.position_title || "TeamMember",
          responsibilities: form.responsibilities,
          joined: fmtDate(form.joined_on || employee.joined_on),
          completion: fmtDate(form.completion_date),
          issuer: form.issuer,
        };
        const renderedBody = form.typeId === "Custom" && form.customBody
          ? applyTemplate(form.customBody, vars)
          : selectedTemplate?.body
            ? applyTemplate(selectedTemplate.body, vars)
            : defaultBody(form.typeId, vars);
        const certificateHtml = buildCertificateHtml({ typeId: form.typeId, body: renderedBody, vars, accent: form.accent });
        try {
          const response = await apiPost("/MainApp/send-certificate", {
            recipient: employee.user,
            title: `${form.typeId} Certificate For ${vars.name}`,
            metadata: {
              certificate_type: form.typeId,
              template_id: form.templateId || null,
              position: form.position,
              responsibilities: form.responsibilities,
              joined_on: form.joined_on,
              completion_date: form.completion_date,
              issuer: form.issuer,
              html: certificateHtml,
            },
          });
          issued.push({ employee: vars.name, ok: true, response });
        } catch (error) {
          issued.push({ employee: vars.name, ok: false, error: error?.data || error?.message });
        }
      }
      setResults(issued);
      reload(["employeeCertificates", "notifications"]);
    } finally { setBusy(false); }
  };

  return (
    <section className="Certificate-Page Screen-Stack">
      <Tabs value={tab} onChange={setTab} items={[["issue", "IssueCertificates"], ["templates", "Templates"]]} />

      {tab === "issue" && (
        <>
          <Panel title={<span><Award size={18} /> Issue Certificates</span>} subtitle="Pick A Type, Choose Recipients, Customise Content, Preview, Then Send.">
            <div className="Form-Grid Two">
              <label>Certificate Type
                <select value={form.typeId} onChange={(event) => setForm({ ...form, typeId: event.target.value, templateId: "" })}>
                  {CERTIFICATE_TYPES.map((type) => <option key={type.id} value={type.id}>{type.label}</option>)}
                </select>
              </label>
              <label>Template (optional)
                <select value={form.templateId} onChange={(event) => setForm({ ...form, templateId: event.target.value })}>
                  <option value="">— Use Default Body —</option>
                  {templates.map((tpl) => <option key={tpl.id} value={tpl.id}>{tpl.title || tpl.code}</option>)}
                </select>
              </label>
              <label>Position / Role<input value={form.position} onChange={(event) => setForm({ ...form, position: event.target.value })} /></label>
              <label>Issuer<input value={form.issuer} onChange={(event) => setForm({ ...form, issuer: event.target.value })} /></label>
              <label>Joining Date<input type="date" value={form.joined_on} onChange={(event) => setForm({ ...form, joined_on: event.target.value })} /></label>
              <label>Completion Date<input type="date" value={form.completion_date} onChange={(event) => setForm({ ...form, completion_date: event.target.value })} /></label>
              <label className="Span-2">Responsibilities / Highlights<input value={form.responsibilities} onChange={(event) => setForm({ ...form, responsibilities: event.target.value })} /></label>
              <label>Accent Colour<input type="color" value={form.accent || (CERTIFICATE_TYPES.find((t) => t.id === form.typeId)?.color || "#7a5a1f")} onChange={(event) => setForm({ ...form, accent: event.target.value })} /></label>
              {form.typeId === "Custom" && (
                <label className="Span-2">Custom Body (HTML, supports {"{{name}}"}, {"{{position}}"}, {"{{joined}}"}, {"{{completion}}"}, {"{{responsibilities}}"})
                  <textarea rows={6} value={form.customBody} onChange={(event) => setForm({ ...form, customBody: event.target.value })} />
                </label>
              )}
            </div>
          </Panel>

          <Panel title={<span><ShieldCheck size={18} /> Recipients ({form.selectedEmployees.length})</span>} right={(
            <div className="Button-Pair">
              <button className="Outline-Button" onClick={() => setShowPreview((value) => !value)}>{showPreview ? "Hide Preview" : "Preview"}</button>
              <button className="Primary-Button" onClick={submit} disabled={busy || !form.selectedEmployees.length}>
                {busy ? "Sending…" : `Issue To ${form.selectedEmployees.length || "—"}`}
              </button>
            </div>
          )}>
            <div className="Recipient-Grid">
              {employees.map((employee) => {
                const checked = form.selectedEmployees.includes(employee.id);
                return (
                  <label key={employee.id} className={checked ? "Recipient-CardActive" : "Recipient-Card"}>
                    <input type="checkbox" checked={checked} onChange={() => toggleEmployee(employee.id)} />
                    <div>
                      <strong>{employee.display_name || employee.candidate_name || `#${employee.id}`}</strong>
                      <small>{employee.position_title || "—"} · {employee.candidate_email || ""}</small>
                    </div>
                  </label>
                );
              })}
              {!employees.length && <p>No Employees Available.</p>}
            </div>
          </Panel>

          {showPreview && (
            <Panel title="Certificate Preview" right={<button className="Soft-Button Small" onClick={() => setShowPreview(false)}>Close</button>}>
              <iframe title="CertificatePreview" srcDoc={html} style={{ width: "100%", minHeight: "560px", border: "1pxSolid #E5e7eb", borderRadius: "10px", background: "#fff" }} />
            </Panel>
          )}

          {results.length > 0 && (
            <Panel title={`Send Result (${results.filter((row) => row.ok).length}/${results.length})`}>
              <ul>
                {results.map((row, index) => (
                  <li key={index}>{row.ok ? "✅" : "❌"} {row.employee}{row.error ? ` — ${typeof row.error === "string" ? row.error : JSON.stringify(row.error)}` : ""}</li>
                ))}
              </ul>
            </Panel>
          )}
        </>
      )}

      {tab === "templates" && (
        <Panel title={<span><FileSignature size={18} /> Certificate Templates</span>} right={<button className="Primary-Button Small" onClick={() => setCreateTemplateOpen(true)}><Plus size={14} /> New Template</button>}>
          <table className="Erp-Table">
            <thead><tr><th>Title</th><th>Category</th><th>Variables</th><th>Updated</th></tr></thead>
            <tbody>
              {templates.map((tpl) => (
                <tr key={tpl.id}>
                  <td>{tpl.title || tpl.code}</td>
                  <td>{tpl.category || "Certificate"}</td>
                  <td>{(tpl.variables || []).join(", ") || "—"}</td>
                  <td>{tpl.updated_at || "—"}</td>
                </tr>
              ))}
              {!templates.length && <tr><td colSpan={4}>No Certificate Templates Yet. Create One To Make Issuing Repeatable.</td></tr>}
            </tbody>
          </table>
        </Panel>
      )}

      {createTemplateOpen && <CreateCertificateTemplateModal onClose={() => setCreateTemplateOpen(false)} reload={reload} />}
    </section>
  );
}

function CreateCertificateTemplateModal({ onClose, reload }) {
  const [form, setForm] = useState({ title: "", category: "Certificate", code: "", body: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const save = async () => {
    if (!form.title || !form.body) return;
    setBusy(true);
    setError("");
    try {
      await apiPost("/HtmlTemplate/ContentTemplates/", { ...form, status: "Active", variables: ["name", "position", "joined", "completion", "responsibilities"] });
      reload(["contentTemplates"]);
      onClose();
    } catch (err) {
      setError(err?.data ? JSON.stringify(err.data) : err?.message || "Failed To Save Template.");
    } finally { setBusy(false); }
  };
  return (
    <Modal title="New Certificate Template" onClose={onClose} wide>
      <div className="Form-Grid Two Modal-Form">
        <label>Title<input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></label>
        <label>Code<input value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value })} /></label>
        <label>Category<select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}><option>Certificate</option><option>Letter</option><option>Award</option></select></label>
      </div>
      <label>Body (HTML, use {"{{name}}"}, {"{{position}}"}, {"{{joined}}"}, {"{{completion}}"}, {"{{responsibilities}}"})
        <textarea rows={10} value={form.body} onChange={(event) => setForm({ ...form, body: event.target.value })} />
      </label>
      {error && <p style={{ color: "#b91c1c" }}>{error}</p>}
      <button className="Primary-Button" onClick={save} disabled={busy || !form.title || !form.body}><Save size={14} /> {busy ? "Saving…" : "Save Template"}</button>
    </Modal>
  );
}
