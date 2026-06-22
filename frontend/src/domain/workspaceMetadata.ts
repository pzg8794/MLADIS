export type WorkspaceDataSource = 'api' | 'fallback' | 'mixed';

export class WorkspaceObjectMetadata {
  constructor(
    public readonly source: WorkspaceDataSource,
    public readonly missingFields: string[] = [],
    public readonly isComplete = missingFields.length === 0,
  ) {}
}

export function createWorkspaceMetadata(
  source: WorkspaceDataSource,
  missingFields: string[] = [],
): WorkspaceObjectMetadata {
  return new WorkspaceObjectMetadata(source, missingFields, missingFields.length === 0);
}
