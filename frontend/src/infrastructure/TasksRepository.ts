import { Task, TaskColumn, TaskDetail, TaskMetric, TaskWorkspace } from '../domain/tasks';
import { createWorkspaceMetadata } from '../domain/workspaceMetadata';
import type { OpsWorkspaceRepository } from './OpsWorkspaceRepository';
import type { OpsWorkItem, OpsWorkboardSnapshot } from '../domain/models';

function taskStatus(item: OpsWorkItem): 'progress' | 'waiting' | 'done' {
  if (item.isDone) return 'done';
  if (item.status === 'in_progress') return 'progress';
  return 'waiting';
}

function dueLabel(item: OpsWorkItem): string {
  if (item.isDone && item.completedAt) {
    return `Completed ${new Date(item.completedAt).toLocaleDateString()}`;
  }
  if (item.dueDate) return `Due ${new Date(`${item.dueDate}T12:00:00`).toLocaleDateString()}`;
  return 'No due date';
}

function toTask(item: OpsWorkItem): Task {
  const status = taskStatus(item);
  return new Task(
    String(item.id),
    item.id,
    item.title,
    [item.listName, item.neuronLabel],
    dueLabel(item),
    item.isDone ? 'done' : item.dueDate ? 'soon' : 'soon',
    item.neuronLabel.slice(0, 2).toUpperCase(),
    status === 'done' ? 'green' : status === 'progress' ? 'blue' : 'slate',
    status,
    item.statusLabel,
  );
}

function taskDetail(item: OpsWorkItem): TaskDetail {
  const links = [
    { label: 'Source', value: 'Open source', url: item.sourceUrl },
    { label: 'GitHub', value: 'Open GitHub record', url: item.githubUrl },
    { label: 'Drive', value: 'Open Drive record', url: item.driveUrl },
  ].filter((link) => Boolean(link.url));

  return new TaskDetail(
    item.description || item.nextAction || 'No description has been recorded for this work item.',
    'MLADIS Operations',
    item.priorityLabel,
    dueLabel(item),
    links,
    [
      { label: 'List', value: item.listName },
      { label: 'Neuron', value: item.neuronLabel },
      { label: 'Status', value: item.statusLabel },
    ],
    item.nextAction || 'No next action has been recorded.',
    item.isDone ? 'Work item completed' : `Work item is ${item.statusLabel.toLowerCase()}`,
    item.updatedAt,
  );
}

function emptyTaskWorkspace(): TaskWorkspace {
  return new TaskWorkspace([], [], {}, createWorkspaceMetadata('api', ['workboard API unavailable']));
}

function toTaskWorkspace(snapshot: OpsWorkboardSnapshot): TaskWorkspace {
  const allItems = snapshot.statusColumns.flatMap((column) => column.items);
  const uniqueItems = Array.from(new Map(allItems.map((item) => [item.id, item])).values());
  const tasks = uniqueItems.map(toTask);
  const progressTasks = tasks.filter((task) => task.status === 'progress');
  const waitingTasks = tasks.filter((task) => task.status === 'waiting');
  const doneTasks = tasks.filter((task) => task.status === 'done');
  const columns = [
    new TaskColumn('In Progress', String(progressTasks.length), 'progress', progressTasks),
    new TaskColumn('Waiting', String(waitingTasks.length), 'waiting', waitingTasks),
    new TaskColumn('Done', String(doneTasks.length), 'done', doneTasks),
  ];
  const allTasks = columns.flatMap((column) => column.tasks);
  const itemById = new Map(uniqueItems.map((item) => [String(item.id), item]));
  const detailsByTaskId = Object.fromEntries(
    allTasks.map((task) => [task.id, taskDetail(itemById.get(task.id)!)]),
  );
  const tones = ['violet', 'success', 'primary', 'warning', 'danger'] as const;
  const iconKeys = ['total', 'completed', 'week', 'today', 'overdue'] as const;

  return new TaskWorkspace(
    snapshot.summaryCards.map((metric, index) => new TaskMetric(
      metric.label,
      metric.value,
      metric.caption,
      tones[index] ?? 'primary',
      iconKeys[index] ?? 'total',
    )),
    columns,
    detailsByTaskId,
    createWorkspaceMetadata('api'),
  );
}

export class TasksRepository {
  constructor(private readonly opsRepository: OpsWorkspaceRepository) {}

  fallback(): TaskWorkspace {
    return emptyTaskWorkspace();
  }

  async getWorkspace(): Promise<TaskWorkspace> {
    try {
      return toTaskWorkspace(await this.opsRepository.getWorkboard());
    } catch {
      return emptyTaskWorkspace();
    }
  }

  async setCompletion(task: Task, completed: boolean): Promise<void> {
    await this.opsRepository.setWorkItemCompletion(task.recordId, completed);
  }
}
