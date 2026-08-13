import type { OpsAgentConversation, OpsAgentFaq, OpsAgentSnapshot } from './models';
import { createWorkspaceMetadata, WorkspaceObjectMetadata } from './workspaceMetadata';

export type AgentConversation = OpsAgentConversation;
export type AgentFAQ = OpsAgentFaq;
export type AgentKnowledgeSource = { label: string; status: string; syncedAt: string };

export type AgentReplyBlockKind = 'heading' | 'step' | 'bullet' | 'paragraph';

export type AgentReplyBlock = {
  kind: AgentReplyBlockKind;
  text: string;
  marker?: string;
};

export class AgentReplyPresentation {
  constructor(public readonly blocks: AgentReplyBlock[]) {}

  static fromText(value: string): AgentReplyPresentation {
    const normalized = value
      .replace(/\r\n?/g, '\n')
      .replace(/\s+(Quick steps(?: \(English \/ Espa[nñ]ol\))?)/gi, '\n\n$1\n')
      .replace(/\s+(Important notes)/gi, '\n\n$1\n')
      .replace(/\s+(Next step[^\n]*\?)/gi, '\n\n$1\n')
      .replace(/(^|\s)(\d{1,2})\)\s+/g, '$1\n$2) ')
      .replace(/\n{3,}/g, '\n\n')
      .trim();

    if (!normalized) return new AgentReplyPresentation([]);

    const blocks = normalized
      .split(/\n+/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map<AgentReplyBlock>((line) => {
        if (/^(Quick steps|Important notes|Next step)/i.test(line)) {
          return { kind: 'heading', text: line };
        }
        const step = line.match(/^(\d{1,2})[.)]\s*(.+)$/);
        if (step) return { kind: 'step', marker: step[1], text: step[2] };
        const bullet = line.match(/^[-*•–—]\s*(.+)$/);
        if (bullet) return { kind: 'bullet', text: bullet[1] };
        return { kind: 'paragraph', text: line };
      });

    return new AgentReplyPresentation(blocks);
  }
}

export class AgentWorkspace {
  constructor(
    public readonly snapshot: OpsAgentSnapshot,
    public readonly knowledgeSources: AgentKnowledgeSource[] = [],
    public readonly metadata: WorkspaceObjectMetadata = createWorkspaceMetadata('api'),
  ) {}
}
