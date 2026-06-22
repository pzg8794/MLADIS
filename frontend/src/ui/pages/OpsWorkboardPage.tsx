import { useEffect, useMemo, useState } from 'react';
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
import { TasksFactory } from '../../application/TasksFactory';
import type { Task, TaskColumn as TaskColumnObject, TaskDetail, TaskMetric, TaskWorkspace } from '../../domain/tasks';

const TASK_METRIC_ICONS = {
  overdue: AlertCircle,
  today: CalendarDays,
  week: ClipboardList,
  completed: CheckCircle2,
  total: ListTodo,
};

function TaskMetricCard({ metric }: { metric: TaskMetric }) {
  const Icon = TASK_METRIC_ICONS[metric.iconKey];

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
  task: Task;
  selected: boolean;
  onSelect: (task: Task) => void;
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
  column: TaskColumnObject;
  selectedTaskId: string;
  onSelect: (task: Task) => void;
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

function TaskDetailPanel({ task, detail }: { task: Task; detail: TaskDetail }) {
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
  const service = useMemo(() => TasksFactory.create(), []);
  const [workspace, setWorkspace] = useState<TaskWorkspace>(() => service.fallbackWorkspace());
  const [selectedTaskId, setSelectedTaskId] = useState(workspace.defaultTask()?.id ?? '');
  const selectedTask = workspace.taskById(selectedTaskId) ?? workspace.defaultTask();

  useEffect(() => {
    let active = true;
    service.loadWorkspace()
      .then((nextWorkspace) => {
        if (!active) return;
        setWorkspace(nextWorkspace);
        setSelectedTaskId((current) => nextWorkspace.taskById(current)?.id ?? nextWorkspace.defaultTask()?.id ?? '');
      })
      .catch(() => {
        if (active) setWorkspace(service.fallbackWorkspace());
      });
    return () => {
      active = false;
    };
  }, [service]);

  if (!selectedTask) return null;

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
            {workspace.metrics.map((metric) => (
              <TaskMetricCard key={metric.label} metric={metric} />
            ))}
          </section>
          <div className="tasks-v4-next">
            <button type="button"><ChevronDown size={16} /> Next Actions <span>8</span></button>
            <button type="button" aria-label="Next actions"><ChevronDown size={16} /></button>
          </div>
          <div className="tasks-v4-columns">
            {workspace.columns.map((column) => (
              <TaskColumn
                key={column.title}
                column={column}
                selectedTaskId={selectedTaskId}
                onSelect={(task) => setSelectedTaskId(task.id)}
              />
            ))}
          </div>
        </div>
        <TaskDetailPanel task={selectedTask} detail={workspace.detailFor(selectedTask)} />
      </section>
    </main>
  );
}
