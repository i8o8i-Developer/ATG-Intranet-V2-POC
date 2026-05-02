import React, { useEffect, useState } from "react";
import { AlertTriangle, Eye, EyeOff, LogIn, LogOut, ShieldCheck, UserRound } from "lucide-react";
import { apiGet, clearApiAuth, saveApiSettings } from "../Api/Client.js";

export function LoginScreen({ settings, onLogin }) {
  const [form, setForm] = useState({
    apiBase: settings.apiBase,
    tenantId: settings.tenantId || "1",
    workspaceId: settings.workspaceId || "1",
    username: "",
    password: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const environmentLabel = String(form.apiBase || "Configured Backend").replace(/^https?:\/\//i, "").replace(/\/$/, "") || "Configured Backend";

  useEffect(() => {
    setForm((current) => ({
      ...current,
      apiBase: settings.apiBase,
      tenantId: settings.tenantId || "1",
      workspaceId: settings.workspaceId || "1",
    }));
  }, [settings]);

  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  const submit = async (event) => {
    event.preventDefault();
    if (!form.username || !form.password) {
      setError("Enter Username And Password.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      saveApiSettings({
        apiBase: form.apiBase,
        tenantId: form.tenantId,
        workspaceId: form.workspaceId,
        basicAuth: { username: form.username, password: form.password },
      });
      await apiGet("/Users/Auth/Me/");
      onLogin();
    } catch (loginError) {
      clearApiAuth();
      setError(loginError?.status === 401 ? "Invalid Username Or Password." : loginError?.message || "Login Failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="login-page">
      <section className="login-brand-panel">
        <div className="login-brand-shell">
          <div className="brand-block login-brand">
            <div className="brand-mark">B</div>
            <div className="brand-copy">
              <strong>Banao</strong>
              <span>Intranet v2</span>
            </div>
          </div>
          <div className="login-hero-copy">
            <span className="section-kicker">Operator-Ready Workspace</span>
            <h1>One Login For People, Delivery, Finance, And Intelligence.</h1>
            <p>Sign In To The Rebuilt Intranet And Work Against The Live Django Backend Without The Old Demo Controls Or Developer Clutter.</p>
          </div>

          <div className="login-proof-grid">
            <article className="login-proof-card">
              <strong>Real Backend Auth</strong>
              <p>Every Session Validates Directly Against The Running Django API.</p>
            </article>
            <article className="login-proof-card">
              <strong>Focused Workbench</strong>
              <p>Use One Secure Entry Point For HRMS, Projects, Payroll, Docs, And Workflow Visibility.</p>
            </article>
            <article className="login-proof-card">
              <strong>Minimal Setup Surface</strong>
              <p>Backend, Tenant, And Workspace Stay Environment-Driven Instead Of Filling The Sign-In Form.</p>
            </article>
          </div>

          <div className="login-environment-rail">
            <span>Connected Environment</span>
            <strong>{environmentLabel}</strong>
            <p>Tenant {form.tenantId} / Workspace {form.workspaceId}</p>
          </div>
        </div>
      </section>

      <section className="login-panel">
        <form className="login-card" onSubmit={submit}>
          <header>
            <ShieldCheck size={22} />
            <div>
              <span className="login-card-badge">Secure Sign In</span>
              <h2>Employee Login</h2>
              <p>Authenticated Against The Live Django Backend.</p>
            </div>
          </header>

          {error && <div className="login-error"><AlertTriangle size={16} />{error}</div>}

          <label>
            Username
            <input autoFocus value={form.username} onChange={(event) => update("username", event.target.value)} autoComplete="username" placeholder="Enter Your Username" />
          </label>
          <label>
            Password
            <span className="password-field">
              <input type={showPassword ? "text" : "password"} value={form.password} onChange={(event) => update("password", event.target.value)} autoComplete="current-password" placeholder="Enter Your Password" />
              <button type="button" className="icon-button" onClick={() => setShowPassword((value) => !value)} title={showPassword ? "Hide Password" : "Show Password"}>{showPassword ? <EyeOff size={16} /> : <Eye size={16} />}</button>
            </span>
          </label>

          <button className="primary-button login-submit" type="submit" disabled={submitting}>
            <LogIn size={16} />
            {submitting ? "Signing In" : "Sign In"}
          </button>

          <div className="login-card-footer">
            <div className="login-environment-pill">{environmentLabel}</div>
            <p>Tenant {form.tenantId} / Workspace {form.workspaceId}</p>
          </div>
        </form>
      </section>
    </main>
  );
}

export function ProfileScreen({ data, onLogout }) {
  const user = data.me?.user || data.me?.account || data.me || {};
  const employee = data.me?.employees?.[0] || (data.employees || []).find((item) => String(item.user) === String(user.id)) || (data.employees || [])[0] || {};
  const fullName = employee.display_name || employee.displayName || user.fullName || user.full_name || user.username || "User";
  const initials = String(fullName).split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase() || "U";
  const employeeTasks = (data.tasks || []).filter((task) => String(task.owner || task.owner_id || task.assignee) === String(employee.id));
  const leaveRows = data.leaveOverview?.results?.length ? data.leaveOverview.results : data.leaveRequests || [];
  const profileRows = [
    ["Username", user.username || employee.username || "-"],
    ["Email", user.email || employee.email || "-"],
    ["Employee Code", employee.employee_code || "-"],
    ["Department", employee.department_name || "-"],
    ["Position", employee.position_title || "-"],
    ["Employment Type", employee.employment_type || "-"],
    ["Status", employee.status || "-"],
    ["Joined", employee.joined_on ? new Date(employee.joined_on).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }) : "-"],
  ];

  return (
    <section className="profile-screen screen-stack">
      <section className="profile-hero">
        <div className="profile-avatar">{initials}</div>
        <div>
          <span className="section-kicker">Signed In Profile</span>
          <h1>{fullName}</h1>
          <p>{employee.department_name || "Banao"} / {employee.position_title || "Intranet User"}</p>
        </div>
        <button className="outline-button" onClick={onLogout}><LogOut size={16} /> Logout</button>
      </section>

      <div className="profile-stats">
        <section><span>Assigned Tasks</span><strong>{employeeTasks.length}</strong></section>
        <section><span>Leave Requests</span><strong>{leaveRows.filter((item) => String(item.employee || item.employee_id) === String(employee.id)).length}</strong></section>
        <section><span>Notifications</span><strong>{(data.notifications || []).filter((item) => !item.is_read).length}</strong></section>
      </div>

      <section className="profile-grid">
        <article className="profile-card">
          <header><UserRound size={18} /><h2>Account Details</h2></header>
          <dl>{profileRows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
        </article>
        <article className="profile-card">
          <header><ShieldCheck size={18} /><h2>Workspace Access</h2></header>
          <dl>
            <div><dt>Tenant</dt><dd>{data.me?.tenant?.name || data.me?.tenant || "Default Tenant"}</dd></div>
            <div><dt>Workspace</dt><dd>{data.me?.workspace?.name || data.me?.workspace || "Default Workspace"}</dd></div>
            <div><dt>Backend Session</dt><dd>Active</dd></div>
          </dl>
        </article>
      </section>
    </section>
  );
}
