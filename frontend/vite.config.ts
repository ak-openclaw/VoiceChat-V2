import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    allowedHosts: ['.ngrok-free.dev', '.ngrok.io', 'all'],
    proxy: {
      '/api': {
        target: 'http://localhost:9004',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
