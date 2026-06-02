import {
  AreaTile,
  MissionCauseSummary,
  PublicChatKitConfig,
  PublicGalleryImage,
  PublicHouseRule,
  PublicReviewHighlight,
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
      data.generated_at,
      'api',
    );
  }
}
