import { createWorkspaceMetadata, WorkspaceObjectMetadata } from './workspaceMetadata';

export type AdminTone = 'blue' | 'violet' | 'teal' | 'amber' | 'rose';
export type AdminFeedTone = 'blue' | 'green' | 'amber' | 'cyan';
export type AdminHealthTone = 'blue' | 'green' | 'teal' | 'slate';

export class AdminShortcut {
  constructor(
    public readonly label: string,
    public readonly description: string,
    public readonly href: string,
    public readonly iconKey: string,
    public readonly action: string,
    public readonly tone: AdminTone = 'blue',
  ) {}
}

export class AdminMetric {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly caption: string,
    public readonly iconKey: string,
    public readonly tone: AdminTone = 'blue',
  ) {}
}

export class AdminFeedItem {
  constructor(
    public readonly time: string,
    public readonly title: string,
    public readonly detail: string,
    public readonly iconKey: string,
    public readonly tone: AdminFeedTone,
  ) {}
}

export class AdminHealthCard {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly caption: string,
    public readonly iconKey: string,
    public readonly tone: AdminHealthTone,
  ) {}
}

export class AdminTransactionDocument {
  constructor(
    public readonly id: string,
    public readonly kind: string,
    public readonly title: string,
    public readonly reference: string,
    public readonly status: string,
    public readonly displayAmount: string,
    public readonly recipientEmail: string,
    public readonly viewUrl: string,
    public readonly downloadUrl: string,
  ) {}
}

export class AdminWorkspace {
  constructor(
    public readonly shortcuts: AdminShortcut[],
    public readonly metrics: AdminMetric[],
    public readonly feedItems: AdminFeedItem[],
    public readonly healthCards: AdminHealthCard[],
    public readonly transactionDocuments: AdminTransactionDocument[],
    public readonly metadata: WorkspaceObjectMetadata = createWorkspaceMetadata('fallback'),
  ) {}

  get source() {
    return this.metadata.source;
  }
}
