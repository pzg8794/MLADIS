import { GuestWorkspace, GuestWorkspaceFilters, GuestWorkspaceSnapshot } from '../domain/guests';
import { HttpClient } from './HttpClient';

export interface GuestMessageResponse {
  ok: boolean;
  message: {
    id: string;
    sender_label: string;
    body: string;
    status: string;
    timestamp: string;
    from_staff: boolean;
    requires_confirmation?: boolean;
  };
}

export class GuestRepository {
  constructor(private readonly http: HttpClient) {}

  async loadWorkspace(filters: GuestWorkspaceFilters = {}): Promise<GuestWorkspace> {
    const query = this.queryString({
      search: filters.query || '',
      segment: filters.segment || '',
      source: filters.source || '',
      status: filters.status || '',
    });
    const payload = await this.http.get<GuestWorkspaceSnapshot>(`/api/ops/guests/${query}`);
    return GuestWorkspace.fromPayload(payload);
  }

  async sendMessage(guestId: string, body: string, confirmed: boolean): Promise<GuestMessageResponse> {
    return this.http.post<GuestMessageResponse>(`/api/ops/guests/${encodeURIComponent(guestId)}/messages/`, {
      body,
      confirmed,
      channel: 'email',
    });
  }

  async addTag(guestId: string, tag: string): Promise<GuestWorkspace> {
    await this.http.post(`/api/ops/guests/${encodeURIComponent(guestId)}/tags/`, { tag });
    return this.loadWorkspace();
  }

  async removeTag(guestId: string, slug: string): Promise<GuestWorkspace> {
    await this.http.delete(`/api/ops/guests/${encodeURIComponent(guestId)}/tags/${encodeURIComponent(slug)}/`, {});
    return this.loadWorkspace();
  }

  private queryString(params: Record<string, string>): string {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) query.set(key, value);
    });
    const serialized = query.toString();
    return serialized ? `?${serialized}` : '';
  }
}
