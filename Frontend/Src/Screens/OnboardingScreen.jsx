import React, { useState } from "react";
import { CheckCircle, User, MapPin, Phone, AlertTriangle } from "Lucide-React";
import { apiGet, apiPatch, apiPost } from "../Api/Client.js";
import { resolveActiveEmployee } from "./Shared/ScreenUtils.jsx";

export default function OnboardingScreen({ data, reload, navigate }) {
  const employee = resolveActiveEmployee(data);
  const [form, setForm] = useState({
    display_name: employee?.display_name || "",
    phone: employee?.phone || "",
    address: employee?.address || "",
    emergency_contact: employee?.emergency_contact || "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  const submit = async () => {
    if (!form.display_name) {
      setError("PleaseProvideYourFullName.");
      return;
    }
    if (!employee?.id) {
      setError("EmployeeNotFound. PleaseRefreshThePage.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      // UpdateProfile      await apiPatch(`/Users/EmployeeProfiles/${employee.id}/`, form);
      // CompleteOnboardingForTheCurrentEmployee      await apiPost(`/Users/EmployeeProfiles/${employee.id}/complete-onboarding/`, {});
      reload(["me", "employees"]);
      navigate("/home/");
    } catch (err) {
      setError(err?.message || "FailedToCompleteOnboarding.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="Onboarding-ScreenScreen-Stack">
      <section className="Page-Heading">
        <div>
          <span>Welcome</span>
          <h1>Complete Your Onboarding</h1>
        </div>
      </section>

      <div className="Onboarding-Form-Container">
        <div className="Onboarding-Card">
          <div className="Onboarding-Header">
            <User size={32} />
            <h2>Personal Information</h2>
            <p>Please provide your details to complete the setup.</p>
          </div>

          {error && <div className="Login-Error"><AlertTriangle size={16} /> {error}</div>}

          <div className="Form-GridTwo">
            <label>
              Full Name
              <input
                value={form.display_name}
                onChange={(e) => update("display_name", e.target.value)}
                placeholder="YourFullLegalName"
              />
            </label>
            <label>
              Phone Number
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => update("phone", e.target.value)}
                placeholder="+91XXXXXXXXXX"
              />
            </label>
            <label>
              Address
              <input
                value={form.address}
                onChange={(e) => update("address", e.target.value)}
                placeholder="YourCurrentAddress"
              />
            </label>
            <label>
              Emergency Contact
              <input
                value={form.emergency_contact}
                onChange={(e) => update("emergency_contact", e.target.value)}
                placeholder="Name - Relationship - Phone"
              />
            </label>
          </div>

          <button className="Primary-Button" onClick={submit} disabled={busy}>
            {busy ? "Completing..." : "CompleteOnboarding"} <CheckCircle size={16} />
          </button>
        </div>
      </div>
    </section>
  );
}