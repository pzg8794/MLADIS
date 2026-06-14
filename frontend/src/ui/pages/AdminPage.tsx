import { Activity, Bot, CalendarDays, CreditCard, Database, ExternalLink, FileText, KeyRound, Settings, ShieldCheck, Users } from 'lucide-react';
import './admin-page.css';

class AdminShortcut {
  constructor(
    public readonly label: string,
    public readonly description: string,
    public readonly href: string,
    public readonly icon: typeof ShieldCheck,
    public readonly tone: 'blue' | 'violet' | 'teal' | 'amber' | 'rose' = 'blue',
  ) {}
}

class AdminHealthItem {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly caption: string,
    public readonly status: 'healthy' | 'review' | 'attention' = 'healthy',
  ) {}
}

const shortcuts = [
  new AdminShortcut('Records', 'Protected database edits and advanced configuration.', '/admin/', ShieldCheck, 'blue'),
  new AdminShortcut('Brand settings', 'Logo, public name, contacts, and booking copy.', '/admin/bookings/sitesettings/1/change/', Settings, 'violet'),
  new AdminShortcut('Reservations', 'Requests, guest notes, coupons, and confirmations.', '/ops/reservations/', CalendarDays, 'teal'),
  new AdminShortcut('Customers', 'Profiles, Airbnb imports, feedback, and consent.', '/ops/customers/', Users, 'violet'),
  new AdminShortcut('Deposits', 'Stripe and PayPal authorization holds.', '/ops/deposits/', CreditCard, 'amber'),
  new AdminShortcut('Agent', 'FAQ answers and customer-question training.', '/ops/agent/', Bot, 'rose'),
  new AdminShortcut('Calendar', 'Blocks, pricing overrides, and availability audit.', '/ops/calendar/', Database, 'teal'),
  new AdminShortcut('Reports', 'Operational charts and daily business signals.', '/ops/reports/', FileText, 'blue'),
  new AdminShortcut('OAuth setup', 'Provider callbacks and sign-in diagnostics.', '/ops/oauth/', KeyRound, 'violet'),
];

const healthItems = [
  new AdminHealthItem('Access', 'Staff only', 'Protected tools stay behind authenticated staff sessions.'),
  new AdminHealthItem('Payments', 'Controlled', 'Payment and deposit changes stay server-side.'),
  new AdminHealthItem('Agent FAQ', 'Review', 'FAQ training records should remain editable by staff.', 'review'),
  new AdminHealthItem('Frontend', 'Build gated', 'Preview assets require a clean Vite build before release.', 'attention'),
];

export function AdminPage() {
  return (
    <main className="dashboard-content admin-page">
      <section className="admin-hero">
        <div>
          <span><ShieldCheck size={16} /> Staff workspace</span>
          <h2>Admin command center</h2>
          <p>Control records, reservations, brand settings, reports, agent training, and booking operations from one clean surface.</p>
        </div>
        <a href="/admin/" className="admin-primary-link">
          Open records
          <ExternalLink size={16} />
        </a>
      </section>

      <section className="admin-health-grid" aria-label="Admin readiness">
        {healthItems.map((item) => (
          <article className={`admin-health-card admin-health-card--${item.status}`} key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
            <p>{item.caption}</p>
          </article>
        ))}
      </section>

      <section className="admin-section-header">
        <div>
          <h3>Control groups</h3>
          <p>Jump directly into the workspace that owns the task.</p>
        </div>
        <span><Activity size={15} /> Controlled edits</span>
      </section>

      <section className="admin-shortcut-grid">
        {shortcuts.map((shortcut) => {
          const Icon = shortcut.icon;
          return (
            <a className={`admin-shortcut admin-shortcut--${shortcut.tone}`} href={shortcut.href} key={shortcut.label}>
              <span className="admin-shortcut__icon"><Icon size={20} /></span>
              <strong>{shortcut.label}</strong>
              <p>{shortcut.description}</p>
              <small>Open <ExternalLink size={13} /></small>
            </a>
          );
        })}
      </section>
    </main>
  );
}
