import {
  PropertyDetailMetric,
  PropertyListing,
  PropertyListingTab,
  PropertyListingTag,
  PropertyListingsWorkspace,
} from '../domain/properties';
import { createWorkspaceMetadata } from '../domain/workspaceMetadata';

const BASE = import.meta.env.BASE_URL;

export class PropertyListingsRepository {
  getWorkspace(): PropertyListingsWorkspace {
    return new PropertyListingsWorkspace(
      [
        new PropertyListingTab('All', '12', true),
        new PropertyListingTab('Published', '11'),
        new PropertyListingTab('Draft', '1'),
        new PropertyListingTab('Inactive', '0'),
        new PropertyListingTab('Maintenance', '1'),
        new PropertyListingTab('Archived', '2', false, true),
      ],
      [
        new PropertyListing(
          'g101',
          '3 Beds Apt, Vacation Home & Pool, G-101',
          'Colinas del Arroyo II, SDN',
          `${BASE}stays/stay-3br.jpg`,
          '$180',
          '4.93',
          '42 reviews',
          '3 bedrooms',
          '4 beds',
          '2 baths',
          '4 guests',
          '72%',
          '+12pp vs last 7 days',
          'Ready',
          'ready',
          'Published',
          [
            new PropertyListingTag('Pool', 'blue'),
            new PropertyListingTag('Self check-in', 'purple'),
            new PropertyListingTag('$200 Secure hold', 'amber'),
            new PropertyListingTag('Direct booking', 'green'),
          ],
        ),
        new PropertyListing(
          'pool-6br',
          '6 Beds Apt, Vacation Home & Pool',
          'Colinas del Arroyo II, SDN',
          `${BASE}stays/stay-6br.jpg`,
          '$250',
          '4.87',
          '37 reviews',
          '6 bedrooms',
          '8 beds',
          '3 baths',
          '8 guests',
          '68%',
          '+8pp vs last 7 days',
          'Ready',
          'ready',
          'Published',
          [
            new PropertyListingTag('Pool', 'blue'),
            new PropertyListingTag('Self check-in', 'purple'),
            new PropertyListingTag('$200 Secure hold', 'amber'),
            new PropertyListingTag('Direct booking', 'green'),
          ],
        ),
        new PropertyListing(
          'pool-2br',
          '2 Beds Apt, Vacation Home & Pool',
          'Colinas del Arroyo II, SDN',
          `${BASE}stays/stay-2br.jpg`,
          '$120',
          '4.76',
          '28 reviews',
          '2 bedrooms',
          '3 beds',
          '2 baths',
          '3 guests',
          '52%',
          '-4pp vs last 7 days',
          'Needs attention',
          'attention',
          'Published',
          [
            new PropertyListingTag('Pool', 'blue'),
            new PropertyListingTag('Self check-in', 'purple'),
            new PropertyListingTag('$200 Secure hold', 'amber'),
            new PropertyListingTag('Direct booking', 'green'),
          ],
        ),
      ],
      [
        new PropertyDetailMetric('Occupancy', '72%', '', 'blue'),
        new PropertyDetailMetric('ADR', '$146', '+9% vs last 7 days', 'green'),
      ],
      createWorkspaceMetadata('fallback', ['properties API projection']),
    );
  }
}
