import {
  Bell,
  BookOpen,
  Bot,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronRight,
  CircleDollarSign,
  Clock,
  Cloud,
  Copy,
  CreditCard,
  Database,
  Download,
  ExternalLink,
  FileText,
  Folder,
  Globe2,
  Home,
  Info,
  KeyRound,
  Link2,
  ListChecks,
  LockKeyhole,
  Mail,
  MessageSquare,
  MoreVertical,
  Palette,
  PlugZap,
  Plus,
  RotateCcw,
  Send,
  Server,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Upload,
  Users,
  Wallet,
  Webhook,
  Workflow,
  Wrench,
  type LucideIcon,
} from 'lucide-react';
import { useEffect, useState, type CSSProperties, type ReactNode } from 'react';
import { getConfiguredLogoUrl } from '../helpers/brand';
import './admin-page.css';

type Tone = 'blue' | 'cyan' | 'green' | 'orange' | 'violet' | 'rose' | 'slate';
type SettingsSectionId =
  | 'business'
  | 'branding'
  | 'booking'
  | 'finance'
  | 'notifications'
  | 'ai'
  | 'knowledge'
  | 'access'
  | 'integrations';

type FieldVariant = 'input' | 'number' | 'email' | 'tel' | 'url' | 'select' | 'textarea';

type SettingsDraft = {
  business: {
    businessName: string;
    legalEntityName: string;
    country: string;
    timeZone: string;
    defaultLanguage: string;
    email: string;
    phone: string;
    address: string;
  };
  brand: {
    displayName: string;
    publicTitle: string;
    tagline: string;
    primaryColor: string;
    accentColor: string;
    logoEnabled: boolean;
    faviconEnabled: boolean;
  };
  booking: {
    defaultChannel: string;
    pricingCurrency: string;
    stayLength: string;
    checkIn: string;
    checkOut: string;
    dateFormat: string;
    numberFormat: string;
    multiProperty: boolean;
    directBooking: boolean;
    maintenanceModule: boolean;
    guestVerification: boolean;
  };
  finance: {
    depositRequired: boolean;
    depositType: string;
    depositAmount: string;
    holdDuration: string;
    releaseOn: string;
    autoHold: boolean;
    requireCard: boolean;
    paymentMethod: string;
    currencies: string[];
    taxRate: string;
    serviceFee: string;
    roundingRule: string;
  };
  notifications: {
    emailEnabled: boolean;
    smsEnabled: boolean;
    whatsappEnabled: boolean;
    adminEmail: string;
    requestTemplate: string;
    testPrefix: boolean;
  };
  ai: {
    requireAccount: boolean;
    questionLimit: string;
    modelMode: string;
    faqReview: boolean;
    dataLakeLogging: boolean;
  };
  knowledge: {
    sourceMode: string;
    publicFaqNotes: string;
    maintenancePrompt: string;
    bookingRules: string;
  };
  access: {
    ownerOnlyTasks: boolean;
    staffCanExport: boolean;
    agentAdminEnabled: boolean;
    dianaOpsAccess: boolean;
  };
  integrations: {
    googleOAuth: boolean;
    facebookOAuth: boolean;
    githubOAuth: boolean;
    stripeMode: string;
    airbnbIcal: string;
    googleCalendar: boolean;
    webhookUrl: string;
  };
};

type RuntimeState = {
  fields: Record<string, string>;
  toggles: Record<string, boolean>;
  checks: Record<string, boolean>;
};

type SettingsTabProps = {
  settings: SettingsDraft;
  runtime: RuntimeState;
  updateSection: <K extends keyof SettingsDraft>(section: K, patch: Partial<SettingsDraft[K]>) => void;
  updateField: (key: string, value: string) => void;
  updateToggle: (key: string, active: boolean) => void;
  updateCheck: (key: string, checked: boolean) => void;
  runAction: (message: string) => void;
};

class SettingsTab {
  constructor(
    public readonly id: SettingsSectionId,
    public readonly label: string,
    public readonly icon: LucideIcon,
  ) {}
}

class HealthItem {
  constructor(
    public readonly label: string,
    public readonly icon: LucideIcon,
    public readonly value = 'Operational',
  ) {}
}

class UsageItem {
  constructor(
    public readonly label: string,
    public readonly caption: string,
    public readonly value: string,
    public readonly progress: number,
    public readonly icon: LucideIcon,
  ) {}
}

class ChangeItem {
  constructor(
    public readonly title: string,
    public readonly owner: string,
    public readonly time: string,
    public readonly tone: Tone,
    public readonly icon: LucideIcon,
  ) {}
}

const SETTINGS_STORAGE_KEY = 'mladis.settings.v4.draft';
const SETTINGS_RUNTIME_KEY = 'mladis.settings.v4.runtime';
const SETTINGS_BACKUP_KEY = 'mladis.settings.v4.backup';

const tabs = [
  new SettingsTab('business', 'Business Profile', BriefcaseBusiness),
  new SettingsTab('branding', 'Branding', Palette),
  new SettingsTab('booking', 'Booking Defaults', CalendarDays),
  new SettingsTab('finance', 'Finance & Deposits', CreditCard),
  new SettingsTab('notifications', 'Notifications', Bell),
  new SettingsTab('ai', 'FairAgent / AI', Bot),
  new SettingsTab('knowledge', 'Knowledge Base', BookOpen),
  new SettingsTab('access', 'Roles & Access', Users),
  new SettingsTab('integrations', 'Integrations', PlugZap),
];

const defaultSettings: SettingsDraft = {
  business: {
    businessName: 'MLADIS Property Management',
    legalEntityName: 'MLADIS LLC',
    country: 'Dominican Republic',
    timeZone: '(UTC-04:00) America/Santo Domingo',
    defaultLanguage: 'English',
    email: 'hello@mladis.com',
    phone: '+1 (809) 555-0198',
    address: 'Avenida Anacaona 123, Suite 401\nSanto Domingo, DN 10110, Dominican Republic',
  },
  brand: {
    displayName: 'MLADIS',
    publicTitle: 'Vacation stays in Santo Domingo Norte',
    tagline: 'Pool-ready apartments near Colinas del Arroyo II, Jacobo Majluta, malls, restaurants, and the Embassy corridor.',
    primaryColor: '#0D47A1',
    accentColor: '#00B894',
    logoEnabled: true,
    faviconEnabled: true,
  },
  booking: {
    defaultChannel: 'Direct Booking',
    pricingCurrency: 'USD - US Dollar',
    stayLength: '2',
    checkIn: '03:00 PM',
    checkOut: '11:00 AM',
    dateFormat: 'Jun 19, 2026',
    numberFormat: '1,234.56',
    multiProperty: true,
    directBooking: true,
    maintenanceModule: true,
    guestVerification: true,
  },
  finance: {
    depositRequired: true,
    depositType: 'Fixed amount',
    depositAmount: '20',
    holdDuration: '24',
    releaseOn: 'Check-out',
    autoHold: true,
    requireCard: true,
    paymentMethod: 'Credit Card',
    currencies: ['USD', 'EUR', 'DOP'],
    taxRate: '18',
    serviceFee: '4.00',
    roundingRule: 'Round to nearest $0.01',
  },
  notifications: {
    emailEnabled: true,
    smsEnabled: true,
    whatsappEnabled: true,
    adminEmail: 'piter@mladis.com',
    requestTemplate: 'Send admins a concise reservation summary with guest, stay, dates, guests, quote, deposit status, and request id.',
    testPrefix: true,
  },
  ai: {
    requireAccount: true,
    questionLimit: '5',
    modelMode: 'GPT-4o (Recommended)',
    faqReview: true,
    dataLakeLogging: true,
  },
  knowledge: {
    sourceMode: 'Published FAQ + admin notes',
    publicFaqNotes: 'Check-in is 3:00 PM, check-out is 11:00 AM. Pool is shared. Direct marketing requires opt-in.',
    maintenancePrompt: 'Summarize title, cost, time, listing or reservation link, pictures, work type, and tax-ready description.',
    bookingRules: 'No parties. No smoking inside. Registered guests only unless approved. Deposit hold required before confirmation.',
  },
  access: {
    ownerOnlyTasks: true,
    staffCanExport: false,
    agentAdminEnabled: true,
    dianaOpsAccess: true,
  },
  integrations: {
    googleOAuth: true,
    facebookOAuth: false,
    githubOAuth: true,
    stripeMode: 'Test mode locally, live mode in production',
    airbnbIcal: 'Synced 2 mins ago',
    googleCalendar: true,
    webhookUrl: 'https://mladis.com/webhooks/ops/',
  },
};

const defaultRuntime: RuntimeState = {
  fields: {
    secondaryColor: '#0B2545',
    neutralColor: '#F4F6F8',
    headingFont: 'Poppins',
    bodyFont: 'Inter',
    minimumStay: '2',
    maximumStay: '30',
    advanceNotice: '12',
    freeCancelDays: '7',
    partialRefundDays: '14',
    noRefundAfter: '30',
    defaultMaxGuests: '4',
    maxAdults: '4',
    maxChildren: '2',
    extraGuestFee: '$25',
    cleaningTime: '2',
    bufferBefore: '1',
    bufferAfter: '1',
    highSeasonTag: 'High Season',
    lowSeasonTag: 'Low season tag',
    fullRefundUntil: '7',
    partialRefundUntil: '1',
    minimumPayout: '100.00',
    payoutFrequency: 'Weekly',
    payoutDay: 'Monday',
    authorizationHoldDays: '7',
    captureWindow: '2 days before check-in',
    invoicePrefix: 'INV-',
    nextInvoiceNumber: '1001',
    invoiceDateFormat: 'YYYY-MM-DD',
    paidStamp: 'On invoices',
    creditCardSurcharge: '2.90',
    exportFormat: 'CSV',
    exportDateRange: 'This Month',
    exportTimezone: '(UTC-04:00) America/Santo Domingo',
    quietStart: '10:00 PM',
    quietEnd: '07:00 AM',
    quietTimezone: '(UTC-04:00) America/Santo Domingo',
    quietChannels: 'All channels',
    agentName: 'FairAgent',
    agentLanguage: 'English',
    aiProvider: 'OpenAI',
    aiModel: 'GPT-4o (Recommended)',
    monthlyBudget: '5,000',
    alertThreshold: '80%',
    hardLimitAction: 'Pause responses',
    confidenceThreshold: '60%',
    escalationTarget: 'Human team (Live agent)',
    tonePreset: 'Professional & Friendly',
    customInstructions: 'Be helpful, concise, and empathetic. Promote direct bookings and upsell add-ons when relevant.',
    minConfidence: '65%',
    fallbackBehavior: 'Ask a clarifying question',
    maxResponseLength: 'Medium',
    faqApprover: 'Knowledge Manager',
    reviewEvery: '90 days',
    inviteName: '',
    inviteEmail: '',
    inviteRole: 'Operator',
    selectedRole: 'Operator',
    auditDateRange: 'Jun 6, 2026 - Jun 12, 2026',
    auditUser: 'All users',
    auditAction: 'All actions',
    passwordLength: '10',
    sessionTimeout: '60',
    apiEnvironment: 'Production',
    webhookReservationUrl: 'https://example.com/webhook/reservations',
    webhookPaymentUrl: 'https://example.com/webhook/payments',
    webhookGuestUrl: 'https://example.com/webhook/guests',
  },
  toggles: {
    darkLogoEnabled: true,
    sameDayBooking: true,
    earlyCheckin: true,
    lateCheckout: true,
    customPolicyPerListing: true,
    instantBooking: true,
    verifiedPayment: true,
    autoApproveRules: true,
    blockInvalidDates: true,
    allowExtraGuests: false,
    seasonalRules: true,
    blockBufferWindow: true,
    applyExistingReservations: false,
    autoTransfer: true,
    releaseOnCancel: true,
    attachPdf: true,
    autoExportReports: false,
    pushEnabled: true,
    inAppEnabled: true,
    quietHours: true,
    escalationRules: true,
    enableFairAgent: true,
    contentGuardrails: true,
    blockOutsideDates: true,
    disallowOverrides: true,
    maskSensitiveInfo: true,
    addInternalNote: true,
    checkAvailability: true,
    createReservations: true,
    holdReservations: true,
    sendPaymentLinks: true,
    applyCoupons: true,
    citeSources: true,
    webChatChannel: true,
    whatsappChannel: true,
    emailChannel: true,
    smsChannel: true,
    facebookChannel: false,
    instagramChannel: false,
    websiteSync: true,
    googleDriveSync: true,
    manualSync: false,
    helpdeskSync: true,
    englishEnabled: true,
    spanishEnabled: true,
    frenchEnabled: false,
    germanEnabled: false,
    requireApproval: true,
    autoExpireArticles: true,
    sendInvitationEmail: true,
    commandCenterAccess: true,
    reservationsAccess: true,
    calendarAccess: true,
    guestsAccess: true,
    propertiesAccess: true,
    maintenanceAccess: true,
    paymentsAccess: true,
    reportsAccess: true,
    settingsAccess: false,
    usersAccess: false,
    strongPasswords: true,
    require2fa: true,
    smsFallback: true,
    stripeConnected: true,
    paypalConnected: true,
    emailConnected: true,
    smsConnected: true,
    analyticsConnected: true,
    sendEmailOnBooking: true,
    lowOccupancyAlert: true,
    syncNewReservations: true,
  },
  checks: {
    sourcePropertyFaqs: true,
    sourcePolicies: true,
    sourceDescriptions: true,
    sourceHouseManual: true,
    sourceCustomDocs: false,
  },
};

const healthItems = [
  new HealthItem('Application', CalendarDays),
  new HealthItem('Database', Database),
  new HealthItem('Integrations', PlugZap),
  new HealthItem('Email Service', Mail),
  new HealthItem('SMS Service', Bell),
  new HealthItem('AI Services', Bot),
];

const usageItems = [
  new UsageItem('Storage', '32%', '64.1 GB of 200 GB', 32, Database),
  new UsageItem('Bandwidth', 'This Month', '240 GB of 500 GB', 48, Cloud),
  new UsageItem('AI Credits', 'This Month', '3,120 of 5,000', 62, Bot),
];

const changeMap: Record<SettingsSectionId, ChangeItem[]> = {
  business: [
    new ChangeItem('Deposit policy updated', 'Piter Garcia', 'Jun 12, 2026 10:15 AM', 'cyan', CircleDollarSign),
    new ChangeItem('Branding assets updated', 'Maria Rodriguez', 'Jun 11, 2026 4:32 PM', 'violet', Palette),
    new ChangeItem('AI guardrails adjusted', 'Piter Garcia', 'Jun 11, 2026 1:08 PM', 'blue', ShieldCheck),
    new ChangeItem('SMS sender ID updated', 'System', 'Jun 10, 2026 9:41 AM', 'green', Bell),
  ],
  branding: [
    new ChangeItem('Branding assets updated', 'Maria Rodriguez', 'Jun 12, 2026 10:15 AM', 'violet', Palette),
    new ChangeItem('Email template updated', 'Piter Garcia', 'Jun 11, 2026 4:32 PM', 'blue', Mail),
    new ChangeItem('Color palette updated', 'Maria Rodriguez', 'Jun 11, 2026 1:08 PM', 'green', Palette),
    new ChangeItem('Favicon updated', 'Piter Garcia', 'Jun 10, 2026 3:22 PM', 'cyan', Upload),
  ],
  booking: [
    new ChangeItem('Booking defaults updated', 'Piter Garcia', 'Jun 12, 2026 10:15 AM', 'cyan', CalendarDays),
    new ChangeItem('Cancellation policy updated', 'Maria Rodriguez', 'Jun 11, 2026 4:32 PM', 'violet', FileText),
    new ChangeItem('Seasonal rules updated', 'Piter Garcia', 'Jun 11, 2026 1:08 PM', 'blue', SlidersHorizontal),
    new ChangeItem('Instant booking enabled', 'Piter Garcia', 'Jun 9, 2026 3:22 PM', 'green', CheckCircle2),
  ],
  finance: [
    new ChangeItem('Deposit policy updated', 'Piter Garcia', 'Jun 12, 2026 10:15 AM', 'cyan', CircleDollarSign),
    new ChangeItem('Stripe account reconnected', 'Maria Rodriguez', 'Jun 11, 2026 4:32 PM', 'violet', CreditCard),
    new ChangeItem('Payout schedule updated', 'Piter Garcia', 'Jun 11, 2026 1:08 PM', 'blue', Wallet),
  ],
  notifications: [
    new ChangeItem('Notification template updated', 'Maria Rodriguez', 'Jun 12, 2026 10:15 AM', 'violet', Bell),
    new ChangeItem('Escalation rule created', 'Piter Garcia', 'Jun 12, 2026 9:02 AM', 'rose', ShieldCheck),
    new ChangeItem('Recipients group updated', 'Maria Rodriguez', 'Jun 11, 2026 4:32 PM', 'blue', Users),
  ],
  ai: [
    new ChangeItem('Escalated conversation', 'System', 'Jun 12, 2026 10:12 AM', 'rose', MessageSquare),
    new ChangeItem('Reservation created', 'FairAgent', 'Jun 12, 2026 9:47 AM', 'green', CalendarDays),
    new ChangeItem('FAQ source updated', 'Piter Garcia', 'Jun 11, 2026 4:31 PM', 'violet', BookOpen),
  ],
  knowledge: [
    new ChangeItem('Knowledge base sync completed', 'System', 'Jun 12, 2026 10:30 AM', 'cyan', BookOpen),
    new ChangeItem('New article published', 'Maria Rodriguez', 'Jun 12, 2026 9:15 AM', 'violet', FileText),
    new ChangeItem('Article approved', 'Maria Rodriguez', 'Jun 11, 2026 11:05 AM', 'green', CheckCircle2),
  ],
  access: [
    new ChangeItem('New user invited', 'Piter Garcia', 'Jun 12, 2026 10:15 AM', 'green', Users),
    new ChangeItem('Role updated', 'Maria Rodriguez', 'Jun 11, 2026 4:32 PM', 'violet', ShieldCheck),
    new ChangeItem('Permissions updated', 'Piter Garcia', 'Jun 11, 2026 1:08 PM', 'blue', LockKeyhole),
  ],
  integrations: [
    new ChangeItem('Integration connected', 'Piter Garcia', 'Jun 12, 2026 9:45 AM', 'cyan', PlugZap),
    new ChangeItem('Webhook updated', 'Maria Rodriguez', 'Jun 12, 2026 8:22 AM', 'violet', Webhook),
    new ChangeItem('API key generated', 'Piter Garcia', 'Jun 11, 2026 4:15 PM', 'blue', KeyRound),
  ],
};

const selectOptions = {
  countries: ['Dominican Republic', 'United States', 'Puerto Rico'],
  timeZones: ['(UTC-04:00) America/Santo Domingo', '(UTC-05:00) America/New_York', '(UTC+00:00) UTC'],
  languages: ['English', 'Spanish', 'English + Spanish', 'French', 'German'],
  channels: ['Direct Booking', 'Airbnb', 'Manual Admin Request', 'Google Calendar Import'],
  currencies: ['USD - US Dollar', 'DOP - Dominican Peso', 'EUR - Euro'],
  times: ['07:00 AM', '10:00 PM', '11:00 AM', '12:00 PM', '01:00 PM', '03:00 PM', '04:00 PM'],
  dateFormats: ['Jun 19, 2026', '2026-06-19', '06/19/2026', '19/06/2026'],
  numberFormats: ['1,234.56', '1.234,56', '1234.56'],
  depositTypes: ['Fixed amount', 'Percentage of reservation', 'Per-night amount'],
  releaseOptions: ['Check-out', '24 hours before arrival', 'After inspection', 'Manual release'],
  paymentMethods: ['Credit Card', 'Stripe Checkout', 'PayPal', 'Cash / Manual'],
  roundingRules: ['Round to nearest $0.01', 'Round to nearest $0.05', 'Round to nearest $1.00'],
  modelModes: ['GPT-4o (Recommended)', 'GPT-4.1', 'o4-mini', 'Draft-only responses'],
  knowledgeSources: ['Published FAQ + admin notes', 'FAQ only', 'Admin notes only', 'Full approved knowledge base'],
  stripeModes: ['Test mode locally, live mode in production', 'Test mode only', 'Live mode only', 'Disabled'],
  refundTypes: ['By nights', 'Fixed date', 'Manual approval'],
  roles: ['Admin', 'Operator', 'Finance', 'Support', 'Housekeeping'],
  accessLevels: ['Full Access', 'Read Only', 'No Access'],
};

const availableCurrencyCodes = ['USD', 'DOP', 'EUR', 'CAD', 'GBP'];

const channelCards = [
  { key: 'emailEnabled', title: 'Email', body: 'Receive notifications via email for important updates.', icon: Mail, value: 'Primary: hello@mladis.com' },
  { key: 'smsEnabled', title: 'SMS', body: 'Receive text messages for urgent alerts.', icon: MessageSquare, value: 'Primary: +1 (809) 555-0198' },
  { key: 'pushEnabled', title: 'Push Notifications', body: 'Receive push notifications in the mobile app.', icon: Bell, value: 'Devices: 2 connected' },
  { key: 'inAppEnabled', title: 'In-App', body: 'View notifications in the Command Center.', icon: MessageSquare, value: 'Enabled in workspace' },
];

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

function mergeSettings<T>(base: T, incoming: unknown): T {
  if (Array.isArray(base)) {
    return (Array.isArray(incoming) ? incoming : base) as T;
  }

  if (!isPlainObject(base) || !isPlainObject(incoming)) {
    return (typeof incoming === typeof base ? incoming : base) as T;
  }

  return Object.entries(base).reduce((next, [key, value]) => ({
    ...next,
    [key]: mergeSettings(value, incoming[key]),
  }), {} as T);
}

function loadLocalState<T>(key: string, defaults: T): T {
  if (typeof window === 'undefined') {
    return defaults;
  }

  try {
    const raw = window.localStorage.getItem(key);
    return raw ? mergeSettings(defaults, JSON.parse(raw)) : defaults;
  } catch {
    return defaults;
  }
}

function buildSettingsPayload(settings: SettingsDraft, runtime: RuntimeState, reason: string) {
  return {
    object_type: 'mladis.settings',
    schema_version: '2026-06-13.v5',
    source: 'ops.settings',
    reason,
    captured_at: new Date().toISOString(),
    settings,
    runtime,
  };
}

function downloadJson(payload: unknown, filename: string) {
  if (typeof document === 'undefined') {
    return;
  }

  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function getField(runtime: RuntimeState, key: string) {
  return runtime.fields[key] ?? defaultRuntime.fields[key] ?? '';
}

function getToggle(runtime: RuntimeState, key: string) {
  return runtime.toggles[key] ?? defaultRuntime.toggles[key] ?? false;
}

function getCheck(runtime: RuntimeState, key: string) {
  return runtime.checks[key] ?? defaultRuntime.checks[key] ?? false;
}

function SettingsPanel({
  title,
  subtitle,
  children,
  className = '',
  action,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  action?: ReactNode;
}) {
  return (
    <section className={`settings-v4-panel ${className}`}>
      <header className="settings-v4-panel__header">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </header>
      {children}
    </section>
  );
}

function EditableField({
  label,
  value,
  onChange,
  variant = 'input',
  options = [],
  suffix = '',
  wide = false,
  rows = 2,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  variant?: FieldVariant;
  options?: string[];
  suffix?: string;
  wide?: boolean;
  rows?: number;
  placeholder?: string;
}) {
  const type = variant === 'number' ? 'number' : variant === 'email' || variant === 'tel' || variant === 'url' ? variant : 'text';

  return (
    <label className={`settings-v4-field${wide || variant === 'textarea' ? ' settings-v4-field--wide' : ''}`}>
      <span>{label}</span>
      <div className={`settings-v4-control settings-v4-control--${variant}`}>
        {variant === 'textarea' ? (
          <textarea value={value} onChange={(event) => onChange(event.target.value)} rows={rows} placeholder={placeholder} />
        ) : variant === 'select' ? (
          <select value={value} onChange={(event) => onChange(event.target.value)}>
            {options.map((option) => <option key={option} value={option}>{option}</option>)}
          </select>
        ) : (
          <input type={type} value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
        )}
        {suffix && <em>{suffix}</em>}
      </div>
    </label>
  );
}

function RuntimeField({
  runtime,
  fieldKey,
  onChange,
  ...props
}: Omit<Parameters<typeof EditableField>[0], 'value' | 'onChange'> & {
  runtime: RuntimeState;
  fieldKey: string;
  onChange: (key: string, value: string) => void;
}) {
  return <EditableField {...props} value={getField(runtime, fieldKey)} onChange={(value) => onChange(fieldKey, value)} />;
}

function SwitchRow({
  title,
  caption,
  active,
  onChange,
}: {
  title: string;
  caption?: string;
  active: boolean;
  onChange: (active: boolean) => void;
}) {
  return (
    <div className="settings-v4-switch-row">
      <span>
        <strong>{title}</strong>
        {caption && <small>{caption}</small>}
      </span>
      <button className={active ? 'is-active' : ''} type="button" aria-pressed={active} aria-label={title} onClick={() => onChange(!active)}>
        <i />
      </button>
    </div>
  );
}

function RuntimeSwitch({
  runtime,
  switchKey,
  onChange,
  title,
  caption,
}: {
  runtime: RuntimeState;
  switchKey: string;
  onChange: (key: string, active: boolean) => void;
  title: string;
  caption?: string;
}) {
  return <SwitchRow title={title} caption={caption} active={getToggle(runtime, switchKey)} onChange={(active) => onChange(switchKey, active)} />;
}

function CheckLine({
  checked,
  onChange,
  label,
  meta,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  meta?: string;
}) {
  return (
    <label className="settings-v4-check-line">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span>
        <strong>{label}</strong>
        {meta && <small>{meta}</small>}
      </span>
    </label>
  );
}

function StatusBadge({ children, tone = 'green' }: { children: ReactNode; tone?: Tone }) {
  return <span className={`settings-v4-badge settings-v4-badge--${tone}`}>{children}</span>;
}

function TinyButton({
  children,
  onClick,
  tone = 'slate',
}: {
  children: ReactNode;
  onClick: () => void;
  tone?: Tone;
}) {
  return (
    <button className={`settings-v4-tiny-button settings-v4-tiny-button--${tone}`} type="button" onClick={onClick}>
      {children}
    </button>
  );
}

function IconBadge({ icon: Icon, tone = 'blue' }: { icon: LucideIcon; tone?: Tone }) {
  return (
    <span className={`settings-v4-icon-badge settings-v4-icon-badge--${tone}`}>
      <Icon size={17} />
    </span>
  );
}

function MiniSparkline({ tone = 'blue' }: { tone?: Tone }) {
  return (
    <svg className={`settings-v4-sparkline settings-v4-sparkline--${tone}`} viewBox="0 0 120 34" aria-hidden="true">
      <polyline points="0,24 12,26 24,20 36,22 48,14 60,16 72,19 84,21 96,17 108,20 120,15" />
    </svg>
  );
}

function MiniProgress({ value, tone = 'blue' }: { value: number; tone?: Tone }) {
  return <i className={`settings-v4-mini-progress settings-v4-mini-progress--${tone}`} style={{ '--settings-progress': `${value}%` } as CSSProperties} />;
}

function ListCard({
  icon,
  title,
  meta,
  status,
  tone = 'blue',
  action,
}: {
  icon?: LucideIcon;
  title: string;
  meta?: string;
  status?: ReactNode;
  tone?: Tone;
  action?: ReactNode;
}) {
  return (
    <article className="settings-v4-list-card">
      {icon && <IconBadge icon={icon} tone={tone} />}
      <div>
        <strong>{title}</strong>
        {meta && <small>{meta}</small>}
      </div>
      {status && <span className="settings-v4-list-card__status">{status}</span>}
      {action && <span className="settings-v4-list-card__actions">{action}</span>}
    </article>
  );
}

function MetricCard({
  icon,
  title,
  value,
  caption,
  tone = 'blue',
}: {
  icon: LucideIcon;
  title: string;
  value: string;
  caption: string;
  tone?: Tone;
}) {
  return (
    <article className={`settings-v4-metric settings-v4-metric--${tone}`}>
      <IconBadge icon={icon} tone={tone} />
      <div>
        <span>{title}</span>
        <strong>{value}</strong>
        <small>{caption}</small>
      </div>
      <MiniSparkline tone={tone} />
    </article>
  );
}

function MiniToggle({ active = true }: { active?: boolean }) {
  return (
    <span className={`settings-v4-mini-toggle${active ? ' is-active' : ''}`} aria-hidden="true">
      <i />
    </span>
  );
}

function WorkflowStep({
  icon: Icon,
  label,
  active,
  onClick,
}: {
  icon: LucideIcon;
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button type="button" className={`settings-v4-workflow-step${active ? ' is-active' : ''}`} onClick={onClick}>
      <span><Icon size={17} /></span>
      <strong>{label}</strong>
      <MiniToggle active={active} />
    </button>
  );
}

function PolicySummaryRow({ title, detail }: { title: string; detail: string }) {
  return (
    <article className="settings-v4-policy-row">
      <strong>{title}</strong>
      <small>{detail}</small>
      <StatusBadge>Active <CheckCircle2 size={12} /></StatusBadge>
    </article>
  );
}

function AvatarCluster({ count }: { count: number }) {
  const initials = ['PG', 'MR', 'DG'];
  return (
    <span className="settings-v4-avatar-cluster" aria-label={`${count} profiles`}>
      {initials.map((initial, index) => <i key={initial} className={`settings-v4-avatar settings-v4-avatar--${index}`}>{initial}</i>)}
      <em>+{Math.max(1, count - initials.length)}</em>
    </span>
  );
}

function RecipientRow({
  title,
  count,
  accent,
  onEdit,
}: {
  title: string;
  count: number;
  accent: Tone;
  onEdit: () => void;
}) {
  return (
    <article className="settings-v4-recipient-row">
      <div>
        <strong>{title}</strong>
        <small>{count} recipients</small>
      </div>
      <AvatarCluster count={count} />
      <StatusBadge tone={accent}>+{Math.max(1, count - 4)}</StatusBadge>
      <TinyButton onClick={onEdit}>Edit</TinyButton>
    </article>
  );
}

function FinanceSummaryChart() {
  return (
    <div className="settings-v4-finance-chart">
      <div className="settings-v4-finance-legend">
        <span><i /> Gross Revenue</span>
        <span><i /> Net Revenue</span>
      </div>
      <svg viewBox="0 0 720 190" aria-label="Finance summary revenue chart" role="img">
        <g className="settings-v4-chart-grid">
          {[36, 72, 108, 144].map((y) => <line key={y} x1="22" x2="700" y1={y} y2={y} />)}
        </g>
        <polyline className="settings-v4-chart-line settings-v4-chart-line--blue" points="24,142 64,128 104,102 144,88 184,92 224,78 264,86 304,74 344,62 384,74 424,68 464,58 504,82 544,74 584,64 624,48 664,54 700,40" />
        <polyline className="settings-v4-chart-line settings-v4-chart-line--green" points="24,154 64,136 104,124 144,112 184,118 224,108 264,114 304,104 344,96 384,105 424,98 464,92 504,108 544,101 584,94 624,84 664,91 700,82" />
        <g className="settings-v4-chart-axis">
          <text x="24" y="182">May 6</text>
          <text x="188" y="182">May 13</text>
          <text x="352" y="182">May 20</text>
          <text x="516" y="182">May 27</text>
          <text x="656" y="182">Jun 3</text>
        </g>
      </svg>
    </div>
  );
}

function FinanceSummaryPanel() {
  const summaryCards: Array<{ icon: LucideIcon; label: string; value: string; trend: string; tone: Tone }> = [
    { icon: CalendarDays, label: 'Total Bookings', value: '86', trend: '+12.5% vs last month', tone: 'green' },
    { icon: CircleDollarSign, label: 'Gross Revenue', value: '$48,952', trend: '+18.7% vs last month', tone: 'blue' },
    { icon: Wallet, label: 'Deposits Collected', value: '$18,430', trend: '+15.3% vs last month', tone: 'cyan' },
    { icon: CreditCard, label: 'Payouts Sent', value: '$24,510', trend: '+10.1% vs last month', tone: 'violet' },
  ];

  return (
    <div className="settings-v4-finance-summary">
      {summaryCards.map(({ icon: Icon, label, value, trend, tone }) => (
        <article key={label}>
          <IconBadge icon={Icon} tone={tone} />
          <div>
            <span>{label}</span>
            <strong>{value}</strong>
            <small>{trend}</small>
          </div>
          <MiniSparkline tone={tone} />
        </article>
      ))}
      <FinanceSummaryChart />
    </div>
  );
}

function QuickAccessShortcuts({ runAction }: { runAction: (message: string) => void }) {
  const shortcuts: Array<{ icon: LucideIcon; title: string; meta: string; tone: Tone }> = [
    { icon: Users, title: 'Manage Users & Roles', meta: 'Add users, set roles, and manage permissions.', tone: 'blue' },
    { icon: Mail, title: 'Notification Templates', meta: 'Customize email and SMS templates.', tone: 'cyan' },
    { icon: CreditCard, title: 'Payment Gateways', meta: 'Connect and manage payment providers.', tone: 'violet' },
    { icon: Workflow, title: 'Automation Rules', meta: 'Create workflows and automations.', tone: 'orange' },
    { icon: KeyRound, title: 'API Keys', meta: 'Manage API keys and access tokens.', tone: 'rose' },
    { icon: Webhook, title: 'Webhooks', meta: 'Configure webhook endpoints.', tone: 'blue' },
  ];

  return (
    <section className="settings-v4-shortcuts">
      <h2>Quick Access Shortcuts</h2>
      <div>
        {shortcuts.map(({ icon: Icon, title, meta, tone }) => (
          <button key={title} type="button" className={`settings-v4-shortcut settings-v4-shortcut--${tone}`} onClick={() => runAction(`${title} opened`)}>
            <IconBadge icon={Icon} tone={tone} />
            <span className="settings-v4-shortcut__copy">
              <strong>{title}</strong>
              <small>{meta}</small>
            </span>
            <ChevronRight size={14} />
          </button>
        ))}
      </div>
    </section>
  );
}

function ChannelOption({
  icon: Icon,
  label,
  meta,
  active,
  onChange,
}: {
  icon: LucideIcon;
  label: string;
  meta: string;
  active: boolean;
  onChange: (active: boolean) => void;
}) {
  return (
    <label className={`settings-v4-channel-option${active ? ' is-active' : ''}`}>
      <IconBadge icon={Icon} tone={active ? 'blue' : 'slate'} />
      <span>
        <strong>{label}</strong>
        <small>{meta}</small>
      </span>
      <input type="checkbox" checked={active} onChange={(event) => onChange(event.target.checked)} />
    </label>
  );
}

function KnowledgeMetricRow({ label, value }: { label: string; value: string }) {
  return (
    <article className="settings-v4-knowledge-metric">
      <strong>{label}</strong>
      <StatusBadge tone="blue">{value}</StatusBadge>
    </article>
  );
}

function SyncStatusRow({ icon: Icon, title, meta }: { icon: LucideIcon; title: string; meta: string }) {
  return (
    <article className="settings-v4-sync-row">
      <IconBadge icon={Icon} tone="blue" />
      <div>
        <strong>{title}</strong>
        <small>Up to date | {meta}</small>
      </div>
      <CheckCircle2 size={15} />
    </article>
  );
}

function IntegrationTestRow({
  icon: Icon,
  title,
  meta,
  onClick,
}: {
  icon: LucideIcon;
  title: string;
  meta: string;
  onClick: () => void;
}) {
  return (
    <article className="settings-v4-test-row">
      <IconBadge icon={Icon} tone="blue" />
      <div>
        <strong>{title}</strong>
        <small>{meta}</small>
      </div>
      <TinyButton onClick={onClick}>Test Connection</TinyButton>
    </article>
  );
}

function LogoPreview({
  compact = false,
  dark = false,
  enabled,
  onChange,
  title = 'MLADIS',
}: {
  compact?: boolean;
  dark?: boolean;
  enabled: boolean;
  onChange: (enabled: boolean) => void;
  title?: string;
}) {
  const logoUrl = getConfiguredLogoUrl();

  return (
    <article className={`settings-v4-logo-card${compact ? ' settings-v4-logo-card--compact' : ''}${dark ? ' settings-v4-logo-card--dark' : ''}${!enabled ? ' is-disabled' : ''}`}>
      <button type="button" aria-label={enabled ? 'Hide asset preview' : 'Restore asset preview'} onClick={() => onChange(!enabled)}>
        {enabled ? 'x' : '+'}
      </button>
      <div className="settings-v4-logo-card__brand">
        {enabled && <img src={logoUrl} alt="MLADIS" />}
        <span>
          <strong>{title}</strong>
          <small>Property Management</small>
        </span>
      </div>
      <p>{compact ? 'Recommended 32x32px, PNG or ICO' : 'Recommended 512x512px, PNG or JPG'}</p>
      <a href="/admin/bookings/sitesettings/1/change/">
        <Upload size={14} />
        {compact ? 'Upload favicon' : dark ? 'Upload dark logo' : 'Upload new logo'}
      </a>
    </article>
  );
}

function CurrencyEditor({
  currencies,
  onChange,
}: {
  currencies: string[];
  onChange: (currencies: string[]) => void;
}) {
  const nextCurrency = availableCurrencyCodes.find((currency) => !currencies.includes(currency)) ?? availableCurrencyCodes[0];

  return (
    <label className="settings-v4-field settings-v4-field--wide">
      <span>Accepted currencies</span>
      <div className="settings-v4-token-control">
        {currencies.map((currency) => (
          <button
            aria-label={`Remove ${currency}`}
            className="settings-v4-token"
            key={currency}
            type="button"
            onClick={() => onChange(currencies.filter((item) => item !== currency))}
          >
            {currency} <i>x</i>
          </button>
        ))}
        <button type="button" onClick={() => !currencies.includes(nextCurrency) && onChange([...currencies, nextCurrency])}>
          + Add {nextCurrency}
        </button>
      </div>
    </label>
  );
}

function EnvironmentHealthCard() {
  return (
    <section className="settings-v4-side-card">
      <header>
        <h2>Environment Health</h2>
        <span>All Systems Operational</span>
      </header>
      <div className="settings-v4-health-list">
        {healthItems.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label}>
              <Icon size={16} />
              <strong>{item.label}</strong>
              <em>{item.value}</em>
              <CheckCircle2 size={14} />
            </div>
          );
        })}
      </div>
    </section>
  );
}

function StorageUsageCard() {
  return (
    <section className="settings-v4-side-card">
      <header>
        <h2>Storage & Usage</h2>
      </header>
      <div className="settings-v4-usage-list">
        {usageItems.map((item) => {
          const Icon = item.icon;
          return (
            <article key={item.label}>
              <Icon size={16} />
              <div>
                <strong>{item.label}</strong>
                <small>{item.caption}</small>
              </div>
              <span>{item.value}</span>
              <i style={{ '--settings-progress': `${item.progress}%` } as CSSProperties} />
            </article>
          );
        })}
      </div>
      <a className="settings-v4-side-link" href="/ops/reports/">View usage details</a>
    </section>
  );
}

function RecentChangesCard({ activeTab }: { activeTab: SettingsSectionId }) {
  const changes = changeMap[activeTab] ?? changeMap.business;

  return (
      <section className="settings-v4-side-card">
        <header>
          <h2>{activeTab === 'access' ? 'Recent Access Changes' : activeTab === 'ai' ? 'Recent AI Activity' : 'Recent Changes'}</h2>
          <a href="/ops/reports/">View all</a>
        </header>
        <div className="settings-v4-change-list">
          {changes.map((change) => {
            const Icon = change.icon;
            return (
              <article className={`settings-v4-change settings-v4-change--${change.tone}`} key={`${change.title}-${change.time}`}>
                <span><Icon size={14} /></span>
                <div>
                  <strong>{change.title}</strong>
                  <small>by {change.owner}</small>
                </div>
                <time>{change.time}</time>
              </article>
            );
          })}
        </div>
      </section>
  );
}

function SettingsBackupCard({ onBackup }: { onBackup: () => void }) {
  return (
    <section className="settings-v4-side-card settings-v4-backup">
      <header>
        <h2>Settings Backup</h2>
      </header>
      <p>Last backup: stored locally when you click below.</p>
      <button type="button" onClick={onBackup}><Download size={15} /> Create Backup</button>
    </section>
  );
}

function NeedHelpCard() {
  return (
    <section className="settings-v4-side-card settings-v4-help-card">
      <header>
        <h2>Need help?</h2>
      </header>
      <p>Visit our Knowledge Base for guides and best practices.</p>
      <a className="settings-v4-side-button" href="/ops/agent/"><BookOpen size={14} /> Go to Knowledge Base</a>
    </section>
  );
}

function FinanceGlanceCard() {
  return (
    <section className="settings-v4-side-card settings-v4-finance-glance">
      <header>
        <h2>Finance At a Glance</h2>
        <button type="button">This Month</button>
      </header>
      <small>Net Revenue</small>
      <strong>$24,442.00 <em>+14.6%</em></strong>
      <MiniSparkline tone="blue" />
      <ListCard icon={FileText} title="Outstanding Invoices" meta="$3,210.00" status={<span>8 Invoices</span>} tone="violet" />
      <ListCard icon={CalendarDays} title="Upcoming Payout" meta="$5,430.00" status={<span>Jun 16, 2026</span>} tone="blue" />
    </section>
  );
}

function AiCreditCard() {
  return (
    <section className="settings-v4-side-card settings-v4-ai-credit">
      <header>
        <h2>AI Credit Usage</h2>
      </header>
      <div className="settings-v4-ai-credit__summary">
        <div>
          <strong>3,120</strong> <span>of 5,000</span>
          <small>credits used this month</small>
        </div>
        <b>62%</b>
      </div>
      <MiniProgress value={62} />
      <ListCard icon={Clock} title="This month" meta="3,120" tone="cyan" />
      <ListCard icon={Database} title="Remaining" meta="1,880" tone="blue" />
      <ListCard icon={RotateCcw} title="Resets on" meta="Jul 1, 2026" tone="violet" />
      <a className="settings-v4-side-button" href="/ops/reports/">View AI usage details</a>
    </section>
  );
}

function AgentPreviewCard({ onAction }: { onAction: (message: string) => void }) {
  return (
    <section className="settings-v4-side-card settings-v4-agent-preview">
      <header>
        <h2>Agent Behavior Preview</h2>
      </header>
      <p>Simulate how FairAgent responds.</p>
      <article className="settings-v4-chat-preview">
        <p>Is there a late check-out available?</p>
        <div>
          <img src={getConfiguredLogoUrl()} alt="" />
          <span>Yes! Late check-out is available until 1:00 PM for $25, subject to availability. Would you like me to add it to your reservation?</span>
        </div>
        <small>Confidence: 84%</small>
        <button type="button" onClick={() => onAction('FairAgent preview regenerated')}>Test another question</button>
      </article>
    </section>
  );
}

function SideRail({
  onBackup,
  activeTab,
  onAction,
}: {
  onBackup: () => void;
  activeTab: SettingsSectionId;
  onAction: (message: string) => void;
}) {
  if (activeTab === 'ai') {
    return (
      <aside className="settings-v4-side">
        <EnvironmentHealthCard />
        <AiCreditCard />
        <AgentPreviewCard onAction={onAction} />
        <RecentChangesCard activeTab={activeTab} />
      </aside>
    );
  }

  return (
    <aside className="settings-v4-side">
      <EnvironmentHealthCard />
      <StorageUsageCard />
      {activeTab === 'finance' && <FinanceGlanceCard />}
      <RecentChangesCard activeTab={activeTab} />
      {activeTab === 'business' && <SettingsBackupCard onBackup={onBackup} />}
      {activeTab === 'booking' && <NeedHelpCard />}
    </aside>
  );
}

function BusinessProfileTab({ settings, runtime, updateSection, updateToggle, runAction }: SettingsTabProps) {
  return (
    <>
      <SettingsPanel title="Business Information" className="settings-v4-panel--business">
        <div className="settings-v4-business-grid">
          <div className="settings-v4-form-grid">
            <EditableField label="Business Name" value={settings.business.businessName} onChange={(businessName) => updateSection('business', { businessName })} />
            <EditableField label="Legal Entity Name" value={settings.business.legalEntityName} onChange={(legalEntityName) => updateSection('business', { legalEntityName })} />
            <EditableField label="Country / Region" value={settings.business.country} onChange={(country) => updateSection('business', { country })} variant="select" options={selectOptions.countries} />
            <EditableField label="Time Zone" value={settings.business.timeZone} onChange={(timeZone) => updateSection('business', { timeZone })} variant="select" options={selectOptions.timeZones} />
            <EditableField label="Default Language" value={settings.business.defaultLanguage} onChange={(defaultLanguage) => updateSection('business', { defaultLanguage })} variant="select" options={selectOptions.languages} />
            <EditableField label="Business Email" value={settings.business.email} onChange={(email) => updateSection('business', { email })} variant="email" />
            <EditableField label="Business Phone" value={settings.business.phone} onChange={(phone) => updateSection('business', { phone })} variant="tel" />
            <EditableField label="Business Address" value={settings.business.address} onChange={(address) => updateSection('business', { address })} variant="textarea" rows={2} />
          </div>
          <div className="settings-v4-brand-stack">
            <div>
              <span>Business Logo</span>
              <LogoPreview enabled={settings.brand.logoEnabled} onChange={(logoEnabled) => updateSection('brand', { logoEnabled })} />
            </div>
            <div>
              <span>Favicon</span>
              <LogoPreview compact enabled={settings.brand.faviconEnabled} onChange={(faviconEnabled) => updateSection('brand', { faviconEnabled })} />
            </div>
          </div>
        </div>
      </SettingsPanel>

      <SettingsPanel title="Deposit Policy Defaults" subtitle="These defaults will be applied to new reservations.">
        <div className="settings-v4-policy-grid">
          <SwitchRow title="Deposit required" active={settings.finance.depositRequired} onChange={(depositRequired) => updateSection('finance', { depositRequired })} />
          <div className="settings-v4-field-grid">
            <EditableField label="Deposit type" value={settings.finance.depositType} onChange={(depositType) => updateSection('finance', { depositType })} variant="select" options={selectOptions.depositTypes} />
            <EditableField label="Deposit amount" value={settings.finance.depositAmount} onChange={(depositAmount) => updateSection('finance', { depositAmount })} variant="number" suffix="%" />
            <EditableField label="Hold duration" value={settings.finance.holdDuration} onChange={(holdDuration) => updateSection('finance', { holdDuration })} variant="number" suffix="hours" />
            <EditableField label="Release on" value={settings.finance.releaseOn} onChange={(releaseOn) => updateSection('finance', { releaseOn })} variant="select" options={selectOptions.releaseOptions} />
          </div>
          <SwitchRow title="Auto-hold for new reservations" active={settings.finance.autoHold} onChange={(autoHold) => updateSection('finance', { autoHold })} />
          <SwitchRow title="Require card on file" active={settings.finance.requireCard} onChange={(requireCard) => updateSection('finance', { requireCard })} />
          <a className="settings-v4-inline-link" href="/ops/deposits/">Manage deposit policies <ChevronRight size={14} /></a>
        </div>
      </SettingsPanel>

      <SettingsPanel title="Business Settings">
        <div className="settings-v4-split-settings">
          <div>
            <SwitchRow title="Enable multi-property management" caption="Manage multiple properties under this business." active={settings.booking.multiProperty} onChange={(multiProperty) => updateSection('booking', { multiProperty })} />
            <SwitchRow title="Allow direct booking by default" caption="Listings are bookable on your direct website." active={settings.booking.directBooking} onChange={(directBooking) => updateSection('booking', { directBooking })} />
            <SwitchRow title="Enable maintenance module" caption="Track, assign, and automate maintenance workflows." active={settings.booking.maintenanceModule} onChange={(maintenanceModule) => updateSection('booking', { maintenanceModule })} />
            <SwitchRow title="Require guest verification" caption="Verify guest identity before allowing reservations." active={settings.booking.guestVerification} onChange={(guestVerification) => updateSection('booking', { guestVerification })} />
          </div>
          <div className="settings-v4-form-grid settings-v4-form-grid--single">
            <EditableField label="Default channel for new listings" value={settings.booking.defaultChannel} onChange={(defaultChannel) => updateSection('booking', { defaultChannel })} variant="select" options={selectOptions.channels} />
            <EditableField label="Default pricing currency" value={settings.booking.pricingCurrency} onChange={(pricingCurrency) => updateSection('booking', { pricingCurrency })} variant="select" options={selectOptions.currencies} />
            <EditableField label="Default length of stay" value={settings.booking.stayLength} onChange={(stayLength) => updateSection('booking', { stayLength })} variant="number" suffix="nights" />
            <EditableField label="Default check-in time" value={settings.booking.checkIn} onChange={(checkIn) => updateSection('booking', { checkIn })} variant="select" options={selectOptions.times} />
            <EditableField label="Default check-out time" value={settings.booking.checkOut} onChange={(checkOut) => updateSection('booking', { checkOut })} variant="select" options={selectOptions.times} />
            <EditableField label="Date format" value={settings.booking.dateFormat} onChange={(dateFormat) => updateSection('booking', { dateFormat })} variant="select" options={selectOptions.dateFormats} />
            <EditableField label="Number format" value={settings.booking.numberFormat} onChange={(numberFormat) => updateSection('booking', { numberFormat })} variant="select" options={selectOptions.numberFormats} />
          </div>
        </div>
      </SettingsPanel>

      <SettingsPanel title="Payment & Finance Defaults">
        <div className="settings-v4-finance-grid">
          <EditableField label="Default payment method" value={settings.finance.paymentMethod} onChange={(paymentMethod) => updateSection('finance', { paymentMethod })} variant="select" options={selectOptions.paymentMethods} />
          <CurrencyEditor currencies={settings.finance.currencies} onChange={(currencies) => updateSection('finance', { currencies })} />
          <EditableField label="Tax rate" value={settings.finance.taxRate} onChange={(taxRate) => updateSection('finance', { taxRate })} variant="number" suffix="%" />
          <EditableField label="Service fee (default)" value={settings.finance.serviceFee} onChange={(serviceFee) => updateSection('finance', { serviceFee })} variant="number" suffix="%" />
          <EditableField label="Rounding rule" value={settings.finance.roundingRule} onChange={(roundingRule) => updateSection('finance', { roundingRule })} variant="select" options={selectOptions.roundingRules} />
          <RuntimeSwitch runtime={runtime} switchKey="autoExportReports" onChange={updateToggle} title="Automatically export reports" caption="Email monthly reports automatically." />
        </div>
      </SettingsPanel>

      <QuickAccessShortcuts runAction={runAction} />
    </>
  );
}

function BrandingTab({ settings, runtime, updateSection, updateField, updateToggle, runAction }: SettingsTabProps) {
  return (
    <>
      <SettingsPanel title="Brand Identity" subtitle="Manage your logos and brand assets." className="settings-v4-panel--span-2">
        <div className="settings-v4-asset-grid">
          <div>
            <span>Primary Logo</span>
            <LogoPreview enabled={settings.brand.logoEnabled} onChange={(logoEnabled) => updateSection('brand', { logoEnabled })} />
          </div>
          <div>
            <span>Favicon</span>
            <LogoPreview compact enabled={settings.brand.faviconEnabled} onChange={(faviconEnabled) => updateSection('brand', { faviconEnabled })} />
          </div>
          <div>
            <span>Dark Mode Logo</span>
            <LogoPreview dark enabled={getToggle(runtime, 'darkLogoEnabled')} onChange={(darkLogoEnabled) => updateToggle('darkLogoEnabled', darkLogoEnabled)} />
          </div>
        </div>
      </SettingsPanel>

      <SettingsPanel title="Color Palette" subtitle="Define your brand colors.">
        <div className="settings-v4-form-grid settings-v4-form-grid--single">
          <EditableField label="Primary Color" value={settings.brand.primaryColor} onChange={(primaryColor) => updateSection('brand', { primaryColor })} />
          <RuntimeField label="Secondary Color" runtime={runtime} fieldKey="secondaryColor" onChange={updateField} />
          <EditableField label="Accent Color" value={settings.brand.accentColor} onChange={(accentColor) => updateSection('brand', { accentColor })} />
          <RuntimeField label="Neutral Color" runtime={runtime} fieldKey="neutralColor" onChange={updateField} />
        </div>
      </SettingsPanel>

      <SettingsPanel title="Typography" subtitle="Set your brand fonts.">
        <div className="settings-v4-form-grid settings-v4-form-grid--single">
          <RuntimeField label="Heading Font" runtime={runtime} fieldKey="headingFont" onChange={updateField} variant="select" options={['Poppins', 'Inter', 'Geist', 'Manrope']} />
          <RuntimeField label="Body Font" runtime={runtime} fieldKey="bodyFont" onChange={updateField} variant="select" options={['Inter', 'Poppins', 'Geist', 'Open Sans']} />
        </div>
      </SettingsPanel>

      <SettingsPanel title="Button Style" subtitle="Preview of your brand buttons.">
        <div className="settings-v4-button-preview">
          <button type="button" onClick={() => runAction('Primary button preview clicked')}>Primary Button</button>
          <button type="button" onClick={() => runAction('Secondary button preview clicked')}>Secondary Button</button>
          <button type="button" onClick={() => runAction('Text button preview clicked')}>Text Button <ChevronRight size={15} /></button>
        </div>
      </SettingsPanel>

      <SettingsPanel title="Email Template Preview" subtitle="Preview how your emails will look.">
        <article className="settings-v4-email-preview">
          <header><LogoPreview compact enabled onChange={() => undefined} /></header>
          <strong>Hello {'{{guest_name}}'},</strong>
          <p>Thank you for choosing MLADIS for your stay. We look forward to hosting you.</p>
          <button type="button" onClick={() => runAction('Email preview button clicked')}>View Reservation</button>
          <small>Questions? Reply to this email or contact us.</small>
        </article>
      </SettingsPanel>

      <SettingsPanel title="Social Preview" subtitle="How your brand appears on social platforms and search." className="settings-v4-panel--span-1">
        <article className="settings-v4-social-preview">
          <img src={getConfiguredLogoUrl()} alt="" />
          <div>
            <h3>{settings.business.businessName}</h3>
            <p>@mladispropertymanagement</p>
            <small>Premium property management and hospitality services across the Dominican Republic.</small>
            <a href="/">www.mladis.com</a>
          </div>
        </article>
      </SettingsPanel>

      <SettingsPanel title="Live Brand Preview" subtitle="See your brand in action." className="settings-v4-panel--span-2">
        <article className="settings-v4-live-preview">
          <div>
            <span>MLADIS Property Management</span>
            <nav>Properties Destinations About Us <button type="button">Book Now</button></nav>
          </div>
          <strong>Exceptional stays. Authentic experiences.</strong>
          <p>Discover premium properties in the Dominican Republic.</p>
        </article>
      </SettingsPanel>
    </>
  );
}

function BookingDefaultsTab({ settings, runtime, updateSection, updateField, updateToggle, runAction }: SettingsTabProps) {
  return (
    <>
      <SettingsPanel title="Default Stay Rules" subtitle="Set default stay requirements for new listings.">
        <div className="settings-v4-field-grid">
          <RuntimeField label="Minimum stay" runtime={runtime} fieldKey="minimumStay" onChange={updateField} variant="number" suffix="nights" />
          <RuntimeField label="Maximum stay" runtime={runtime} fieldKey="maximumStay" onChange={updateField} variant="number" suffix="nights" />
        </div>
        <RuntimeSwitch runtime={runtime} switchKey="sameDayBooking" onChange={updateToggle} title="Allow same-day booking" />
        <RuntimeField label="Minimum advance notice" runtime={runtime} fieldKey="advanceNotice" onChange={updateField} variant="number" suffix="hours" />
      </SettingsPanel>

      <SettingsPanel title="Check-in / Check-out" subtitle="Set default times for guest arrivals and departures.">
        <EditableField label="Check-in time" value={settings.booking.checkIn} onChange={(checkIn) => updateSection('booking', { checkIn })} variant="select" options={selectOptions.times} />
        <EditableField label="Check-out time" value={settings.booking.checkOut} onChange={(checkOut) => updateSection('booking', { checkOut })} variant="select" options={selectOptions.times} />
        <RuntimeSwitch runtime={runtime} switchKey="earlyCheckin" onChange={updateToggle} title="Early check-in (if available)" />
        <RuntimeSwitch runtime={runtime} switchKey="lateCheckout" onChange={updateToggle} title="Late check-out (if available)" />
      </SettingsPanel>

      <SettingsPanel title="Deposit Defaults" subtitle="Default deposit settings for new reservations.">
        <SwitchRow title="Deposit required" active={settings.finance.depositRequired} onChange={(depositRequired) => updateSection('finance', { depositRequired })} />
        <EditableField label="Deposit type" value={settings.finance.depositType} onChange={(depositType) => updateSection('finance', { depositType })} variant="select" options={selectOptions.depositTypes} />
        <div className="settings-v4-field-grid">
          <EditableField label="Deposit amount" value={settings.finance.depositAmount} onChange={(depositAmount) => updateSection('finance', { depositAmount })} variant="number" suffix="%" />
          <EditableField label="Hold duration" value={settings.finance.holdDuration} onChange={(holdDuration) => updateSection('finance', { holdDuration })} variant="number" suffix="hours" />
        </div>
        <EditableField label="Release on" value={settings.finance.releaseOn} onChange={(releaseOn) => updateSection('finance', { releaseOn })} variant="select" options={selectOptions.releaseOptions} />
      </SettingsPanel>

      <SettingsPanel title="Cancellation Policy" subtitle="Default cancellation rules and refund windows.">
        <div className="settings-v4-field-grid">
          <RuntimeField label="Free cancellation window" runtime={runtime} fieldKey="freeCancelDays" onChange={updateField} variant="number" suffix="days" />
          <RuntimeField label="Partial refund window" runtime={runtime} fieldKey="partialRefundDays" onChange={updateField} variant="number" suffix="days" />
        </div>
        <RuntimeField label="No refund after" runtime={runtime} fieldKey="noRefundAfter" onChange={updateField} variant="number" suffix="days" />
        <RuntimeSwitch runtime={runtime} switchKey="customPolicyPerListing" onChange={updateToggle} title="Enable custom policy per listing" />
      </SettingsPanel>

      <SettingsPanel title="Instant Booking" subtitle="Control instant booking behavior.">
        <RuntimeSwitch runtime={runtime} switchKey="instantBooking" onChange={updateToggle} title="Instant booking enabled" />
        <RuntimeSwitch runtime={runtime} switchKey="verifiedPayment" onChange={updateToggle} title="Require verified payment" />
        <RuntimeSwitch runtime={runtime} switchKey="autoApproveRules" onChange={updateToggle} title="Auto-approve if rules met" />
        <RuntimeSwitch runtime={runtime} switchKey="blockInvalidDates" onChange={updateToggle} title="Block dates that violate rules" />
      </SettingsPanel>

      <SettingsPanel title="Booking Source Defaults" subtitle="Set default source and channel for new bookings.">
        <EditableField label="Default booking channel" value={settings.booking.defaultChannel} onChange={(defaultChannel) => updateSection('booking', { defaultChannel })} variant="select" options={selectOptions.channels} />
        <div className="settings-v4-field-grid">
          <EditableField label="Default source" value="Website" onChange={() => runAction('Default source ready for backend binding')} variant="select" options={['Website', 'Airbnb', 'Referral', 'Manual']} />
          <EditableField label="UTM source (optional)" value="" onChange={() => runAction('UTM source ready for backend binding')} placeholder="e.g. google, newsletter" />
        </div>
        <EditableField label="Referral source (optional)" value="" onChange={() => runAction('Referral source ready for backend binding')} placeholder="e.g. partner name" />
      </SettingsPanel>

      <SettingsPanel title="Guest Capacity Rules" subtitle="Set default occupancy and guest limits.">
        <div className="settings-v4-field-grid">
          <RuntimeField label="Default max guests" runtime={runtime} fieldKey="defaultMaxGuests" onChange={updateField} variant="number" suffix="guests" />
          <RuntimeField label="Max adults" runtime={runtime} fieldKey="maxAdults" onChange={updateField} variant="number" suffix="adults" />
          <RuntimeField label="Max children" runtime={runtime} fieldKey="maxChildren" onChange={updateField} variant="number" suffix="children" />
        </div>
        <RuntimeSwitch runtime={runtime} switchKey="allowExtraGuests" onChange={updateToggle} title="Allow extra guests" />
        <RuntimeField label="Extra guest fee" runtime={runtime} fieldKey="extraGuestFee" onChange={updateField} suffix="per guest / night" />
      </SettingsPanel>

      <SettingsPanel title="Cleaning & Buffer" subtitle="Set cleaning time and buffer between stays.">
        <RuntimeField label="Cleaning time" runtime={runtime} fieldKey="cleaningTime" onChange={updateField} variant="number" suffix="hours" />
        <div className="settings-v4-field-grid">
          <RuntimeField label="Buffer before check-in" runtime={runtime} fieldKey="bufferBefore" onChange={updateField} variant="number" suffix="hours" />
          <RuntimeField label="Buffer after check-out" runtime={runtime} fieldKey="bufferAfter" onChange={updateField} variant="number" suffix="hours" />
        </div>
        <RuntimeSwitch runtime={runtime} switchKey="blockBufferWindow" onChange={updateToggle} title="Block entire buffer window" />
      </SettingsPanel>

      <SettingsPanel title="Seasonal Rules" subtitle="Apply seasonal pricing or rules automatically.">
        <RuntimeSwitch runtime={runtime} switchKey="seasonalRules" onChange={updateToggle} title="Enable seasonal rules" />
        <RuntimeField label="High season tag" runtime={runtime} fieldKey="highSeasonTag" onChange={updateField} variant="select" options={['High Season', 'Holiday', 'Peak Demand']} />
        <RuntimeField label="Low season tag" runtime={runtime} fieldKey="lowSeasonTag" onChange={updateField} variant="select" options={['Low season tag', 'Slow Season', 'Off Peak']} />
        <TinyButton onClick={() => runAction('Seasonal rules manager opened')}>Manage seasonal rules</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Reservation Workflow" subtitle="Configure default reservation workflow steps." className="settings-v4-panel--span-2">
        <div className="settings-v4-workflow-strip">
          {[
            ['Payment authorization', 'requireCard', Workflow],
            ['ID verification', 'guestVerification', FileText],
            ['Rental agreement', 'customPolicyPerListing', Copy],
            ['Damage deposit hold', 'autoHold', Users],
            ['Pre-arrival message', 'emailEnabled', MessageSquare],
            ['Post-stay review', 'faqReview', CalendarDays],
          ].map(([label, key, Icon]) => (
            <WorkflowStep
              key={label as string}
              icon={Icon as LucideIcon}
              label={label as string}
              active={getToggle(runtime, key as string) || Boolean((settings as unknown as Record<string, Record<string, boolean>>).finance?.[key as string])}
              onClick={() => runAction(`${label} workflow selected`)}
            />
          ))}
        </div>
      </SettingsPanel>

      <SettingsPanel title="Active Booking Policies Summary" subtitle="Overview of your active booking policy settings.">
        <div className="settings-v4-policy-summary">
          {[
            ['Stay requirements', 'Min 2 nights · Max 30 nights'],
            ['Cancellation policy', '7d free · 14d partial · 30d no refund'],
            ['Deposits', '20% · Held for 24 hours · Released on check-out'],
            ['Instant booking', 'Enabled · Auto-approve · Verified payment'],
            ['Check-in / Check-out', 'Check-in 03:00 PM · Check-out 11:00 AM'],
          ].map(([title, detail]) => <PolicySummaryRow key={title} title={title} detail={detail} />)}
        </div>
      </SettingsPanel>
    </>
  );
}

function FinanceTab({ settings, runtime, updateSection, updateField, updateToggle, runAction }: SettingsTabProps) {
  return (
    <>
      <SettingsPanel title="Deposit Policy Defaults" subtitle="Configure how deposits are collected for new reservations.">
        <SwitchRow title="Deposit required" active={settings.finance.depositRequired} onChange={(depositRequired) => updateSection('finance', { depositRequired })} />
        <div className="settings-v4-field-grid">
          <EditableField label="Deposit type" value={settings.finance.depositType} onChange={(depositType) => updateSection('finance', { depositType })} variant="select" options={selectOptions.depositTypes} />
          <EditableField label="Deposit amount" value={settings.finance.depositAmount} onChange={(depositAmount) => updateSection('finance', { depositAmount })} variant="number" suffix="%" />
          <EditableField label="Hold duration" value={settings.finance.holdDuration} onChange={(holdDuration) => updateSection('finance', { holdDuration })} variant="number" suffix="hours" />
          <EditableField label="Release on" value={settings.finance.releaseOn} onChange={(releaseOn) => updateSection('finance', { releaseOn })} variant="select" options={selectOptions.releaseOptions} />
        </div>
        <SwitchRow title="Auto-hold for new reservations" active={settings.finance.autoHold} onChange={(autoHold) => updateSection('finance', { autoHold })} />
        <RuntimeSwitch runtime={runtime} switchKey="applyExistingReservations" onChange={updateToggle} title="Apply to existing reservations" caption="Update deposit policy for existing future reservations." />
      </SettingsPanel>

      <SettingsPanel title="Payment Providers" subtitle="Manage how you collect payments from guests." className="settings-v4-panel--span-2">
        <div className="settings-v4-provider-list">
          <ListCard icon={CreditCard} title="Stripe" meta="Mode: Live | Account: mladis_stripe" tone="violet" status={<StatusBadge>Connected</StatusBadge>} action={<TinyButton onClick={() => runAction('Stripe settings opened')}>Manage</TinyButton>} />
          <ListCard icon={Wallet} title="PayPal" meta="Mode: Live | Account: payments@mladis.com" tone="blue" status={<StatusBadge>Connected</StatusBadge>} action={<TinyButton onClick={() => runAction('PayPal settings opened')}>Manage</TinyButton>} />
          <TinyButton onClick={() => runAction('Payment provider form opened')}><Plus size={14} /> Add Payment Provider</TinyButton>
        </div>
      </SettingsPanel>

      <SettingsPanel title="Currency & Tax Defaults" subtitle="Set your currency and tax preferences.">
        <EditableField label="Default currency" value={settings.booking.pricingCurrency} onChange={(pricingCurrency) => updateSection('booking', { pricingCurrency })} variant="select" options={selectOptions.currencies} />
        <div className="settings-v4-field-grid">
          <EditableField label="Currency position" value="$1,234.56 (before amount)" onChange={() => runAction('Currency position ready for backend binding')} variant="select" options={['$1,234.56 (before amount)', '1,234.56 $ (after amount)']} />
          <EditableField label="Rounding" value="2 decimals" onChange={() => runAction('Rounding decimals ready for backend binding')} variant="select" options={['2 decimals', '0 decimals']} />
        </div>
        <EditableField label="Default tax rate" value={settings.finance.taxRate} onChange={(taxRate) => updateSection('finance', { taxRate })} variant="number" suffix="%" />
        <p className="settings-v4-note"><Info size={14} /> These defaults will be used for pricing, invoices, and reports.</p>
      </SettingsPanel>

      <SettingsPanel title="Refund & Cancellation Rules" subtitle="Define how refunds are handled.">
        <RuntimeField label="Refund type" runtime={runtime} fieldKey="refundType" onChange={updateField} variant="select" options={selectOptions.refundTypes} />
        <div className="settings-v4-field-grid">
          <RuntimeField label="Full refund until" runtime={runtime} fieldKey="fullRefundUntil" onChange={updateField} variant="number" suffix="days before check-in" />
          <RuntimeField label="Partial refund until" runtime={runtime} fieldKey="partialRefundUntil" onChange={updateField} variant="number" suffix="day before check-in" />
        </div>
        <EditableField label="No refund after" value="Check-in" onChange={() => runAction('No refund rule ready for backend binding')} variant="select" options={['Check-in', '24 hours before check-in']} />
        <p className="settings-v4-note"><Info size={14} /> These rules apply to standard reservations.</p>
      </SettingsPanel>

      <SettingsPanel title="Payout Schedule" subtitle="Choose how often you receive payouts.">
        <div className="settings-v4-field-grid">
          <RuntimeField label="Payout frequency" runtime={runtime} fieldKey="payoutFrequency" onChange={updateField} variant="select" options={['Weekly', 'Monthly', 'Manual']} />
          <RuntimeField label="Payout day" runtime={runtime} fieldKey="payoutDay" onChange={updateField} variant="select" options={['Monday', 'Friday', 'Last day of month']} />
        </div>
        <RuntimeField label="Minimum payout" runtime={runtime} fieldKey="minimumPayout" onChange={updateField} variant="number" suffix="USD" />
        <RuntimeSwitch runtime={runtime} switchKey="autoTransfer" onChange={updateToggle} title="Auto-transfer to bank" caption="Automatically transfer payouts to your bank." />
      </SettingsPanel>

      <SettingsPanel title="Authorization Hold Duration" subtitle="Set how long card authorizations are held.">
        <div className="settings-v4-field-grid">
          <RuntimeField label="Hold duration" runtime={runtime} fieldKey="authorizationHoldDays" onChange={updateField} variant="number" suffix="days" />
          <RuntimeField label="Capture window" runtime={runtime} fieldKey="captureWindow" onChange={updateField} variant="select" options={['2 days before check-in', '24 hours before check-in', 'Manual capture']} />
        </div>
        <RuntimeSwitch runtime={runtime} switchKey="releaseOnCancel" onChange={updateToggle} title="Release on cancellation" caption="Automatically release holds on canceled bookings." />
      </SettingsPanel>

      <SettingsPanel title="Invoice & Document Settings" subtitle="Configure numbering and document preferences.">
        <div className="settings-v4-field-grid">
          <RuntimeField label="Invoice prefix" runtime={runtime} fieldKey="invoicePrefix" onChange={updateField} />
          <RuntimeField label="Next number" runtime={runtime} fieldKey="nextInvoiceNumber" onChange={updateField} variant="number" />
          <RuntimeField label="Date format" runtime={runtime} fieldKey="invoiceDateFormat" onChange={updateField} variant="select" options={['YYYY-MM-DD', 'MM/DD/YYYY', 'Jun 19, 2026']} />
          <RuntimeField label="Include paid stamp" runtime={runtime} fieldKey="paidStamp" onChange={updateField} variant="select" options={['On invoices', 'Never', 'Receipts only']} />
        </div>
        <RuntimeSwitch runtime={runtime} switchKey="attachPdf" onChange={updateToggle} title="Attach PDF to emails" caption="Automatically attach invoices to emails." />
      </SettingsPanel>

      <SettingsPanel title="Fees & Surcharges" subtitle="Configure additional fees and how they are handled.">
        <div className="settings-v4-field-grid">
          <EditableField label="Service fee" value={settings.finance.serviceFee} onChange={(serviceFee) => updateSection('finance', { serviceFee })} variant="number" suffix="%" />
          <RuntimeField label="Credit card surcharge" runtime={runtime} fieldKey="creditCardSurcharge" onChange={updateField} variant="number" suffix="%" />
        </div>
        <RuntimeField label="Who pays the fee?" runtime={runtime} fieldKey="whoPaysFee" onChange={updateField} variant="select" options={['Guest', 'Company', 'Split']} />
        <p className="settings-v4-note"><Info size={14} /> Fees will be added to the reservation total.</p>
      </SettingsPanel>

      <SettingsPanel title="Transaction Export Settings" subtitle="Customize your financial data exports.">
        <div className="settings-v4-field-grid">
          <RuntimeField label="Export format" runtime={runtime} fieldKey="exportFormat" onChange={updateField} variant="select" options={['CSV', 'JSON', 'Excel']} />
          <RuntimeField label="Date range default" runtime={runtime} fieldKey="exportDateRange" onChange={updateField} variant="select" options={['This Month', 'This Quarter', 'This Year']} />
          <RuntimeField label="Include details" runtime={runtime} fieldKey="includeDetails" onChange={updateField} variant="select" options={['All transactions', 'Summary only']} />
          <RuntimeField label="Timezone" runtime={runtime} fieldKey="exportTimezone" onChange={updateField} variant="select" options={selectOptions.timeZones} />
        </div>
        <RuntimeSwitch runtime={runtime} switchKey="autoExportReports" onChange={updateToggle} title="Automatically export reports" />
        <TinyButton onClick={() => runAction('Transaction export generated')}><Download size={14} /> Export Now</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Finance Summary" className="settings-v4-panel--span-2 settings-v4-panel--finance-summary" action={<EditableField label="Range" value="This Month" onChange={() => runAction('Finance summary range ready for backend binding')} variant="select" options={['This Month', 'This Quarter']} />}>
        <FinanceSummaryPanel />
      </SettingsPanel>
    </>
  );
}

function NotificationsTab({ settings, runtime, updateSection, updateField, updateToggle, runAction }: SettingsTabProps) {
  return (
    <>
      <SettingsPanel title="Notification Channels" subtitle="Manage how and when you receive notifications across the platform." className="settings-v4-panel--span-3">
        <div className="settings-v4-grid settings-v4-grid--4">
          {channelCards.map((card) => {
            const active = card.key in settings.notifications
              ? Boolean(settings.notifications[card.key as keyof typeof settings.notifications])
              : getToggle(runtime, card.key);
            return (
              <article className="settings-v4-channel-card" key={card.title}>
                <header>
                  <IconBadge icon={card.icon} tone="blue" />
                  <strong>{card.title}</strong>
                  <StatusBadge>Enabled</StatusBadge>
                </header>
                <p>{card.body}</p>
                <SwitchRow title={card.value} active={active} onChange={(next) => {
                  if (card.key === 'emailEnabled' || card.key === 'smsEnabled' || card.key === 'whatsappEnabled') {
                    updateSection('notifications', { [card.key]: next } as Partial<typeof settings.notifications>);
                  } else {
                    updateToggle(card.key, next);
                  }
                }} />
              </article>
            );
          })}
        </div>
        <div className="settings-v4-alert-row">
          {['Reservation Alerts', 'Maintenance Alerts', 'Deposit Alerts', 'System Alerts'].map((label) => (
            <button key={label} type="button" onClick={() => runAction(`${label} opened`)}>
              <strong>{label}</strong>
              <small>Booking, updates, payments, platform</small>
              <ChevronRight size={14} />
            </button>
          ))}
        </div>
      </SettingsPanel>

      <SettingsPanel title="Quiet Hours" subtitle="Mute non-urgent notifications during these hours.">
        <RuntimeSwitch runtime={runtime} switchKey="quietHours" onChange={updateToggle} title="Enable quiet hours" />
        <div className="settings-v4-field-grid">
          <RuntimeField label="Start time" runtime={runtime} fieldKey="quietStart" onChange={updateField} variant="select" options={selectOptions.times} />
          <RuntimeField label="End time" runtime={runtime} fieldKey="quietEnd" onChange={updateField} variant="select" options={selectOptions.times} />
        </div>
        <RuntimeField label="Time zone" runtime={runtime} fieldKey="quietTimezone" onChange={updateField} variant="select" options={selectOptions.timeZones} />
        <RuntimeField label="Apply to" runtime={runtime} fieldKey="quietChannels" onChange={updateField} variant="select" options={['All channels', 'SMS only', 'Push only']} />
      </SettingsPanel>

      <SettingsPanel title="Notification Templates" subtitle="Customize the content of your notifications.">
        {['Email Templates', 'SMS Templates', 'Push Templates', 'In-App Templates'].map((template, index) => (
          <ListCard key={template} title={template} meta={`${12 - index * 2} templates`} action={<ChevronRight size={15} />} />
        ))}
      </SettingsPanel>

      <SettingsPanel title="Escalation Rules" subtitle="Automatically escalate unresolved alerts.">
        <RuntimeSwitch runtime={runtime} switchKey="escalationRules" onChange={updateToggle} title="Enable escalation rules" />
        {[
          ['Level 1', 'After 15 min', 'Admin'],
          ['Level 2', 'After 30 min', 'Manager'],
          ['Level 3', 'After 60 min', 'Director'],
        ].map(([level, time, owner]) => <ListCard key={level} title={level} meta={`${time} -> ${owner}`} action={<ChevronRight size={15} />} />)}
        <TinyButton onClick={() => runAction('Escalation rules manager opened')}>Manage escalation rules <ChevronRight size={14} /></TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Notification Recipients" subtitle="Manage who receives specific types of notifications.">
        <div className="settings-v4-recipient-list">
          {[
            ['Administrators', 5, 'green'],
            ['Property Managers', 8, 'blue'],
            ['Maintenance Team', 6, 'green'],
            ['Accounting Team', 4, 'blue'],
          ].map(([group, count, tone]) => (
            <RecipientRow
              key={group as string}
              title={group as string}
              count={count as number}
              accent={tone as Tone}
              onEdit={() => runAction(`${group} recipients opened`)}
            />
          ))}
        </div>
        <TinyButton onClick={() => runAction('Recipient groups opened')}>View all recipient groups <ChevronRight size={14} /></TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Delivery Status" subtitle="Last 7 Days">
        <div className="settings-v4-grid settings-v4-grid--2">
          {['Email Delivered', 'SMS Delivered', 'Push Delivered', 'In-App Delivered'].map((label, index) => (
            <MetricCard key={label} icon={Bell} title={label} value={['1,248', '892', '1,102', '1,534'][index]} caption={`${98 - index * 0.7}%`} tone="green" />
          ))}
        </div>
      </SettingsPanel>

      <SettingsPanel title="Recent Activity" subtitle="Latest notification-related events.">
        {changeMap.notifications.slice(0, 4).map((item) => (
          <ListCard key={item.title} icon={item.icon} title={item.title} meta={`${item.time} by ${item.owner}`} tone={item.tone} />
        ))}
      </SettingsPanel>

    </>
  );
}

function AiTab({ settings, runtime, updateSection, updateField, updateToggle, updateCheck, runAction }: SettingsTabProps) {
  return (
    <>
      <SettingsPanel title="FairAgent / AI Configuration" subtitle="Configure your AI assistant to help guests, automate tasks, and protect your business." className="settings-v4-panel--span-3">
        <div className="settings-v4-ai-config">
          <div>
            <RuntimeSwitch runtime={runtime} switchKey="enableFairAgent" onChange={updateToggle} title="Enable FairAgent" caption="Turn on the AI assistant for your business." />
            <div className="settings-v4-field-grid">
              <RuntimeField label="Agent name" runtime={runtime} fieldKey="agentName" onChange={updateField} />
              <RuntimeField label="Default language" runtime={runtime} fieldKey="agentLanguage" onChange={updateField} variant="select" options={selectOptions.languages} />
            </div>
          </div>
          <div>
            <h3>AI Model</h3>
            <div className="settings-v4-field-grid">
              <RuntimeField label="Model provider" runtime={runtime} fieldKey="aiProvider" onChange={updateField} variant="select" options={['OpenAI', 'Anthropic', 'Google']} />
              <EditableField label="Model" value={settings.ai.modelMode} onChange={(modelMode) => updateSection('ai', { modelMode })} variant="select" options={selectOptions.modelModes} />
            </div>
          </div>
        </div>
      </SettingsPanel>

      <SettingsPanel title="Usage Budget & Controls" subtitle="Set monthly AI credit limits and alerts.">
        <div className="settings-v4-field-grid">
          <RuntimeField label="Monthly budget" runtime={runtime} fieldKey="monthlyBudget" onChange={updateField} suffix="credits" />
          <RuntimeField label="Alert threshold" runtime={runtime} fieldKey="alertThreshold" onChange={updateField} variant="select" options={['70%', '80%', '90%']} />
        </div>
        <RuntimeField label="Hard limit action" runtime={runtime} fieldKey="hardLimitAction" onChange={updateField} variant="select" options={['Pause responses', 'Draft only', 'Notify admin']} />
        <MiniProgress value={62} />
        <small>3,120 of 5,000 credits (62%)</small>
      </SettingsPanel>

      <SettingsPanel title="Guardrails & Safety" subtitle="Set boundaries to keep responses accurate and safe.">
        <RuntimeSwitch runtime={runtime} switchKey="contentGuardrails" onChange={updateToggle} title="Enable content guardrails" />
        <RuntimeSwitch runtime={runtime} switchKey="blockOutsideDates" onChange={updateToggle} title="Block booking outside allowed dates" />
        <RuntimeSwitch runtime={runtime} switchKey="disallowOverrides" onChange={updateToggle} title="Disallow pricing & policy overrides" />
        <RuntimeSwitch runtime={runtime} switchKey="maskSensitiveInfo" onChange={updateToggle} title="Mask sensitive property information" />
        <TinyButton onClick={() => runAction('Blocked topics manager opened')}>Manage blocked topics & phrases <ChevronRight size={14} /></TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Escalation Behavior" subtitle="Decide when and how conversations escalate.">
        <RuntimeField label="Escalate when confidence is below" runtime={runtime} fieldKey="confidenceThreshold" onChange={updateField} variant="select" options={['50%', '60%', '70%']} />
        <RuntimeField label="Escalate to" runtime={runtime} fieldKey="escalationTarget" onChange={updateField} variant="select" options={['Human team (Live agent)', 'Owner only', 'Operations team']} />
        <CheckLine checked={settings.notifications.emailEnabled} onChange={(emailEnabled) => updateSection('notifications', { emailEnabled })} label="Notify via Email" />
        <CheckLine checked={settings.notifications.smsEnabled} onChange={(smsEnabled) => updateSection('notifications', { smsEnabled })} label="Notify via SMS" />
        <RuntimeSwitch runtime={runtime} switchKey="addInternalNote" onChange={updateToggle} title="Add internal note" />
      </SettingsPanel>

      <SettingsPanel title="Tone & Personality" subtitle="Choose how FairAgent communicates.">
        <RuntimeField label="Tone preset" runtime={runtime} fieldKey="tonePreset" onChange={updateField} variant="select" options={['Professional & Friendly', 'Concise', 'Warm and detailed']} />
        <RuntimeField label="Custom instructions (optional)" runtime={runtime} fieldKey="customInstructions" onChange={updateField} variant="textarea" rows={4} />
      </SettingsPanel>

      <SettingsPanel title="Booking Automation" subtitle="Allow FairAgent to take actions on your behalf.">
        <RuntimeSwitch runtime={runtime} switchKey="checkAvailability" onChange={updateToggle} title="Check availability" />
        <RuntimeSwitch runtime={runtime} switchKey="createReservations" onChange={updateToggle} title="Create reservations" />
        <RuntimeSwitch runtime={runtime} switchKey="holdReservations" onChange={updateToggle} title="Hold reservations" />
        <RuntimeSwitch runtime={runtime} switchKey="sendPaymentLinks" onChange={updateToggle} title="Send payment links" />
        <RuntimeSwitch runtime={runtime} switchKey="applyCoupons" onChange={updateToggle} title="Apply coupons / discounts" />
        <small>Automated actions are logged and auditable.</small>
      </SettingsPanel>

      <SettingsPanel title="FAQ & Knowledge Grounding" subtitle="Choose sources FairAgent can use to answer guests.">
        {[
          ['Property FAQs', 'sourcePropertyFaqs'],
          ['Policies & Rules', 'sourcePolicies'],
          ['Listing Descriptions', 'sourceDescriptions'],
          ['House Manual', 'sourceHouseManual'],
          ['Custom Documents', 'sourceCustomDocs'],
        ].map(([label, key]) => (
          <CheckLine key={key} checked={getCheck(runtime, key)} onChange={(checked) => updateCheck(key, checked)} label={label} />
        ))}
        <TinyButton onClick={() => runAction('FairAgent knowledge sync queued')}>Sync now</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Confidence & Response Controls" subtitle="Control answer quality and fallback behavior.">
        <div className="settings-v4-field-grid">
          <RuntimeField label="Minimum confidence to answer" runtime={runtime} fieldKey="minConfidence" onChange={updateField} variant="select" options={['55%', '65%', '75%']} />
          <RuntimeField label="If unsure" runtime={runtime} fieldKey="fallbackBehavior" onChange={updateField} variant="select" options={['Ask a clarifying question', 'Escalate to staff', 'Draft only']} />
        </div>
        <RuntimeField label="Max response length" runtime={runtime} fieldKey="maxResponseLength" onChange={updateField} variant="select" options={['Short', 'Medium', 'Detailed']} />
        <RuntimeSwitch runtime={runtime} switchKey="citeSources" onChange={updateToggle} title="Cite sources in responses" />
      </SettingsPanel>

      <SettingsPanel title="Supported Channels" subtitle="Choose where FairAgent is available." className="settings-v4-panel--span-2">
        <div className="settings-v4-channel-option-grid">
          {[
            ['Web Chat', 'Live', 'webChatChannel', MessageSquare],
            ['WhatsApp', 'Live', 'whatsappChannel', MessageSquare],
            ['Email', 'Live', 'emailChannel', Mail],
            ['SMS', 'Live', 'smsChannel', Bell],
            ['Facebook', 'Disabled', 'facebookChannel', Users],
            ['Instagram', 'Disabled', 'instagramChannel', Globe2],
          ].map(([label, meta, key, Icon]) => (
            <ChannelOption
              key={key as string}
              icon={Icon as LucideIcon}
              label={label as string}
              meta={meta as string}
              active={getToggle(runtime, key as string)}
              onChange={(checked) => updateToggle(key as string, checked)}
            />
          ))}
        </div>
      </SettingsPanel>

    </>
  );
}

function KnowledgeTab({ runtime, updateField, updateToggle, runAction }: SettingsTabProps) {
  return (
    <>
      <SettingsPanel title="FAQ Collections" subtitle="Organize FAQs into collections for different audiences." className="settings-v4-panel--kb-top">
        {[
          ['Guest FAQs', '24 Articles', 'Active'],
          ['Property Owner FAQs', '18 Articles', 'Active'],
          ['Operations FAQs', '12 Articles', 'Draft'],
        ].map(([title, meta, status]) => <ListCard key={title} title={title} meta={meta} status={<StatusBadge tone={status === 'Draft' ? 'slate' : 'green'}>{status}</StatusBadge>} />)}
        <TinyButton onClick={() => runAction('New FAQ collection opened')}><Plus size={14} /> New Collection</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Categories" subtitle="Manage categories to keep content organized." className="settings-v4-panel--kb-top">
        {[
          ['Booking & Reservations', '15'],
          ['Payments & Deposits', '12'],
          ['Property & Stay Info', '18'],
          ['Policies & Rules', '10'],
          ['Maintenance & Services', '8'],
        ].map(([title, count]) => <ListCard key={title} icon={Folder} title={title} status={<StatusBadge tone="blue">{count}</StatusBadge>} />)}
        <TinyButton onClick={() => runAction('New category opened')}><Plus size={14} /> New Category</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Article Manager" subtitle="Create, edit, and manage knowledge base articles." className="settings-v4-panel--kb-top">
        {[
          ['Total Articles', '84'],
          ['Published', '68'],
          ['Drafts', '12'],
          ['Pending Review', '4'],
          ['Archived', '0'],
        ].map(([title, count], index) => <ListCard key={title} title={title} status={<StatusBadge tone={['blue', 'green', 'orange', 'violet', 'slate'][index] as Tone}>{count}</StatusBadge>} />)}
        <TinyButton onClick={() => runAction('Article manager opened')}>View All Articles</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Sync Source Configuration" subtitle="Choose content sources to keep your knowledge base up to date." className="settings-v4-panel--span-3">
        <div className="settings-v4-split-settings">
          <div>
            <RuntimeSwitch runtime={runtime} switchKey="websiteSync" onChange={updateToggle} title="Public Website" caption="Sync FAQs and content from your website." />
            <RuntimeSwitch runtime={runtime} switchKey="googleDriveSync" onChange={updateToggle} title="Internal Docs (Google Drive)" caption="Sync from Drive folders and documents." />
            <RuntimeSwitch runtime={runtime} switchKey="manualSync" onChange={updateToggle} title="Property Manuals (PDF)" caption="Extract and sync from uploaded manuals." />
            <RuntimeSwitch runtime={runtime} switchKey="helpdeskSync" onChange={updateToggle} title="Helpdesk Tickets" caption="Sync resolved tickets as articles." />
          </div>
          <div className="settings-v4-sync-list">
            {['Website', 'Google Drive', 'Manuals', 'Helpdesk'].map((item, index) => (
              <SyncStatusRow key={item} icon={[Globe2, Cloud, FileText, MessageSquare][index]} title={item} meta={`Synced ${index + 1} hours ago`} />
            ))}
            <TinyButton onClick={() => runAction('Knowledge sync started')}>Sync Now</TinyButton>
          </div>
        </div>
      </SettingsPanel>

      <SettingsPanel title="Search Weighting" subtitle="Prioritize content sources in AI responses." className="settings-v4-panel--kb-quarter">
        {[
          ['Knowledge Base Articles', 60],
          ['Website Content', 20],
          ['Property Manuals', 10],
          ['Helpdesk Tickets', 10],
        ].map(([label, value]) => (
          <div className="settings-v4-weight-row" key={label as string}>
            <span>{label}</span>
            <MiniProgress value={value as number} />
            <strong>{value}%</strong>
          </div>
        ))}
      </SettingsPanel>

      <SettingsPanel title="Multilingual Support" subtitle="Manage supported languages." className="settings-v4-panel--kb-quarter">
        <RuntimeSwitch runtime={runtime} switchKey="englishEnabled" onChange={updateToggle} title="English (Default)" />
        <RuntimeSwitch runtime={runtime} switchKey="spanishEnabled" onChange={updateToggle} title="Espanol (Spanish)" />
        <RuntimeSwitch runtime={runtime} switchKey="frenchEnabled" onChange={updateToggle} title="Francais (French)" />
        <RuntimeSwitch runtime={runtime} switchKey="germanEnabled" onChange={updateToggle} title="Deutsch (German)" />
        <TinyButton onClick={() => runAction('Language manager opened')}><Plus size={14} /> Add Language</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Approval Workflow" subtitle="Require review before publishing." className="settings-v4-panel--kb-quarter">
        <RuntimeSwitch runtime={runtime} switchKey="requireApproval" onChange={updateToggle} title="Require Approval" />
        <RuntimeField label="Default Approver" runtime={runtime} fieldKey="faqApprover" onChange={updateField} variant="select" options={['Knowledge Manager', 'Piter Garcia', 'Operations Lead']} />
        <RuntimeSwitch runtime={runtime} switchKey="autoExpireArticles" onChange={updateToggle} title="Auto-expire Articles" />
        <RuntimeField label="Review Every" runtime={runtime} fieldKey="reviewEvery" onChange={updateField} variant="select" options={['30 days', '60 days', '90 days']} />
      </SettingsPanel>

      <SettingsPanel title="Content Usage Analytics" subtitle="Track how your content is used." className="settings-v4-panel--kb-quarter">
        <div className="settings-v4-knowledge-metrics">
          {[
            ['Searches This Month', '1,248'],
            ['Top Viewed Articles', '152'],
            ['No Results Searches', '38'],
            ['Helpful Responses', '87%'],
          ].map(([label, value]) => <KnowledgeMetricRow key={label} label={label} value={value} />)}
        </div>
        <TinyButton onClick={() => runAction('Knowledge analytics opened')}>View Full Analytics</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Knowledge Sources" subtitle="Manage and monitor all connected knowledge sources." className="settings-v4-panel--span-3">
        <div className="settings-v4-table-wrap">
          <table className="settings-v4-table">
            <thead><tr><th>Source</th><th>Type</th><th>Status</th><th>Last Sync</th><th>Articles</th><th>Actions</th></tr></thead>
            <tbody>
              {[
                ['MLADIS Website', 'Website', 'Connected', '2 hours ago', '24'],
                ['Operations Docs', 'Google Drive', 'Connected', '1 hour ago', '32'],
                ['Guest Manual 2026', 'PDF Manual', 'Connected', '3 hours ago', '18'],
              ].map((row) => (
                <tr key={row[0]}>
                  {row.slice(0, 5).map((cell, index) => <td key={`${row[0]}-${cell}`}>{index === 2 ? <StatusBadge>{cell}</StatusBadge> : cell}</td>)}
                  <td>
                    <span className="settings-v4-source-actions">
                      <TinyButton onClick={() => runAction(`${row[0]} source refreshed`)}><RotateCcw size={14} /></TinyButton>
                      <TinyButton onClick={() => runAction(`${row[0]} source edited`)}><Settings2 size={14} /></TinyButton>
                      <TinyButton onClick={() => runAction(`${row[0]} source opened`)}><MoreVertical size={14} /></TinyButton>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SettingsPanel>
    </>
  );
}

function AccessTab({ runtime, updateField, updateToggle, runAction }: SettingsTabProps) {
  const roles = [
    ['Admin', 'Full access', 'green'],
    ['Operator', 'Daily operations', 'blue'],
    ['Finance', 'Financial access', 'violet'],
    ['Support', 'Limited access', 'orange'],
  ];

  return (
    <>
      <SettingsPanel title="User Role Matrix" subtitle="Review and manage role permissions across all modules." className="settings-v4-panel--span-2">
        <div className="settings-v4-table-wrap">
          <table className="settings-v4-table settings-v4-role-table">
            <thead><tr><th>Role</th><th>Reservations</th><th>Guests</th><th>Properties</th><th>Payments</th><th>Reports</th><th>Settings</th><th>Users</th></tr></thead>
            <tbody>
              {roles.map(([role, meta, tone], rowIndex) => (
                <tr key={role}>
                  <td><IconBadge icon={Users} tone={tone as Tone} /><strong>{role}</strong><small>{meta}</small></td>
                  {Array.from({ length: 7 }).map((_, index) => <td key={`${role}-${index}`}>{rowIndex === 0 || index < 5 ? <CheckCircle2 size={14} /> : '-'}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <TinyButton onClick={() => runAction('Custom roles manager opened')}>Manage custom roles <ExternalLink size={14} /></TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Invite Team Member" subtitle="Send an invitation to join your team.">
        <RuntimeField label="Full name" runtime={runtime} fieldKey="inviteName" onChange={updateField} placeholder="e.g. Maria Rodriguez" />
        <RuntimeField label="Email address" runtime={runtime} fieldKey="inviteEmail" onChange={updateField} variant="email" placeholder="e.g. maria@company.com" />
        <RuntimeField label="Role" runtime={runtime} fieldKey="inviteRole" onChange={updateField} variant="select" options={selectOptions.roles} />
        <RuntimeSwitch runtime={runtime} switchKey="sendInvitationEmail" onChange={updateToggle} title="Send invitation email" />
        <TinyButton tone="blue" onClick={() => runAction('Invitation prepared for sending')}><Send size={14} /> Send Invitation</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Permissions Overview" subtitle="Configure fine-grained permissions for each role.">
        <RuntimeField label="Select role" runtime={runtime} fieldKey="selectedRole" onChange={updateField} variant="select" options={selectOptions.roles} />
        {['Reservations', 'Guests', 'Properties', 'Payments', 'Reports', 'Settings', 'Users'].map((label, index) => (
          <ListCard key={label} icon={[CalendarDays, Users, Building2, CreditCard, ListChecks, Settings2, Users][index]} title={label} meta={['Create, edit, cancel reservations', 'View and manage guest profiles', 'View and manage properties', 'Process payments and refunds', 'View operational reports', 'View basic settings', 'Manage users and roles'][index]} status={<StatusBadge tone={index < 5 ? 'green' : 'slate'}>{index < 5 ? 'Full Access' : 'No Access'}</StatusBadge>} />
        ))}
      </SettingsPanel>

      <SettingsPanel title="Module Access" subtitle="Enable or restrict access to modules by role.">
        <RuntimeField label="Select role" runtime={runtime} fieldKey="selectedRole" onChange={updateField} variant="select" options={selectOptions.roles} />
        {[
          ['Command Center', 'commandCenterAccess'],
          ['Reservations', 'reservationsAccess'],
          ['Calendar', 'calendarAccess'],
          ['Guests', 'guestsAccess'],
          ['Properties', 'propertiesAccess'],
          ['Maintenance', 'maintenanceAccess'],
          ['Payments', 'paymentsAccess'],
          ['Reports', 'reportsAccess'],
          ['Settings', 'settingsAccess'],
          ['Users', 'usersAccess'],
        ].map(([label, key]) => <RuntimeSwitch key={key} runtime={runtime} switchKey={key} onChange={updateToggle} title={label} />)}
      </SettingsPanel>

      <SettingsPanel title="Roles" subtitle="Manage user roles in your organization.">
        {[
          ['Admin', 'Full system access', '3 users', 'green'],
          ['Operator', 'Handles daily operations', '18 users', 'blue'],
          ['Finance', 'Manages billing & finances', '5 users', 'violet'],
          ['Support', 'Provides customer support', '4 users', 'orange'],
          ['Housekeeping', 'Property & cleaning tasks', '6 users', 'slate'],
        ].map(([title, meta, users, tone]) => <ListCard key={title} icon={Users} title={title} meta={meta} tone={tone as Tone} status={<span>{users}</span>} action={<ChevronRight size={14} />} />)}
        <TinyButton onClick={() => runAction('New role form opened')}><Plus size={14} /> Create new role</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Audit Access" subtitle="Review user activity and access logs.">
        <RuntimeField label="Date range" runtime={runtime} fieldKey="auditDateRange" onChange={updateField} />
        <RuntimeField label="User" runtime={runtime} fieldKey="auditUser" onChange={updateField} variant="select" options={['All users', 'Piter Garcia', 'Maria Rodriguez']} />
        <RuntimeField label="Action" runtime={runtime} fieldKey="auditAction" onChange={updateField} variant="select" options={['All actions', 'Login', 'Export', 'Edit']} />
        <TinyButton onClick={() => runAction('Audit log opened')}><FileText size={14} /> View audit log</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Login Security" subtitle="Configure password and session policies.">
        <RuntimeField label="Password minimum length" runtime={runtime} fieldKey="passwordLength" onChange={updateField} variant="number" suffix="characters" />
        <RuntimeField label="Session timeout" runtime={runtime} fieldKey="sessionTimeout" onChange={updateField} variant="number" suffix="minutes" />
        <RuntimeSwitch runtime={runtime} switchKey="strongPasswords" onChange={updateToggle} title="Require strong passwords" />
      </SettingsPanel>

      <SettingsPanel title="Two-Factor Authentication" subtitle="Enforce 2FA for enhanced account security.">
        <RuntimeSwitch runtime={runtime} switchKey="require2fa" onChange={updateToggle} title="Require 2FA for all users" />
        <RuntimeSwitch runtime={runtime} switchKey="smsFallback" onChange={updateToggle} title="Allow SMS fallback" />
        <StatusBadge>Enforced</StatusBadge>
        <TinyButton onClick={() => runAction('2FA setup guide opened')}>View 2FA setup guide <ExternalLink size={14} /></TinyButton>
      </SettingsPanel>
    </>
  );
}

function IntegrationsTab({ settings, runtime, updateSection, updateField, updateToggle, runAction }: SettingsTabProps) {
  const integrations: Array<{ title: string; meta: string; status: string; tone: Tone; icon: LucideIcon; key: string }> = [
    { title: 'Airbnb', meta: 'Synced 2 mins ago', status: 'Connected', tone: 'rose', icon: Home, key: 'airbnbIcal' },
    { title: 'PayPal', meta: 'Synced 3 mins ago', status: 'Connected', tone: 'blue', icon: Wallet, key: 'paypalConnected' },
    { title: 'Stripe', meta: 'Synced 3 mins ago', status: 'Connected', tone: 'violet', icon: CreditCard, key: 'stripeConnected' },
    { title: 'SMS Service (Twilio)', meta: 'Synced 4 mins ago', status: 'Connected', tone: 'rose', icon: MessageSquare, key: 'smsConnected' },
    { title: 'Google Calendar', meta: 'Synced 1 min ago', status: 'Connected', tone: 'green', icon: CalendarDays, key: 'googleCalendar' },
    { title: 'Analytics (Google Analytics)', meta: 'Synced 6 mins ago', status: 'Connected', tone: 'orange', icon: ListChecks, key: 'analyticsConnected' },
    { title: 'Email Service (SendGrid)', meta: 'Synced 5 mins ago', status: 'Connected', tone: 'blue', icon: Mail, key: 'emailConnected' },
  ];

  return (
    <>
      <SettingsPanel title="Connected Integrations" subtitle="Manage and monitor your connected apps and services." className="settings-v4-panel--span-3">
        <div className="settings-v4-integration-grid">
          {integrations.map(({ title, meta, status, tone, icon, key }) => (
            <ListCard
              key={title}
              icon={icon}
              title={title}
              meta={meta}
              tone={tone}
              status={<StatusBadge>{status}</StatusBadge>}
              action={<><TinyButton onClick={() => runAction(`${title} integration opened`)}>Manage</TinyButton><button className="settings-v4-icon-button" type="button" onClick={() => key === 'googleCalendar' ? updateSection('integrations', { googleCalendar: !settings.integrations.googleCalendar }) : updateToggle(key, !getToggle(runtime, key))}><MoreVertical size={14} /></button></>}
            />
          ))}
          <button className="settings-v4-add-card" type="button" onClick={() => runAction('Add integration picker opened')}>
            <Plus size={18} />
            <strong>Add Integration</strong>
            <small>Connect a new app or service</small>
            <ChevronRight size={14} />
          </button>
        </div>
      </SettingsPanel>

      <SettingsPanel title="API Keys" subtitle="Manage API keys for developer access." action={<TinyButton onClick={() => runAction('New API key generated')}><Plus size={14} /> Generate New Key</TinyButton>}>
        {[
          ['MLADIS API (Production)', 'sk_live_************************4b7f', 'Created Jun 5, 2026'],
          ['MLADIS API (Testing)', 'sk_test_************************1d9e', 'Created May 28, 2026'],
          ['Read Only Access', 'sk_live_************************8e2c', 'Created May 10, 2026'],
        ].map(([title, key, meta]) => <ListCard key={title} icon={KeyRound} title={title} meta={`${key} | ${meta}`} status={<StatusBadge>Active</StatusBadge>} action={<button type="button" className="settings-v4-icon-button" onClick={() => navigator.clipboard?.writeText(key)}><Copy size={14} /></button>} />)}
        <TinyButton onClick={() => runAction('API key vault opened')}>View all API keys</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Webhook Configuration" subtitle="Receive real-time notifications.">
        <ListCard title="Reservation Events" meta={getField(runtime, 'webhookReservationUrl')} status={<StatusBadge>Active</StatusBadge>} />
        <ListCard title="Payment Events" meta={getField(runtime, 'webhookPaymentUrl')} status={<StatusBadge>Active</StatusBadge>} />
        <ListCard title="Guest Events" meta={getField(runtime, 'webhookGuestUrl')} status={<StatusBadge>Active</StatusBadge>} />
        <TinyButton onClick={() => runAction('Webhook form opened')}><Plus size={14} /> Add Webhook</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Sync Status" subtitle="Real-time synchronization overview.">
        {[
          ['Calendar Sync', '2 mins ago'],
          ['Listing Sync', '3 mins ago'],
          ['Pricing Sync', '4 mins ago'],
          ['Availability Sync', '2 mins ago'],
          ['Guest Data Sync', '1 min ago'],
        ].map(([title, meta]) => <SyncStatusRow key={title} icon={Server} title={title} meta={meta} />)}
        <TinyButton onClick={() => runAction('Sync logs opened')}>View sync logs</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Integration Tests" subtitle="Test your integration connections." className="settings-v4-panel--span-1">
        {[
          ['Airbnb Connection', 'Test API connectivity and permissions', Home],
          ['Stripe Connection', 'Test payment processing', CreditCard],
          ['Email Service', 'Test email delivery', Mail],
          ['SMS Service', 'Test SMS delivery', MessageSquare],
        ].map(([title, meta, Icon]) => (
          <IntegrationTestRow
            key={title as string}
            icon={Icon as LucideIcon}
            title={title as string}
            meta={meta as string}
            onClick={() => runAction(`${title} test queued`)}
          />
        ))}
        <TinyButton onClick={() => runAction('All integration tests queued')}>Run all tests</TinyButton>
      </SettingsPanel>

      <SettingsPanel title="Automation & Integration Rules" subtitle="Automate workflows between your apps." className="settings-v4-panel--span-2" action={<TinyButton onClick={() => runAction('New automation rule opened')}><Plus size={14} /> New Rule</TinyButton>}>
        <div className="settings-v4-rule-list">
          {[
            ['Sync new reservations to Google Calendar', 'When reservation is confirmed', 'syncNewReservations'],
            ['Send email on new booking', 'When reservation is confirmed', 'sendEmailOnBooking'],
            ['Update availability on all channels', 'When reservation is created or updated', 'googleCalendar'],
            ['Low occupancy alert', 'When occupancy falls below 20%', 'lowOccupancyAlert'],
          ].map(([title, meta, key]) => <RuntimeSwitch key={key} runtime={runtime} switchKey={key} onChange={updateToggle} title={title} caption={meta} />)}
        </div>
        <TinyButton onClick={() => runAction('Automation rules opened')}>View all automation rules</TinyButton>
      </SettingsPanel>
    </>
  );
}

function renderTab(props: SettingsTabProps & { activeTab: SettingsSectionId }) {
  switch (props.activeTab) {
    case 'branding':
      return <BrandingTab {...props} />;
    case 'booking':
      return <BookingDefaultsTab {...props} />;
    case 'finance':
      return <FinanceTab {...props} />;
    case 'notifications':
      return <NotificationsTab {...props} />;
    case 'ai':
      return <AiTab {...props} />;
    case 'knowledge':
      return <KnowledgeTab {...props} />;
    case 'access':
      return <AccessTab {...props} />;
    case 'integrations':
      return <IntegrationsTab {...props} />;
    case 'business':
    default:
      return <BusinessProfileTab {...props} />;
  }
}

export function OpsSettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsSectionId>('business');
  const [settings, setSettings] = useState<SettingsDraft>(() => loadLocalState(SETTINGS_STORAGE_KEY, defaultSettings));
  const [runtime, setRuntime] = useState<RuntimeState>(() => loadLocalState(SETTINGS_RUNTIME_KEY, defaultRuntime));
  const [statusMessage, setStatusMessage] = useState('Ready');

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    window.localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
    window.localStorage.setItem(SETTINGS_RUNTIME_KEY, JSON.stringify(runtime));
  }, [settings, runtime]);

  function markDirty() {
    setStatusMessage('Unsaved local changes');
  }

  function updateSection<K extends keyof SettingsDraft>(section: K, patch: Partial<SettingsDraft[K]>) {
    setSettings((current) => ({
      ...current,
      [section]: {
        ...current[section],
        ...patch,
      },
    }));
    markDirty();
  }

  function updateField(key: string, value: string) {
    setRuntime((current) => ({ ...current, fields: { ...current.fields, [key]: value } }));
    markDirty();
  }

  function updateToggle(key: string, active: boolean) {
    setRuntime((current) => ({ ...current, toggles: { ...current.toggles, [key]: active } }));
    markDirty();
  }

  function updateCheck(key: string, checked: boolean) {
    setRuntime((current) => ({ ...current, checks: { ...current.checks, [key]: checked } }));
    markDirty();
  }

  function runAction(message: string) {
    setStatusMessage(message);
  }

  function createBackup() {
    const backupPayload = buildSettingsPayload(settings, runtime, 'settings-backup');
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(SETTINGS_BACKUP_KEY, JSON.stringify(backupPayload));
    }
    downloadJson(backupPayload, `mladis-settings-backup-${new Date().toISOString().slice(0, 10)}.json`);
    setStatusMessage('Backup created locally');
  }

  const tabProps: SettingsTabProps = {
    settings,
    runtime,
    updateSection,
    updateField,
    updateToggle,
    updateCheck,
    runAction,
  };

  return (
    <main className="dashboard-content settings-v4-page">
      <section className="settings-v4-titlebar">
        <div>
          <h1>Settings</h1>
          <p>Configure your business, booking rules, notifications, AI, and integrations.</p>
        </div>
        {statusMessage !== 'Ready' && (
          <div className="settings-v4-titlebar__actions settings-v4-titlebar__actions--status-only">
            <span className="settings-v4-status-pill">{statusMessage}</span>
          </div>
        )}
      </section>

      <nav className="settings-v4-tabs" aria-label="Settings sections">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              aria-current={activeTab === tab.id ? 'page' : undefined}
              className={activeTab === tab.id ? 'is-active' : ''}
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={15} />
              {tab.label}
            </button>
          );
        })}
      </nav>

      <div className="settings-v4-layout">
        <div className={`settings-v4-main settings-v4-main--dense settings-v4-main--${activeTab}`}>
          {renderTab({ ...tabProps, activeTab })}
        </div>
        <SideRail onBackup={createBackup} activeTab={activeTab} onAction={runAction} />
      </div>
    </main>
  );
}
