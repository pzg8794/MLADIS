import { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  FileText,
  ListTodo,
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
    </section>
  );
}

function TaskDetailPanel({
  task,
  detail,
  saving,
  onClose,
  onCompletion,
}: {
  task: Task;
  detail: TaskDetail;
  saving: boolean;
  onClose: () => void;
  onCompletion: (completed: boolean) => void;
}) {
  return (
    <aside className="tasks-v4-detail">
      <header>
        <div>
          <FileText size={18} />
          <h2>{task.title}</h2>
        </div>
        <span className={`tasks-v4-status tasks-v4-status--${task.status}`}>
          {task.statusLabel}
        </span>
        <button type="button" aria-label="Close task details" onClick={onClose}><X size={18} /></button>
      </header>

      <p className="tasks-v4-detail__summary">{detail.description}</p>

      <section className="tasks-v4-detail__selectors" aria-label="Task assignment">
        <article>
          <label>Assignee</label>
          <span className="tasks-v4-detail__value"><span className="tasks-v4-avatar tasks-v4-avatar--green">ML</span> {detail.assignee}</span>
        </article>
        <article>
          <label>Priority</label>
          <span className="tasks-v4-detail__value is-high"><AlertCircle size={13} /> {detail.priority}</span>
        </article>
        <article>
          <label>Due</label>
          <span className="tasks-v4-detail__value is-due"><CalendarDays size={13} /> {detail.due}</span>
        </article>
      </section>

      <section className="tasks-v4-detail__section">
        <h3>Links</h3>
        <div className="tasks-v4-links">
          {detail.links.map((link) => (
            <a href={link.url} key={`${link.label}-${link.value}`} target="_blank" rel="noreferrer">{link.label}: {link.value}</a>
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
        <small>Next action from the tracked work item.</small>
      </section>

      <section className="tasks-v4-detail__section tasks-v4-activity">
        <h3>Activity</h3>
        <p><span className="tasks-v4-avatar tasks-v4-avatar--blue">PG</span> {detail.activity}</p>
        <small>{new Date(detail.updatedAt).toLocaleString()}</small>
      </section>

      <div className="tasks-v4-detail__actions">
        <button type="button" className="is-complete" disabled={saving} onClick={() => onCompletion(task.status !== 'done')}>
          <Check size={16} /> {saving ? 'Saving...' : task.status === 'done' ? 'Reopen task' : 'Mark complete'}
        </button>
      </div>
    </aside>
  );
}

export function OpsWorkboardPage() {
  const service = useMemo(() => TasksFactory.create(), []);
  const [workspace, setWorkspace] = useState<TaskWorkspace>(() => service.fallbackWorkspace());
  const [selectedTaskId, setSelectedTaskId] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const selectedTask = selectedTaskId ? workspace.taskById(selectedTaskId) : null;

  useEffect(() => {
    let active = true;
    service.loadWorkspace()
      .then((nextWorkspace) => {
        if (!active) return;
        setWorkspace(nextWorkspace);
        setSelectedTaskId((current) => nextWorkspace.taskById(current)?.id ?? '');
      })
      .catch(() => {
        if (active) setWorkspace(service.fallbackWorkspace());
      });
    return () => {
      active = false;
    };
  }, [service]);

  const updateCompletion = async (task: Task, completed: boolean) => {
    setSaving(true);
    setMessage('');
    try {
      const nextWorkspace = await service.setCompletion(task, completed);
      setWorkspace(nextWorkspace);
      setSelectedTaskId(nextWorkspace.taskById(task.id)?.id ?? '');
      setMessage(completed ? 'Task marked complete.' : 'Task reopened.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'The task could not be updated.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="dashboard-content tasks-v4-page">
      <section className="tasks-v4-header">
        <div>
          <h1>Tasks &amp; Workboard</h1>
          <p>Track operational to-dos across reservations, maintenance, guest communication, content, and finance.</p>
        </div>
        {message && <p className="tasks-v4-message" role="status">{message}</p>}
      </section>

      <section className={`tasks-v4-layout${selectedTask ? ' tasks-v4-layout--detail' : ''}`} aria-label="Tasks board">
        <div className="tasks-v4-board">
          <section className="tasks-v4-metrics" aria-label="Task summary">
            {workspace.metrics.map((metric) => (
              <TaskMetricCard key={metric.label} metric={metric} />
            ))}
          </section>
          <div className="tasks-v4-next"><strong>Tracked work items</strong><span>{workspace.allTasks.length}</span></div>
          {workspace.allTasks.length === 0 && <p className="tasks-v4-empty">No work items are currently available.</p>}
          <div className="tasks-v4-columns">
            {workspace.columns.map((column) => (
              <TaskColumn
                key={column.title}
                column={column}
                selectedTaskId={selectedTaskId}
                onSelect={(task) => setSelectedTaskId((current) => current === task.id ? '' : task.id)}
              />
            ))}
          </div>
        </div>
        {selectedTask && (
          <TaskDetailPanel
            task={selectedTask}
            detail={workspace.detailFor(selectedTask)}
            saving={saving}
            onClose={() => setSelectedTaskId('')}
            onCompletion={(completed) => updateCompletion(selectedTask, completed)}
          />
        )}
      </section>
    </main>
  );
}
