import { createWorkspaceMetadata, WorkspaceObjectMetadata } from './workspaceMetadata';

export type TaskTone = 'danger' | 'warning' | 'primary' | 'success' | 'violet';
export type TaskStatus = 'progress' | 'waiting' | 'done';
export type TaskDueTone = 'today' | 'soon' | 'done';

export class TaskMetric {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly caption: string,
    public readonly tone: TaskTone,
    public readonly iconKey: 'overdue' | 'today' | 'week' | 'completed' | 'total',
  ) {}
}

export class Task {
  constructor(
    public readonly id: string,
    public readonly title: string,
    public readonly meta: string[],
    public readonly due: string,
    public readonly dueTone: TaskDueTone,
    public readonly avatar: string,
    public readonly avatarTone: string,
    public readonly status: TaskStatus,
  ) {}
}

export class TaskColumn {
  constructor(
    public readonly title: string,
    public readonly count: string,
    public readonly tone: TaskStatus,
    public readonly tasks: Task[],
  ) {}
}

export class TaskDetail {
  constructor(
    public readonly description: string,
    public readonly assignee: string,
    public readonly priority: string,
    public readonly due: string,
    public readonly links: Array<{ label: string; value: string }>,
    public readonly details: Array<{ label: string; value: string }>,
    public readonly note: string,
    public readonly activity: string,
  ) {}
}

export class TaskWorkspace {
  constructor(
    public readonly metrics: TaskMetric[],
    public readonly columns: TaskColumn[],
    public readonly detailsByTaskId: Record<string, TaskDetail>,
    public readonly metadata: WorkspaceObjectMetadata = createWorkspaceMetadata('fallback'),
  ) {}

  get source() {
    return this.metadata.source;
  }

  get allTasks(): Task[] {
    return this.columns.flatMap((column) => column.tasks);
  }

  defaultTask(): Task | null {
    return this.allTasks[0] ?? null;
  }

  taskById(id: string): Task | null {
    return this.allTasks.find((task) => task.id === id) ?? null;
  }

  detailFor(task: Task): TaskDetail {
    return this.detailsByTaskId[task.id] ?? this.detailsByTaskId.default;
  }
}
