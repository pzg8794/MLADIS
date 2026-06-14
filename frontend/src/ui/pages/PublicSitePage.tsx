import { useEffect, useMemo, useState, type FormEvent } from 'react';
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
  Home,
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
  XCircle,
  DollarSign,
  Music2,
} from 'lucide-react';
import { AccountFactory } from '../../application/AccountFactory';
import { PublicSiteFactory } from '../../application/PublicSiteFactory';
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

const SOL_ORIENS_MAP_EMBED_URL = 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3782.782382437169!2d-69.9484538248079!3d18.538733682558327!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x8eaf897e8fbf9ce9%3A0x2e510419521c5941!2sResidential%20Sol%20Oriens%20V!5e0!3m2!1sen!2sus!4v1781349935983!5m2!1sen!2sus';
const SOL_ORIENS_STAY_MAP_EMBED_URL = mapEmbedWithDistance(SOL_ORIENS_MAP_EMBED_URL, '7600');
const SOL_ORIENS_DIRECTIONS_URL = 'https://maps.app.goo.gl/EhA3JTQ685awyX9T9';

function mapEmbedWithDistance(url: string, distance: string) {
  return url.replace('!1d3782.782382437169!', `!1d${distance}!`);
}


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

type PaymentContextResponse = {
  ok?: boolean;
  message?: string;
  inquiry?: CreatedReservationRequest;
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
      'Pool-ready apartments near Colinas del Arroyo II, Jacobo Majluta, malls, restaurants, and the Embassy corridor.',
    primary: 'Start booking',
    secondary: 'Explore stays',
    proof: 'Guest rating',
    staysTitle: 'Choose your stay',
    staysText: 'Photos, reviews, rules, and direct booking in one clean view.',
    areaTitle: 'More than a place to sleep',
    areaText:
      'Beyond the room: city errands, food, malls, beach-day options, and hosted support from Santo Domingo Norte.',
    bookingTitle: 'Ask first, then book with confidence',
    bookingText: '',
    agentTitle: 'Booking agent',
    agentText: 'Ask about availability, guest count, deposit holds, house rules, transportation, or which apartment fits your group.',
    formTitle: 'Start a reservation',
    formText: 'Send the request first. The $200 secure deposit hold opens next in a secure step.',
    pricePreview: 'Price preview',
    stayPayment: 'Stay payment hold',
    highlights: 'Top guest highlights',
    rules: 'Apartment rules',
    mission: 'Travel with mission',
    signInToAskAgent: 'Sign in to ask agent',
    agentLimitReached: 'Question limit reached',
    agentLimitText: 'You have reached the current question limit for this account.',
    submit: 'Send request',
    autofill: 'Use my account info',
    required: 'required',
    depositTitle: 'Make secure deposit',
    depositText: 'Your request is saved. Continue with the refundable damage-deposit hold for this stay.',
    depositAction: 'Make secure deposit',
    paymentTitle: 'Hold reservation payment',
    paymentText: 'Deposit hold recorded. Now place the stay-payment authorization hold; it is captured 24 hours before check-in.',
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
      'Apartamentos con piscina cerca de Colinas del Arroyo II, Los Guaricanos, Jacobo Majluta, plazas, restaurantes y la zona de la Embajada.',
    primary: 'Empezar reserva',
    secondary: 'Ver estadías',
    proof: 'Valoración de huéspedes',
    staysTitle: 'Elige tu estadía',
    staysText: 'Fotos, reseñas, reglas y reserva directa en una vista clara.',
    areaTitle: 'Más que un lugar para dormir',
    areaText:
      'Más allá del cuarto: diligencias, comida, plazas, playa y apoyo anfitrión desde Santo Domingo Norte.',
    bookingTitle: 'Pregunta primero y reserva con confianza',
    bookingText: '',
    agentTitle: 'Agente de reservas',
    agentText: 'Pregunta por disponibilidad, cantidad de huéspedes, depósito, reglas, transporte o cuál apartamento te conviene.',
    formTitle: 'Iniciar reserva',
    formText: 'Envía la solicitud primero. El depósito seguro de $200 se abre después en un paso seguro.',
    pricePreview: 'Vista previa del precio',
    stayPayment: 'Retención de estadía',
    highlights: 'Comentarios destacados',
    rules: 'Reglas del apartamento',
    mission: 'Viaja con misión',
    signInToAskAgent: 'Entra para preguntar al agente',
    agentLimitReached: 'Límite de preguntas alcanzado',
    agentLimitText: 'Has alcanzado el límite actual de preguntas para esta cuenta.',
    submit: 'Enviar solicitud',
    autofill: 'Usar mi cuenta',
    required: 'requerido',
    depositTitle: 'Hacer depósito seguro',
    depositText: 'Tu solicitud está guardada. Continúa con el depósito reembolsable por daños para esta estadía.',
    depositAction: 'Hacer depósito seguro',
    paymentTitle: 'Retener pago de reserva',
    paymentText: 'El depósito quedó registrado. Ahora haz la retención del pago de estadía; se captura 24 horas antes del check-in.',
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
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(
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

function HomeStars({ rating }: { rating?: string }) {
  return (
    <span className="public-home-v5-stars" aria-label={`${rating || '4.93'} guest rating`}>
      {Array.from({ length: 5 }, (_, index) => (
        <Star key={index} size={15} fill="currentColor" />
      ))}
    </span>
  );
}

function stayGalleryImages(stay: PublicStay) {
  const gallery = stay.gallery.length
    ? stay.gallery
    : [{ imageUrl: stay.imageUrl, altText: formatStayName(stay.name), caption: formatStayName(stay.name) }];
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

function useGuestRatingItems(snapshot: PublicSiteSnapshot) {
  return useMemo(() => {
    const voices = [
      { guest: 'Airbnb guest', initials: 'AG', avatar: 'https://i.pravatar.cc/96?img=12', title: 'Clean, bright, and easy to enjoy', body: 'Guests consistently mention the pool, clean spaces, and helpful arrival support.' },
      { guest: 'Family stay', initials: 'FS', avatar: 'https://i.pravatar.cc/96?img=32', title: 'Great for groups and families', body: 'The apartments work well for families who want space, privacy, and quick access to Santo Domingo Norte.' },
      { guest: 'Verified guest', initials: 'VG', avatar: 'https://i.pravatar.cc/96?img=47', title: 'Simple check-in and local guidance', body: 'Clear rules, host support, and nearby food and shopping help guests plan with confidence.' },
    ];
    const derived = snapshot.stays.flatMap((stay, stayIndex) => {
      const voice = voices[stayIndex % voices.length];
      const nextVoice = voices[(stayIndex + 1) % voices.length];
      return [voice, nextVoice].map((reviewVoice) => ({
        stayName: formatStayName(stay.name),
        title: reviewVoice.title,
        body: reviewVoice.body,
        guest: reviewVoice.guest,
        initials: reviewVoice.initials,
        avatar: reviewVoice.avatar,
        rating: stay.rating || '4.9',
      }));
    });
    return derived.length ? derived : [{
      stayName: 'Guest stays',
      title: 'Loved by guests',
      body: 'Clean spaces, local support, and clear booking steps.',
      guest: 'Guest review',
      initials: 'GR',
      avatar: 'https://i.pravatar.cc/96?img=56',
      rating: '4.93',
    }];
  }, [snapshot.stays]);
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
      <a className="public-stay-rotator__link" href={linkUrl} aria-label={`View ${formatStayName(stay.name)}`}>
        <img src={image?.imageUrl || stay.imageUrl} alt={image?.altText || formatStayName(stay.name)} loading="eager" />
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
  const displayName = formatStayName(stay.name);
  return (
    <article className="public-stay-card">
      <StayImageRotator stay={stay} linkUrl={stay.detailUrl} className="public-stay-rotator--card" />
      <div className="public-stay-card__body">
        <div>
          <h3>{displayName}</h3>
          <p>{stay.headline || stay.description}</p>
        </div>
        <div className="public-stay-card__stats">
          <span><Star size={14} /> {stay.rating || 'Airbnb'}</span>
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
        <label>
          <MessageSquareText size={16} />
          <textarea
            name="message"
            value={agentMessage}
            onChange={(event) => setAgentMessage(event.target.value)}
            placeholder="Can I bring family visitors? What are the pool hours?"
          />
        </label>
        <a className="public-agent-action" href={agentAccess.loginUrl}>{t.signInToAskAgent}</a>
      </div>
    );
  }

  if (!agentAccess.canAsk) {
    return (
      <div className="public-agent-prompt">
        <label>
          <MessageSquareText size={16} />
          <textarea
            name="message"
            value={agentMessage}
            onChange={(event) => setAgentMessage(event.target.value)}
            placeholder="Can I bring family visitors? What are the pool hours?"
          />
        </label>
        <button type="button" disabled>{t.agentLimitReached}</button>
        <p className="public-agent-reply">{t.agentLimitText}</p>
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
            placeholder="Can I bring family visitors? What are the pool hours?"
          />
        </label>
        <button type="submit" disabled={agentBusy}>{agentBusy ? 'Asking...' : 'Ask agent'}</button>
      </form>
      {agentReply && <p className="public-agent-reply">{agentReply}</p>}
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
  const [requestResult, setRequestResult] = useState<CreatedReservationRequest | null>(null);
  const [paymentRequest, setPaymentRequest] = useState<CreatedReservationRequest | null>(null);
  const [requestMessage, setRequestMessage] = useState('');
  const [requestErrors, setRequestErrors] = useState<string[]>([]);
  const [requestBusy, setRequestBusy] = useState(false);
  const selectedStay = useMemo(
    () => snapshot.stays.find((availableStay) => String(availableStay.id) === draft.item) ?? null,
    [draft.item, snapshot.stays],
  );
  const quote = selectedStay
    ? selectedStay.pricing.quote(draft.guests, nightsBetween(draft.checkIn, draft.checkOut))
    : null;
  const guestLimit = selectedStay?.pricing.maxGuests ?? null;
  const guestsNumber = Math.max(Number(draft.guests) || 1, 1);
  const overGuestLimit = Boolean(guestLimit && guestsNumber > guestLimit);

  useEffect(() => {
    setDraft((currentDraft) => {
      const itemValue = stay?.id ? String(stay.id) : currentDraft.item;
      const nextStay = snapshot.stays.find((availableStay) => String(availableStay.id) === itemValue) ?? null;
      return currentDraft.withField('item', itemValue).withStayPricing(nextStay?.pricing ?? null);
    });
  }, [snapshot.stays, stay?.id]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const paymentFor = params.get('payment_for');
    const paymentSuccess = params.get('payment_success') === '1';
    if (paymentSuccess) {
      setRequestMessage('Reservation payment hold recorded. MLADIS will review and confirm by email.');
      return;
    }
    if (!paymentFor || params.get('deposit_success') !== '1') return;
    let isMounted = true;
    fetch(`/payments/context/?inquiry_id=${encodeURIComponent(paymentFor)}`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
    })
      .then((response) => response.json() as Promise<PaymentContextResponse>)
      .then((data) => {
        if (!isMounted) return;
        if (data.ok && data.inquiry) {
          setPaymentRequest(data.inquiry);
          setRequestMessage('Damage deposit hold recorded. Finish the reservation payment hold next.');
        } else {
          setRequestErrors([data.message || 'Could not reopen the reservation payment window.']);
        }
      })
      .catch(() => {
        if (isMounted) setRequestErrors(['Could not reopen the reservation payment window.']);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  function updateDraft(field: ReservationRequestField, value: string) {
    setDraft((currentDraft) => {
      const nextDraft = currentDraft.withField(field, value);
      if (field !== 'item') return nextDraft;
      const nextStay = snapshot.stays.find((availableStay) => String(availableStay.id) === value) ?? null;
      return nextDraft.withStayPricing(nextStay?.pricing ?? null);
    });
  }

  function autofillAccount() {
    setDraft((currentDraft) => currentDraft.withAccount(userContext));
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
      setRequestResult(data.inquiry);
      setRequestMessage('');
    } catch {
      setRequestErrors(['Could not reach the reservation request service from this browser session.']);
    } finally {
      setRequestBusy(false);
    }
  }

  return (
    <section id="booking" className="public-section public-booking">
      <div className="public-section__heading public-booking__intro">
        <div>
          <h2>{t.bookingTitle}</h2>
          {t.bookingText && <p>{t.bookingText}</p>}
        </div>
        <GuestRatingSpotlight snapshot={snapshot} />
      </div>
      <div className="public-booking__grid">
        <article className="public-agent-card">
          <span><Bot size={19} /> {t.agentTitle}</span>
          <p>{t.agentText}</p>
          <LegacyAgentPrompt stay={stay} token={token} agent={userContext.agent} language={language} />
          {stay && (
            <div className="public-agent-card__rules">
              <RulesBook stay={stay} language={language} />
            </div>
          )}
        </article>

        <form className="public-booking-form" method="post" action="/inquiries/" onSubmit={submitReservationRequest}>
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
          {submitted && <p className="public-success">Request received. Continue with the secure deposit hold.</p>}
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
                <option value={availableStay.id} key={availableStay.id}>{formatStayName(availableStay.name)}</option>
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
            <label>Coupon<input name="coupon_code" value={draft.couponCode} onChange={(event) => updateDraft('coupon_code', event.target.value)} /></label>
          </div>
          <div className="public-price-preview" aria-live="polite">
            <div className="public-price-preview__box public-price-preview__box--quote">
              <span>{t.pricePreview}</span>
              <strong>{quote ? quote.displaySubtotal : 'Choose a stay for an exact quote'}</strong>
              <small>{quote ? `${quote.displayNightly}/night · ${quote.nights} night${quote.nights === 1 ? '' : 's'}` : 'G-101/G-102 pricing appears here before you send.'}</small>
            </div>
            <div className="public-price-preview__box public-price-preview__box--payment">
              <span>{t.stayPayment}</span>
              <strong>{quote ? quote.displaySubtotal : '$0.00 USD'}</strong>
              <small>Held now, charged 24 hours before check-in.</small>
            </div>
            <div className="public-price-preview__box public-price-preview__box--deposit">
              <span>Damage deposit</span>
              <strong>{snapshot.depositAmount}</strong>
              <small>Refundable hold.</small>
            </div>
          </div>
          <p className="public-price-note">
            <strong>{selectedStay?.pricing.extraGuestRuleLabel() ?? '$10/night per added guest, max 7 guests.'}</strong>
            {quote && quote.extraGuestCount > 0 && (
              <span>{quote.extraGuestCount} added guest{quote.extraGuestCount === 1 ? '' : 's'} included at {selectedStay?.pricing.displayExtraGuestPrice}/night each.</span>
            )}
          </p>
          {overGuestLimit && (
            <p className="public-deposit-modal__error" role="alert">This stay allows up to {guestLimit} guests.</p>
          )}
          <label>Notes<textarea name="message" rows={3} value={draft.message} onChange={(event) => updateDraft('message', event.target.value)} /></label>
          <button type="submit" disabled={requestBusy || overGuestLimit}><CreditCard size={17} /> {requestBusy ? 'Sending...' : t.submit}</button>
        </form>
      </div>
      {requestResult && (
        <DepositHoldModal
          request={requestResult}
          token={token}
          onClose={() => setRequestResult(null)}
          language={language}
        />
      )}
      {paymentRequest && (
        <ReservationPaymentHoldModal
          request={paymentRequest}
          token={token}
          onClose={() => setPaymentRequest(null)}
          language={language}
        />
      )}
    </section>
  );
}

function DepositHoldModal({
  request,
  token,
  onClose,
  language,
}: {
  request: CreatedReservationRequest;
  token: string;
  onClose: () => void;
  language: Language;
}) {
  const t = copy[language];
  const [provider, setProvider] = useState('stripe');
  const [isStartingCheckout, setIsStartingCheckout] = useState(false);
  const [checkoutError, setCheckoutError] = useState('');

  async function startDepositCheckout(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsStartingCheckout(true);
    setCheckoutError('');
    const formData = new FormData(event.currentTarget);
    formData.set('payment_provider', provider);

    try {
      const response = await fetch(request.deposit_checkout_url || '/deposits/checkout/', {
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
      <article className="public-deposit-modal" role="dialog" aria-modal="true" aria-labelledby="deposit-modal-title">
        <header className="public-deposit-modal__header">
          <div>
            <span>{request.request_key}</span>
            <h2 id="deposit-modal-title">{t.depositTitle}</h2>
            <p>{t.depositText}</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close deposit form">
            <XCircle size={24} />
          </button>
        </header>
        <div className="public-deposit-modal__summary">
          <div>
            <span>Stay</span>
            <strong>{formatStayName(request.stay_name)}</strong>
          </div>
          <div>
            <span>Dates</span>
            <strong>{request.check_in} to {request.check_out}</strong>
          </div>
          <div>
            <span>Guests</span>
            <strong>{request.guests}</strong>
          </div>
          <div>
            <span>Deposit</span>
            <strong>{request.display_deposit}</strong>
          </div>
          <div>
            <span>Next stay hold</span>
            <strong>{request.display_reservation_payment}</strong>
          </div>
        </div>
        <form className="public-deposit-modal__form" method="post" action={request.deposit_checkout_url || '/deposits/checkout/'} onSubmit={startDepositCheckout}>
          <input type="hidden" name="csrfmiddlewaretoken" value={token} />
          <input type="hidden" name="inquiry_id" value={request.id} />
          <input type="hidden" name="item" value={request.item_id ?? ''} />
          <input type="hidden" name="guest_name" value={request.guest_name} />
          <input type="hidden" name="email" value={request.email} />
          <fieldset>
            <legend>Payment method</legend>
            <label><input type="radio" name="payment_provider" value="stripe" checked={provider === 'stripe'} onChange={(event) => setProvider(event.target.value)} /> Card / wallet through Stripe</label>
            <label><input type="radio" name="payment_provider" value="paypal" checked={provider === 'paypal'} onChange={(event) => setProvider(event.target.value)} /> PayPal</label>
          </fieldset>
          {checkoutError && <p className="public-deposit-modal__error" role="alert">{checkoutError}</p>}
          <footer className="public-deposit-modal__actions">
            <button type="button" onClick={onClose}>Close</button>
            <button type="submit" disabled={isStartingCheckout}>
              <ShieldCheck size={17} /> {isStartingCheckout ? 'Opening checkout...' : t.depositAction}
            </button>
          </footer>
        </form>
      </article>
    </div>
  );
}

function ReservationPaymentHoldModal({
  request,
  token,
  onClose,
  language,
}: {
  request: CreatedReservationRequest;
  token: string;
  onClose: () => void;
  language: Language;
}) {
  const t = copy[language];
  const [isStartingCheckout, setIsStartingCheckout] = useState(false);
  const [checkoutError, setCheckoutError] = useState('');

  async function startPaymentCheckout(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsStartingCheckout(true);
    setCheckoutError('');
    const formData = new FormData(event.currentTarget);

    try {
      const response = await fetch(request.reservation_payment_checkout_url || '/payments/checkout/', {
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
      setCheckoutError(validationErrors[0] || data.message || 'The reservation payment hold could not be started.');
    } catch {
      setCheckoutError('Could not reach the reservation payment service from this browser session.');
    } finally {
      setIsStartingCheckout(false);
    }
  }

  return (
    <div className="public-modal-backdrop" role="presentation">
      <article className="public-deposit-modal" role="dialog" aria-modal="true" aria-labelledby="payment-modal-title">
        <header className="public-deposit-modal__header">
          <div>
            <span>{request.request_key}</span>
            <h2 id="payment-modal-title">{t.paymentTitle}</h2>
            <p>{t.paymentText}</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close payment form">
            <XCircle size={24} />
          </button>
        </header>
        <div className="public-deposit-modal__summary">
          <div>
            <span>Stay</span>
            <strong>{formatStayName(request.stay_name)}</strong>
          </div>
          <div>
            <span>Dates</span>
            <strong>{request.check_in} to {request.check_out}</strong>
          </div>
          <div>
            <span>Stay hold</span>
            <strong>{request.display_reservation_payment}</strong>
          </div>
          <div>
            <span>Total incl. deposit</span>
            <strong>{request.display_total}</strong>
          </div>
        </div>
        <form className="public-deposit-modal__form" method="post" action={request.reservation_payment_checkout_url || '/payments/checkout/'} onSubmit={startPaymentCheckout}>
          <input type="hidden" name="csrfmiddlewaretoken" value={token} />
          <input type="hidden" name="inquiry_id" value={request.id} />
          <p className="public-price-note">
            This is an authorization hold for the stay payment. MLADIS captures it 24 hours before check-in after admin review.
          </p>
          {checkoutError && <p className="public-deposit-modal__error" role="alert">{checkoutError}</p>}
          <footer className="public-deposit-modal__actions">
            <button type="button" onClick={onClose}>Close</button>
            <button type="submit" disabled={isStartingCheckout}>
              <ShieldCheck size={17} /> {isStartingCheckout ? 'Opening checkout...' : t.paymentAction}
            </button>
          </footer>
        </form>
      </article>
    </div>
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
  const highlights = (stay.highlights.length ? stay.highlights : [
    { title: 'Trusted by guests', body: stay.reviewLabel || 'Reliable host support for Santo Domingo stays.', sourceLabel: 'Guest reviews' },
    { title: 'Secure booking', body: 'Payment holds keep the reservation process structured and reviewable.', sourceLabel: 'MLADIS' },
    { title: 'Local support', body: 'Area guidance helps guests plan malls, errands, restaurants, and beach days.', sourceLabel: 'MLADIS' },
  ]).slice(0, 6);
  const spreads = useMemo(() => [
    {
      leftTitle: t.rules,
      leftTone: 'green',
      leftItems: rules.slice(0, 3).map((rule) => ({ ...rule, icon: 'rule' })),
      rightTitle: 'Stay rhythm',
      rightTone: 'gold',
      rightItems: rules.slice(3, 6).map((rule) => ({ ...rule, icon: 'shield' })),
    },
    {
      leftTitle: 'Guest care',
      leftTone: 'blue',
      leftItems: highlights.slice(0, 3).map((highlight) => ({ title: highlight.title, description: highlight.body, icon: 'guest' })),
      rightTitle: 'Secure booking',
      rightTone: 'teal',
      rightItems: [
        { title: 'Refundable deposit hold', description: 'The damage deposit is handled as a secure refundable hold.', icon: 'shield' },
        { title: 'Stay-payment hold', description: 'The stay-payment hold is captured 24 hours before check-in.', icon: 'payment' },
        { title: 'Account records', description: 'Requests, invoices, and updates stay tied to the guest account.', icon: 'document' },
      ],
    },
    {
      leftTitle: 'Arrival prep',
      leftTone: 'indigo',
      leftItems: [
        { title: 'Ask before booking', description: 'Use the agent for rules, transport, deposit, and fit questions.', icon: 'agent' },
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
  ], [highlights, rules, t.rules]);
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
  const [areaDistance, setAreaDistance] = useState(52000);
  const areaMapUrl = useMemo(() => mapEmbedWithDistance(SOL_ORIENS_MAP_EMBED_URL, String(areaDistance)), [areaDistance]);
  const zoomIn = () => setAreaDistance((current) => Math.max(22000, Math.round(current * 0.74)));
  const zoomOut = () => setAreaDistance((current) => Math.min(82000, Math.round(current * 1.26)));
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
          <a href={SOL_ORIENS_DIRECTIONS_URL} target="_blank" rel="noreferrer">Directions <ArrowUpRight size={14} /></a>
        </div>
        <iframe
          title="Residential Sol Oriens V area map"
          loading="lazy"
          allowFullScreen
          referrerPolicy="no-referrer-when-downgrade"
          src={areaMapUrl}
        />
        <div className="public-home-v5-map-zoom" aria-label="Map zoom controls">
          <button type="button" onClick={zoomIn} aria-label="Zoom in">+</button>
          <button type="button" onClick={zoomOut} aria-label="Zoom out">-</button>
        </div>
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

function HomeRulesMapSection({ snapshot, stay, language }: { snapshot: PublicSiteSnapshot; stay: PublicStay; language: Language }) {
  const mapStays = snapshot.stays.slice(0, 3);
  return (
    <section className="public-section public-home-v5-rules-map">
      <div className="public-home-v5-rules-copy">
        <h2>Know Where You Are Staying</h2>
        <p className="public-home-v5-rules-alert"><ShieldCheck size={18} /> Must Read Rules of Your Stay</p>
        <RulesBook stay={stay} language={language} />
      </div>
      <article className="public-home-v5-map-card public-home-v5-map-card--large">
        <div className="public-home-v5-map-card__header">
          <span><Home size={15} /> Apartment location</span>
          <strong>Sol Oriens V stay area</strong>
          <a className="public-home-v5-map-card__button" href={SOL_ORIENS_DIRECTIONS_URL} target="_blank" rel="noreferrer">View full map <ArrowUpRight size={14} /></a>
        </div>
        <iframe
          title="Sol Oriens V apartment location map"
          loading="lazy"
          allowFullScreen
          referrerPolicy="no-referrer-when-downgrade"
          src={SOL_ORIENS_STAY_MAP_EMBED_URL}
        />
        <div className="public-home-v5-stay-markers">
          {mapStays.map((mapStay, index) => (
            <a className={`public-home-v5-stay-marker public-home-v5-stay-marker--${index + 1}`} href={mapStay.detailUrl} key={mapStay.id}>
              <img src={mapStay.imageUrl} alt={formatStayName(mapStay.name)} />
              <span>
                <strong>{formatStayName(mapStay.name)}</strong>
                <small><Star size={13} fill="currentColor" /> {mapStay.rating || '4.9'} · {mapStay.statList.slice(0, 2).map(normaliseStayStatLabel).join(' · ')}</small>
              </span>
            </a>
          ))}
        </div>
      </article>
    </section>
  );
}

function HomeTrustStrip({ snapshot }: { snapshot: PublicSiteSnapshot }) {
  const rating = snapshot.stays[0]?.rating || '4.93';
  const trustItems = useMemo(() => [
    {
      title: 'Trusted by guests',
      body: `${rating} average guest rating from Airbnb reviews`,
      icon: <ShieldCheck size={22} />,
    },
    {
      title: 'Secure booking',
      body: `${snapshot.depositAmount} deposit hold opens next in a secure step.`,
      icon: <CreditCard size={22} />,
    },
    {
      title: 'Human support',
      body: 'Real people, local knowledge, and agent support when guests need help.',
      icon: <Bot size={22} />,
    },
  ], [rating, snapshot.depositAmount]);
  const visibleTrustItems = useRotatingList(trustItems, 5000).slice(0, 3);
  return (
    <section className="public-home-v5-trust-strip" aria-label="Trust signals">
      {visibleTrustItems.map((item) => (
        <article key={item.title}>
          {item.icon}
          <strong>{item.title}</strong>
          <span>{item.body}</span>
        </article>
      ))}
    </section>
  );
}

function GuestRatingSpotlight({ snapshot }: { snapshot: PublicSiteSnapshot }) {
  const [current] = useRotatingList(useGuestRatingItems(snapshot), 5000);

  return (
    <section className="public-guest-spotlight" aria-label="Top guest rating">
      <span className="public-guest-spotlight__avatar" aria-hidden="true">
        <img src={current.avatar} alt="" />
      </span>
      <div>
        <span><Star size={16} fill="currentColor" /> {current.rating}</span>
        <strong>{current.title}</strong>
        <p>{current.body}</p>
      </div>
      <small>{current.guest}</small>
    </section>
  );
}

function HomeLovedGuestsCard({ snapshot }: { snapshot: PublicSiteSnapshot }) {
  const [current] = useRotatingList(useGuestRatingItems(snapshot), 5000);
  return (
    <article className="public-home-loved-card" aria-label="Loved by guests">
      <span className="public-home-loved-card__avatar" aria-hidden="true">
        <img src={current.avatar} alt="" />
      </span>
      <div>
        <strong>Loved by guests</strong>
        <span className="public-home-loved-card__rating"><HomeStars rating={current.rating} /> {current.rating}</span>
        <small>{current.body}</small>
      </div>
    </article>
  );
}

function HomeExperience({ snapshot, userContext, language }: { snapshot: PublicSiteSnapshot; userContext: PublicUserContext; language: Language }) {
  const t = copy[language];
  const heroStay = snapshot.stays[0];
  const heroStats = [
    { label: 'Ready stays', value: String(snapshot.stays.length), icon: <Home size={18} />, tone: 'green' },
    { label: 'Guest rating', value: heroStay?.rating || '4.9', icon: <Star size={18} />, tone: 'blue', detail: heroStay?.reviewLabel },
    { label: 'Deposit hold', value: snapshot.depositAmount, icon: <CreditCard size={18} />, tone: 'orange' },
    { label: 'Agent limit', value: `${userContext.agent.questionLimit}/user`, icon: <Bot size={18} />, tone: 'indigo' },
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
            <span className="public-home-v5-favorite"><HeartHandshake size={15} /> Guest favorite</span>
            <b className="public-home-v5-rating-badge"><Star size={16} fill="currentColor" /> {heroStay.rating || '4.93'}</b>
            <StayImageRotator stay={heroStay} linkUrl={heroStay.detailUrl} className="public-stay-rotator--hero" defaultRotating showControls={false} />
            <div className="public-home-v5-hero-card__body">
              <span>{t.proof}</span>
              <a className="public-home-v5-hero-card__title-link" href={heroStay.detailUrl}>
                <h2>{formatStayName(heroStay.name)}</h2>
              </a>
              <p><HomeStars rating={heroStay.rating} /> {heroStay.reviewLabel}</p>
              <div className="public-hero__stay-metrics">
                {heroStay.statList.slice(0, 3).map((stat) => <b key={stat}>{normaliseStayStatLabel(stat)}</b>)}
              </div>
              <div className="public-home-v5-hero-card__split">
                <strong><span>{snapshot.depositAmount}</span>Deposit hold</strong>
                <strong><span>{userContext.agent.questionLimit}/user</span>Agent limit</strong>
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
        <HomeLovedGuestsCard snapshot={snapshot} />
      </section>

      <section id="stays" className="public-section public-home-v5-stays">
        <div className="public-section__heading">
          <h2>{t.staysTitle}</h2>
          <p>{t.staysText}</p>
        </div>
        <RotatingStayGrid stays={snapshot.stays} language={language} />
      </section>

      {heroStay && <HomeRulesMapSection snapshot={snapshot} stay={heroStay} language={language} />}

      <HomeTrustStrip snapshot={snapshot} />

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
          <h1>{formatStayName(stay.name)}</h1>
          <p>{stay.description}</p>
          <div className="public-proof-strip">
            <span><Star size={16} /> {stay.rating || 'Airbnb'} rating</span>
            {stay.statList.slice(0, 4).map((stat) => <span key={stat}>{stat}</span>)}
            <span><ShieldCheck size={16} /> {snapshot.depositAmount} deposit hold</span>
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
          <p>Every stay page now has a dedicated visual gallery area, ready for more apartment-specific images as we add them.</p>
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

      <section className="public-section public-feature-shell">
        <div className="public-two-col">
          <article>
            <h3>{t.highlights}</h3>
            {(stay.highlights.length ? stay.highlights : [
              { title: 'Strong Airbnb signal', body: stay.reviewLabel, sourceLabel: 'Airbnb' },
              { title: 'Group-friendly stay', body: 'A clear layout for families, travel groups, and Santo Domingo plans.', sourceLabel: 'MLADIS' },
            ]).slice(0, 4).map((highlight) => (
              <p key={highlight.title}><Sparkles size={15} /> <strong>{highlight.title}</strong> {highlight.body}</p>
            ))}
          </article>
          <RulesBook stay={stay} language={language} />
        </div>
      </section>

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

  return (
    <>
      <section className="public-subhero account-hero">
        <div>
          <h1>{t.accountTitle}</h1>
          <p>{t.accountText}</p>
          <div className="public-proof-strip">
            <span><Users size={16} /> {account.name}</span>
            <span><ReceiptText size={16} /> {account.reservations.length} reservations</span>
            <span><FileText size={16} /> {account.invoices.length} invoices</span>
            {account.isStaff && <span><ShieldCheck size={16} /> Admin access</span>}
          </div>
        </div>
      </section>

      {account.isStaff && <AccountAdminTools />}

      <section className="public-section account-modern">
        <div className="account-grid">
          <article className="account-list">
            <h2>Reservations</h2>
            {account.reservations.length === 0 && <p>No reservations yet. Start a stay request when you are ready.</p>}
            {account.reservations.map((reservation) => (
              <a className="account-reservation-row" href={reservation.detailUrl} key={reservation.id}>
                <span>{reservation.stayName}</span>
                <strong>{formatDate(reservation.checkIn)} to {formatDate(reservation.checkOut)}</strong>
                <small>{reservation.guests} guests · {reservation.status}</small>
              </a>
            ))}
          </article>

          <article className="account-detail">
            {!activeReservation && (
              <>
                <h2>Reservation center</h2>
                <p>Select a reservation to see details, edit eligible requests, or cancel when the current policy allows it.</p>
                <div className="account-invoice-grid">
                  {account.invoices.slice(0, 4).map((invoice) => (
                    <a href={invoice.printUrl} key={invoice.id}>
                      <ReceiptText size={18} />
                      <span>{invoice.title}</span>
                      <strong>{invoice.displayTotal}</strong>
                      <small>{invoice.status}</small>
                    </a>
                  ))}
                </div>
              </>
            )}
            {activeReservation && mode === 'detail' && <ReservationDetail reservation={activeReservation} />}
            {activeReservation && mode === 'edit' && <ReservationEditForm reservation={activeReservation} token={token} />}
            {activeReservation && mode === 'cancel' && <ReservationCancelForm reservation={activeReservation} token={token} />}
          </article>
        </div>
      </section>

      <AgentBookingSection snapshot={snapshot} userContext={userContext} stay={snapshot.stays[0]} language={language} />
    </>
  );
}

function AccountAdminTools() {
  const tools = [
    { label: 'Modern dashboard', href: '/ops/dashboard/', detail: 'Metrics, deposits, agent questions, and stay performance.' },
    { label: 'Reservations CRM', href: '/ops/reservations/', detail: 'Combined direct requests and imported Airbnb guest records.' },
    { label: 'Reports', href: '/ops/reports/', detail: 'Modern charts for visits, bookings, deposits, feedback, and agent questions.' },
    { label: 'Customers', href: '/ops/customers/', detail: 'Guest profiles, segments, consent, feedback, and promotion readiness.' },
    { label: 'Deposits', href: '/ops/deposits/', detail: 'Stripe and PayPal security deposit records in a modern ledger.' },
    { label: 'Agent workspace', href: '/ops/agent/', detail: 'Question analytics and FAQ training controls.' },
    { label: 'Business calendar', href: '/ops/calendar/', detail: 'Block dates, pricing overrides, and availability review.' },
    { label: 'Admin tools', href: '/admin/', detail: 'Full protected admin tools.' },
  ];
  return (
    <section className="public-section account-admin-tools">
      <div className="public-section__heading">
        <h2>Admin command center</h2>
        <p>You are signed in with staff access, so the operational tools are available from the modern account area.</p>
      </div>
      <div>
        {tools.map((tool) => (
          <a href={tool.href} key={tool.label}>
            <ShieldCheck size={18} />
            <strong>{tool.label}</strong>
            <span>{tool.detail}</span>
            <ArrowUpRight size={15} />
          </a>
        ))}
      </div>
    </section>
  );
}

function ReservationDetail({ reservation }: { reservation: AccountReservation }) {
  return (
    <>
      <h2>{reservation.stayName}</h2>
      <div className="account-detail-grid">
        <span><CalendarDays size={16} /> {formatDate(reservation.checkIn)} to {formatDate(reservation.checkOut)}</span>
        <span><Users size={16} /> {reservation.guests} guests</span>
        <span><ShieldCheck size={16} /> {reservation.displayDeposit || '$0.00 USD'} deposit</span>
        <span><CreditCard size={16} /> {reservation.displayTotal}</span>
      </div>
      <p>{reservation.message || 'No extra notes were added yet.'}</p>
      <div className="public-stay-card__actions">
        <a href={reservation.editUrl}><PencilLine size={15} /> Edit request</a>
        {reservation.canCancel && <a href={reservation.cancelUrl}>Cancel reservation</a>}
        {reservation.airbnbUrl && <a href={reservation.airbnbUrl} target="_blank" rel="noreferrer">Airbnb</a>}
      </div>
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

  useEffect(() => {
    window.localStorage.setItem('mladis_language', language);
  }, [language]);

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
    </main>
  );
}
