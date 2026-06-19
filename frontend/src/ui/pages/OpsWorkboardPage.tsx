import { useMemo, useState } from 'react';
import type { LucideIcon } from 'lucide-react';
import {
  AlertCircle,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  FileText,
  Filter,
  Grip,
  ListTodo,
  MoreHorizontal,
  Plus,
  UserRound,
  X,
} from 'lucide-react';

type TaskTone = 'danger' | 'warning' | 'primary' | 'success' | 'violet';
type TaskStatus = 'progress' | 'waiting' | 'done';
type TaskDueTone = 'today' | 'soon' | 'done';

class TaskMetricModel {
  constructor(
    readonly label: string,
    readonly value: string,
    readonly caption: string,
    readonly tone: TaskTone,
    readonly icon: LucideIcon,
  ) {}
}

class TaskCardModel {
  constructor(
    readonly id: string,
    readonly title: string,
    readonly meta: string[],
    readonly due: string,
    readonly dueTone: TaskDueTone,
    readonly avatar: string,
    readonly avatarTone: string,
    readonly status: TaskStatus,
  ) {}
}

class TaskColumnModel {
  constructor(
    readonly title: string,
    readonly count: string,
    readonly tone: TaskStatus,
    readonly tasks: TaskCardModel[],
  ) {}
}

class TaskDetailModel {
  constructor(
    readonly description: string,
    readonly assignee: string,
    readonly priority: string,
    readonly due: string,
    readonly links: Array<{ label: string; value: string }>,
    readonly details: Array<{ label: string; value: string }>,
    readonly note: string,
    readonly activity: string,
  ) {}
}

const TASK_METRICS = [
  new TaskMetricModel('Overdue', '8', '+3 vs yesterday', 'danger', AlertCircle),
  new TaskMetricModel('Due Today', '12', '+2 vs yesterday', 'warning', CalendarDays),
  new TaskMetricModel('Due This Week', '24', '+6 vs yesterday', 'primary', ClipboardList),
  new TaskMetricModel('Completed (7d)', '36', '+12 vs last 7 days', 'success', CheckCircle2),
  new TaskMetricModel('Total', '68', 'Active tasks', 'violet', ListTodo),
];

const TASK_COLUMNS = [
  new TaskColumnModel('In Progress', '6', 'progress', [
    new TaskCardModel(
      'self-checkin',
      'Send self check-in instructions',
      ['Reservation: R-1042', '3 Beds Apt, Vacation Home & Pool, G-101'],
      'Today',
      'today',
      'MR',
      'green',
      'progress',
    ),
    new TaskCardModel(
      'cleaning',
      'Confirm cleaning completion',
      ['Reservation: R-1035', '2 Beds Apt, Vacation Home & Pool'],
      'Today',
      'today',
      'AS',
      'lime',
      'progress',
    ),
    new TaskCardModel(
      'deposit-review',
      'Review expiring deposit hold',
      ['Deposit: D-1009', 'Guest: Maria Rodriguez'],
      'Today',
      'today',
      'PG',
      'blue',
      'progress',
    ),
    new TaskCardModel(
      'maintenance-bill',
      'Generate maintenance bill',
      ['Work Order: WO-2026-0104', 'AC not cooling - G-101'],
      'Today',
      'today',
      'CM',
      'purple',
      'progress',
    ),
    new TaskCardModel(
      'work-order',
      'Approve pending work order',
      ['Work Order: WO-2026-0107', 'Replace ceiling light - Meeting Room 1'],
      'Tomorrow',
      'soon',
      'PG',
      'blue',
      'progress',
    ),
    new TaskCardModel(
      'listing-photos',
      'Update listing photos',
      ['Listing: L-1003', '3 Beds Apt, Vacation Home & Pool, G-101'],
      'Tomorrow',
      'soon',
      'DM',
      'slate',
      'progress',
    ),
  ]),
  new TaskColumnModel('Waiting', '5', 'waiting', [
    new TaskCardModel(
      'late-checkin',
      'Guest reply: late check-in request',
      ['Reservation: R-1046', '2 Beds Apt, Vacation Home & Pool'],
      'Due Jun 13',
      'soon',
      'JS',
      'photo',
      'waiting',
    ),
    new TaskCardModel(
      'payout',
      'Payout confirmation',
      ['Payment: P-1021', 'Guest: John Smith'],
      'Due Jun 13',
      'soon',
      'PG',
      'blue',
      'waiting',
    ),
    new TaskCardModel(
      'vendor-quote',
      'Vendor quote approval',
      ['Work Order: WO-2026-0108', 'TV not turning on - G-101'],
      'Due Jun 14',
      'soon',
      'TS',
      'green',
      'waiting',
    ),
    new TaskCardModel(
      'proof-payment',
      'Awaiting proof of payment',
      ['Deposit: D-1011', 'Guest: Ana Lopez'],
      'Due Jun 14',
      'soon',
      'PG',
      'blue',
      'waiting',
    ),
    new TaskCardModel(
      'content-review',
      'Content review',
      ['Listing: L-1005', 'Meeting Room 1'],
      'Due Jun 15',
      'soon',
      'DM',
      'slate',
      'waiting',
    ),
  ]),
  new TaskColumnModel('Done', '17', 'done', [
    new TaskCardModel(
      'booking-confirmation',
      'Send booking confirmation',
      ['Reservation: R-1040'],
      'Completed Jun 10, 9:15 AM',
      'done',
      'PG',
      'green',
      'done',
    ),
    new TaskCardModel(
      'collect-deposit',
      'Collect security deposit',
      ['Deposit: D-1007'],
      'Completed Jun 10, 10:02 AM',
      'done',
      'PG',
      'green',
      'done',
    ),
    new TaskCardModel(
      'inspect-ac',
      'Inspect AC repair',
      ['Work Order: WO-2026-0102'],
      'Completed Jun 9, 4:45 PM',
      'done',
      'CM',
      'slate',
      'done',
    ),
    new TaskCardModel(
      'block-dates',
      'Block dates for maintenance',
      ['Property: Conference Room A'],
      'Completed Jun 9, 11:12 AM',
      'done',
      'TS',
      'green',
      'done',
    ),
    new TaskCardModel(
      'welcome-message',
      'Welcome message sent',
      ['Reservation: R-1038'],
      'Completed Jun 9, 9:08 AM',
      'done',
      'AS',
      'green',
      'done',
    ),
  ]),
];

const DETAIL_MODEL = new TaskDetailModel(
  'Send self check-in instructions and house guide to the guest 24 hours before arrival.',
  'Maria Rodriguez',
  'High',
  'Today, Jun 12',
  [
    { label: 'Reservation', value: 'R-1042' },
    { label: 'Listing', value: '3 Beds Apt, G-101' },
    { label: 'Guest', value: 'John Smith' },
  ],
  [
    { label: 'Check-in', value: 'Jun 13, 2026 (3:00 PM)' },
    { label: 'Channel', value: 'Direct Website' },
    { label: 'Nights', value: '3' },
  ],
  'Guest requested early check-in if possible. Include parking and Wi-Fi info.',
  'Piter Garcia created this task',
);

function TaskMetricCard({ metric }: { metric: TaskMetricModel }) {
  const Icon = metric.icon;

  return (
    <article className={`tasks-v4-metric tasks-v4-metric--${metric.tone}`}>
      <span className="tasks-v4-metric__icon"><Icon size={19} /></span>
      <div>
        <p>{metric.label}</p>
        <strong>{metric.value}</strong>
        <small>{metric.caption}</small>
      </div>
    </article>
  );
}

function TaskCard({
  task,
  selected,
  onSelect,
}: {
  task: TaskCardModel;
  selected: boolean;
  onSelect: (task: TaskCardModel) => void;
}) {
  return (
    <button
      type="button"
      className={`tasks-v4-card tasks-v4-card--${task.status}${selected ? ' is-selected' : ''}`}
      onClick={() => onSelect(task)}
    >
      <strong>{task.title}</strong>
      {task.meta.map((line) => (
        <span key={line}>{line}</span>
      ))}
      <footer>
        <span className={`tasks-v4-due tasks-v4-due--${task.dueTone}`}><CalendarDays size={13} /> {task.due}</span>
        <span className={`tasks-v4-avatar tasks-v4-avatar--${task.avatarTone}`}>{task.avatar}</span>
      </footer>
    </button>
  );
}

function TaskColumn({
  column,
  selectedTaskId,
  onSelect,
}: {
  column: TaskColumnModel;
  selectedTaskId: string;
  onSelect: (task: TaskCardModel) => void;
}) {
  return (
    <section className={`tasks-v4-column tasks-v4-column--${column.tone}`}>
      <header>
        <h2><span /> {column.title} <em>{column.count}</em></h2>
      </header>
      <div className="tasks-v4-column__cards">
        {column.tasks.map((task) => (
          <TaskCard key={task.id} task={task} selected={task.id === selectedTaskId} onSelect={onSelect} />
        ))}
      </div>
      <button type="button" className="tasks-v4-add"><Plus size={14} /> Add task</button>
    </section>
  );
}

function TaskDetailPanel({ task, detail }: { task: TaskCardModel; detail: TaskDetailModel }) {
  return (
    <aside className="tasks-v4-detail">
      <header>
        <div>
          <FileText size={18} />
          <h2>{task.title}</h2>
        </div>
        <span className={`tasks-v4-status tasks-v4-status--${task.status}`}>
          {task.status === 'progress' ? 'In Progress' : task.status === 'waiting' ? 'Waiting' : 'Done'}
        </span>
        <button type="button" aria-label="More task actions"><MoreHorizontal size={18} /></button>
        <button type="button" aria-label="Close task details"><X size={18} /></button>
      </header>

      <p className="tasks-v4-detail__summary">{detail.description}</p>

      <section className="tasks-v4-detail__selectors" aria-label="Task assignment">
        <article>
          <label>Assignee</label>
          <button type="button"><span className="tasks-v4-avatar tasks-v4-avatar--green">MR</span> {detail.assignee} <ChevronDown size={14} /></button>
        </article>
        <article>
          <label>Priority</label>
          <button type="button" className="is-high"><AlertCircle size={13} /> {detail.priority}</button>
        </article>
        <article>
          <label>Due</label>
          <button type="button" className="is-due"><CalendarDays size={13} /> {detail.due}</button>
        </article>
      </section>

      <section className="tasks-v4-detail__section">
        <h3>Links</h3>
        <div className="tasks-v4-links">
          {detail.links.map((link) => (
            <a href="#" key={`${link.label}-${link.value}`}>{link.label}: {link.value}</a>
          ))}
        </div>
      </section>

      <section className="tasks-v4-detail__section">
        <h3>Details</h3>
        <dl className="tasks-v4-detail-list">
          {detail.details.map((item) => (
            <div key={item.label}>
              <dt>{item.label}</dt>
              <dd>{item.value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="tasks-v4-detail__section">
        <h3>Notes</h3>
        <p className="tasks-v4-note">{detail.note}</p>
        <small>Added by you · Jun 11, 2026, 2:18 PM</small>
      </section>

      <section className="tasks-v4-detail__section tasks-v4-activity">
        <h3>Activity</h3>
        <p><span className="tasks-v4-avatar tasks-v4-avatar--blue">PG</span> {detail.activity}</p>
        <small>Jun 11, 2026, 2:18 PM</small>
      </section>

      <div className="tasks-v4-detail__actions">
        <button type="button" className="is-complete"><Check size={16} /> Mark Complete</button>
        <button type="button"><UserRound size={16} /> Reassign <ChevronDown size={16} /></button>
        <button type="button" className="is-waiting"><AlertCircle size={16} /> Move to Waiting</button>
      </div>
    </aside>
  );
}

export function OpsWorkboardPage() {
  const [selectedTaskId, setSelectedTaskId] = useState(TASK_COLUMNS[0].tasks[0].id);
  const allTasks = useMemo(() => TASK_COLUMNS.flatMap((column) => column.tasks), []);
  const selectedTask = allTasks.find((task) => task.id === selectedTaskId) ?? allTasks[0];

  return (
    <main className="dashboard-content tasks-v4-page">
      <section className="tasks-v4-header">
        <div>
          <h1>Tasks &amp; Workboard</h1>
          <p>Track operational to-dos across reservations, maintenance, guest communication, content, and finance.</p>
        </div>
        <div className="tasks-v4-toolbar" aria-label="Task filters">
          <button type="button"><Filter size={16} /> Filters</button>
          <button type="button">Assignee <ChevronDown size={16} /></button>
          <button type="button">Priority <ChevronDown size={16} /></button>
          <button type="button"><CalendarDays size={16} /> Jun 6 – Jun 12, 2026 <ChevronDown size={16} /></button>
          <button type="button" aria-label="Board view"><Grip size={17} /></button>
        </div>
      </section>

      <section className="tasks-v4-layout" aria-label="Tasks board">
        <div className="tasks-v4-board">
          <section className="tasks-v4-metrics" aria-label="Task summary">
            {TASK_METRICS.map((metric) => (
              <TaskMetricCard key={metric.label} metric={metric} />
            ))}
          </section>
          <div className="tasks-v4-next">
            <button type="button"><ChevronDown size={16} /> Next Actions <span>8</span></button>
            <button type="button" aria-label="Next actions"><ChevronDown size={16} /></button>
          </div>
          <div className="tasks-v4-columns">
            {TASK_COLUMNS.map((column) => (
              <TaskColumn
                key={column.title}
                column={column}
                selectedTaskId={selectedTaskId}
                onSelect={(task) => setSelectedTaskId(task.id)}
              />
            ))}
          </div>
        </div>
        <TaskDetailPanel task={selectedTask} detail={DETAIL_MODEL} />
      </section>
    </main>
  );
}
