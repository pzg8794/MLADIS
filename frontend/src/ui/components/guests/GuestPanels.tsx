import type { ComponentType } from 'react';
import { CalendarDays, CheckCircle2, CreditCard, FileText, Mail, MessageSquare, ShieldCheck, Sparkles, Tag, UserRound } from 'lucide-react';
import { Guest, GuestDetailTab } from '../../../domain/guests';

const detailTabs: Array<{ id: GuestDetailTab; label: string; icon: ComponentType<{ size?: number }> }> = [
  { id: 'messages', label: 'Messages', icon: MessageSquare },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'payments', label: 'Payments', icon: CreditCard },
  { id: 'deposits', label: 'Deposits', icon: ShieldCheck },
  { id: 'activity', label: 'Activity', icon: CalendarDays },
];

export function GuestProfileCard({ guest }: { guest: Guest }) {
  const profile = guest.profileProjection();
  return (
    <article className="guests-profile-card">
      <div className="guests-profile-card__head">
        <span className="guests-avatar guests-avatar--large">{guest.identity.initials}</span>
        <div>
          <h3>{guest.displayName}</h3>
          <p>{guest.contact.primary}</p>
          <span>{guest.identity.country}</span>
        </div>
        <span className={`guests-status guests-status--${guest.segment.tone}`}>{guest.segment.label}</span>
      </div>
      <a className="guests-profile-link" href={profile.fullProfileUrl || profile.adminUrl}>
        <UserRound size={15} />
        View full profile
      </a>
      <dl className="guests-profile-facts">
        <div>
          <dt>Preferred language</dt>
          <dd>{guest.identity.preferredLanguage.toUpperCase()}</dd>
        </div>
        <div>
          <dt>Birthday</dt>
          <dd>{profile.birthday || 'Not captured'}</dd>
        </div>
        <div>
          <dt>Travel style</dt>
          <dd>{profile.travelStyle}</dd>
        </div>
        <div>
          <dt>Guest since</dt>
          <dd>{profile.guestSince}</dd>
        </div>
      </dl>
      <div className="guests-profile-tags">
        {guest.tags.map((tag) => (
          <span className={`guests-tag guests-tag--${tag.tone}`} key={tag.slug}>
            <Tag size={12} />
            {tag.label}
          </span>
        ))}
      </div>
      <div className="guests-notes">
        <strong>Notes</strong>
        <p>{profile.notes}</p>
      </div>
    </article>
  );
}

export function GuestDetailPanel({
  activeTab,
  guest,
  onTabChange,
}: {
  activeTab: GuestDetailTab;
  guest: Guest;
  onTabChange: (tab: GuestDetailTab) => void;
}) {
  return (
    <article className="guests-detail-card">
      <div className="guests-detail-tabs" role="tablist" aria-label="Guest detail tabs">
        {detailTabs.map(({ id, label, icon: Icon }) => (
          <button
            aria-selected={activeTab === id}
            className={activeTab === id ? 'is-active' : ''}
            key={id}
            onClick={() => onTabChange(id)}
            role="tab"
            type="button"
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>
      {activeTab === 'messages' && <GuestMessages guest={guest} />}
      {activeTab === 'documents' && <GuestDocuments guest={guest} />}
      {activeTab === 'payments' && <GuestPayments guest={guest} />}
      {activeTab === 'deposits' && <GuestDeposits guest={guest} />}
      {activeTab === 'activity' && <GuestActivity guest={guest} />}
    </article>
  );
}

export function GuestMessageComposer({
  confirmed,
  disabled,
  draft,
  notice,
  onConfirmedChange,
  onDraftChange,
  onSend,
}: {
  confirmed: boolean;
  disabled: boolean;
  draft: string;
  notice: string;
  onConfirmedChange: (value: boolean) => void;
  onDraftChange: (value: string) => void;
  onSend: () => void;
}) {
  return (
    <article className="guests-action-card">
      <div className="guests-card-title">
        <Sparkles size={17} />
        <div>
          <h3>Guest action panel</h3>
          <p>Drafts stay internal unless staff approval is checked.</p>
        </div>
      </div>
      <textarea
        disabled={disabled}
        onChange={(event) => onDraftChange(event.target.value)}
        placeholder="Type a message for this guest..."
        value={draft}
      />
      <label className="guests-confirm-row">
        <input checked={confirmed} disabled={disabled} onChange={(event) => onConfirmedChange(event.target.checked)} type="checkbox" />
        Staff approved outbound send
      </label>
      <button className="guests-primary-action" disabled={disabled || !draft.trim()} onClick={onSend} type="button">
        <Mail size={16} />
        {confirmed ? 'Send confirmed message' : 'Stage draft'}
      </button>
      {notice && <p className="guests-notice">{notice}</p>}
    </article>
  );
}

export function GuestLinkedStaysPanel({ guest }: { guest: Guest }) {
  const stays = guest.staysProjection();
  return (
    <article className="guests-linked-card">
      <div className="guests-card-title">
        <CalendarDays size={17} />
        <div>
          <h3>Last stays</h3>
          <p>Linked reservations and imported Airbnb records.</p>
        </div>
      </div>
      <div className="guests-linked-list">
        {stays.length ? stays.slice(0, 4).map((stay) => (
          <a href={stay.reservation_url || '#'} key={stay.id}>
            <span>{stay.reservation_key}</span>
            <strong>{stay.listing_name}</strong>
            <small>{stay.date_range} - {stay.status}</small>
          </a>
        )) : (
          <p>No linked stays yet.</p>
        )}
      </div>
    </article>
  );
}

function GuestMessages({ guest }: { guest: Guest }) {
  const messages = guest.messageProjection().items;
  return (
    <div className="guests-thread-list">
      {messages.map((message) => (
        <div className={message.from_staff ? 'is-staff' : ''} key={message.id}>
          <span>{message.sender_label} - {message.timestamp}</span>
          <p>{message.body}</p>
          <small>{message.status}</small>
        </div>
      ))}
    </div>
  );
}

function GuestDocuments({ guest }: { guest: Guest }) {
  return (
    <div className="guests-table-list">
      {guest.documentsProjection().map((document) => (
        <a href={document.url || '#'} key={document.id}>
          <FileText size={16} />
          <span>{document.title}</span>
          <small>{document.type}</small>
          <strong>{document.status}</strong>
        </a>
      ))}
    </div>
  );
}

function GuestPayments({ guest }: { guest: Guest }) {
  const payments = guest.paymentsProjection();
  return (
    <div className="guests-table-list">
      <div className="guests-summary-strip">
        <span>Total spend</span>
        <strong>{payments.totalSpend.withCurrency}</strong>
        <small>{payments.paymentCount} linked records</small>
      </div>
      {payments.items.length ? payments.items.map((payment) => (
        <a href={payment.url || '#'} key={payment.id}>
          <CreditCard size={16} />
          <span>{payment.label}</span>
          <small>{payment.date}</small>
          <strong>{payment.amount.with_currency}</strong>
        </a>
      )) : <p>No linked payments yet.</p>}
    </div>
  );
}

function GuestDeposits({ guest }: { guest: Guest }) {
  const deposits = guest.depositsProjection();
  return (
    <div className="guests-table-list">
      <div className="guests-summary-strip">
        <span>Deposit holds</span>
        <strong>{deposits.activeHolds} active</strong>
        <small>{deposits.releasedHolds} released - {deposits.disputeCount} disputes</small>
      </div>
      {deposits.items.length ? deposits.items.map((deposit) => (
        <a href={deposit.url || '#'} key={deposit.id}>
          <ShieldCheck size={16} />
          <span>{deposit.label}</span>
          <small>{deposit.date}</small>
          <strong>{deposit.amount.with_currency}</strong>
        </a>
      )) : <p>No linked deposits yet.</p>}
    </div>
  );
}

function GuestActivity({ guest }: { guest: Guest }) {
  return (
    <div className="guests-activity-list">
      {guest.activityProjection().map((event) => (
        <div key={`${event.type}-${event.timestamp}-${event.label}`}>
          <CheckCircle2 size={15} />
          <span>
            <strong>{event.label}</strong>
            <small>{event.timestamp} by {event.actor}</small>
          </span>
          <p>{event.note}</p>
        </div>
      ))}
    </div>
  );
}
