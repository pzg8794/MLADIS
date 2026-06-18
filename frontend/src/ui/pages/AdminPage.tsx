import { Activity, Bell, Bot, Box, Building2, CalendarDays, CheckCircle2, ClipboardList, Clock3, CreditCard, Database, ExternalLink, FileText, Settings, ShieldCheck, SlidersHorizontal, Sparkles, Users, Wifi, Wrench } from 'lucide-react';
import './admin-page.css';

const ADMIN_HERO_IMAGE = '/static/frontend/modern-dashboard/stays/stay-6br.jpg';

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

class AdminFeedItem {
  constructor(
    public readonly time: string,
    public readonly title: string,
    public readonly detail: string,
    public readonly icon: typeof ShieldCheck,
    public readonly tone: 'blue' | 'green' | 'amber' | 'cyan',
  ) {}
}

class AdminHealthCard {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly caption: string,
    public readonly icon: typeof ShieldCheck,
    public readonly tone: 'blue' | 'green' | 'teal' | 'slate',
  ) {}
}

class AdminUptimeSample {
  constructor(public readonly level: 'low' | 'base' | 'mid' | 'high' | 'peak') {}
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
  new AdminShortcut('Brand Settings', 'Logo, contacts, policies, and brand assets.', '/ops/settings/', Settings, 'Manage', 'amber'),
  new AdminShortcut('Agent FAQ', 'Guest and AI training, answers, and resources.', '/ops/agent/', Bot, 'Manage', 'rose'),
];

const metrics = [
  new AdminMetric('Active stays', '128', '↑ 12% vs yesterday', Box, 'violet'),
  new AdminMetric('Pending requests', '23', '↑ 5 new', Clock3, 'amber'),
  new AdminMetric('Deposit holds', '$74,560', '12 holds', ShieldCheck, 'teal'),
  new AdminMetric('Open tasks', '18', '↓ 3 completed', ClipboardList, 'blue'),
];

const feedItems = [
  new AdminFeedItem('2m ago', 'New reservation created', '#R-58291 · Ocean View Villa · Aug 12 - 16', CalendarDays, 'blue'),
  new AdminFeedItem('7m ago', 'Deposit captured', '$2,450.00 · #R-58288 · Beach House', ShieldCheck, 'green'),
  new AdminFeedItem('16m ago', 'Maintenance issue reported', 'AC not cooling · Unit 3B · High priority', Wrench, 'amber'),
  new AdminFeedItem('28m ago', 'Guest message received', 'Late check-in request · #R-58285', Bell, 'cyan'),
  new AdminFeedItem('35m ago', 'Payment refunded', '$125.00 · #R-58262 · Cancellation', CreditCard, 'green'),
];

const healthCards = [
  new AdminHealthCard('Staff access', 'Staff only', 'Protected', Users, 'slate'),
  new AdminHealthCard('Controlled edits', 'Enabled', 'Audit on', Wifi, 'green'),
  new AdminHealthCard('Build status', 'Production', 'v2.4.17', Database, 'blue'),
  new AdminHealthCard('Last backup', 'Today, 3:14 AM', 'Automated', Database, 'teal'),
];

const uptimeSamples = [
  new AdminUptimeSample('base'),
  new AdminUptimeSample('mid'),
  new AdminUptimeSample('base'),
  new AdminUptimeSample('high'),
  new AdminUptimeSample('low'),
  new AdminUptimeSample('mid'),
  new AdminUptimeSample('base'),
  new AdminUptimeSample('low'),
  new AdminUptimeSample('mid'),
  new AdminUptimeSample('base'),
  new AdminUptimeSample('high'),
  new AdminUptimeSample('peak'),
  new AdminUptimeSample('high'),
  new AdminUptimeSample('mid'),
  new AdminUptimeSample('high'),
  new AdminUptimeSample('mid'),
  new AdminUptimeSample('peak'),
  new AdminUptimeSample('base'),
  new AdminUptimeSample('high'),
  new AdminUptimeSample('peak'),
  new AdminUptimeSample('high'),
  new AdminUptimeSample('peak'),
];

export function AdminPage() {
  return (
    <main className="dashboard-content admin-page">
      <section className="admin-hero">
        <div>
          <h1>Admin command center <Sparkles size={28} /></h1>
          <p>Your operational cockpit for reservations, guests, properties, payments, maintenance, and everything in between.</p>
          <a href="#admin-workspaces" className="admin-primary-link">
            Open all workspaces
            <ExternalLink size={16} />
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
                <h2><Settings size={22} /> Operations hub</h2>
                <p>Access the tools and data you need to run a world-class hospitality operation.</p>
              </div>
              <div className="admin-view-actions" aria-label="Workspace controls">
                <button type="button" aria-label="Grid view"><SlidersHorizontal size={17} /></button>
                <button type="button"><Settings size={17} /> Customize</button>
              </div>
            </header>

            <section className="admin-shortcut-grid">
              {shortcuts.map((shortcut) => {
                const Icon = shortcut.icon;
                return (
                  <a className={`admin-shortcut admin-shortcut--${shortcut.tone}`} href={shortcut.href} key={shortcut.label}>
                    <span className="admin-shortcut__icon"><Icon size={23} /></span>
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
        </div>

        <aside className="admin-side-rail">
          <section className="admin-feed-card" aria-label="Live operations feed">
            <header>
              <h2><Activity size={16} /> Live operations feed</h2>
              <a href="/ops/reports/">View all</a>
            </header>
            <div>
              {feedItems.map((item) => {
                const Icon = item.icon;
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
              {healthCards.map((card) => {
                const Icon = card.icon;
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
                {uptimeSamples.map((sample, index) => <i className={`admin-uptime-chart__bar admin-uptime-chart__bar--${sample.level}`} key={`${sample.level}-${index}`} />)}
              </div>
            </article>
          </section>
        </aside>
      </section>
    </main>
  );
}
