import { Bot, CalendarDays, Home, LayoutDashboard, LineChart, ReceiptText, Search, ShieldCheck, Sparkles, Users } from 'lucide-react';
import { ReactNode } from 'react';

interface DashboardLayoutProps {
  children: ReactNode;
}

const navItems = [
  { label: 'Dashboard', icon: LayoutDashboard, href: '/ops/dashboard/' },
  { label: 'Reservations', icon: CalendarDays, href: '/ops/reservations/' },
  { label: 'Reports', icon: LineChart, href: '/ops/reports/' },
  { label: 'Customers', icon: Users, href: '/ops/customers/' },
  { label: 'Deposits', icon: ReceiptText, href: '/ops/deposits/' },
  { label: 'Agent', icon: Bot, href: '/ops/agent/' },
];

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = window.location.pathname;
  return (
    <div className="dashboard-shell">
      <aside className="dashboard-sidebar">
        <div className="dashboard-brand">
          <span>M</span>
          <div>
            <strong>MLADIS</strong>
            <small>Stay operations</small>
          </div>
        </div>
        <nav aria-label="Dashboard sections">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname.startsWith(item.href.replace(/\/$/, ''));
            return (
              <a className={isActive ? 'active' : ''} href={item.href} key={item.label}>
                <Icon size={18} />
                {item.label}
              </a>
            );
          })}
        </nav>
        <div className="sidebar-card">
          <Sparkles size={18} />
          <strong>Modern ops mode</strong>
          <span>Django remains the source of truth for reservations, deposits, reports, and admin controls.</span>
        </div>
        <a className="back-to-site" href="/">
          <Home size={16} />
          Back to live site
        </a>
      </aside>
      <div className="dashboard-main">
        <header className="dashboard-topbar">
          <div>
            <p><ShieldCheck size={16} /> Modern operations cockpit</p>
            <h1>Welcome back, Piter</h1>
          </div>
          <label className="dashboard-search">
            <Search size={17} />
            <input aria-label="Search dashboard" placeholder="Search guests or stays" />
          </label>
          <div className="dashboard-topbar__actions">
            <a href="/admin/" aria-label="Open Django admin">Admin</a>
            <a href="/ops/reports/" aria-label="Open reports">Reports</a>
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}
