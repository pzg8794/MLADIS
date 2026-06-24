import type { PaymentsWorkspace, PaymentsWorkspaceFilters } from '../domain/payments';
import type { PaymentsRepository } from '../infrastructure/PaymentsRepository';

export class PaymentsService {
  constructor(private readonly repository: PaymentsRepository) {}

  async loadWorkspace(selectedTransactionId = '', filters: PaymentsWorkspaceFilters = {}): Promise<PaymentsWorkspace> {
    return this.repository.getWorkspace(selectedTransactionId, filters);
  }

  async runAction(transactionId: string, action: string): Promise<{ ok: boolean; message?: string }> {
    return this.repository.runAction(transactionId, action);
  }
}
