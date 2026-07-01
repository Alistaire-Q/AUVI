import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Backend URL: gunakan env var untuk Docker, fallback ke localhost untuk dev lokal
const backendUrl = process.env.VITE_BACKEND_URL || 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/storage': {
        target: backendUrl,
        changeOrigin: true,
      },
    },
  },
});
