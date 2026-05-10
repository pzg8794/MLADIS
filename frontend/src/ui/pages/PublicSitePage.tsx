import { useEffect, useMemo, useState, type FormEvent } from 'react';
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
} from 'lucide-react';
import { AccountFactory } from '../../application/AccountFactory';
import { PublicSiteFactory } from '../../application/PublicSiteFactory';
import { AccountReservation, AccountSnapshot, PublicSiteSnapshot, PublicStay } from '../../domain/models';

type Language = 'en' | 'es';
type LegalKind = 'business' | 'privacy' | 'terms' | 'data-deletion';

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
        <a href="/accounts/"><Home size={16} /> {t.navAccount}</a>
        <a href="/accounts/login/?next=/accounts/"><LogIn size={16} /> {t.signIn}</a>
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
    <section id="booking" className="public-section public-booking">
      <div className="public-section__heading public-booking__intro">
        <h2>{t.bookingTitle}</h2>
        <p>{t.bookingText}</p>
      </div>
      <div className="public-booking__grid">
        <article className="public-agent-card">
          <span><Bot size={19} /> {t.agentTitle}</span>
          <p>{t.agentText}</p>
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
          <div className="public-social-card">
            <strong>{t.social}</strong>
            <div>
              <a href="/accounts/login/?next=/accounts/">Google</a>
              <a href="/accounts/login/?next=/accounts/">Facebook</a>
              <a href="/accounts/login/?next=/accounts/">GitHub</a>
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
          </div>
        </div>
      </section>

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
  if (path.startsWith('/accounts')) content = <AccountExperience snapshot={snapshot} language={language} />;

  return (
    <main className="public-site">
      <PublicNav snapshot={snapshot} language={language} onLanguageChange={setLanguage} />
      {content}
    </main>
  );
}
