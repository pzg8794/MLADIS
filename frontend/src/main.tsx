import React from 'react';
import ReactDOM from 'react-dom/client';
import { DashboardLayout } from './ui/components/DashboardLayout';
import { DashboardPage } from './ui/pages/DashboardPage';
import { PublicSitePage } from './ui/pages/PublicSitePage';
import { AdminPage } from './ui/pages/AdminPage';
import './styles.css';

const pathname = window.location.pathname;
const isOpsDashboard = pathname.startsWith('/ops/dashboard');
const isOpsAdmin = pathname.startsWith('/ops/admin');

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    {isOpsDashboard || isOpsAdmin ? (
      <DashboardLayout>
        {isOpsAdmin ? <AdminPage /> : <DashboardPage />}
      </DashboardLayout>
    ) : (
      <PublicSitePage />
    )}
  </React.StrictMode>,
);
