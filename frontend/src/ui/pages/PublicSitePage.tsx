import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { ChatKit, useChatKit } from '@openai/chatkit-react';
import {
  ArrowUpRight,
  Bot,
  CalendarDays,
  CheckCircle2,
  CreditCard,
  FileText,
  Globe2,
  HeartHandshake,
  Home,
  LogIn,
  MapPin,
  MessageSquareText,
  PencilLine,
  ReceiptText,
  ShieldCheck,
  Sparkles,
  Star,
  Users,
  Clock,
  XCircle,
  DollarSign,
} from 'lucide-react';
import { AccountFactory } from '../../application/AccountFactory';
import { PublicSiteFactory } from '../../application/PublicSiteFactory';
import { AccountReservation, AccountSnapshot, PublicSiteSnapshot, PublicStay } from '../../domain/models';

type Language = 'en' | 'es';
type LegalKind = 'business' | 'privacy' | 'terms' | 'data-deletion';


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

type AuthNavState = {
  status: 'checking' | 'anonymous' | 'authenticated';
  name?: string;
  isStaff?: boolean;
};

const copy = {
  en: {
    navStays: 'Stays',
    navArea: 'Area',
    navBooking: 'Book',
    navAbout: 'About',
    navAccount: 'Account',
    signIn: 'Sign in',
    heroTitle: 'Modern vacation stays in Santo Domingo Norte.',
    heroText:
      'Pool-ready apartments near Colinas del Arroyo II, Los Guaricanos, Jacobo Majluta, malls, restaurants, and the Embassy corridor.',
    primary: 'Start booking',
    secondary: 'Explore stays',
    proof: 'Airbnb review signals',
    staysTitle: 'Choose your stay',
    staysText: 'Each apartment keeps its own images, guest proof, rules, and direct booking path.',
    areaTitle: 'More than a place to sleep',
    areaText:
      'Sell the trip, not only the room: city errands, food, malls, beach-day options, and hosted support from Santo Domingo Norte.',
    bookingTitle: 'Ask first, then book with confidence',
    bookingText:
      'The agent sits beside the booking form so guests can ask about rules, deposits, location, and the best fit before starting a reservation.',
    agentTitle: 'MLADIS booking agent',
    agentText: 'Ask about availability, guest count, deposit holds, house rules, transportation, or which apartment fits your group.',
    formTitle: 'Start a reservation',
    formText: 'Phone is required for booking. The $200 secure deposit hold appears after the request starts.',
    highlights: 'Top guest highlights',
    rules: 'Apartment rules',
    mission: 'Travel with mission',
    social: 'Account access',
    submit: 'Make secure deposit hold',
    details: 'Details',
    airbnb: 'Airbnb',
    gallery: 'Gallery',
    aboutTitle: 'Hosted stays for Santo Domingo days, family plans, and island time.',
    aboutText:
      'MLADIS gives guests a practical Santo Domingo Norte base with warm host support, access to city errands, mall corridors, restaurants, and day-trip beaches like Juan Dolio or Boca Chica.',
    aboutMission:
      'We want every stay to support a larger mission: better guest care, local opportunity, and charity work for children, education, and families who need support.',
    accountTitle: 'Your MLADIS reservations',
    accountText: 'Manage requests, watch cancellation windows, review invoices, and keep your booking details in one place.',
  },
  es: {
    navStays: 'Estadías',
    navArea: 'Zona',
    navBooking: 'Reservar',
    navAbout: 'Nosotros',
    navAccount: 'Cuenta',
    signIn: 'Entrar',
    heroTitle: 'Estadías modernas en Santo Domingo Norte.',
    heroText:
      'Apartamentos con piscina cerca de Colinas del Arroyo II, Los Guaricanos, Jacobo Majluta, plazas, restaurantes y la zona de la Embajada.',
    primary: 'Empezar reserva',
    secondary: 'Ver estadías',
    proof: 'Señales de reseñas Airbnb',
    staysTitle: 'Elige tu estadía',
    staysText: 'Cada apartamento conserva sus propias imágenes, prueba social, reglas y ruta de reserva.',
    areaTitle: 'Más que un lugar para dormir',
    areaText:
      'Vendemos el viaje completo: diligencias, comida, plazas, playa y apoyo anfitrión desde Santo Domingo Norte.',
    bookingTitle: 'Pregunta primero y reserva con confianza',
    bookingText:
      'El agente está al lado del formulario para responder sobre reglas, depósito, ubicación y el mejor apartamento antes de iniciar la reserva.',
    agentTitle: 'Agente de reservas MLADIS',
    agentText: 'Pregunta por disponibilidad, cantidad de huéspedes, depósito, reglas, transporte o cuál apartamento te conviene.',
    formTitle: 'Iniciar reserva',
    formText: 'El teléfono es requerido para reservar. El depósito seguro de $200 aparece después de iniciar la solicitud.',
    highlights: 'Comentarios destacados',
    rules: 'Reglas del apartamento',
    mission: 'Viaja con misión',
    social: 'Acceso de cuenta',
    submit: 'Make secure deposit hold',
    details: 'Detalles',
    airbnb: 'Airbnb',
    gallery: 'Galería',
    aboutTitle: 'Estadías anfitrionas para Santo Domingo, planes familiares y tiempo de isla.',
    aboutText:
      'MLADIS ofrece una base práctica en Santo Domingo Norte con apoyo anfitrión, acceso a diligencias, plazas, restaurantes y playas como Juan Dolio o Boca Chica.',
    aboutMission:
      'Queremos que cada estadía apoye una misión mayor: mejor servicio, oportunidades locales y ayuda para niños, educación y familias que necesitan apoyo.',
    accountTitle: 'Tus reservas MLADIS',
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

function formatDate(value: string) {
  if (!value) return '';
  const [year, month, day] = value.split('-').map(Number);
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(
    new Date(Date.UTC(year, month - 1, day)),
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
  language,
  onLanguageChange,
}: {
  snapshot: PublicSiteSnapshot;
  language: Language;
  onLanguageChange: (language: Language) => void;
}) {
  const t = copy[language];
  const [auth, setAuth] = useState<AuthNavState>({ status: 'checking' });

  useEffect(() => {
    let active = true;

    fetch('/api/account/summary/', {
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
      .then(async (response) => {
        if (!active) return;
        const contentType = response.headers.get('content-type') || '';
        if (!response.ok || !contentType.includes('application/json')) {
          setAuth({ status: 'anonymous' });
          return;
        }

        const data = await response.json() as {
          authenticated?: boolean;
          profile?: {
            name?: string;
            email?: string;
            is_staff?: boolean;
            is_superuser?: boolean;
          } | null;
          is_staff?: boolean;
          is_superuser?: boolean;
        };

        if (!data.profile || data.authenticated === false) {
          setAuth({ status: 'anonymous' });
          return;
        }

        setAuth({
          status: 'authenticated',
          name: data.profile.name || data.profile.email,
          isStaff: Boolean(data.profile.is_staff || data.profile.is_superuser || data.is_staff || data.is_superuser),
        });
      })
      .catch(() => {
        if (active) setAuth({ status: 'anonymous' });
      });

    return () => {
      active = false;
    };
  }, []);

  const isAuthenticated = auth.status === 'authenticated';
  const showAdmin = isAuthenticated && auth.isStaff === true;

  return (
    <header className="public-nav">
      <a className="public-brand" href="/">
        {snapshot.logoUrl ? <img src={snapshot.logoUrl} alt={snapshot.siteName} /> : <span>M</span>}
        <strong>{snapshot.siteName}</strong>
      </a>
      <nav aria-label="Primary">
        <a href="/#stays">{t.navStays}</a>
        <a href="/#area">{t.navArea}</a>
        <a href="/about/">{t.navAbout}</a>
        <a href="/#booking">{t.navBooking}</a>
      </nav>
      <div className="public-nav__actions">
        <button type="button" onClick={() => onLanguageChange(language === 'en' ? 'es' : 'en')}>
          <Globe2 size={16} /> {language === 'en' ? 'ES' : 'EN'}
        </button>

        {isAuthenticated ? (
          <>
            <a href="/accounts/" title={auth.name ? `Signed in as ${auth.name}` : 'Signed in'}>
              <Home size={16} /> {t.navAccount}
            </a>
            {showAdmin && (
              <a href="/ops/admin/">
                <ShieldCheck size={16} /> Admin
              </a>
            )}
            <form method="post" action="/accounts/logout/" className="public-nav-logout">
              <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken()} />
              <button type="submit">
                <LogIn size={16} /> Sign out
              </button>
            </form>
          </>
        ) : (
          <>
            <a href="/accounts/">
              <Home size={16} /> {t.navAccount}
            </a>
            <a href="/accounts/login/?next=/accounts/">
              <LogIn size={16} /> {auth.status === 'checking' ? 'Checking...' : t.signIn}
            </a>
          </>
        )}
      </div>
    </header>
  );
}

function StayCard({ stay, language }: { stay: PublicStay; language: Language }) {
  const t = copy[language];
  return (
    <article className="public-stay-card">
      <img src={stay.imageUrl} alt={stay.name} />
      <div className="public-stay-card__body">
        <div>
          <h3>{stay.name}</h3>
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

function chatKitOptions(language: Language) {
  return {
    frameTitle: copy[language].agentTitle,
    theme: {
      colorScheme: 'light' as const,
      radius: 'soft' as const,
      density: 'compact' as const,
    },
    thread: { autoScroll: true },
    history: {
      enabled: true,
      showDelete: false,
      showRename: false,
    },
    header: {
      title: { text: copy[language].agentTitle },
    },
    composer: {
      placeholder:
        language === 'en'
          ? 'Ask about dates, guest count, rules, or deposit holds.'
          : 'Pregunta por fechas, cantidad de huéspedes, reglas o depósito.',
    },
    startScreen: {
      greeting: copy[language].agentText,
      prompts:
        language === 'en'
          ? [
            { label: 'Check availability', prompt: 'Do you have availability for next weekend?' },
            { label: 'Deposit hold', prompt: 'How does the secure deposit hold work?' },
            { label: 'Best fit', prompt: 'Which stay is best for four guests?' },
          ]
          : [
            { label: 'Ver disponibilidad', prompt: 'Tienen disponibilidad para el próximo fin de semana?' },
            { label: 'Depósito', prompt: 'Cómo funciona el depósito seguro?' },
            { label: 'Mejor opción', prompt: 'Cuál estadía conviene para cuatro huéspedes?' },
          ],
    },
  };
}

function ManagedChatKitAgent({ sessionUrl, token, language }: { sessionUrl: string; token: string; language: Language }) {
  const { control } = useChatKit({
    ...chatKitOptions(language),
    api: {
      async getClientSecret() {
        const response = await fetch(sessionUrl, {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': token,
          },
        });
        const data = await response.json() as { client_secret?: string; error?: string };
        if (!response.ok || !data.client_secret) {
          throw new Error(data.error || 'Could not start the booking chat.');
        }
        return data.client_secret;
      },
    },
  });

  return (
    <div className="public-agent-chatkit-shell">
      <ChatKit control={control} className="public-agent-chatkit" />
    </div>
  );
}

function CustomChatKitAgent({ apiUrl, domainKey, language }: { apiUrl: string; domainKey: string; language: Language }) {
  const { control } = useChatKit({
    ...chatKitOptions(language),
    api: {
      url: apiUrl,
      domainKey,
      fetch(input, init) {
        return fetch(input, { ...init, credentials: 'include' });
      },
    },
  });

  return (
    <div className="public-agent-chatkit-shell">
      <ChatKit control={control} className="public-agent-chatkit" />
    </div>
  );
}

function LegacyAgentPrompt({ stay, token }: { stay?: PublicStay | null; token: string }) {
  const [agentMessage, setAgentMessage] = useState('');
  const [agentReply, setAgentReply] = useState('');
  const [agentBusy, setAgentBusy] = useState(false);

  async function askAgent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
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
      const data = await response.json() as { reply?: string; error?: string; session_id?: string };
      if (data.session_id) window.sessionStorage.setItem('mladis_agent_session', data.session_id);
      setAgentReply(data.reply || data.error || 'The agent did not return a reply yet.');
    } catch {
      setAgentReply('I could not reach the agent API from this browser session.');
    } finally {
      setAgentBusy(false);
    }
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
  stay,
  language,
}: {
  snapshot: PublicSiteSnapshot;
  stay?: PublicStay | null;
  language: Language;
}) {
  const t = copy[language];
  const token = csrfToken();
  const submitted = new URLSearchParams(window.location.search).get('submitted') === '1';
  const managedChatKit = snapshot.chatKit?.mode === 'managed' ? snapshot.chatKit : null;
  const customChatKit = snapshot.chatKit?.mode === 'custom' ? snapshot.chatKit : null;

  return (
    <section id="booking" className="public-section public-booking">
      <div className="public-section__heading public-booking__intro">
        <h2>{t.bookingTitle}</h2>
        <p>{t.bookingText}</p>
      </div>
      <div className="public-booking__grid">
        <article className="public-agent-card">
          <span><Bot size={19} /> {t.agentTitle}</span>
          <p>{t.agentText}</p>
          {managedChatKit?.sessionUrl ? (
            <ManagedChatKitAgent sessionUrl={managedChatKit.sessionUrl} token={token} language={language} />
          ) : customChatKit?.apiUrl && customChatKit.domainKey ? (
            <CustomChatKitAgent apiUrl={customChatKit.apiUrl} domainKey={customChatKit.domainKey} language={language} />
          ) : (
            <LegacyAgentPrompt stay={stay} token={token} />
          )}
          <div className="public-social-card">
            <strong>{t.social}</strong>
            <div>
              {snapshot.socialProviders.length > 0 ? (
                snapshot.socialProviders.map((provider) => (
                  provider.isLaunchable ? (
                    <form method="post" action={provider.loginUrl} key={provider.id}>
                      <input type="hidden" name="csrfmiddlewaretoken" value={token} />
                      <button type="submit">{provider.label}</button>
                    </form>
                  ) : (
                    <span
                      className="public-social-card__disabled"
                      title={provider.helpText || provider.disabledReason}
                      key={provider.id}
                    >
                      {provider.label}
                      <small>{provider.disabledReason || 'setup needed'}</small>
                    </span>
                  )
                ))
              ) : (
                <a href="/accounts/login/?next=/accounts/">Account login</a>
              )}
            </div>
          </div>
        </article>

        <form className="public-booking-form" method="post" action="/inquiries/">
          <input type="hidden" name="csrfmiddlewaretoken" value={token} />
          <div>
            <h3>{t.formTitle}</h3>
            <p>{t.formText}</p>
          </div>
          {submitted && <p className="public-success">Request received. Continue to the secure deposit hold when prompted.</p>}
          <label>
            Stay
            <select name="item" defaultValue={stay?.id ?? ''}>
              <option value="">Flexible / help me choose</option>
              {snapshot.stays.map((availableStay) => (
                <option value={availableStay.id} key={availableStay.id}>{availableStay.name}</option>
              ))}
            </select>
          </label>
          <div className="public-form-row">
            <label>Name<input name="guest_name" required /></label>
            <label>Phone<input name="phone" required /></label>
          </div>
          <label>Email<input type="email" name="email" required /></label>
          <div className="public-form-row">
            <label>Check in<input type="date" name="check_in" required /></label>
            <label>Check out<input type="date" name="check_out" required /></label>
          </div>
          <div className="public-form-row">
            <label><Users size={15} /> Guests<input type="number" name="guests" min="1" defaultValue="1" required /></label>
            <label>Coupon<input name="coupon_code" /></label>
          </div>
          <label>Notes<textarea name="message" rows={3} /></label>
          <button type="submit"><CreditCard size={17} /> {t.submit}</button>
        </form>
      </div>
    </section>
  );
}

function RulesBook({ stay, language }: { stay: PublicStay; language: Language }) {
  const t = copy[language];
  const rules = stay.rules.length ? stay.rules : [
    { title: 'Respectful noise', description: 'Keep music and visitors respectful so every guest and neighbor can enjoy the property.' },
    { title: 'Registered guests only', description: 'Booking details should match the group staying at the apartment.' },
    { title: 'Pool care', description: 'Use shared amenities with care and follow posted hours.' },
    { title: 'No smoking inside', description: 'Please keep interiors fresh for the next guest.' },
  ];
  const midpoint = Math.ceil(rules.length / 2);
  return (
    <article className="rules-book">
      <div className="rules-book__page">
        <h3>{t.rules}</h3>
        {rules.slice(0, midpoint).map((rule) => (
          <p key={rule.title}>
            <CheckCircle2 size={16} />
            <span className="rules-book__copy"><strong>{rule.title}:</strong><span>{rule.description}</span></span>
          </p>
        ))}
      </div>
      <div className="rules-book__page">
        <h3>Stay rhythm</h3>
        {rules.slice(midpoint).map((rule) => (
          <p key={rule.title}>
            <CheckCircle2 size={16} />
            <span className="rules-book__copy"><strong>{rule.title}:</strong><span>{rule.description}</span></span>
          </p>
        ))}
      </div>
    </article>
  );
}

function HomeExperience({ snapshot, language }: { snapshot: PublicSiteSnapshot; language: Language }) {
  const t = copy[language];
  const heroStay = snapshot.stays[0];
  const secondStay = snapshot.stays[1] ?? heroStay;
  return (
    <>
      <section className="public-hero">
        <div className="public-hero__copy">
          <h1>{t.heroTitle}</h1>
          <p>{t.heroText}</p>
          <div className="public-hero__actions">
            <a href="#booking">{t.primary} <ArrowUpRight size={17} /></a>
            <a href="#stays">{t.secondary}</a>
          </div>
          <div className="public-proof-strip">
            <span><Star size={16} /> {heroStay?.rating || '4.9'}</span>
            <span><MapPin size={16} /> {snapshot.publicAddressLabel}</span>
            <span><ShieldCheck size={16} /> {snapshot.depositAmount} deposit hold</span>
          </div>
        </div>
        {heroStay && (
          <article className="public-hero__stay">
            <img src={heroStay.imageUrl} alt={heroStay.name} />
            <div>
              <span>{t.proof}</span>
              <h2>{heroStay.name}</h2>
              <p>{heroStay.reviewLabel}</p>
            </div>
          </article>
        )}
      </section>

      <section id="stays" className="public-section">
        <div className="public-section__heading">
          <h2>{t.staysTitle}</h2>
          <p>{t.staysText}</p>
        </div>
        <div className="public-stay-grid">
          {snapshot.stays.map((stay) => <StayCard stay={stay} language={language} key={stay.id} />)}
        </div>
      </section>

      <AreaSection snapshot={snapshot} language={language} />
      <AgentBookingSection snapshot={snapshot} stay={heroStay} language={language} />

      {secondStay && (
        <section className="public-section public-detail-strip">
          <div>
            <h2>{secondStay.name}</h2>
            <p>{secondStay.description}</p>
          </div>
          <div className="public-gallery-rail">
            {(secondStay.gallery.length ? secondStay.gallery : [{ imageUrl: secondStay.imageUrl, altText: secondStay.name, caption: secondStay.name }])
              .slice(0, 4)
              .map((image) => <img src={image.imageUrl} alt={image.altText} key={image.imageUrl} />)}
          </div>
          <div className="public-two-col">
            <article>
              <h3>{t.highlights}</h3>
              {secondStay.highlights.slice(0, 3).map((highlight) => (
                <p key={highlight.title}><Sparkles size={15} /> <strong>{highlight.title}</strong> {highlight.body}</p>
              ))}
            </article>
            <RulesBook stay={secondStay} language={language} />
          </div>
        </section>
      )}

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

function StayDetailExperience({ snapshot, stay, language }: { snapshot: PublicSiteSnapshot; stay: PublicStay; language: Language }) {
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
            <span><Star size={16} /> {stay.rating || 'Airbnb'} rating</span>
            {stay.statList.slice(0, 4).map((stat) => <span key={stat}>{stat}</span>)}
            <span><ShieldCheck size={16} /> {snapshot.depositAmount} deposit hold</span>
          </div>
          <div className="public-hero__actions">
            <a href="#booking">{t.primary} <ArrowUpRight size={17} /></a>
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

      <AgentBookingSection snapshot={snapshot} stay={stay} language={language} />
    </>
  );
}

function AboutExperience({ snapshot, language }: { snapshot: PublicSiteSnapshot; language: Language }) {
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
      <AgentBookingSection snapshot={snapshot} stay={snapshot.stays[0]} language={language} />
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

function AccountExperience({ snapshot, language }: { snapshot: PublicSiteSnapshot; language: Language }) {
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

      <AgentBookingSection snapshot={snapshot} stay={snapshot.stays[0]} language={language} />
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
    { label: 'Business calendar', href: '/admin/bookings/bookableitem/calendar/', detail: 'Block dates, pricing overrides, and availability review.' },
    { label: 'Django admin', href: '/admin/', detail: 'Full source-of-truth admin tools.' },
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
  return (
    <form className="public-booking-form" method="post" action={currentPath()}>
      <input type="hidden" name="csrfmiddlewaretoken" value={token} />
      <h2>Edit reservation request</h2>
      <label>Phone<input name="phone" defaultValue={reservation.phone} required /></label>
      <div className="public-form-row">
        <label>Check in<input type="date" name="check_in" defaultValue={reservation.checkIn} required /></label>
        <label>Check out<input type="date" name="check_out" defaultValue={reservation.checkOut} required /></label>
      </div>
      <label>Guests<input type="number" name="guests" min="1" defaultValue={reservation.guests} required /></label>
      <label>Notes<textarea name="message" rows={4} defaultValue={reservation.message} /></label>
      <button type="submit"><PencilLine size={17} /> Save changes</button>
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
      <section className="public-section">
        <div className="account-modern">
          <div className="account-header">
            <h1>Admin Dashboard</h1>
            <p>Loading admin data...</p>
          </div>
        </div>
      </section>
    );
  }

  if (!adminData) {
    return (
      <section className="public-section">
        <div className="account-modern">
          <div className="account-header">
            <h1>Admin Dashboard</h1>
            <p>Unable to load admin data. Please check your permissions.</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="public-section account-modern">
      <div className="account-header">
        <h1>
          <ShieldCheck size={24} /> Admin Dashboard
        </h1>
        <p>Manage reservations and view system statistics</p>
      </div>

      {actionMessage && (
        <div style={{
          padding: 'var(--space-4)',
          background: 'var(--color-success-highlight)',
          color: 'var(--color-success)',
          borderRadius: 'var(--radius-md)',
          marginBottom: 'var(--space-6)'
        }}>
          {actionMessage}
        </div>
      )}

      {/* Stats Grid */}
      <div className="account-stats">
        <span>
          <Clock size={16} /> {adminData.pendingCount} pending
        </span>
        <span>
          <CheckCircle2 size={16} /> {adminData.confirmedCount} confirmed
        </span>
        <span>
          <XCircle size={16} /> {adminData.cancelledCount} cancelled
        </span>
        <span>
          <DollarSign size={16} /> {adminData.totalRevenue} total revenue
        </span>
      </div>

      {/* Reservations Table */}
      <div className="account-grid">
        <article className="account-list" style={{ gridColumn: '1 / -1' }}>
          <h2>All Reservations ({adminData.reservations.length})</h2>

          {adminData.reservations.length === 0 ? (
            <p>No reservations in the system yet.</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: 'var(--text-sm)'
              }}>
                <thead>
                  <tr style={{
                    borderBottom: '2px solid var(--color-divider)',
                    textAlign: 'left'
                  }}>
                    <th style={{ padding: 'var(--space-3)' }}>Guest</th>
                    <th style={{ padding: 'var(--space-3)' }}>Stay</th>
                    <th style={{ padding: 'var(--space-3)' }}>Dates</th>
                    <th style={{ padding: 'var(--space-3)' }}>Guests</th>
                    <th style={{ padding: 'var(--space-3)' }}>Total</th>
                    <th style={{ padding: 'var(--space-3)' }}>Status</th>
                    <th style={{ padding: 'var(--space-3)' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {adminData.reservations.map((reservation) => (
                    <tr
                      key={reservation.id}
                      style={{
                        borderBottom: '1px solid var(--color-divider)'
                      }}
                    >
                      <td style={{ padding: 'var(--space-3)' }}>
                        <strong>{reservation.guestName}</strong><br />
                        <small style={{ color: 'var(--color-text-muted)' }}>
                          {reservation.guestEmail}
                        </small>
                        {reservation.phone && (
                          <><br /><small style={{ color: 'var(--color-text-muted)' }}>
                            {reservation.phone}
                          </small></>
                        )}
                      </td>
                      <td style={{ padding: 'var(--space-3)' }}>{reservation.stayName}</td>
                      <td style={{ padding: 'var(--space-3)' }}>
                        {formatDate(reservation.checkIn)} → {formatDate(reservation.checkOut)}
                      </td>
                      <td style={{ padding: 'var(--space-3)' }}>{reservation.guests}</td>
                      <td style={{ padding: 'var(--space-3)' }}>
                        <strong>{reservation.totalDisplay}</strong>
                      </td>
                      <td style={{ padding: 'var(--space-3)' }}>
                        <span style={{
                          display: 'inline-block',
                          padding: 'var(--space-1) var(--space-2)',
                          borderRadius: 'var(--radius-full)',
                          fontSize: 'var(--text-xs)',
                          fontWeight: 500,
                          background:
                            reservation.status === 'confirmed' ? 'var(--color-success-highlight)' :
                            reservation.status === 'cancelled' ? 'var(--color-error-highlight)' :
                            'var(--color-warning-highlight)',
                          color:
                            reservation.status === 'confirmed' ? 'var(--color-success)' :
                            reservation.status === 'cancelled' ? 'var(--color-error)' :
                            'var(--color-warning)'
                        }}>
                          {reservation.status}
                        </span>
                      </td>
                      <td style={{ padding: 'var(--space-3)' }}>
                        {reservation.status === 'pending' && (
                          <>
                            <button
                              onClick={() => handleStatusChange(reservation.id, 'confirmed')}
                              style={{
                                padding: 'var(--space-1) var(--space-3)',
                                marginRight: 'var(--space-2)',
                                background: 'var(--color-success)',
                                color: 'white',
                                border: 'none',
                                borderRadius: 'var(--radius-sm)',
                                cursor: 'pointer',
                                fontSize: 'var(--text-xs)'
                              }}
                            >
                              Confirm
                            </button>
                            <button
                              onClick={() => handleStatusChange(reservation.id, 'cancelled')}
                              style={{
                                padding: 'var(--space-1) var(--space-3)',
                                background: 'var(--color-error)',
                                color: 'white',
                                border: 'none',
                                borderRadius: 'var(--radius-sm)',
                                cursor: 'pointer',
                                fontSize: 'var(--text-xs)'
                              }}
                            >
                              Cancel
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>
      </div>
    </section>
  );
}

export function PublicSitePage() {
  const service = useMemo(() => PublicSiteFactory.create(), []);
  const [snapshot, setSnapshot] = useState<PublicSiteSnapshot | null>(null);
  const [error, setError] = useState('');
  const [language, setLanguage] = useState<Language>(() => (window.localStorage.getItem('mladis_language') === 'es' ? 'es' : 'en'));

  useEffect(() => {
    window.localStorage.setItem('mladis_language', language);
  }, [language]);

  useEffect(() => {
    let active = true;
    service
      .loadSite()
      .then((data) => {
        if (active) setSnapshot(data);
      })
      .catch((caught: unknown) => {
        if (active) setError(caught instanceof Error ? caught.message : 'Could not load the modern site.');
      });
    return () => {
      active = false;
    };
  }, [service]);

  if (!snapshot && !error) return <PublicSiteSkeleton />;
  if (!snapshot) return <main className="public-site"><section className="dashboard-error">{error}</section></main>;

  const stay = findStayByPath(snapshot);
  const legalKind = legalKindFromPath();
  const path = currentPath();

  let content = <HomeExperience snapshot={snapshot} language={language} />;
  if (stay) content = <StayDetailExperience snapshot={snapshot} stay={stay} language={language} />;
  if (path.startsWith('/about')) content = <AboutExperience snapshot={snapshot} language={language} />;
  if (legalKind) content = <LegalExperience snapshot={snapshot} kind={legalKind} />;
    if (path.startsWith('/ops/admin')) content = <AdminExperience language={language} />;
  if (path.startsWith('/accounts')) content = <AccountExperience snapshot={snapshot} language={language} />;

  return (
    <main className="public-site">
      <PublicNav snapshot={snapshot} language={language} onLanguageChange={setLanguage} />
      {content}
    </main>
  );
}
