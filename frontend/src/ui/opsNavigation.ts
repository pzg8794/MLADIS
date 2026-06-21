import {
  BarChart3,
  Building2,
  CalendarDays,
  ClipboardList,
  CreditCard,
  LayoutDashboard,
  ReceiptText,
  Settings,
  Sparkles,
  UserCog,
  Users,
  Wrench,
  type LucideIcon,
} from 'lucide-react';

type ShortcutTone = 'blue' | 'violet' | 'teal' | 'amber' | 'rose';

interface RuntimeOpsNavItem {
  group: string;
  label: string;
  href: string;
  icon: string;
  description: string;
  tone: string;
  bg: string;
  shortcutAction: string;
  shortcutTone: ShortcutTone;
  badge?: string;
}

export interface OpsNavItem extends RuntimeOpsNavItem {
  iconComponent: LucideIcon;
}

const iconComponents: Record<string, LucideIcon> = {
  dashboard: LayoutDashboard,
  reservations: ClipboardList,
  calendar: CalendarDays,
  stays: Building2,
  maintenance: Wrench,
  payments: CreditCard,
  deposits: ReceiptText,
  reports: BarChart3,
  agent: Sparkles,
  fairagent: Sparkles,
  customers: Users,
  tasks: ClipboardList,
  settings: Settings,
  'users-admin': UserCog,
};

const fallbackOpsNavItems: RuntimeOpsNavItem[] = [
  { group: 'Overview', label: 'Command Center', href: '/ops/dashboard/', icon: 'dashboard', description: 'Command overview and live metrics', tone: '#2563eb', bg: '#dbeafe', shortcutAction: 'Open', shortcutTone: 'blue' },
  { group: 'Operations', label: 'Reservations', href: '/ops/reservations/', icon: 'reservations', description: 'Guest stays, channels, arrivals', tone: '#0ea5e9', bg: '#e0f2fe', shortcutAction: 'Manage', shortcutTone: 'teal' },
  { group: 'Operations', label: 'Calendar', href: '/ops/calendar/', icon: 'calendar', description: 'Availability, blocks, pricing', tone: '#7c3aed', bg: '#ede9fe', shortcutAction: 'Open', shortcutTone: 'teal' },
  { group: 'Operations', label: 'Guests', href: '/ops/customers/', icon: 'customers', description: 'Guest stays, channels, arrivals', tone: '#0f766e', bg: '#ccfbf1', shortcutAction: 'Manage', shortcutTone: 'blue' },
  { group: 'Operations', label: 'Maintenance', href: '/ops/maintenance/', icon: 'maintenance', description: 'Issues, photos, repair status', tone: '#f97316', bg: '#ffedd5', shortcutAction: 'View', shortcutTone: 'amber' },
  { group: 'Operations', label: 'Payments', href: '/ops/payments/', icon: 'payments', description: 'Checkout status and providers', tone: '#0891b2', bg: '#cffafe', shortcutAction: 'Open', shortcutTone: 'blue' },
  { group: 'Operations', label: 'Deposits', href: '/ops/deposits/', icon: 'deposits', description: 'Holds, captures, releases', tone: '#e11d48', bg: '#ffe4e6', shortcutAction: 'Open', shortcutTone: 'teal' },
  { group: 'Operations', label: 'Reports', href: '/ops/reports/', icon: 'reports', description: 'Revenue, occupancy, trends', tone: '#6d28d9', bg: '#f3e8ff', shortcutAction: 'View', shortcutTone: 'violet' },
  { group: 'Operations', label: 'FairAgent', href: '/ops/agent/', icon: 'fairagent', description: 'AI suggestions and training', tone: '#0d9488', bg: '#ccfbf1', shortcutAction: 'Manage', shortcutTone: 'rose' },
  { group: 'Business', label: 'Properties', href: '/ops/properties/', icon: 'stays', description: 'Properties and availability', tone: '#059669', bg: '#d1fae5', shortcutAction: 'Manage', shortcutTone: 'blue' },
  { group: 'Business', label: 'Tasks', href: '/ops/workboard/', icon: 'tasks', description: 'Assigned jobs and completion', tone: '#d97706', bg: '#fef3c7', shortcutAction: 'Open', shortcutTone: 'violet', badge: '12' },
  { group: 'Admin', label: 'Settings', href: '/ops/settings/', icon: 'settings', description: 'Public site copy and identity', tone: '#475569', bg: '#e2e8f0', shortcutAction: 'Manage', shortcutTone: 'amber' },
  { group: 'Admin', label: 'Admin', href: '/ops/admin/', icon: 'users-admin', description: 'Access, roles, operators', tone: '#1d4ed8', bg: '#dbeafe', shortcutAction: 'Manage', shortcutTone: 'violet' },
];

function isRuntimeOpsNavItem(value: unknown): value is RuntimeOpsNavItem {
  if (!value || typeof value !== 'object') return false;
  const item = value as Record<string, unknown>;
  return ['group', 'label', 'href', 'icon', 'description', 'tone', 'bg', 'shortcutAction', 'shortcutTone']
    .every((key) => typeof item[key] === 'string');
}

function readRuntimeOpsNavItems(): RuntimeOpsNavItem[] | null {
  if (typeof document === 'undefined') return null;
  const script = document.getElementById('mladis-ops-nav-items');
  if (!script?.textContent) return null;

  try {
    const parsed = JSON.parse(script.textContent) as unknown;
    if (!Array.isArray(parsed) || !parsed.every(isRuntimeOpsNavItem)) return null;
    return parsed;
  } catch {
    return null;
  }
}

export const OPS_NAV_ITEMS: OpsNavItem[] = (readRuntimeOpsNavItems() ?? fallbackOpsNavItems).map((item) => ({
  ...item,
  iconComponent: iconComponents[item.icon] ?? LayoutDashboard,
}));
