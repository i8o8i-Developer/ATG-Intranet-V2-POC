import React, { useState } from "react";

import { apiPost } from "../Api/Client.js";
import { Panel } from "./Shared/ScreenComponents.jsx";
import { findById } from "./Shared/ScreenUtils.jsx";

export function SendOfferScreen({ data, reload }) {
  const [form, setForm] = useState({ company_name: "ATG", candidate_email: "", candidate_name: "", username: "", department: "", sub_department: "", position_title: "", employment_type: "", pay_type: "Performance Based" });
  const [preview, setPreview] = useState(null);
  const [showHtml, setShowHtml] = useState(false);

  const buildHtmlPreview = () => {
    const dept = findById(data.departments || [], form.department)?.name || "";
    const sub = findById(data.subDepartments || [], form.sub_department)?.name || "";
    return `<!doctype html><html><head><meta charset='utf-8'><style>body{font-family:Inter,Arial,sans-serif;color:#1f2937;margin:0;padding:32px;background:#f8fafc}.card{max-width:720px;margin:0 auto;background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:32px;box-shadow:0 6px 18px rgba(15,23,42,0.06)}h1{margin:0 0 4px;font-size:22px}.muted{color:#64748b;font-size:13px;margin:0 0 24px}table{width:100%;border-collapse:collapse;margin:16px 0}td{padding:8px 0;border-bottom:1px dashed #e5e7eb;vertical-align:top}td.k{color:#64748b;width:200px}strong{color:#0f172a}p.sig{margin-top:32px}.brand{font-weight:700;color:#1e3a8a}</style></head><body><div class='card'><div class='brand'>${form.company_name || "Banao"}</div><h1>Offer Of Employment</h1><p class='muted'>Issued ${new Date().toLocaleDateString()}</p><p>Dear <strong>${form.candidate_name || "Candidate"}</strong>,</p><p>We Are Pleased To Offer You The Position Of <strong>${form.position_title || "—"}</strong> At <strong>${form.company_name || "Banao"}</strong>. Please Find The Key Terms Of Your Engagement Below.</p><table><tbody><tr><td class='k'>Candidate Email</td><td>${form.candidate_email || "—"}</td></tr><tr><td class='k'>Suggested Username</td><td>${form.username || "—"}</td></tr><tr><td class='k'>Department</td><td>${dept || "—"}</td></tr><tr><td class='k'>Sub Department</td><td>${sub || "—"}</td></tr><tr><td class='k'>Position</td><td>${form.position_title || "—"}</td></tr><tr><td class='k'>Employment Type</td><td>${form.employment_type || "—"}</td></tr><tr><td class='k'>Pay Type</td><td>${form.pay_type || "—"}</td></tr></tbody></table><p>This Offer Is Subject To The Standard Terms And Conditions Of ${form.company_name || "Banao"} And Acceptance Of The Code Of Conduct.</p><p class='sig'>Sincerely,<br/><strong>${form.company_name || "Banao"} HR</strong></p></div></body></html>`;
  };

  const submit = async (issue) => {
    const payload = { ...form, offer_payload: { department: form.department, sub_department: form.sub_department, username: form.username, pay_type: form.pay_type, employment_type: form.employment_type } };
    const result = await apiPost(issue ? "/MainApp/Onboard/send-actual-offer" : "/MainApp/Onboard/Send_Offer", payload);
    setPreview(result);
    setShowHtml(false);
    reload(["onboardingOffers"]);
  };

  return (
    <section className="offer-page">
      <div className="offer-actions">
        <button className="outline-button" onClick={() => { setPreview(form); setShowHtml(true); }}>Preview</button>
        <button className="outline-button" onClick={() => submit(true)}>Send Offer</button>
      </div>
      <form className="center-form" onSubmit={(event) => event.preventDefault()}>
        <label>Domain Name:<span className="radio-row">{["ATG", "Banao", "Bunny"].map((name) => <label key={name}><input type="radio" checked={form.company_name === name} onChange={() => setForm({ ...form, company_name: name })} />{name}</label>)}</span></label>
        <h3>Create An Offer</h3>
        <strong>--------Profile Info--------</strong>
        <label>Email<input value={form.candidate_email} onChange={(event) => setForm({ ...form, candidate_email: event.target.value })} /></label>
        <div className="two-col">
          <label>Department Name<select value={form.department} onChange={(event) => setForm({ ...form, department: event.target.value })}><option>Select Department Name</option>{(data.departments || []).map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}</select></label>
          <label>Role Type<input value={form.position_title} onChange={(event) => setForm({ ...form, position_title: event.target.value })} /></label>
        </div>
        <label>Sub Departments<select value={form.sub_department} onChange={(event) => setForm({ ...form, sub_department: event.target.value })}><option>----------</option>{(data.subDepartments || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label>Title<input value={form.position_title} onChange={(event) => setForm({ ...form, position_title: event.target.value })} /></label>
        <div className="two-col">
          <label>Name<input value={form.candidate_name} onChange={(event) => setForm({ ...form, candidate_name: event.target.value })} /></label>
          <label>Username<input value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} /></label>
        </div>
        <div className="two-col">
          <label>Employment Type<input value={form.employment_type} onChange={(event) => setForm({ ...form, employment_type: event.target.value })} /></label>
          <label>Pay Type<select value={form.pay_type} onChange={(event) => setForm({ ...form, pay_type: event.target.value })}><option>Performance Based</option><option>Fixed</option></select></label>
        </div>
        <button className="primary-button" onClick={() => submit(false)}>Create Draft</button>
      </form>
      {showHtml && (
        <Panel title="Offer Preview" right={<button className="soft-button small" onClick={() => setShowHtml(false)}>Close</button>}>
          <iframe title="Offer Preview" srcDoc={buildHtmlPreview()} style={{ width: "100%", minHeight: "560px", border: "1px solid #e5e7eb", borderRadius: "10px", background: "#fff" }} />
        </Panel>
      )}
      {preview && !showHtml && <Panel title="Offer Result"><pre>{JSON.stringify(preview, null, 2)}</pre></Panel>}
    </section>
  );
}