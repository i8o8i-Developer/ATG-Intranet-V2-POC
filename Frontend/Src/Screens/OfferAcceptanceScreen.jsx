import React, { useEffect, useState } from "react";
import { CheckCircle, FileText, Check, AlertCircle, User, Shield, Download } from "lucide-react";
import { apiGet, apiPost } from "../Api/Client";

function fmt(val) {
  if (!val) return "—";
  const d = new Date(val);
  return isNaN(d) ? String(val) : d.toLocaleDateString("en-GB", { day: "2-digit", month: "long", year: "numeric" });
}

export default function OfferAcceptanceScreen() {
  const token = window.location.pathname.split("/offer/accept/")[1]?.replace(/\/$/, "");
  const [offer, setOffer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(1); // 1: Review, 2: NDA, 3: Profile, 4: Done
  const [accepting, setAccepting] = useState(false);
  const [ndaChecked, setNdaChecked] = useState(false);
  const [profile, setProfile] = useState({ full_name: "", phone: "", city: "", emergency_contact: "" });

  useEffect(() => {
    async function fetchOffer() {
      try {
        const data = await apiGet(`/MainApp/offer/${token}`);
        setOffer(data);
        if (data?.candidate_name) {
          setProfile((p) => ({ ...p, full_name: data.candidate_name }));
        }
      } catch {
        setError("Invalid or expired offer link. Please contact HR.");
      } finally {
        setLoading(false);
      }
    }
    if (token) fetchOffer();
    else { setError("No token found in URL."); setLoading(false); }
  }, [token]);

  const [acceptedOffer, setAcceptedOffer] = useState(null);

  const handleAcceptOffer = async () => {
    if (!ndaChecked) return;
    setAccepting(true);
    try {
      const result = await apiPost(`/MainApp/offer/${token}`, {
        accepted: true,
        nda_accepted: true,
        acceptance_timestamp: new Date().toISOString(),
        profile_data: profile,
      });
      setAcceptedOffer(result);
      setStep(4);
    } catch {
      alert("Failed to accept offer. Please try again or contact HR.");
    } finally {
      setAccepting(false);
    }
  };

  const payload = offer?.offer_payload || {};

  if (loading) {
    return (
      <div className="onboarding-flow-screen" style={{ background: "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)" }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "16px" }}>
          <div className="onboarding-spinner" />
          <p style={{ color: "#94a3b8", fontSize: "15px" }}>Loading your offer...</p>
        </div>
      </div>
    );
  }

  if (error || !offer) {
    return (
      <div className="onboarding-flow-screen" style={{ background: "linear-gradient(135deg, #0f172a, #1e293b)" }}>
        <div className="onboarding-card glass" style={{ textAlign: "center", maxWidth: "480px" }}>
          <AlertCircle size={52} style={{ color: "#ef4444", marginBottom: "16px" }} />
          <h2 style={{ color: "#111827", marginTop: 0 }}>Offer Unavailable</h2>
          <p style={{ color: "#6b7280" }}>{error}</p>
          <p style={{ color: "#9ca3af", fontSize: "13px" }}>Contact HR at projectdurgaaisolutions@gmail.com</p>
        </div>
      </div>
    );
  }

  const steps = [
    { n: 1, label: "Review Offer" },
    { n: 2, label: "Sign NDA" },
    { n: 3, label: "Your Profile" },
    { n: 4, label: "Confirmed" },
  ];

  return (
    <div className="onboarding-flow-screen" style={{ background: "linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f172a 100%)", padding: "24px 16px" }}>
      <div className="onboarding-container" style={{ maxWidth: "720px" }}>

        {/* Header */}
        <header className="onboarding-header" style={{ marginBottom: "8px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ width: "38px", height: "38px", borderRadius: "10px", background: "linear-gradient(135deg,#2563eb,#1d4ed8)", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: "800", color: "#fff", fontSize: "16px" }}>ATG</div>
            <div>
              <div style={{ fontWeight: "700", color: "#f8fafc", fontSize: "15px" }}>Across The Globe</div>
              <div style={{ fontSize: "12px", color: "#94a3b8" }}>Onboarding Portal</div>
            </div>
          </div>
          <div className="onboarding-progress" style={{ gap: "0" }}>
            {steps.map((s, i) => (
              <React.Fragment key={s.n}>
                <div style={{
                  display: "flex", flexDirection: "column", alignItems: "center", gap: "4px"
                }}>
                  <div style={{
                    width: "28px", height: "28px", borderRadius: "50%",
                    background: step >= s.n ? "linear-gradient(135deg,#2563eb,#1d4ed8)" : "rgba(255,255,255,0.1)",
                    color: step >= s.n ? "#fff" : "#94a3b8",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "12px", fontWeight: "700", transition: "all 0.3s"
                  }}>
                    {step > s.n ? <Check size={14} /> : s.n}
                  </div>
                  <span style={{ fontSize: "10px", color: step >= s.n ? "#93c5fd" : "#475569", whiteSpace: "nowrap" }}>{s.label}</span>
                </div>
                {i < steps.length - 1 && (
                  <div style={{ width: "32px", height: "2px", background: step > s.n ? "#2563eb" : "rgba(255,255,255,0.1)", margin: "0 4px", marginBottom: "16px", transition: "all 0.3s" }} />
                )}
              </React.Fragment>
            ))}
          </div>
        </header>

        {/* ── STEP 1: OFFER REVIEW ── */}
        {step === 1 && (
          <div className="onboarding-card glass fade-in">
            <div style={{ display: "flex", alignItems: "flex-start", gap: "16px", marginBottom: "28px" }}>
              <div style={{ width: "52px", height: "52px", borderRadius: "14px", background: "linear-gradient(135deg,#2563eb,#1d4ed8)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <FileText size={24} color="#fff" />
              </div>
              <div>
                <h2 style={{ margin: "0 0 4px", fontSize: "24px" }}>Welcome, {offer.candidate_name}!</h2>
                <p className="subtitle" style={{ margin: 0 }}>
                  Congratulations on your offer as <strong>{offer.position_title}</strong> at {offer.company_name || "ATG"}.
                </p>
              </div>
            </div>

            <div className="offer-preview-box">
              {[
                ["Candidate", offer.candidate_name],
                ["Role / Designation", offer.position_title],
                ["Company", offer.company_name || "Across The Globe (ATG)"],
                ["Department", payload.department_name || "—"],
                ["Sub Department", payload.sub_department_name || "—"],
                ["Employment Type", payload.employment_type || "Intern"],
                ["Date of Joining", fmt(payload.joining_date)],
                ["Compensation Type", payload.pay_type || "Performance Based"],
                ["System Username", payload.username || "—"],
              ].map(([label, value]) => (
                <div className="detail-row" key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>

            <div style={{ background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "12px", padding: "16px", marginBottom: "28px", fontSize: "14px", color: "#1e40af", lineHeight: "1.6" }}>
              <strong>📋 Please review your offer details carefully.</strong><br />
              This offer is valid for 15 days from the date of this email. Proceeding to the next step means you agree to review the Non-Disclosure Agreement (NDA) before final acceptance.
            </div>

            <button className="btn-modern primary" style={{ width: "100%" }} onClick={() => setStep(2)}>
              Continue to NDA &amp; Acceptance <FileText size={16} />
            </button>
          </div>
        )}

        {/* ── STEP 2: NDA ── */}
        {step === 2 && (
          <div className="onboarding-card glass fade-in">
            <div style={{ display: "flex", alignItems: "center", gap: "14px", marginBottom: "24px" }}>
              <div style={{ width: "46px", height: "46px", borderRadius: "12px", background: "linear-gradient(135deg,#7c3aed,#6d28d9)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <Shield size={22} color="#fff" />
              </div>
              <div>
                <h2 style={{ margin: 0, fontSize: "22px" }}>Non-Disclosure Agreement</h2>
                <p className="subtitle" style={{ margin: 0, fontSize: "14px" }}>Read carefully before signing.</p>
              </div>
            </div>

            <div className="nda-scroll-box">
              <p><strong>Hi {offer.candidate_name},</strong><br />
              Please read this agreement and agree to its terms before accepting your offer.</p>

              <h3>Confidentiality Agreement</h3>
              <p>It is understood and agreed to that the Discloser (Across The Globe / ATG) and the Recipient (you, the Candidate) would like to exchange certain information that may be considered confidential. To ensure the protection of such information and in consideration of the agreement to exchange said information, the parties agree as follows:</p>

              <h3>1. Confidential Information</h3>
              <p>The confidential information to be disclosed by Discloser under this Agreement ("Confidential Information") can be described as and includes: Technical and business information relating to Discloser's proprietary ideas, patentable ideas, copyrights and/or trade secrets, existing and/or contemplated products and services, software, research and development, production, costs, profit and margin information, finances, customers, clients, marketing, and current or future business plans and models.</p>

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
              <p>You shall not conduct yourself in any manner amounting to breach of confidence reposed in you or inconsistent with the position of responsibility occupied by you. Please deal with the Company's money, material and documents with utmost honesty, moral and professional ethics.</p>

              <h3>8. Data Privacy</h3>
              <p>The Company requires that you shall observe Data Privacy as per Company's regulations/policy, regarding the processing and protection of any personal information and/or data to which you may have access to in the course of your duties, and shall report any infringement relating to the manner in which personal information or other data is processed to the Company immediately.</p>

              <p style={{ marginTop: "16px" }}><strong>Congratulations!<br />Team ATG — Across The Globe</strong></p>
            </div>

            <label className="checkbox-label modern-checkbox">
              <input type="checkbox" checked={ndaChecked} onChange={(e) => setNdaChecked(e.target.checked)} />
              <div className="checkbox-custom"><Check size={14} /></div>
              <span>I, <strong>{offer.candidate_name}</strong>, have read and agree to the Non-Disclosure Agreement and all Terms &amp; Conditions of this offer.</span>
            </label>

            <div className="action-row">
              <button className="btn-modern secondary" onClick={() => setStep(1)}>← Back</button>
              <button
                className="btn-modern primary"
                disabled={!ndaChecked || accepting}
                onClick={() => setStep(3)}
              >
                Continue to Profile →
              </button>
            </div>
          </div>
        )}

        {/* ── STEP 3: PROFILE COMPLETION ── */}
        {step === 3 && (
          <div className="onboarding-card glass fade-in">
            <div style={{ display: "flex", alignItems: "center", gap: "14px", marginBottom: "24px" }}>
              <div style={{ width: "46px", height: "46px", borderRadius: "12px", background: "linear-gradient(135deg,#059669,#047857)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <User size={22} color="#fff" />
              </div>
              <div>
                <h2 style={{ margin: 0, fontSize: "22px" }}>Complete Your Profile</h2>
                <p className="subtitle" style={{ margin: 0, fontSize: "14px" }}>Help us set up your account before your joining date.</p>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "24px" }}>
              {[
                ["Full Legal Name", "full_name", "text", "As on official documents"],
                ["Mobile / WhatsApp", "phone", "tel", "+91 XXXXX XXXXX"],
                ["Current City", "city", "text", "Delhi, Mumbai, etc."],
                ["Emergency Contact", "emergency_contact", "text", "Name - Relationship - Phone"],
              ].map(([label, key, type, placeholder]) => (
                <label key={key} style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "14px", color: "#374151", fontWeight: "500" }}>
                  {label}
                  <input
                    type={type}
                    value={profile[key]}
                    placeholder={placeholder}
                    onChange={(e) => setProfile((p) => ({ ...p, [key]: e.target.value }))}
                    style={{ padding: "10px 14px", borderRadius: "10px", border: "1px solid #d1d5db", fontSize: "14px", background: "#f9fafb" }}
                  />
                </label>
              ))}
            </div>

            <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "12px", padding: "16px", marginBottom: "28px", fontSize: "13px", color: "#166534" }}>
              ✅ By clicking <strong>"Accept Offer & Sign NDA"</strong> below, you confirm that you have read and agreed to all offer terms and the NDA. Your onboarding credentials will be emailed to <strong>{offer.candidate_email}</strong>.
            </div>

            <div className="action-row">
              <button className="btn-modern secondary" onClick={() => setStep(2)}>← Back</button>
              <button
                className="btn-modern primary"
                disabled={accepting || !profile.full_name}
                onClick={handleAcceptOffer}
                style={{ minWidth: "200px" }}
              >
                {accepting ? "Processing..." : "Accept Offer & Sign NDA"} <CheckCircle size={16} />
              </button>
            </div>
          </div>
        )}

        {/* ── STEP 4: SUCCESS ── */}
        {step === 4 && (
          <div className="onboarding-card glass fade-in text-center">
            <div className="success-icon-wrap">
              <div style={{ width: "80px", height: "80px", borderRadius: "50%", background: "linear-gradient(135deg,#10b981,#059669)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 20px" }}>
                <CheckCircle size={44} color="#fff" className="bounce" />
              </div>
            </div>
            <h2 style={{ fontSize: "26px", marginBottom: "8px" }}>Offer Accepted!</h2>
            <p className="subtitle">Congratulations, <strong>{offer.candidate_name}</strong>! You have successfully accepted your offer and signed the NDA.</p>

            <div style={{ background: "linear-gradient(135deg, #0f172a, #1e293b)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "16px", padding: "24px", marginBottom: "24px", textAlign: "left" }}>
              <div style={{ color: "#94a3b8", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "16px" }}>Offer Summary</div>
              {[
                ["Role", offer.position_title],
                ["Company", offer.company_name || "ATG"],
                ["Joining Date", fmt(payload.joining_date)],
                ["Email", offer.candidate_email],
              ].map(([label, value]) => (
                <div key={label} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid rgba(255,255,255,0.06)", fontSize: "14px" }}>
                  <span style={{ color: "#94a3b8" }}>{label}</span>
                  <strong style={{ color: "#f1f5f9" }}>{value}</strong>
                </div>
              ))}
            </div>

            <div className="next-steps-box">
              <h3>What happens next?</h3>
              {acceptedOffer?.offer_payload?.onboarding?.provisioned && (
                <div style={{ background: "linear-gradient(135deg,#10b981,#059669)", borderRadius: "12px", padding: "16px", marginBottom: "16px", color: "#fff" }}>
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
