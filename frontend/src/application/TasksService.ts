import type { TaskWorkspace } from '../domain/tasks';
import type { TasksRepository } from '../infrastructure/TasksRepository';

export class TasksService {
  constructor(private readonly repository: TasksRepository) {}

  fallbackWorkspace(): TaskWorkspace {
    return this.repository.fallback();
  }

  async loadWorkspace(): Promise<TaskWorkspace> {
    return this.repository.getWorkspace();
  }
}
