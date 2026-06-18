import { Activity, Bell, Bot, Building2, CalendarDays, ClipboardList, CreditCard, Database, ExternalLink, FileText, Grid3X3, Home, Settings, ShieldCheck, SlidersHorizontal, Users, Wrench } from 'lucide-react';
import './admin-page.css';

class AdminShortcut {
  constructor(
    public readonly label: string,
    public readonly description: string,
    public readonly href: string,
    public readonly icon: typeof ShieldCheck,
    public readonly action: string,
    public readonly tone: 'blue' | 'violet' | 'teal' | 'amber' | 'rose' = 'blue',
  ) {}
}

class AdminMetric {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly caption: string,
    public readonly icon: typeof ShieldCheck,
    public readonly tone: 'blue' | 'violet' | 'teal' | 'amber' | 'rose' = 'blue',
  ) {}
}

const shortcuts = [
  new AdminShortcut('Records', 'Master data, settings, and system records.', '/admin/', Database, 'Open', 'blue'),
  new AdminShortcut('Reservations', 'Manage bookings, requests, and confirmations.', '/ops/reservations/', CalendarDays, 'Manage', 'teal'),
  new AdminShortcut('Guests / Customers', 'Profiles, communications, and guest history.', '/ops/customers/', Users, 'View', 'violet'),
  new AdminShortcut('Properties', 'Inventory, details, photos, and configurations.', '/ops/stays/', Building2, 'Manage', 'blue'),
  new AdminShortcut('Calendar', 'Availability, pricing, blocks, and overrides.', '/ops/calendar/', CalendarDays, 'Open', 'teal'),
  new AdminShortcut('Maintenance', 'Issues, inspections, and preventive maintenance.', '/ops/maintenance/', Wrench, 'View', 'amber'),
  new AdminShortcut('Work Orders', 'Task assignments, status, and completion.', '/ops/workboard/', ClipboardList, 'Open', 'violet'),
  new AdminShortcut('Payments', 'Transactions, refunds, and reconciliation.', '/ops/deposits/', CreditCard, 'Open', 'blue'),
  new AdminShortcut('Deposits', 'Holds, releases, and deposit management.', '/ops/deposits/', ShieldCheck, 'Open', 'teal'),
  new AdminShortcut('Reports', 'Operational charts, KPIs, and exports.', '/ops/reports/', FileText, 'View', 'violet'),
  new AdminShortcut('FairAgent', 'Question analytics and FAQ training controls.', '/ops/agent/', Bot, 'Open', 'rose'),
  new AdminShortcut('Settings', 'Brand settings, access, and system controls.', '/ops/settings/', Settings, 'Open', 'amber'),
];

const metrics = [
  new AdminMetric('Active stays', '128', '↑ 12% vs yesterday', Home, 'teal'),
  new AdminMetric('Pending requests', '23', '↑ 5 new', Bell, 'blue'),
  new AdminMetric('Deposit holds', '$74,560', 'Protected ledger', CreditCard, 'violet'),
  new AdminMetric('Open tasks', '18', '↓ 3 completed', ClipboardList, 'amber'),
];

export function AdminPage() {
  return (
    <main className="dashboard-content admin-page">
      <section className="admin-hero">
        <div>
          <h1>Admin command center <ShieldCheck size={30} /></h1>
          <p>Your operational cockpit for reservations, guests, properties, payments, maintenance, and everything in between.</p>
          <a href="#admin-workspaces" className="admin-primary-link">
            Open all workspaces
            <ExternalLink size={16} />
          </a>
        </div>
        <aside className="admin-sync-card" aria-label="System status">
          <span>System healthy</span>
          <strong>Last sync: 2m ago</strong>
          <p>All systems operational</p>
        </aside>
      </section>

      <section className="admin-metric-grid" aria-label="Admin metrics">
        {metrics.map((metric) => {
          const Icon = metric.icon;
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
            <h2><Activity size={22} /> Operations hub</h2>
            <p>Access the tools and data you need to run a world-class hospitality operation.</p>
          </div>
          <div className="admin-view-actions" aria-label="Workspace controls">
            <button type="button" aria-label="Grid view"><Grid3X3 size={17} /></button>
            <button type="button"><SlidersHorizontal size={17} /> Customize</button>
          </div>
        </header>

        <section className="admin-shortcut-grid">
          {shortcuts.map((shortcut) => {
            const Icon = shortcut.icon;
            return (
              <a className={`admin-shortcut admin-shortcut--${shortcut.tone}`} href={shortcut.href} key={shortcut.label}>
                <span className="admin-shortcut__icon"><Icon size={22} /></span>
                <span>
                  <strong>{shortcut.label}</strong>
                  <p>{shortcut.description}</p>
                  <small>{shortcut.action} <ExternalLink size={13} /></small>
                </span>
              </a>
            );
          })}
        </section>
      </section>

      <section className="admin-footer-strip" aria-label="Admin safeguards">
        <article>
          <ShieldCheck size={18} />
          <span>Staff only</span>
          <p>Protected tools stay behind authenticated staff sessions.</p>
        </article>
        <article>
          <CreditCard size={18} />
          <span>Payment controlled</span>
          <p>Payment and deposit changes stay server-side.</p>
        </article>
        <article>
          <Bot size={18} />
          <span>Agent review</span>
          <p>FAQ training records remain editable by staff.</p>
        </article>
      </section>
    </main>
  );
}
