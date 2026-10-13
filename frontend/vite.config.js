import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev only: proxy /api to the FastAPI backend. In production Caddy
// reverse-proxies /memedesk/api to the backend on the same host.
// base '/memedesk/' matches the Atlas tailnet deploy subpath.
export default defineConfig({
  base: '/memedesk/',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
