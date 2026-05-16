import React, { useMemo, useState } from "react";
import { Award, ShieldCheck } from "lucide-react";

import { apiPost } from "../Api/Client.js";
import "../Styles/CertScreen.css";
import { findById } from "./Shared/ScreenUtils.jsx";

const CERTIFICATE_TYPES = [
  { id: "Completion",   label: "Internship / Engagement Completion", color: "#7a5a1f", subtitle: "OF COMPLETION" },
  { id: "Experience",   label: "Experience Letter",                  color: "#1d4e89", subtitle: "OF EXPERIENCE" },
  { id: "Achievement",  label: "Achievement / Award",                color: "#a4133c", subtitle: "OF ACHIEVEMENT" },
  { id: "Recognition",  label: "Recognition",                        color: "#0f766e", subtitle: "OF RECOGNITION" },
];

function esc(val) { return String(val || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
function fmtDate(value) {
  return value ? esc(new Date(value).toLocaleDateString("en-GB", { day: "2-digit", month: "long", year: "numeric" })) : "—";
}

function defaultBody(typeId, vars) {
  const e = (v) => esc(v);
  if (typeId === "Experience") {
    return `<p>This Is To Certify That <strong>${e(vars.name)}</strong> Has Been Associated With Us As <strong>${e(vars.position)}</strong> From <strong>${e(vars.joined)}</strong> To <strong>${e(vars.completion)}</strong>.</p><p>During This Tenure, Key Contributions Included <strong>${e(vars.responsibilities) || "—"}</strong>. We Wish Them Success In Future Endeavours.</p>`;
  }
  if (typeId === "Achievement") {
    return `<p>Awarded To <strong>${e(vars.name)}</strong> In Recognition Of Outstanding Achievement In <strong>${e(vars.responsibilities || vars.position)}</strong> On <strong>${e(vars.completion)}</strong>.</p>`;
  }
  if (typeId === "Recognition") {
    return `<p>We Hereby Recognise <strong>${e(vars.name)}</strong> For Exceptional Contribution As <strong>${e(vars.position)}</strong>. ${vars.responsibilities ? `Highlights: <strong>${e(vars.responsibilities)}</strong>.` : ""}</p>`;
  }
  return `<p>This Is To Certify That <strong>${e(vars.name)}</strong> Has Successfully Served As <strong>${e(vars.position)}</strong> With Major Responsibilities Including <strong>${e(vars.responsibilities) || "—"}</strong>, From <strong>${e(vars.joined)}</strong> To <strong>${e(vars.completion)}</strong>.</p><p>We Acknowledge The Dedication, Commitment And Contribution Made During This Engagement.</p>`;
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
    <div class='Certificate-Signature'>${esc(vars.issuer) || "Saurabh Bassi"}<br/>Across The Globe (ATG)</div>
    <div class='Certificate-Footer'>Across The Globe (ATG)<br/>ATGWorld Networks Pvt. Ltd.<br/>809/1, Ferns Paradise, Doddanekundi, Bengaluru, KA, India - 560048</div>
  </div></body></html>`;
}

export function SendCertificateScreen({ data, reload }) {
  const employees = data.employees || [];

  const [form, setForm] = useState({
    typeId: "Completion",
    selectedEmployees: [],
    joined_on: "",
    completion_date: "",
    position: "",
    responsibilities: "",
    issuer: "Saurabh Bassi",
    accent: "",
  });
  const [showPreview, setShowPreview] = useState(false);
  const [busy, setBusy] = useState(false);
  const [results, setResults] = useState([]);

  const previewEmployee = findById(employees, form.selectedEmployees[0]) || employees[0] || {};
  const previewVars = {
    name: previewEmployee.display_name || previewEmployee.candidate_name || previewEmployee.username || "Recipient",
    position: form.position || previewEmployee.position_title || "Team Member",
    responsibilities: form.responsibilities,
    joined: fmtDate(form.joined_on || previewEmployee.joined_on),
    completion: fmtDate(form.completion_date),
    issuer: form.issuer,
  };
  const body = useMemo(() => defaultBody(form.typeId, previewVars), [form.typeId, previewVars]);
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
          position: form.position || employee.position_title || "Team Member",
          responsibilities: form.responsibilities,
          joined: fmtDate(form.joined_on || employee.joined_on),
          completion: fmtDate(form.completion_date),
          issuer: form.issuer,
        };
        const renderedBody = defaultBody(form.typeId, vars);
        const certificateHtml = buildCertificateHtml({ typeId: form.typeId, body: renderedBody, vars, accent: form.accent });
        try {
          const response = await apiPost("/MainApp/send-certificate", {
            recipient: employee.user,
            title: `${form.typeId} Certificate For ${vars.name}`,
            metadata: {
              certificate_type: form.typeId,
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
    <section className="CT">
      <div className="CT" style={{ padding: 0, gap: 20 }}>
        <div className="CT-Card">
          <div className="CT-CardHead"><h2><Award size={18} /> Issue Certificates</h2><p>Select Type, Recipients, Fill Details, Preview, Then Send.</p></div>
          <div className="CT-CardBody">
            <div className="CT-Form">
              <label>Certificate Type
                <select value={form.typeId} onChange={(event) => setForm({ ...form, typeId: event.target.value })}>
                  {CERTIFICATE_TYPES.map((type) => <option key={type.id} value={type.id}>{type.label}</option>)}
                </select>
              </label>
              <label>Position / Role<input value={form.position} onChange={(event) => setForm({ ...form, position: event.target.value })} /></label>
              <label>Issuer<input value={form.issuer} onChange={(event) => setForm({ ...form, issuer: event.target.value })} /></label>
              <label>Joining Date<input type="date" value={form.joined_on} onChange={(event) => setForm({ ...form, joined_on: event.target.value })} /></label>
              <label>Completion Date<input type="date" value={form.completion_date} onChange={(event) => setForm({ ...form, completion_date: event.target.value })} /></label>
              <label className="CT-Span2">Responsibilities / Highlights<input value={form.responsibilities} onChange={(event) => setForm({ ...form, responsibilities: event.target.value })} /></label>
              <label>Accent Colour<input type="color" value={form.accent || (CERTIFICATE_TYPES.find((t) => t.id === form.typeId)?.color || "#7a5a1f")} onChange={(event) => setForm({ ...form, accent: event.target.value })} /></label>
            </div>
          </div>
        </div>

        <div className="CT-Card">
          <div className="CT-CardHead">
            <h2><ShieldCheck size={18} /> Recipients ({form.selectedEmployees.length})</h2>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="Outline-Button" onClick={() => setShowPreview((v) => !v)}>{showPreview ? "Hide Preview" : "Preview"}</button>
              <button className="Primary-Button" onClick={submit} disabled={busy || !form.selectedEmployees.length}>
                {busy ? "Sending..." : `Issue To ${form.selectedEmployees.length || "—"}`}
              </button>
            </div>
          </div>
          <div className="CT-CardBody">
            <div className="CT-Recipients">
              {employees.map((employee) => {
                const checked = form.selectedEmployees.includes(employee.id);
                return (
                  <label key={employee.id} className={checked ? "CT-RecipCard Active" : "CT-RecipCard"}>
                    <input type="checkbox" checked={checked} onChange={() => toggleEmployee(employee.id)} />
                    <div>
                      <strong>{employee.display_name || employee.candidate_name || `#${employee.id}`}</strong>
                      <small>{employee.position_title || "—"}</small>
                    </div>
                  </label>
                );
              })}
              {!employees.length && <p>No Employees Available.</p>}
            </div>
          </div>
        </div>

        {showPreview && (
          <div className="CT-Card CT-Preview">
            <div className="CT-CardHead"><h2>Certificate Preview</h2><button className="Outline-Button" onClick={() => setShowPreview(false)}>Close</button></div>
            <div className="CT-CardBody"><iframe title="CertificatePreview" srcDoc={html} /></div>
          </div>
        )}

        {results.length > 0 && (
          <div className="CT-Card">
            <div className="CT-CardHead"><h2>Send Result ({results.filter((r) => r.ok).length}/{results.length})</h2></div>
            <div className="CT-CardBody">
              <ul className="CT-Results">
                {results.map((row, index) => (
                  <li key={index}>{row.ok ? "✅" : "❌"} {row.employee}{row.error ? ` — ${typeof row.error === "string" ? row.error : JSON.stringify(row.error)}` : ""}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}