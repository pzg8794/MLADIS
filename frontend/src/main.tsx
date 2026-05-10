import React from 'react';
import ReactDOM from 'react-dom/client';
import { DashboardLayout } from './ui/components/DashboardLayout';
import { DashboardPage } from './ui/pages/DashboardPage';
import { PublicSitePage } from './ui/pages/PublicSitePage';
import './styles.css';

const isOpsDashboard = window.location.pathname.startsWith('/ops/dashboard');

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    {isOpsDashboard ? (
      <DashboardLayout>
        <DashboardPage />
      </DashboardLayout>
    ) : (
      <PublicSitePage />
    )}
  </React.StrictMode>,
);
