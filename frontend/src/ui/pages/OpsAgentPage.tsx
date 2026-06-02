import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, Bot, BrainCircuit, ExternalLink, MessageSquareText, Search, Sparkles } from 'lucide-react';
import { OpsWorkspaceFactory } from '../../application/OpsWorkspaceFactory';
import { OpsAgentSnapshot } from '../../domain/models';

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
          <h2>Train the booking agent from real customer questions.</h2>
          <p>See what guests ask, what the FAQ layer handled, where OpenAI helped, and which answers should be added or improved.</p>
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
        <article className="ops-chart-card">
          <div className="ops-card-heading">
            <div>
              <span>Question analytics</span>
              <h3>Top topics</h3>
            </div>
            <strong>{snapshot.topics.length}</strong>
          </div>
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
        </article>

        <article className="ops-training-card">
          <span><MessageSquareText size={16} /> Training loop</span>
          <h3>Use the conversation list as your agent curriculum.</h3>
          <p>When the same question repeats, promote the best answer into an Agent FAQ. Keep rules, deposit holds, location guidance, cancellation policy, and payment language precise.</p>
          <a href="/admin/bookings/agentfaq/add/">Create a new answer</a>
        </article>
      </section>

      <section className="ops-table-card">
        <div className="ops-card-heading">
          <div>
            <span>Recent questions</span>
            <h3>{conversations.length} conversations shown</h3>
          </div>
          <strong>{snapshot.conversations.length}</strong>
        </div>
        {conversations.map((row) => (
          <article className="ops-data-row ops-data-row--agent" key={row.id}>
            <div>
              <span className={`ops-status-pill ops-status-pill--${row.mode}`}>{modeLabel(row.mode)}</span>
              <h3>{row.topic || 'General'}</h3>
              <p>{row.visitor} · {row.item}</p>
            </div>
            <div>
              <strong>{row.lastQuestion}</strong>
              <p>{row.lastReply}</p>
            </div>
            <div className="ops-row-actions">
              <a href={row.adminUrl}>Conversation</a>
            </div>
          </article>
        ))}
      </section>

      <section className="ops-card-grid">
        {faqs.map((faq) => (
          <article className="ops-faq-card" key={faq.id}>
            <div>
              <span className={`ops-status-pill ${faq.isActive ? 'ops-status-pill--active' : 'ops-status-pill--inactive'}`}>{faq.isActive ? 'Active' : 'Inactive'}</span>
              <small>{faq.category} · {faq.item} · {faq.language}</small>
            </div>
            <h3>{faq.question}</h3>
            <p>{faq.answer}</p>
            {faq.keywords && <strong>{faq.keywords}</strong>}
            <a href={faq.adminUrl}>Edit FAQ</a>
          </article>
        ))}
      </section>
    </main>
  );
}
