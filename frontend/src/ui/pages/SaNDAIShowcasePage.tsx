import { useEffect, type ReactNode } from 'react';
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  CalendarCheck2,
  CheckCircle2,
  ExternalLink,
  GraduationCap,
  Network,
  RefreshCw,
  Sparkles,
  Target,
  TrendingUp,
  Users,
} from 'lucide-react';
import './sandai-showcase.css';

const attendance = [22, 24, 18, 23, 21, 26, 24, 25];
const cumulative = [22, 46, 64, 87, 108, 134, 158, 183];
const cumulativeTarget = [20, 40, 60, 80, 100, 120, 140, 160];

const channels = [
  { label: 'Faculty referrals', value: 40, group: 'Anchor network' },
  { label: 'Career services', value: 36, group: 'Institutional multiplier' },
  { label: 'Student organizations', value: 34, group: 'Institutional multiplier' },
  { label: 'Academic departments', value: 29, group: 'Institutional multiplier' },
  { label: 'Peer referrals', value: 19, group: 'Partner and referral network' },
  { label: 'Community partners', value: 16, group: 'Partner and referral network' },
  { label: 'Approved digital', value: 9, group: 'Broader reach' },
];

const funnel = [
  { label: 'Attended', value: 183 },
  { label: 'Opted in', value: 100 },
  { label: 'Qualified', value: 59 },
  { label: 'Approved conversion', value: 22 },
];

const cadence = [
  ['T-7', 'Open registration', 'Activate at least three partner channels'],
  ['T-5', 'Check pace', 'Review registrations and channel contribution'],
  ['T-3', 'Forecast', 'Trigger recovery when expected attendance is at risk'],
  ['T-1', 'Confirm', 'Run confirmation sprint and backfill'],
  ['T', 'Deliver', 'Record actual attendance'],
  ['T+1', 'Learn', 'Review results and choose the next small improvement'],
];

const studentJourney = [
  ['Reflect', 'Choose a useful starting point'],
  ['Practice', 'Use AI on a structured problem'],
  ['Check', 'Question assumptions and evidence'],
  ['Build', 'Turn learning into a reviewable artifact'],
  ['Plan', 'Leave with one realistic next action'],
];

const artifactLinks = {
  strategy: 'https://github.com/pzg8794/sandai-seminar-operations-demo/blob/main/strategy/Piter_Garcia_SaNDAI_8_Week_Seminar_Growth_Plan.pdf',
  management: 'https://colab.research.google.com/drive/18GBDjNQp4IHl_wzDl0d3t9hX_B73Bssj',
  student: 'https://colab.research.google.com/drive/1W3lfj1sGvSrruN24_0WnqEkZsN8rLL8I',
  repo: 'https://github.com/pzg8794/sandai-seminar-operations-demo',
};

function AttendanceChart() {
  const width = 760;
  const height = 300;
  const left = 46;
  const right = 20;
  const top = 26;
  const bottom = 42;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const yMax = 30;
  const x = (index: number) => left + (index + 0.5) * (plotWidth / attendance.length);
  const y = (value: number) => top + plotHeight - (value / yMax) * plotHeight;
  const barWidth = Math.min(48, plotWidth / attendance.length - 18);

  return (
    <svg className="sandai-chart-svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Weekly attendance against the 20 attendee target">
      {[0, 10, 20, 30].map((tick) => (
        <g key={tick}>
          <line x1={left} x2={width - right} y1={y(tick)} y2={y(tick)} className={tick === 20 ? 'sandai-grid-target' : 'sandai-grid'} />
          <text x={left - 10} y={y(tick) + 4} textAnchor="end" className="sandai-axis-label">{tick}</text>
        </g>
      ))}
      <text x={width - right} y={y(20) - 8} textAnchor="end" className="sandai-target-label">weekly floor = 20</text>
      {attendance.map((value, index) => {
        const state = index === 2 ? 'miss' : index === 3 ? 'recovery' : 'met';
        return (
          <g key={index}>
            <rect
              x={x(index) - barWidth / 2}
              y={y(value)}
              width={barWidth}
              height={y(0) - y(value)}
              rx="8"
              className={`sandai-attendance-bar sandai-attendance-bar--${state}`}
            >
              <title>{`Week ${index + 1}: ${value} attendees`}</title>
            </rect>
            <text x={x(index)} y={y(value) - 9} textAnchor="middle" className="sandai-chart-value">{value}</text>
            <text x={x(index)} y={height - 15} textAnchor="middle" className="sandai-axis-label">W{index + 1}</text>
          </g>
        );
      })}
    </svg>
  );
}

function CumulativeChart() {
  const width = 760;
  const height = 300;
  const left = 46;
  const right = 20;
  const top = 26;
  const bottom = 42;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const yMax = 200;
  const x = (index: number) => left + index * (plotWidth / 7);
  const y = (value: number) => top + plotHeight - (value / yMax) * plotHeight;
  const path = (values: number[]) => values.map((value, index) => `${index ? 'L' : 'M'}${x(index).toFixed(1)},${y(value).toFixed(1)}`).join(' ');

  return (
    <svg className="sandai-chart-svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Cumulative attendance against cumulative target">
      {[0, 40, 80, 120, 160, 200].map((tick) => (
        <g key={tick}>
          <line x1={left} x2={width - right} y1={y(tick)} y2={y(tick)} className="sandai-grid" />
          <text x={left - 10} y={y(tick) + 4} textAnchor="end" className="sandai-axis-label">{tick}</text>
        </g>
      ))}
      <path d={path(cumulativeTarget)} className="sandai-line-target" />
      <path d={path(cumulative)} className="sandai-line-actual" />
      {cumulative.map((value, index) => (
        <g key={index}>
          <circle cx={x(index)} cy={y(value)} r="5" className="sandai-line-point">
            <title>{`Week ${index + 1}: ${value} cumulative attendances`}</title>
          </circle>
          <text x={x(index)} y={height - 15} textAnchor="middle" className="sandai-axis-label">W{index + 1}</text>
        </g>
      ))}
      <g transform="translate(505 24)">
        <line x1="0" x2="26" y1="0" y2="0" className="sandai-line-actual" />
        <text x="34" y="4" className="sandai-legend-text">demo attendance</text>
        <line x1="122" x2="148" y1="0" y2="0" className="sandai-line-target" />
        <text x="156" y="4" className="sandai-legend-text">target</text>
      </g>
    </svg>
  );
}

function ChannelBars() {
  const maximum = Math.max(...channels.map((channel) => channel.value));
  return (
    <div className="sandai-channel-list" aria-label="Attendance contribution by channel">
      {channels.map((channel) => (
        <div className="sandai-channel-row" key={channel.label}>
          <div className="sandai-channel-copy">
            <strong>{channel.label}</strong>
            <span>{channel.group}</span>
          </div>
          <div className="sandai-channel-track" aria-hidden="true">
            <div className="sandai-channel-fill" style={{ width: `${(channel.value / maximum) * 100}%` }} />
          </div>
          <strong className="sandai-channel-value">{channel.value}</strong>
        </div>
      ))}
    </div>
  );
}

function Funnel() {
  const maximum = funnel[0].value;
  return (
    <div className="sandai-funnel" aria-label="Free seminar downstream opportunity funnel">
      {funnel.map((stage, index) => (
        <div
          className="sandai-funnel-stage"
          key={stage.label}
          style={{ width: `${Math.max(34, (stage.value / maximum) * 100)}%` }}
        >
          <span>{stage.label}</span>
          <strong>{stage.value}</strong>
          {index < funnel.length - 1 && <ArrowRight size={16} aria-hidden="true" />}
        </div>
      ))}
    </div>
  );
}

function ExternalButton({ href, children, primary = false }: { href: string; children: ReactNode; primary?: boolean }) {
  return (
    <a className={primary ? 'sandai-button sandai-button--primary' : 'sandai-button'} href={href} target="_blank" rel="noreferrer">
      {children}
      <ExternalLink size={15} aria-hidden="true" />
    </a>
  );
}

export function SaNDAIShowcasePage() {
  useEffect(() => {
    document.title = 'SaNDAI Seminar Growth System | Piter Garcia';
  }, []);

  return (
    <main className="sandai-page">
      <nav className="sandai-nav" aria-label="SaNDAI showcase navigation">
        <a className="sandai-brand" href="#top">
          <span className="sandai-brand-mark">S</span>
          <span>SaNDAI Seminar Growth System</span>
        </a>
        <div className="sandai-nav-links">
          <a href="#performance">Performance</a>
          <a href="#recovery">Recovery</a>
          <a href="#experience">Student experience</a>
          <a href="#ownership">Ownership</a>
        </div>
        <ExternalButton href={artifactLinks.strategy}>Strategy PDF</ExternalButton>
      </nav>

      <section className="sandai-hero" id="top">
        <div className="sandai-hero-copy">
          <div className="sandai-eyebrow"><Sparkles size={15} /> Case challenge prototype · Piter Garcia</div>
          <h1>Turn an eight-week attendance goal into a system that can be run, measured, and improved.</h1>
          <p className="sandai-hero-lead">
            A decision-first operating model for reaching <strong>20+ student seminar attendees every week</strong>,
            expanding beyond the immediate network, recovering early when the forecast is weak, and connecting the free
            seminar to measurable student and business value.
          </p>
          <div className="sandai-hero-actions">
            <a className="sandai-button sandai-button--primary" href="#performance">
              Explore the operating system <ArrowRight size={16} />
            </a>
            <ExternalButton href={artifactLinks.management}>Open management notebook</ExternalButton>
          </div>
          <p className="sandai-demo-note">Illustrative eight-week data from the validated prototype — not live campaign results.</p>
        </div>
        <div className="sandai-hero-panel" aria-label="Eight-week objective summary">
          <div className="sandai-hero-panel-head">
            <span>8-week objective</span>
            <span className="sandai-status-pill"><CheckCircle2 size={14} /> executable prototype</span>
          </div>
          <div className="sandai-kpi-grid">
            <article>
              <Target size={20} />
              <strong>20+</strong>
              <span>weekly attendance floor</span>
            </article>
            <article>
              <Users size={20} />
              <strong>160+</strong>
              <span>eight-week target</span>
            </article>
            <article>
              <TrendingUp size={20} />
              <strong>183</strong>
              <span>demo attendances</span>
            </article>
            <article>
              <RefreshCw size={20} />
              <strong>26% → 98%</strong>
              <span>Week 4 recovery probability</span>
            </article>
          </div>
          <div className="sandai-hero-decision">
            <span>Decision rule</span>
            <strong>Forecast early. Intervene before seminar day. Measure the result.</strong>
          </div>
        </div>
      </section>

      <section className="sandai-section sandai-section--decision">
        <div className="sandai-section-heading">
          <span className="sandai-section-kicker">The one-minute decision</span>
          <h2>STATUS → WHY → ACTION → NEXT CHECK</h2>
          <p>The operating system surfaces the decision before the detail.</p>
        </div>
        <div className="sandai-decision-grid">
          <article className="sandai-decision-card sandai-decision-card--status">
            <span>STATUS</span>
            <strong>Recovery triggered</strong>
            <p>Week 4 was below the safe T−3 forecast threshold.</p>
          </article>
          <article className="sandai-decision-card">
            <span>WHY</span>
            <strong>18.1 expected</strong>
            <p>Only a 26% modeled chance of reaching 20 before intervention.</p>
          </article>
          <article className="sandai-decision-card">
            <span>ACTION</span>
            <strong>Activate partner + confirmation recovery</strong>
            <p>Add targeted registrations and secure confirmations while there is still time.</p>
          </article>
          <article className="sandai-decision-card">
            <span>NEXT CHECK</span>
            <strong>T−1</strong>
            <p>Review confirmations, rerun the forecast, and backfill if needed.</p>
          </article>
        </div>
      </section>

      <section className="sandai-section" id="performance">
        <div className="sandai-section-heading sandai-section-heading--split">
          <div>
            <span className="sandai-section-kicker">Performance</span>
            <h2>Protect the weekly floor without losing the eight-week view.</h2>
          </div>
          <div className="sandai-heading-stat">
            <span>Demo total</span>
            <strong>183 / 160</strong>
            <small>114% of cumulative target</small>
          </div>
        </div>
        <div className="sandai-chart-grid">
          <article className="sandai-card sandai-chart-card">
            <header>
              <div>
                <span>Weekly attendance</span>
                <h3>Week 3 misses. Week 4 recovers.</h3>
              </div>
              <BarChart3 size={22} />
            </header>
            <AttendanceChart />
            <div className="sandai-insight-strip">
              <span className="sandai-dot sandai-dot--miss" /> Week 3: 18
              <ArrowRight size={14} />
              <span className="sandai-dot sandai-dot--recovery" /> Week 4: 23
              <span className="sandai-insight-copy">A cumulative total never hides a missed weekly requirement.</span>
            </div>
          </article>
          <article className="sandai-card sandai-chart-card">
            <header>
              <div>
                <span>Cumulative progress</span>
                <h3>Stay ahead of the 160-attendance trajectory.</h3>
              </div>
              <TrendingUp size={22} />
            </header>
            <CumulativeChart />
            <p className="sandai-card-note">The demo finishes at 183 attendances while still preserving the weekly pass/fail view.</p>
          </article>
        </div>
      </section>

      <section className="sandai-section sandai-section--tint" id="recovery">
        <div className="sandai-section-heading">
          <span className="sandai-section-kicker">Early warning + recovery</span>
          <h2>Do not wait for a missed seminar to learn that the plan was weak.</h2>
          <p>The same forecast is rerun after the planned intervention so the operator can see whether the recovery is sufficient.</p>
        </div>
        <div className="sandai-recovery-grid">
          <article className="sandai-recovery-card sandai-recovery-card--before">
            <span>T−3 · before intervention</span>
            <strong>18.1</strong>
            <p>expected attendance</p>
            <div className="sandai-probability">
              <span>Chance of reaching 20</span>
              <strong>26%</strong>
            </div>
            <div className="sandai-risk-label">RED · recovery required</div>
          </article>
          <div className="sandai-recovery-arrow">
            <RefreshCw size={28} />
            <strong>Secondary partner + targeted confirmation sprint</strong>
            <span>+7 registrations · +9 confirmations</span>
          </div>
          <article className="sandai-recovery-card sandai-recovery-card--after">
            <span>after planned recovery</span>
            <strong>25.3</strong>
            <p>expected attendance</p>
            <div className="sandai-probability">
              <span>Chance of reaching 20</span>
              <strong>98%</strong>
            </div>
            <div className="sandai-risk-label sandai-risk-label--good">GREEN · recovery sufficient</div>
          </article>
          <article className="sandai-recovery-observed">
            <CalendarCheck2 size={24} />
            <div>
              <span>Observed Week 4 result in the demo scenario</span>
              <strong>23 attendees</strong>
            </div>
          </article>
        </div>
      </section>

      <section className="sandai-section">
        <div className="sandai-section-heading sandai-section-heading--split">
          <div>
            <span className="sandai-section-kicker">Growth channels</span>
            <h2>Expand through institutional multipliers, not one personal network.</h2>
            <p>Volume is attributed to the channel that actually produces attendance.</p>
          </div>
          <Network className="sandai-heading-icon" size={44} />
        </div>
        <div className="sandai-two-column">
          <article className="sandai-card">
            <header className="sandai-card-header">
              <div>
                <span>Attributed attendance</span>
                <h3>Which channels bring students into the room?</h3>
              </div>
            </header>
            <ChannelBars />
          </article>
          <article className="sandai-card sandai-growth-model">
            <span className="sandai-mini-label">Network expansion model</span>
            <div className="sandai-layer sandai-layer--1">
              <strong>Layer 1</strong>
              <span>Anchor network</span>
              <p>Existing faculty and trusted relationships open the first doors.</p>
            </div>
            <div className="sandai-layer sandai-layer--2">
              <strong>Layer 2</strong>
              <span>Institutional multipliers</span>
              <p>Student organizations, academic departments, and career services multiply reach.</p>
            </div>
            <div className="sandai-layer sandai-layer--3">
              <strong>Layer 3</strong>
              <span>Partner + referral network</span>
              <p>Peer ambassadors and community partners reduce dependence on one institution.</p>
            </div>
            <div className="sandai-layer sandai-layer--4">
              <strong>Layer 4</strong>
              <span>Broader approved reach</span>
              <p>Digital promotion supports the system rather than replacing trusted channels.</p>
            </div>
          </article>
        </div>
      </section>

      <section className="sandai-section sandai-section--student" id="experience">
        <div className="sandai-student-intro">
          <div>
            <span className="sandai-section-kicker">Student value</span>
            <h2>The seminar should leave students with something they can explain, improve, and use.</h2>
            <p>
              The companion is designed as a guided AI career lab with clear goals, worked examples, visible progress,
              flexible response modes, and concrete finish signals.
            </p>
          </div>
          <GraduationCap size={54} />
        </div>
        <div className="sandai-journey">
          {studentJourney.map(([title, body], index) => (
            <article key={title}>
              <span>{index + 1}</span>
              <strong>{title}</strong>
              <p>{body}</p>
              {index < studentJourney.length - 1 && <ArrowRight size={18} aria-hidden="true" />}
            </article>
          ))}
        </div>
        <div className="sandai-student-bottom">
          <div className="sandai-student-output">
            <BrainCircuit size={25} />
            <div>
              <span>Visible learning routine</span>
              <strong>ASK → CHECK → CHOOSE → CHANGE → EXPLAIN</strong>
            </div>
          </div>
          <div className="sandai-student-output">
            <CheckCircle2 size={25} />
            <div>
              <span>Student leaves with</span>
              <strong>one artifact · one evidence statement · one realistic next step</strong>
            </div>
          </div>
          <ExternalButton href={artifactLinks.student} primary>Open Student AI Career Lab</ExternalButton>
        </div>
      </section>

      <section className="sandai-section">
        <div className="sandai-section-heading">
          <span className="sandai-section-kicker">Business value</span>
          <h2>Keep the seminar free. Measure what happens next.</h2>
          <p>No invented prices or revenue claims — only an attributed path from useful free value to approved follow-on opportunity.</p>
        </div>
        <div className="sandai-card sandai-funnel-card">
          <Funnel />
          <div className="sandai-funnel-note">
            <span>183 attended</span>
            <ArrowRight size={14} />
            <span>100 opted in</span>
            <ArrowRight size={14} />
            <span>59 qualified</span>
            <ArrowRight size={14} />
            <span>22 approved conversions</span>
          </div>
        </div>
      </section>

      <section className="sandai-section sandai-section--ai">
        <div className="sandai-section-heading sandai-section-heading--split">
          <div>
            <span className="sandai-section-kicker">Practical AI support</span>
            <h2>Use AI where judgment benefits — use ordinary automation where it does not.</h2>
          </div>
          <BrainCircuit className="sandai-heading-icon" size={44} />
        </div>
        <div className="sandai-ai-grid">
          <article>
            <Sparkles size={20} />
            <strong>Partner research</strong>
            <p>Identify potential institutional multipliers and organize outreach hypotheses.</p>
          </article>
          <article>
            <Users size={20} />
            <strong>Message adaptation</strong>
            <p>Draft audience-specific outreach while keeping the operator responsible for what is sent.</p>
          </article>
          <article>
            <TrendingUp size={20} />
            <strong>Pattern analysis</strong>
            <p>Summarize channel, attendance, and student-feedback signals into decisions.</p>
          </article>
          <article>
            <RefreshCw size={20} />
            <strong>Learning loop</strong>
            <p>Turn observed results into the next small test instead of repeating a weak tactic.</p>
          </article>
        </div>
      </section>

      <section className="sandai-section sandai-section--ownership" id="ownership">
        <div className="sandai-section-heading">
          <span className="sandai-section-kicker">Ownership</span>
          <h2>The system says what happens next without waiting for a reminder.</h2>
          <p>Every gate has a purpose, an action, and one accountable operator.</p>
        </div>
        <div className="sandai-cadence">
          {cadence.map(([gate, title, body]) => (
            <article key={gate}>
              <span>{gate}</span>
              <strong>{title}</strong>
              <p>{body}</p>
              <small>Owner · Piter</small>
            </article>
          ))}
        </div>
        <div className="sandai-trust-statement">
          <CheckCircle2 size={24} />
          <div>
            <strong>Why trust the operator?</strong>
            <p>Because the objective, thresholds, cadence, evidence, next action, and review loop are explicit before the eight weeks begin.</p>
          </div>
        </div>
      </section>

      <section className="sandai-section sandai-section--artifacts">
        <div className="sandai-section-heading">
          <span className="sandai-section-kicker">Inspect the work</span>
          <h2>Strategy, executable management logic, and the student experience all tell the same story.</h2>
        </div>
        <div className="sandai-artifact-grid">
          <a href={artifactLinks.strategy} target="_blank" rel="noreferrer">
            <span>01</span>
            <strong>8-Week Growth Strategy</strong>
            <p>The concise strategy, measurement, recovery, monetization, AI, and ownership plan.</p>
            <em>Open PDF <ExternalLink size={14} /></em>
          </a>
          <a href={artifactLinks.management} target="_blank" rel="noreferrer">
            <span>02</span>
            <strong>Management Command Center</strong>
            <p>The executable forecast, recovery, channel, funnel, and decision-support notebook.</p>
            <em>Open Colab <ExternalLink size={14} /></em>
          </a>
          <a href={artifactLinks.student} target="_blank" rel="noreferrer">
            <span>03</span>
            <strong>Student AI Career Lab</strong>
            <p>The UDL-aligned workshop experience students can actually use during a seminar.</p>
            <em>Open Colab <ExternalLink size={14} /></em>
          </a>
          <a href={artifactLinks.repo} target="_blank" rel="noreferrer">
            <span>04</span>
            <strong>Reproducible Prototype</strong>
            <p>Versioned code, tests, synthetic inputs, documentation, and parity verification.</p>
            <em>Open repository <ExternalLink size={14} /></em>
          </a>
        </div>
      </section>

      <footer className="sandai-footer">
        <div>
          <strong>SaNDAI Seminar Growth System</strong>
          <span>Case challenge prototype prepared by Piter Garcia</span>
        </div>
        <span>Illustrative data · validated local/Colab parity · no live campaign results claimed</span>
      </footer>
    </main>
  );
}
