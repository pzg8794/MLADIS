import { ReactNode, useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { OpsListModal } from './OpsListModal';

interface OpsRecordSectionProps<T> {
  rows: T[];
  renderRow: (row: T) => ReactNode;
  eyebrow: string;
  title: string;
  subtitle: string;
  modalTitle: string;
  modalSubtitle: string;
  actionLabel?: string;
  aside?: ReactNode;
  toolbar?: ReactNode;
  notice?: ReactNode;
  emptyState?: ReactNode;
  defaultVisible?: number;
  className?: string;
  listClassName?: string;
  limitLabel?: string;
}

function normalizeLimit(value: number, total: number) {
  if (total <= 0) return 0;
  if (!Number.isFinite(value)) return Math.min(3, total);
  return Math.max(1, Math.min(total, Math.floor(value)));
}

export function OpsRecordSection<T>({
  rows,
  renderRow,
  eyebrow,
  title,
  subtitle,
  modalTitle,
  modalSubtitle,
  actionLabel = 'Open list',
  aside,
  toolbar,
  notice,
  emptyState,
  defaultVisible = 3,
  className = 'ops-table-card',
  listClassName = 'ops-list-scroll',
  limitLabel = 'Records visible',
}: OpsRecordSectionProps<T>) {
  const [isOpen, setIsOpen] = useState(false);
  const [visibleLimit, setVisibleLimit] = useState(() => normalizeLimit(defaultVisible, rows.length));

  const safeVisibleLimit = normalizeLimit(visibleLimit || defaultVisible, rows.length);
  const visibleRows = useMemo(() => rows.slice(0, safeVisibleLimit), [rows, safeVisibleLimit]);

  function updateVisibleLimit(value: string) {
    setVisibleLimit(normalizeLimit(Number(value), rows.length));
  }

  return (
    <>
      <section className={className}>
        <div className="ops-card-heading ops-record-heading">
          <div>
            <span>{eyebrow}</span>
            <h3>{title}</h3>
            <p>{rows.length > 0 ? `${visibleRows.length} visible here. ${subtitle}` : subtitle}</p>
          </div>
          <div className="ops-card-heading__actions">
            {rows.length > 0 && (
              <label className="ops-inline-stepper">
                Show
                <input
                  aria-label={limitLabel}
                  type="number"
                  min={1}
                  max={rows.length}
                  step={1}
                  value={safeVisibleLimit}
                  onChange={(event) => updateVisibleLimit(event.target.value)}
                />
              </label>
            )}
            <button type="button" onClick={() => setIsOpen(true)} disabled={rows.length === 0}>
              <Search size={15} /> {actionLabel}
            </button>
            {aside}
          </div>
        </div>

        {notice}
        {toolbar}
        {rows.length === 0 && emptyState}

        <div className={listClassName}>
          {visibleRows.map(renderRow)}
        </div>
      </section>

      <OpsListModal
        isOpen={isOpen}
        title={modalTitle}
        subtitle={modalSubtitle}
        onClose={() => setIsOpen(false)}
      >
        {rows.map(renderRow)}
      </OpsListModal>
    </>
  );
}
