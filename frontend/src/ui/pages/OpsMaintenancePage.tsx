import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  Camera,
  CheckCircle2,
  ChevronRight,
  FileJson,
  ImagePlus,
  Search,
  Sparkles,
  Upload,
  Wrench,
} from 'lucide-react';
import { OpsWorkspaceFactory } from '../../application/OpsWorkspaceFactory';
import { OpsMaintenanceEvent, OpsMaintenanceSnapshot } from '../../domain/models';
import { OpsListModal } from '../components/OpsListModal';
import { formatStayName } from '../helpers/stayNames';

function nowForInput() {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 16);
}

function statusTone(status: string) {
  if (status === 'completed' || status === 'documented' || status === 'billed') return 'captured';
  if (status === 'in_progress' || status === 'scheduled' || status === 'logged') return 'authorized';
  if (status === 'draft') return 'pending';
  return 'released';
}

function parseErrorMessage(message: string) {
  try {
    const payload = JSON.parse(message);
    if (payload.errors) {
      return Object.entries(payload.errors)
        .map(([field, values]) => `${field}: ${(values as string[]).join(', ')}`)
        .join(' ');
    }
    return payload.error || message;
  } catch {
    return message;
  }
}

function compactDuration(minutes: number | null) {
  if (minutes === null) return 'Time pending';
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours}h ${rest}m` : `${hours}h`;
}

export function OpsMaintenancePage() {
  const service = useMemo(() => OpsWorkspaceFactory.create(), []);
  const [snapshot, setSnapshot] = useState<OpsMaintenanceSnapshot | null>(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [search, setSearch] = useState('');
  const [workType, setWorkType] = useState('');
  const [status, setStatus] = useState('');
  const [paymentStatus, setPaymentStatus] = useState('');
  const [photoFiles, setPhotoFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [payload, setPayload] = useState<Record<string, unknown> | null>(null);
  const [isPayloadOpen, setIsPayloadOpen] = useState(false);
  const [describingId, setDescribingId] = useState('');
  const [descriptionModes, setDescriptionModes] = useState<Record<string, 'manual' | 'ai'>>({});
  const [formValues, setFormValues] = useState({
    item: '',
    title: '',
    work_type: 'cleaning',
    status: 'completed',
    cost_amount: '',
    cost_currency: 'USD',
    reported_at: nowForInput(),
    started_at: '',
    completed_at: '',
    vendor_name: '',
    vendor_contact: '',
    payment_status: 'pending',
    invoice_number: '',
    proof_of_payment_ref: '',
    tax_category_code: '',
    description: '',
    admin_notes: '',
  });

  function loadSnapshot() {
    service
      .loadMaintenance()
      .then((data) => {
        setSnapshot(data);
        setError('');
        setFormValues((current) => ({
          ...current,
          item: current.item || (data.stays[0] ? String(data.stays[0].id) : ''),
        }));
      })
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : 'Could not load maintenance records.');
      });
  }

  useEffect(() => {
    loadSnapshot();
  }, []);

  const filteredRows = useMemo(() => {
    if (!snapshot) return [];
    const query = search.trim().toLowerCase();
    return snapshot.rows.filter((row) => {
      const matchesSearch = !query || [
        row.title,
        row.itemName,
        row.vendorName,
        row.description,
        row.aiDescription,
        row.workTypeLabel,
        row.statusLabel,
      ].some((value) => value.toLowerCase().includes(query));
      return matchesSearch
        && (!workType || row.workType === workType)
        && (!status || row.status === status)
        && (!paymentStatus || row.paymentStatus === paymentStatus);
    });
  }, [paymentStatus, search, snapshot, status, workType]);

  function updateForm(event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) {
    const { name, value } = event.target;
    setFormValues((current) => ({ ...current, [name]: value }));
  }

  function updatePhotos(event: ChangeEvent<HTMLInputElement>) {
    setPhotoFiles(Array.from(event.target.files || []));
  }

  async function submitMaintenance(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setMessage('');
    setError('');
    const formData = new FormData();
    Object.entries(formValues).forEach(([key, value]) => formData.set(key, value));
    photoFiles.forEach((file) => {
      formData.append('photos', file);
      formData.append('photo_captions', file.name);
    });
    try {
      const created = await service.createMaintenanceEvent(formData);
      setMessage(`Saved ${created.title}.`);
      setPhotoFiles([]);
      setFormValues((current) => ({
        ...current,
        title: '',
        cost_amount: '',
        started_at: '',
        completed_at: '',
        vendor_name: '',
        vendor_contact: '',
        invoice_number: '',
        proof_of_payment_ref: '',
        tax_category_code: '',
        description: '',
        admin_notes: '',
        reported_at: nowForInput(),
      }));
      loadSnapshot();
    } catch (caught) {
      setError(caught instanceof Error ? parseErrorMessage(caught.message) : 'Could not save maintenance record.');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function openPayload(row: OpsMaintenanceEvent) {
    setError('');
    try {
      const data = await service.loadMaintenanceAgentPayload(row.id);
      setPayload(data);
      setIsPayloadOpen(true);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not load agent payload.');
    }
  }

  async function generateAiDescription(row: OpsMaintenanceEvent) {
    setError('');
    setMessage('');
    setDescribingId(row.id);
    try {
      const updated = await service.generateMaintenanceAiDescription(row.id);
      setDescriptionModes((current) => ({ ...current, [updated.id]: 'ai' }));
      setMessage(`AI description added to ${updated.title}.`);
      loadSnapshot();
    } catch (caught) {
      setError(caught instanceof Error ? parseErrorMessage(caught.message) : 'Could not generate AI description.');
    } finally {
      setDescribingId('');
    }
  }

  const renderMaintenanceRow = (row: OpsMaintenanceEvent) => {
    const descriptionMode = descriptionModes[row.id] || (row.useAiDescription && row.aiDescription ? 'ai' : 'manual');
    const activeDescription = descriptionMode === 'ai' ? row.aiDescription : row.description;
    return (
    <details className="ops-data-row ops-data-row--maintenance ops-expand-card" data-status={statusTone(row.status)} key={row.id}>
      <summary className="ops-data-summary ops-maintenance-summary">
        <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
        <div className="ops-maintenance-thumb">
          {row.firstPhotoUrl ? <img src={row.firstPhotoUrl} alt="" /> : <Camera size={24} />}
        </div>
        <div>
          <span className={`ops-status-pill ops-status-pill--${statusTone(row.status)}`}>{row.statusLabel}</span>
          <h3>{row.title}</h3>
          <p>{formatStayName(row.itemName)} · {row.workTypeLabel}</p>
        </div>
        <div>
          <strong>{row.displayCost}</strong>
          <p>{row.reportedLabel || 'Date pending'} · {compactDuration(row.durationMinutes)}</p>
        </div>
        <div>
          <strong>{row.photoCount} photos</strong>
          <p>{row.isTaxReady ? 'Tax-ready evidence' : 'Needs tax evidence'}</p>
        </div>
      </summary>
      <div className="ops-expand-details ops-maintenance-details">
        <div>
          <div className="ops-maintenance-note-heading">
            <span>Work notes</span>
            {row.aiDescription && (
              <div className="ops-maintenance-description-toggle" aria-label="Description mode">
                <button
                  type="button"
                  className={descriptionMode === 'manual' ? 'is-active' : ''}
                  onClick={() => setDescriptionModes((current) => ({ ...current, [row.id]: 'manual' }))}
                >
                  Manual
                </button>
                <button
                  type="button"
                  className={descriptionMode === 'ai' ? 'is-active' : ''}
                  onClick={() => setDescriptionModes((current) => ({ ...current, [row.id]: 'ai' }))}
                >
                  AI
                </button>
              </div>
            )}
          </div>
          <p>{activeDescription || 'No description captured yet.'}</p>
          {descriptionMode === 'ai' && row.aiDescriptionGeneratedAt && (
            <small>Generated with {row.aiDescriptionModel || 'maintenance vision'}.</small>
          )}
          <small>{row.vendorName || 'No vendor'} {row.vendorContact ? `· ${row.vendorContact}` : ''}</small>
        </div>
        <div>
          <span>Payment evidence</span>
          <p>{row.paymentStatusLabel} {row.invoiceNumber ? `· Invoice ${row.invoiceNumber}` : ''}</p>
          <small>{row.proofOfPaymentRef || row.taxCategoryCode || 'Receipt/tax reference pending'}</small>
        </div>
        <div className="ops-row-actions">
          <button
            type="button"
            onClick={() => generateAiDescription(row)}
            disabled={describingId === row.id || row.photoCount === 0}
          >
            <Sparkles size={14} /> {describingId === row.id ? 'Reading photos...' : 'AI description'}
          </button>
          <button type="button" onClick={() => openPayload(row)}><FileJson size={14} /> Agent payload</button>
          <a href={row.adminUrl}>Record</a>
        </div>
        {row.photos.length > 0 && (
          <div className="ops-maintenance-photo-strip">
            {row.photos.slice(0, 6).map((photo) => (
              <a href={photo.url} target="_blank" rel="noreferrer" key={photo.id}>
                <img src={photo.url} alt={photo.caption || row.title} />
              </a>
            ))}
          </div>
        )}
      </div>
    </details>
    );
  };

  if (error && !snapshot) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!snapshot) {
    return <main className="dashboard-content ops-page"><section className="ops-hero is-loading" /></main>;
  }

  return (
    <main className="dashboard-content ops-page ops-page--maintenance">
      <section className="ops-hero ops-hero--maintenance">
        <div>
          <span><Wrench size={16} /> Maintenance operations</span>
          <h2>Maintenance</h2>
          <p>Log cleaning, repairs, cost, time, and photo evidence for agent-ready bills and tax records.</p>
        </div>
        <div className="ops-hero-actions">
          <a href={snapshot.adminUrl}>Maintenance admin</a>
          <a href={snapshot.addAdminUrl}>Add in admin</a>
        </div>
      </section>

      <section className="ops-metric-grid ops-maintenance-metrics">
        {snapshot.summaryCards.map((card) => (
          <article key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <p>{card.caption}</p>
          </article>
        ))}
      </section>

      <section className="ops-maintenance-layout">
        <form className="ops-maintenance-form" onSubmit={submitMaintenance}>
          <div className="ops-card-heading">
            <div>
              <span>New record</span>
              <h3>Work, cost, time, photos</h3>
              <p>Required: title, cost, time, and pictures.</p>
            </div>
            <button type="submit" disabled={isSubmitting}>
              <Upload size={15} /> {isSubmitting ? 'Saving...' : 'Save'}
            </button>
          </div>

          <div className="ops-form-grid">
            <label>
              Stay *
              <select name="item" value={formValues.item} onChange={updateForm} required>
                {snapshot.stays.map((stay) => (
                  <option value={stay.id} key={stay.id}>{formatStayName(stay.name)}</option>
                ))}
              </select>
            </label>
            <label>
              Title *
              <input name="title" value={formValues.title} onChange={updateForm} placeholder="Deep cleaning after stay" required />
            </label>
            <label>
              Work type *
              <select name="work_type" value={formValues.work_type} onChange={updateForm} required>
                {snapshot.workTypeOptions.filter((option) => option.value).map((option) => (
                  <option value={option.value} key={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
            <label>
              Status *
              <select name="status" value={formValues.status} onChange={updateForm} required>
                {snapshot.statusOptions.filter((option) => option.value).map((option) => (
                  <option value={option.value} key={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
            <label>
              Cost *
              <input name="cost_amount" value={formValues.cost_amount} onChange={updateForm} inputMode="decimal" placeholder="75.00" required />
            </label>
            <label>
              Currency
              <input name="cost_currency" value={formValues.cost_currency} onChange={updateForm} maxLength={3} required />
            </label>
            <label>
              Reported time *
              <input name="reported_at" type="datetime-local" value={formValues.reported_at} onChange={updateForm} required />
            </label>
            <label>
              Started
              <input name="started_at" type="datetime-local" value={formValues.started_at} onChange={updateForm} />
            </label>
            <label>
              Completed
              <input name="completed_at" type="datetime-local" value={formValues.completed_at} onChange={updateForm} />
            </label>
            <label>
              Vendor
              <input name="vendor_name" value={formValues.vendor_name} onChange={updateForm} placeholder="Cleaner, plumber, supplier..." />
            </label>
            <label>
              Payment
              <select name="payment_status" value={formValues.payment_status} onChange={updateForm}>
                {snapshot.paymentStatusOptions.filter((option) => option.value).map((option) => (
                  <option value={option.value} key={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
            <label>
              Receipt / invoice
              <input name="proof_of_payment_ref" value={formValues.proof_of_payment_ref} onChange={updateForm} placeholder="Receipt, Zelle, cash note..." />
            </label>
          </div>

          <label className="ops-maintenance-textarea">
            Description
            <textarea name="description" value={formValues.description} onChange={updateForm} placeholder="What was done, why, and anything the agent should know." />
          </label>

          <label className="ops-maintenance-upload">
            <ImagePlus size={18} />
            <span>{photoFiles.length ? `${photoFiles.length} photo(s) ready` : 'Add pictures *'}</span>
            <input type="file" accept="image/*" capture="environment" multiple onChange={updatePhotos} />
          </label>

          {photoFiles.length > 0 && (
            <div className="ops-maintenance-preview">
              {photoFiles.slice(0, 6).map((file) => (
                <figure key={`${file.name}-${file.lastModified}`}>
                  <img src={URL.createObjectURL(file)} alt="" />
                  <figcaption>{file.name}</figcaption>
                </figure>
              ))}
            </div>
          )}
        </form>

        <section className="ops-table-card ops-maintenance-records">
          <div className="ops-card-heading">
            <div>
              <span>Evidence ledger</span>
              <h3>{filteredRows.length} records shown</h3>
              <p>{snapshot.rows.length} maintenance objects available.</p>
            </div>
            <strong>{message || 'Photos + cost + time'}</strong>
          </div>

          {error && <div className="ops-res-alert"><AlertCircle size={16} /> {error}</div>}

          <section className="ops-toolbar ops-maintenance-toolbar">
            <label>
              <Search size={17} />
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search work, vendor, stay, notes..." />
            </label>
            <select value={workType} onChange={(event) => setWorkType(event.target.value)} aria-label="Work type">
              {snapshot.workTypeOptions.map((option) => <option value={option.value} key={option.value || 'all'}>{option.label} ({option.count})</option>)}
            </select>
            <select value={status} onChange={(event) => setStatus(event.target.value)} aria-label="Maintenance status">
              {snapshot.statusOptions.map((option) => <option value={option.value} key={option.value || 'all'}>{option.label} ({option.count})</option>)}
            </select>
            <select value={paymentStatus} onChange={(event) => setPaymentStatus(event.target.value)} aria-label="Payment status">
              {snapshot.paymentStatusOptions.map((option) => <option value={option.value} key={option.value || 'all'}>{option.label} ({option.count})</option>)}
            </select>
          </section>

          {filteredRows.length === 0 && (
            <article className="ops-empty-state">
              <CheckCircle2 size={28} />
              <h3>No maintenance records match this view.</h3>
              <p>Add the first record with cost, time, and pictures.</p>
            </article>
          )}

          <div className="ops-list-scroll">
            {filteredRows.map(renderMaintenanceRow)}
          </div>
        </section>
      </section>

      <OpsListModal
        isOpen={isPayloadOpen}
        title="Agent payload"
        subtitle="Structured JSON for bill, tax, and diagnosis automation."
        onClose={() => setIsPayloadOpen(false)}
      >
        <pre className="ops-json-payload">{payload ? JSON.stringify(payload, null, 2) : ''}</pre>
      </OpsListModal>
    </main>
  );
}
