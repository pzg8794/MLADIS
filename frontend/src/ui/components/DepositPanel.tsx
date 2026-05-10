import { CreditCard } from 'lucide-react';
import { DepositSummary } from '../../domain/models';
import { StatusBadge } from './StatusBadge';
import { StatusBadgePresenter } from './StatusBadgePresenter';

interface DepositPanelProps {
  deposits: DepositSummary[];
}

export function DepositPanel({ deposits }: DepositPanelProps) {
  return (
    <article className="dashboard-panel">
      <header className="panel-heading">
        <span className="panel-heading__icon"><CreditCard size={19} /></span>
        <div>
          <h2>Deposit holds</h2>
          <p>Safe authorizations only. Capture and release actions stay in Django admin.</p>
        </div>
      </header>
      <div className="compact-list">
        {deposits.map((deposit) => (
          <div key={deposit.id}>
            <span>
              <strong>{deposit.guestName}</strong>
              <small>{deposit.provider} · {deposit.stayName}</small>
            </span>
            <span>
              <strong>{deposit.amount.format()}</strong>
              <StatusBadge label={StatusBadgePresenter.labelForStatus(deposit.status)} tone={StatusBadgePresenter.toneForStatus(deposit.status)} />
            </span>
          </div>
        ))}
      </div>
    </article>
  );
}
