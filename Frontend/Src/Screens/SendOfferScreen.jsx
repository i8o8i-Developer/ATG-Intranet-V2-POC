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
  if (!value) return new Date().toLocaleDateString("En-GB");
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString("En-GB");
}

function defaultEmailTemplate() {
  return "<DivStyle='Padding:32px;Font-Family:Arial,Helvetica,Sans-Serif;Background:#F5f7fb'><DivStyle='Max-Width:680px;Margin:0Auto;Background:#Fff;Border:1pxSolid #Dfe5ee;Border-Radius:18px;Padding:28px'><H2Style='Margin-Top:0'>OnboardingEmail</H2><P>Hi {{ Candidate_Name }},</P><P>YourOfferFor <Strong>{{ Position_Title }}</Strong> With <Strong>{{ Company_Name }}</Strong> IsReady.</P><P><AHref='{{ Offer_Url }}'>OpenOffer</A></P></Div></Div>";
}

function defaultOfferTemplate() {
  return `<!doctype html>
  <html>
    <head>
      <meta charset="Utf-8" />
      <style>
        body { margin: 0; padding: 28px; background: #ffffff; color: #111827; font-family: Georgia, 'TimesNewRoman', serif; }
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
      <div class="Offer-Shell">
        <div class="Offer-Logo"><img src="https://i.postimg.cc/kgHvKMLz/employed-India-Logo.png" alt="ATGOfferLetter" /></div>
        <div class="Offer-Title">{{ offer_heading }}</div>
        {{ offer_disclaimer }}
        <div class="Offer-Date"><strong>{{ joining_date }}</strong></div>
        <p class="Offer-Copy">Dear Mr./Ms. {{ candidate_name }},</p>
        <p class="Offer-Copy">We are pleased to offer you the position of <strong>{{ position_title }}</strong> with <strong>{{ company_name }}</strong>. This fallback template is ready to preview and send even before the synced library finishes loading.</p>
        <table class="Offer-Table">
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
        <p class="Offer-Copy">This offer remains subject to company policy and onboarding formalities communicated by the hiring team.</p>
      </div>
    </body>
  </html>`;
}

function templateSummary(template) {
  return template?.metadata?.summary || template?.position || template?.name || "LegacyOfferTemplate";
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
    pay_type: "PerformanceBased",
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
    () => templates.filter((template) => template?.metadata?.source === "Legacy-Offer-Library").length,
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
        setResult({ mode: "sync_error", response: error?.data || { error: error?.message || "UnableToSyncLegacyTemplates." } });
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
      pay_type: form.pay_type || "PerformanceBased",
      joining_date: displayDate(form.joining_date),
      offer_heading: "PROVISIONALOFFERLETTER",
      offer_disclaimer: "<PStyle='Text-Align:Center;Margin:8px022px;Font-Size:13px;Font-Weight:700;'>ThisIsAProvisionalOfferLetter. ThisIsNOTAnActualOfferLetterWhichWillBeSentAfterSuccessfulFirstMonthCompletion.</P>",
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
      setResult({ mode: "sync_error", response: error?.data || { error: error?.message || "UnableToSyncLegacyTemplates." } });
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
          template_name: selectedTemplate?.name || "FallbackLegacyTemplate",
          template_key: selectedTemplate?.metadata?.template_key || "fallback_legacy_template",
          summary: templateSummary(selectedTemplate) || "FallbackLegacyOfferTemplate",
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
            offer_heading: "OFFERLETTER",
            offer_disclaimer: "",
          },
        });
      }
      setResult({ mode: issue ? "sent" : "draft", response });
      reload(["offers"]);
    } catch (error) {
      setResult({ mode: "error", response: error?.payload || { error: error?.message || "UnableToProcessOffer." } });
    } finally {
      setBusyAction("");
    }
  };

  return (
    <section className="Offer-PageScreen-Stack">
      <section className="Page-Heading">
        <div>
          <span>Onboarding / Offers</span>
          <h1>Offer Templates And Onboarding Email</h1>
        </div>
        <div className="Button-Row">
          <StatusPill tone="blue">{visibleTemplates.length} Templates</StatusPill>
          <button className="Outline-Button" disabled={busyAction === "sync"} onClick={syncLibrary}>{busyAction === "sync" ? "Syncing…" : "SyncLegacyTemplates"}</button>
          <button className="Outline-Button" onClick={() => setShowPreview(!showPreview)}>{showPreview ? "HidePreview" : "ShowPreview"}</button>
          <button className="Outline-Button" disabled={!formReady || Boolean(busyAction)} onClick={() => submit(false)}>{busyAction === "draft" ? "Creating…" : "CreateDraft"}</button>
          <button className="Primary-Button" disabled={!formReady || Boolean(busyAction)} onClick={() => submit(true)}>{busyAction === "send" ? "Sending…" : "SendOffer"}</button>
        </div>
      </section>

      <section className="Stat-GridFour">
        <StatCard label="ActiveTemplateLibrary" value={String(templates.length)} />
        <StatCard label="CurrentDomain" value={form.company_name} />
        <StatCard label="RecentOffers" value={String(recentOffers.length)} />
        <StatCard label="OnboardingEmailReady" value={selectedTemplate?.email_template ? "Template" : "Fallback"} />
      </section>

      <Panel title="OfferConfiguration & Templates" subtitle="ConfigureCandidateDetails, SelectALegacyTemplate, AndPreviewTheOnboardingPackage.">
        <div className="Split-GridTwo-OneOffer-Screen-Grid">
          <div>
            <div className="Form-GridTwo">
              <label>Company<select value={form.company_name} onChange={(event) => setForm((current) => ({ ...current, company_name: event.target.value }))}><option>ATG</option><option>Banao</option><option>Bunny</option></select></label>
              <label>Candidate Name<input value={form.candidate_name} onChange={(event) => setForm((current) => ({ ...current, candidate_name: event.target.value }))} /></label>
              <label>Candidate Email<input type="email" value={form.candidate_email} onChange={(event) => setForm((current) => ({ ...current, candidate_email: event.target.value }))} /></label>
              <label>Username<input value={form.username} onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))} placeholder="candidate.login" /></label>
              <label>Joining Date<input type="date" value={form.joining_date} onChange={(event) => setForm((current) => ({ ...current, joining_date: event.target.value }))} /></label>
              <label>Employment Type<select value={form.employment_type} onChange={(event) => setForm((current) => ({ ...current, employment_type: event.target.value }))}><option>Intern</option><option>Full Time</option><option>Contract</option><option>Part Time</option></select></label>
              <label>Department<select value={form.department} onChange={(event) => setForm((current) => ({ ...current, department: event.target.value }))}><option value="">Select Department</option>{(data.departments || []).map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}</select></label>
              <label>Sub Department<select value={form.sub_department} onChange={(event) => setForm((current) => ({ ...current, sub_department: event.target.value }))}><option value="">Select Sub Department</option>{(data.subDepartments || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
              <label>Position Title<input value={form.position_title} onChange={(event) => setForm((current) => ({ ...current, position_title: event.target.value }))} placeholder={selectedTemplate?.position || "RoleTitle"} /></label>
              <label>Pay Type<select value={form.pay_type} onChange={(event) => setForm((current) => ({ ...current, pay_type: event.target.value }))}><option>Performance Based</option><option>Fixed</option><option>Hybrid</option></select></label>
            </div>
          </div>

          <div>
            <div style={{ marginBottom: "12px", display: "flex", flexDirection: "column", gap: "6px" }}>
              <h3 style={{ margin: 0, fontSize: "15px" }}>Template Library</h3>
              <p style={{ margin: 0, fontSize: "13px", color: "Var(--Muted)" }}>All discovered legacy offer types are synced here.</p>
            </div>
            {autoBootstrapState === "running" && <div className="Notice-RowCompact">Bootstrapping the legacy offer library for this workspace.</div>}
            {showingFallbackLibrary && <div className="Notice-Row"><div><strong>No exact {form.company_name} template yet.</strong><p>Showing templates from other domains so you can still preview and send immediately. Sync will populate the full ATG library.</p></div></div>}
            <div className="Form-Grid">
              <label>Search Templates<input value={form.template_search} onChange={(event) => setForm((current) => ({ ...current, template_search: event.target.value }))} placeholder="Developer, Marketing, Testing..." /></label>
            </div>
            <div className="Template-Catalog">
              {visibleTemplates.length ? visibleTemplates.map((template) => {
                const active = String(template.id) === String(selectedTemplateId);
                return (
                  <button key={template.id} className={active ? "Template-CardActive" : "Template-Card"} onClick={() => setSelectedTemplateId(String(template.id))}>
                    <div className="Template-Card-Head">
                      <strong>{normalizeLabel(template.name)}</strong>
                      <StatusPill tone={active ? "blue" : "green"}>{template.offer_type || "Offer"}</StatusPill>
                    </div>
                    <p>{templateSummary(template)}</p>
                    <div className="Template-Card-Tags">
                      <span>{template.offer_domain || form.company_name}</span>
                      <span>{template.position || "General"}</span>
                      <span>{normalizeLabel(template.metadata?.template_key || "legacy")}</span>
                    </div>
                  </button>
                );
              }) : <div className="Empty-State">No templates are loaded yet. The fallback preview below is still ready, and the legacy library sync will populate this list.</div>}
            </div>
          </div>
        </div>
      </Panel>

      {showPreview && (
        <section className="Preview-SectionFade-In">
          <Panel title="PreviewWorkspace" subtitle={selectedTemplate ? `Selected template: ${normalizeLabel(selectedTemplate.name)}` : "PreviewIsAvailableBelowEvenWithoutASelectedTemplate. OnceTheLibraryLoads, ClickingATemplateCardUpdatesItHere."}>
            <Tabs value={previewMode} onChange={setPreviewMode} items={[["offer", "OfferLetter"], ["email", "OnboardingEmail"]]} />
            <div className="Template-Preview-Shell">
              <iframe
                title={previewMode === "offer" ? "OfferPreview" : "OnboardingEmailPreview"}
                srcDoc={previewMode === "offer" ? offerPreviewHtml : emailPreviewHtml}
                className="Offer-Preview-Frame"
              />
            </div>
          </Panel>
        </section>
      )}

      <section className="Recent-Offers-Section">
        <Panel title="RecentOffers" subtitle="LatestOnboardingOffersCreatedInTheRebuiltMainAppService.">
          <SimpleTable
            columns={["Candidate", "Position", "Status", "Email", "Created"]}
            rows={recentOffers.map((offer) => [offer.candidate_name, offer.position_title, offer.status, offer.candidate_email, formatDate(offer.created_at)])}
          />
        </Panel>
      </section>

      {result && (
        <Panel title="OfferActivityResult" subtitle={`Mode: ${result.mode}`}>
          <pre>{JSON.stringify(result.response, null, 2)}</pre>
        </Panel>
      )}
    </section>
  );
}