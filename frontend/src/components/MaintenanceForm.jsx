/**
 * MaintenanceForm.jsx
 * React form for creating a MaintenanceEvent via the REST API.
 * Works on desktop and mobile (responsive, camera-capture enabled on mobile).
 *
 * Required fields: title, cost (amount + currency), time (start_at), pictures (>=1)
 * POST to: /api/maintenance/
 *
 * Usage:
 *   <MaintenanceForm propertyId="<uuid>" onSuccess={(event) => console.log(event)} />
 */

import React, { useState } from "react";

const CATEGORIES = [
  { value: "CLEANING", label: "Cleaning" },
  { value: "REPAIR", label: "Repair" },
  { value: "INSPECTION", label: "Inspection" },
  { value: "OTHER", label: "Other" },
];

const CURRENCIES = ["USD", "EUR", "DOP", "GBP"];

export default function MaintenanceForm({ propertyId, bookingId = null, onSuccess }) {
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("CLEANING");
  const [costAmount, setCostAmount] = useState("");
  const [costCurrency, setCostCurrency] = useState("USD");
  const [startAt, setStartAt] = useState("");
  const [endAt, setEndAt] = useState("");
  const [description, setDescription] = useState("");
  const [pictures, setPictures] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    setPictures(files);
    setPreviews(files.map((f) => URL.createObjectURL(f)));
  };

  const validate = () => {
    const errs = {};
    if (!title.trim()) errs.title = "Title is required.";
    if (!costAmount || parseFloat(costAmount) < 0) errs.costAmount = "Valid cost is required.";
    if (!startAt) errs.startAt = "Start time is required.";
    if (pictures.length === 0) errs.pictures = "At least one picture is required.";
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }
    setErrors({});
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("property", propertyId);
      if (bookingId) formData.append("booking", bookingId);
      formData.append("title", title.trim());
      formData.append("category", category);
      formData.append("description", description);
      // Nested cost as flat keys — backend serializer merges them
      formData.append("cost[amount]", costAmount);
      formData.append("cost[currency]", costCurrency);
      // Nested time
      formData.append("time[start_at]", new Date(startAt).toISOString());
      if (endAt) formData.append("time[end_at]", new Date(endAt).toISOString());
      // Pictures
      pictures.forEach((file, idx) => {
        formData.append(`pictures[${idx}]image`, file);
      });

      const res = await fetch("/api/maintenance/", {
        method: "POST",
        headers: {
          // Include CSRF token if your Django setup requires it
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json();
        setErrors(data);
      } else {
        const event = await res.json();
        setSuccess(true);
        if (onSuccess) onSuccess(event);
      }
    } catch (err) {
      setErrors({ non_field_errors: "Network error. Please try again." });
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="maintenance-success">
        <h3>✅ Maintenance event recorded!</h3>
        <button onClick={() => { setSuccess(false); setTitle(""); setCostAmount(""); setStartAt(""); setEndAt(""); setPictures([]); setPreviews([]); }}>
          Record another
        </button>
      </div>
    );
  }

  return (
    <form className="maintenance-form" onSubmit={handleSubmit} encType="multipart/form-data">
      <h2>Log Maintenance / Cleaning</h2>

      {/* Title */}
      <div className="field">
        <label htmlFor="mf-title">Title <span className="required">*</span></label>
        <input
          id="mf-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Turnover cleaning after checkout"
          maxLength={200}
        />
        {errors.title && <span className="field-error">{errors.title}</span>}
      </div>

      {/* Category */}
      <div className="field">
        <label htmlFor="mf-category">Category</label>
        <select id="mf-category" value={category} onChange={(e) => setCategory(e.target.value)}>
          {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
        </select>
      </div>

      {/* Cost */}
      <div className="field field-row">
        <div>
          <label htmlFor="mf-cost">Cost <span className="required">*</span></label>
          <input
            id="mf-cost"
            type="number"
            step="0.01"
            min="0"
            value={costAmount}
            onChange={(e) => setCostAmount(e.target.value)}
            placeholder="85.00"
          />
          {errors.costAmount && <span className="field-error">{errors.costAmount}</span>}
        </div>
        <div>
          <label htmlFor="mf-currency">Currency</label>
          <select id="mf-currency" value={costCurrency} onChange={(e) => setCostCurrency(e.target.value)}>
            {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      </div>

      {/* Time */}
      <div className="field field-row">
        <div>
          <label htmlFor="mf-start">Start <span className="required">*</span></label>
          <input id="mf-start" type="datetime-local" value={startAt} onChange={(e) => setStartAt(e.target.value)} />
          {errors.startAt && <span className="field-error">{errors.startAt}</span>}
        </div>
        <div>
          <label htmlFor="mf-end">End (optional)</label>
          <input id="mf-end" type="datetime-local" value={endAt} onChange={(e) => setEndAt(e.target.value)} />
        </div>
      </div>

      {/* Description */}
      <div className="field">
        <label htmlFor="mf-desc">Description</label>
        <textarea
          id="mf-desc"
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Additional notes..."
        />
      </div>

      {/* Pictures — supports camera capture on mobile */}
      <div className="field">
        <label htmlFor="mf-pics">Pictures <span className="required">*</span></label>
        <input
          id="mf-pics"
          type="file"
          accept="image/*"
          capture="environment"
          multiple
          onChange={handleFileChange}
        />
        {errors.pictures && <span className="field-error">{errors.pictures}</span>}
        {previews.length > 0 && (
          <div className="photo-previews">
            {previews.map((src, i) => (
              <img key={i} src={src} alt={`Preview ${i + 1}`} width={80} height={80} style={{ objectFit: "cover", borderRadius: 6, marginRight: 4 }} />
            ))}
          </div>
        )}
      </div>

      {errors.non_field_errors && (
        <div className="field-error">{errors.non_field_errors}</div>
      )}

      <button type="submit" disabled={loading} className="btn-primary">
        {loading ? "Saving…" : "Save Maintenance Event"}
      </button>
    </form>
  );
}

// Helper to read Django CSRF cookie
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return "";
}
