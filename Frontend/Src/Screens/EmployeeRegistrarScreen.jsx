import React, { useEffect, useState } from "react";

import { apiPost } from "../Api/Client.js";
import { Panel, SimpleTable, StatusPill } from "./Shared/ScreenComponents.jsx";
import { findById, formatDate, isoDate, numberOrNull } from "./Shared/ScreenUtils.jsx";

export function EmployeeRegistrarScreen({ data, reload }) {
  const currentUserId = data.me?.user?.id || "";
  const [form, setForm] = useState({ candidate_name: "", candidate_email: "", company_name: "Banao", employee_code: "", display_name: "", user: "", department: "", position: "", manager: "", employment_type: "Intern", joined_on: isoDate(new Date()), contact_number: "", github_username: "", leaves_wallet: "0", leaves_per_month: "0" });
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!form.user && currentUserId) setForm((current) => ({ ...current, user: String(currentUserId) }));
  }, [currentUserId, form.user]);

  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  const createOfferRegistration = async () => {
    const payload = {
      candidate_name: form.candidate_name || form.display_name,
      candidate_email: form.candidate_email,
      company_name: form.company_name,
      position_title: findById(data.positions || [], form.position)?.title || form.employment_type,
      offer_type: "Employee Registration",
      offer_payload: {
        employee_code: form.employee_code,
        department: form.department,
        position: form.position,
        manager: form.manager,
        employment_type: form.employment_type,
        joined_on: form.joined_on,
        contact_number: form.contact_number,
        github_username: form.github_username,
      },
    };
    const response = await apiPost("/MainApp/Onboard/Send_Offer", payload);
    setResult({ mode: "registration_offer", response });
    reload();
  };

  const createEmployeeProfile = async () => {
    const payload = {
      user: numberOrNull(form.user),
      employee_code: form.employee_code,
      display_name: form.display_name || form.candidate_name,
      contact_number: form.contact_number,
      github_username: form.github_username,
      department: numberOrNull(form.department),
      position: numberOrNull(form.position),
      manager: numberOrNull(form.manager),
      employment_type: form.employment_type,
      joined_on: form.joined_on || null,
      leaves_wallet: form.leaves_wallet || "0",
      leaves_per_month: form.leaves_per_month || "0",
      status: "Active",
      onboarding_completed: false,
      profile_payload: { registered_from: "react_employee_registrar", candidate_email: form.candidate_email },
    };
    const response = await apiPost("/Users/EmployeeProfiles/", payload);
    setResult({ mode: "employee_profile", response });
    reload();
  };

  return (
    <section className="registrar-screen screen-stack">
      <section className="page-heading"><div><span>HRMS / Registrar</span><h1>Employee Registrar</h1></div><StatusPill tone="blue">{(data.employees || []).length} Employees</StatusPill></section>
      <section className="split-grid">
        <Panel title="Registration Intake" subtitle="Creates A Real Onboarding Offer, Then Tracks It In MainApp.">
          <div className="form-grid three">
            <label>Candidate Name<input value={form.candidate_name} onChange={(event) => update("candidate_name", event.target.value)} /></label>
            <label>Email<input type="email" value={form.candidate_email} onChange={(event) => update("candidate_email", event.target.value)} /></label>
            <label>Company<select value={form.company_name} onChange={(event) => update("company_name", event.target.value)}><option>ATG</option><option>Banao</option><option>Bunny</option></select></label>
            <label>Employee Code<input value={form.employee_code} onChange={(event) => update("employee_code", event.target.value)} /></label>
            <label>Display Name<input value={form.display_name} onChange={(event) => update("display_name", event.target.value)} /></label>
            <label>Existing User ID<input value={form.user} onChange={(event) => update("user", event.target.value)} /></label>
            <label>Department<select value={form.department} onChange={(event) => update("department", event.target.value)}><option value="">Select Department</option>{(data.departments || []).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
            <label>Position<select value={form.position} onChange={(event) => update("position", event.target.value)}><option value="">Select Position</option>{(data.positions || []).map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
            <label>Manager<select value={form.manager} onChange={(event) => update("manager", event.target.value)}><option value="">No Manager</option>{(data.employees || []).map((item) => <option key={item.id} value={item.id}>{item.display_name}</option>)}</select></label>
            <label>Employment Type<select value={form.employment_type} onChange={(event) => update("employment_type", event.target.value)}><option>Intern</option><option>Full Time</option><option>Contract</option><option>Part Time</option></select></label>
            <label>Joining Date<input type="date" value={form.joined_on} onChange={(event) => update("joined_on", event.target.value)} /></label>
            <label>Contact Number<input value={form.contact_number} onChange={(event) => update("contact_number", event.target.value)} /></label>
            <label>GitHub Username<input value={form.github_username} onChange={(event) => update("github_username", event.target.value)} /></label>
            <label>Leave Wallet<input type="number" value={form.leaves_wallet} onChange={(event) => update("leaves_wallet", event.target.value)} /></label>
            <label>Leaves Per Month<input type="number" value={form.leaves_per_month} onChange={(event) => update("leaves_per_month", event.target.value)} /></label>
          </div>
          <div className="button-row"><button className="outline-button" onClick={createOfferRegistration} disabled={!form.candidate_email || !(form.candidate_name || form.display_name)}>Create Registration Offer</button><button className="primary-button" onClick={createEmployeeProfile} disabled={!form.user || !form.employee_code || !(form.display_name || form.candidate_name)}>Create Employee Profile</button></div>
          {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
        </Panel>
        <Panel title="Recent Registered Employees"><SimpleTable columns={["Code", "Name", "Department", "Position", "Status", "Joined"]} rows={(data.employees || []).slice(0, 12).map((item) => [item.employee_code, item.display_name, item.department_name, item.position_title, item.status, formatDate(item.joined_on)])} /></Panel>
      </section>
    </section>
  );
}