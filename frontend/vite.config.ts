import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const djangoTarget = process.env.MLADIS_DJANGO_URL ?? 'http://127.0.0.1:8000';
const djangoProxy = {
  target: djangoTarget,
  changeOrigin: false,
  xfwd: true,
};
const allowedHosts = process.env.MLADIS_VITE_ALLOWED_HOSTS
  ? process.env.MLADIS_VITE_ALLOWED_HOSTS.split(',').map((host) => host.trim()).filter(Boolean)
  : true;

export default defineConfig(({ command }) => ({
  base: command === 'serve' ? '/' : '/static/frontend/modern-dashboard/',
  plugins: [react()],
  build: {
    outDir: '../airbnb_agent/bookings/static/frontend/modern-dashboard',
    emptyOutDir: true,
    manifest: false,
    rollupOptions: {
      output: {
        entryFileNames: 'assets/app.js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.names?.some((name) => name.endsWith('.css'))) {
            return 'assets/app.css';
          }
          return 'assets/[name][extname]';
        },
      },
    },
  },
  server: {
    allowedHosts,
    proxy: {
      '/api': djangoProxy,
      '/accounts': djangoProxy,
      '/admin': djangoProxy,
      '/i18n': djangoProxy,
      '/media': djangoProxy,
      '/oauth': djangoProxy,
      '/ops': djangoProxy,
      '/static': djangoProxy,
    },
  },
}));
