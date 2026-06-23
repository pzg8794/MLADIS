import { Guest, GuestWorkspace, GuestWorkspaceFilters } from '../domain/guests';
import type { GuestMessageResponse, GuestRepository } from '../infrastructure/GuestRepository';

export class GuestService {
  constructor(private readonly repository: GuestRepository) {}

  async loadWorkspace(filters: GuestWorkspaceFilters = {}): Promise<GuestWorkspace> {
    return this.repository.loadWorkspace(filters);
  }

  filterGuests(workspace: GuestWorkspace, filters: GuestWorkspaceFilters): Guest[] {
    return workspace.filteredGuests(filters);
  }

  selectGuest(workspace: GuestWorkspace, guestId?: string): Guest | null {
    return workspace.selectedGuest(guestId);
  }

  async sendMessage(guest: Guest, body: string, confirmed: boolean): Promise<GuestMessageResponse> {
    if (!guest.canMessage) {
      throw new Error('This guest cannot be messaged until contact details are available and the profile is not blocked.');
    }
    return this.repository.sendMessage(guest.id, body, confirmed);
  }
}
