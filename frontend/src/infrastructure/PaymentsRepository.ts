import { PaymentsSnapshotPayload, PaymentsWorkspace, PaymentsWorkspaceFilters } from '../domain/payments';
import { HttpClient } from './HttpClient';

export class PaymentsRepository {
  constructor(private readonly http: HttpClient) {}

  async getWorkspace(selectedTransactionId = '', filters: PaymentsWorkspaceFilters = {}): Promise<PaymentsWorkspace> {
    const params = new URLSearchParams();
    if (selectedTransactionId) params.set('transaction', selectedTransactionId);
    if (filters.searchText || filters.search) params.set('search', filters.searchText || filters.search || '');
    if (filters.status) params.set('status', filters.status);
    if (filters.channel) params.set('channel', filters.channel);
    if (filters.method) params.set('method', filters.method);
    if (filters.dateFrom) params.set('date_from', filters.dateFrom);
    if (filters.dateTo) params.set('date_to', filters.dateTo);
    if (filters.page) params.set('page', String(filters.page));
    if (filters.pageSize) params.set('page_size', String(filters.pageSize));
    const query = params.toString() ? `?${params.toString()}` : '';
    const payload = await this.http.get<PaymentsSnapshotPayload>(`/api/ops/payments/${query}`);
    return PaymentsWorkspace.fromPayload(payload);
  }

  async runAction(transactionId: string, action: string): Promise<{ ok: boolean; message?: string }> {
    return this.http.post(`/api/ops/payments/${encodeURIComponent(transactionId)}/${encodeURIComponent(action)}/`, {});
  }
}
