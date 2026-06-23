import React from 'react';
import ReactDOM from 'react-dom/client';
import { DashboardLayout } from './ui/components/DashboardLayout';
import { DashboardPage } from './ui/pages/DashboardPage';
import { PublicSitePage } from './ui/pages/PublicSitePage';
import { AdminPage } from './ui/pages/AdminPage';
import { OpsAgentPage } from './ui/pages/OpsAgentPage';
import { OpsBusinessPage } from './ui/pages/OpsBusinessPage';
import { OpsCalendarPage } from './ui/pages/OpsCalendarPage';
import { OpsCustomersPage } from './ui/pages/OpsCustomersPage';
import { OpsDepositsPage } from './ui/pages/OpsDepositsPage';
import { OpsGuestsPage } from './ui/pages/OpsGuestsPage';
import { OpsMaintenancePage } from './ui/pages/OpsMaintenancePage';
import { OpsPaymentsPage } from './ui/pages/OpsPaymentsPage';
import { OpsReportsPage } from './ui/pages/OpsReportsPage';
import { OpsReservationsPage } from './ui/pages/OpsReservationsPage';
import { OpsSettingsPage } from './ui/pages/OpsSettingsPage';
import { OpsStayPortfolioPage } from './ui/pages/OpsStayPortfolioPage';
import { OpsWorkboardPage } from './ui/pages/OpsWorkboardPage';
import './styles.css';

const pathname = window.location.pathname;
const isOpsDashboard = pathname.startsWith('/ops/dashboard');
const isOpsAdmin = pathname.startsWith('/ops/admin');
const isOpsReservations = pathname.startsWith('/ops/reservations');
const isOpsReports = pathname.startsWith('/ops/reports');
const isOpsGuests = pathname.startsWith('/ops/guests');
const isOpsCustomers = pathname.startsWith('/ops/customers');
const isOpsDeposits = pathname.startsWith('/ops/deposits');
const isOpsPayments = pathname.startsWith('/ops/payments');
const isOpsMaintenance = pathname.startsWith('/ops/maintenance');
const isOpsAgent = pathname.startsWith('/ops/agent');
const isOpsCalendar = pathname.startsWith('/ops/calendar');
const isOpsProperties = pathname.startsWith('/ops/properties');
const isOpsStays = pathname.startsWith('/ops/stays');
const isOpsSettings = pathname.startsWith('/ops/settings');
const isOpsWorkboard = pathname.startsWith('/ops/workboard');
const isBusinessProfile = pathname.startsWith('/business');
const isOps = isOpsDashboard || isOpsAdmin || isOpsReservations || isOpsReports || isOpsGuests || isOpsCustomers || isOpsDeposits || isOpsPayments || isOpsMaintenance || isOpsAgent || isOpsCalendar || isOpsProperties || isOpsStays || isOpsSettings || isOpsWorkboard || isBusinessProfile;

function renderOpsPage() {
  if (isOpsAdmin) return <AdminPage />;
  if (isOpsReservations) return <OpsReservationsPage />;
  if (isOpsReports) return <OpsReportsPage />;
  if (isOpsGuests) return <OpsGuestsPage />;
  if (isOpsCustomers) return <OpsCustomersPage />;
  if (isOpsPayments) return <OpsPaymentsPage />;
  if (isOpsDeposits) return <OpsDepositsPage />;
  if (isOpsMaintenance) return <OpsMaintenancePage />;
  if (isOpsAgent) return <OpsAgentPage />;
  if (isOpsCalendar) return <OpsCalendarPage />;
  if (isOpsProperties || isOpsStays) return <OpsStayPortfolioPage />;
  if (isOpsSettings) return <OpsSettingsPage />;
  if (isOpsWorkboard) return <OpsWorkboardPage />;
  if (isBusinessProfile) return <OpsBusinessPage />;
  return <DashboardPage />;
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    {isOps ? (
      <DashboardLayout>
        {renderOpsPage()}
      </DashboardLayout>
    ) : (
      <PublicSitePage />
    )}
  </React.StrictMode>,
);
