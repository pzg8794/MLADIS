import { useEffect, useMemo, useState } from 'react';
import { ArrowRight, Box, CalendarDays, ClipboardList, Clock3, Database, DollarSign, MessageCircle, Radio, Settings, ShieldCheck, Sparkles, TrendingUp, Users, Wrench, type LucideIcon } from 'lucide-react';
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
            <span><i /> Live admin records</span>
            <span>{workspace.source === 'api' ? 'Connected to MLADIS' : 'Admin data unavailable'}</span>
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
              <a className="admin-primary-link" href="/admin/"><Settings size={17} /> Django admin</a>
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

      </section>
    </main>
  );
}
