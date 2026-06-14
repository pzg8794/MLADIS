import {
  BarChart3,
  Bell,
  Building2,
  CalendarDays,
  ChevronDown,
  ClipboardList,
  CreditCard,
  LayoutDashboard,
  ListChecks,
  Menu,
  Plus,
  ReceiptText,
  Search,
  Settings,
  Users,
  Wrench,
  Sparkles,
  UserCog,
} from 'lucide-react';
import { ReactNode, useState } from 'react';
import { getConfiguredLogoUrl } from '../helpers/brand';
import { opsTheme } from '../theme/opsTheme';

interface DashboardLayoutProps {
  children: ReactNode;
}

const navItems = [
  { group: '', label: 'Command Center', icon: LayoutDashboard, href: '/ops/dashboard/' },
  { group: 'Operations', label: 'Reservations', icon: ClipboardList, href: '/ops/reservations/' },
  { group: 'Operations', label: 'Calendar', icon: CalendarDays, href: '/ops/calendar/' },
  { group: 'Operations', label: 'Guests', icon: Users, href: '/ops/customers/' },
  { group: 'Operations', label: 'Properties', icon: Building2, href: '/ops/stays/' },
  { group: 'Operations', label: 'Maintenance', icon: Wrench, href: '/ops/maintenance/' },
  { group: 'Operations', label: 'Work Orders', icon: Wrench, href: '/ops/maintenance/' },
  { group: 'Operations', label: 'Payments', icon: CreditCard, href: '/ops/deposits/' },
  { group: 'Operations', label: 'Deposits', icon: ReceiptText, href: '/ops/deposits/' },
  { group: 'Operations', label: 'Reports', icon: BarChart3, href: '/ops/reports/' },
  { group: 'Operations', label: 'FairAgent', icon: Sparkles, href: '/ops/agent/' },
  { group: 'Business', label: 'Listings', icon: Building2, href: '/ops/stays/' },
  { group: 'Business', label: 'Customers', icon: Users, href: '/ops/customers/' },
  { group: 'Business', label: 'Tasks', icon: ListChecks, href: '/ops/workboard/' },
  { group: 'Admin', label: 'Settings', icon: Settings, href: '/ops/settings/' },
  { group: 'Admin', label: 'Users', icon: UserCog, href: '/ops/admin/' },
];

function isNavActive(pathname: string, href: string) {
  if (href === '/') return pathname === '/';
  const normalized = href.replace(/\/$/, '');
  return pathname === normalized || pathname.startsWith(`${normalized}/`);
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = window.location.pathname;
  const logoUrl = getConfiguredLogoUrl();
  const [sidebarExpanded, setSidebarExpanded] = useState(true);
  let previousGroup = '';

  return (
    <div
      className={`dashboard-shell${sidebarExpanded ? ' is-sidebar-expanded' : ''}`}
      data-theme-reference={opsTheme.referenceName}
    >
      <aside className={`modern-admin-sidebar v4-command-sidebar${sidebarExpanded ? ' is-expanded' : ''}`}>
        <a className="modern-admin-brand" href="/">
          <img src={logoUrl} alt="MLADIS" />
          <div>
            <strong>{opsTheme.brandTitle}</strong>
            <small>{opsTheme.brandSubtitle}</small>
          </div>
        </a>
        <nav aria-label="Dashboard sections">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = isNavActive(pathname, item.href);
            const showGroup = previousGroup !== item.group;
            previousGroup = item.group;
            return (
              <div className="v4-nav-cluster" key={`${item.group}-${item.label}`}>
                {showGroup && item.group && <span className="v4-nav-group">{item.group}</span>}
                <a className={isActive ? 'is-active' : ''} href={item.href}>
                  <Icon className="modern-admin-rail-icon" aria-hidden="true" size={18} />
                  <span className="modern-admin-nav-label">{item.label}</span>
                  {item.label === 'Tasks' && <b className="v4-nav-count">12</b>}
                </a>
              </div>
            );
          })}
        </nav>
        <div className="v4-sidebar-user">
          <span>PG</span>
          <div>
            <strong>Piter Garcia</strong>
            <small>Operator</small>
          </div>
          <ChevronDown size={15} />
        </div>
      </aside>
      <div className="dashboard-main">
        <header className="dashboard-topbar v4-commandbar">
          <button
            className="v4-icon-button"
            type="button"
            aria-label={sidebarExpanded ? 'Collapse menu' : 'Expand menu'}
            aria-expanded={sidebarExpanded}
            onClick={() => setSidebarExpanded((current) => !current)}
          >
            <Menu size={19} />
          </button>
          <label className="dashboard-search v4-command-search">
            <Search size={17} />
            <input aria-label="Search dashboard" placeholder="Search reservations, guests, properties..." />
            <kbd>⌘ K</kbd>
          </label>
          <div className="v4-commandbar__actions">
            <a className="v4-new-button" href="/ops/reservations/">
              <Plus size={17} />
              New
              <ChevronDown size={15} />
            </a>
            <button className="v4-icon-button has-badge" type="button" aria-label="Notifications"><Bell size={18} /><span>8</span></button>
            <a className="v4-icon-button" href="/ops/calendar/" aria-label="Calendar"><CalendarDays size={18} /></a>
            <a className="v4-user-menu" href="/accounts/">
              <span>PG</span>
              <div>
                <strong>Piter Garcia</strong>
                <small>Operator</small>
              </div>
              <ChevronDown size={15} />
            </a>
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}
