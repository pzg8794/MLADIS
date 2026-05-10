import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base: '/static/frontend/modern-dashboard/',
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
    proxy: {
      '/api': {
        target: process.env.MLADIS_DJANGO_URL ?? 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
