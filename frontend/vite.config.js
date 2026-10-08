import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev only: proxy /api to the FastAPI backend. In production Caddy
// reverse-proxies /api to the backend on the same host.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
