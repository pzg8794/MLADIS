import { AccountInvoice, AccountReservation, AccountSnapshot } from '../domain/models';
import { HttpClient } from './HttpClient';

interface ApiAccountReservation {
  id: number;
  guest_name: string;
  stay_name: string;
  check_in: string;
  check_out: string;
  guests: number;
  phone: string;
  status: string;
  can_cancel: boolean;
  display_total: string;
  display_deposit: string;
  coupon_code: string;
  message: string;
  detail_url: string;
  edit_url: string;
  cancel_url: string;
  airbnb_url: string;
  created_at: string;
}

interface ApiAccountInvoice {
  id: number;
  title: string;
  status: string;
  display_total: string;
  print_url: string;
  created_at: string;
}

interface ApiAccountSnapshot {
  profile: {
    name: string;
    email: string;
    is_staff?: boolean;
    is_superuser?: boolean;
  };
  reservations: ApiAccountReservation[];
  invoices: ApiAccountInvoice[];
  generated_at: string;
}

export interface AccountRepository {
  getSnapshot(): Promise<AccountSnapshot>;
}

export class ApiAccountRepository implements AccountRepository {
  constructor(private readonly http: HttpClient) {}

  async getSnapshot(): Promise<AccountSnapshot> {
    const data = await this.http.get<ApiAccountSnapshot>('/api/account/summary/');
    return new AccountSnapshot(
      data.profile.name,
      data.profile.email,
      Boolean(data.profile.is_staff),
      Boolean(data.profile.is_superuser),
      data.reservations.map((reservation) => new AccountReservation(
        reservation.id,
        reservation.guest_name,
        reservation.stay_name,
        reservation.check_in,
        reservation.check_out,
        reservation.guests,
        reservation.phone,
        reservation.status,
        reservation.can_cancel,
        reservation.display_total,
        reservation.display_deposit,
        reservation.coupon_code,
        reservation.message,
        reservation.detail_url,
        reservation.edit_url,
        reservation.cancel_url,
        reservation.airbnb_url,
        reservation.created_at,
      )),
      data.invoices.map((invoice) => new AccountInvoice(
        invoice.id,
        invoice.title,
        invoice.status,
        invoice.display_total,
        invoice.print_url,
        invoice.created_at,
      )),
      data.generated_at,
    );
  }
}
