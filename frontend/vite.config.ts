import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Docker Desktop на Windows не пробрасывает нативные fs-события bind-mount
  // в контейнер — без polling Vite HMR не видит правки исходников на хосте.
  server: {
    watch: {
      usePolling: true,
    },
  },
})
