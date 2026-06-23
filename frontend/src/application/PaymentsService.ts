import type { PaymentsWorkspace } from '../domain/payments';
import type { PaymentsRepository } from '../infrastructure/PaymentsRepository';

export class PaymentsService {
  constructor(private readonly repository: PaymentsRepository) {}

  async loadWorkspace(selectedTransactionId = ''): Promise<PaymentsWorkspace> {
    return this.repository.getWorkspace(selectedTransactionId);
  }

  async runAction(transactionId: string, action: string): Promise<void> {
    return this.repository.runAction(transactionId, action);
  }
}
