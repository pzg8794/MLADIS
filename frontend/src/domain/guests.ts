import type { OpsCustomersSnapshot } from './models';
import { createWorkspaceMetadata, WorkspaceObjectMetadata } from './workspaceMetadata';

export class GuestWorkspace {
  constructor(
    public readonly snapshot: OpsCustomersSnapshot,
    public readonly compatibilityRoute = '/ops/customers/',
    public readonly metadata: WorkspaceObjectMetadata = createWorkspaceMetadata('api'),
  ) {}
}
