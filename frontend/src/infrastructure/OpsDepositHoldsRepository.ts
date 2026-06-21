import {
  DepositHold,
  DepositHoldsSnapshot,
  type DepositHoldAction,
  type DepositHoldPayload,
  type DepositHoldsSnapshotPayload,
} from '../domain/depositHolds';
import { HttpClient } from './HttpClient';

interface DepositHoldActionResponse {
  ok: boolean;
  hold: DepositHoldPayload;
  snapshot: DepositHoldsSnapshotPayload;
}

export interface OpsDepositHoldsRepository {
  getSnapshot(): Promise<DepositHoldsSnapshot>;
  applyAction(hold: DepositHold, action: DepositHoldAction): Promise<DepositHoldsSnapshot>;
}

export class ApiOpsDepositHoldsRepository implements OpsDepositHoldsRepository {
  constructor(private readonly http: HttpClient) {}

  async getSnapshot(): Promise<DepositHoldsSnapshot> {
    const data = await this.http.get<DepositHoldsSnapshotPayload>('/api/ops/deposits/');
    return DepositHoldsSnapshot.fromPayload(data);
  }

  async applyAction(hold: DepositHold, action: DepositHoldAction): Promise<DepositHoldsSnapshot> {
    const data = await this.http.post<DepositHoldActionResponse>(
      `/api/ops/deposit-holds/${encodeURIComponent(hold.id)}/${action}/`,
      {},
    );
    return DepositHoldsSnapshot.fromPayload(data.snapshot);
  }
}
