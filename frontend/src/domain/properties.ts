import { createWorkspaceMetadata, WorkspaceObjectMetadata } from './workspaceMetadata';

export type PropertyListingTone = 'blue' | 'purple' | 'amber' | 'green' | 'orange' | 'red';
export type PropertyListingStatusTone = 'ready' | 'attention' | 'published';

export class PropertyListingTab {
  constructor(
    public readonly label: string,
    public readonly count: string,
    public readonly active = false,
    public readonly separated = false,
  ) {}
}

export class PropertyListingTag {
  constructor(
    public readonly label: string,
    public readonly tone: PropertyListingTone,
  ) {}
}

export class PropertyListing {
  constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly location: string,
    public readonly imageSrc: string,
    public readonly price: string,
    public readonly rating: string,
    public readonly reviews: string,
    public readonly bedrooms: string,
    public readonly beds: string,
    public readonly baths: string,
    public readonly guests: string,
    public readonly occupancy: string,
    public readonly occupancyTrend: string,
    public readonly readiness: string,
    public readonly readinessTone: PropertyListingStatusTone,
    public readonly status: string,
    public readonly tags: PropertyListingTag[],
  ) {}
}

export class PropertyDetailMetric {
  constructor(
    public readonly label: string,
    public readonly value: string,
    public readonly caption: string,
    public readonly tone: PropertyListingTone,
  ) {}
}

export class PropertyListingsWorkspace {
  constructor(
    public readonly tabs: PropertyListingTab[],
    public readonly listings: PropertyListing[],
    public readonly availability: PropertyDetailMetric[],
    public readonly metadata: WorkspaceObjectMetadata = createWorkspaceMetadata('fallback'),
  ) {}

  get source() {
    return this.metadata.source;
  }
}
