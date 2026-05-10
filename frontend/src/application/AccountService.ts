import { AccountRepository } from '../infrastructure/AccountRepository';

export class AccountService {
  constructor(private readonly repository: AccountRepository) {}

  async loadAccount() {
    return this.repository.getSnapshot();
  }
}
