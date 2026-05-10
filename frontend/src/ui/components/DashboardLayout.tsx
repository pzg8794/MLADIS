import { Bot, CalendarDays, Home, LayoutDashboard, LineChart, ReceiptText, Users } from 'lucide-react';
import { ReactNode } from 'react';

interface DashboardLayoutProps {
  children: ReactNode;
}

const navItems = [
  { label: 'Dashboard', icon: LayoutDashboard, active: true },
  { label: 'Reservations', icon: CalendarDays },
  { label: 'Reports', icon: LineChart },
  { label: 'Customers', icon: Users },
  { label: 'Deposits', icon: ReceiptText },
  { label: 'Agent', icon: Bot },
];

export function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="dashboard-shell">
      <aside className="dashboard-sidebar glass-card">
        <div className="dashboard-brand">
          <span>M</span>
          <div>
            <strong>MLADIS</strong>
            <small>Vacation Homes</small>
          </div>
        </div>
        <nav aria-label="Dashboard sections">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button className={item.active ? 'active' : ''} key={item.label} type="button">
                <Icon size={18} />
                {item.label}
              </button>
            );
          })}
        </nav>
        <a className="back-to-site" href="/">
          <Home size={16} />
          Back to live site
        </a>
      </aside>
      <div className="dashboard-main">
        <header className="dashboard-topbar glass-card">
          <div>
            <p>Modern operations dashboard</p>
            <h1>Welcome back, Piter</h1>
          </div>
          <div className="dashboard-topbar__actions">
            <a href="/admin/">Open Django Admin</a>
            <a href="/ops/reports/">Legacy reports</a>
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}
