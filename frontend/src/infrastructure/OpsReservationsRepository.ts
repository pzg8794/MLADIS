import {
  OpsReservationMetric,
  OpsReservationRow,
  OpsReservationSegment,
  OpsReservationsSnapshot,
} from '../domain/models';
import { OpsReservation, type OpsReservationPayload } from '../domain/reservations';
import { HttpClient } from './HttpClient';

interface ApiOpsReservationMetric {
  label: string;
  value: number;
  caption: string;
}

interface ApiOpsReservationSegment {
  value: string;
  label: string;
  count: number;
  url: string;
}

interface ApiOpsReservationRow {
  id: number;
  record_type: 'direct' | 'airbnb';
  name: string;
  email: string;
  phone: string;
  contact_path: string;
  listing: string;
  listing_id: string;
  stay_dates: string;
  guests: string;
  rating: string;
  feedback: string;
  source_subject: string;
  thread_url: string;
  consent_status: string;
  segment: string;
  segment_value: string;
  record_admin_url: string;
  profile_admin_url: string;
  feedback_admin_url: string;
  updated_at: string;
}

interface ApiOpsReservationsSnapshot {
  summary_cards: ApiOpsReservationMetric[];
  segment_options: ApiOpsReservationSegment[];
  selected_segment: string;
  export_url: string;
  legacy_url: string;
  rows: ApiOpsReservationRow[];
  reservations?: OpsReservationPayload[];
  generated_at: string;
}

export interface OpsReservationsRepository {
  getSnapshot(): Promise<OpsReservationsSnapshot>;
  updateStatus(reservation: OpsReservation, status: 'reviewing' | 'confirmed' | 'cancelled'): Promise<OpsReservation | null>;
}

export class ApiOpsReservationsRepository implements OpsReservationsRepository {
  constructor(private readonly http: HttpClient) {}

  async getSnapshot(): Promise<OpsReservationsSnapshot> {
    const data = await this.http.get<ApiOpsReservationsSnapshot>(this.snapshotPath());
    const rows = data.rows.map((row) => new OpsReservationRow(
      row.id,
      row.record_type,
      row.name,
      row.email,
      row.phone,
      row.contact_path,
      row.listing,
      row.listing_id,
      row.stay_dates,
      row.guests,
      row.rating,
      row.feedback,
      row.source_subject,
      row.thread_url,
      row.consent_status,
      row.segment,
      row.segment_value,
      row.record_admin_url,
      row.profile_admin_url,
      row.feedback_admin_url,
      row.updated_at,
    ));
    const reservations = (data.reservations ?? []).map((reservation) => OpsReservation.fromPayload(reservation));

    return new OpsReservationsSnapshot(
      data.summary_cards.map((metric) => new OpsReservationMetric(metric.label, metric.value, metric.caption)),
      data.segment_options.map((segment) => new OpsReservationSegment(segment.value, segment.label, segment.count, segment.url)),
      data.selected_segment,
      data.export_url,
      data.legacy_url,
      rows,
      data.generated_at,
      reservations,
    );
  }

  async updateStatus(reservation: OpsReservation, status: 'reviewing' | 'confirmed' | 'cancelled'): Promise<OpsReservation | null> {
    const data = await this.http.post<{ reservation?: OpsReservationPayload }>(
      `/api/ops/reservations/${reservation.id}/status/`,
      { status },
    );
    return data.reservation ? OpsReservation.fromPayload(data.reservation) : null;
  }

  private snapshotPath(): string {
    const params = new URLSearchParams(window.location.search);
    const segment = params.get('segment');
    return segment ? `/api/ops/reservations/?segment=${encodeURIComponent(segment)}` : '/api/ops/reservations/';
  }
}
