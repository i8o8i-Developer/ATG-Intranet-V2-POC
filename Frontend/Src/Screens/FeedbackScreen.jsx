import React, { useState, useMemo } from "react";
import { 
  MessageSquare, Users, Send, Search, 
  Filter, CheckCircle, AlertCircle, Trash2,
  TrendingUp, Award, Zap
} from "lucide-react";
import { apiPost, apiDelete } from "../Api/Client.js";
import { Panel, EmptyState, SimpleTable, Progress } from "./Shared/ScreenComponents.jsx";
import { formatDate } from "./Shared/ScreenUtils.jsx";

const FEEDBACK_TYPES = [
  { label: "Recognition", icon: <Award size={14} />, color: "#10b981" },
  { label: "Constructive", icon: <Zap size={14} />, color: "#f59e0b" },
  { label: "Project Feedback", icon: <TrendingUp size={14} />, color: "#3b82f6" },
  { label: "General Note", icon: <MessageSquare size={14} />, color: "#64748b" },
];

export function FeedbackScreen({ data, reload }) {
  const [submitting, setSubmitting] = useState(false);
  const [search, setSearch] = useState("");
  const [formData, setFormData] = useState({
    employee: "",
    feedback_type: "General Note",
    project_name: "",
    feedback_text: "",
  });
  const [errors, setErrors] = useState({});
  const [success, setSuccess] = useState(false);

  const employees = data.employees || [];
  const feedbacks = data.employeeFeedback || [];

  const filteredFeedbacks = useMemo(() => {
    if (!search) return feedbacks;
    const s = search.toLowerCase();
    return feedbacks.filter(f => 
      String(f.feedback_text).toLowerCase().includes(s) ||
      String(f.project_name).toLowerCase().includes(s) ||
      String(f.employee_display_name || "").toLowerCase().includes(s)
    );
  }, [feedbacks, search]);

  const validate = () => {
    const errs = {};
    if (!formData.employee) errs.employee = "Please Select An Employee";
    if (!formData.feedback_text.trim()) errs.feedback_text = "Please Enter Feedback Content";
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }

    setSubmitting(true);
    setErrors({});
    try {
      await apiPost("/Users/EmployeeFeedback/", formData);
      setFormData({
        employee: "",
        feedback_type: "General Note",
        project_name: "",
        feedback_text: "",
      });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
      if (reload) reload(["employeeFeedback"]);
    } catch (err) {
      setErrors({ submit: err.message || "Failed To Submit Feedback" });
    } finally {
      setSubmitting(false);
    }
  };

  const deleteFeedback = async (id) => {
    if (!window.confirm("Are You Sure You Want To Remove This Feedback?")) return;
    try {
      await apiDelete(`/Users/EmployeeFeedback/${id}/`);
      if (reload) reload(["employeeFeedback"]);
    } catch (err) {
      alert("Failed To Delete Feedback");
    }
  };

  return (
    <div className="Feedback-Page" >
      <header className= "Feedback-Hero" >
        <div className="Hero-Content">
          <span className="Kicker">Talent Excellence</span>
          <h1>Employee Feedback</h1>
          <p>Provide Recognition, Constructive Criticism, Or Project Performance Notes.</p>
        </div>
        <div className="Hero-Stats">
          <div className="Stat-Card">
            <strong>{feedbacks.length}</strong>
            <span>Total Given</span>
          </div>
          <div className="Stat-Card Green">
            <strong>{feedbacks.filter(f => f.feedback_type === "Recognition").length}</strong>
            <span>Recognitions</span>
          </div>
        </div>
      </header>

      <div className="Feedback-Grid">
        <div className="Feedback-Form-Col">
          <Panel title="Submit New Feedback">
            <form className="Feedback-Form" onSubmit={handleSubmit}>
              <div className="Form-Group">
                <label>Target Employee</label>
                <div className="Select-Wrap">
                  <Users className="Icon" size={16} />
                  <select 
                    value={formData.employee} 
                    onChange={e => setFormData({...formData, employee: e.target.value})}
                    className={errors.employee ? "Error" : ""}
                  >
                    <option value="">Select An Employee...</option>
                    {employees.map(emp => (
                      <option key={emp.id} value={emp.id}>{emp.display_name} ({emp.department_name})</option>
                    ))}
                  </select>
                </div>
                {errors.employee && <small className="Error-Text">{errors.employee}</small>}
              </div>

              <div className="Form-Row">
                <div className="Form-Group">
                  <label>Feedback Type</label>
                  <select 
                    value={formData.feedback_type} 
                    onChange={e => setFormData({...formData, feedback_type: e.target.value})}
                  >
                    {FEEDBACK_TYPES.map(t => (
                      <option key={t.label} value={t.label}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div className="Form-Group">
                  <label>Project (Optional)</label>
                  <input 
                    placeholder="Project Name"
                    value={formData.project_name}
                    onChange={e => setFormData({...formData, project_name: e.target.value})}
                  />
                </div>
              </div>

              <div className="Form-Group">
                <label>Feedback Details</label>
                <textarea 
                  rows={6}
                  placeholder="Write Detailed Feedback Here..."
                  value={formData.feedback_text}
                  onChange={e => setFormData({...formData, feedback_text: e.target.value})}
                  className={errors.feedback_text ? "Error" : ""}
                />
                {errors.feedback_text && <small className="Error-Text">{errors.feedback_text}</small>}
              </div>

              {errors.submit && (
                <div className="Error-Banner">
                  <AlertCircle size={16} />
                  <span>{errors.submit}</span>
                </div>
              )}

              {success && (
                <div className="Success-Banner">
                  <CheckCircle size={16} />
                  <span>Feedback Submitted Successfully!</span>
                </div>
              )}

              <button type="submit" className="Primary-Button Wide" disabled={submitting}>
                {submitting ? "Submitting..." : <><Send size={16} /> Submit Feedback</>}
              </button>
            </form>
          </Panel>
        </div>

        <div className="Feedback-History-Col">
          <Panel 
            title="Feedback History"
            right={
              <div className="Table-Search">
                <Search size={14} />
                <input 
                  placeholder="Filter History..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                />
              </div>
            }
          >
            {filteredFeedbacks.length ? (
              <div className="Feedback-List">
                {filteredFeedbacks.map(item => {
                  const type = FEEDBACK_TYPES.find(t => t.label === item.feedback_type) || FEEDBACK_TYPES[3];
                  return (
                    <div key={item.id} className="Feedback-Item-Card">
                      <div className="Card-Head">
                        <div className="User-Info">
                          <div className="Avatar">{String(item.employee_display_name || "?")[0]}</div>
                          <div className="Meta">
                            <strong>{item.employee_display_name}</strong>
                            <small>{formatDate(item.created_at)}</small>
                          </div>
                        </div>
                        <span className="Type-Badge" style={{ background: type.color + "15", color: type.color }}>
                          {type.icon} {item.feedback_type}
                        </span>
                      </div>
                      <div className="Card-Body">
                        {item.project_name && <div className="Project-Tag">Project: {item.project_name}</div>}
                        <p>{item.feedback_text}</p>
                      </div>
                      <div className="Card-Footer">
                        <button className="Text-Button Danger" onClick={() => deleteFeedback(item.id)}>
                          <Trash2 size={14} /> Delete
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyState label="No Feedback History Found." />
            )}
          </Panel>
        </div>
      </div>

      <style>{`
        .Feedback-Page { padding: 24px; display: flex; flex-direction: column; gap: 24px; animation: fadeIn 0.4s ease-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .Feedback-Hero {
          display: flex; justify-content: space-between; align-items: center;
          padding: 32px; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
          border-radius: 16px; color: #fff; box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .Hero-Content .Kicker { color: #38bdf8; font-weight: 700; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; }
        .Hero-Content h1 { font-size: 32px; margin: 8px 0; font-weight: 800; }
        .Hero-Content p { color: #94a3b8; font-size: 16px; }

        .Hero-Stats { display: flex; gap: 16px; }
        .Stat-Card {
          background: rgba(255,255,255,0.05); padding: 16px 24px; border-radius: 12px;
          display: flex; flex-direction: column; align-items: center; min-width: 120px;
          border: 1px solid rgba(255,255,255,0.1);
        }
        .Stat-Card strong { font-size: 24px; color: #38bdf8; }
        .Stat-Card span { font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 600; margin-top: 4px; }
        .Stat-Card.Green strong { color: #10b981; }

        .Feedback-Grid { display: grid; grid-template-columns: 450px 1fr; gap: 24px; }

        .Feedback-Form { display: flex; flex-direction: column; gap: 20px; padding: 8px 0; }
        .Form-Group { display: flex; flex-direction: column; gap: 8px; }
        .Form-Group label { font-size: 13px; font-weight: 600; color: #475569; }
        .Form-Row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

        .Select-Wrap { position: relative; display: flex; align-items: center; }
        .Select-Wrap .Icon { position: absolute; left: 12px; color: #94a3b8; pointer-events: none; }
        .Select-Wrap select { padding-left: 36px; }

        input, select, textarea {
          width: 100%; padding: 10px 12px; border-radius: 8px;
          border: 1px solid #e2e8f0; background: #f8fafc;
          font-size: 14px; font-family: inherit; transition: all 0.2s;
        }
        input:focus, select:focus, textarea:focus {
          outline: none; border-color: #3b82f6; background: #fff;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        input.Error, select.Error, textarea.Error { border-color: #ef4444; background: #fef2f2; }

        .Error-Text { color: #ef4444; font-size: 12px; margin-top: 4px; font-weight: 500; }
        .Error-Banner {
          display: flex; align-items: center; gap: 8px; padding: 12px;
          background: #fef2f2; color: #dc2626; border-radius: 8px; font-size: 13px;
        }
        .Success-Banner {
          display: flex; align-items: center; gap: 8px; padding: 12px;
          background: #f0fdf4; color: #16a34a; border-radius: 8px; font-size: 13px;
        }

        .Primary-Button.Wide { justify-content: center; padding: 12px; font-size: 15px; font-weight: 600; margin-top: 8px; }

        .Table-Search {
          display: flex; align-items: center; gap: 8px;
          background: #f1f5f9; padding: 4px 12px; border-radius: 8px; width: 240px;
        }
        .Table-Search input { border: none; background: transparent; padding: 4px 0; font-size: 13px; box-shadow: none; }

        .Feedback-List { display: flex; flex-direction: column; gap: 16px; }
        .Feedback-Item-Card {
          background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
          padding: 20px; transition: all 0.2s;
        }
        .Feedback-Item-Card:hover { border-color: #cbd5e1; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }

        .Card-Head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
        .User-Info { display: flex; align-items: center; gap: 12px; }
        .Avatar {
          width: 40px; height: 40px; border-radius: 50%;
          background: #e0e7ff; color: #4338ca;
          display: flex; align-items: center; justify-content: center;
          font-weight: 700; font-size: 16px;
        }
        .Meta strong { display: block; font-size: 15px; color: #1e293b; }
        .Meta small { font-size: 12px; color: #94a3b8; }

        .Type-Badge {
          padding: 4px 10px; border-radius: 20px; font-size: 11px;
          font-weight: 700; display: flex; align-items: center; gap: 6px;
          text-transform: uppercase;
        }

        .Project-Tag {
          display: inline-block; padding: 2px 8px; border-radius: 4px;
          background: #f1f5f9; color: #64748b; font-size: 11px;
          font-weight: 600; margin-bottom: 8px;
        }
        .Card-Body p { color: #475569; font-size: 14px; line-height: 1.6; margin: 0; }

        .Card-Footer {
          margin-top: 16px; padding-top: 16px; border-top: 1px solid #f1f5f9;
          display: flex; justify-content: flex-end;
        }
        .Text-Button {
          background: transparent; border: none; cursor: pointer;
          font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 6px;
          padding: 4px 8px; border-radius: 6px; transition: background 0.2s;
        }
        .Text-Button.Danger { color: #94a3b8; }
        .Text-Button.Danger:hover { background: #fee2e2; color: #ef4444; }

        @media (max-width: 1200px) {
          .Feedback-Grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
}
