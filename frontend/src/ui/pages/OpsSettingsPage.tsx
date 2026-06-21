import { ChangeEvent, useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  Download,
  ExternalLink,
  LockKeyhole,
  RotateCcw,
  Save,
  Search,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';
import { OpsWorkspaceFactory } from '../../application/OpsWorkspaceFactory';
import { OpsSettingsField, OpsSettingsSection, OpsSettingsSnapshot } from '../../domain/models';
import './ops-settings-page.css';

type DraftValue = string | boolean | number;
type DraftState = Record<string, DraftValue>;

function snapshotToDraft(snapshot: OpsSettingsSnapshot): DraftState {
  return snapshot.sections.reduce<DraftState>((draft, section) => {
    section.fields.forEach((field) => {
      draft[field.key] = field.value;
    });
    return draft;
  }, {});
}

function statusTone(section: OpsSettingsSection) {
  if (section.statusTone === 'green') return 'green';
  if (section.statusTone === 'orange') return 'orange';
  if (section.statusTone === 'blue') return 'blue';
  if (section.statusTone === 'violet') return 'violet';
  return 'slate';
}

function fieldValue(draft: DraftState, field: OpsSettingsField) {
  return draft[field.key] ?? field.value;
}

function exportSettings(snapshot: OpsSettingsSnapshot, draft: DraftState) {
  const blob = new Blob([JSON.stringify({ snapshot, draft }, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `mladis-settings-draft-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function readSavedDraft(): DraftState {
  const saved = localStorage.getItem('mladis.ops.settings.draft');
  if (!saved) return {};
  try {
    const parsed = JSON.parse(saved);
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) return parsed as DraftState;
  } catch {
    localStorage.removeItem('mladis.ops.settings.draft');
  }
  return {};
}

function SettingsFieldControl({
  field,
  value,
  onChange,
}: {
  field: OpsSettingsField;
  value: DraftValue;
  onChange: (key: string, value: DraftValue) => void;
}) {
  if (field.type === 'boolean') {
    const checked = Boolean(value);
    return (
      <button
        className={`ops-settings-toggle ${checked ? 'is-on' : ''}`}
        onClick={() => onChange(field.key, !checked)}
        type="button"
      >
        {checked ? <ToggleRight size={20} /> : <ToggleLeft size={20} />}
        {checked ? 'Enabled' : 'Disabled'}
      </button>
    );
  }

  if (field.type === 'textarea') {
    return (
      <textarea
        value={String(value ?? '')}
        onChange={(event: ChangeEvent<HTMLTextAreaElement>) => onChange(field.key, event.target.value)}
        rows={5}
      />
    );
  }

  return (
    <input
      type={field.type === 'email' || field.type === 'url' ? field.type : 'text'}
      value={String(value ?? '')}
      onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(field.key, event.target.value)}
    />
  );
}

export function OpsSettingsPage() {
  const service = useMemo(() => OpsWorkspaceFactory.create(), []);
  const [snapshot, setSnapshot] = useState<OpsSettingsSnapshot | null>(null);
  const [draft, setDraft] = useState<DraftState>({});
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [activeSection, setActiveSection] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    let mounted = true;
    service.loadSettings()
      .then((data) => {
        if (!mounted) return;
        setSnapshot(data);
        setDraft({ ...snapshotToDraft(data), ...readSavedDraft() });
        setActiveSection(data.sections[0]?.id || '');
      })
      .catch((caught: unknown) => {
        if (mounted) setError(caught instanceof Error ? caught.message : 'Could not load settings.');
      });
    return () => {
      mounted = false;
    };
  }, [service]);

  const filteredSections = useMemo(() => {
    if (!snapshot) return [];
    const query = search.trim().toLowerCase();
    return snapshot.sections.filter((section) => {
      if (!query) return true;
      return [
        section.label,
        section.description,
        section.status,
        ...section.fields.flatMap((field) => [field.label, field.key, String(field.value)]),
      ].some((value) => value.toLowerCase().includes(query));
    });
  }, [search, snapshot]);

  const selectedSection = filteredSections.find((section) => section.id === activeSection)
    || filteredSections[0]
    || snapshot?.sections[0]
    || null;

  function updateField(key: string, value: DraftValue) {
    setDraft((current) => ({ ...current, [key]: value }));
    setMessage('Draft updated locally. Open Django admin to publish persistent settings.');
  }

  function saveDraft() {
    localStorage.setItem('mladis.ops.settings.draft', JSON.stringify(draft));
    setMessage('Draft saved in this browser session.');
  }

  function resetDraft() {
    if (!snapshot) return;
    localStorage.removeItem('mladis.ops.settings.draft');
    setDraft(snapshotToDraft(snapshot));
    setMessage('Draft reset to the live API values.');
  }

  if (error) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!snapshot || !selectedSection) {
    return <main className="dashboard-content ops-settings-page"><section className="ops-settings-card">Loading settings...</section></main>;
  }

  return (
    <main className="dashboard-content ops-settings-page">
      <section className="ops-settings-titlebar">
        <div>
          <h1>Settings</h1>
          <p>Review brand, documents, notifications, provider readiness, and protected configuration status.</p>
        </div>
        <div className="ops-settings-title-actions">
          <a href={snapshot.adminUrls.site_settings || '/admin/bookings/sitesettings/'}><Settings2 size={16} /> Django settings <ExternalLink size={14} /></a>
          <button type="button" onClick={saveDraft}><Save size={16} /> Save draft</button>
          <button type="button" onClick={() => exportSettings(snapshot, draft)}><Download size={16} /> Export</button>
        </div>
      </section>

      {message && <section className="ops-settings-alert"><CheckCircle2 size={16} /> {message}</section>}

      <section className="ops-settings-metrics">
        {snapshot.summaryCards.map((card) => (
          <article key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <p>{card.caption}</p>
          </article>
        ))}
      </section>

      <section className="ops-settings-workspace">
        <aside className="ops-settings-card ops-settings-menu">
          <label>
            <Search size={15} />
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search settings..." />
          </label>
          <nav aria-label="Settings sections">
            {filteredSections.map((section) => (
              <button
                className={selectedSection.id === section.id ? 'is-active' : ''}
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                type="button"
              >
                <span className={`ops-settings-dot ops-settings-dot--${statusTone(section)}`} />
                <span><strong>{section.label}</strong><small>{section.description}</small></span>
                <ChevronRight size={15} />
              </button>
            ))}
          </nav>
          <section className="ops-settings-owner-links">
            <a href={snapshot.adminUrls.oauth || '/ops/oauth/'}><LockKeyhole size={15} /> OAuth diagnostics</a>
            <a href={snapshot.adminUrls.agent_faq || '/admin/bookings/agentfaq/'}><ShieldCheck size={15} /> Agent FAQ admin</a>
            <a href={snapshot.adminUrls.users || '/ops/admin/'}><SlidersHorizontal size={15} /> Admin access</a>
          </section>
        </aside>

        <section className="ops-settings-card ops-settings-editor">
          <header>
            <div>
              <span className={`ops-settings-status ops-settings-status--${statusTone(selectedSection)}`}>{selectedSection.status}</span>
              <h2>{selectedSection.label}</h2>
              <p>{selectedSection.description}</p>
            </div>
            <button type="button" onClick={resetDraft}><RotateCcw size={15} /> Reset</button>
          </header>

          <div className="ops-settings-fields">
            {selectedSection.fields.map((field) => (
              <label className={field.type === 'textarea' ? 'is-wide' : ''} key={field.key}>
                <span>{field.label}</span>
                <SettingsFieldControl field={field} value={fieldValue(draft, field)} onChange={updateField} />
              </label>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
