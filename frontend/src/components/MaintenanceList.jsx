/**
 * MaintenanceList.jsx
 * Displays all maintenance events for a given property.
 * Includes a button to fetch the invoice/agent payload.
 *
 * Usage:
 *   <MaintenanceList propertyId="<uuid>" />
 */

import React, { useEffect, useState } from "react";

export default function MaintenanceList({ propertyId }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [invoicePayload, setInvoicePayload] = useState(null);

  useEffect(() => {
    fetch(`/api/maintenance/?property=${propertyId}`, {
      credentials: "include",
    })
      .then((r) => r.json())
      .then((data) => {
        setEvents(Array.isArray(data) ? data : data.results || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [propertyId]);

  const fetchInvoice = async (id) => {
    const res = await fetch(`/api/maintenance/${id}/invoice-payload/`, {
      credentials: "include",
    });
    const data = await res.json();
    setInvoicePayload(data.payload);
  };

  if (loading) return <p>Loading maintenance events…</p>;
  if (events.length === 0)
    return (
      <div className="empty-state">
        <p>No maintenance events recorded yet.</p>
      </div>
    );

  return (
    <div className="maintenance-list">
      <h3>Maintenance History</h3>
      <table>
        <thead>
          <tr>
            <th>Title</th>
            <th>Category</th>
            <th>Date</th>
            <th>Cost</th>
            <th>Status</th>
            <th>Photos</th>
            <th>Invoice</th>
          </tr>
        </thead>
        <tbody>
          {events.map((evt) => (
            <tr key={evt.id}>
              <td>{evt.title}</td>
              <td>{evt.category}</td>
              <td>{evt.time_out?.start_at ? new Date(evt.time_out.start_at).toLocaleDateString() : "—"}</td>
              <td>{evt.cost_out ? `${evt.cost_out.amount} ${evt.cost_out.currency}` : "—"}</td>
              <td><span className={`badge badge-${evt.status?.toLowerCase()}`}>{evt.status}</span></td>
              <td>{evt.photos?.length ?? 0}</td>
              <td>
                <button
                  className="btn-secondary btn-sm"
                  onClick={() => fetchInvoice(evt.id)}
                >
                  Get Payload
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {invoicePayload && (
        <div className="invoice-payload-modal">
          <h4>Invoice / Agent Payload</h4>
          <pre>{JSON.stringify(invoicePayload, null, 2)}</pre>
          <button onClick={() => setInvoicePayload(null)}>Close</button>
        </div>
      )}
    </div>
  );
}
