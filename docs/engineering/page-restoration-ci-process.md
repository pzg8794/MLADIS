# Page Restoration and CI Process

This process governs recovery and redesign work for the MLADIS public booking, payment, account, and operations pages.

## Scope

The current restoration target covers these user-facing surfaces:

- Secure payment modal in the public reservation flow.
- Property Rules review document.
- Damage Deposit Hold Terms review document.
- Payment confirmation page.
- Account reservations dashboard.
- Operations Admin command center.

## Non-Negotiable Workflow

1. Start every work session with `git status --short --branch`.
2. Work on a branch, never on an unknown dirty state.
3. Finish one page or one infrastructure step at a time.
4. Run the relevant validation before committing.
5. Commit the finished unit immediately.
6. Push the branch immediately after each commit.
7. Do not run destructive cleanup commands unless the user explicitly approves the exact command.

## Validation Gates

For frontend or shared UI work:

- `cd frontend && npm run build:django`

`cd frontend && npm run lint` is an audit gate until inherited lint debt is cleared. Do not introduce new lint debt in files touched by a page restoration.

For Django models, views, URLs, templates, or payment flow work:

- `cd airbnb_agent && python3 manage.py check`
- `cd airbnb_agent && python3 manage.py test bookings --verbosity 2`

## OOP and MVC Expectations

- Django models own durable payment, reservation, policy, and confirmation state.
- Django services create payment provider sessions and send confirmation messages.
- Django views coordinate requests and pass explicit context to templates.
- React page components compose reusable view objects and must not duplicate backend business rules.
- Shared visual patterns should be reusable components or scoped page objects, not copy-pasted one-off scripts.

## Documentation Rule

Every committed page restoration must update either this file, the page-specific implementation notes, or the relevant architecture document when it changes the model/controller/view boundary.