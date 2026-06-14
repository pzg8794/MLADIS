import {
  AreaTile,
  AgentAccessStatus,
  MissionCauseSummary,
  PublicChatKitConfig,
  PublicGalleryImage,
  PublicHouseRule,
  PublicReviewHighlight,
  ReservationPricingPolicy,
  PublicSiteSnapshot,
  PublicStay,
  SocialLoginProvider,
} from '../domain/models';
import { HttpClient } from './HttpClient';

interface ApiGalleryImage {
  image_url: string;
  alt_text: string;
  caption: string;
}

interface ApiReviewHighlight {
  title: string;
  body: string;
  source_label: string;
}

interface ApiHouseRule {
  title: string;
  description: string;
}

interface ApiStay {
  id: number;
  name: string;
  slug: string;
  headline: string;
  description: string;
  location: string;
  image_url: string;
  rating: string;
  review_label: string;
  price_label: string;
  stat_list: string[];
  detail_url: string;
  airbnb_url: string;
  pricing: {
    base_price_cents: number;
    included_guests: number;
    extra_guest_cents: number;
    max_guests: number;
    currency: string;
    label: string;
    display_base_price: string;
    display_extra_guest_price: string;
  };
  gallery: ApiGalleryImage[];
  highlights: ApiReviewHighlight[];
  rules: ApiHouseRule[];
}

interface ApiAreaTile {
  title: string;
  caption: string;
  image_url: string;
}

interface ApiMissionCause {
  title: string;
  description: string;
}

interface ApiSocialLoginProvider {
  id: string;
  label: string;
  login_url: string;
  is_configured: boolean;
  is_launchable: boolean;
  disabled_reason: string;
  help_text: string;
}

interface ApiManagedChatKitConfig {
  mode: 'managed';
  session_url: string;
}

interface ApiCustomChatKitConfig {
  mode: 'custom';
  api_url: string;
  domain_key: string;
}

type ApiChatKitConfig = ApiManagedChatKitConfig | ApiCustomChatKitConfig;

interface ApiPublicSiteSnapshot {
  site_name: string;
  logo_url: string;
  contact_email: string;
  public_address_label: string;
  deposit_amount: string;
  stays: ApiStay[];
  area_tiles: ApiAreaTile[];
  mission_causes: ApiMissionCause[];
  social_providers?: ApiSocialLoginProvider[];
  chatkit?: ApiChatKitConfig | null;
  agent?: {
    agent_key?: string;
    agent_name?: string;
    is_authenticated: boolean;
    question_limit: number;
    questions_used: number;
    remaining_questions: number | null;
    can_ask: boolean;
    login_url: string;
  };
  generated_at: string;
}

export interface PublicSiteRepository {
  getSnapshot(): Promise<PublicSiteSnapshot>;
}

export class ApiPublicSiteRepository implements PublicSiteRepository {
  constructor(private readonly http: HttpClient) {}

  async getSnapshot(): Promise<PublicSiteSnapshot> {
    const data = await this.http.get<ApiPublicSiteSnapshot>('/api/site/summary/');
    return new PublicSiteSnapshot(
      data.site_name,
      data.logo_url,
      data.contact_email,
      data.public_address_label,
      data.deposit_amount,
      data.stays.map((stay) => new PublicStay(
        stay.id,
        stay.name,
        stay.slug,
        stay.headline,
        stay.description,
        stay.location,
        stay.image_url,
        stay.rating,
        stay.review_label,
        stay.price_label,
        stay.stat_list,
        stay.detail_url,
        stay.airbnb_url,
        new ReservationPricingPolicy(
          stay.pricing.base_price_cents,
          stay.pricing.included_guests,
          stay.pricing.extra_guest_cents,
          stay.pricing.max_guests,
          stay.pricing.currency,
          stay.pricing.label,
          stay.pricing.display_base_price,
          stay.pricing.display_extra_guest_price,
        ),
        stay.gallery.map((image) => new PublicGalleryImage(image.image_url, image.alt_text, image.caption)),
        stay.highlights.map((highlight) => new PublicReviewHighlight(highlight.title, highlight.body, highlight.source_label)),
        stay.rules.map((rule) => new PublicHouseRule(rule.title, rule.description)),
      )),
      data.area_tiles.map((tile) => new AreaTile(tile.title, tile.caption, tile.image_url)),
      data.mission_causes.map((cause) => new MissionCauseSummary(cause.title, cause.description)),
      (data.social_providers ?? []).map((provider) => new SocialLoginProvider(
        provider.id,
        provider.label,
        provider.login_url,
        provider.is_configured,
        provider.is_launchable,
        provider.disabled_reason,
        provider.help_text,
      )),
      data.chatkit
        ? new PublicChatKitConfig(
          data.chatkit.mode,
          data.chatkit.mode === 'managed' ? data.chatkit.session_url : null,
          data.chatkit.mode === 'custom' ? data.chatkit.api_url : null,
          data.chatkit.mode === 'custom' ? data.chatkit.domain_key : null,
        )
        : null,
      new AgentAccessStatus(
        Boolean(data.agent?.is_authenticated),
        data.agent?.question_limit ?? 5,
        data.agent?.questions_used ?? 0,
        data.agent?.remaining_questions ?? null,
        Boolean(data.agent?.can_ask),
        data.agent?.login_url ?? '/accounts/login/?next=/accounts/',
        data.agent?.agent_key ?? 'public-booking-agent',
        data.agent?.agent_name ?? 'Booking agent',
      ),
      data.generated_at,
      'api',
    );
  }
}
