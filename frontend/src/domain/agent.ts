import type { OpsAgentConversation, OpsAgentFaq, OpsAgentSnapshot } from './models';
import { createWorkspaceMetadata, WorkspaceObjectMetadata } from './workspaceMetadata';

export type AgentConversation = OpsAgentConversation;
export type AgentFAQ = OpsAgentFaq;
export type AgentKnowledgeSource = { label: string; status: string; syncedAt: string };

export class AgentWorkspace {
  constructor(
    public readonly snapshot: OpsAgentSnapshot,
    public readonly knowledgeSources: AgentKnowledgeSource[] = [],
    public readonly metadata: WorkspaceObjectMetadata = createWorkspaceMetadata('api'),
  ) {}
}
