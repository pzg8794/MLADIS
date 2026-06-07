import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, Bot, BrainCircuit, ChevronRight, ExternalLink, MessageSquareText, Search, Sparkles } from 'lucide-react';
import { OpsWorkspaceFactory } from '../../application/OpsWorkspaceFactory';
import { OpsAgentConversation, OpsAgentFaq, OpsAgentSnapshot } from '../../domain/models';
import { OpsListModal } from '../components/OpsListModal';

function modeLabel(mode: string) {
  if (mode === 'openai') return 'OpenAI';
  if (mode === 'faq') return 'FAQ';
  if (mode === 'guardrail') return 'Guardrail';
  return 'Fallback';
}

export function OpsAgentPage() {
  const service = useMemo(() => OpsWorkspaceFactory.create(), []);
  const [snapshot, setSnapshot] = useState<OpsAgentSnapshot | null>(null);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [isQuestionsOpen, setIsQuestionsOpen] = useState(false);

  useEffect(() => {
    let mounted = true;
    service
      .loadAgent()
      .then((data) => {
        if (mounted) setSnapshot(data);
      })
      .catch((caught: unknown) => {
        if (mounted) setError(caught instanceof Error ? caught.message : 'Could not load agent workspace.');
      });
    return () => {
      mounted = false;
    };
  }, [service]);

  const conversations = useMemo(() => {
    if (!snapshot) return [];
    const query = search.trim().toLowerCase();
    if (!query) return snapshot.conversations;
    return snapshot.conversations.filter((row) => [row.topic, row.mode, row.item, row.visitor, row.lastQuestion, row.lastReply].some((value) => value.toLowerCase().includes(query)));
  }, [search, snapshot]);

  const faqs = useMemo(() => {
    if (!snapshot) return [];
    const query = search.trim().toLowerCase();
    if (!query) return snapshot.faqs;
    return snapshot.faqs.filter((row) => [row.question, row.answer, row.category, row.keywords, row.item].some((value) => value.toLowerCase().includes(query)));
  }, [search, snapshot]);

  const renderConversationRow = (row: OpsAgentConversation) => (
    <details className="ops-data-row ops-data-row--agent ops-expand-card" data-status={row.mode} key={row.id}>
      <summary className="ops-data-summary">
        <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
        <div>
          <span className={`ops-status-pill ops-status-pill--${row.mode}`}>{modeLabel(row.mode)}</span>
          <h3>{row.topic || 'General'}</h3>
          <p>{row.visitor} · {row.item}</p>
        </div>
        <div>
          <strong>{row.lastQuestion}</strong>
          <p>{row.language.toUpperCase()} · {row.updatedAt ? new Date(row.updatedAt).toLocaleString() : 'Update pending'}</p>
        </div>
      </summary>
      <div className="ops-expand-details">
        <div>
          <span>Last reply</span>
          <p>{row.lastReply || 'No reply captured yet.'}</p>
        </div>
        <div className="ops-row-actions">
          <a href={row.adminUrl}>Conversation</a>
        </div>
      </div>
    </details>
  );

  const renderFaqRow = (faq: OpsAgentFaq) => (
    <details className="ops-faq-card ops-expand-card" key={faq.id}>
      <summary className="ops-faq-summary">
        <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
        <div>
          <span className={`ops-status-pill ${faq.isActive ? 'ops-status-pill--active' : 'ops-status-pill--inactive'}`}>{faq.isActive ? 'Active' : 'Inactive'}</span>
          <small>{faq.category} · {faq.item} · {faq.language}</small>
          <h3>{faq.question}</h3>
        </div>
      </summary>
      <div className="ops-expand-details">
        <div>
          <span>Answer</span>
          <p>{faq.answer}</p>
          {faq.keywords && <strong>{faq.keywords}</strong>}
        </div>
        <a href={faq.adminUrl}>Edit FAQ</a>
      </div>
    </details>
  );

  if (error) {
    return <section className="dashboard-error"><AlertCircle /> {error}</section>;
  }

  if (!snapshot) {
    return <main className="dashboard-content ops-page"><section className="ops-hero is-loading" /></main>;
  }

  return (
    <main className="dashboard-content ops-page">
      <section className="ops-hero ops-hero--agent">
        <div>
          <span><Bot size={16} /> Agent workspace</span>
          <h2>Agent training</h2>
          <p>Use real customer questions to improve FAQ answers, guardrails, and booking support.</p>
        </div>
        <div className="ops-hero-actions">
          <a href={snapshot.faqAdminUrl}><BrainCircuit size={16} /> Manage FAQs</a>
          <a href={snapshot.conversationAdminUrl}><ExternalLink size={16} /> Conversation admin</a>
        </div>
      </section>

      <section className="ops-metric-grid">
        {snapshot.summaryCards.map((card) => (
          <article key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <p>{card.caption}</p>
          </article>
        ))}
      </section>

      <section className="ops-toolbar">
        <label>
          <Search size={17} />
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search questions, answers, topics, stays..." />
        </label>
        <div className="ops-chip-row">
          <span><Sparkles size={15} /> {snapshot.topics.length} topics detected</span>
          <a href="/admin/bookings/agentfaq/add/">Add FAQ</a>
          <a href="/admin/bookings/agentknowledgesource/">Knowledge sources</a>
        </div>
      </section>

      <section className="ops-split-grid">
        <details className="ops-chart-card ops-expand-card ops-equal-collapse">
          <summary className="ops-card-heading">
            <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
            <div>
              <span>Question analytics</span>
              <h3>Top topics</h3>
            </div>
            <a href={snapshot.conversationAdminUrl} onClick={(event) => event.stopPropagation()}>
              Open logs
            </a>
          </summary>
          <div className="ops-chart-bars">
            {snapshot.topics.length === 0 && <p>No agent topics captured yet.</p>}
            {snapshot.topics.map((topic) => (
              <div className="ops-chart-row" key={topic.value}>
                <span>{topic.label}</span>
                <div><i style={{ width: `${topic.width}%` }} /></div>
                <strong>{topic.total}</strong>
              </div>
            ))}
          </div>
        </details>

        <details className="ops-training-card ops-expand-card ops-equal-collapse">
          <summary className="ops-card-heading">
            <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
            <div>
              <span><MessageSquareText size={16} /> Training loop</span>
              <h3>Agent curriculum</h3>
            </div>
            <a href="/admin/bookings/agentfaq/add/" onClick={(event) => event.stopPropagation()}>Create answer</a>
          </summary>
          <div className="ops-training-card__details">
            <p>When the same question repeats, promote the best answer into an Agent FAQ. Keep rules, deposit holds, location guidance, cancellation policy, and payment language precise.</p>
          </div>
        </details>
      </section>

      <section className="ops-table-card">
        <div className="ops-card-heading">
          <div>
            <span>Recent questions</span>
            <h3>{conversations.length} conversations shown</h3>
          </div>
          <div className="ops-card-heading__actions">
            <button type="button" onClick={() => setIsQuestionsOpen(true)}><Search size={15} /> Open list</button>
            <strong>{snapshot.conversations.length}</strong>
          </div>
        </div>
        <div className="ops-list-scroll">
          {conversations.map(renderConversationRow)}
        </div>
      </section>

      <details className="ops-table-card ops-expand-card">
        <summary className="ops-card-heading">
          <span className="ops-expand-chevron"><ChevronRight size={17} /></span>
          <div>
            <span>Agent FAQ library</span>
            <h3>{faqs.length} answer cards</h3>
          </div>
          <a href={snapshot.faqAdminUrl}>Manage FAQs</a>
        </summary>
        <section className="ops-card-grid ops-faq-library">
          {faqs.map(renderFaqRow)}
        </section>
      </details>

      <OpsListModal
        isOpen={isQuestionsOpen}
        title={`${conversations.length} recent questions`}
        subtitle="Scroll the latest agent questions, routing mode, visitor context, and captured answer."
        onClose={() => setIsQuestionsOpen(false)}
      >
        {conversations.map(renderConversationRow)}
      </OpsListModal>
    </main>
  );
}
