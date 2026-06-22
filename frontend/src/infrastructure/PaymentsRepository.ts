import { PaymentsSnapshotPayload, PaymentsWorkspace } from '../domain/payments';
import { HttpClient } from './HttpClient';

export class PaymentsRepository {
  constructor(private readonly http: HttpClient) {}

  async getWorkspace(selectedTransactionId = ''): Promise<PaymentsWorkspace> {
    const query = selectedTransactionId ? `?transaction=${encodeURIComponent(selectedTransactionId)}` : '';
    const payload = await this.http.get<PaymentsSnapshotPayload>(`/api/ops/payments/${query}`);
    return PaymentsWorkspace.fromPayload(payload);
  }

  async runAction(transactionId: string, action: string): Promise<void> {
    await this.http.post(`/api/ops/payments/${encodeURIComponent(transactionId)}/${encodeURIComponent(action)}/`, {});
  }
}
