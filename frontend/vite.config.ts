import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Flask (ui/app.py) runs on :5000. Only the dev server needs this —
    // production is same-origin because Flask serves frontend/dist directly.
    proxy: {
      '/start': 'http://localhost:5000',
      '/stop': 'http://localhost:5000',
      '/status': 'http://localhost:5000',
      '/api': 'http://localhost:5000',
      '/review': 'http://localhost:5000',
    },
  },
})
