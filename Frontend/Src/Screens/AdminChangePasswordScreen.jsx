import React, { useMemo, useState } from "react";
import { KeyRound, Search, ShieldAlert } from "lucide-react";
import { apiPost } from "../Api/Client.js";
import { Panel } from "./Shared/ScreenComponents.jsx";

export function AdminChangePasswordScreen({ data }) {
  const me = data.me?.user || data.me?.account || data.me || {};
  const isAdmin = Boolean(me.is_superuser || me.is_staff);
  const employees = data.employees || [];
  const [mode, setMode] = useState(isAdmin ? "admin" : "self");
  const [query, setQuery] = useState("");
  const [targetId, setTargetId] = useState("");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  const filtered = useMemo(() => {
    if (!query) return employees.slice(0, 50);
    const q = query.toLowerCase();
    return employees.filter((employee) => {
      const haystack = `${employee.display_name || ""} ${employee.candidate_name || ""} ${employee.candidate_email || ""} ${employee.user || ""}`.toLowerCase();
      return haystack.includes(q);
    }).slice(0, 50);
  }, [employees, query]);

  const submit = async () => {
    setResult(null);
    if (!newPassword || newPassword.length < 6) {
      setResult({ ok: false, message: "Password must be at least 6 characters." });
      return;
    }
    if (newPassword !== confirmPassword) {
      setResult({ ok: false, message: "Passwords Do Not Match." });
      return;
    }
    if (mode === "admin" && !targetId) {
      setResult({ ok: false, message: "Select A Target User." });
      return;
    }
    setBusy(true);
    try {
      const payload = mode === "admin"
        ? { user_id: targetId, new_password: newPassword }
        : { old_password: oldPassword, new_password: newPassword };
      const response = await apiPost("/Users/Auth/ChangePassword/", payload);
      setResult({ ok: true, message: response.detail || "Password Updated." });
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (error) {
      setResult({ ok: false, message: error?.data?.detail || error?.message || "Update Failed." });
    } finally {
      setBusy(false);
    }
  };

  return (
    <Panel
      title={<span><KeyRound size={18} /> Change Password</span>}
      subtitle={mode === "admin" ? "Reset Password For Any User (Admin)." : "Update Your Own Password."}
      right={isAdmin ? (
        <div className="tabs" style={{ display: "inline-flex" }}>
          <button className={mode === "self" ? "active" : ""} onClick={() => setMode("self")}>My Account</button>
          <button className={mode === "admin" ? "active" : ""} onClick={() => setMode("admin")}>Admin Reset</button>
        </div>
      ) : null}
    >
      <div className="form-grid" style={{ gap: 12 }}>
        {mode === "admin" && isAdmin && (
          <>
            <label>Target User
              <span style={{ position: "relative", display: "block" }}>
                <Search size={14} style={{ position: "absolute", left: 8, top: 9, opacity: 0.5 }} />
                <input className="mini-inp" style={{ paddingLeft: 26 }} placeholder="Search Employees" value={query} onChange={(e) => setQuery(e.target.value)} />
              </span>
            </label>
            <label>Select User
              <select className="mini-inp" value={targetId} onChange={(e) => setTargetId(e.target.value)}>
                <option value="">— Pick User —</option>
                {filtered.map((employee) => (
                  <option key={employee.id} value={employee.user || employee.id}>
                    {employee.display_name || employee.candidate_name || `#${employee.id}`} ({employee.candidate_email || "no email"})
                  </option>
                ))}
              </select>
            </label>
          </>
        )}
        {mode === "self" && (
          <label>Current Password
            <input type="password" className="mini-inp" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} />
          </label>
        )}
        <label>New Password
          <input type="password" className="mini-inp" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
        </label>
        <label>Confirm Password
          <input type="password" className="mini-inp" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
        </label>
        <div>
          <button className="primary-button" onClick={submit} disabled={busy}>
            {busy ? "Saving…" : (mode === "admin" ? "Reset User Password" : "Update My Password")}
          </button>
        </div>
        {result && (
          <div className={result.ok ? "auth-alert ok" : "auth-alert"}>
            <ShieldAlert size={14} />
            <span>{result.message}</span>
          </div>
        )}
      </div>
    </Panel>
  );
}
