# Frontend Domain Code Stubs

These TypeScript stubs show the intended OOP shape for the Reservations frontend.

## Domain objects

```ts
export type ReservationStatusValue = 'new' | 'reviewing' | 'quoted' | 'confirmed' | 'hold' | 'completed' | 'canceled' | 'declined';
export type ReservationRiskLevel = 'low' | 'medium' | 'high';

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

export class ReservationGuest {
  constructor(
    public readonly name: string,
    public readonly email: string,
    public readonly phone: string,
    public readonly country: string,
    public readonly profileAdminUrl: string,
    public readonly threadUrl: string,
  ) {}

  get initials(): string {
    const parts = this.name.trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return 'G';
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
}

export class ReservationStay {
  constructor(
    public readonly id: number,
    public readonly name: string,
    public readonly unitLabel: string,
    public readonly listingUrl: string,
    public readonly adminUrl: string,
  ) {}
}

export class ReservationDates {
  constructor(
    public readonly checkIn: string,
    public readonly checkOut: string,
    public readonly nights: number,
    public readonly displayRange: string,
  ) {}
}

export class ReservationStatusState {
  constructor(
    public readonly value: ReservationStatusValue,
    public readonly label: string,
    public readonly tone: string,
  ) {}
}

export class ReservationRiskState {
  constructor(
    public readonly level: ReservationRiskLevel,
    public readonly label: string,
    public readonly signals: string[],
  ) {}
}

export class ReservationPaymentStep {
  constructor(
    public readonly label: string,
    public readonly amount: Money,
    public readonly status: string,
    public readonly dueLabel: string,
  ) {}
}

export class ReservationPaymentPlan {
  constructor(
    public readonly total: Money,
    public readonly stayPayment: Money,
    public readonly deposit: Money,
    public readonly status: string,
    public readonly steps: ReservationPaymentStep[],
  ) {}

  isPaid(): boolean {
    return this.status === 'paid';
  }
}

export class ReservationDepositHold {
  constructor(
    public readonly amount: Money,
    public readonly status: string,
    public readonly label: string,
    public readonly expiresAt: string,
  ) {}

  canApprove(): boolean {
    return this.status === 'pending' || this.status === 'authorized';
  }

  canRelease(): boolean {
    return this.status === 'pending' || this.status === 'authorized';
  }
}

export class ReservationDocumentState {
  constructor(
    public readonly propertyRulesAccepted: boolean,
    public readonly damageTermsAccepted: boolean,
    public readonly propertyRulesVersion: string,
    public readonly damageTermsVersion: string,
  ) {}

  allAccepted(): boolean {
    return this.propertyRulesAccepted && this.damageTermsAccepted;
  }
}

export class ReservationMessage {
  constructor(
    public readonly id: string,
    public readonly senderLabel: string,
    public readonly body: string,
    public readonly status: string,
    public readonly timestamp: string,
    public readonly fromStaff: boolean,
  ) {}
}

export class ReservationMessageThread {
  constructor(
    public readonly messages: ReservationMessage[],
    public readonly suggestedDraft: string,
  ) {}

  latestMessage(): ReservationMessage | null {
    return this.messages[0] || null;
  }
}

export class ReservationTimelineEvent {
  constructor(
    public readonly type: string,
    public readonly label: string,
    public readonly actor: string,
    public readonly timestamp: string,
    public readonly note: string,
  ) {}
}

export class ReservationAgentAssessment {
  constructor(
    public readonly riskLevel: ReservationRiskLevel,
    public readonly suggestedReply: string,
    public readonly missingInformation: string[],
    public readonly recommendedActions: string[],
    public readonly positiveSignals: string[],
  ) {}
}

export class Reservation {
  constructor(
    public readonly id: string,
    public readonly key: string,
    public readonly requestKey: string,
    public readonly guest: ReservationGuest,
    public readonly stay: ReservationStay,
    public readonly dates: ReservationDates,
    public readonly status: ReservationStatusState,
    public readonly risk: ReservationRiskState,
    public readonly paymentPlan: ReservationPaymentPlan,
    public readonly depositHold: ReservationDepositHold,
    public readonly documents: ReservationDocumentState,
    public readonly messages: ReservationMessageThread,
    public readonly timeline: ReservationTimelineEvent[],
    public readonly agent: ReservationAgentAssessment,
  ) {}

  displayTitle(): string {
    return this.guest.name;
  }

  displaySubtitle(): string {
    return `${this.stay.name} · ${this.dates.displayRange}`;
  }

  canSendCheckInInstructions(): boolean {
    return Boolean(this.guest.email && this.status.value !== 'canceled');
  }

  canApproveDeposit(): boolean {
    return this.depositHold.canApprove();
  }

  canGenerateInvoice(): boolean {
    return this.status.value !== 'canceled' && this.paymentPlan.total.cents > 0;
  }
}
```

## Recommended files

```text
frontend/src/domain/reservations.ts
frontend/src/application/ReservationService.ts
frontend/src/infrastructure/ReservationRepository.ts
frontend/src/ui/pages/OpsReservationsPage.tsx
frontend/src/ui/components/reservations/ReservationTable.tsx
frontend/src/ui/components/reservations/ReservationRow.tsx
frontend/src/ui/components/reservations/ReservationDetailPanel.tsx
frontend/src/ui/components/reservations/ReservationGuestCard.tsx
frontend/src/ui/components/reservations/ReservationMessagePanel.tsx
frontend/src/ui/components/reservations/ReservationDepositPanel.tsx
frontend/src/ui/components/reservations/FairAgentPanel.tsx
```
