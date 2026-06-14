import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, BriefcaseBusiness, Building2, FileText, Mail, MapPin, ShieldCheck } from 'lucide-react';
import { PublicSiteFactory } from '../../application/PublicSiteFactory';
import { PublicSiteSnapshot } from '../../domain/models';

export function OpsBusinessPage() {
  const service = useMemo(() => PublicSiteFactory.create(), []);
  const [snapshot, setSnapshot] = useState<PublicSiteSnapshot | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    service
      .loadSite()
      .then((data) => {
        if (mounted) setSnapshot(data);
      })
      .catch((caught: unknown) => {
        if (mounted) setError(caught instanceof Error ? caught.message : 'Could not load business profile.');
      });
    return () => {
      mounted = false;
    };
  }, [service]);

  if (error) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!snapshot) {
    return <main className="dashboard-content ops-page"><section className="ops-hero is-loading" /></main>;
  }

  return (
    <main className="dashboard-content ops-page ops-page--business">
      <section className="ops-hero ops-hero--business">
        <div>
          <span><BriefcaseBusiness size={16} /> Business profile</span>
          <h2>Business profile</h2>
          <p>Public company details, contact points, booking controls, and compliance links in the same operations frame.</p>
        </div>
        <div className="ops-hero-actions">
          <a href="/admin/bookings/sitesettings/1/change/"><ShieldCheck size={16} /> Brand settings</a>
          <a href="/"><Building2 size={16} /> Open site</a>
        </div>
      </section>

      <section className="ops-metric-grid ops-business-metrics">
        <article>
          <span>Public name</span>
          <strong>{snapshot.siteName}</strong>
          <p>Shown in the website header and account surfaces.</p>
        </article>
        <article>
          <span>Contact</span>
          <strong>{snapshot.contactEmail}</strong>
          <p>Primary inbox for guest and business requests.</p>
        </article>
        <article>
          <span>Location</span>
          <strong>{snapshot.publicAddressLabel}</strong>
          <p>Public operating area shown to guests.</p>
        </article>
        <article>
          <span>Booking deposit</span>
          <strong>{snapshot.depositAmount}</strong>
          <p>Current security hold displayed before checkout.</p>
        </article>
      </section>

      <section className="ops-split-grid">
        <article className="ops-table-card ops-business-card">
          <div className="ops-card-heading">
            <div>
              <span><FileText size={15} /> Legal profile</span>
              <h3>Guest-facing documents</h3>
              <p>Keep these links aligned with the live business and social provider requirements.</p>
            </div>
          </div>
          <div className="ops-business-link-grid">
            <a href="/business/">Business profile</a>
            <a href="/privacy/">Privacy policy</a>
            <a href="/terms/">Terms</a>
            <a href="/data-deletion/">Data deletion</a>
          </div>
        </article>
        <article className="ops-table-card ops-business-card">
          <div className="ops-card-heading">
            <div>
              <span><Mail size={15} /> Operations</span>
              <h3>{snapshot.stays.length} stays online</h3>
              <p>Bookings, deposits, maintenance, reports, and agent behavior should stay tied to these records.</p>
            </div>
          </div>
          <div className="ops-business-link-grid">
            <a href="/ops/stays/"><MapPin size={14} /> Stay portfolio</a>
            <a href="/ops/reservations/">Reservations</a>
            <a href="/ops/deposits/">Deposits</a>
            <a href="/ops/maintenance/">Maintenance</a>
          </div>
        </article>
      </section>
    </main>
  );
}
