import React, { useState, useMemo } from "react";
import { 
  MessageSquare, Users, Send, Search, X,
  Filter, CheckCircle, AlertCircle, Trash2,
  TrendingUp, Award, Zap
} from "lucide-react";
import { apiPost, apiDelete } from "../Api/Client.js";
import { Panel, EmptyState, SimpleTable, Progress } from "./Shared/ScreenComponents.jsx";
import { formatDate } from "./Shared/ScreenUtils.jsx";
import "../Styles/FeedbackScreen.css";

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
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleteBusy, setDeleteBusy] = useState(false);

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
    setDeleteBusy(true);
    try {
      await apiDelete(`/Users/EmployeeFeedback/${id}/`);
      setDeleteConfirm(null);
      if (reload) reload(["employeeFeedback"]);
    } catch (err) {
      setErrors({ submit: "Failed To Delete Feedback" });
    } finally {
      setDeleteBusy(false);
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
                  <button className="Dismiss-Button" onClick={() => setErrors({})}><X size={14} /></button>
                </div>
              )}

              {success && (
                <div className="Success-Banner">
                  <CheckCircle size={16} />
                  <span>Feedback Submitted Successfully!</span>
                  <button className="Dismiss-Button" onClick={() => setSuccess(false)}><X size={14} /></button>
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
                        {deleteConfirm === item.id ? (
                          <span style={{ display: "flex", gap: 4, alignItems: "center" }}>
                            <button className="Text-Button Danger" onClick={() => deleteFeedback(item.id)} disabled={deleteBusy}>Confirm</button>
                            <button className="Text-Button" onClick={() => setDeleteConfirm(null)}>Cancel</button>
                          </span>
                        ) : (
                          <button className="Text-Button Danger" onClick={() => setDeleteConfirm(item.id)}>
                            <Trash2 size={14} /> Delete
                          </button>
                        )}
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


    </div>
  );
}
