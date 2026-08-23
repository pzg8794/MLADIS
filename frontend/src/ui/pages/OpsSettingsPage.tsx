import { useEffect, useMemo, useState } from 'react';
import {
  Bell,
  Bot,
  CheckCircle2,
  ExternalLink,
  FileText,
  Globe2,
  Settings2,
  ShieldCheck,
} from 'lucide-react';
import { SettingsFactory } from '../../application/SettingsFactory';
import type { OpsSettingsSection } from '../../domain/models';
import type { SettingsWorkspace } from '../../domain/settings';
import './admin-page.css';

const SECTION_ICONS = [Globe2, FileText, Bell, ShieldCheck];
const METRIC_ICONS = [Globe2, Bell, FileText, ShieldCheck, Bot, Settings2];
const TONES = ['blue', 'green', 'violet', 'orange'] as const;

function displayValue(value: string | number | boolean) {
  if (typeof value === 'boolean') return value ? 'Enabled' : 'Disabled';
  return String(value || 'Not configured');
}

function SettingsSectionPanel({ section }: { section: OpsSettingsSection }) {
  return (
    <section className="settings-v4-panel settings-v4-panel--span-2">
      <header className="settings-v4-panel__header">
        <div>
          <h2>{section.label}</h2>
          <p>{section.description}</p>
        </div>
        <span className={`settings-v4-badge settings-v4-badge--${section.statusTone}`}>
          {section.status}
        </span>
      </header>
      <div className="settings-v4-form-grid">
        {section.fields.map((field) => (
          <div className={`settings-v4-field${field.type === 'textarea' ? ' settings-v4-field--wide' : ''}`} key={field.key}>
            <span>{field.label}</span>
            <div className="settings-v4-control settings-v4-control--readonly">
              <strong>{displayValue(field.value)}</strong>
              {typeof field.value === 'boolean' && (
                field.value
                  ? <CheckCircle2 aria-label="Enabled" size={16} />
                  : <span aria-label="Disabled">Off</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export function OpsSettingsPage() {
  const settingsService = useMemo(() => SettingsFactory.create(), []);
  const [workspace, setWorkspace] = useState<SettingsWorkspace | null>(null);
  const [activeSection, setActiveSection] = useState('');

  useEffect(() => {
    let active = true;
    settingsService.loadWorkspace().then((next) => {
      if (!active) return;
      setWorkspace(next);
      setActiveSection(next.snapshot?.sections[0]?.id ?? '');
    });
    return () => { active = false; };
  }, [settingsService]);

  const snapshot = workspace?.snapshot;
  const selected = snapshot?.sections.find((section) => section.id === activeSection);

  return (
    <main className="dashboard-content settings-v4-page">
      <section className="settings-v4-titlebar">
        <div>
          <h1>Settings</h1>
          <p>Verified public-site, guest-document, notification, and provider configuration.</p>
        </div>
        {snapshot && (
          <div className="settings-v4-titlebar__actions">
            <a className="settings-v4-side-button" href={snapshot.adminUrls.site_settings}>
              <Settings2 size={15} /> Edit authoritative settings <ExternalLink size={13} />
            </a>
          </div>
        )}
      </section>

      {snapshot ? (
        <>
          <section className="settings-v4-metric-row" aria-label="Configuration summary">
            {snapshot.summaryCards.map((metric, index) => {
              const Icon = METRIC_ICONS[index % METRIC_ICONS.length];
              return (
                <article className={`settings-v4-metric settings-v4-metric--${TONES[index % TONES.length]}`} key={metric.label}>
                  <span className={`settings-v4-icon-badge settings-v4-icon-badge--${TONES[index % TONES.length]}`}>
                    <Icon size={17} />
                  </span>
                  <div>
                    <span>{metric.label}</span>
                    <strong>{metric.value}</strong>
                    <small>{metric.caption}</small>
                  </div>
                </article>
              );
            })}
          </section>

          <nav className="settings-v4-tabs" aria-label="Settings sections">
            {snapshot.sections.map((section, index) => {
              const Icon = SECTION_ICONS[index % SECTION_ICONS.length];
              return (
                <button
                  className={section.id === activeSection ? 'is-active' : ''}
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  type="button"
                >
                  <Icon size={15} /> {section.label}
                </button>
              );
            })}
          </nav>

          <div className="settings-v4-layout" data-settings-source={workspace.source}>
            <div className="settings-v4-main settings-v4-main--dense">
              {selected && <SettingsSectionPanel section={selected} />}
            </div>
            <aside className="settings-v4-side">
              <section className="settings-v4-side-card">
                <h2>Authoritative controls</h2>
                <p>Changes are made in protected server-backed owners. Secrets are never displayed here.</p>
                <a className="settings-v4-side-link" href={snapshot.adminUrls.site_settings}>Site settings <ExternalLink size={13} /></a>
                <a className="settings-v4-side-link" href={snapshot.adminUrls.oauth}>OAuth diagnostics <ExternalLink size={13} /></a>
                <a className="settings-v4-side-link" href={snapshot.adminUrls.agent_faq}>Agent knowledge <ExternalLink size={13} /></a>
                <a className="settings-v4-side-link" href={snapshot.adminUrls.users}>Users and access <ExternalLink size={13} /></a>
              </section>
            </aside>
          </div>
        </>
      ) : (
        <section className="settings-v4-panel" role="status">
          <h2>Settings are unavailable</h2>
          <p>The settings API did not return a verified configuration snapshot.</p>
        </section>
      )}
    </main>
  );
}
