# Frontend Domain Code Stubs

These TypeScript stubs show the intended OOP shape for the Guests frontend.

## Domain objects

```ts
export type GuestSegmentValue = 'new' | 'average' | 'repeat' | 'vip' | 'blacklisted';
export type GuestStatusValue = 'active' | 'inactive' | 'blocked' | 'archived';

export class Money {
  constructor(
    public readonly cents: number,
    public readonly currency: string = 'USD',
  ) {}

  format(): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: this.currency,
      maximumFractionDigits: 0,
    }).format(this.cents / 100);
  }
}

export class GuestIdentity {
  constructor(
    public readonly name: string,
    public readonly country: string,
    public readonly preferredLanguage: string,
    public readonly source: string,
  ) {}

  initials(): string {
    const parts = this.name.trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return 'G';
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
}

export class GuestContact {
  constructor(
    public readonly email: string,
    public readonly phone: string,
    public readonly lastContactAt: string,
    public readonly profileAdminUrl: string,
    public readonly fullProfileUrl: string,
  ) {}

  canMessage(): boolean {
    return Boolean(this.email || this.phone);
  }
}

export class GuestProfile {
  constructor(
    public readonly birthday: string,
    public readonly travelStyle: string,
    public readonly guestSince: string,
    public readonly notes: string,
  ) {}
}

export class GuestSegmentState {
  constructor(
    public readonly value: GuestSegmentValue,
    public readonly label: string,
    public readonly tone: string,
  ) {}
}

export class GuestStatusState {
  constructor(
    public readonly value: GuestStatusValue,
    public readonly label: string,
    public readonly tone: string,
  ) {}
}

export class GuestMarketingState {
  constructor(
    public readonly consentStatus: string,
    public readonly consentLabel: string,
    public readonly requestedAt: string,
    public readonly consentAt: string,
    public readonly canReceivePromotions: boolean,
  ) {}
}

export class GuestTag {
  constructor(
    public readonly label: string,
    public readonly slug: string,
    public readonly tone: string,
  ) {}
}

export class GuestPreference {
  constructor(
    public readonly key: string,
    public readonly value: string,
    public readonly source: string,
  ) {}
}

export class GuestMessage {
  constructor(
    public readonly id: string,
    public readonly senderLabel: string,
    public readonly body: string,
    public readonly status: string,
    public readonly timestamp: string,
    public readonly fromStaff: boolean,
  ) {}
}

export class GuestMessageThread {
  constructor(
    public readonly messages: GuestMessage[],
    public readonly draft: string,
  ) {}

  latestMessage(): GuestMessage | null {
    return this.messages[0] || null;
  }
}

export class GuestStaySummary {
  constructor(
    public readonly id: string,
    public readonly reservationKey: string,
    public readonly listingName: string,
    public readonly dateRange: string,
    public readonly total: Money,
    public readonly status: string,
    public readonly reservationUrl: string,
  ) {}
}

export class GuestPaymentSummary {
  constructor(
    public readonly totalSpend: Money,
    public readonly paymentCount: number,
    public readonly lastPaymentAt: string,
  ) {}
}

export class GuestDepositSummary {
  constructor(
    public readonly activeHolds: number,
    public readonly releasedHolds: number,
    public readonly disputeCount: number,
  ) {}
}

export class GuestTimelineEvent {
  constructor(
    public readonly type: string,
    public readonly label: string,
    public readonly actor: string,
    public readonly timestamp: string,
    public readonly note: string,
  ) {}
}

export class Guest {
  constructor(
    public readonly id: string,
    public readonly key: string,
    public readonly identity: GuestIdentity,
    public readonly contact: GuestContact,
    public readonly profile: GuestProfile,
    public readonly status: GuestStatusState,
    public readonly segment: GuestSegmentState,
    public readonly marketing: GuestMarketingState,
    public readonly preferences: GuestPreference[],
    public readonly tags: GuestTag[],
    public readonly messages: GuestMessageThread,
    public readonly stays: GuestStaySummary[],
    public readonly payments: GuestPaymentSummary,
    public readonly deposits: GuestDepositSummary,
    public readonly timeline: GuestTimelineEvent[],
  ) {}

  displayName(): string {
    return this.identity.name || this.contact.email || 'Guest';
  }

  initials(): string {
    return this.identity.initials();
  }

  isVip(): boolean {
    return this.segment.value === 'vip';
  }

  isRepeatGuest(): boolean {
    return this.segment.value === 'repeat' || this.stays.length > 1;
  }

  isBlocked(): boolean {
    return this.segment.value === 'blacklisted' || this.status.value === 'blocked';
  }

  canMessage(): boolean {
    return !this.isBlocked() && this.contact.canMessage();
  }

  canReceivePromotions(): boolean {
    return !this.isBlocked() && this.marketing.canReceivePromotions;
  }
}
```

## Recommended files

```text
frontend/src/domain/guests.ts
frontend/src/application/GuestService.ts
frontend/src/infrastructure/GuestRepository.ts
frontend/src/ui/pages/OpsGuestsPage.tsx
frontend/src/ui/components/guests/GuestTable.tsx
frontend/src/ui/components/guests/GuestRow.tsx
frontend/src/ui/components/guests/GuestProfileCard.tsx
frontend/src/ui/components/guests/GuestMessagePanel.tsx
frontend/src/ui/components/guests/GuestStayPanel.tsx
frontend/src/ui/components/guests/GuestActivityPanel.tsx
```
