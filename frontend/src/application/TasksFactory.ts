import { HttpClient } from '../infrastructure/HttpClient';
import { ApiOpsWorkspaceRepository } from '../infrastructure/OpsWorkspaceRepository';
import { TasksRepository } from '../infrastructure/TasksRepository';
import { TasksService } from './TasksService';

export class TasksFactory {
  static create(): TasksService {
    const http = new HttpClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' });
    return new TasksService(new TasksRepository(new ApiOpsWorkspaceRepository(http)));
  }
}
