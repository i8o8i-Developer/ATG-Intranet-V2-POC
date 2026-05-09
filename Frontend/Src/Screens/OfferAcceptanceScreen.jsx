import React, { useEffect, useState } from "react";
import { CheckCircle, FileText, Check, AlertCircle, User, Shield, Download } from "Lucide-React";
import { apiGet, apiPost } from "../Api/Client";

function fmt(val) {
  if (!val) return "—";
  const d = new Date(val);
  return isNaN(d) ? String(val) : d.toLocaleDateString("En-GB", { day: "2-Digit", month: "long", year: "numeric" });
}

export default function OfferAcceptanceScreen() {
  const token = window.location.pathname.split("/offer/accept/")[1]?.replace(/\/$/, "");
  const [offer, setOffer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(1); // 1: Review, 2: NDA, 3: Profile, 4: Done  const [accepting, setAccepting] = useState(false);
  const [ndaChecked, setNdaChecked] = useState(false);
  const [profile, setProfile] = useState({ full_name: "", phone: "", city: "", emergency_contact: "", signature_name: "" });

  useEffect(() => {
    async function fetchOffer() {
      try {
        const data = await apiGet(`/MainApp/offer/${token}`);
        setOffer(data);
        if (data?.candidate_name) {
          setProfile((p) => ({ ...p, full_name: data.candidate_name, signature_name: data.candidate_name }));
        }
      } catch {
        setError("InvalidOrExpiredOfferLink. PleaseContactHR.");
      } finally {
        setLoading(false);
      }
    }
    if (token) fetchOffer();
    else { setError("NoTokenFoundInURL."); setLoading(false); }
  }, [token]);

  const [acceptedOffer, setAcceptedOffer] = useState(null);

  const handleAcceptOffer = async () => {
    if (!ndaChecked) return;
    if (!profile.signature_name) {
      alert("PleaseProvideYourSignatureNameBeforeAcceptingTheOffer.");
      return;
    }
    setAccepting(true);
    try {
      const result = await apiPost(`/MainApp/offer/${token}`, {
        accepted_nda: ndaChecked,
        accepted_terms: true,
        signature_name: profile.signature_name,
      });
      setAcceptedOffer(result);
      setStep(4);
    } catch {
      alert("FailedToAcceptOffer. PleaseTryAgainOrContactHR.");
    } finally {
      setAccepting(false);
    }
  };

  const payload = offer?.offer_payload || {};

  if (loading) {
    return (
      <div className="Onboarding-Flow-Screen" style={{ background: "Linear-Gradient(135deg, #0f172a0%, #1e293b50%, #0f172a100%)" }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "16px" }}>
          <div className="Onboarding-Spinner" />
          <p style={{ color: "#94a3b8", fontSize: "15px" }}>Loading your offer...</p>
        </div>
      </div>
    );
  }

  if (error || !offer) {
    return (
      <div className="Onboarding-Flow-Screen" style={{ background: "Linear-Gradient(135deg, #0f172a, #1e293b)" }}>
        <div className="Onboarding-CardGlass" style={{ textAlign: "center", maxWidth: "480px" }}>
          <AlertCircle size={52} style={{ color: "#ef4444", marginBottom: "16px" }} />
          <h2 style={{ color: "#111827", marginTop: 0 }}>Offer Unavailable</h2>
          <p style={{ color: "#6b7280" }}>{error}</p>
          <p style={{ color: "#9ca3af", fontSize: "13px" }}>Contact HR at projectdurgaaisolutions@gmail.com</p>
        </div>
      </div>
    );
  }

  const steps = [
    { n: 1, label: "ReviewOffer" },
    { n: 2, label: "SignNDA" },
    { n: 3, label: "YourProfile" },
    { n: 4, label: "Confirmed" },
  ];

  return (
    <div className="Onboarding-Flow-Screen" style={{ background: "Linear-Gradient(135deg, #0f172a0%, #1e293b60%, #0f172a100%)", padding: "24px16px" }}>
      <div className="Onboarding-Container" style={{ maxWidth: "720px" }}>

        {/* Header */}
        <header className="Onboarding-Header" style={{ marginBottom: "8px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ width: "38px", height: "38px", borderRadius: "10px", background: "Linear-Gradient(135deg,#2563eb,#1d4ed8)", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: "800", color: "#fff", fontSize: "16px" }}>ATG</div>
            <div>
              <div style={{ fontWeight: "700", color: "#f8fafc", fontSize: "15px" }}>Across The Globe</div>
              <div style={{ fontSize: "12px", color: "#94a3b8" }}>Onboarding Portal</div>
            </div>
          </div>
          <div className="Onboarding-Progress" style={{ gap: "0" }}>
            {steps.map((s, i) => (
              <React.Fragment key={s.n}>
                <div style={{
                  display: "flex", flexDirection: "column", alignItems: "center", gap: "4px"
                }}>
                  <div style={{
                    width: "28px", height: "28px", borderRadius: "50%",
                    background: step >= s.n ? "Linear-Gradient(135deg,#2563eb,#1d4ed8)" : "rgba(255,255,255,0.1)",
                    color: step >= s.n ? "#fff" : "#94a3b8",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "12px", fontWeight: "700", transition: "All0.3s"
                  }}>
                    {step > s.n ? <Check size={14} /> : s.n}
                  </div>
                  <span style={{ fontSize: "10px", color: step >= s.n ? "#93c5fd" : "#475569", whiteSpace: "nowrap" }}>{s.label}</span>
                </div>
                {i < steps.length - 1 && (
                  <div style={{ width: "32px", height: "2px", background: step > s.n ? "#2563eb" : "rgba(255,255,255,0.1)", margin: "04px", marginBottom: "16px", transition: "All0.3s" }} />
                )}
              </React.Fragment>
            ))}
          </div>
        </header>

        {/* ── STEP1: OFFERREVIEW ── */}
        {step === 1 && (
          <div className="Onboarding-CardGlassFade-In">
            <div style={{ display: "flex", alignItems: "Flex-Start", gap: "16px", marginBottom: "28px" }}>
              <div style={{ width: "52px", height: "52px", borderRadius: "14px", background: "Linear-Gradient(135deg,#2563eb,#1d4ed8)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <FileText size={24} color="#fff" />
              </div>
              <div>
                <h2 style={{ margin: "004px", fontSize: "24px" }}>Welcome, {offer.candidate_name}!</h2>
                <p className="subtitle" style={{ margin: 0 }}>
                  Congratulations on your offer as <strong>{offer.position_title}</strong> at {offer.company_name || "ATG"}.
                </p>
              </div>
            </div>

            <div className="Offer-Preview-Box">
              {[
                ["Candidate", offer.candidate_name],
                ["Role / Designation", offer.position_title],
                ["Company", offer.company_name || "AcrossTheGlobe (ATG)"],
                ["Department", payload.department_name || "—"],
                ["SubDepartment", payload.sub_department_name || "—"],
                ["EmploymentType", payload.employment_type || "Intern"],
                ["DateOfJoining", fmt(payload.joining_date)],
                ["CompensationType", payload.pay_type || "PerformanceBased"],
                ["SystemUsername", payload.username || "—"],
              ].map(([label, value]) => (
                <div className="Detail-Row" key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>

            <div style={{ background: "#eff6ff", border: "1pxSolid #Bfdbfe", borderRadius: "12px", padding: "16px", marginBottom: "28px", fontSize: "14px", color: "#1e40af", lineHeight: "1.6" }}>
              <strong>📋 Please review your offer details carefully.</strong><br />
              This offer is valid for 15 days from the date of this email. Proceeding to the next step means you agree to review the Non-Disclosure Agreement (NDA) before final acceptance.
            </div>

            <button className="Btn-ModernPrimary" style={{ width: "100%" }} onClick={() => setStep(2)}>
              Continue to NDA &amp; Acceptance <FileText size={16} />
            </button>
          </div>
        )}

        {/* ── STEP2: NDA ── */}
        {step === 2 && (
          <div className="Onboarding-CardGlassFade-In">
            <div style={{ display: "flex", alignItems: "center", gap: "14px", marginBottom: "24px" }}>
              <div style={{ width: "46px", height: "46px", borderRadius: "12px", background: "Linear-Gradient(135deg,#7c3aed,#6d28d9)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <Shield size={22} color="#fff" />
              </div>
              <div>
                <h2 style={{ margin: 0, fontSize: "22px" }}>Non-Disclosure Agreement</h2>
                <p className="subtitle" style={{ margin: 0, fontSize: "14px" }}>Read carefully before signing.</p>
              </div>
            </div>

            <div className="Nda-Scroll-Box">
              <p><strong>Hi {offer.candidate_name},</strong><br />
              Please read this agreement and agree to its terms before accepting your offer.</p>

              <h3>Confidentiality Agreement</h3>
              <p>It is understood and agreed to that the Discloser (Across The Globe / ATG) and the Recipient (you, the Candidate) would like to exchange certain information that may be considered confidential. To ensure the protection of such information and in consideration of the agreement to exchange said information, the parties agree as follows:</p>

              <h3>1. Confidential Information</h3>
              <p>The confidential information to be disclosed by Discloser under this Agreement ("ConfidentialInformation") can be described as and includes: Technical and business information relating to Discloser's proprietary ideas, patentable ideas, copyrights and/or trade secrets, existing and/or contemplated products and services, software, research and development, production, costs, profit and margin information, finances, customers, clients, marketing, and current or future business plans and models.</p>

              <h3>2. Non-Disclosure Obligation</h3>
              <p>Recipient shall use the Confidential Information only for the purpose of evaluating potential business and investment relationships with Discloser. Recipient shall limit disclosure of Confidential Information within its own organization to its directors, officers, partners, members and/or employees having a need to know and shall not disclose Confidential Information to any third party without the prior written consent of Discloser.</p>

              <h3>3. Term of Agreement</h3>
              <p>This Agreement shall remain in full force and effect for the period of employment and for a period of 5 (five) years after termination of employment, whatever the reason for such termination.</p>

              <h3>4. Non-Solicitation</h3>
              <p>Unless authorized in writing by the Company, you shall not divulge, communicate or pass on any "confidential" information in any form, related to any aspect of the Company to anyone outside the Company. You acknowledge that the Company owns trade secrets and confidential and proprietary information that are very important to the success of the Company's business.</p>

              <h3>5. Reporting / Joining</h3>
              <p>Your Appointment shall be effective from your Date of Joining. You will be on probation for a period of 1 (One) month from the date of your joining. Your probation period can be extended further at the sole discretion of the Company if your performance / conduct are found to be unsatisfactory.</p>

              <h3>6. Resignation / Termination</h3>
              <p>You shall give a One Month prior notice to the Company before you can be officially relieved from your work. For Interns whose location is Work From Home, the period is One Week. Internship can be extended to beyond 6 months at the discretion of your manager.</p>

              <h3>7. Professional Ethics</h3>
              <p>You shall not conduct yourself in any manner amounting to breach of confidence reposed in you or inconsistent with the position of responsibility occupied by you. Please deal with the Company'SMoney, MaterialAndDocumentsWithUtmostHonesty, MoralAndProfessionalEthics.</P>

              <H3>8. DataPrivacy</H3>
              <P>TheCompanyRequiresThatYouShallObserveDataPrivacyAsPerCompany's regulations/policy, regarding the processing and protection of any personal information and/or data to which you may have access to in the course of your duties, and shall report any infringement relating to the manner in which personal information or other data is processed to the Company immediately.</p>

              <p style={{ marginTop: "16px" }}><strong>Congratulations!<br />Team ATG — Across The Globe</strong></p>
            </div>

            <label className="Checkbox-LabelModern-Checkbox">
              <input type="checkbox" checked={ndaChecked} onChange={(e) => setNdaChecked(e.target.checked)} />
              <div className="Checkbox-Custom"><Check size={14} /></div>
              <span>I, <strong>{offer.candidate_name}</strong>, have read and agree to the Non-Disclosure Agreement and all Terms &amp; Conditions of this offer.</span>
            </label>

            <div className="Action-Row">
              <button className="Btn-ModernSecondary" onClick={() => setStep(1)}>← Back</button>
              <button
                className="Btn-ModernPrimary"
                disabled={!ndaChecked || accepting}
                onClick={() => setStep(3)}
              >
                Continue to Profile →
              </button>
            </div>
          </div>
        )}

        {/* ── STEP3: PROFILECOMPLETION ── */}
        {step === 3 && (
          <div className="Onboarding-CardGlassFade-In">
            <div style={{ display: "flex", alignItems: "center", gap: "14px", marginBottom: "24px" }}>
              <div style={{ width: "46px", height: "46px", borderRadius: "12px", background: "Linear-Gradient(135deg,#059669,#047857)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <User size={22} color="#fff" />
              </div>
              <div>
                <h2 style={{ margin: 0, fontSize: "22px" }}>Complete Your Profile</h2>
                <p className="subtitle" style={{ margin: 0, fontSize: "14px" }}>Help us set up your account before your joining date.</p>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr1fr", gap: "16px", marginBottom: "24px" }}>
              {[
                ["FullLegalName", "full_name", "text", "AsOnOfficialDocuments"],
                ["SignatureName", "signature_name", "text", "TypeYourFullNameToSign"],
                ["Mobile / WhatsApp", "phone", "tel", "+91XXXXXXXXXX"],
                ["CurrentCity", "city", "text", "Delhi, Mumbai, Etc."],
                ["EmergencyContact", "emergency_contact", "text", "Name - Relationship - Phone"],
              ].map(([label, key, type, placeholder]) => (
                <label key={key} style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "14px", color: "#374151", fontWeight: "500" }}>
                  {label}
                  <input
                    type={type}
                    value={profile[key]}
                    placeholder={placeholder}
                    onChange={(e) => setProfile((p) => ({ ...p, [key]: e.target.value }))}
                    style={{ padding: "10px14px", borderRadius: "10px", border: "1pxSolid #D1d5db", fontSize: "14px", background: "#f9fafb" }}
                  />
                </label>
              ))}
            </div>

            <div style={{ background: "#f0fdf4", border: "1pxSolid #Bbf7d0", borderRadius: "12px", padding: "16px", marginBottom: "28px", fontSize: "13px", color: "#166534" }}>
              ✅ By clicking <strong>"AcceptOffer & SignNDA"</strong> below, you confirm that you have read and agreed to all offer terms and the NDA. Your onboarding credentials will be emailed to <strong>{offer.candidate_email}</strong>.
            </div>

            <div className="Action-Row">
              <button className="Btn-ModernSecondary" onClick={() => setStep(2)}>← Back</button>
              <button
                className="Btn-ModernPrimary"
                disabled={accepting || !profile.signature_name}
                onClick={handleAcceptOffer}
                style={{ minWidth: "200px" }}
              >
                {accepting ? "Processing..." : "AcceptOffer & SignNDA"} <CheckCircle size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ── STEP4: SUCCESS ── */}
        {step === 4 && (
          <div className="Onboarding-CardGlassFade-InText-Center">
            <div className="Success-Icon-Wrap">
              <div style={{ width: "80px", height: "80px", borderRadius: "50%", background: "Linear-Gradient(135deg,#10b981,#059669)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0Auto20px" }}>
                <CheckCircle size={44} color="#fff" className="bounce" />
              </div>
            </div>
            <h2 style={{ fontSize: "26px", marginBottom: "8px" }}>Offer Accepted!</h2>
            <p className="subtitle">Congratulations, <strong>{offer.candidate_name}</strong>! You have successfully accepted your offer and signed the NDA.</p>

            <div style={{ background: "Linear-Gradient(135deg, #0f172a, #1e293b)", border: "1pxSolidRgba(255,255,255,0.1)", borderRadius: "16px", padding: "24px", marginBottom: "24px", textAlign: "left" }}>
              <div style={{ color: "#94a3b8", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "16px" }}>Offer Summary</div>
              {[
                ["Role", offer.position_title],
                ["Company", offer.company_name || "ATG"],
                ["JoiningDate", fmt(payload.joining_date)],
                ["Email", offer.candidate_email],
              ].map(([label, value]) => (
                <div key={label} style={{ display: "flex", justifyContent: "Space-Between", padding: "8px0", borderBottom: "1pxSolidRgba(255,255,255,0.06)", fontSize: "14px" }}>
                  <span style={{ color: "#94a3b8" }}>{label}</span>
                  <strong style={{ color: "#f1f5f9" }}>{value}</strong>
                </div>
              ))}
            </div>

            <div className="Next-Steps-Box">
              <h3>What happens next?</h3>
              {acceptedOffer?.offer_payload?.onboarding?.provisioned && (
                <div style={{ background: "Linear-Gradient(135deg,#10b981,#059669)", borderRadius: "12px", padding: "16px", marginBottom: "16px", color: "#fff" }}>
                  <div style={{ fontWeight: "700", marginBottom: "6px" }}>✅ Your Intranet Account is Ready!</div>
                  <div style={{ fontSize: "14px", opacity: 0.9 }}>
                    Username: <strong style={{ fontFamily: "monospace", fontSize: "16px" }}>{acceptedOffer.offer_payload.onboarding.username}</strong>
                  </div>
                  <div style={{ fontSize: "13px", opacity: 0.8, marginTop: "4px" }}>Your temporary password has been emailed to <strong>{offer.candidate_email}</strong></div>
                </div>
              )}
              <ul>
                <li>✉️ Your <strong>intranet credentials</strong> (username + temporary password) have been sent to your email.</li>
                <li>🔑 Login at <a href={window.location.origin} style={{ color: "#2563eb" }}>{window.location.origin}</a> and change your password after first login.</li>
                <li>👔 Your manager will reach out via WhatsApp/email with first-day instructions.</li>
                <li>💻 IT setup will be ready before your joining date: <strong>{fmt(payload.joining_date)}</strong>.</li>
              </ul>
            </div>

            <p style={{ marginTop: "20px", fontSize: "13px", color: "#9ca3af" }}>
              Questions? Email HR at <a href="mailto:projectdurgaaisolutions@gmail.com" style={{ color: "#2563eb" }}>projectdurgaaisolutions@gmail.com</a>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
