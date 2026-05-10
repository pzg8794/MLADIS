import { Bot, MessageSquareText } from 'lucide-react';
import { AgentQuestionSummary } from '../../domain/models';
import { StatusBadge } from './StatusBadge';
import { StatusBadgePresenter } from './StatusBadgePresenter';

interface AgentPanelProps {
  questions: AgentQuestionSummary[];
}

export function AgentPanel({ questions }: AgentPanelProps) {
  return (
    <article className="dashboard-panel agent-panel">
      <header className="panel-heading">
        <span className="panel-heading__icon"><Bot size={19} /></span>
        <div>
          <h2>Agent intelligence</h2>
          <p>Watch what guests ask before booking and tune the FAQ layer.</p>
        </div>
      </header>
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
    </article>
  );
}
