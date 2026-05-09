import React, { useEffect, useState } from "react";
import { AlertTriangle, Edit3, Eye, EyeOff, LogIn, LogOut, ShieldCheck, UserRound } from "lucide-react";
import { apiGet, apiPost, apiPatch, clearApiAuth, saveApiSettings } from "../Api/Client.js";
import { Modal } from "./Shared/ScreenComponents.jsx";
import { resolveActiveEmployee } from "./Shared/ScreenUtils.jsx";

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
      const loginSettings = {
        apiBase: form.apiBase,
        tenantId: form.tenantId,
        workspaceId: form.workspaceId,
        basicAuth: { username: form.username, password: form.password },
      };
      saveApiSettings(loginSettings);
      const currentUser = await apiPost("/Users/Auth/Login/", {
        username: form.username,
        password: form.password,
        tenant_id: form.tenantId,
        workspace_id: form.workspaceId,
      });
      saveApiSettings({
        ...loginSettings,
        tenantId: currentUser?.activeTenant?.id || form.tenantId,
        workspaceId: currentUser?.activeWorkspace?.id || form.workspaceId,
      });
      // Check If Onboarding Is Completed
      const employee = currentUser.employees?.[0];
      if (employee) {
        const employeeProfile = await apiGet(`/Users/EmployeeProfiles/${employee.id}/`);
        if (!employeeProfile.onboarding_completed) {
          onLogin("/onboarding/");
          return;
        }
      }
      onLogin();
    } catch (loginError) {
      clearApiAuth();
      setError(loginError?.status === 401 ? "Invalid Username Or Password." : loginError?.message || "Login Failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="Login-Page">
      <form className="Login-Card" onSubmit={submit}>
        <div className="Brand-Block">
          <div className="Brand-Mark">B</div>
          <div className="Brand-Copy">
            <strong>Banao Intranet</strong>
            <span>v2</span>
          </div>
        </div>

        <h2 style={{ margin: 0, fontSize: "20px" }}>Sign In</h2>

        {error && <div className="Login-Error"><AlertTriangle size={15} />{error}</div>}

        <label>
          Username
          <input autoFocus value={form.username} onChange={(e) => update("username", e.target.value)} autoComplete="username" placeholder="Username" />
        </label>
        <label>
          Password
          <span className="Password-Field">
            <input type={showPassword ? "text" : "password"} value={form.password} onChange={(e) => update("password", e.target.value)} autoComplete="current-password" placeholder="Password" />
            <button type="button" className="Icon-Button" onClick={() => setShowPassword((v) => !v)} title={showPassword ? "Hide" : "Show"}>
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </span>
        </label>

        <button className="Primary-Button Login-Submit" type="submit" disabled={submitting}>
          <LogIn size={16} />{submitting ? "Signing In…" : "Sign In"}
        </button>
      </form>
    </main>
  );
}

export function ProfileScreen({ data, onLogout, reload }) {
  const [editOpen, setEditOpen] = useState(false);
  const user = data.me?.user || data.me?.account || data.me || {};
  const employee = resolveActiveEmployee(data) || {};
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
    <section className="Profile-Screen Screen-Stack">
      <section className="Profile-Hero">
        <div className="Profile-Avatar">{initials}</div>
        <div>
          <span className="Section-Kicker">Signed In Profile</span>
          <h1>{fullName}</h1>
          <p>{employee.department_name || "Banao"} / {employee.position_title || "Intranet User"}</p>
        </div>
        <button className="Outline-Button" onClick={() => setEditOpen(true)}><Edit3 size={16} /> Edit Profile</button>
        <button className="Outline-Button" onClick={onLogout}><LogOut size={16} /> Logout</button>
      </section>

      <div className="Profile-Stats">
        <section><span>Assigned Tasks</span><strong>{employeeTasks.length}</strong></section>
        <section><span>Leave Requests</span><strong>{leaveRows.filter((item) => String(item.employee || item.employee_id) === String(employee.id)).length}</strong></section>
        <section><span>Notifications</span><strong>{(data.notifications || []).filter((item) => !item.is_read).length}</strong></section>
      </div>

      <section className="Profile-Grid">
        <article className="Profile-Card">
          <header><UserRound size={18} /><h2>Account Details</h2></header>
          <dl>{profileRows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
        </article>
        <article className="Profile-Card">
          <header><ShieldCheck size={18} /><h2>Workspace Access</h2></header>
          <dl>
            <div><dt>Tenant</dt><dd>{data.me?.activeTenant?.name || data.me?.tenant?.name || data.me?.tenant || "Default Tenant"}</dd></div>
            <div><dt>Workspace</dt><dd>{data.me?.activeWorkspace?.name || data.me?.workspace?.name || data.me?.workspace || "Default Workspace"}</dd></div>
            <div><dt>Backend Session</dt><dd>Active</dd></div>
          </dl>
        </article>
      </section>
      {editOpen && <ProfileEditModal employee={employee} onClose={() => setEditOpen(false)} reload={reload} />}
    </section>
  );
}

function ProfileEditModal({ employee, onClose, reload }) {
  const [form, setForm] = useState({
    display_name: employee.display_name || "",
    phone: employee.phone || "",
    address: employee.address || "",
    department_name: employee.department_name || "",
    position_title: employee.position_title || "",
    joined_on: employee.joined_on || "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const save = async () => {
    if (!employee.id) {
      setError("No Employee Profile Linked To This User.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const payload = { ...form };
      if (!payload.joined_on) delete payload.joined_on;
      await apiPatch(`/Users/EmployeeProfiles/${employee.id}/`, payload);
      if (reload) reload(["employees", "me"]);
      onClose();
    } catch (saveError) {
      setError(saveError?.message || "Update Failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal title="Edit Profile" onClose={onClose} wide>
      {error && <div className="Login-Error"><AlertTriangle size={14} /> {error}</div>}
      <div className="Form-Grid Two Modal-Form">
        <label>Display Name<input value={form.display_name} onChange={(event) => setForm({ ...form, display_name: event.target.value })} /></label>
        <label>Phone<input value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} /></label>
        <label>Department<input value={form.department_name} onChange={(event) => setForm({ ...form, department_name: event.target.value })} /></label>
        <label>Position<input value={form.position_title} onChange={(event) => setForm({ ...form, position_title: event.target.value })} /></label>
        <label>Joined On<input type="date" value={form.joined_on ? String(form.joined_on).slice(0, 10) : ""} onChange={(event) => setForm({ ...form, joined_on: event.target.value })} /></label>
      </div>
      <label>Address<textarea rows={3} value={form.address} onChange={(event) => setForm({ ...form, address: event.target.value })} /></label>
      <button className="Primary-Button" onClick={save} disabled={busy}>Save Profile</button>
    </Modal>
  );
}
