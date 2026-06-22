import { useEffect, useMemo, useState } from 'react';
import { ArrowRight, Box, CalendarDays, CheckCircle2, ClipboardList, Clock3, Database, DollarSign, LayoutGrid, MessageCircle, Radio, Settings, ShieldCheck, Sparkles, TrendingUp, Users, Wrench, type LucideIcon } from 'lucide-react';
import { AdminWorkspaceFactory } from '../../application/AdminWorkspaceFactory';
import type { AdminWorkspace } from '../../domain/admin';
import './admin-page.css';

const ADMIN_HERO_IMAGE = `${import.meta.env.BASE_URL}admin-command-hero.png`;

const ADMIN_ICONS: Record<string, LucideIcon> = {
  box: Box,
  calendar: CalendarDays,
  clipboard: ClipboardList,
  clock: Clock3,
  database: Database,
  dollar: DollarSign,
  message: MessageCircle,
  radio: Radio,
  settings: Settings,
  shield: ShieldCheck,
  trend: TrendingUp,
  users: Users,
  wrench: Wrench,
};

export function AdminPage() {
  const service = useMemo(() => AdminWorkspaceFactory.create(), []);
  const [workspace, setWorkspace] = useState<AdminWorkspace>(() => service.fallbackWorkspace());

  useEffect(() => {
    let active = true;
    service.loadWorkspace()
      .then((nextWorkspace) => {
        if (active) setWorkspace(nextWorkspace);
      })
      .catch(() => {
        if (active) setWorkspace(service.fallbackWorkspace());
      });
    return () => {
      active = false;
    };
  }, [service]);

  return (
    <main className="dashboard-content admin-page">
      <section className="admin-hero">
        <div>
          <h1>Admin command center <Sparkles size={28} /></h1>
          <p>Your operational cockpit for reservations, guests, properties, and everything in between.</p>
          <a href="#admin-workspaces" className="admin-primary-link">
            Open all workspaces
            <ArrowRight size={16} />
          </a>
        </div>
        <figure className="admin-hero-media">
          <img src={ADMIN_HERO_IMAGE} alt="MLADIS pool workspace" />
          <figcaption>
            <span><i /> System healthy</span>
            <span>Last sync: 2m ago</span>
            <span>All systems operational</span>
          </figcaption>
        </figure>
      </section>

      <section className="admin-body-grid">
        <div className="admin-main-stack">
          <section className="admin-metric-grid" aria-label="Admin metrics">
            {workspace.metrics.map((metric) => {
              const Icon = ADMIN_ICONS[metric.iconKey] ?? ShieldCheck;
              return (
                <article className={`admin-metric-card admin-metric-card--${metric.tone}`} key={metric.label}>
                  <span><Icon size={24} /></span>
                  <div>
                    <small>{metric.label}</small>
                    <strong>{metric.value}</strong>
                    <em>{metric.caption}</em>
                  </div>
                </article>
              );
            })}
          </section>

          <section className="admin-operations" id="admin-workspaces">
            <header className="admin-section-header">
              <div>
                <h2><ClipboardList size={22} /> Operations hub</h2>
                <p>Access the tools and data you need to run a world-class hospitality operation.</p>
              </div>
              <div className="admin-view-actions" aria-label="Workspace controls">
                <button type="button" aria-label="Grid view"><LayoutGrid size={17} /></button>
                <button type="button"><Settings size={17} /> Customize</button>
              </div>
            </header>

            <section className="admin-shortcut-grid">
              {workspace.shortcuts.map((shortcut) => {
                const Icon = ADMIN_ICONS[shortcut.iconKey] ?? Box;
                return (
                  <a className={`admin-shortcut admin-shortcut--${shortcut.tone}`} href={shortcut.href} key={shortcut.label}>
                    <span className="admin-shortcut__icon"><Icon size={23} /></span>
                    <span>
                      <strong>{shortcut.label}</strong>
                      <p>{shortcut.description}</p>
                      <small>{shortcut.action} <ArrowRight size={13} /></small>
                    </span>
                  </a>
                );
              })}
            </section>
          </section>
        </div>

        <aside className="admin-side-rail">
          <section className="admin-feed-card" aria-label="Live operations feed">
            <header>
              <h2><Radio size={16} /> Live operations feed</h2>
              <a href="/ops/reports/">View all</a>
            </header>
            <div>
              {workspace.feedItems.map((item) => {
                const Icon = ADMIN_ICONS[item.iconKey] ?? CalendarDays;
                return (
                  <article className={`admin-feed-item admin-feed-item--${item.tone}`} key={`${item.time}-${item.title}`}>
                    <time>{item.time}</time>
                    <span><Icon size={17} /></span>
                    <div>
                      <strong>{item.title}</strong>
                      <p>{item.detail}</p>
                    </div>
                  </article>
                );
              })}
            </div>
            <p><CheckCircle2 size={14} /> All activity is up to date</p>
          </section>

          <section className="admin-health-panel" aria-label="System health and access">
            <header>
              <h2>System health &amp; access</h2>
              <a href="/ops/settings/">Details</a>
            </header>
            <div>
              {workspace.healthCards.map((card) => {
                const Icon = ADMIN_ICONS[card.iconKey] ?? ShieldCheck;
                return (
                  <article className={`admin-health-tile admin-health-tile--${card.tone}`} key={card.label}>
                    <span><Icon size={18} /></span>
                    <strong>{card.label}<b>{card.value}</b></strong>
                    <em>{card.caption}</em>
                  </article>
                );
              })}
            </div>
            <article className="admin-uptime-card">
              <div>
                <strong>Uptime</strong>
                <b>99.99%</b>
                <span>30-day</span>
              </div>
              <div className="admin-uptime-chart" aria-label="30-day uptime trend">
                <svg viewBox="0 0 260 48" preserveAspectRatio="none" role="img" aria-hidden="true">
                  <defs>
                    <linearGradient id="admin-uptime-fill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#bbf7d0" stopOpacity="0.72" />
                      <stop offset="100%" stopColor="#bbf7d0" stopOpacity="0.08" />
                    </linearGradient>
                  </defs>
                  <path className="admin-uptime-chart__area" d="M0 35 C13 29 25 28 38 31 C52 36 64 27 78 28 C92 30 104 33 118 29 C132 24 145 27 158 25 C172 23 185 30 198 27 C211 24 224 26 236 22 C247 18 254 20 260 17 L260 48 L0 48 Z" />
                  <path className="admin-uptime-chart__line" d="M0 35 C13 29 25 28 38 31 C52 36 64 27 78 28 C92 30 104 33 118 29 C132 24 145 27 158 25 C172 23 185 30 198 27 C211 24 224 26 236 22 C247 18 254 20 260 17" />
                </svg>
              </div>
            </article>
          </section>
        </aside>
      </section>
    </main>
  );
}
