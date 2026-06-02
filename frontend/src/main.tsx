import React from 'react';
import ReactDOM from 'react-dom/client';
import { DashboardLayout } from './ui/components/DashboardLayout';
import { DashboardPage } from './ui/pages/DashboardPage';
import { PublicSitePage } from './ui/pages/PublicSitePage';
import { AdminPage } from './ui/pages/AdminPage';
import { OpsAgentPage } from './ui/pages/OpsAgentPage';
import { OpsCustomersPage } from './ui/pages/OpsCustomersPage';
import { OpsDepositsPage } from './ui/pages/OpsDepositsPage';
import { OpsReportsPage } from './ui/pages/OpsReportsPage';
import { OpsReservationsPage } from './ui/pages/OpsReservationsPage';
import './styles.css';

const pathname = window.location.pathname;
const isOpsDashboard = pathname.startsWith('/ops/dashboard');
const isOpsAdmin = pathname.startsWith('/ops/admin');
const isOpsReservations = pathname.startsWith('/ops/reservations');
const isOpsReports = pathname.startsWith('/ops/reports');
const isOpsCustomers = pathname.startsWith('/ops/customers');
const isOpsDeposits = pathname.startsWith('/ops/deposits');
const isOpsAgent = pathname.startsWith('/ops/agent');
const isOps = isOpsDashboard || isOpsAdmin || isOpsReservations || isOpsReports || isOpsCustomers || isOpsDeposits || isOpsAgent;

function renderOpsPage() {
  if (isOpsAdmin) return <AdminPage />;
  if (isOpsReservations) return <OpsReservationsPage />;
  if (isOpsReports) return <OpsReportsPage />;
  if (isOpsCustomers) return <OpsCustomersPage />;
  if (isOpsDeposits) return <OpsDepositsPage />;
  if (isOpsAgent) return <OpsAgentPage />;
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
