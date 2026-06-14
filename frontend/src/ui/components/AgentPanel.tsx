import { ArrowUpRight, Bot, ChevronRight, MessageSquareText } from 'lucide-react';
import { AgentQuestionSummary } from '../../domain/models';
import { StatusBadge } from './StatusBadge';
import { StatusBadgePresenter } from './StatusBadgePresenter';

interface AgentPanelProps {
  questions: AgentQuestionSummary[];
}

export function AgentPanel({ questions }: AgentPanelProps) {
  return (
    <details className="dashboard-panel agent-panel dashboard-collapse-card">
      <summary className="panel-heading dashboard-panel-summary">
        <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
        <span className="panel-heading__icon"><Bot size={19} /></span>
        <div>
          <h2>Latest agent questions</h2>
          <p>Recent guest questions and routing mode.</p>
        </div>
        <a className="panel-action-link" href="/ops/agent/" onClick={(event) => event.stopPropagation()}>
          Open agent <ArrowUpRight size={14} />
        </a>
      </summary>
      <div className="agent-score">
        <strong>64%</strong>
        <span>answered locally</span>
      </div>
      <div className="compact-list">
        {questions.map((question) => (
          <div key={question.id}>
            <span>
              <strong><MessageSquareText size={15} /> {question.topic}</strong>
              <small>{question.lastQuestion}</small>
            </span>
            <StatusBadge label={StatusBadgePresenter.labelForStatus(question.mode)} tone={StatusBadgePresenter.toneForStatus(question.mode)} />
          </div>
        ))}
      </div>
    </details>
  );
}
