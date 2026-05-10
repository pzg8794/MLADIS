import { Activity, Bot, CalendarDays, CreditCard, Database, ExternalLink, FileText, KeyRound, ShieldCheck, Users } from 'lucide-react';

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
  new AdminShortcut('Django admin home', 'Open the protected source-of-truth admin console.', '/admin/', ShieldCheck, 'blue'),
  new AdminShortcut('Reservations', 'Review booking requests, guest notes, coupons, and confirmations.', '/admin/bookings/bookinginquiry/', CalendarDays, 'teal'),
  new AdminShortcut('Customers', 'Manage customer profiles, Airbnb imports, and marketing consent.', '/admin/bookings/customerprofile/', Users, 'violet'),
  new AdminShortcut('Damage deposits', 'Review Stripe and PayPal authorization holds.', '/admin/bookings/damagedeposit/', CreditCard, 'amber'),
  new AdminShortcut('Agent FAQs', 'Edit local FAQ answers that reduce OpenAI API spend.', '/admin/bookings/agentfaq/', Bot, 'rose'),
  new AdminShortcut('Business calendar', 'Block dates, set overrides, and audit availability.', '/admin/bookings/bookableitem/calendar/', Database, 'teal'),
  new AdminShortcut('Reports', 'Open legacy reporting while the React report section is migrated.', '/ops/reports/', FileText, 'blue'),
  new AdminShortcut('OAuth setup', 'Check Google/Airbnb-connected setup diagnostics.', '/ops/oauth/', KeyRound, 'violet'),
];

const healthItems = [
  new AdminHealthItem('Admin source of truth', 'Django protected', 'Mutations still happen in Django until React APIs are finalized.'),
  new AdminHealthItem('Booking mutations', 'Locked down', 'No React-side payment/deposit mutations in this prototype.'),
  new AdminHealthItem('Agent FAQ layer', 'Needs review', 'Confirm AgentFAQ exists in admin and can be edited.', 'review'),
  new AdminHealthItem('Static deployment', 'Build required', 'Run npm build before copying frontend assets.', 'attention'),
];

export function AdminPage() {
  return (
    <main className="dashboard-content admin-page">
      <section className="admin-hero">
        <div>
          <span><ShieldCheck size={16} /> Staff operations</span>
          <h2>Admin command center</h2>
          <p>
            A modern control layer for the Django admin tools. Keep Django as the source of truth while the new dashboard grows section by section.
          </p>
        </div>
        <a href="/admin/" className="admin-primary-link">
          Open Django admin
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
          <h3>Admin shortcuts</h3>
          <p>Jump into the exact operational area without hunting through old admin menus.</p>
        </div>
        <span><Activity size={15} /> Safe bridge mode</span>
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

      <section className="admin-checklist">
        <div>
          <h3>Before replacing the old admin experience</h3>
          <p>Use this checklist to avoid another deploy where the code changed but the live workflow did not.</p>
        </div>
        <ol>
          <li>Run the React build and verify the compiled static assets changed.</li>
          <li>Confirm /ops/admin/ loads for staff users.</li>
          <li>Confirm every shortcut opens the correct Django admin or ops page.</li>
          <li>Confirm AgentFAQ is visible/editable in Django admin.</li>
          <li>Keep payment/deposit captures inside Django admin until API permissions are designed.</li>
        </ol>
      </section>
    </main>
  );
}
