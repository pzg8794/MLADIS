# Frontend Domain Code Stubs

These TypeScript stubs show the intended OOP shape for the Work Orders frontend.

## Domain objects

```ts
export type WorkOrderStatus = 'open' | 'in_progress' | 'pending' | 'completed' | 'overdue' | 'cancelled' | 'archived';
export type WorkOrderPriority = 'low' | 'medium' | 'high' | 'urgent';

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

export class WorkOrderProperty {
  constructor(
    public readonly id: number,
    public readonly name: string,
    public readonly slug: string,
    public readonly adminUrl: string,
  ) {}
}

export class WorkOrderReservation {
  constructor(
    public readonly id: number,
    public readonly requestKey: string,
    public readonly guestName: string,
    public readonly dateRange: string,
    public readonly adminUrl: string,
  ) {}
}

export class WorkOrderAssignee {
  constructor(
    public readonly name: string,
    public readonly role: string,
    public readonly avatarLabel: string,
  ) {}
}

export class WorkOrderDates {
  constructor(
    public readonly reportedAt: string,
    public readonly scheduledFor: string,
    public readonly startedAt: string,
    public readonly completedAt: string,
    public readonly dueAt: string,
    public readonly display: string,
  ) {}

  durationLabel(): string {
    if (!this.startedAt || !this.completedAt) return 'Time pending';
    const start = new Date(this.startedAt).getTime();
    const end = new Date(this.completedAt).getTime();
    const minutes = Math.max(Math.floor((end - start) / 60000), 0);
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const rest = minutes % 60;
    return rest ? `${hours}h ${rest}m` : `${hours}h`;
  }
}

export class WorkOrderPhoto {
  constructor(
    public readonly id: string,
    public readonly url: string,
    public readonly caption: string,
    public readonly isCover: boolean = false,
  ) {}
}

export class WorkOrderEvidence {
  constructor(public readonly photos: WorkOrderPhoto[]) {}

  get photoCount(): number {
    return this.photos.length;
  }

  coverPhoto(): WorkOrderPhoto | null {
    return this.photos.find((photo) => photo.isCover) || this.photos[0] || null;
  }
}

export class WorkOrderNotes {
  constructor(
    public readonly manual: string,
    public readonly internal: string,
    public readonly aiSummary: string,
    public readonly aiDiagnostics: string,
    public readonly aiRecommendation: string,
    public readonly activeMode: 'manual' | 'ai' = 'manual',
  ) {}

  effectiveText(): string {
    if (this.activeMode === 'ai' && this.aiSummary) return this.aiSummary;
    return this.manual || this.aiSummary || '';
  }
}

export class WorkOrderReportState {
  constructor(
    public readonly status: string,
    public readonly previewTitle: string,
    public readonly canGenerate: boolean,
    public readonly documentUrl: string,
    public readonly invoiceUrl: string,
  ) {}
}

export class WorkOrderTimelineEvent {
  constructor(
    public readonly type: string,
    public readonly label: string,
    public readonly actor: string,
    public readonly timestamp: string,
    public readonly note: string,
  ) {}
}

export class WorkOrder {
  constructor(
    public readonly id: string,
    public readonly number: string,
    public readonly title: string,
    public readonly summary: string,
    public readonly property: WorkOrderProperty,
    public readonly reservation: WorkOrderReservation | null,
    public readonly assignee: WorkOrderAssignee | null,
    public readonly priority: WorkOrderPriority,
    public readonly status: WorkOrderStatus,
    public readonly cost: Money,
    public readonly dates: WorkOrderDates,
    public readonly evidence: WorkOrderEvidence,
    public readonly notes: WorkOrderNotes,
    public readonly report: WorkOrderReportState,
    public readonly timeline: WorkOrderTimelineEvent[],
  ) {}

  isOverdue(): boolean {
    return this.status === 'overdue' || Boolean(this.dates.dueAt && new Date(this.dates.dueAt) < new Date() && this.status !== 'completed');
  }

  isReportReady(): boolean {
    return this.report.canGenerate;
  }

  displaySubtitle(): string {
    return this.reservation
      ? `${this.property.name} · ${this.reservation.requestKey}`
      : `${this.property.name} · Listing-level work`;
  }
}
```

## Layer boundaries

Recommended files:

```text
frontend/src/domain/work-orders.ts
frontend/src/application/WorkOrderService.ts
frontend/src/infrastructure/WorkOrderRepository.ts
frontend/src/ui/pages/OpsWorkOrdersPage.tsx
frontend/src/ui/components/work-orders/WorkOrderMetricCard.tsx
frontend/src/ui/components/work-orders/WorkOrderTable.tsx
frontend/src/ui/components/work-orders/WorkOrderRow.tsx
frontend/src/ui/components/work-orders/WorkOrderDetailPanel.tsx
frontend/src/ui/components/work-orders/WorkOrderTimeline.tsx
frontend/src/ui/components/work-orders/WorkOrderReportPreview.tsx
frontend/src/ui/components/work-orders/WorkOrderPhotoStrip.tsx
```
