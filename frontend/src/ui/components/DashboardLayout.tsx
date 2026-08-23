import { CalendarDays, ChevronDown, Menu, Plus } from 'lucide-react';
import { Fragment, ReactNode, useState } from 'react';
import { OPS_NAV_ITEMS } from '../opsNavigation';
import { getConfiguredLogoUrl } from '../helpers/brand';
import { opsTheme } from '../theme/opsTheme';

interface DashboardLayoutProps {
  children: ReactNode;
}

function isNavActive(pathname: string, href: string) {
  if (href === '/') return pathname === '/';
  const normalized = href.replace(/\/$/, '');
  return pathname === normalized || pathname.startsWith(`${normalized}/`);
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = window.location.pathname;
  const logoUrl = getConfiguredLogoUrl();
  const currentUserName = document.querySelector<HTMLMetaElement>('meta[name="mladis-ops-user-name"]')?.content || 'Operator';
  const currentUserInitials = currentUserName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || 'OP';
  const [sidebarPinned, setSidebarPinned] = useState(false);
  const [sidebarHovered, setSidebarHovered] = useState(false);
  const [sidebarFocused, setSidebarFocused] = useState(false);
  const sidebarExpanded = sidebarPinned || sidebarHovered || sidebarFocused;

  return (
    <div
      className={`dashboard-shell${sidebarExpanded ? ' is-sidebar-expanded' : ''}${sidebarPinned ? ' is-sidebar-pinned' : ''}`}
      data-theme-reference={opsTheme.referenceName}
    >
      <aside
        className={`modern-admin-sidebar v4-command-sidebar${sidebarExpanded ? ' is-expanded' : ''}`}
        onMouseEnter={() => setSidebarHovered(true)}
        onMouseLeave={() => setSidebarHovered(false)}
        onFocus={() => setSidebarFocused(true)}
        onBlur={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
            setSidebarFocused(false);
          }
        }}
      >
        <a className="modern-admin-brand" href="/">
          <img src={logoUrl} alt="MLADIS" />
          <div>
            <strong>{opsTheme.brandTitle}</strong>
            <small>{opsTheme.brandSubtitle}</small>
          </div>
        </a>
        <nav aria-label="Dashboard sections">
          {OPS_NAV_ITEMS.map((item, index) => {
            const Icon = item.iconComponent;
            const isActive = isNavActive(pathname, item.href);
            const showGroup = index === 0 || OPS_NAV_ITEMS[index - 1].group !== item.group;
            return (
              <Fragment key={item.href}>
                {showGroup && item.group && <span className="v4-nav-group">{item.group}</span>}
                <div className="v4-nav-cluster">
                <a className={isActive ? 'is-active' : ''} href={item.href}>
                  <Icon className="modern-admin-rail-icon" aria-hidden="true" size={18} />
                  <span className="modern-admin-nav-label">{item.label}</span>
                  {item.badge && <b className="v4-nav-count">{item.badge}</b>}
                </a>
                </div>
              </Fragment>
            );
          })}
        </nav>
        <div className="v4-sidebar-user">
          <span>{currentUserInitials}</span>
          <div>
            <strong>{currentUserName}</strong>
            <small>Operator</small>
          </div>
          <ChevronDown size={15} />
        </div>
      </aside>
      <div
        className="v4-sidebar-hover-zone"
        aria-hidden="true"
        onMouseEnter={() => setSidebarHovered(true)}
      />
      <div className="dashboard-main">
        <header className="dashboard-topbar v4-commandbar">
          <button
            className="v4-icon-button"
            type="button"
            aria-label={sidebarPinned ? 'Unpin menu' : 'Pin menu open'}
            onClick={() => setSidebarPinned((current) => !current)}
          >
            <Menu size={19} />
          </button>
          <div className="v4-commandbar__actions">
            <a className="v4-new-button" href="/admin/bookings/bookinginquiry/add/">
              <Plus size={17} />
              New reservation
            </a>
            <a className="v4-icon-button" href="/ops/calendar/" aria-label="Calendar"><CalendarDays size={18} /></a>
            <a className="v4-user-menu" href="/accounts/">
              <span>{currentUserInitials}</span>
              <div>
                <strong>{currentUserName}</strong>
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
