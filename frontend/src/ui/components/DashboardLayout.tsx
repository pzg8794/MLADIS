import {
  BarChart3,
  Bot,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  LayoutDashboard,
  ReceiptText,
  Search,
  Settings,
  ShieldCheck,
  Users,
  Wrench,
} from 'lucide-react';
import { FocusEvent, ReactNode, useState } from 'react';
import { getConfiguredLogoUrl } from '../helpers/brand';

interface DashboardLayoutProps {
  children: ReactNode;
}

const navItems = [
  { label: 'Dashboard', icon: LayoutDashboard, href: '/ops/dashboard/' },
  { label: 'Admin', icon: ShieldCheck, href: '/admin/' },
  { label: 'Brand settings', icon: Settings, href: '/admin/bookings/sitesettings/1/change/' },
  { label: 'Reservations', icon: CalendarDays, href: '/ops/reservations/' },
  { label: 'Calendar', icon: CalendarDays, href: '/ops/calendar/' },
  { label: 'Stay portfolio', icon: Building2, href: '/ops/stays/' },
  { label: 'Reports', icon: BarChart3, href: '/ops/reports/' },
  { label: 'Customers', icon: Users, href: '/ops/customers/' },
  { label: 'Deposits', icon: ReceiptText, href: '/ops/deposits/' },
  { label: 'Maintenance', icon: Wrench, href: '/ops/maintenance/' },
  { label: 'Agent', icon: Bot, href: '/ops/agent/' },
];

function isNavActive(pathname: string, href: string) {
  if (href === '/') return pathname === '/';
  const normalized = href.replace(/\/$/, '');
  return pathname === normalized || pathname.startsWith(`${normalized}/`);
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = window.location.pathname;
  const showTopbar = pathname.startsWith('/ops/admin');
  const [railExpanded, setRailExpanded] = useState(false);
  const logoUrl = getConfiguredLogoUrl();

  function handleRailBlur(event: FocusEvent<HTMLElement>) {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
      setRailExpanded(false);
    }
  }

  return (
    <div className="dashboard-shell">
      <aside
        className={`modern-admin-sidebar${railExpanded ? ' is-expanded' : ''}`}
        onBlur={handleRailBlur}
        onClick={() => setRailExpanded(true)}
        onFocus={() => setRailExpanded(true)}
        onMouseEnter={() => setRailExpanded(true)}
        onMouseMove={() => setRailExpanded(true)}
        onMouseLeave={() => setRailExpanded(false)}
        onPointerEnter={() => setRailExpanded(true)}
        onPointerMove={() => setRailExpanded(true)}
      >
        <a className="modern-admin-brand" href="/">
          <img src={logoUrl} alt="MLADIS" />
          <div>
            <strong>MLADIS</strong>
            <small>Stay operations</small>
          </div>
        </a>
        <nav aria-label="Dashboard sections">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = isNavActive(pathname, item.href);
            return (
              <a className={isActive ? 'is-active' : ''} href={item.href} key={item.label}>
                <Icon className="modern-admin-rail-icon" aria-hidden="true" size={18} />
                <span className="modern-admin-nav-label">{item.label}</span>
              </a>
            );
          })}
        </nav>
        <div className="modern-admin-sidecard">
          <span>Protected controls</span>
          <p>Sensitive edits, payments, calendar records, and publishing controls stay permissioned.</p>
        </div>
        <a className="modern-admin-back" href="/business/">
          <BriefcaseBusiness className="modern-admin-rail-icon" aria-hidden="true" size={18} />
          <span className="modern-admin-nav-label">Business profile</span>
        </a>
      </aside>
      <div className="dashboard-main">
        {showTopbar && (
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
              <a href="/admin/" aria-label="Open admin">Admin</a>
              <a href="/ops/reports/" aria-label="Open reports">Reports</a>
            </div>
          </header>
        )}
        {children}
      </div>
    </div>
  );
}
