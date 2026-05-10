# MLADIS Modern Dashboard

New isolated frontend for the future MLADIS operations dashboard. It does not replace the live Django website yet.

## Goal

Build a modern Soft UI inspired dashboard one section at a time while Django remains the source of truth for the database, booking logic, deposits, email, admin, and APIs.

## OOP-oriented structure

- `src/domain/models.ts` defines domain classes.
- `src/infrastructure/HttpClient.ts` owns HTTP behavior.
- `src/infrastructure/DashboardRepository.ts` provides API and mock repositories.
- `src/application/DashboardService.ts` contains use cases.
- `src/application/DashboardFactory.ts` chooses mock or API data.
- `src/ui/` contains React presentation components.

## Local setup

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Mock vs API data

Default mode uses mock data:

```env
VITE_USE_MOCK_DATA=true
```

When Django API endpoints are ready:

```env
VITE_USE_MOCK_DATA=false
VITE_API_BASE_URL=
```

The first endpoint expected by the frontend is `GET /api/ops/summary/`.

That endpoint should return metrics, reservations, deposits, agent question summaries, calendar alerts, and a generated timestamp. See `src/infrastructure/DashboardRepository.ts` for the exact TypeScript API interfaces.

## Build

```bash
npm run build
npm run preview
```

## Recommended migration order

1. Ops dashboard
2. Reports
3. Reservations
4. Business calendar
5. Customers and Airbnb guests
6. Agent FAQ and conversations
7. Public booking flow only after the dashboard is stable

## Deployment options later

Do not deploy over the live site yet. Once stable, choose one:

- serve from Django under `/ops-new/`,
- serve from a subdomain like `dashboard.mladis.com`,
- or build and copy static assets into Django.
