import React, { useState } from "react";

import { apiPost } from "../Api/Client.js";
import { findById } from "./Shared/ScreenUtils.jsx";

export function SendCertificateScreen({ data, reload }) {
  const [form, setForm] = useState({ user_id: "", joined_on: "", completion_date: "", position: "", responsibilities: "", send: false });
  const users = data.employees || [];

  const submit = async () => {
    const employee = findById(users, form.user_id) || users[0];
    if (!employee?.user) return;
    await apiPost("/MainApp/send-certificate", { recipient: employee.user, title: `Certificate for ${employee.display_name}`, metadata: form });
    reload();
  };

  return <section className="certificate-page"><h1>Send Certificate</h1><div className="center-form"><label>Username:<select value={form.user_id} onChange={(event) => setForm({ ...form, user_id: event.target.value })}><option>Search Username</option>{users.map((employee) => <option key={employee.id} value={employee.id}>{employee.username || employee.display_name}</option>)}</select></label><label>Joining Date:<input type="date" value={form.joined_on} onChange={(event) => setForm({ ...form, joined_on: event.target.value })} /></label><label>Completion Date:<input type="date" value={form.completion_date} onChange={(event) => setForm({ ...form, completion_date: event.target.value })} /></label><label>Position:<input value={form.position} onChange={(event) => setForm({ ...form, position: event.target.value })} /></label><label>Major Responsibilities (If Any):<input value={form.responsibilities} onChange={(event) => setForm({ ...form, responsibilities: event.target.value })} /></label><label className="check-label"><input type="checkbox" checked={form.send} onChange={(event) => setForm({ ...form, send: event.target.checked })} />Send Certificate</label><div className="button-pair"><button className="outline-button">Preview Certificate</button><button className="outline-button" onClick={submit}>Send Certificate</button></div></div></section>;
}