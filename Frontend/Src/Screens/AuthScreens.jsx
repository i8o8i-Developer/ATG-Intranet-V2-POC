import React, { useEffect, useState } from "react";
import { AlertTriangle, Edit3, Eye, EyeOff, LogIn, LogOut, ShieldCheck, UserRound } from "lucide-react";
import { apiGet, apiPost, apiPatch, clearApiAuth, saveApiSettings } from "../Api/Client.js";
import { Modal } from "./Shared/ScreenComponents.jsx";
import { resolveActiveEmployee } from "./Shared/ScreenUtils.jsx";
import atgLogoPng from "../Images/Atg_Logo.png";
import "../Styles/ProfileScreen.css";
import "../Styles/LoginScreen.css";

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
  const [showDisclaimer, setShowDisclaimer] = useState(true);

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
      <div className="Login-Bg" />
      {showDisclaimer && (
        <div className="Login-Disclaimer-Overlay">
          <div className="Login-Disclaimer-Card">
            <div className="Login-Disclaimer-Header">
              <ShieldCheck size={24} className="Disclaimer-Icon" />
              <h2>System Ownership Disclaimer</h2>
            </div>
            <div className="Login-Disclaimer-Body">
              <p>
                This Property, Its Underlying Code, And Intellectual Rights Belong Exclusively To 
                <strong> Banao Technologies</strong>, Not DurgaAI Solutions.
              </p>
              <p className="Disclaimer-Note">
                It Is Currently Deployed Here For <strong>Internal Testing Purposes Only</strong>.
              </p>
            </div>
            <button 
              className="Login-Disclaimer-Btn" 
              onClick={() => setShowDisclaimer(false)}
            >
              I Understand & Proceed
            </button>
          </div>
        </div>
      )}
      <div className="Login-Container">
        <div className="Login-Brand">
          <div className="Login-Logo">
            <img src={atgLogoPng} alt="ATG" width="48" height="48" />
          </div>
          <h1>ATG Intranet</h1>
          <p>Sign In To Your Workspace</p>
        </div>

        <form className="Login-Card" onSubmit={submit}>
          {error && (
            <div className="Login-Error">
              <AlertTriangle size={15} />
              <span>{error}</span>
            </div>
          )}

          <div className="Login-Field">
            <label>Username</label>
            <div className="Login-Input-Wrap">
              <input autoFocus value={form.username} onChange={(e) => update("username", e.target.value)} autoComplete="username" placeholder="Enter Your Username" />
            </div>
          </div>

          <div className="Login-Field">
            <label>Password</label>
            <div className="Login-Input-Wrap">
              <input type={showPassword ? "text" : "password"} value={form.password} onChange={(e) => update("password", e.target.value)} autoComplete="current-password" placeholder="Enter Your Password" />
              <button type="button" className="Login-Pw-Toggle" onClick={() => setShowPassword((v) => !v)} title={showPassword ? "Hide" : "Show"}>
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <button className="Login-Submit" type="submit" disabled={submitting}>
            {submitting ? (
              <span className="Login-Spinner" />
            ) : (
              <LogIn size={18} />
            )}
            <span>{submitting ? "Signing In..." : "Sign In"}</span>
          </button>
        </form>

      </div>
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
  const payProfile = (data.payProfiles || []).find((p) => String(p.employee) === String(employee.id));
  const profileRows = [
    ["Username", user.username || employee.username || "-"],
    ["Email", user.email || employee.email || "-"],
    ["Employee Code", employee.employee_code || "-"],
    ["Department", employee.department_name || "-"],
    ["Position", employee.position_title || "-"],
    ["Employment Type", employee.employment_type || "-"],
    ["Status", employee.status || "-"],
    ["Joined", employee.joined_on ? new Date(employee.joined_on).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }) : "-"],
    ["Contact Number", employee.contact_number || "-"],
    ["GitHub Username", employee.github_username || "-"],
    ["City", employee.city || "-"],
    ["Slack Username", employee.slack_username || "-"],
    ["Calendar ID", employee.calendar_id || "-"],
    ["College Name", employee.college_name || "-"],
    ["Year of Graduation", employee.year_of_graduation || "-"],
    ["Availability (hrs/week)", employee.availability_hours || "40"],
    ["Pay Type", payProfile?.pay_type || employee.profile_payload?.pay_type || "-"],
    ["Pay Per Task", payProfile?.pay_per_task ? `₹${payProfile.pay_per_task}` : "-"],
    ["Performance Pay", payProfile?.performance_pay ? `₹${payProfile.performance_pay}` : "-"],
    ["Address", employee.profile_payload?.address || "-"],
    ["Emergency Contact", employee.profile_payload?.emergency_contact || "-"],
  ];

  return (
    <section className="PProfile">
      <section className="PProfile-Hero">
        <div className="PProfile-Avatar">{initials}</div>
        <div className="PProfile-Info">
          <small>Signed In Profile</small>
          <h1>{fullName}</h1>
          <p>{employee.department_name || "Banao"} &middot; {employee.position_title || "Intranet User"}</p>
        </div>
        <div className="PProfile-Actions">
          <button className="PProfile-Btn" onClick={() => setEditOpen(true)}><Edit3 size={15} /> Edit Profile</button>
          <button className="PProfile-Btn" onClick={onLogout}><LogOut size={15} /> Logout</button>
        </div>
      </section>

      <div className="PProfile-Stats">
        <div className="PProfile-StatCard">
          <div className="PProfile-StatIcon Blue"><UserRound size={22} /></div>
          <div>
            <span>Assigned Tasks</span>
            <strong>{employeeTasks.length}</strong>
          </div>
        </div>
        <div className="PProfile-StatCard">
          <div className="PProfile-StatIcon Green"><ShieldCheck size={22} /></div>
          <div>
            <span>Leave Requests</span>
            <strong>{leaveRows.filter((item) => String(item.employee || item.employee_id) === String(employee.id)).length}</strong>
          </div>
        </div>
        <div className="PProfile-StatCard">
          <div className="PProfile-StatIcon Orange"><AlertTriangle size={22} /></div>
          <div>
            <span>Unread Notifications</span>
            <strong>{(data.notifications || []).filter((item) => !item.is_read).length}</strong>
          </div>
        </div>
      </div>

      <div className="PProfile-Grid">
        <article className="PProfile-Card">
          <div className="PProfile-CardHead"><UserRound size={18} /><h2>Account Details</h2></div>
          <div className="PProfile-CardBody" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 24px" }}>
            {profileRows.map(([label, value]) => (
              <dl className="PProfile-Row" key={label} style={{ margin: 0, padding: "6px 0" }}><dt style={{ fontSize: 11, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.04em" }}>{label}</dt><dd style={{ margin: 0, fontSize: 14, color: "#0f172a", fontWeight: 500 }}>{value}</dd></dl>
            ))}
          </div>
        </article>
        <article className="PProfile-Card">
          <div className="PProfile-CardHead"><ShieldCheck size={18} /><h2>Workspace Access</h2></div>
          <div className="PProfile-CardBody">
            <dl className="PProfile-Row"><dt>Tenant</dt><dd>{data.me?.activeTenant?.name || data.me?.tenant?.name || data.me?.tenant || "Default Tenant"}</dd></dl>
            <dl className="PProfile-Row"><dt>Workspace</dt><dd>{data.me?.activeWorkspace?.name || data.me?.workspace?.name || data.me?.workspace || "Default Workspace"}</dd></dl>
            <dl className="PProfile-Row"><dt>Backend Session</dt><dd>Active</dd></dl>
          </div>
        </article>
      </div>
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
