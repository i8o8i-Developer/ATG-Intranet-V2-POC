import React, { useEffect, useMemo, useState } from "react";

import { apiPost } from "../Api/Client.js";
import { Panel, SimpleTable, StatCard, StatusPill, Tabs } from "./Shared/ScreenComponents.jsx";
import { findById, formatDate, isoDate } from "./Shared/ScreenUtils.jsx";

function normalizeLabel(value = "") {
  return String(value || "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function renderTemplate(template = "", variables = {}) {
  let rendered = String(template || "");
  Object.entries(variables).forEach(([key, value]) => {
    const safeValue = value === undefined || value === null ? "" : String(value);
    rendered = rendered.replace(new RegExp(`{{\\s*${key}\\s*}}`, "g"), safeValue);
  });
  return rendered.replace(/{{\s*[a-zA-Z_][a-zA-Z0-9_]*\s*}}/g, "");
}

function displayDate(value) {
  if (!value) return new Date().toLocaleDateString("en-GB");
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString("en-GB");
}

function defaultEmailTemplate() {
  return "<div style='padding:32px;font-family:Arial,Helvetica,sans-serif;background:#f5f7fb'><div style='max-width:680px;margin:0 auto;background:#fff;border:1px solid #dfe5ee;border-radius:18px;padding:28px'><h2 style='margin-top:0'>Onboarding Email</h2><p>Hi {{ candidate_name }},</p><p>Your offer for <strong>{{ position_title }}</strong> with <strong>{{ company_name }}</strong> is ready.</p><p><a href='{{ offer_url }}'>Open offer</a></p></div></div>";
}

function defaultOfferTemplate() {
  return `<!doctype html>
  <html>
    <head>
      <meta charset="utf-8" />
      <style>
        body { margin: 0; padding: 28px; background: #ffffff; color: #111827; font-family: Georgia, 'Times New Roman', serif; }
        .offer-shell { max-width: 860px; margin: 0 auto; border: 2px solid #111827; padding: 36px 42px 48px; }
        .offer-logo { text-align: center; margin-bottom: 18px; }
        .offer-logo img { width: 100%; max-width: 520px; height: auto; }
        .offer-title { text-align: center; font-size: 27px; font-weight: 700; letter-spacing: 1.4px; margin: 6px 0 0; }
        .offer-date { text-align: right; margin: 18px 0 22px; font-size: 15px; }
        .offer-copy { font-size: 15px; line-height: 1.72; margin: 0 0 14px; text-align: justify; }
        .offer-table { width: 100%; border-collapse: collapse; margin: 20px 0 24px; }
        .offer-table td, .offer-table th { border: 1px solid #111827; padding: 10px 12px; vertical-align: top; }
        .offer-table th { background: #efefef; text-align: left; }
      </style>
    </head>
    <body>
      <div class="offer-shell">
        <div class="offer-logo"><img src="https://i.postimg.cc/kgHvKMLz/employed-India-Logo.png" alt="ATG Offer Letter" /></div>
        <div class="offer-title">{{ offer_heading }}</div>
        {{ offer_disclaimer }}
        <div class="offer-date"><strong>{{ joining_date }}</strong></div>
        <p class="offer-copy">Dear Mr./Ms. {{ candidate_name }},</p>
        <p class="offer-copy">We are pleased to offer you the position of <strong>{{ position_title }}</strong> with <strong>{{ company_name }}</strong>. This fallback template is ready to preview and send even before the synced library finishes loading.</p>
        <table class="offer-table">
          <tbody>
            <tr><th style="width:34%">Designation</th><td>{{ position_title }}</td></tr>
            <tr><th>Date of Joining / Issue</th><td>{{ joining_date }}</td></tr>
            <tr><th>Department</th><td>{{ department_name }}</td></tr>
            <tr><th>Sub Department</th><td>{{ sub_department_name }}</td></tr>
            <tr><th>Employment Type</th><td>{{ employment_type }}</td></tr>
            <tr><th>Compensation</th><td>{{ pay_type }}</td></tr>
            <tr><th>System Username</th><td>{{ username }}</td></tr>
            <tr><th>Candidate Email</th><td>{{ candidate_email }}</td></tr>
          </tbody>
        </table>
        <p class="offer-copy">This offer remains subject to company policy and onboarding formalities communicated by the hiring team.</p>
      </div>
    </body>
  </html>`;
}

function templateSummary(template) {
  return template?.metadata?.summary || template?.position || template?.name || "Legacy offer template";
}

export function SendOfferScreen({ data, reload }) {
  const [form, setForm] = useState({
    company_name: "ATG",
    candidate_email: "",
    candidate_name: "",
    username: "",
    department: "",
    sub_department: "",
    position_title: "",
    employment_type: "Intern",
    pay_type: "Performance Based",
    joining_date: isoDate(new Date()),
    template_search: "",
  });
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [previewMode, setPreviewMode] = useState("offer");
  const [showPreview, setShowPreview] = useState(false);
  const [result, setResult] = useState(null);
  const [busyAction, setBusyAction] = useState("");
  const [autoBootstrapState, setAutoBootstrapState] = useState("idle");

  const departmentName = findById(data.departments || [], form.department)?.name || "";
  const subDepartmentName = findById(data.subDepartments || [], form.sub_department)?.name || "";
  const recentOffers = (data.offers || []).slice(0, 8);

  const templates = useMemo(() => {
    return (data.contentTemplates || [])
      .filter((item) => String(item.template_type || "").toLowerCase() === "offer")
      .sort((left, right) => String(left.name || "").localeCompare(String(right.name || "")));
  }, [data.contentTemplates]);

  const searchedTemplates = useMemo(() => {
    const search = form.template_search.trim().toLowerCase();
    return templates.filter((template) => {
      const searchBlob = `${template.name || ""} ${template.position || ""} ${templateSummary(template)} ${normalizeLabel(template.metadata?.template_key || "")}`.toLowerCase();
      return !search || searchBlob.includes(search);
    });
  }, [form.template_search, templates]);

  const exactDomainTemplates = useMemo(
    () => searchedTemplates.filter((template) => String(template.offer_domain || "").toLowerCase() === String(form.company_name || "").toLowerCase()),
    [form.company_name, searchedTemplates],
  );

  const legacyLibraryCount = useMemo(
    () => templates.filter((template) => template?.metadata?.source === "legacy-offer-library").length,
    [templates],
  );

  const showingFallbackLibrary = !exactDomainTemplates.length && searchedTemplates.length > 0;
  const formReady = Boolean(String(form.candidate_name || "").trim() && String(form.candidate_email || "").trim());

  const visibleTemplates = useMemo(() => {
    return exactDomainTemplates.length ? exactDomainTemplates : searchedTemplates;
  }, [exactDomainTemplates, searchedTemplates]);

  useEffect(() => {
    if (autoBootstrapState !== "idle") return;
    if (busyAction) return;
    if (exactDomainTemplates.length) return;
    if (legacyLibraryCount >= 10) return;
    let active = true;
    setAutoBootstrapState("running");
    (async () => {
      try {
        await apiPost("/HtmlTemplate/GenericHtmlTemplates/sync-legacy-library/", {});
        if (!active) return;
        setAutoBootstrapState("done");
        reload(["contentTemplates", "genericHtmlTemplates", "offerTemplates"]);
      } catch (error) {
        if (!active) return;
        setAutoBootstrapState("failed");
        setResult({ mode: "sync_error", response: error?.data || { error: error?.message || "Unable to sync legacy templates." } });
      }
    })();
    return () => {
      active = false;
    };
  }, [autoBootstrapState, busyAction, exactDomainTemplates.length, legacyLibraryCount, reload]);

  useEffect(() => {
    if (!visibleTemplates.length) {
      setSelectedTemplateId("");
      return;
    }
    if (!visibleTemplates.some((template) => String(template.id) === String(selectedTemplateId))) {
      setSelectedTemplateId(String(visibleTemplates[0].id));
    }
  }, [selectedTemplateId, visibleTemplates]);

  const selectedTemplate = useMemo(
    () => visibleTemplates.find((template) => String(template.id) === String(selectedTemplateId)) || null,
    [selectedTemplateId, visibleTemplates],
  );

  const templateVariables = useMemo(() => {
    const effectivePosition = form.position_title || selectedTemplate?.position || "Intern";
    return {
      candidate_name: form.candidate_name || "Candidate",
      candidate_email: form.candidate_email || "candidate@example.com",
      company_name: form.company_name || selectedTemplate?.offer_domain || "ATG",
      position_title: effectivePosition,
      department_name: departmentName || "General",
      sub_department_name: subDepartmentName || "-",
      username: form.username || form.candidate_email.split("@")[0] || "candidate",
      employment_type: form.employment_type || selectedTemplate?.offer_type || "Intern",
      pay_type: form.pay_type || "Performance Based",
      joining_date: displayDate(form.joining_date),
      offer_heading: "PROVISIONAL OFFER LETTER",
      offer_disclaimer: "<p style='text-align:center;margin:8px 0 22px;font-size:13px;font-weight:700;'>This is a provisional offer letter. This is NOT an actual offer letter which will be sent after successful first month completion.</p>",
      offer_url: `${window.location.origin}/offer/accept/DEMO_TOKEN`,
    };
  }, [departmentName, form.candidate_email, form.candidate_name, form.company_name, form.employment_type, form.joining_date, form.pay_type, form.position_title, form.username, selectedTemplate?.offer_domain, selectedTemplate?.offer_type, selectedTemplate?.position, subDepartmentName]);

  const offerPreviewHtml = useMemo(() => renderTemplate(selectedTemplate?.body_html || defaultOfferTemplate(), templateVariables), [selectedTemplate?.body_html, templateVariables]);
  const emailPreviewHtml = useMemo(() => renderTemplate(selectedTemplate?.email_template || defaultEmailTemplate(), templateVariables), [selectedTemplate?.email_template, templateVariables]);

  const syncLibrary = async () => {
    setBusyAction("sync");
    try {
      const response = await apiPost("/HtmlTemplate/GenericHtmlTemplates/sync-legacy-library/", {});
      setAutoBootstrapState("done");
      setResult({ mode: "sync", response });
      reload(["contentTemplates", "genericHtmlTemplates", "offerTemplates"]);
    } catch (error) {
      setAutoBootstrapState("failed");
      setResult({ mode: "sync_error", response: error?.data || { error: error?.message || "Unable to sync legacy templates." } });
    } finally {
      setBusyAction("");
    }
  };

  const submit = async (issue) => {
    setBusyAction(issue ? "send" : "draft");
    try {
      const payload = {
        ...form,
        position_title: form.position_title || selectedTemplate?.position || "Intern",
        offer_type: selectedTemplate?.offer_type || "Intern",
        offer_payload: {
          department: form.department,
          department_name: departmentName,
          sub_department: form.sub_department,
          sub_department_name: subDepartmentName,
          username: form.username || form.candidate_email.split("@")[0] || "candidate",
          pay_type: form.pay_type,
          employment_type: form.employment_type,
          joining_date: form.joining_date,
          template_id: selectedTemplate?.id,
          template_name: selectedTemplate?.name || "Fallback Legacy Template",
          template_key: selectedTemplate?.metadata?.template_key || "fallback_legacy_template",
          summary: templateSummary(selectedTemplate) || "Fallback legacy offer template",
        },
      };
      const offer = await apiPost(issue ? "/MainApp/Onboard/send-actual-offer" : "/MainApp/Onboard/Send_Offer", payload);
      let response = offer;
      if (issue && offer?.id) {
        response = await apiPost("/MainApp/send-pdf-offer", {
          offer_id: offer.id,
          email: form.candidate_email,
          macro_values: {
            ...templateVariables,
            offer_heading: "OFFER LETTER",
            offer_disclaimer: "",
          },
        });
      }
      setResult({ mode: issue ? "sent" : "draft", response });
      reload(["offers"]);
    } catch (error) {
      setResult({ mode: "error", response: error?.payload || { error: error?.message || "Unable to process offer." } });
    } finally {
      setBusyAction("");
    }
  };

  return (
    <section className="offer-page screen-stack">
      <section className="page-heading">
        <div>
          <span>Onboarding / Offers</span>
          <h1>Offer Templates And Onboarding Email</h1>
        </div>
        <div className="button-row">
          <StatusPill tone="blue">{visibleTemplates.length} Templates</StatusPill>
          <button className="outline-button" disabled={busyAction === "sync"} onClick={syncLibrary}>{busyAction === "sync" ? "Syncing…" : "Sync Legacy Templates"}</button>
          <button className="outline-button" onClick={() => setShowPreview(!showPreview)}>{showPreview ? "Hide Preview" : "Show Preview"}</button>
          <button className="outline-button" disabled={!formReady || Boolean(busyAction)} onClick={() => submit(false)}>{busyAction === "draft" ? "Creating…" : "Create Draft"}</button>
          <button className="primary-button" disabled={!formReady || Boolean(busyAction)} onClick={() => submit(true)}>{busyAction === "send" ? "Sending…" : "Send Offer"}</button>
        </div>
      </section>

      <section className="stat-grid four">
        <StatCard label="Active Template Library" value={String(templates.length)} />
        <StatCard label="Current Domain" value={form.company_name} />
        <StatCard label="Recent Offers" value={String(recentOffers.length)} />
        <StatCard label="Onboarding Email Ready" value={selectedTemplate?.email_template ? "Template" : "Fallback"} />
      </section>

      <Panel title="Offer Configuration & Templates" subtitle="Configure candidate details, select a legacy template, and preview the onboarding package.">
        <div className="split-grid two-one offer-screen-grid">
          <div>
            <div className="form-grid two">
              <label>Company<select value={form.company_name} onChange={(event) => setForm((current) => ({ ...current, company_name: event.target.value }))}><option>ATG</option><option>Banao</option><option>Bunny</option></select></label>
              <label>Candidate Name<input value={form.candidate_name} onChange={(event) => setForm((current) => ({ ...current, candidate_name: event.target.value }))} /></label>
              <label>Candidate Email<input type="email" value={form.candidate_email} onChange={(event) => setForm((current) => ({ ...current, candidate_email: event.target.value }))} /></label>
              <label>Username<input value={form.username} onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))} placeholder="candidate.login" /></label>
              <label>Joining Date<input type="date" value={form.joining_date} onChange={(event) => setForm((current) => ({ ...current, joining_date: event.target.value }))} /></label>
              <label>Employment Type<select value={form.employment_type} onChange={(event) => setForm((current) => ({ ...current, employment_type: event.target.value }))}><option>Intern</option><option>Full Time</option><option>Contract</option><option>Part Time</option></select></label>
              <label>Department<select value={form.department} onChange={(event) => setForm((current) => ({ ...current, department: event.target.value }))}><option value="">Select Department</option>{(data.departments || []).map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}</select></label>
              <label>Sub Department<select value={form.sub_department} onChange={(event) => setForm((current) => ({ ...current, sub_department: event.target.value }))}><option value="">Select Sub Department</option>{(data.subDepartments || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
              <label>Position Title<input value={form.position_title} onChange={(event) => setForm((current) => ({ ...current, position_title: event.target.value }))} placeholder={selectedTemplate?.position || "Role title"} /></label>
              <label>Pay Type<select value={form.pay_type} onChange={(event) => setForm((current) => ({ ...current, pay_type: event.target.value }))}><option>Performance Based</option><option>Fixed</option><option>Hybrid</option></select></label>
            </div>
          </div>

          <div>
            <div style={{ marginBottom: "12px", display: "flex", flexDirection: "column", gap: "6px" }}>
              <h3 style={{ margin: 0, fontSize: "15px" }}>Template Library</h3>
              <p style={{ margin: 0, fontSize: "13px", color: "var(--muted)" }}>All discovered legacy offer types are synced here.</p>
            </div>
            {autoBootstrapState === "running" && <div className="notice-row compact">Bootstrapping the legacy offer library for this workspace.</div>}
            {showingFallbackLibrary && <div className="notice-row"><div><strong>No exact {form.company_name} template yet.</strong><p>Showing templates from other domains so you can still preview and send immediately. Sync will populate the full ATG library.</p></div></div>}
            <div className="form-grid">
              <label>Search Templates<input value={form.template_search} onChange={(event) => setForm((current) => ({ ...current, template_search: event.target.value }))} placeholder="Developer, marketing, testing..." /></label>
            </div>
            <div className="template-catalog">
              {visibleTemplates.length ? visibleTemplates.map((template) => {
                const active = String(template.id) === String(selectedTemplateId);
                return (
                  <button key={template.id} className={active ? "template-card active" : "template-card"} onClick={() => setSelectedTemplateId(String(template.id))}>
                    <div className="template-card-head">
                      <strong>{normalizeLabel(template.name)}</strong>
                      <StatusPill tone={active ? "blue" : "green"}>{template.offer_type || "Offer"}</StatusPill>
                    </div>
                    <p>{templateSummary(template)}</p>
                    <div className="template-card-tags">
                      <span>{template.offer_domain || form.company_name}</span>
                      <span>{template.position || "General"}</span>
                      <span>{normalizeLabel(template.metadata?.template_key || "legacy")}</span>
                    </div>
                  </button>
                );
              }) : <div className="empty-state">No templates are loaded yet. The fallback preview below is still ready, and the legacy library sync will populate this list.</div>}
            </div>
          </div>
        </div>
      </Panel>

      {showPreview && (
        <section className="preview-section fade-in">
          <Panel title="Preview Workspace" subtitle={selectedTemplate ? `Selected template: ${normalizeLabel(selectedTemplate.name)}` : "Preview is available below even without a selected template. Once the library loads, clicking a template card updates it here."}>
            <Tabs value={previewMode} onChange={setPreviewMode} items={[["offer", "Offer Letter"], ["email", "Onboarding Email"]]} />
            <div className="template-preview-shell">
              <iframe
                title={previewMode === "offer" ? "Offer preview" : "Onboarding email preview"}
                srcDoc={previewMode === "offer" ? offerPreviewHtml : emailPreviewHtml}
                className="offer-preview-frame"
              />
            </div>
          </Panel>
        </section>
      )}

      <section className="recent-offers-section">
        <Panel title="Recent Offers" subtitle="Latest onboarding offers created in the rebuilt MainApp service.">
          <SimpleTable
            columns={["Candidate", "Position", "Status", "Email", "Created"]}
            rows={recentOffers.map((offer) => [offer.candidate_name, offer.position_title, offer.status, offer.candidate_email, formatDate(offer.created_at)])}
          />
        </Panel>
      </section>

      {result && (
        <Panel title="Offer Activity Result" subtitle={`Mode: ${result.mode}`}>
          <pre>{JSON.stringify(result.response, null, 2)}</pre>
        </Panel>
      )}
    </section>
  );
}