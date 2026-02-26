import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    host: true,
    allowedHosts: ['.ngrok-free.dev', '.ngrok.io', 'all', 'creasy-tommy-unfragmented.ngrok-free.dev'],
    cors: true,
    proxy: {
      '/api': {
        target: 'http://localhost:9005',
        changeOrigin: true,
      },
    },
  },
})
