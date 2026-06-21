import {
  DepositHold,
  DepositHoldsSnapshot,
  type DepositHoldAction,
} from '../domain/depositHolds';
import { OpsDepositHoldsRepository } from '../infrastructure/OpsDepositHoldsRepository';

export class OpsDepositHoldsService {
  constructor(private readonly repository: OpsDepositHoldsRepository) {}

  async loadDeposits(): Promise<DepositHoldsSnapshot> {
    return this.repository.getSnapshot();
  }

  filterDeposits(rows: DepositHold[], query: string): DepositHold[] {
    return rows.filter((row) => row.matches(query));
  }

  async applyAction(hold: DepositHold, action: DepositHoldAction): Promise<DepositHoldsSnapshot> {
    if (!hold.can(action)) {
      throw new Error('That action is not available for this deposit hold.');
    }
    return this.repository.applyAction(hold, action);
  }
}
