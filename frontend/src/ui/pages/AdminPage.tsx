import { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Download,
  ExternalLink,
  LockKeyhole,
  Mail,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  UserCog,
  Users,
  X,
  type LucideIcon,
} from 'lucide-react';
import { OpsWorkspaceFactory } from '../../application/OpsWorkspaceFactory';
import { OpsAdminSnapshot, OpsAdminUserRow, OpsMetric } from '../../domain/models';
import './ops-admin-page.css';

const metricIcons: LucideIcon[] = [Users, ShieldCheck, UserCog, CheckCircle2, LockKeyhole, Mail];
const metricTones = ['blue', 'green', 'violet', 'teal', 'orange', 'slate'];

function initials(row: OpsAdminUserRow) {
  const source = row.name || row.username || row.email || 'Admin';
  return source.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join('') || 'A';
}

function statusTone(row: OpsAdminUserRow) {
  if (!row.statusValue || row.statusValue === 'inactive') return 'red';
  if (row.accessStatusValue === 'protected') return 'green';
  if (row.accessStatusValue === 'invited') return 'orange';
  return 'blue';
}

function MetricCard({ metric, index }: { metric: OpsMetric; index: number }) {
  const Icon = metricIcons[index % metricIcons.length];
  const tone = metricTones[index % metricTones.length];
  return (
    <article className={`ops-admin-metric ops-admin-tone--${tone}`}>
      <span><Icon size={18} /></span>
      <div>
        <small>{metric.label}</small>
        <strong>{metric.value}</strong>
        <em>{metric.caption}</em>
      </div>
    </article>
  );
}

function StatusBadge({ label, tone }: { label: string; tone: string }) {
  return <span className={`ops-admin-badge ops-admin-badge--${tone}`}>{label}</span>;
}

function exportAdmin(snapshot: OpsAdminSnapshot) {
  const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `mladis-admin-access-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function AdminDetail({ row, onClose }: { row: OpsAdminUserRow; onClose: () => void }) {
  return (
    <aside className="ops-admin-detail">
      <button className="ops-admin-close" onClick={onClose} type="button" aria-label="Close admin details"><X size={17} /></button>
      <section className="ops-admin-person">
        <span className={`ops-admin-avatar ops-admin-avatar--${statusTone(row)}`}>{initials(row)}</span>
        <div>
          <h2>{row.name}</h2>
          <p>{row.email || 'Email missing'}</p>
          <strong>{row.username}</strong>
        </div>
      </section>

      <section className="ops-admin-facts">
        <div><small>Role</small><span>{row.role}</span></div>
        <div><small>Status</small><span>{row.status}</span></div>
        <div><small>Access</small><StatusBadge label={row.accessStatus} tone={statusTone(row)} /></div>
        <div><small>Staff</small><span>{row.isStaff ? 'Yes' : 'No'}</span></div>
      </section>

      <section className="ops-admin-section">
        <h3>Account timeline</h3>
        <ol>
          <li><i /><span>Joined</span><strong>{row.joined}</strong></li>
          <li><i /><span>Last login</span><strong>{row.lastLogin}</strong></li>
          <li><i /><span>Provisioning</span><strong>{row.accessStatus}</strong></li>
        </ol>
      </section>

      <section className="ops-admin-section">
        <h3>Access notes</h3>
        <p>{row.notes || 'No AdminAccess notes are attached to this operator yet.'}</p>
      </section>

      <section className="ops-admin-actions">
        <a className="ops-admin-primary" href={row.adminUrl}><UserCog size={15} /> Open Django user</a>
        <a href={row.accessAdminUrl}><ShieldCheck size={15} /> Access record</a>
        {row.email && <a href={`mailto:${row.email}`}><Mail size={15} /> Email operator</a>}
      </section>
    </aside>
  );
}

export function AdminPage() {
  const service = useMemo(() => OpsWorkspaceFactory.create(), []);
  const [snapshot, setSnapshot] = useState<OpsAdminSnapshot | null>(null);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [role, setRole] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    let mounted = true;
    service.loadAdmin()
      .then((data) => {
        if (mounted) setSnapshot(data);
      })
      .catch((caught: unknown) => {
        if (mounted) setError(caught instanceof Error ? caught.message : 'Could not load admin access.');
      });
    return () => {
      mounted = false;
    };
  }, [service]);

  const rows = useMemo(() => {
    if (!snapshot) return [];
    const query = search.trim().toLowerCase();
    return snapshot.rows.filter((row) => {
      const matchesRole = !role
        || row.roleValue === role
        || (role === 'inactive' && row.statusValue === 'inactive');
      const matchesSearch = !query || [
        row.name,
        row.username,
        row.email,
        row.phone,
        row.role,
        row.status,
        row.accessStatus,
        row.notes,
      ].some((value) => value.toLowerCase().includes(query));
      return matchesRole && matchesSearch;
    });
  }, [role, search, snapshot]);

  const selected = rows.find((row) => row.id === selectedId) || null;

  if (error) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!snapshot) {
    return <main className="dashboard-content ops-admin-page"><section className="ops-admin-card">Loading admin access...</section></main>;
  }

  return (
    <main className="dashboard-content ops-admin-page">
      <section className="ops-admin-titlebar">
        <div>
          <h1>Admin</h1>
          <p>Manage operators, staff access, protected accounts, and admin provisioning records.</p>
        </div>
        <div className="ops-admin-title-actions">
          <a href={snapshot.adminUrl}><UserCog size={16} /> Django users <ChevronDown size={15} /></a>
          <button type="button"><SlidersHorizontal size={16} /> Filters</button>
          <button type="button" onClick={() => exportAdmin(snapshot)}><Download size={16} /> Export</button>
        </div>
      </section>

      <section className="ops-admin-metric-grid">
        {snapshot.summaryCards.map((metric, index) => <MetricCard metric={metric} index={index} key={metric.label} />)}
      </section>

      <section className={`ops-admin-workspace ${selected ? 'is-detail-open' : ''}`}>
        <section className="ops-admin-card ops-admin-table-card">
          <div className="ops-admin-toolbar">
            <label>
              <Search size={15} />
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by name, email, role, notes..." />
              <kbd>⌘ F</kbd>
            </label>
            <div className="ops-admin-role-tabs">
              {snapshot.roleOptions.map((option) => (
                <button className={role === option.value ? 'is-active' : ''} key={option.value || 'all'} onClick={() => setRole(option.value)} type="button">
                  {option.label}
                  <small>{option.count}</small>
                </button>
              ))}
            </div>
          </div>

          <div className="ops-admin-table-scroll">
            <table>
              <colgroup>
                <col style={{ width: '34px' }} />
                <col style={{ width: '28%' }} />
                <col style={{ width: '16%' }} />
                <col style={{ width: '16%' }} />
                <col style={{ width: '16%' }} />
                <col style={{ width: '24%' }} />
              </colgroup>
              <thead>
                <tr>
                  <th />
                  <th>Operator</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Last Login</th>
                  <th>Access Notes</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr className={row.id === selectedId ? 'is-selected' : ''} key={row.id} onClick={() => setSelectedId((current) => (current === row.id ? null : row.id))}>
                    <td>
                      <button className={`ops-admin-check ${row.id === selectedId ? 'is-checked' : ''}`} type="button" aria-label={`Select ${row.name}`}>
                        {row.id === selectedId && <CheckCircle2 size={13} />}
                      </button>
                    </td>
                    <td>
                      <div className="ops-admin-user-cell">
                        <span className={`ops-admin-avatar ops-admin-avatar--${statusTone(row)}`}>{initials(row)}</span>
                        <span><strong>{row.name}</strong><small>{row.email || row.username}</small></span>
                      </div>
                    </td>
                    <td>{row.role}</td>
                    <td><StatusBadge label={row.accessStatus} tone={statusTone(row)} /></td>
                    <td>{row.lastLogin}</td>
                    <td>{row.notes || 'No notes'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <footer className="ops-admin-footer">
            <span>Showing {rows.length ? 1 : 0} to {rows.length} of {snapshot.rows.length} admin records</span>
            <nav aria-label="Admin pagination">
              <button type="button" aria-label="Previous page"><ChevronLeft size={16} /></button>
              <button className="is-active" type="button">1</button>
              <button type="button">2</button>
              <button type="button" aria-label="Next page"><ChevronRight size={16} /></button>
            </nav>
          </footer>
        </section>

        {selected && <AdminDetail row={selected} onClose={() => setSelectedId(null)} />}
      </section>

      <section className="ops-admin-shortcuts">
        <a href={snapshot.accessAdminUrl}><ShieldCheck size={16} /> Manage AdminAccess records <ExternalLink size={14} /></a>
        <a href="/ops/settings/"><LockKeyhole size={16} /> Review system settings <ExternalLink size={14} /></a>
      </section>
    </main>
  );
}
