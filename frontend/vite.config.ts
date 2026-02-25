import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,  // Allow external access
    allowedHosts: [
      'localhost',
      '*.ngrok-free.dev',
      '*.ngrok.io',
      'creasy-tommy-unfragmented.ngrok-free.dev',
      'all'  // Allow all hosts (for development)
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:9005',
        changeOrigin: true,
      },
    },
    cors: true,
  },
})
