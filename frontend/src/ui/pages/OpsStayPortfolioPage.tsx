import { useMemo, useState } from 'react';
import {
  Bath,
  BedDouble,
  Building2,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Download,
  ExternalLink,
  Image,
  Search,
  SlidersHorizontal,
  Star,
  Users,
  Wrench,
  X,
} from 'lucide-react';
import './ops-stays-page.css';

const BASE = import.meta.env.BASE_URL;

type ListingTone = 'blue' | 'purple' | 'amber' | 'green' | 'orange' | 'red';
type ListingStatusTone = 'ready' | 'attention' | 'published';

class ListingTabModel {
  constructor(
    public readonly label: string,
    public readonly count: string,
    public readonly active = false,
    public readonly separated = false,
  ) {}
}

class ListingTagModel {
  constructor(
    public readonly label: string,
    public readonly tone: ListingTone,
  ) {}
}

class StayListingModel {
  constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly location: string,
    public readonly imageSrc: string,
    public readonly price: string,
    public readonly rating: string,
    public readonly reviews: string,
    public readonly bedrooms: string,
    public readonly beds: string,
    public readonly baths: string,
    public readonly guests: string,
    public readonly occupancy: string,
    public readonly occupancyTrend: string,
    public readonly readiness: string,
    public readonly readinessTone: ListingStatusTone,
    public readonly status: string,
    public readonly tags: ListingTagModel[],
  ) {}
}

class DetailMetricModel {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly caption: string,
    public readonly tone: ListingTone,
  ) {}
}

const tabs = [
  new ListingTabModel('All', '12', true),
  new ListingTabModel('Published', '11'),
  new ListingTabModel('Draft', '1'),
  new ListingTabModel('Inactive', '0'),
  new ListingTabModel('Maintenance', '1'),
  new ListingTabModel('Archived', '2', false, true),
];

const listings = [
  new StayListingModel(
    'g101',
    '3 Beds Apt, Vacation Home & Pool, G-101',
    'Colinas del Arroyo II, SDN',
    `${BASE}stays/stay-3br.jpg`,
    '$180',
    '4.93',
    '42 reviews',
    '3 bedrooms',
    '4 beds',
    '2 baths',
    '4 guests',
    '72%',
    '+12pp vs last 7 days',
    'Ready',
    'ready',
    'Published',
    [
      new ListingTagModel('Pool', 'blue'),
      new ListingTagModel('Self check-in', 'purple'),
      new ListingTagModel('$200 Secure hold', 'amber'),
      new ListingTagModel('Direct booking', 'green'),
    ],
  ),
  new StayListingModel(
    'pool-6br',
    '6 Beds Apt, Vacation Home & Pool',
    'Colinas del Arroyo II, SDN',
    `${BASE}stays/stay-6br.jpg`,
    '$250',
    '4.87',
    '37 reviews',
    '6 bedrooms',
    '8 beds',
    '3 baths',
    '8 guests',
    '68%',
    '+8pp vs last 7 days',
    'Ready',
    'ready',
    'Published',
    [
      new ListingTagModel('Pool', 'blue'),
      new ListingTagModel('Self check-in', 'purple'),
      new ListingTagModel('$200 Secure hold', 'amber'),
      new ListingTagModel('Direct booking', 'green'),
    ],
  ),
  new StayListingModel(
    'pool-2br',
    '2 Beds Apt, Vacation Home & Pool',
    'Colinas del Arroyo II, SDN',
    `${BASE}stays/stay-2br.jpg`,
    '$120',
    '4.76',
    '28 reviews',
    '2 bedrooms',
    '3 beds',
    '2 baths',
    '3 guests',
    '52%',
    '-4pp vs last 7 days',
    'Needs attention',
    'attention',
    'Published',
    [
      new ListingTagModel('Pool', 'blue'),
      new ListingTagModel('Self check-in', 'purple'),
      new ListingTagModel('$200 Secure hold', 'amber'),
      new ListingTagModel('Direct booking', 'green'),
    ],
  ),
];

const availability = [
  new DetailMetricModel('Occupancy', '72%', 'Next 7 days', 'blue'),
  new DetailMetricModel('ADR', '$146', '+9% vs last 7 days', 'green'),
];

function ListingTabs() {
  return (
    <nav className="stays-v4-tabs" aria-label="Listing status">
      {tabs.map((tab) => (
        <button className={`${tab.active ? 'is-active' : ''}${tab.separated ? ' is-separated' : ''}`} type="button" key={tab.label}>
          {tab.label}
          <span>{tab.count}</span>
        </button>
      ))}
    </nav>
  );
}

function ListingFilterBar() {
  return (
    <div className="stays-v4-filterbar">
      <label className="stays-v4-search">
        <Search size={15} />
        <input aria-label="Search stays" placeholder="Search by stay name, property, area..." readOnly />
        <kbd>⌘ F</kbd>
      </label>
      {[
        ['Area', 'All areas'],
        ['Property', 'All properties'],
        ['Status', 'All statuses'],
      ].map(([label, value]) => (
        <button className="stays-v4-select" type="button" key={label}>
          <small>{label}</small>
          <span>{value}</span>
          <ChevronDown size={14} />
        </button>
      ))}
      <button className="stays-v4-more" type="button">More filters</button>
    </div>
  );
}

function AmenityRow({ listing }: { listing: StayListingModel }) {
  const amenities = [
    [BedDouble, listing.bedrooms],
    [BedDouble, listing.beds],
    [Bath, listing.baths],
    [Users, listing.guests],
  ];

  return (
    <div className="stays-v4-amenities">
      {amenities.map(([Icon, label]) => (
        <span key={String(label)}><Icon size={14} /> {String(label)}</span>
      ))}
    </div>
  );
}

function StatusDot({ tone, label }: { tone: ListingStatusTone; label: string }) {
  return <span className={`stays-v4-dot stays-v4-dot--${tone}`}><i /> {label}</span>;
}

function ListingCard({
  listing,
  selected,
  onSelect,
}: {
  listing: StayListingModel;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <article className={`stays-v4-listing${selected ? ' is-selected' : ''}`} onClick={() => onSelect(listing.id)}>
      <button className={`stays-v4-check ${selected ? 'is-checked' : ''}`} type="button" aria-label={`Select ${listing.name}`}>
        {selected && <CheckCircle2 size={13} />}
      </button>
      <img src={listing.imageSrc} alt={listing.name} />
      <section className="stays-v4-listing-main">
        <h2>{listing.name}</h2>
        <p>{listing.location}</p>
        <div className="stays-v4-rating"><Star size={14} fill="currentColor" /> {listing.rating} <span>({listing.reviews})</span></div>
        <AmenityRow listing={listing} />
        <div className="stays-v4-tags">
          {listing.tags.map((tag) => <span className={`stays-v4-tag stays-v4-tag--${tag.tone}`} key={tag.label}>{tag.label}</span>)}
        </div>
      </section>
      <aside className="stays-v4-listing-stats">
        <strong>{listing.price} <span>/ night</span></strong>
        <dl>
          <div>
            <dt>Occupancy</dt>
            <dd>{listing.occupancy}<small className={listing.occupancyTrend.startsWith('-') ? 'is-down' : ''}>{listing.occupancyTrend}</small></dd>
          </div>
          <div>
            <dt>Readiness</dt>
            <dd><StatusDot tone={listing.readinessTone} label={listing.readiness} /></dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd><StatusDot tone="published" label={listing.status} /></dd>
          </div>
        </dl>
      </aside>
    </article>
  );
}

function ListingList({
  selectedId,
  onSelect,
}: {
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  return (
    <section className="stays-v4-list-card">
      <ListingFilterBar />
      <div className="stays-v4-list">
        {listings.map((listing) => <ListingCard listing={listing} selected={listing.id === selectedId} onSelect={onSelect} key={listing.id} />)}
      </div>
      <footer className="stays-v4-list-footer">
        <span>Showing 1 to 3 of 12 results</span>
        <nav aria-label="Listings pagination">
          <button type="button" aria-label="Previous page"><ChevronLeft size={15} /></button>
          <button className="is-active" type="button">1</button>
          <button type="button">2</button>
          <button type="button">3</button>
          <button type="button">4</button>
          <button type="button" aria-label="Next page"><ChevronRight size={15} /></button>
        </nav>
        <a href="/ops/stays/">View archived listings <ChevronRight size={14} /></a>
      </footer>
    </section>
  );
}

function AvailabilitySparkline() {
  return (
    <svg className="stays-v4-detail-sparkline" viewBox="0 0 128 38" preserveAspectRatio="none" aria-hidden="true">
      <path d="M0 27 L14 22 L26 24 L38 14 L49 20 L59 10 L72 23 L84 17 L96 21 L110 13 L128 24" />
    </svg>
  );
}

function MiniMap() {
  return (
    <div className="stays-v4-minimap" aria-hidden="true">
      <span />
      <i />
      <b />
    </div>
  );
}

function DetailSmallCards() {
  return (
    <div className="stays-v4-detail-grid">
      <article className="stays-v4-detail-card stays-v4-detail-card--availability">
        <h3>Availability Snapshot</h3>
        <small>Next 7 days</small>
        <div className="stays-v4-availability">
          {availability.map((metric) => (
            <div className={`stays-v4-availability__metric stays-v4-availability__metric--${metric.tone}`} key={metric.label}>
              <strong>{metric.value}</strong>
              <span>{metric.label}</span>
              <em>{metric.caption}</em>
            </div>
          ))}
          <AvailabilitySparkline />
        </div>
      </article>
      <article className="stays-v4-detail-card">
        <h3>Location &amp; Area</h3>
        <p>Colinas del Arroyo II,<br />Santo Domingo Norte</p>
        <MiniMap />
        <small><Building2 size={13} /> 8 min to Embassy</small>
      </article>
      <article className="stays-v4-detail-card">
        <h3>Housekeeping Readiness</h3>
        <dl className="stays-v4-detail-list">
          <div><dt>Status</dt><dd className="is-green">Ready <ChevronRight size={12} /></dd></div>
          <div><dt>Next clean</dt><dd>Today, 11:00 AM</dd></div>
          <div><dt>Cleaner</dt><dd>María Rodríguez <span>MR</span></dd></div>
        </dl>
      </article>
      <article className="stays-v4-detail-card">
        <h3>Maintenance Status</h3>
        <dl className="stays-v4-detail-list">
          <div><dt>Open Work Orders</dt><dd className="is-orange">1</dd></div>
          <div><dt>Overdue</dt><dd className="is-green">0</dd></div>
          <div><dt>Last inspection</dt><dd>Jun 4, 2026 <CheckCircle2 size={13} /></dd></div>
        </dl>
      </article>
    </div>
  );
}

function SelectedListingPanel({ selected }: { selected: StayListingModel }) {
  return (
    <aside className="stays-v4-selected">
      <header>
        <h2>Selected listing</h2>
        <button type="button" aria-label="Close selected listing"><X size={16} /></button>
      </header>
      <div className="stays-v4-selected-hero">
        <img src={selected.imageSrc} alt={selected.name} />
        <span className="stays-v4-published">Published</span>
        <span className="stays-v4-gallery-count"><Image size={12} /> 1/18</span>
      </div>
      <section className="stays-v4-selected-main">
        <h2>{selected.name}</h2>
        <p>{selected.location}</p>
        <div className="stays-v4-selected-row">
          <span><Star size={14} fill="currentColor" /> {selected.rating} from {selected.reviews} Airbnb reviews</span>
          <em>Direct booking enabled <CheckCircle2 size={14} /></em>
        </div>
        <div className="stays-v4-selected-actions">
          <button type="button">Preview public page <ExternalLink size={14} /></button>
          <button type="button"><Wrench size={14} /> Edit listing</button>
          <button className="is-primary" type="button"><CalendarDays size={14} /> Open calendar</button>
        </div>
      </section>
      <DetailSmallCards />
      <section className="stays-v4-reservations">
        <h3>Linked Reservations</h3>
        <div>
          <span><small>Upcoming (Next 7 days)</small><strong>2 bookings</strong></span>
          <span><small>Total guests</small><strong>4</strong></span>
          <button type="button">View reservations</button>
        </div>
      </section>
      <footer className="stays-v4-tagline">
        <span>Public page tagline: Vacation stays in Santo Domingo Norte</span>
        <a href="/ops/settings/">Edit</a>
      </footer>
    </aside>
  );
}

export function OpsStayPortfolioPage() {
  const [selectedId, setSelectedId] = useState(listings[0].id);
  const selected = useMemo(() => listings.find((listing) => listing.id === selectedId) ?? listings[0], [selectedId]);

  return (
    <main className="dashboard-content stays-v4-page">
      <section className="stays-v4-titlebar">
        <div>
          <h1>Stays &amp; Listings</h1>
          <p>Manage live listings, public content, amenities, pricing, and operational readiness.</p>
        </div>
        <div className="stays-v4-title-actions">
          <button type="button"><SlidersHorizontal size={16} /> Filters</button>
          <button type="button"><Download size={16} /> Export</button>
          <button className="is-primary" type="button">+ Add New Listing</button>
        </div>
      </section>

      <ListingTabs />

      <section className="stays-v4-workspace">
        <ListingList selectedId={selectedId} onSelect={setSelectedId} />
        <SelectedListingPanel selected={selected} />
      </section>
    </main>
  );
}
