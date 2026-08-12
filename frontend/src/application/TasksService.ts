import type { Task, TaskWorkspace } from '../domain/tasks';
import type { TasksRepository } from '../infrastructure/TasksRepository';

export class TasksService {
  constructor(private readonly repository: TasksRepository) {}

  fallbackWorkspace(): TaskWorkspace {
    return this.repository.fallback();
  }

  async loadWorkspace(): Promise<TaskWorkspace> {
    return this.repository.getWorkspace();
  }

  async setCompletion(task: Task, completed: boolean): Promise<TaskWorkspace> {
    await this.repository.setCompletion(task, completed);
    return this.repository.getWorkspace();
  }
}
