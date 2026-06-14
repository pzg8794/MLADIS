import { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Circle,
  ExternalLink,
  ListChecks,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { OpsWorkspaceFactory } from '../../application/OpsWorkspaceFactory';
import { OpsWorkboardSnapshot, OpsWorkItem } from '../../domain/models';

function priorityClass(priority: string) {
  return `ops-work-chip ops-work-chip--${priority || 'medium'}`;
}

function statusClass(status: string) {
  return `ops-work-chip ops-work-chip--status-${status || 'captured'}`;
}

function readableDate(value: string) {
  if (!value) return 'Not updated';
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value));
}

function WorkItemCard({
  item,
  busy,
  onToggle,
}: {
  item: OpsWorkItem;
  busy: boolean;
  onToggle: (item: OpsWorkItem) => void;
}) {
  const links = [
    { label: 'Source', href: item.sourceUrl },
    { label: 'GitHub', href: item.githubUrl },
    { label: 'Drive', href: item.driveUrl },
  ].filter((link) => link.href);

  return (
    <article className={`ops-work-item${item.isDone ? ' is-done' : ''}`}>
      <button
        type="button"
        className="ops-work-item__check"
        aria-pressed={item.isDone}
        aria-label={item.isDone ? `Mark ${item.title} open` : `Mark ${item.title} done`}
        disabled={busy}
        onClick={() => onToggle(item)}
      >
        {item.isDone ? <CheckCircle2 size={18} /> : <Circle size={18} />}
      </button>
      <div>
        <header>
          <div>
            <h4>{item.title}</h4>
            <p>{item.nextAction || item.description || 'No next action recorded yet.'}</p>
          </div>
          <span className={priorityClass(item.priority)}>{item.priorityLabel}</span>
        </header>
        <div className="ops-work-item__meta">
          <span className={statusClass(item.status)}>{item.statusLabel}</span>
          <span>{item.neuronLabel}</span>
          <span>{readableDate(item.updatedAt)}</span>
        </div>
        {item.description && item.nextAction && <p className="ops-work-item__description">{item.description}</p>}
        {links.length > 0 && (
          <div className="ops-work-item__links">
            {links.map((link) => (
              <a href={link.href} key={link.label} target="_blank" rel="noreferrer">
                {link.label} <ExternalLink size={13} />
              </a>
            ))}
          </div>
        )}
      </div>
    </article>
  );
}

export function OpsWorkboardPage() {
  const service = useMemo(() => OpsWorkspaceFactory.create(), []);
  const [snapshot, setSnapshot] = useState<OpsWorkboardSnapshot | null>(null);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState<number | null>(null);

  function load() {
    setError('');
    service
      .loadWorkboard()
      .then(setSnapshot)
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : 'Could not load workboard.');
      });
  }

  useEffect(() => {
    load();
  }, [service]);

  async function toggleItem(item: OpsWorkItem) {
    setBusyId(item.id);
    try {
      await service.setWorkItemCompletion(item.id, !item.isDone);
      load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not update this work item.');
    } finally {
      setBusyId(null);
    }
  }

  if (error && !snapshot) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!snapshot) {
    return <main className="dashboard-content ops-page"><section className="ops-hero is-loading" /></main>;
  }

  return (
    <main className="dashboard-content ops-page ops-page--workboard">
      <section className="ops-hero ops-hero--workboard">
        <div>
          <span><ListChecks size={16} /> Owner workboard</span>
          <h2>Workboard</h2>
          <p>Business tasks, architecture work, product fixes, and next actions grouped by MLADIS neuron.</p>
        </div>
        <div className="ops-hero-actions">
          <button type="button" onClick={load}><RefreshCw size={16} /> Refresh</button>
          <a href="/admin/operations/operationsworkitem/add/"><ListChecks size={16} /> Add item</a>
        </div>
      </section>

      {error && <section className="dashboard-error"><AlertCircle /> {error}</section>}

      <section className="ops-metric-grid ops-work-summary">
        {snapshot.summaryCards.map((card, index) => (
          <article key={card.label} className={`ops-work-summary-card ops-work-summary-card--${index + 1}`}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <p>{card.caption}</p>
          </article>
        ))}
      </section>

      <section className="ops-work-focus">
        <div className="ops-card-heading">
          <div>
            <span><Sparkles size={15} /> Focus</span>
            <h3>Next actions</h3>
            <p>Only active items are shown here so the board stays useful instead of noisy.</p>
          </div>
        </div>
        <div className="ops-work-focus-grid">
          {snapshot.focusItems.length === 0 && <p>Nothing active. Nice.</p>}
          {snapshot.focusItems.map((item) => (
            <WorkItemCard item={item} busy={busyId === item.id} key={item.id} onToggle={toggleItem} />
          ))}
        </div>
      </section>

      <section className="ops-work-list-groups" aria-label="Work item lists">
        {snapshot.lists.map((list) => (
          <details className="ops-work-list ops-expand-card" key={list.name}>
            <summary className="ops-card-heading">
              <div>
                <span>Work list</span>
                <h3>{list.name}</h3>
                <p>{list.open} open, {list.done} done.</p>
              </div>
              <strong>{list.total}</strong>
            </summary>
            <div className="ops-work-list__items">
              {list.items.map((item) => (
                <WorkItemCard item={item} busy={busyId === item.id} key={item.id} onToggle={toggleItem} />
              ))}
            </div>
          </details>
        ))}
      </section>
    </main>
  );
}
