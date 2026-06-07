import { ArrowUpRight, ChevronRight, CreditCard } from 'lucide-react';
import { DepositSummary } from '../../domain/models';
import { StatusBadge } from './StatusBadge';
import { StatusBadgePresenter } from './StatusBadgePresenter';
import { formatStayName } from '../helpers/stayNames';

interface DepositPanelProps {
  deposits: DepositSummary[];
}

export function DepositPanel({ deposits }: DepositPanelProps) {
  return (
    <details className="dashboard-panel dashboard-collapse-card">
      <summary className="panel-heading dashboard-panel-summary">
        <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
        <span className="panel-heading__icon"><CreditCard size={19} /></span>
        <div>
          <h2>Latest deposits</h2>
          <p>Newest security deposit records. Open the ledger for all deposits.</p>
        </div>
        <a className="panel-action-link" href="/ops/deposits/" onClick={(event) => event.stopPropagation()}>
          Open deposits <ArrowUpRight size={14} />
        </a>
      </summary>
      <div className="compact-list">
        {deposits.map((deposit) => (
          <div key={deposit.id}>
            <span>
              <strong>{deposit.guestName}</strong>
              <small>{deposit.provider} · {formatStayName(deposit.stayName)}</small>
            </span>
            <span>
              <strong>{deposit.amount.format()}</strong>
              <StatusBadge label={StatusBadgePresenter.labelForStatus(deposit.status)} tone={StatusBadgePresenter.toneForStatus(deposit.status)} />
            </span>
          </div>
        ))}
      </div>
    </details>
  );
}
