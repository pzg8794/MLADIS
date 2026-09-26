import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import {
  ArrowUpRight,
  Bot,
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  CreditCard,
  FileText,
  Globe2,
  HeartHandshake,
  Headphones,
  Home,
  Info,
  LogIn,
  MapPin,
  Menu,
  MessageSquareText,
  PencilLine,
  ReceiptText,
  ShieldCheck,
  ShoppingBag,
  Sparkles,
  Star,
  Utensils,
  Users,
  Waves,
  Clock,
  X,
  XCircle,
  DollarSign,
  Music2,
  Send,
} from 'lucide-react';
import { AccountFactory } from '../../application/AccountFactory';
import { PublicSiteFactory } from '../../application/PublicSiteFactory';
import { AgentReplyPresentation } from '../../domain/agent';
import {
  AccountReservation,
  AccountSnapshot,
  AgentAccessStatus,
  PublicSiteSnapshot,
  PublicStay,
  PublicUserContext,
  ReservationRequestDraft,
  type ReservationRequestField,
} from '../../domain/models';
import { getConfiguredLogoUrl } from '../helpers/brand';
import { formatStayName } from '../helpers/stayNames';

type Language = 'en' | 'es';
type LegalKind = 'business' | 'privacy' | 'terms' | 'data-deletion';

const SANTO_DOMINGO_NORTE_MAP_URL = 'https://www.google.com/maps?q=Santo+Domingo+Norte%2C+Dominican+Republic&output=embed';
const SANTO_DOMINGO_NORTE_SEARCH_URL = 'https://www.google.com/maps/search/?api=1&query=Santo+Domingo+Norte%2C+Dominican+Republic';
const AGENT_MESSAGE_LIMIT = 500;
const AGENT_MESSAGE_PLACEHOLDER = 'Type your message here...';

type AdminReservation = {
  id: number;
  guestName: string;
  guestEmail: string;
  stayName: string;
  checkIn: string;
  checkOut: string;
  guests: number;
  status: 'pending' | 'confirmed' | 'cancelled';
  phone: string;
  message: string;
  totalDisplay: string;
  createdAt: string;
};

type AdminSnapshot = {
  reservations: AdminReservation[];
  totalRevenue: string;
  pendingCount: number;
  confirmedCount: number;
  cancelledCount: number;
};

type ApiAgentAccess = {
  agent_key?: string;
  agent_name?: string;
  is_authenticated: boolean;
  question_limit: number;
  questions_used: number;
  remaining_questions: number | null;
  can_ask: boolean;
  login_url: string;
};

type ApiAccountUserContext = {
  authenticated?: boolean;
  profile?: {
    name?: string;
    email?: string;
    phone?: string;
    is_staff?: boolean;
    is_superuser?: boolean;
  } | null;
  is_staff?: boolean;
  is_superuser?: boolean;
  agent?: ApiAgentAccess;
};

type CreatedReservationRequest = {
  id: number;
  request_key: string;
  guest_name: string;
  email: string;
  phone: string;
  item_id: number | null;
  stay_name: string;
  check_in: string;
  check_out: string;
  nights: number;
  guests: number;
  coupon_code: string;
  display_subtotal: string;
  display_discount: string;
  display_deposit: string;
  display_reservation_payment: string;
  display_total: string;
  reservation_payment_cents: number;
  deposit_checkout_url: string;
  reservation_payment_checkout_url: string;
  payment_confirmation_url: string;
  property_rules_url: string;
  damage_terms_url: string;
  property_rules_title: string;
  property_rules_version: string;
  property_rules_body?: string;
  damage_terms_title: string;
  damage_terms_version: string;
  damage_terms_body?: string;
  documents_accepted: boolean;
  admin_test: boolean;
};

type DepositCheckoutResponse = {
  ok?: boolean;
  message?: string;
  checkout_url?: string;
  deposit_id?: number;
  provider?: string;
  status?: string;
  errors?: Record<string, string[]>;
};

type AgentRuleIcon = 'agent' | 'area' | 'calendar' | 'document' | 'guest' | 'payment' | 'star' | 'shield';

type AgentRuleCard = {
  title: string;
  description: string;
  icon: AgentRuleIcon;
  tone: 'blue' | 'green' | 'orange' | 'teal' | 'violet';
};

type AgentRuleTab = {
  id: string;
  label: string;
  cards: AgentRuleCard[];
};

function agentAccessFromApi(data?: ApiAgentAccess, fallback?: AgentAccessStatus): AgentAccessStatus {
  return new AgentAccessStatus(
    Boolean(data?.is_authenticated ?? fallback?.isAuthenticated ?? false),
    data?.question_limit ?? fallback?.questionLimit ?? 5,
    data?.questions_used ?? fallback?.questionsUsed ?? 0,
    data?.remaining_questions ?? fallback?.remainingQuestions ?? null,
    Boolean(data?.can_ask ?? fallback?.canAsk ?? false),
    data?.login_url ?? fallback?.loginUrl ?? '/accounts/login/?next=/accounts/',
    data?.agent_key ?? fallback?.agentKey ?? 'public-booking-agent',
    data?.agent_name ?? fallback?.agentName ?? 'Booking agent',
  );
}

function userContextFromApi(data: ApiAccountUserContext, fallbackAgent: AgentAccessStatus): PublicUserContext {
  const agent = agentAccessFromApi(data.agent, fallbackAgent);
  if (!data.profile || data.authenticated === false) {
    return PublicUserContext.anonymous(agent);
  }
  return new PublicUserContext(
    'authenticated',
    data.profile.name || data.profile.email || '',
    data.profile.email || '',
    data.profile.phone || '',
    Boolean(data.profile.is_staff || data.profile.is_superuser || data.is_staff || data.is_superuser),
    agent,
  );
}

const copy = {
  en: {
    navStays: 'Stays',
    navArea: 'Area',
    navBooking: 'Book',
    navAbout: 'About',
    navAccount: 'Account',
    signIn: 'Sign in',
    heroTitle: 'Vacation stays in Santo Domingo Norte.',
    heroText:
      'Apartments in Santo Domingo Norte, near Colinas del Arroyo II, Jacobo Majluta, malls, and restaurants.',
    primary: 'Start booking',
    secondary: 'Explore stays',
    proof: 'Guest rating',
    staysTitle: 'Choose your stay',
    staysText: 'Photos, property details, rules, and direct inquiries in one place.',
    areaTitle: 'More than a place to sleep',
    areaText:
      'Beyond the room: city errands, food, malls, beach-day options, and hosted support from Santo Domingo Norte.',
    bookingTitle: 'Ask first, then book with confidence',
    bookingText: '',
    agentTitle: 'Booking agent',
    agentText: 'Ask about availability, guest count, house rules, transportation, or which apartment fits your group.',
    formTitle: 'Start a reservation request',
    formText: 'Choose a stay, dates, and guest count. MLADIS will confirm availability and send the complete quote. No payment is collected with this inquiry.',
    pricePreview: 'Quote',
    stayPayment: 'Availability',
    highlights: 'Top guest highlights',
    rules: 'Apartment rules',
    mission: 'Travel with mission',
    signInToAskAgent: 'Sign in to ask agent',
    agentAction: 'Ask agent',
    inquiryFallback: 'Ask through the inquiry form',
    availabilityChoose: 'Choose a stay and dates to check availability.',
    availabilityChecking: 'Checking dates…',
    availabilityUnknown: 'Availability could not be checked just now. You can still request these dates; MLADIS will verify them before confirming.',
    availabilityNeedsConfirmation: 'No conflict appears in MLADIS records. MLADIS must confirm against the current booking-channel calendar before booking.',
    availabilityUnavailable: 'These dates are not currently available for this stay.',
    quoteRequest: 'A complete, date-specific quote is provided by MLADIS after the inquiry. Fees and deposit treatment are confirmed before booking.',
    noPaymentAtInquiry: 'No payment or deposit is collected when you send an inquiry.',
    agentLimitReached: 'Question limit reached',
    agentLimitText: 'You have reached the current question limit for this account.',
    submit: 'Send request',
    autofill: 'Use my account info',
    required: 'required',
    depositTitle: 'Make secure deposit',
    depositText: 'Your inquiry is received. MLADIS will confirm availability, fees, deposit treatment, and booking terms before any payment.',
    depositAction: 'Make secure deposit',
    paymentTitle: 'Hold reservation payment',
    paymentText: 'No payment is collected with an inquiry. Payment timing and any deposit are confirmed before a reservation.',
    paymentAction: 'Hold reservation payment',
    details: 'Details',
    airbnb: 'Airbnb',
    gallery: 'Gallery',
    aboutTitle: 'Hosted stays for Santo Domingo days, family plans, and island time.',
    aboutText:
      'MLADIS gives guests a practical Santo Domingo Norte base with warm host support, access to city errands, mall corridors, restaurants, and day-trip beaches like Juan Dolio or Boca Chica.',
    aboutMission:
      'We want every stay to support a larger mission: better guest care, local opportunity, and charity work for children, education, and families who need support.',
    accountTitle: 'Your reservations',
    accountText: 'Manage requests, watch cancellation windows, review invoices, and keep your booking details in one place.',
  },
  es: {
    navStays: 'Estadías',
    navArea: 'Zona',
    navBooking: 'Reservar',
    navAbout: 'Nosotros',
    navAccount: 'Cuenta',
    signIn: 'Entrar',
    heroTitle: 'Estadías en Santo Domingo Norte.',
    heroText:
      'Apartamentos en Santo Domingo Norte, cerca de Colinas del Arroyo II, Jacobo Majluta, plazas y restaurantes.',
    primary: 'Empezar reserva',
    secondary: 'Ver estadías',
    proof: 'Valoración de huéspedes',
    staysTitle: 'Elige tu estadía',
    staysText: 'Fotos, detalles, reglas y consultas directas en un solo lugar.',
    areaTitle: 'Más que un lugar para dormir',
    areaText:
      'Más allá del cuarto: diligencias, comida, plazas, playa y apoyo anfitrión desde Santo Domingo Norte.',
    bookingTitle: 'Pregunta primero y reserva con confianza',
    bookingText: '',
    agentTitle: 'Agente de reservas',
    agentText: 'Pregunta por disponibilidad, cantidad de huéspedes, reglas, transporte o cuál apartamento te conviene.',
    formTitle: 'Iniciar solicitud de reserva',
    formText: 'Elige el apartamento, las fechas y la cantidad de huéspedes. MLADIS confirmará la disponibilidad y enviará la cotización completa. No se cobra al enviar esta consulta.',
    pricePreview: 'Cotización',
    stayPayment: 'Disponibilidad',
    highlights: 'Comentarios destacados',
    rules: 'Reglas del apartamento',
    mission: 'Viaja con misión',
    signInToAskAgent: 'Entra para preguntar al agente',
    agentAction: 'Preguntar',
    inquiryFallback: 'Consultar mediante el formulario',
    availabilityChoose: 'Elige un apartamento y fechas para consultar disponibilidad.',
    availabilityChecking: 'Consultando las fechas…',
    availabilityUnknown: 'No pudimos consultar la disponibilidad ahora. Puedes solicitar estas fechas; MLADIS las verificará antes de confirmar.',
    availabilityNeedsConfirmation: 'No aparece un conflicto en los registros de MLADIS. MLADIS debe confirmar con el calendario actual del canal de reservas antes de reservar.',
    availabilityUnavailable: 'Estas fechas no están disponibles actualmente para este apartamento.',
    quoteRequest: 'MLADIS enviará la cotización completa para esas fechas después de recibir la consulta. Los cargos y el depósito se confirman antes de reservar.',
    noPaymentAtInquiry: 'No se cobra ningún pago ni depósito al enviar una consulta.',
    agentLimitReached: 'Límite de preguntas alcanzado',
    agentLimitText: 'Has alcanzado el límite actual de preguntas para esta cuenta.',
    submit: 'Enviar solicitud',
    autofill: 'Usar mi cuenta',
    required: 'requerido',
    depositTitle: 'Hacer depósito seguro',
    depositText: 'Recibimos tu consulta. MLADIS confirmará disponibilidad, cargos, depósito y condiciones antes de cualquier pago.',
    depositAction: 'Hacer depósito seguro',
    paymentTitle: 'Retener pago de reserva',
    paymentText: 'No se cobra al enviar una consulta. MLADIS confirmará el momento de pago y cualquier depósito antes de reservar.',
    paymentAction: 'Retener pago de reserva',
    details: 'Detalles',
    airbnb: 'Airbnb',
    gallery: 'Galería',
    aboutTitle: 'Estadías anfitrionas para Santo Domingo, planes familiares y tiempo de isla.',
    aboutText:
      'MLADIS ofrece una base práctica en Santo Domingo Norte con apoyo anfitrión, acceso a diligencias, plazas, restaurantes y playas como Juan Dolio o Boca Chica.',
    aboutMission:
      'Queremos que cada estadía apoye una misión mayor: mejor servicio, oportunidades locales y ayuda para niños, educación y familias que necesitan apoyo.',
    accountTitle: 'Tus reservas',
    accountText: 'Maneja solicitudes, ventanas de cancelación, facturas y detalles de reserva en un solo lugar.',
  },
};

function csrfToken() {
  const meta = document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.content;
  if (meta) return meta;
  const cookie = document.cookie.split('; ').find((row) => row.startsWith('csrftoken='));
  return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
}

function campaignUtmPayload() {
  const params = new URLSearchParams(window.location.search);
  const values: Record<string, string> = {};
  for (const key of ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_id']) {
    const value = params.get(key)?.trim() ?? '';
    if (/^[A-Za-z0-9._-]{1,100}$/.test(value)
      && value.replace(/\D/g, '').length < 7
      && !/^\d{4}[-_.]?\d{2}[-_.]?\d{2}$/.test(value)) values[key] = value;
  }
  return values;
}

function recordMarketingEvent(eventName: 'landing_visit' | 'inquiry_start', itemSlug = '') {
  const payload = { event_name: eventName, item_slug: itemSlug, ...campaignUtmPayload() };
  return fetch('/api/marketing/events/', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
    body: JSON.stringify(payload),
  }).catch(() => undefined);
}

function currentPath() {
  return window.location.pathname;
}

function stayPath(stay: PublicStay) {
  return new URL(stay.detailUrl, window.location.origin).pathname;
}

function findStayByPath(snapshot: PublicSiteSnapshot) {
  const path = currentPath();
  const slug = path.match(/^\/stays\/([^/]+)\/?$/)?.[1];
  if (!slug) return null;
  return snapshot.stays.find((stay) => stay.slug === slug || stayPath(stay) === path) ?? null;
}

function legalKindFromPath(): LegalKind | null {
  const path = currentPath();
  if (path.startsWith('/business')) return 'business';
  if (path.startsWith('/privacy')) return 'privacy';
  if (path.startsWith('/terms')) return 'terms';
  if (path.startsWith('/data-deletion')) return 'data-deletion';
  return null;
}

function scrollToBookingSection() {
  const bookingSection = document.getElementById('booking');
  if (!bookingSection) return false;
  bookingSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  window.setTimeout(() => bookingSection.scrollIntoView({ block: 'start' }), 120);
  return true;
}

function handleBookingLinkClick(event: { preventDefault: () => void }) {
  if (!scrollToBookingSection()) return;
  event.preventDefault();
  window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}#booking`);
}

function formatDate(value: string) {
  if (!value) return '';
  const [year, month, day] = value.split('-').map(Number);
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }).format(
    new Date(Date.UTC(year, month - 1, day)),
  );
}

function nightsBetween(checkIn: string, checkOut: string) {
  if (!checkIn || !checkOut) return 1;
  const start = new Date(`${checkIn}T00:00:00Z`).getTime();
  const end = new Date(`${checkOut}T00:00:00Z`).getTime();
  const nights = Math.round((end - start) / 86_400_000);
  return Math.max(nights || 1, 1);
}

function normaliseStayStatLabel(stat: string) {
  return stat.replace(/\bbedrooms\b/gi, 'bedrooms').replace(/\bbaths\b/gi, 'baths');
}

function stayGalleryImages(stay: PublicStay) {
  const gallery = stay.gallery.length
    ? stay.gallery
    : [{ imageUrl: stay.imageUrl, altText: stay.name, caption: stay.name }];
  const seen = new Set<string>();
  return gallery.filter((image) => {
    if (!image.imageUrl || seen.has(image.imageUrl)) return false;
    seen.add(image.imageUrl);
    return true;
  });
}

function useRotatingList<T>(items: T[], intervalMs = 5000) {
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    if (items.length <= 1) return undefined;
    const intervalId = window.setInterval(() => {
      setOffset((current) => (current + 1) % items.length);
    }, intervalMs);
    return () => window.clearInterval(intervalId);
  }, [intervalMs, items.length]);

  useEffect(() => {
    setOffset(0);
  }, [items]);

  return useMemo(() => {
    if (items.length <= 1) return items;
    return items.map((_, index) => items[(index + offset) % items.length]);
  }, [items, offset]);
}

function StayImageRotator({
  stay,
  linkUrl,
  className = '',
  defaultRotating = true,
  showControls = false,
  intervalMs = 5000,
}: {
  stay: PublicStay;
  linkUrl: string;
  className?: string;
  defaultRotating?: boolean;
  showControls?: boolean;
  intervalMs?: number;
}) {
  const images = useMemo(() => stayGalleryImages(stay), [stay]);
  const [index, setIndex] = useState(0);
  const [rotating, setRotating] = useState(defaultRotating && images.length > 1);
  const image = images[index] ?? images[0];

  useEffect(() => {
    setIndex(0);
    setRotating(defaultRotating && images.length > 1);
  }, [defaultRotating, images.length, stay.id]);

  useEffect(() => {
    if (!rotating || images.length <= 1) return undefined;
    const intervalId = window.setInterval(() => {
      setIndex((current) => (current + 1) % images.length);
    }, intervalMs);
    return () => window.clearInterval(intervalId);
  }, [images.length, intervalMs, rotating]);

  return (
    <div className={`public-stay-rotator ${className}`}>
      <a className="public-stay-rotator__link" href={linkUrl} aria-label={`View ${stay.name}`}>
        <img src={image?.imageUrl || stay.imageUrl} alt={image?.altText || stay.name} loading="eager" />
      </a>
      {showControls && images.length > 1 && (
        <button
          type="button"
          className="public-stay-rotator__toggle"
          onClick={() => setRotating((current) => !current)}
          aria-pressed={rotating}
        >
          {rotating ? 'Pause photos' : 'Rotate photos'}
        </button>
      )}
    </div>
  );
}

function PublicSiteSkeleton() {
  return (
    <main className="public-site">
      <section className="public-hero public-skeleton">
        <span />
        <strong />
        <p />
      </section>
    </main>
  );
}

function PublicNav({
  snapshot,
  userContext,
  language,
  navOpen,
  onLanguageChange,
  onNavToggle,
  onSignOutStart,
}: {
  snapshot: PublicSiteSnapshot;
  userContext: PublicUserContext;
  language: Language;
  navOpen: boolean;
  onLanguageChange: (language: Language) => void;
  onNavToggle: () => void;
  onSignOutStart: () => void;
}) {
  const t = copy[language];
  const isAuthenticated = userContext.isAuthenticated;
  const showAdmin = isAuthenticated && userContext.isStaff === true;
  const logoUrl = snapshot.logoUrl || getConfiguredLogoUrl();

  return (
    <header className="public-nav">
      <div className="public-nav__topline">
        <button
          type="button"
          className="public-nav__toggle"
          aria-label={navOpen ? 'Collapse menu' : 'Expand menu'}
          aria-expanded={navOpen}
          onClick={onNavToggle}
        >
          <Menu size={20} />
        </button>
        <a className="public-brand" href="/">
          <img src={logoUrl} alt={snapshot.siteName} />
          <strong>{snapshot.siteName}</strong>
        </a>
      </div>
      <nav aria-label="Primary">
        <a href="/#stays"><Home size={17} /><span>{t.navStays}</span></a>
        <a href="/#area"><MapPin size={17} /><span>{t.navArea}</span></a>
        <a href="/about/"><HeartHandshake size={17} /><span>{t.navAbout}</span></a>
        <a href="#booking" onClick={handleBookingLinkClick}><CalendarDays size={17} /><span>{t.navBooking}</span></a>
      </nav>
      <div className="public-nav__actions">
        <button type="button" onClick={() => onLanguageChange(language === 'en' ? 'es' : 'en')}>
          <Globe2 size={16} /> <span>{language === 'en' ? 'ES' : 'EN'}</span>
        </button>

        {isAuthenticated ? (
          <>
            <a href="/accounts/" title={userContext.displayName ? `Signed in as ${userContext.displayName}` : 'Signed in'}>
              <Home size={16} /> <span>{t.navAccount}</span>
            </a>
            {showAdmin && (
              <a href="/ops/admin/">
                <ShieldCheck size={16} /> <span>Admin</span>
              </a>
            )}
            <form method="post" action="/accounts/logout/" className="public-nav-logout" onSubmit={onSignOutStart}>
              <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken()} />
              <button type="submit">
                <LogIn size={16} /> <span>Sign out</span>
              </button>
            </form>
          </>
        ) : (
          <>
            <a href="/accounts/login/?next=/accounts/">
              <LogIn size={16} /> <span>{userContext.status === 'checking' ? 'Checking...' : t.signIn}</span>
            </a>
          </>
        )}
      </div>
    </header>
  );
}

function StayCard({ stay, language }: { stay: PublicStay; language: Language }) {
  const t = copy[language];
  const displayName = stay.name.replace(/^MLADIS\s+/i, '');
  return (
    <article className="public-stay-card">
      <StayImageRotator stay={stay} linkUrl={stay.detailUrl} className="public-stay-rotator--card" />
      <div className="public-stay-card__body">
        <div>
          <h3>{displayName}</h3>
          <p>{stay.headline || stay.description}</p>
        </div>
        <div className="public-stay-card__stats">
          {stay.statList.slice(0, 3).map((stat) => <span key={stat}>{stat}</span>)}
        </div>
        <div className="public-stay-card__actions">
          <a href={stay.detailUrl}>{t.details}</a>
          <a href={stay.airbnbUrl} target="_blank" rel="noreferrer">{t.airbnb}</a>
        </div>
      </div>
    </article>
  );
}

function RotatingStayGrid({ stays, language }: { stays: PublicStay[]; language: Language }) {
  const rotatedStays = useRotatingList(stays, 5000);
  return (
    <div className="public-stay-grid public-stay-grid--rotating">
      {rotatedStays.map((stay) => <StayCard stay={stay} language={language} key={stay.id} />)}
    </div>
  );
}

function LegacyAgentPrompt({
  stay,
  token,
  agent,
  language,
}: {
  stay?: PublicStay | null;
  token: string;
  agent: AgentAccessStatus;
  language: Language;
}) {
  const [agentMessage, setAgentMessage] = useState('');
  const [agentReply, setAgentReply] = useState('');
  const [agentBusy, setAgentBusy] = useState(false);
  const [agentAccess, setAgentAccess] = useState(agent);
  const t = copy[language];
  const replyPresentation = useMemo(() => AgentReplyPresentation.fromText(agentReply), [agentReply]);

  useEffect(() => {
    setAgentAccess(agent);
  }, [agent]);

  async function askAgent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!agentAccess.canAsk) return;
    const message = agentMessage.trim();
    if (!message) return;
    setAgentBusy(true);
    setAgentReply('');
    try {
      const response = await fetch('/api/agent/', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': token,
        },
        body: JSON.stringify({
          message,
          item_id: stay?.id,
          session_id: window.sessionStorage.getItem('mladis_agent_session') || undefined,
        }),
      });
      const data = await response.json() as { reply?: string; error?: string; session_id?: string; agent?: ApiAgentAccess };
      if (data.session_id) window.sessionStorage.setItem('mladis_agent_session', data.session_id);
      if (data.agent) {
        setAgentAccess(agentAccessFromApi(data.agent, agentAccess));
      }
      setAgentReply(data.reply || data.error || 'The agent did not return a reply yet.');
    } catch {
      setAgentReply('I could not reach the agent API from this browser session.');
    } finally {
      setAgentBusy(false);
    }
  }

  if (!agentAccess.isAuthenticated) {
    return (
      <div className="public-agent-prompt">
        <p>{stay ? `Ask about ${stay.name} using the inquiry form.` : 'Use the inquiry form to ask about dates and stays.'}</p>
        <a className="public-agent-action" href="#booking-request-form"><Send size={15} /> {t.inquiryFallback}</a>
      </div>
    );
  }

  if (!agentAccess.canAsk) {
    return (
      <div className="public-agent-prompt">
        <p className="public-agent-reply">{t.agentLimitText}</p>
        <a className="public-agent-action" href="#booking-request-form"><Send size={15} /> {t.inquiryFallback}</a>
      </div>
    );
  }

  return (
    <>
      <form className="public-agent-prompt" onSubmit={askAgent}>
        <label>
          <MessageSquareText size={16} />
          <textarea
            name="message"
            value={agentMessage}
            onChange={(event) => setAgentMessage(event.target.value)}
            maxLength={AGENT_MESSAGE_LIMIT}
            placeholder={AGENT_MESSAGE_PLACEHOLDER}
          />
        </label>
        <small className="public-agent-prompt__count">{agentMessage.length} / {AGENT_MESSAGE_LIMIT}</small>
        <button type="submit" disabled={agentBusy}><Send size={15} /> {agentBusy ? 'Asking...' : t.agentAction}</button>
      </form>
      {agentReply && (
        <div className="public-agent-reply" role="status" aria-live="polite">
          {replyPresentation.blocks.map((block, index) => {
            if (block.kind === 'heading') {
              return <h4 key={`${block.kind}-${index}`}>{block.text}</h4>;
            }
            if (block.kind === 'step') {
              return (
                <div className="public-agent-reply__item" key={`${block.kind}-${index}`}>
                  <span aria-hidden="true">{block.marker}</span>
                  <p>{block.text}</p>
                </div>
              );
            }
            if (block.kind === 'bullet') {
              return (
                <div className="public-agent-reply__item public-agent-reply__item--bullet" key={`${block.kind}-${index}`}>
                  <span aria-hidden="true">•</span>
                  <p>{block.text}</p>
                </div>
              );
            }
            return <p key={`${block.kind}-${index}`}>{block.text}</p>;
          })}
        </div>
      )}
    </>
  );
}

function AgentBookingSection({
  snapshot,
  userContext,
  stay,
  language,
}: {
  snapshot: PublicSiteSnapshot;
  userContext: PublicUserContext;
  stay?: PublicStay | null;
  language: Language;
}) {
  const t = copy[language];
  const token = csrfToken();
  const submitted = new URLSearchParams(window.location.search).get('submitted') === '1';
  const [draft, setDraft] = useState(() => ReservationRequestDraft.forStay(stay?.id));
  const [requestMessage, setRequestMessage] = useState('');
  const [requestErrors, setRequestErrors] = useState<string[]>([]);
  const [requestBusy, setRequestBusy] = useState(false);
  const [availability, setAvailability] = useState<'idle' | 'checking' | 'confirmation_required' | 'unavailable' | 'unknown'>('idle');
  const trackedInquiryStarts = useRef(new Set<string>());
  const selectedStay = useMemo(
    () => snapshot.stays.find((availableStay) => String(availableStay.id) === draft.item) ?? null,
    [draft.item, snapshot.stays],
  );
  const guestLimit = selectedStay?.maxGuests ?? null;
  const guestsNumber = Math.max(Number(draft.guests) || 1, 1);
  const overGuestLimit = Boolean(guestLimit && guestsNumber > guestLimit);

  useEffect(() => {
    setDraft((currentDraft) => {
      const itemValue = stay?.id ? String(stay.id) : currentDraft.item;
      const nextStay = snapshot.stays.find((availableStay) => String(availableStay.id) === itemValue) ?? null;
      return currentDraft.withField('item', itemValue);
    });
  }, [snapshot.stays, stay?.id]);

  useEffect(() => {
    if (!selectedStay || !draft.checkIn || !draft.checkOut || draft.checkOut <= draft.checkIn || overGuestLimit) {
      setAvailability('idle');
      return undefined;
    }
    const controller = new AbortController();
    setAvailability('checking');
    const timer = window.setTimeout(() => {
      const params = new URLSearchParams({
        slug: selectedStay.slug,
        check_in: draft.checkIn,
        check_out: draft.checkOut,
        guests: String(guestsNumber),
      });
      fetch(`/api/public/stay-availability/?${params}`, { credentials: 'same-origin', signal: controller.signal })
        .then(async (response) => {
          const data = await response.json() as { ok?: boolean; availability_status?: string };
          if (!response.ok || !data.ok) throw new Error('availability unavailable');
          setAvailability(data.availability_status === 'unavailable' ? 'unavailable' : 'confirmation_required');
        })
        .catch((error: unknown) => {
          if (!(error instanceof DOMException && error.name === 'AbortError')) setAvailability('unknown');
        });
    }, 250);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [selectedStay, draft.checkIn, draft.checkOut, guestsNumber, overGuestLimit]);

  function updateDraft(field: ReservationRequestField, value: string) {
    setDraft((currentDraft) => {
      const nextDraft = currentDraft.withField(field, value);
      if (field !== 'item') return nextDraft;
      const nextStay = snapshot.stays.find((availableStay) => String(availableStay.id) === value) ?? null;
      return nextDraft;
    });
  }

  function autofillAccount() {
    setDraft((currentDraft) => currentDraft.withAccount(userContext));
  }

  function trackInquiryStart() {
    if (!selectedStay || trackedInquiryStarts.current.has(selectedStay.slug)) return;
    trackedInquiryStarts.current.add(selectedStay.slug);
    void recordMarketingEvent('inquiry_start', selectedStay.slug);
  }

  async function submitReservationRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setRequestBusy(true);
    setRequestErrors([]);
    setRequestMessage('');
    try {
      const response = await fetch('/inquiries/', {
        method: 'POST',
        credentials: 'include',
        headers: {
          Accept: 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': token,
        },
        body: draft.toFormData(token),
      });
      const data = await response.json() as {
        ok?: boolean;
        message?: string;
        inquiry?: CreatedReservationRequest;
        errors?: Record<string, string[]>;
      };
      if (!response.ok || !data.ok || !data.inquiry) {
        const errors = Object.entries(data.errors || {}).flatMap(([field, values]) => values.map((value) => `${field}: ${value}`));
        setRequestErrors(errors.length ? errors : ['Could not send this request yet. Check the required fields.']);
        return;
      }
      setRequestMessage(`${data.message || 'Request received.'} Reference: ${data.inquiry.request_key}.`);
    } catch {
      setRequestErrors(['Could not reach the reservation request service from this browser session.']);
    } finally {
      setRequestBusy(false);
    }
  }

  return (
    <section id="booking" className="public-section public-booking">
      <div className="public-booking__grid">
        <article className="public-agent-card">
          <header className="public-agent-card__header">
            <div>
              <h2>{t.bookingTitle}</h2>
              <p>Our local experts are here to help you plan the perfect stay.</p>
            </div>
            <Headphones size={19} />
          </header>
          <span><Bot size={19} /> {t.agentTitle}</span>
          <p>{t.agentText}</p>
          <LegacyAgentPrompt stay={stay} token={token} agent={userContext.agent} language={language} />
          {stay && (
            <div className="public-agent-card__rules">
              <AgentRulesTabs stay={stay} language={language} />
            </div>
          )}
        </article>

        <div className="public-booking__form-stack">
        <form className="public-booking-form" method="post" action="/inquiries/" onSubmit={submitReservationRequest} onFocusCapture={trackInquiryStart}>
          <div id="booking-request-form" />
          <input type="hidden" name="csrfmiddlewaretoken" value={token} />
          <div className="public-booking-form__header">
            <div>
              <h3>{t.formTitle}</h3>
              <p>{t.formText}</p>
            </div>
            {userContext.isAuthenticated && (
              <button className="public-booking-form__autofill" type="button" onClick={autofillAccount}>
                <PencilLine size={15} /> {t.autofill}
              </button>
            )}
          </div>
          {submitted && <p className="public-success">Your inquiry was received. MLADIS will verify availability and send the complete quote before booking.</p>}
          {requestMessage && <p className="public-success">{requestMessage}</p>}
          {requestErrors.length > 0 && (
            <div className="public-error-list">
              {requestErrors.map((error) => <p key={error}>{error}</p>)}
            </div>
          )}
          <label>
            Stay
            <select name="item" value={draft.item} onChange={(event) => updateDraft('item', event.target.value)}>
              <option value="">Flexible / help me choose</option>
              {snapshot.stays.map((availableStay) => (
                <option value={availableStay.id} key={availableStay.id}>{availableStay.name.replace(/^MLADIS\s+/i, '')}</option>
              ))}
            </select>
          </label>
          <div className="public-form-row">
            <label><span className="public-label-text">Name <span className="public-required" aria-label={t.required}>*</span></span><input name="guest_name" value={draft.guestName} onChange={(event) => updateDraft('guest_name', event.target.value)} required /></label>
            <label>Phone <span className="public-optional">optional now</span><input name="phone" value={draft.phone} onChange={(event) => updateDraft('phone', event.target.value)} autoComplete="tel" /></label>
          </div>
          <label><span className="public-label-text">Email <span className="public-required" aria-label={t.required}>*</span></span><input type="email" name="email" value={draft.email} onChange={(event) => updateDraft('email', event.target.value)} autoComplete="email" required /></label>
          <div className="public-form-row">
            <label><span className="public-label-text">Check in <span className="public-required" aria-label={t.required}>*</span></span><input type="date" name="check_in" value={draft.checkIn} onChange={(event) => updateDraft('check_in', event.target.value)} required /></label>
            <label><span className="public-label-text">Check out <span className="public-required" aria-label={t.required}>*</span></span><input type="date" name="check_out" value={draft.checkOut} onChange={(event) => updateDraft('check_out', event.target.value)} required /></label>
          </div>
          <div className="public-form-row">
            <label><span className="public-label-text"><Users size={15} /> Guests <span className="public-required" aria-label={t.required}>*</span></span><input type="number" name="guests" min="1" max={guestLimit ?? undefined} value={draft.guests} onChange={(event) => updateDraft('guests', event.target.value)} required /></label>
          </div>
          <div className="public-price-preview" aria-live="polite">
            <div className="public-price-preview__box public-price-preview__box--quote">
              <span>{t.pricePreview}</span>
              <strong>{t.quoteRequest}</strong>
              <small>{t.noPaymentAtInquiry}</small>
            </div>
            <div className="public-price-preview__box public-price-preview__box--payment">
              <span>{t.stayPayment}</span>
              <strong>{availability === 'checking' ? t.availabilityChecking : availability === 'confirmation_required' ? t.availabilityNeedsConfirmation : availability === 'unavailable' ? t.availabilityUnavailable : availability === 'unknown' ? t.availabilityUnknown : t.availabilityChoose}</strong>
              <small>Availability is rechecked when your inquiry is submitted.</small>
            </div>
          </div>
          {overGuestLimit && (
            <p className="public-deposit-modal__error" role="alert">This stay allows up to {guestLimit} guests.</p>
          )}
          <label>Notes<textarea name="message" rows={3} value={draft.message} onChange={(event) => updateDraft('message', event.target.value)} /></label>
          <button type="submit" disabled={requestBusy || overGuestLimit || availability === 'checking' || availability === 'unavailable'}><Send size={16} /> {requestBusy ? 'Sending...' : t.submit}</button>
        </form>
        </div>
      </div>
    </section>
  );
}

function DepositHoldModal({
  request,
  token,
  onClose,
}: {
  request: CreatedReservationRequest;
  token: string;
  onClose: () => void;
  language: Language;
}) {
  type PaymentProvider = 'stripe' | 'paypal';
  const [provider, setProvider] = useState<PaymentProvider>('stripe');
  const [paymentChoice, setPaymentChoice] = useState<'deposit' | 'combined'>('deposit');
  const [acceptedDocuments, setAcceptedDocuments] = useState({
    rules: request.documents_accepted,
    terms: request.documents_accepted,
  });
  const [isStartingCheckout, setIsStartingCheckout] = useState(false);
  const [checkoutError, setCheckoutError] = useState('');
  const processingToday = paymentChoice === 'combined' ? request.display_total : request.display_deposit;
  const laterCharge = paymentChoice === 'combined' ? '$0.00 USD' : request.display_reservation_payment;
  const allDocumentsAccepted = acceptedDocuments.rules && acceptedDocuments.terms;
  const checkoutUrl = paymentChoice === 'combined'
    ? request.reservation_payment_checkout_url || '/payments/checkout/'
    : request.deposit_checkout_url || '/deposits/checkout/';

  function selectPaymentChoice(nextChoice: 'deposit' | 'combined') {
    setPaymentChoice(nextChoice);
    if (nextChoice === 'combined' && provider === 'paypal') {
      setProvider('stripe');
    }
  }

  function selectProvider(nextProvider: PaymentProvider) {
    setProvider(nextProvider);
    if (nextProvider === 'paypal') {
      setPaymentChoice('deposit');
    }
  }

  function recordAcceptedDocument(kind: 'rules' | 'terms') {
    setAcceptedDocuments((current) => ({ ...current, [kind]: true }));
  }

  function normalizeAcceptedDocumentKind(kind?: string): 'rules' | 'terms' | null {
    if (kind === 'property_rules' || kind === 'rules') return 'rules';
    if (kind === 'damage_terms' || kind === 'terms') return 'terms';
    return null;
  }

  useEffect(() => {
    function applyStoredAcceptance() {
      try {
        const raw = window.sessionStorage.getItem('mladis-policy-accepted');
        if (!raw) return;
        window.sessionStorage.removeItem('mladis-policy-accepted');
        const payload = JSON.parse(raw) as { kind?: string };
        const kind = normalizeAcceptedDocumentKind(payload.kind);
        if (kind) recordAcceptedDocument(kind);
      } catch {
        window.sessionStorage.removeItem('mladis-policy-accepted');
      }
    }

    function handleAcceptedMessage(event: MessageEvent) {
      if (event.origin !== window.location.origin) return;
      const payload = event.data as { type?: string; kind?: string };
      if (!payload || payload.type !== 'mladis-policy-accepted') return;
      const kind = normalizeAcceptedDocumentKind(payload.kind);
      if (kind) recordAcceptedDocument(kind);
    }

    applyStoredAcceptance();
    window.addEventListener('message', handleAcceptedMessage);
    window.addEventListener('focus', applyStoredAcceptance);
    return () => {
      window.removeEventListener('message', handleAcceptedMessage);
      window.removeEventListener('focus', applyStoredAcceptance);
    };
  }, []);

  function openPolicyDocument(kind: 'rules' | 'terms') {
    const url = kind === 'rules' ? request.property_rules_url : request.damage_terms_url;
    const opened = window.open(
      url,
      `mladis-${kind}-document`,
      'popup=yes,width=1280,height=860',
    );
    if (!opened) {
      window.location.href = url;
    }
  }

  async function startDepositCheckout(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsStartingCheckout(true);
    setCheckoutError('');
    const formData = new FormData(event.currentTarget);
    formData.set('payment_provider', provider);
    formData.set('payment_choice', paymentChoice);
    formData.set('property_rules_accepted', acceptedDocuments.rules ? '1' : '');
    formData.set('damage_terms_accepted', acceptedDocuments.terms ? '1' : '');

    try {
      const response = await fetch(checkoutUrl, {
        method: 'POST',
        credentials: 'include',
        headers: {
          Accept: 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': token,
        },
        body: formData,
      });
      const data = await response.json() as DepositCheckoutResponse;
      if (response.ok && data.ok && data.checkout_url) {
        window.location.assign(data.checkout_url);
        return;
      }
      const validationErrors = Object.entries(data.errors || {})
        .flatMap(([field, values]) => values.map((value) => `${field}: ${value}`));
      setCheckoutError(validationErrors[0] || data.message || 'The secure deposit checkout could not be started.');
    } catch {
      setCheckoutError('Could not reach the secure deposit checkout service from this browser session.');
    } finally {
      setIsStartingCheckout(false);
    }
  }

  return (
    <div className="public-modal-backdrop" role="presentation">
      <article className="public-deposit-modal public-payment-modal" role="dialog" aria-modal="true" aria-labelledby="deposit-modal-title">
        <header className="public-deposit-modal__header">
          <div className="public-deposit-modal__title-row">
            <div>
              <span className="public-deposit-modal__request"><FileText size={17} /> {request.request_key}</span>
              <div className="public-deposit-modal__headline">
                <span className="public-deposit-modal__lock"><ShieldCheck size={26} /></span>
                <div>
                  <h2 id="deposit-modal-title">Complete secure payment</h2>
                  <p>Your request is saved. Choose how you&apos;d like to pay and review the property rules before continuing.</p>
                </div>
              </div>
            </div>
          </div>
          <button type="button" onClick={onClose} aria-label="Close deposit form">
            <X size={24} />
          </button>
        </header>
        <div className="public-deposit-modal__summary">
          <div className="public-deposit-modal__summary-card public-deposit-modal__summary-card--stay">
            <Home size={22} />
            <span>Stay</span>
            <strong>{formatStayName(request.stay_name)}</strong>
          </div>
          <div className="public-deposit-modal__summary-card public-deposit-modal__summary-card--dates">
            <CalendarDays size={22} />
            <span>Dates</span>
            <strong>{request.check_in} to {request.check_out}</strong>
          </div>
          <div className="public-deposit-modal__summary-card public-deposit-modal__summary-card--guests">
            <Users size={22} />
            <span>Guests</span>
            <strong>{request.guests}</strong>
          </div>
          <div className="public-deposit-modal__summary-card public-deposit-modal__summary-card--deposit">
            <ShieldCheck size={22} />
            <span>Damage deposit</span>
            <strong>{request.display_deposit}</strong>
          </div>
          <div className="public-deposit-modal__summary-card public-deposit-modal__summary-card--charge">
            <ReceiptText size={22} />
            <span>Stay charge</span>
            <strong>{request.display_reservation_payment}</strong>
          </div>
        </div>
        <form className="public-deposit-modal__form" method="post" action={checkoutUrl} onSubmit={startDepositCheckout}>
          <input type="hidden" name="csrfmiddlewaretoken" value={token} />
          <input type="hidden" name="inquiry_id" value={request.id} />
          <input type="hidden" name="item" value={request.item_id ?? ''} />
          <input type="hidden" name="guest_name" value={request.guest_name} />
          <input type="hidden" name="email" value={request.email} />
          <input type="hidden" name="payment_choice" value={paymentChoice} />
          <input type="hidden" name="property_rules_accepted" value={acceptedDocuments.rules ? '1' : ''} />
          <input type="hidden" name="damage_terms_accepted" value={acceptedDocuments.terms ? '1' : ''} />
          <div className="public-deposit-modal__grid">
            <div className="public-deposit-modal__column">
              <section className="public-deposit-modal__section">
                <h3><span>1</span>Choose how you want to pay</h3>
                <button
                  type="button"
                  className={`public-deposit-modal__option${paymentChoice === 'deposit' ? ' public-deposit-modal__option--selected' : ''}`}
                  onClick={() => selectPaymentChoice('deposit')}
                >
                  <input type="radio" checked={paymentChoice === 'deposit'} readOnly />
                  <span className="public-deposit-modal__option-icon"><ShieldCheck size={30} /></span>
                  <span className="public-deposit-modal__option-copy"><strong>Pay deposit only now</strong><small>Hold the refundable damage deposit now. The stay charge will be collected later.</small></span>
                  <b className="public-deposit-modal__price-pill">{request.display_deposit}<small>today</small></b>
                </button>
                <button
                  type="button"
                  className={`public-deposit-modal__option${paymentChoice === 'combined' ? ' public-deposit-modal__option--selected' : ''}`}
                  onClick={() => selectPaymentChoice('combined')}
                >
                  <input type="radio" checked={paymentChoice === 'combined'} readOnly />
                  <span className="public-deposit-modal__option-icon public-deposit-modal__option-icon--purple"><CreditCard size={30} /></span>
                  <span className="public-deposit-modal__option-copy"><strong>Pay stay + deposit together</strong><small>Make one payment now to avoid paying twice.</small></span>
                  <b className="public-deposit-modal__price-pill public-deposit-modal__price-pill--purple">{request.display_total}<small>today</small></b>
                </button>
              </section>
              <section className="public-deposit-modal__section">
                <h3><span>2</span>Read and accept required documents</h3>
                <p className="public-deposit-modal__notice">You must open each document and accept it inside the document window before continuing.</p>
                <p className="public-deposit-modal__info"><Info size={16} /> This form updates automatically after you click Accept inside each document.</p>
                <button
                  type="button"
                  className="public-deposit-modal__doc-row"
                  onClick={() => openPolicyDocument('rules')}
                >
                  <FileText size={23} />
                  <span><strong>View {request.property_rules_title || 'Property Rules'} <ArrowUpRight size={15} /></strong><small>(opens in a new window)</small></span>
                  <b className={`public-deposit-modal__status${acceptedDocuments.rules ? ' public-deposit-modal__status--accepted' : ' public-deposit-modal__status--pending'}`}>
                    {acceptedDocuments.rules ? <CheckCircle2 size={14} /> : <XCircle size={14} />} {acceptedDocuments.rules ? 'Accepted' : 'Pending acceptance'}
                  </b>
                </button>
                <button
                  type="button"
                  className="public-deposit-modal__doc-row"
                  onClick={() => openPolicyDocument('terms')}
                >
                  <FileText size={23} />
                  <span><strong>View {request.damage_terms_title || 'Damage Deposit Hold Terms'} <ArrowUpRight size={15} /></strong><small>(opens in a new window)</small></span>
                  <b className={`public-deposit-modal__status${acceptedDocuments.terms ? ' public-deposit-modal__status--accepted' : ' public-deposit-modal__status--pending'}`}>
                    {acceptedDocuments.terms ? <CheckCircle2 size={14} /> : <XCircle size={14} />} {acceptedDocuments.terms ? 'Accepted' : 'Pending acceptance'}
                  </b>
                </button>
                <p className="public-deposit-modal__locked"><ShieldCheck size={15} /> Both documents must show Accepted to continue.</p>
              </section>
            </div>
            <div className="public-deposit-modal__column">
              <section className="public-deposit-modal__section public-deposit-modal__breakdown">
                <h3><CalendarDays size={20} />Payment breakdown</h3>
                <div>
                  <strong>You pay today</strong>
                  <p><span>Stay charge</span><b>{request.display_reservation_payment}</b></p>
                  <p><span>Damage deposit (refundable)</span><b>{request.display_deposit}</b></p>
                  <p className="public-deposit-modal__total"><span>{paymentChoice === 'combined' ? 'Authorized today in two holds' : 'Processing today'}</span><b>{processingToday}</b></p>
                </div>
                <div>
                  <strong>What gets charged later</strong>
                  <p><span>Stay charge</span><b>{laterCharge}</b></p>
                  <small>{paymentChoice === 'combined' ? 'After checkout, MLADIS records the stay hold and refundable deposit separately.' : 'Charged closer to check-in.'}</small>
                </div>
                <div className="public-deposit-modal__grand-total">
                  <span>Total if paid together</span><b>{request.display_total}</b>
                </div>
              </section>
              <section className="public-deposit-modal__section">
                <h3><span>3</span>Select payment method</h3>
                <label className={`public-deposit-modal__method${provider === 'stripe' ? ' public-deposit-modal__method--selected' : ''}`}>
                  <input type="radio" name="payment_provider" value="stripe" checked={provider === 'stripe'} onChange={() => selectProvider('stripe')} />
                  <span className="public-deposit-modal__brand-stack"><i>VISA</i><i className="public-deposit-modal__mc">**</i></span>
                  <strong>Card / wallet through Stripe</strong>
                  <small><CheckCircle2 size={12} /> Secure <em>Fast</em></small>
                </label>
                <label className={`public-deposit-modal__method${provider === 'paypal' ? ' public-deposit-modal__method--selected' : ''}`}>
                  <input type="radio" name="payment_provider" value="paypal" checked={provider === 'paypal'} onChange={() => selectProvider('paypal')} />
                  <span className="public-deposit-modal__paypal">P</span>
                  <strong>PayPal</strong>
                  <small><CheckCircle2 size={12} /> Secure</small>
                </label>
                <p className="public-deposit-modal__secure-note"><ShieldCheck size={15} /> Your payment is encrypted and securely processed.</p>
              </section>
            </div>
          </div>
          {checkoutError && <p className="public-deposit-modal__error" role="alert">{checkoutError}</p>}
          <footer className="public-deposit-modal__actions">
            <button type="button" onClick={onClose}>Back</button>
            <button type="submit" disabled={isStartingCheckout || !allDocumentsAccepted}>
              <ShieldCheck size={17} /> {isStartingCheckout ? 'Opening checkout...' : 'Continue to secure payment'}
            </button>
          </footer>
        </form>
        <p className="public-deposit-modal__powered">Secure • Trusted • Powered by MLADIS & Stripe</p>
      </article>
    </div>
  );
}

function AgentRulesTabs({ stay, language }: { stay: PublicStay; language: Language }) {
  const t = copy[language];
  const ruleFallbacks = useMemo(() => [
    { title: 'No parties or events', description: 'Keep the stay peaceful for the residential community and nearby neighbors.' },
    { title: 'No smoking indoors', description: 'Smoking is not allowed inside the apartment or shared indoor areas.' },
    { title: 'Registered guests only', description: 'Guest count must match the reservation unless MLADIS approves a change.' },
    { title: 'Respect quiet hours', description: 'Keep noise reasonable, especially late at night and in common areas.' },
    { title: 'Protect keys and locks', description: 'Report lost keys, codes, or access issues immediately so MLADIS can help.' },
    { title: 'Keep shared areas clean', description: 'Leave halls, parking, and common spaces ready for the next guest.' },
  ], []);
  const ruleSupplements = useMemo(() => [
    { title: 'Keep shared areas clean', description: 'Leave halls, parking, and common spaces ready for the next guest.' },
    { title: 'Ask before exceptions', description: 'Message MLADIS before bringing visitors, changing plans, or using amenities differently.' },
    { title: 'Report issues early', description: 'Send photos or details quickly if something breaks, leaks, or needs host attention.' },
  ], []);
  const rules = useMemo(() => {
    const sourceRules = stay.rules.length ? [...stay.rules, ...ruleSupplements] : ruleFallbacks;
    const seenTitles = new Set<string>();
    return sourceRules.filter((rule) => {
      const titleKey = rule.title.toLowerCase();
      if (seenTitles.has(titleKey)) return false;
      seenTitles.add(titleKey);
      return true;
    }).slice(0, 6);
  }, [ruleFallbacks, ruleSupplements, stay.rules]);
  const cardPages = useMemo<AgentRuleTab[]>(() => [
    {
      id: 'arrival-prep',
      label: 'Arrival prep',
      cards: [
        { title: 'Ask before booking', description: 'Use the inquiry form for stay, dates, and fit questions.', icon: 'agent', tone: 'teal' },
        { title: 'Correct guest count', description: 'Guest count controls pricing and must match the reservation.', icon: 'guest', tone: 'orange' },
        { title: 'Host review', description: 'MLADIS reviews requests before confirming details.', icon: 'document', tone: 'blue' },
        { title: 'Check-in timing', description: 'Plan arrival around confirmed instructions and account updates.', icon: 'calendar', tone: 'violet' },
        { title: 'ID and account ready', description: 'Keep your account details current before the reservation is finalized.', icon: 'document', tone: 'green' },
        { title: 'Arrival questions', description: 'Ask for practical arrival support before travel day.', icon: 'agent', tone: 'teal' },
      ],
    },
    {
      id: 'local-guidance',
      label: 'Local guidance',
      cards: [
        { title: 'Area context', description: 'Residential Sol Oriens V sits in Santo Domingo Norte near key errands.', icon: 'area', tone: 'orange' },
        { title: 'Transport planning', description: 'Ask about arrival routes, rides, and nearby stops before booking.', icon: 'agent', tone: 'teal' },
        { title: 'Beach-day options', description: 'Juan Dolio and nearby beach trips can be planned around the stay.', icon: 'star', tone: 'blue' },
        { title: 'Practical local tips', description: 'Get help with groceries, restaurants, and timing for your group.', icon: 'document', tone: 'green' },
        { title: 'Errand planning', description: 'Coordinate malls, pharmacies, and food stops around check-in timing.', icon: 'area', tone: 'violet' },
        { title: 'Neighborhood rhythm', description: 'Keep arrival and late-night movement considerate for residents.', icon: 'shield', tone: 'teal' },
      ],
    },
    {
      id: 'house-rules',
      label: language === 'es' ? t.rules : 'House rules',
      cards: rules.map((rule, index) => ({
        title: rule.title,
        description: rule.description,
        icon: index === 0 ? 'shield' : index === 1 ? 'payment' : index === 2 ? 'guest' : index === 3 ? 'calendar' : index === 4 ? 'document' : 'area',
        tone: index === 0 ? 'teal' : index === 1 ? 'blue' : index === 2 ? 'violet' : index === 3 ? 'green' : index === 4 ? 'orange' : 'teal',
      })),
    },
    {
      id: 'faqs',
      label: 'FAQs',
      cards: [
        { title: 'No inquiry payment', description: 'Sending an inquiry does not authorize a payment or deposit.', icon: 'payment', tone: 'blue' },
        { title: 'Terms before booking', description: 'MLADIS confirms the applicable deposit treatment and terms with the complete quote.', icon: 'shield', tone: 'teal' },
        { title: 'Host confirmation', description: 'An inquiry is not a confirmed reservation.', icon: 'document', tone: 'violet' },
        { title: 'Human support', description: 'Ask for practical help before the reservation is finalized.', icon: 'agent', tone: 'green' },
        { title: 'Cancellation windows', description: 'Review reservation dates and policy details before submitting.', icon: 'calendar', tone: 'orange' },
        { title: 'Messages stay saved', description: 'Important answers remain connected to the booking account.', icon: 'document', tone: 'blue' },
      ],
    },
  ], [language, rules, t.rules]);
  const [cardPageIndex, setCardPageIndex] = useState(0);
  const activePage = cardPages[cardPageIndex] ?? cardPages[0];

  const moveCards = (direction: -1 | 1) => {
    setCardPageIndex((current) => (current + direction + cardPages.length) % cardPages.length);
  };

  const iconFor = (icon: AgentRuleIcon) => {
    if (icon === 'agent') return <Bot size={18} />;
    if (icon === 'area') return <MapPin size={18} />;
    if (icon === 'calendar') return <CalendarDays size={18} />;
    if (icon === 'document') return <ReceiptText size={18} />;
    if (icon === 'guest') return <Users size={18} />;
    if (icon === 'payment') return <CreditCard size={18} />;
    if (icon === 'star') return <Star size={18} />;
    return <ShieldCheck size={18} />;
  };

  return (
    <article className="agent-rules-tabs" aria-label="Booking agent guidance">
      <div className="agent-rules-tabs__tablist" aria-label="Booking guidance card groups">
        {cardPages.map((tab, index) => (
          <button
            type="button"
            className={`agent-rules-tabs__tab${index === cardPageIndex ? ' is-active' : ''}`}
            onClick={() => setCardPageIndex(index)}
            aria-controls="agent-rules-panel"
            id={`agent-rules-tab-${tab.id}`}
            key={tab.id}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div
        className="agent-rules-tabs__panel"
        id="agent-rules-panel"
        aria-labelledby={`agent-rules-tab-${activePage.id}`}
      >
        <div className="agent-rules-tabs__cards">
          {activePage.cards.slice(0, 4).map((card) => (
            <article className={`agent-rules-tabs__card agent-rules-tabs__card--${card.tone}`} key={`${activePage.id}-${card.title}`}>
              <span>{iconFor(card.icon)}</span>
              <strong>{card.title}</strong>
              <p>{card.description}</p>
            </article>
          ))}
        </div>
      </div>
      <footer className="agent-rules-tabs__pager" aria-label="Booking guidance card pages">
        <button type="button" onClick={() => moveCards(-1)} aria-label="Previous booking guidance cards">
          <ChevronLeft size={17} />
        </button>
        <div>
          {cardPages.map((tab, index) => (
            <button
              type="button"
              className={index === cardPageIndex ? 'is-active' : ''}
              onClick={() => setCardPageIndex(index)}
              aria-label={`Show ${tab.label} cards`}
              key={`${tab.id}-dot`}
            />
          ))}
        </div>
        <button type="button" onClick={() => moveCards(1)} aria-label="Next booking guidance cards">
          <ChevronRight size={17} />
        </button>
      </footer>
    </article>
  );
}

function RulesBook({ stay, language, compact = false }: { stay: PublicStay; language: Language; compact?: boolean }) {
  const t = copy[language];
  const rules = (stay.rules.length ? stay.rules : [
    { title: 'No parties or events', description: 'Keep the stay peaceful for the residential community and nearby neighbors.' },
    { title: 'No smoking indoors', description: 'Smoking is not allowed inside the apartment or shared indoor areas.' },
    { title: 'Registered guests only', description: 'Guest count must match the reservation unless MLADIS approves a change.' },
    { title: 'Respect quiet hours', description: 'Keep noise reasonable, especially late at night and in common areas.' },
    { title: 'Protect keys and locks', description: 'Report lost keys, codes, or access issues immediately so the host can help.' },
  ]).slice(0, 6);
  const spreads = useMemo(() => [
    {
      leftTitle: language === 'es' ? t.rules : 'House rules',
      leftTone: 'green',
      leftItems: rules.slice(0, 3).map((rule) => ({ ...rule, icon: 'rule' })),
      rightTitle: 'Quiet stay rhythm',
      rightTone: 'teal',
      rightItems: rules.slice(3, 6).map((rule) => ({ ...rule, icon: 'shield' })),
    },
    {
      leftTitle: 'Availability & quote',
      leftTone: 'blue',
      leftItems: [
        { title: 'Choose dates', description: 'Check the dates and requested guest count for this stay.', icon: 'calendar' },
        { title: 'Request a complete quote', description: 'MLADIS confirms the full price and any applicable charges before booking.', icon: 'document' },
        { title: 'No payment with inquiry', description: 'Sending an inquiry does not create a payment or deposit hold.', icon: 'shield' },
      ],
      rightTitle: 'Before confirmation',
      rightTone: 'teal',
      rightItems: [
        { title: 'Availability review', description: 'Calendar availability is rechecked when MLADIS reviews the request.', icon: 'calendar' },
        { title: 'Terms confirmed', description: 'Applicable fees, deposit treatment, and terms are provided before booking.', icon: 'document' },
        { title: 'Host confirmation', description: 'An inquiry is not a confirmed reservation.', icon: 'agent' },
      ],
    },
    {
      leftTitle: 'Arrival prep',
      leftTone: 'indigo',
      leftItems: [
        { title: 'Ask before booking', description: 'Use the inquiry form for questions about the stay and dates.', icon: 'agent' },
        { title: 'Correct guest count', description: 'Guest count controls pricing and must match the reservation.', icon: 'guest' },
        { title: 'Host review', description: 'MLADIS reviews requests before confirming details.', icon: 'document' },
      ],
      rightTitle: 'Local guidance',
      rightTone: 'orange',
      rightItems: [
        { title: 'Malls and errands', description: 'Use the area guide for malls, restaurants, and Embassy-corridor errands.', icon: 'area' },
        { title: 'Beach-day options', description: 'Juan Dolio and nearby beach trips can be planned around the stay.', icon: 'area' },
        { title: 'Human support', description: 'Ask for practical help before the reservation is finalized.', icon: 'agent' },
      ],
    },
    {
      leftTitle: 'FAQs',
      leftTone: 'gold',
      leftItems: [
        { title: 'When do I pay?', description: 'MLADIS confirms payment timing and any deposit before a reservation is finalized.', icon: 'payment' },
        { title: 'Is this a reservation?', description: 'No. This form sends an inquiry; MLADIS must confirm the booking.', icon: 'shield' },
        { title: 'Can I ask a question?', description: 'Yes. Use the inquiry form and include your question.', icon: 'agent' },
      ],
      rightTitle: 'Booking fit',
      rightTone: 'indigo',
      rightItems: [
        { title: 'Guest count matters', description: 'Pricing and approval depend on the correct guest count.', icon: 'guest' },
        { title: 'Direct request record', description: 'Requests, invoices, and updates stay attached to your account.', icon: 'document' },
        { title: 'Host confirmation', description: 'MLADIS reviews each request before final confirmation.', icon: 'document' },
      ],
    },
  ], [language, rules, t.rules]);
  const [spreadIndex, setSpreadIndex] = useState(0);
  const spread = spreads[spreadIndex] ?? spreads[0];

  useEffect(() => {
    if (spreads.length <= 1) return undefined;
    const intervalId = window.setInterval(() => {
      setSpreadIndex((current) => (current + 1) % spreads.length);
    }, 15000);
    return () => window.clearInterval(intervalId);
  }, [spreads.length]);

  const iconFor = (icon: string) => {
    if (icon === 'guest') return <Users size={18} />;
    if (icon === 'payment') return <CreditCard size={18} />;
    if (icon === 'document') return <ReceiptText size={18} />;
    if (icon === 'agent') return <Bot size={18} />;
    if (icon === 'area') return <MapPin size={18} />;
    return <ShieldCheck size={18} />;
  };

  return (
    <article className={`rules-book${compact ? ' rules-book--compact' : ''}`}>
      <div className={`rules-book__page rules-book__page--${spread.leftTone}`}>
        <h3>{spread.leftTitle}</h3>
        {spread.leftItems.map((item) => (
          <p key={item.title}>
            {iconFor(item.icon)}
            <span className="rules-book__copy"><strong>{item.title}</strong><span>{item.description}</span></span>
          </p>
        ))}
      </div>
      <div className={`rules-book__page rules-book__page--${spread.rightTone}`}>
        <h3>{spread.rightTitle}</h3>
        {spread.rightItems.map((item) => (
          <p key={item.title}>
            {iconFor(item.icon)}
            <span className="rules-book__copy"><strong>{item.title}</strong><span>{item.description}</span></span>
          </p>
        ))}
      </div>
      <footer className="rules-book__pager" aria-label="Rules book pages">
        <button type="button" onClick={() => setSpreadIndex((current) => (current - 1 + spreads.length) % spreads.length)} aria-label="Previous rules page">
          <ChevronLeft size={17} />
        </button>
        {spreads.map((_, index) => (
          <button
            type="button"
            className={index === spreadIndex ? 'is-active' : ''}
            onClick={() => setSpreadIndex(index)}
            aria-label={`Rules page ${index + 1}`}
            key={index}
          >
            {index + 1}
          </button>
        ))}
        <button type="button" onClick={() => setSpreadIndex((current) => (current + 1) % spreads.length)} aria-label="Next rules page">
          <ChevronRight size={17} />
        </button>
        <span><Clock size={15} /> Auto-advances every 15 seconds</span>
      </footer>
    </article>
  );
}

function HomeAreaExperience({ snapshot, language }: { snapshot: PublicSiteSnapshot; language: Language }) {
  const t = copy[language];
  const tiles = useMemo(() => snapshot.areaTiles.slice(0, 4), [snapshot.areaTiles]);
  const rotatedTiles = useRotatingList(tiles, 5000);
  return (
    <section id="area" className="public-section public-home-v5-area">
      <div className="public-home-v5-area__copy">
        <h2>{t.areaTitle}</h2>
        <p>{t.areaText}</p>
        <div className="public-home-v5-area__cards">
          {rotatedTiles.map((tile) => (
            <article key={tile.title}>
              <img src={tile.imageUrl} alt={tile.title} />
              <h3>{tile.title}</h3>
              <p>{tile.caption}</p>
              <a href="#booking" onClick={handleBookingLinkClick} aria-label={`Ask about ${tile.title}`}>
                <ArrowUpRight size={15} />
              </a>
            </article>
          ))}
        </div>
      </div>
      <article className="public-home-v5-map-card public-home-v5-map-card--area">
        <div className="public-home-v5-map-card__header">
          <span><MapPin size={15} /> Santo Domingo Norte</span>
          <strong>Residential Sol Oriens V</strong>
          <a href={SANTO_DOMINGO_NORTE_SEARCH_URL} target="_blank" rel="noreferrer">Directions <ArrowUpRight size={14} /></a>
        </div>
        <iframe
          title="Residential Sol Oriens V area map"
          loading="lazy"
          allowFullScreen
          referrerPolicy="no-referrer-when-downgrade"
          src={SANTO_DOMINGO_NORTE_MAP_URL}
        />
        <div className="public-home-v5-map-card__legend">
          <strong>Explore nearby</strong>
          <span><i className="public-home-v5-pin public-home-v5-pin--purple"><ShoppingBag size={13} /></i> Mall / Shopping</span>
          <span><i className="public-home-v5-pin public-home-v5-pin--orange"><Utensils size={13} /></i> Restaurant / Food</span>
          <span><i className="public-home-v5-pin public-home-v5-pin--blue"><Waves size={13} /></i> Beach</span>
          <span><i className="public-home-v5-pin public-home-v5-pin--green"><Music2 size={13} /></i> Entertainment</span>
          <a href="#area">View all places <ArrowUpRight size={14} /></a>
        </div>
      </article>
    </section>
  );
}

function HomeRulesMapSection({ snapshot }: { snapshot: PublicSiteSnapshot }) {
  const mapStays = snapshot.stays.slice(0, 3);
  return (
    <section id="rules" className="public-section public-home-v5-rules-map">
      <div className="public-home-v5-rules-copy">
        <p className="public-home-v5-rules-alert"><MapPin size={18} /> Santo Domingo Norte</p>
        <h2>Choose the right stay for your dates</h2>
        <p>Compare the available apartment options, request your dates, and receive availability confirmation and a complete quote from MLADIS.</p>
        <div className="public-home-v5-rules-promise" aria-label="Booking promise">
          <span><CalendarDays size={17} /> Date check</span>
          <span><FileText size={17} /> Complete quote</span>
          <span><Bot size={17} /> Host confirmation</span>
        </div>
      </div>
      <article className="public-home-v5-map-card public-home-v5-map-card--large">
        <div className="public-home-v5-map-card__header">
          <span><MapPin size={15} /> Santo Domingo Norte</span>
          <strong>Santo Domingo Norte, Dominican Republic</strong>
          <a className="public-home-v5-map-card__button" href={SANTO_DOMINGO_NORTE_SEARCH_URL} target="_blank" rel="noreferrer">View area map <ArrowUpRight size={14} /></a>
        </div>
        <iframe
          title="Sol Oriens V apartment location map"
          loading="eager"
          allowFullScreen
          referrerPolicy="no-referrer-when-downgrade"
          src={SANTO_DOMINGO_NORTE_MAP_URL}
        />
        <div className="public-home-v5-stay-markers">
          {mapStays.map((mapStay, index) => (
            <a className={`public-home-v5-stay-marker public-home-v5-stay-marker--${index + 1}`} href={mapStay.detailUrl} key={mapStay.id}>
              <img src={mapStay.imageUrl} alt={formatStayName(mapStay.name)} />
              <span>
                <strong>{formatStayName(mapStay.name)}</strong>
                <small>{mapStay.statList.slice(0, 2).map(normaliseStayStatLabel).join(' · ')}</small>
              </span>
            </a>
          ))}
        </div>
      </article>
    </section>
  );
}

function HomeExperience({ snapshot, userContext, language }: { snapshot: PublicSiteSnapshot; userContext: PublicUserContext; language: Language }) {
  const t = copy[language];
  const heroStay = snapshot.stays[0];
  const heroStats = [
    { label: 'Stays', value: String(snapshot.stays.length), icon: <Home size={18} />, tone: 'green' },
    { label: 'Inquiry first', value: 'No payment at inquiry', icon: <FileText size={18} />, tone: 'blue' },
    { label: 'Host confirmation', value: 'Required', icon: <Bot size={18} />, tone: 'indigo' },
  ];

  return (
    <>
      <section className="public-hero public-hero--v4 public-home-v5-hero">
        <div className="public-hero__copy">
          <h1>{t.heroTitle}</h1>
          <p>{t.heroText}</p>
          <div className="public-hero__actions">
            <a href="#booking" onClick={handleBookingLinkClick}>{t.primary} <ArrowUpRight size={17} /></a>
            <a href="#stays">{t.secondary}</a>
          </div>
        </div>
        {heroStay && (
          <article className="public-hero__stay public-home-v5-hero-card">
            <StayImageRotator stay={heroStay} linkUrl={heroStay.detailUrl} className="public-stay-rotator--hero" defaultRotating showControls={false} />
            <div className="public-home-v5-hero-card__body">
              <a className="public-home-v5-hero-card__title-link" href={heroStay.detailUrl}>
                <h2>{formatStayName(heroStay.name)}</h2>
              </a>
              <div className="public-hero__stay-metrics">
                {heroStay.statList.slice(0, 3).map((stat) => <b key={stat}>{normaliseStayStatLabel(stat)}</b>)}
              </div>
            </div>
          </article>
        )}
      </section>

      <section className="public-home-metrics public-home-metrics--strip" aria-label="Stay highlights">
        {heroStats.map((stat) => (
          <article className={`public-home-metric public-home-metric--${stat.tone}`} key={stat.label}>
            <span>{stat.icon}</span>
            <strong>{stat.value}</strong>
            <small>{stat.label}</small>
          </article>
        ))}
      </section>

      <section id="stays" className="public-section public-home-v5-stays">
        <div className="public-section__heading">
          <h2>{t.staysTitle}</h2>
          <p>{t.staysText}</p>
        </div>
        <RotatingStayGrid stays={snapshot.stays} language={language} />
      </section>

      {heroStay && <HomeRulesMapSection snapshot={snapshot} />}

      <AgentBookingSection snapshot={snapshot} userContext={userContext} stay={heroStay} language={language} />

      <HomeAreaExperience snapshot={snapshot} language={language} />

      <MissionSection snapshot={snapshot} language={language} />
    </>
  );
}

function AreaSection({ snapshot, language }: { snapshot: PublicSiteSnapshot; language: Language }) {
  const t = copy[language];
  return (
    <section id="area" className="public-section public-area">
      <div className="public-section__heading">
        <h2>{t.areaTitle}</h2>
        <p>{t.areaText}</p>
      </div>
      <div className="public-area-grid">
        {snapshot.areaTiles.map((tile) => (
          <article key={tile.title}>
            <img src={tile.imageUrl} alt={tile.title} />
            <div>
              <h3>{tile.title}</h3>
              <p>{tile.caption}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function MissionSection({ snapshot, language }: { snapshot: PublicSiteSnapshot; language: Language }) {
  const t = copy[language];
  return (
    <section className="public-section public-mission">
      <h2>{t.mission}</h2>
      <div>
        {snapshot.missionCauses.slice(0, 3).map((cause) => (
          <article key={cause.title}>
            <HeartHandshake size={20} />
            <strong>{cause.title}</strong>
            <p>{cause.description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function StayDetailExperience({ snapshot, userContext, stay, language }: { snapshot: PublicSiteSnapshot; userContext: PublicUserContext; stay: PublicStay; language: Language }) {
  const t = copy[language];
  const gallery = stay.gallery.length ? stay.gallery : [{ imageUrl: stay.imageUrl, altText: stay.name, caption: stay.name }];
  return (
    <>
      <section className="public-subhero public-stay-detail-hero">
        <div>
          <a className="public-subtle-link" href="/#stays">All stays</a>
          <h1>{stay.name}</h1>
          <p>{stay.description}</p>
          <div className="public-proof-strip">
            <span><MapPin size={16} /> {stay.location}</span>
            {stay.statList.slice(0, 4).map((stat) => <span key={stat}>{stat}</span>)}
            <span><ShieldCheck size={16} /> No payment with inquiry</span>
          </div>
          <div className="public-hero__actions">
            <a href="#booking" onClick={handleBookingLinkClick}>{t.primary} <ArrowUpRight size={17} /></a>
            <a href={stay.airbnbUrl} target="_blank" rel="noreferrer">View on Airbnb</a>
          </div>
        </div>
        <img src={stay.imageUrl} alt={stay.name} />
      </section>

      <section className="public-section public-gallery-section">
        <div className="public-section__heading">
          <h2>{t.gallery}</h2>
          <p>Apartment photos</p>
        </div>
        <div className="public-feature-gallery">
          {gallery.slice(0, 8).map((image) => (
            <figure key={image.imageUrl}>
              <img src={image.imageUrl} alt={image.altText} />
              <figcaption>{image.caption || image.altText}</figcaption>
            </figure>
          ))}
        </div>
      </section>

      {stay.highlights.length > 0 && <section className="public-section public-feature-shell">
        <div className="public-two-col">
          <article>
            <h3>{t.highlights}</h3>
            {stay.highlights.slice(0, 4).map((highlight) => (
              <p key={highlight.title}><Sparkles size={15} /> <strong>{highlight.title}</strong> {highlight.body}</p>
            ))}
          </article>
          <RulesBook stay={stay} language={language} />
        </div>
      </section>}

      <AgentBookingSection snapshot={snapshot} userContext={userContext} stay={stay} language={language} />
    </>
  );
}

function AboutExperience({ snapshot, userContext, language }: { snapshot: PublicSiteSnapshot; userContext: PublicUserContext; language: Language }) {
  const t = copy[language];
  return (
    <>
      <section className="public-subhero public-about-hero">
        <div>
          <h1>{t.aboutTitle}</h1>
          <p>{t.aboutText}</p>
          <div className="public-proof-strip">
            <span><MapPin size={16} /> {snapshot.publicAddressLabel}</span>
            <span><Star size={16} /> Guest-led hospitality</span>
            <span><HeartHandshake size={16} /> Mission support</span>
          </div>
        </div>
      </section>
      <AreaSection snapshot={snapshot} language={language} />
      <section className="public-section public-feature-shell">
        <div className="public-section__heading">
          <h2>Why guests book with us</h2>
          <p>{t.aboutMission}</p>
        </div>
        <div className="public-stay-grid">
          {snapshot.stays.map((stay) => <StayCard stay={stay} language={language} key={stay.id} />)}
        </div>
      </section>
      <MissionSection snapshot={snapshot} language={language} />
      <AgentBookingSection snapshot={snapshot} userContext={userContext} stay={snapshot.stays[0]} language={language} />
    </>
  );
}

function LegalExperience({ snapshot, kind }: { snapshot: PublicSiteSnapshot; kind: LegalKind }) {
  const titles = {
    business: 'Business profile',
    privacy: 'Privacy policy',
    terms: 'Terms of service',
    'data-deletion': 'Data deletion instructions',
  };
  const intro = {
    business: `MLADIS operates hosted stays from ${snapshot.publicAddressLabel}. Contact ${snapshot.contactEmail} for business, privacy, or booking questions.`,
    privacy: `We collect booking and account details needed to manage reservations, deposits, invoices, customer support, and optional promotions. Contact ${snapshot.contactEmail} for privacy requests.`,
    terms: 'Reservations are admin-confirmed, deposits are processed through configured payment providers, and house rules apply to each stay.',
    'data-deletion': `To request deletion of account or social login data, email ${snapshot.contactEmail} with the account email and provider used to sign in.`,
  };
  return (
    <section className="public-section public-legal">
      <div className="public-subhero">
        <div>
          <a className="public-subtle-link" href="/">Back to MLADIS</a>
          <h1>{titles[kind]}</h1>
          <p>{intro[kind]}</p>
        </div>
      </div>
      <div className="public-legal-grid">
        <article>
          <FileText size={22} />
          <h3>What this covers</h3>
          <p>{intro[kind]}</p>
        </article>
        <article>
          <ShieldCheck size={22} />
          <h3>Guest protection</h3>
          <p>We keep operational details private, use secure payment flows, and keep booking records tied to the guest account where possible.</p>
        </article>
        <article>
          <MessageSquareText size={22} />
          <h3>Contact</h3>
          <p>{snapshot.contactEmail}</p>
        </article>
      </div>
    </section>
  );
}

type AccountIconKey = 'guest' | 'calendar' | 'invoice' | 'home' | 'dashboard' | 'reservations' | 'reports' | 'customers' | 'deposits' | 'agent' | 'tools';

class AccountStatCardModel {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly caption: string,
    public readonly icon: AccountIconKey,
    public readonly tone: 'teal' | 'blue' | 'violet' | 'green',
  ) {}
}

class AccountAdminToolModel {
  constructor(
    public readonly label: string,
    public readonly href: string,
    public readonly detail: string,
    public readonly icon: AccountIconKey,
    public readonly tone: 'cyan' | 'blue' | 'violet' | 'green' | 'amber' | 'teal' | 'indigo' | 'rose',
  ) {}
}

class AccountTimelineStepModel {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly status: 'done' | 'current' | 'future',
  ) {}
}

function accountIcon(icon: AccountIconKey, size = 20) {
  if (icon === 'guest' || icon === 'customers') return <Users size={size} />;
  if (icon === 'calendar') return <CalendarDays size={size} />;
  if (icon === 'invoice' || icon === 'reports') return <FileText size={size} />;
  if (icon === 'home' || icon === 'dashboard') return <Home size={size} />;
  if (icon === 'reservations') return <ReceiptText size={size} />;
  if (icon === 'deposits') return <CreditCard size={size} />;
  if (icon === 'agent') return <Bot size={size} />;
  return <ShieldCheck size={size} />;
}

function compactStatusTone(status: string) {
  const normalized = status.toLowerCase();
  if (normalized.includes('cancel')) return 'cancelled';
  if (normalized.includes('pending') || normalized.includes('review')) return 'pending';
  if (normalized.includes('complete')) return 'completed';
  return 'confirmed';
}

function accountReservationNumber(reservation: AccountReservation) {
  return `ML-2026-${String(reservation.id).padStart(6, '0')}`;
}

function normalizeAccountName(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

function stayForReservation(snapshot: PublicSiteSnapshot, reservation: AccountReservation | null) {
  if (!reservation) return snapshot.stays[0] ?? null;
  const reservationName = normalizeAccountName(formatStayName(reservation.stayName));
  return snapshot.stays.find((stay) => {
    const stayName = normalizeAccountName(formatStayName(stay.name));
    return reservationName.includes(stayName) || stayName.includes(reservationName);
  }) ?? snapshot.stays[0] ?? null;
}

function accountDateRange(reservation: AccountReservation) {
  if (!reservation.checkIn || !reservation.checkOut) return 'Dates pending';
  return `${formatDate(reservation.checkIn)} – ${formatDate(reservation.checkOut)}`;
}

function activeStayCount(reservations: AccountReservation[]) {
  const now = new Date();
  return reservations.filter((reservation) => {
    const status = reservation.status.toLowerCase();
    const starts = reservation.checkIn ? new Date(`${reservation.checkIn}T00:00:00`) : null;
    const ends = reservation.checkOut ? new Date(`${reservation.checkOut}T23:59:59`) : null;
    return !status.includes('cancel') && starts && ends && starts <= now && ends >= now;
  }).length;
}

function AccountStatCard({ stat }: { stat: AccountStatCardModel }) {
  return (
    <article className={`account-v2-stat account-v2-stat--${stat.tone}`}>
      <span>{accountIcon(stat.icon, 23)}</span>
      <div>
        <small>{stat.label}</small>
        <strong>{stat.value}</strong>
        <em>{stat.caption}</em>
      </div>
    </article>
  );
}

function AccountExperience({ snapshot, userContext, language }: { snapshot: PublicSiteSnapshot; userContext: PublicUserContext; language: Language }) {
  const t = copy[language];
  const service = useMemo(() => AccountFactory.create(), []);
  const [account, setAccount] = useState<AccountSnapshot | null>(null);
  const [error, setError] = useState('');
  const token = csrfToken();

  useEffect(() => {
    let active = true;
    service
      .loadAccount()
      .then((data) => {
        if (active) setAccount(data);
      })
      .catch((caught: unknown) => {
        if (active) setError(caught instanceof Error ? caught.message : 'Could not load your account.');
      });
    return () => {
      active = false;
    };
  }, [service]);

  if (error) return <section className="dashboard-error">{error}</section>;
  if (!account) return <PublicSiteSkeleton />;

  const match = currentPath().match(/^\/accounts\/reservations\/(\d+)\/?(edit|cancel)?\/?$/);
  const activeReservation = match ? account.reservations.find((reservation) => reservation.id === Number(match[1])) : null;
  const mode = match?.[2] ?? 'detail';
  const selectedReservation = activeReservation ?? account.reservations[0] ?? null;
  const selectedStay = stayForReservation(snapshot, selectedReservation);
  const heroStay = selectedStay ?? snapshot.stays[0] ?? null;
  const invoiceTotal = account.invoices.length;
  const stats = [
    new AccountStatCardModel('Guest', account.name || userContext.displayName || 'Guest account', account.email || userContext.email || 'Signed-in account', 'guest', 'teal'),
    new AccountStatCardModel('Total reservations', String(account.reservations.length), 'Upcoming & past', 'calendar', 'blue'),
    new AccountStatCardModel('Invoices', String(invoiceTotal), invoiceTotal === 1 ? '1 total outstanding' : 'Total outstanding', 'invoice', 'violet'),
    new AccountStatCardModel('Active stays', String(activeStayCount(account.reservations)), 'Currently active', 'home', 'green'),
  ];

  return (
    <div className="account-v2-page">
      <section className="account-v2-hero">
        <div>
          <h1>{t.accountTitle}</h1>
          <p>{t.accountText}</p>
        </div>
        {heroStay && (
          <figure>
            <img src={heroStay.imageUrl} alt={formatStayName(heroStay.name)} />
          </figure>
        )}
      </section>

      <section className="account-v2-stats" aria-label="Account summary">
        {stats.map((stat) => <AccountStatCard stat={stat} key={stat.label} />)}
      </section>

      {account.isStaff && <AccountAdminTools />}

      <section className="public-section account-v2-workspace">
        <article className="account-v2-list">
          <header>
            <h2>Reservations</h2>
            <a href="#booking" onClick={handleBookingLinkClick}>+ New request</a>
          </header>
          {account.reservations.length === 0 && <p>No reservations yet. Start a stay request when you are ready.</p>}
          <div className="account-v2-reservation-stack">
            {account.reservations.slice(0, 4).map((reservation) => (
              <AccountReservationRow
                reservation={reservation}
                stay={stayForReservation(snapshot, reservation)}
                selected={selectedReservation?.id === reservation.id}
                key={reservation.id}
              />
            ))}
          </div>
          {account.reservations.length > 0 && (
            <a className="account-v2-past-link" href="/accounts/">
              <CalendarDays size={16} /> View past reservations <ChevronRight size={16} />
            </a>
          )}
        </article>

        <article className="account-v2-center">
          {selectedReservation && mode === 'edit' && activeReservation ? (
            <ReservationEditForm reservation={activeReservation} token={token} />
          ) : selectedReservation && mode === 'cancel' && activeReservation ? (
            <ReservationCancelForm reservation={activeReservation} token={token} />
          ) : selectedReservation ? (
            <AccountReservationCenter
              reservation={selectedReservation}
              stay={selectedStay}
              invoices={account.invoices}
              transactionDocuments={account.transactionDocuments}
            />
          ) : (
            <div className="account-v2-empty">
              <h2>Reservation center</h2>
              <p>Select a reservation to see details, edit eligible requests, or cancel when the current policy allows it.</p>
            </div>
          )}
        </article>
      </section>

      <div className="account-v2-booking-anchor">
        <AgentBookingSection snapshot={snapshot} userContext={userContext} stay={heroStay} language={language} />
      </div>
    </div>
  );
}

function AccountAdminTools() {
  const tools = [
    new AccountAdminToolModel('Operations dashboard', '/ops/dashboard/', 'Metrics, deposits, agent questions, and stay performance.', 'dashboard', 'cyan'),
    new AccountAdminToolModel('Reservations CRM', '/ops/reservations/', 'Combined direct requests and imported Airbnb guest records.', 'reservations', 'blue'),
    new AccountAdminToolModel('Reports', '/ops/reports/', 'Operational charts for visits, bookings, deposits, feedback, and agent questions.', 'reports', 'violet'),
    new AccountAdminToolModel('Customers', '/ops/customers/', 'Guest profiles, segments, consent, feedback, and promotion readiness.', 'customers', 'green'),
    new AccountAdminToolModel('Deposits', '/ops/deposits/', 'Stripe and PayPal security deposit records in a managed ledger.', 'deposits', 'amber'),
    new AccountAdminToolModel('Agent workspace', '/ops/agent/', 'Question analytics and FAQ training controls.', 'agent', 'teal'),
    new AccountAdminToolModel('Business calendar', '/ops/calendar/', 'Block dates, pricing overrides, and availability review.', 'calendar', 'indigo'),
    new AccountAdminToolModel('Admin tools', '/admin/', 'Full protected admin tools.', 'tools', 'rose'),
  ];
  return (
    <section className="account-v2-admin-tools">
      <div className="account-v2-admin-tools__header">
        <span><ShieldCheck size={22} /> Admin command center</span>
        <strong>Staff access enabled <CheckCircle2 size={15} /></strong>
        <p>You are signed in with staff access, so the operational tools are available in this account.</p>
      </div>
      <div className="account-v2-admin-grid">
        {tools.map((tool) => (
          <a className={`account-v2-admin-card account-v2-admin-card--${tool.tone}`} href={tool.href} key={tool.label}>
            {accountIcon(tool.icon, 27)}
            <span>
              <strong>{tool.label}</strong>
              <small>{tool.detail}</small>
            </span>
            <ArrowUpRight size={20} />
          </a>
        ))}
      </div>
    </section>
  );
}

function AccountReservationRow({
  reservation,
  stay,
  selected,
}: {
  reservation: AccountReservation;
  stay: PublicStay | null;
  selected: boolean;
}) {
  return (
    <a className={`account-v2-row${selected ? ' is-selected' : ''}`} href={reservation.detailUrl}>
      {stay && <img src={stay.imageUrl} alt={formatStayName(stay.name)} />}
      <span>
        <strong>{formatStayName(reservation.stayName)}</strong>
        <small>{accountDateRange(reservation)}</small>
        <small>{reservation.guests} guests</small>
      </span>
      <em className={`account-v2-status account-v2-status--${compactStatusTone(reservation.status)}`}>{reservation.status}</em>
      <ChevronRight size={17} />
    </a>
  );
}

function AccountReservationCenter({
  reservation,
  stay,
  invoices,
  transactionDocuments,
}: {
  reservation: AccountReservation;
  stay: PublicStay | null;
  invoices: AccountSnapshot['invoices'];
  transactionDocuments: AccountSnapshot['transactionDocuments'];
}) {
  const nights = nightsBetween(reservation.checkIn, reservation.checkOut);
  const depositDisplay = reservation.displayDeposit || '$200.00 USD';
  const stayPaymentDisplay = reservation.displayReservationPayment || reservation.displaySubtotal || reservation.displayTotal;
  const timeline = [
    new AccountTimelineStepModel('Request confirmed', reservation.createdAt ? formatDate(reservation.createdAt.slice(0, 10)) : 'Saved', 'done'),
    new AccountTimelineStepModel('Deposit hold placed', depositDisplay || 'On file', 'done'),
    new AccountTimelineStepModel('Check-in', formatDate(reservation.checkIn), 'future'),
    new AccountTimelineStepModel('Check-out', formatDate(reservation.checkOut), 'future'),
  ];
  const reservationInvoices = invoices.filter((invoice) => invoice.reservationId === reservation.id);
  const reservationDocuments = transactionDocuments.filter((document) => document.reservationId === reservation.id);
  const latestInvoice = reservationInvoices[0] ?? null;

  return (
    <>
      <header className="account-v2-center__header">
        {stay && <img src={stay.imageUrl} alt={formatStayName(stay.name)} />}
        <div>
          <h2>{formatStayName(reservation.stayName)}</h2>
          <span>Reservation #{accountReservationNumber(reservation)}</span>
          <p>{accountDateRange(reservation)} <b>•</b> {nights} night{nights === 1 ? '' : 's'} <b>•</b> {reservation.guests} guests</p>
        </div>
        <em className={`account-v2-status account-v2-status--${compactStatusTone(reservation.status)}`}>{reservation.status}</em>
      </header>

      <div className="account-v2-center__badges">
        <span><ShieldCheck size={20} /><strong>Deposit hold</strong><small>{depositDisplay}</small></span>
        <span><FileText size={20} /><strong>Invoice status</strong><small>{latestInvoice ? latestInvoice.status : 'No invoices'}</small></span>
        <span><Clock size={20} /><strong>Cancellation window</strong><small>{reservation.canCancel ? 'Host review' : 'Contact host'}</small></span>
      </div>

      <div className="account-v2-center__split">
        <section className="account-v2-payment-card">
          <h3>Payment summary</h3>
          <p><span>{reservation.pricing.displayBasePrice} × {nights} night{nights === 1 ? '' : 's'}</span><strong>{reservation.displaySubtotal}</strong></p>
          {reservation.displayDiscount && <p><span>Discount</span><strong>{reservation.displayDiscount}</strong></p>}
          <p><span>Stay payment hold</span><strong>{stayPaymentDisplay}</strong></p>
          <p><span>Security deposit hold</span><strong>{depositDisplay}</strong></p>
          <p className="account-v2-payment-card__total"><span>Total</span><strong>{reservation.displayTotal}</strong></p>
          <small>Deposit hold will be released after checkout unless a documented issue is found.</small>
        </section>

        <section className="account-v2-next-card">
          <h3>What happens next?</h3>
          {timeline.map((step) => (
            <p className={`account-v2-step account-v2-step--${step.status}`} key={step.label}>
              <i />
              <span>{step.label}</span>
              <strong>{step.value}</strong>
            </p>
          ))}
        </section>
      </div>

      <section className="account-v2-documents" aria-label="Documents and receipts">
        <header>
          <h3><ReceiptText size={17} /> Documents &amp; receipts</h3>
          <p>Available here and sent to your account email when generated.</p>
        </header>
        {reservationDocuments.length > 0 ? (
          <div>
            {reservationDocuments.map((document) => (
              <article key={document.id}>
                <FileText size={18} />
                <span>
                  <strong>{document.title}</strong>
                  <small>{document.reference} · {document.status} · {document.displayAmount}</small>
                </span>
                <a href={document.viewUrl} target="_blank" rel="noreferrer">View</a>
                {document.downloadUrl && <a href={document.downloadUrl}>Download</a>}
              </article>
            ))}
          </div>
        ) : (
          <p className="account-v2-documents__empty">Transaction documents will appear here after payment authorization or invoice creation.</p>
        )}
      </section>

      <footer className="account-v2-center__actions">
        <a href={reservation.detailUrl}><ReceiptText size={16} /> View details</a>
        {reservation.canEdit && <a href={reservation.editUrl}><PencilLine size={16} /> Edit request</a>}
        {reservation.canCancel && <a href={reservation.cancelUrl}><X size={16} /> Cancel request</a>}
        <a href={`mailto:?subject=MLADIS reservation ${accountReservationNumber(reservation)}`}><MessageSquareText size={16} /> Message host</a>
        {reservation.airbnbUrl && <a href={reservation.airbnbUrl} target="_blank" rel="noreferrer"><ArrowUpRight size={16} /> Airbnb</a>}
      </footer>
    </>
  );
}

function ReservationEditForm({ reservation, token }: { reservation: AccountReservation; token: string }) {
  const [checkIn, setCheckIn] = useState(reservation.checkIn);
  const [checkOut, setCheckOut] = useState(reservation.checkOut);
  const [guests, setGuests] = useState(String(reservation.guests));
  const quote = reservation.pricing.quote(guests, nightsBetween(checkIn, checkOut));
  const overGuestLimit = (Number(guests) || 1) > reservation.pricing.maxGuests;

  return (
    <form className="public-booking-form" method="post" action={currentPath()}>
      <input type="hidden" name="csrfmiddlewaretoken" value={token} />
      <h2>Edit reservation request</h2>
      <label>Phone<input name="phone" defaultValue={reservation.phone} required /></label>
      <div className="public-form-row">
        <label>Check in<input type="date" name="check_in" value={checkIn} onChange={(event) => setCheckIn(event.target.value)} required /></label>
        <label>Check out<input type="date" name="check_out" value={checkOut} onChange={(event) => setCheckOut(event.target.value)} required /></label>
      </div>
      <label>Guests<input type="number" name="guests" min="1" max={reservation.pricing.maxGuests} value={guests} onChange={(event) => setGuests(event.target.value)} required /></label>
      <div className="public-price-preview" aria-live="polite">
        <div>
          <span>Updated stay hold</span>
          <strong>{quote.displaySubtotal}</strong>
          <small>{quote.displayNightly}/night · {quote.nights} night{quote.nights === 1 ? '' : 's'}</small>
        </div>
        <div>
          <span>Current deposit</span>
          <strong>{reservation.displayDeposit}</strong>
          <small>Separate refundable damage hold.</small>
        </div>
        <div>
          <span>Guest cap</span>
          <strong>{reservation.pricing.maxGuests}</strong>
          <small>{reservation.pricing.label}</small>
        </div>
      </div>
      {overGuestLimit && (
        <p className="public-deposit-modal__error" role="alert">This stay allows up to {reservation.pricing.maxGuests} guests.</p>
      )}
      <label>Notes<textarea name="message" rows={4} defaultValue={reservation.message} /></label>
      <button type="submit" disabled={overGuestLimit}><PencilLine size={17} /> Save changes</button>
    </form>
  );
}

function ReservationCancelForm({ reservation, token }: { reservation: AccountReservation; token: string }) {
  return (
    <form className="public-booking-form" method="post" action={currentPath()}>
      <input type="hidden" name="csrfmiddlewaretoken" value={token} />
      <h2>Cancel reservation</h2>
      <p>{reservation.canCancel ? 'This reservation is currently inside the cancellation window.' : 'This reservation cannot be canceled online under the current policy.'}</p>
      <label>Reason<textarea name="reason" rows={4} required /></label>
      <button type="submit" disabled={!reservation.canCancel}>Confirm cancellation</button>
    </form>
  );
}


// ─────────────────────────────────────────────────────────────────────────────
// Admin Experience
// ─────────────────────────────────────────────────────────────────────────────

function AdminExperience({ language }: { language: Language }) {
  void language;
  const [adminData, setAdminData] = useState<AdminSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState('');

  useEffect(() => {
    let active = true;
    fetch('/api/admin/reservations', {
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
      .then(async (response) => {
        if (!active) return;
        if (!response.ok) {
          throw new Error('Failed to load admin data');
        }
        const data = await response.json();
        setAdminData(data as AdminSnapshot);
        setLoading(false);
      })
      .catch(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const handleStatusChange = async (reservationId: number, newStatus: string) => {
    setActionMessage('Updating...');
    try {
      const response = await fetch(`/api/admin/reservations/${reservationId}/status`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken(),
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (response.ok) {
        setActionMessage('Status updated successfully');
        // Refresh data
        const refreshResponse = await fetch('/api/admin/reservations', {
          credentials: 'include',
          headers: { Accept: 'application/json' },
        });
        const data = await refreshResponse.json();
        setAdminData(data as AdminSnapshot);
        setTimeout(() => setActionMessage(''), 3000);
      } else {
        setActionMessage('Failed to update status');
      }
    } catch {
      setActionMessage('Error updating status');
    }
  };

  if (loading) {
    return (
      <section className="public-admin-v4">
        <div className="public-admin-v4__hero">
          <div>
            <span>Admin workspace</span>
            <h1>Loading command center</h1>
            <p>Pulling reservation status, revenue, and action queues.</p>
          </div>
        </div>
      </section>
    );
  }

  if (!adminData) {
    return (
      <section className="public-admin-v4">
        <div className="public-admin-v4__hero">
          <div>
            <span>Admin workspace</span>
            <h1>Permission needed</h1>
            <p>Unable to load admin data. Please check that this account has staff access.</p>
          </div>
        </div>
      </section>
    );
  }

  const adminMetrics = [
    { label: 'Pending', value: String(adminData.pendingCount), icon: <Clock size={18} />, tone: 'orange' },
    { label: 'Confirmed', value: String(adminData.confirmedCount), icon: <CheckCircle2 size={18} />, tone: 'green' },
    { label: 'Cancelled', value: String(adminData.cancelledCount), icon: <XCircle size={18} />, tone: 'red' },
    { label: 'Revenue', value: adminData.totalRevenue, icon: <DollarSign size={18} />, tone: 'blue' },
  ];
  const adminTiles = [
    { label: 'Records', text: 'Protected system tables', href: '/admin/', icon: <ShieldCheck size={20} />, tone: 'blue' },
    { label: 'Brand', text: 'Logo, site text, public settings', href: '/admin/bookings/sitesettings/1/change/', icon: <Sparkles size={20} />, tone: 'green' },
    { label: 'Reservations', text: 'Requests, guests, imported stays', href: '/ops/reservations/', icon: <CalendarDays size={20} />, tone: 'orange' },
    { label: 'Reports', text: 'Revenue, agent, customer signals', href: '/ops/reports/', icon: <FileText size={20} />, tone: 'indigo' },
    { label: 'Maintenance', text: 'Work orders and evidence', href: '/ops/maintenance/', icon: <PencilLine size={20} />, tone: 'teal' },
    { label: 'Agent', text: 'FAQ training and questions', href: '/ops/agent/', icon: <Bot size={20} />, tone: 'violet' },
  ];

  return (
    <section className="public-admin-v4">
      <div className="public-admin-v4__hero">
        <div>
          <span>Admin workspace</span>
          <h1>Command center</h1>
          <p>Protected records, booking controls, brand settings, reports, and agent operations in one workspace.</p>
        </div>
        <div className="public-admin-v4__hero-actions">
          <a href="/admin/"><ShieldCheck size={17} /> Records</a>
          <a href="/ops/dashboard/"><Home size={17} /> Ops dashboard</a>
        </div>
      </div>

      {actionMessage && (
        <div className="public-admin-v4__notice" role="status">
          {actionMessage}
        </div>
      )}

      <div className="public-admin-v4__metrics">
        {adminMetrics.map((metric) => (
          <article className={`public-admin-v4__metric public-admin-v4__metric--${metric.tone}`} key={metric.label}>
            <span>{metric.icon}</span>
            <strong>{metric.value}</strong>
            <small>{metric.label}</small>
          </article>
        ))}
      </div>

      <div className="public-admin-v4__tiles">
        {adminTiles.map((tile) => (
          <a className={`public-admin-v4__tile public-admin-v4__tile--${tile.tone}`} href={tile.href} key={tile.label}>
            <span>{tile.icon}</span>
            <strong>{tile.label}</strong>
            <small>{tile.text}</small>
          </a>
        ))}
      </div>

      <article className="public-admin-v4__panel">
        <div className="public-admin-v4__panel-head">
          <div>
            <span>Reservation queue</span>
            <h2>{adminData.reservations.length} records</h2>
          </div>
          <a href="/ops/reservations/">Open reservations <ArrowUpRight size={16} /></a>
        </div>

        {adminData.reservations.length === 0 ? (
          <p className="public-admin-v4__empty">No reservations in the system yet.</p>
        ) : (
          <div className="public-admin-v4__records">
            {adminData.reservations.map((reservation) => (
              <article className="public-admin-v4__record" key={reservation.id}>
                <div>
                  <strong>{reservation.guestName}</strong>
                  <small>{reservation.guestEmail}</small>
                  {reservation.phone && <small>{reservation.phone}</small>}
                </div>
                <div>
                  <span>Stay</span>
                  <strong>{reservation.stayName}</strong>
                </div>
                <div>
                  <span>Dates</span>
                  <strong>{formatDate(reservation.checkIn)} → {formatDate(reservation.checkOut)}</strong>
                  <small>{reservation.guests} guests</small>
                </div>
                <div>
                  <span>Total</span>
                  <strong>{reservation.totalDisplay}</strong>
                  <small>{reservation.createdAt}</small>
                </div>
                <div className="public-admin-v4__record-actions">
                  <span className={`public-admin-v4__status public-admin-v4__status--${reservation.status}`}>
                    {reservation.status}
                  </span>
                  {reservation.status === 'pending' && (
                    <div>
                      <button type="button" onClick={() => handleStatusChange(reservation.id, 'confirmed')}>Confirm</button>
                      <button type="button" onClick={() => handleStatusChange(reservation.id, 'cancelled')}>Cancel</button>
                    </div>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </article>
    </section>
  );
}

export function PublicSitePage() {
  const service = useMemo(() => PublicSiteFactory.create(), []);
  const [snapshot, setSnapshot] = useState<PublicSiteSnapshot | null>(null);
  const [userContext, setUserContext] = useState<PublicUserContext | null>(null);
  const [error, setError] = useState('');
  const [language, setLanguage] = useState<Language>(() => (window.localStorage.getItem('mladis_language') === 'es' ? 'es' : 'en'));
  const [navOpen, setNavOpen] = useState(false);
  const [analyticsConsent, setAnalyticsConsent] = useState<'unknown' | 'granted' | 'denied'>(() => {
    const cookie = document.cookie.split('; ').find((row) => row.startsWith('mladis_analytics_consent='));
    return cookie?.split('=')[1] === 'granted' ? 'granted' : cookie?.split('=')[1] === 'denied' ? 'denied' : 'unknown';
  });

  useEffect(() => {
    window.localStorage.setItem('mladis_language', language);
  }, [language]);

  useEffect(() => {
    if (analyticsConsent !== 'granted') return;
    const slug = window.location.pathname.match(/^\/stays\/([^/]+)\/?$/)?.[1] ?? '';
    if (window.location.pathname === '/' || slug) void recordMarketingEvent('landing_visit', slug);
  }, [analyticsConsent]);

  function chooseAnalyticsConsent(choice: 'granted' | 'denied') {
    const secure = window.location.protocol === 'https:' ? '; secure' : '';
    document.cookie = `mladis_analytics_consent=${choice}; path=/; max-age=15552000; samesite=lax${secure}`;
    setAnalyticsConsent(choice);
  }

  useEffect(() => {
    let active = true;
    service
      .loadSite()
      .then((data) => {
        if (!active) return;
        setSnapshot(data);
        setUserContext(PublicUserContext.checking(data.agent));
      })
      .catch((caught: unknown) => {
        if (active) setError(caught instanceof Error ? caught.message : 'Could not load the modern site.');
      });
    return () => {
      active = false;
    };
  }, [service]);

  useEffect(() => {
    if (!snapshot) return undefined;
    let active = true;

    fetch('/api/account/summary/', {
      cache: 'no-store',
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
      .then(async (response) => {
        if (!active) return;
        const contentType = response.headers.get('content-type') || '';
        if (!response.ok || !contentType.includes('application/json')) {
          setUserContext(PublicUserContext.anonymous(snapshot.agent));
          return;
        }
        const data = await response.json() as ApiAccountUserContext;
        setUserContext(userContextFromApi(data, snapshot.agent));
      })
      .catch(() => {
        if (active) setUserContext(PublicUserContext.anonymous(snapshot.agent));
      });

    return () => {
      active = false;
    };
  }, [snapshot]);

  useEffect(() => {
    if (!snapshot) return undefined;
    const scrollFromHash = window.setTimeout(() => {
      if (window.location.hash === '#booking') scrollToBookingSection();
    }, 80);

    function handleBookingAnchorClick(event: MouseEvent) {
      const target = event.target as HTMLElement | null;
      const anchor = target?.closest<HTMLAnchorElement>('a[href="#booking"], a[href="/#booking"]');
      if (!anchor) return;
      if (!scrollToBookingSection()) return;
      event.preventDefault();
      window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}#booking`);
    }

    document.addEventListener('click', handleBookingAnchorClick);
    return () => {
      window.clearTimeout(scrollFromHash);
      document.removeEventListener('click', handleBookingAnchorClick);
    };
  }, [snapshot]);

  if (!snapshot && !error) return <PublicSiteSkeleton />;
  if (!snapshot) return <main className="public-site"><section className="dashboard-error">{error}</section></main>;

  const resolvedUserContext = userContext ?? PublicUserContext.checking(snapshot.agent);
  const stay = findStayByPath(snapshot);
  const legalKind = legalKindFromPath();
  const path = currentPath();

  let content = <HomeExperience snapshot={snapshot} userContext={resolvedUserContext} language={language} />;
  if (stay) content = <StayDetailExperience snapshot={snapshot} userContext={resolvedUserContext} stay={stay} language={language} />;
  if (path.startsWith('/about')) content = <AboutExperience snapshot={snapshot} userContext={resolvedUserContext} language={language} />;
  if (legalKind) content = <LegalExperience snapshot={snapshot} kind={legalKind} />;
  if (path.startsWith('/ops/admin')) content = <AdminExperience language={language} />;
  if (path.startsWith('/accounts')) content = <AccountExperience snapshot={snapshot} userContext={resolvedUserContext} language={language} />;

  return (
    <main className={`public-site public-site--v4-preview${navOpen ? ' public-site--nav-open' : ''}`}>
      <PublicNav
        snapshot={snapshot}
        userContext={resolvedUserContext}
        language={language}
        navOpen={navOpen}
        onLanguageChange={setLanguage}
        onNavToggle={() => setNavOpen((current) => !current)}
        onSignOutStart={() => setUserContext(PublicUserContext.anonymous(resolvedUserContext.agent))}
      />
      {content}
      {analyticsConsent === 'unknown' && (
        <AnalyticsConsentBanner language={language} onChoice={chooseAnalyticsConsent} />
      )}
    </main>
  );
}

function AnalyticsConsentBanner({
  language,
  onChoice,
}: {
  language: Language;
  onChoice: (choice: 'granted' | 'denied') => void;
}) {
  return (
    <aside className="public-consent-banner" aria-label={language === 'es' ? 'Preferencias de medición' : 'Measurement preferences'}>
      <p>{language === 'es'
        ? '¿Permites medición anónima de campañas para mejorar las consultas y reservas? No se incluyen nombres, mensajes, pagos ni fechas.'
        : 'Allow anonymous campaign measurement to improve inquiries and bookings? Names, messages, payments, and dates are not included.'}</p>
      <div>
        <button type="button" onClick={() => onChoice('denied')}>{language === 'es' ? 'Solo lo necesario' : 'Necessary only'}</button>
        <button type="button" onClick={() => onChoice('granted')}>{language === 'es' ? 'Permitir medición' : 'Allow measurement'}</button>
      </div>
    </aside>
  );
}
