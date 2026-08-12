import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, BellRing, BookOpenCheck, ExternalLink, KeyRound, Settings2, ShieldCheck } from 'lucide-react';
import { SettingsFactory } from '../../application/SettingsFactory';
import type { SettingsWorkspace } from '../../domain/settings';

const sectionIcons = {
  brand: Settings2,
  documents: BookOpenCheck,
  notifications: BellRing,
  providers: KeyRound,
};

function displayValue(value: string | boolean | number) {
  if (typeof value === 'boolean') return value ? 'Enabled' : 'Not configured';
  const text = String(value ?? '').trim();
  return text || 'Not set';
}

export function OpsSettingsPage() {
  const service = useMemo(() => SettingsFactory.create(), []);
  const [workspace, setWorkspace] = useState<SettingsWorkspace | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    service.loadWorkspace()
      .then((nextWorkspace) => {
        if (!active) return;
        if (!nextWorkspace.snapshot) {
          setError('The persisted settings workspace is unavailable.');
          return;
        }
        setWorkspace(nextWorkspace);
      })
      .catch((caught: unknown) => {
        if (active) setError(caught instanceof Error ? caught.message : 'Could not load settings.');
      });
    return () => {
      active = false;
    };
  }, [service]);

  if (error) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!workspace?.snapshot) {
    return <main className="dashboard-content ops-page"><section className="ops-hero is-loading" /></main>;
  }

  const { snapshot } = workspace;
  const settingsAdminUrl = snapshot.adminUrls.site_settings || '/admin/bookings/sitesettings/';

  return (
    <main className="dashboard-content ops-page real-settings-page">
      <section className="ops-hero real-settings-hero">
        <div>
          <span><Settings2 size={16} /> Persisted configuration</span>
          <h2>Settings</h2>
          <p>Review the live MLADIS configuration. Changes open the persisted SiteSettings record instead of being stored only in this browser.</p>
        </div>
        <div className="ops-hero-actions">
          <a href={settingsAdminUrl}><Settings2 size={16} /> Edit persisted settings</a>
          {snapshot.adminUrls.oauth && <a href={snapshot.adminUrls.oauth}><ShieldCheck size={16} /> Provider diagnostics</a>}
        </div>
      </section>

      <section className="ops-metric-grid real-settings-metrics" aria-label="Settings summary">
        {snapshot.summaryCards.map((metric) => (
          <article key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <p>{metric.caption}</p>
          </article>
        ))}
      </section>

      <section className="real-settings-grid">
        {snapshot.sections.map((section) => {
          const Icon = sectionIcons[section.id as keyof typeof sectionIcons] ?? Settings2;
          return (
            <article className="real-settings-card" key={section.id}>
              <header>
                <span><Icon size={18} /></span>
                <div>
                  <h3>{section.label}</h3>
                  <p>{section.description}</p>
                </div>
                <em data-tone={section.statusTone}>{section.status}</em>
              </header>
              <dl>
                {section.fields.map((field) => (
                  <div key={field.key}>
                    <dt>{field.label}</dt>
                    <dd data-empty={displayValue(field.value) === 'Not set' || displayValue(field.value) === 'Not configured'}>
                      {field.type === 'textarea' ? `${String(field.value).split('\n').filter(Boolean).length} configured entries` : displayValue(field.value)}
                    </dd>
                  </div>
                ))}
              </dl>
            </article>
          );
        })}
      </section>

      <section className="real-settings-actions" aria-label="Related configuration workspaces">
        <div>
          <h3>Configuration workspaces</h3>
          <p>These links open real persisted records. Provider secrets are never exposed here.</p>
        </div>
        {snapshot.adminUrls.agent_faq && <a href={snapshot.adminUrls.agent_faq}>Agent FAQ <ExternalLink size={14} /></a>}
        {snapshot.adminUrls.users && <a href={snapshot.adminUrls.users}>Admin users <ExternalLink size={14} /></a>}
        <a href={settingsAdminUrl}>Site settings <ExternalLink size={14} /></a>
      </section>

      <footer className="real-settings-footer">Loaded from MLADIS at {new Date(snapshot.generatedAt).toLocaleString()}.</footer>
    </main>
  );
}
