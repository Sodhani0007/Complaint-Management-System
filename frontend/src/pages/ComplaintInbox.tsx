import { useEffect, useState } from "react";
import { extractErrorMessage, getComplaint, listComplaints } from "../api/client";
import type { ComplaintRead } from "../types/complaint";

export function ComplaintInbox() {
  const [items, setItems] = useState<ComplaintRead[]>([]);
  const [selected, setSelected] = useState<ComplaintRead | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const refresh = async () => {
    setBusy(true); setError("");
    try { setItems(await listComplaints()); }
    catch (err) { setError(extractErrorMessage(err)); }
    finally { setBusy(false); }
  };
  useEffect(() => { void refresh(); }, []);
  return <main className="demo-inbox">
    <h1>Saved complaints</h1>
    <p>The 20 most recent records. Select a complaint to inspect the saved values.</p>
    <button disabled={busy} onClick={refresh}>{busy ? "Loading…" : "Refresh"}</button>
    {error && <p role="alert" className="demo-error">{error}</p>}
    {!busy && items.length === 0 && <p>No complaints saved yet.</p>}
    <div className="demo-records">{items.map((item) => <button key={item.id} className="demo-record"
      onClick={async () => {
        setError("");
        try { setSelected(await getComplaint(item.id)); }
        catch (err) { setError(extractErrorMessage(err)); }
      }}>
      <strong>Complaint #{item.id} · {item.status}</strong>
      <span>{item.description}</span>
      <small>{item.severity || "Unassessed"} severity · {item.priority || "Unassigned"} priority</small>
    </button>)}</div>
    {selected && <section className="demo-detail" aria-label="Complaint details">
      <h2>Complaint #{selected.id}</h2><p>{selected.description}</p>
      <dl>
        <dt>Status</dt><dd>{selected.status}</dd>
        <dt>Severity</dt><dd>{selected.severity || "Unassessed"}</dd>
        <dt>Priority</dt><dd>{selected.priority || "Unassigned"}</dd>
        <dt>Customer</dt><dd>{selected.customer_name || "Not supplied"}</dd>
        <dt>Batch ID</dt><dd>{selected.batch_id}</dd>
      </dl>
    </section>}
  </main>;
}
