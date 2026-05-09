import React, { useEffect, useMemo, useState } from "react";

import { apiPost } from "../Api/Client.js";
import { Panel, SimpleTable, StatCard, StatusPill } from "./Shared/ScreenComponents.jsx";
import { findById, formatDate, isoDate, numberOrNull } from "./Shared/ScreenUtils.jsx";

function generatePassword() {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%";
  const values = globalThis.crypto?.getRandomValues ? globalThis.crypto.getRandomValues(new Uint32Array(12)) : Array.from({ length: 12 }, () => Math.floor(Math.random() * alphabet.length));
  return Array.from(values, (value) => alphabet[Number(value) % alphabet.length]).join("");
}

export function EmployeeRegistrarScreen({ data, reload }) {
  const currentUserId = data.me?.user?.id || "";
  const [form, setForm] = useState({
    candidate_name: "",
    candidate_email: "",
    company_name: "Banao",
    employee_code: "",
    display_name: "",
    user: "",
    username: "",
    password: generatePassword(),
    department: "",
    position: "",
    manager: "",
    employment_type: "Intern",
    joined_on: isoDate(new Date()),
    contact_number: "",
    github_username: "",
    leaves_wallet: "0",
    leaves_per_month: "0",
  });
  const [credentialOptions, setCredentialOptions] = useState({ intranet: true, email: true, github: true, slack: false });
  const [busyAction, setBusyAction] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!form.user && currentUserId) setForm((current) => ({ ...current, user: String(currentUserId) }));
  }, [currentUserId, form.user]);

  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const derivedUsername = form.username || (form.candidate_email ? form.candidate_email.split("@")[0] : "") || (form.display_name || form.candidate_name).toLowerCase().replace(/\s+/g, ".");
  const positionTitle = findById(data.positions || [], form.position)?.title || form.employment_type;

  const credentialBlueprints = useMemo(() => {
    const employeeName = form.display_name || form.candidate_name || "New Hire";
    const vaultSlug = (derivedUsername || "candidate").replace(/[^a-z0-9._-]+/gi, "-").toLowerCase();
    return [
      {
        key: "intranet",
        enabled: credentialOptions.intranet,
        system_name: "Intranet",
        name: `${employeeName} Intranet Login`,
        login: derivedUsername,
        secret_reference: `vault://onboarding/${vaultSlug}/intranet`,
      },
      {
        key: "email",
        enabled: credentialOptions.email,
        system_name: "Work Email",
        name: `${employeeName} Work Email`,
        login: form.candidate_email || `${vaultSlug}@example.com`,
        secret_reference: `vault://onboarding/${vaultSlug}/email`,
      },
      {
        key: "github",
        enabled: credentialOptions.github,
        system_name: "GitHub",
        name: `${employeeName} GitHub Access`,
        login: form.github_username || derivedUsername,
        secret_reference: `vault://onboarding/${vaultSlug}/github`,
      },
      {
        key: "slack",
        enabled: credentialOptions.slack,
        system_name: "Slack",
        name: `${employeeName} Slack Access`,
        login: form.candidate_email || derivedUsername,
        secret_reference: `vault://onboarding/${vaultSlug}/slack`,
      },
    ];
  }, [credentialOptions.email, credentialOptions.github, credentialOptions.intranet, credentialOptions.slack, derivedUsername, form.candidate_email, form.candidate_name, form.display_name, form.github_username]);

  const createOfferRegistration = async () => {
    setBusyAction("offer");
    try {
      const payload = {
        candidate_name: form.candidate_name || form.display_name,
        candidate_email: form.candidate_email,
        company_name: form.company_name,
        position_title: positionTitle,
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
      reload(["offers"]);
    } catch (error) {
      setResult({ mode: "registration_offer_error", response: error?.data || { error: error?.message || "Failed To Create Registration Offer." } });
    } finally {
      setBusyAction("");
    }
  };

  const provisionEmployeePackage = async () => {
    setBusyAction("provision");
    try {
      const employee = await apiPost("/MainApp/Onboard/register-employee", {
        username: derivedUsername,
        password: form.password,
        email: form.candidate_email,
        employee_code: form.employee_code,
        display_name: form.display_name || form.candidate_name,
        candidate_name: form.candidate_name,
        candidate_email: form.candidate_email,
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
        profile_payload: {
          registered_from: "react_employee_registrar",
          candidate_email: form.candidate_email,
          onboarding_company: form.company_name,
        },
      });

      const credentialResults = await Promise.allSettled(
        credentialBlueprints
          .filter((item) => item.enabled)
          .map((item) => apiPost("/MainApp/create-credentials/", {
            owner: employee.user,
            name: item.name,
            system_name: item.system_name,
            secret_reference: item.secret_reference,
            metadata: {
              login: item.login,
              employee_code: form.employee_code,
              onboarding_pack: true,
              company_name: form.company_name,
            },
          })),
      );

      setResult({
        mode: "provisioned",
        response: {
          employee,
          login_credentials: { username: derivedUsername, password: form.password },
          credentials: credentialResults.map((item, index) => ({
            system: credentialBlueprints.filter((row) => row.enabled)[index]?.system_name,
            status: item.status,
            response: item.status === "fulfilled" ? item.value : (item.reason?.data || { error: item.reason?.message || "Credential Provisioning Failed." }),
          })),
        },
      });
      reload(["employees", "users", "credentialVaultItems"]);
    } catch (error) {
      setResult({ mode: "error", response: error?.data || { error: error?.message || "Failed To Provision Onboarding Package." } });
    } finally {
      setBusyAction("");
    }
  };

  const recentCredentials = (data.credentialVaultItems || []).slice(0, 10);

  return (
    <section className="Registrar-Screen Screen-Stack">
      <section className="Page-Heading">
        <div>
          <span>HRMS / Registrar</span>
          <h1>Employee Onboarding And Credentials</h1>
        </div>
        <StatusPill tone="blue">{(data.employees || []).length} Employees</StatusPill>
      </section>

      <section className="Stat-Grid Four">
        <StatCard label="Employees" value={String((data.employees || []).length)} />
        <StatCard label="Credential Vault Items" value={String((data.credentialVaultItems || []).length)} />
        <StatCard label="Provisioned Systems" value={String(credentialBlueprints.filter((item) => item.enabled).length)} />
        <StatCard label="Login Username" value={derivedUsername || "Pending"} />
      </section>

      <section className="Split-Grid Two-One">
        <Panel title="Onboarding Intake" subtitle="Create The Employee Record, Generate A One-Time Login, And Provision Credential Vault Entries.">
          <div className="Form-Grid Three">
            <label>Candidate Name<input value={form.candidate_name} onChange={(event) => update("candidate_name", event.target.value)} /></label>
            <label>Company<select value={form.company_name} onChange={(event) => update("company_name", event.target.value)}><option>ATG</option><option>Banao</option><option>Bunny</option></select></label>
            <label>Candidate Email<input type="email" value={form.candidate_email} onChange={(event) => update("candidate_email", event.target.value)} /></label>
            <label>Employee Code<input value={form.employee_code} onChange={(event) => update("employee_code", event.target.value)} /></label>
            <label>Display Name<input value={form.display_name} onChange={(event) => update("display_name", event.target.value)} /></label>
            <label>Username<input value={derivedUsername} onChange={(event) => update("username", event.target.value)} /></label>
            <label>Password<div className="Credential-Inline-Field"><input value={form.password} onChange={(event) => update("password", event.target.value)} /><button className="Soft-Button Small" type="button" onClick={() => update("password", generatePassword())}>Regenerate</button></div></label>
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

          <div className="Credential-Pack">
            <header>
              <div>
                <strong>Credential Pack</strong>
                <p>Select Which Systems Should Be Provisioned Into The Vault For This New Hire.</p>
              </div>
            </header>
            {credentialBlueprints.map((item) => (
              <label key={item.key} className="Credential-Row">
                <span className="Credential-Toggle"><input type="checkbox" checked={item.enabled} onChange={(event) => setCredentialOptions((current) => ({ ...current, [item.key]: event.target.checked }))} />{item.system_name}</span>
                <span>{item.login}</span>
                <span>{item.secret_reference}</span>
              </label>
            ))}
          </div>

          <div className="Button-Row">
            <button className="Outline-Button" onClick={createOfferRegistration} disabled={busyAction === "offer" || !form.candidate_email || !(form.candidate_name || form.display_name)}>Create Registration Offer</button>
            <button className="Primary-Button" onClick={provisionEmployeePackage} disabled={Boolean(busyAction) || !form.employee_code || !form.candidate_email || !(form.display_name || form.candidate_name)}>{busyAction === "provision" ? "Provisioning…" : "Provision Employee + Credentials"}</button>
          </div>
        </Panel>

        <Panel title="Existing Access Pack" subtitle="Recent Credential Items Already Created In The Rebuilt Vault.">
          <SimpleTable columns={["System", "Name", "Owner", "Status"]} rows={recentCredentials.map((item) => [item.system_name, item.name, item.owner, item.status])} />
        </Panel>
      </section>

      <section className="Split-Grid">
        <Panel title="Recent Registered Employees">
          <SimpleTable columns={["Code", "Name", "Department", "Position", "Status", "Joined"]} rows={(data.employees || []).slice(0, 12).map((item) => [item.employee_code, item.display_name, item.department_name, item.position_title, item.status, formatDate(item.joined_on)])} />
        </Panel>

        {result && (
          <Panel title="Onboarding Result" subtitle={`Mode: ${result.mode}`}>
            <pre>{JSON.stringify(result.response, null, 2)}</pre>
          </Panel>
        )}
      </section>

    </section>
  );
}