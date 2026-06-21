import { ApiOpsDepositHoldsRepository } from '../infrastructure/OpsDepositHoldsRepository';
import { HttpClient } from '../infrastructure/HttpClient';
import { OpsDepositHoldsService } from './OpsDepositHoldsService';

export class OpsDepositHoldsFactory {
  static create(): OpsDepositHoldsService {
    return new OpsDepositHoldsService(
      new ApiOpsDepositHoldsRepository(
        new HttpClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' }),
      ),
    );
  }
}
