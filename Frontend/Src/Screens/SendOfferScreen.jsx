import React, { useState } from "react";
import { Mail, Send, FileText } from "lucide-react";
import { apiPost } from "../Api/Client.js";
import { Modal } from "./Shared/ScreenComponents.jsx";
import { formatDate } from "./Shared/ScreenUtils.jsx";

function esc(val) { return String(val || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
function fmt(val) { if (!val) return "—"; const d = new Date(val); return isNaN(d) ? String(val) : d.toLocaleDateString("en-GB", { day: "2-digit", month: "long", year: "numeric" }); }
function pascal(val) { return esc(String(val || "").replace(/[_-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()).trim()); }

const OFFER_HTML = (v) => `<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;padding:28px;background:#fff;color:#111;font-family:Georgia,'Times New Roman',serif}
.offer-shell{max-width:860px;margin:0 auto;border:2px solid #111;padding:36px 42px 48px;background:#fff}
.offer-title{text-align:center;font-size:26px;font-weight:700;letter-spacing:1.2px;margin:6px 0 20px;text-transform:uppercase}
.offer-date{text-align:right;margin:10px 0 22px;font-size:14px;color:#475569}
table{width:100%;border-collapse:collapse;margin:16px 0}
td,th{border:1px solid #111;padding:8px 10px;font-size:14px;vertical-align:top}
th{background:#f1f5f9;text-align:left;font-weight:600}
.sign-row{display:flex;justify-content:space-between;margin-top:32px;padding-top:20px;border-top:1px solid #ddd}
.sign-line{width:200px;border-top:1px solid #111;padding-top:4px;font-size:12px;text-align:center}
.footer{text-align:center;margin-top:28px;font-size:12px;color:#94a3b8}
</style></head><body>
<div class="offer-shell">
<div style="text-align:center;font-size:22px;font-weight:800;letter-spacing:2px">ATG</div>
<div style="text-align:center;font-size:11px;color:#64748b;margin-bottom:16px">Across The Globe</div>
<div class="offer-title">Offer Of Employment</div>
<div class="offer-date">Date: ${fmt(v.offerDate)}</div>
<p style="font-size:15px;line-height:1.7;text-align:justify">Dear <strong>${pascal(v.candidateName)}</strong>,</p>
<p style="font-size:15px;line-height:1.7;text-align:justify">We Are Pleased To Offer You The Position Of <strong>${pascal(v.positionTitle)}</strong> With <strong>${pascal(v.companyName || "Banao")}</strong>. We Were Impressed With Your Background And Believe Your Skills Will Be A Valuable Addition To Our Team.</p>
<table><tr><th style="width:40%">Detail</th><th>Value</th></tr>
<tr><td>Position Title</td><td>${pascal(v.positionTitle)}</td></tr>
<tr><td>Department</td><td>${pascal(v.departmentName)}</td></tr>
<tr><td>Sub Department</td><td>${pascal(v.subDepartment)}</td></tr>
<tr><td>Role Type</td><td>${pascal(v.roleType)}</td></tr>
<tr><td>Employee Type</td><td>${pascal(v.empType)}</td></tr>
<tr><td>Pay Type</td><td>${pascal(v.payType)}</td></tr>
<tr><td>Base Pay</td><td>₹${Number(v.basePay || 0).toLocaleString()} / Month</td></tr>
<tr><td>Pay Per Task</td><td>₹${Number(v.payPerTask || 0).toLocaleString()}</td></tr>
${v.internDuration ? `<tr><td>Intern Duration</td><td>${v.internDuration} Months</td></tr>` : ""}
<tr><td>Reporting To</td><td>${pascal(v.reportingTo)}</td></tr>
<tr><td>Location</td><td>${pascal(v.location)}</td></tr>
<tr><td>Joining Date</td><td>${fmt(v.joiningDate)}</td></tr>
</table>
<p style="font-size:15px;line-height:1.7;text-align:justify">Your appointment will be governed by the terms and conditions outlined in this offer letter and the company's standard employment policies. This offer is subject to verification of your credentials and background check.</p>
<p style="font-size:15px;line-height:1.7;text-align:justify">Please indicate your acceptance by signing below and returning this letter. Once signed, you will receive further instructions regarding onboarding documentation and your first day details.</p>
<div class="sign-row">
<div class="sign-line">Authorized Signatory</div>
<div class="sign-line">Candidate Signature</div>
</div>
<div style="margin-top:12px;font-size:13px;text-align:center;color:#64748b">Offer Valid Until: ${fmt(v.expiryDate || new Date(Date.now() + 7 * 86400000))}</div>
<div class="footer">This Is A System-Generated Offer Letter From ATG Intranet. For Queries, Contact HR.</div>
</div></body></html>`;

const NDA_HTML = (v) => `<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;padding:28px;background:#fff;color:#111;font-family:Georgia,'Times New Roman',serif}
.nda-shell{max-width:800px;margin:0 auto;border:2px solid #111;padding:32px 38px}
h1{text-align:center;font-size:22px;font-weight:700;letter-spacing:1px}
h2{font-size:15px;font-weight:600;margin:18px 0 8px}
p{font-size:14px;line-height:1.6;text-align:justify}
.sign-line{width:220px;border-top:1px solid #111;padding-top:4px;font-size:12px;text-align:center;margin-top:24px}
</style></head><body>
<div class="nda-shell">
<h1>Non-Disclosure Agreement</h1>
<p>This Non-Disclosure Agreement (The "Agreement") Is Entered Into By And Between <strong>ATG (Across The Globe)</strong> And <strong>${pascal(v.candidateName)}</strong>.</p>
<h2>1. Definition Of Confidential Information</h2>
<p>"Confidential Information" Shall Include All Information Disclosed By The Company To The Employee, Whether Verbally Or In Writing, Including But Not Limited To: Trade Secrets, Business Plans, Client Data, Technical Specifications, Financial Data, Software Code, And Internal Processes.</p>
<h2>2. Obligations</h2>
<p>The Employee Agrees To: (A) Hold All Confidential Information In Strict Confidence; (B) Not Disclose Such Information To Any Third Party Without Prior Written Consent; (C) Use The Information Solely For The Purpose Of Employment; (D) Return All Materials Upon Termination Of Employment.</p>
<h2>3. Term</h2>
<p>This Agreement Shall Remain In Effect During Employment And For A Period Of Two (2) Years Following The Cessation Of Employment.</p>
<h2>4. Governing Law</h2>
<p>This Agreement Shall Be Governed By The Laws Of India. Any Disputes Arising Hereunder Shall Be Subject To The Exclusive Jurisdiction Of The Courts In Bengaluru, Karnataka.</p>
<div style="text-align:right;margin-top:28px"><div class="sign-line" style="margin-left:auto">${pascal(v.candidateName)}</div></div>
<div style="text-align:right;font-size:11px;color:#94a3b8;margin-top:4px">Signed On: ${fmt(new Date())}</div>
</div></body></html>`;

export function SendOfferScreen({ data, reload }) {
  const [form, setForm] = useState({
    domain: "", candidateEmail: "", departmentName: "", roleType: "", subDepartment: "",
    positionTitle: "", candidateName: "", username: "", empType: "Intern", payType: "Performance Based",
    basePay: "", payPerTask: "", offerDate: new Date().toISOString().split("T")[0], internDuration: "6",
    reportingTo: "", location: "Bengaluru", joiningDate: "", companyName: "Banao",
  });
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);

  const handleChange = (field, value) => setForm({ ...form, [field]: value });

  const sendOffer = async () => {
    setBusy(true);
    setResult(null);
    try {
      const offerHtml = OFFER_HTML(form);
      const ndaHtml = NDA_HTML(form);
      const payload = {
        candidate_name: form.candidateName,
        candidate_email: form.candidateEmail,
        company_name: form.companyName,
        position_title: form.positionTitle,
        offer_type: form.empType,
        offer_payload: { ...form, offerHtml, ndaHtml },
      };
      const resp = await apiPost("/MainApp/Onboard/send-actual-offer/", payload);
      if (resp?.token) {
        setResult({ ok: true, message: `Offer sent to ${form.candidateEmail} successfully.` });
      } else {
        setResult({ ok: false, message: "Failed To Generate Offer Token." });
      }
    } catch (err) {
      setResult({ ok: false, message: err?.payload?.detail || err?.message || "Failed To Send Offer." });
    } finally {
      setBusy(false);
    }
  };

  return (
    <section style={{ padding: "24px 28px", maxWidth: 960, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <span style={{ fontSize: 12, color: "#64748b", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em" }}>HR / Onboarding</span>
          <h1 style={{ margin: "4px 0 0", fontSize: 26, fontWeight: 700 }}>Send Offer Letter</h1>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="Soft-Button Small" onClick={() => setPreview(preview ? null : "offer")}>{preview ? "Hide" : "Preview"} Offer</button>
          <button className="Primary-Button Small" onClick={sendOffer} disabled={busy || !form.candidateEmail || !form.candidateName}>
            <Send size={14} /> {busy ? "Sending..." : "Send Offer"}
          </button>
        </div>
      </div>

      {result && <div className={result.ok ? "Auth-AlertOk" : "Auth-Alert"} style={{ marginBottom: 16 }}>{result.message}</div>}

      <div style={{ display: "grid", gridTemplateColumns: preview ? "1fr 500px" : "1fr", gap: 24 }}>
        <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: 20 }}>
          <h2 style={{ margin: "0 0 16px", fontSize: 15, fontWeight: 600 }}>Candidate & Offer Details</h2>
          <div className="Form-Grid Two" style={{ gap: 12 }}>
            <label>Domain<select className="Mini-Inp" value={form.domain} onChange={(e) => handleChange("domain", e.target.value)}><option value="">Select Domain</option>{(data.domains || []).map((d) => <option key={d.id || d.domain_name} value={d.domain_name || d.name || d}>{d.domain_name || d.name || d}</option>)}</select></label>
            <label>Email<input className="Mini-Inp" value={form.candidateEmail} onChange={(e) => handleChange("candidateEmail", e.target.value)} placeholder="candidate@example.com" /></label>
            <label>Department Name<select className="Mini-Inp" value={form.departmentName} onChange={(e) => handleChange("departmentName", e.target.value)}><option value="">Select Department</option>{(data.departments || []).map((d) => <option key={d.id} value={d.name}>{d.name}</option>)}</select></label>
            <label>Role Type<input className="Mini-Inp" value={form.roleType} onChange={(e) => handleChange("roleType", e.target.value)} placeholder="e.g. Senior Developer" /></label>
            <label>Sub Department<select className="Mini-Inp" value={form.subDepartment} onChange={(e) => handleChange("subDepartment", e.target.value)}><option value="">Select Sub Department</option>{(data.subDepartments || []).filter((s) => { if (!form.departmentName) return true; const dept = (data.departments || []).find((d) => d.name === form.departmentName); return dept && String(s.department) === String(dept.id); }).map((s) => <option key={s.id} value={s.name}>{s.name}</option>)}</select></label>
            <label>Position Title<input className="Mini-Inp" value={form.positionTitle} onChange={(e) => handleChange("positionTitle", e.target.value)} placeholder="React Developer" /></label>
            <label>Candidate Name<input className="Mini-Inp" value={form.candidateName} onChange={(e) => handleChange("candidateName", e.target.value)} placeholder="Full Name" /></label>
            <label>Username<input className="Mini-Inp" value={form.username} onChange={(e) => handleChange("username", e.target.value)} placeholder="username" /></label>
            <label>Employee Type<select className="Mini-Inp" value={form.empType} onChange={(e) => handleChange("empType", e.target.value)}><option>Full-Time</option><option>Part-Time</option><option>Intern</option><option>Contract</option></select></label>
            <label>Pay Type<select className="Mini-Inp" value={form.payType} onChange={(e) => handleChange("payType", e.target.value)}><option>Performance Based</option><option>Fixed</option><option>Monthly</option></select></label>
            <label>Base Pay (₹/Month)<input type="number" min="0" className="Mini-Inp" value={form.basePay} onChange={(e) => handleChange("basePay", e.target.value)} /></label>
            <label>Pay Per Task (₹)<input type="number" min="0" className="Mini-Inp" value={form.payPerTask} onChange={(e) => handleChange("payPerTask", e.target.value)} /></label>
            <label>Offer Date<input type="date" className="Mini-Inp" value={form.offerDate} onChange={(e) => handleChange("offerDate", e.target.value)} /></label>
            <label>Intern Duration (Months)<input type="number" min="1" className="Mini-Inp" value={form.internDuration} onChange={(e) => handleChange("internDuration", e.target.value)} /></label>
            <label>Reporting To<select className="Mini-Inp" value={form.reportingTo} onChange={(e) => handleChange("reportingTo", e.target.value)}><option value="">Select Manager</option>{(data.employees || []).filter((e) => e.status === "Active").map((e) => <option key={e.id} value={e.display_name}>{e.display_name}</option>)}</select></label>
            <label>Location<input className="Mini-Inp" value={form.location} onChange={(e) => handleChange("location", e.target.value)} /></label>
            <label>Joining Date<input type="date" className="Mini-Inp" value={form.joiningDate} onChange={(e) => handleChange("joiningDate", e.target.value)} /></label>
            <label>Company Name<input className="Mini-Inp" value={form.companyName} onChange={(e) => handleChange("companyName", e.target.value)} /></label>
          </div>
        </div>

        {preview && (
          <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, overflow: "hidden" }}>
            <div style={{ padding: "10px 16px", background: "#f8fafc", borderBottom: "1px solid #e2e8f0", fontSize: 13, fontWeight: 600 }}>Offer Preview</div>
            <iframe srcDoc={OFFER_HTML(form)} title="Offer Preview" style={{ width: "100%", height: "80vh", border: "none" }} />
          </div>
        )}
      </div>
    </section>
  );
}
