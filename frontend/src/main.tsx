import React from 'react';
import ReactDOM from 'react-dom/client';
import { DashboardLayout } from './ui/components/DashboardLayout';
import { DashboardPage } from './ui/pages/DashboardPage';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <DashboardLayout>
      <DashboardPage />
    </DashboardLayout>
  </React.StrictMode>,
);
