import { ApiAccountRepository } from '../infrastructure/AccountRepository';
import { HttpClient } from '../infrastructure/HttpClient';
import { AccountService } from './AccountService';

export class AccountFactory {
  static create(): AccountService {
    return new AccountService(
      new ApiAccountRepository(
        new HttpClient({ baseUrl: import.meta.env.VITE_API_BASE_URL ?? '' }),
      ),
    );
  }
}
