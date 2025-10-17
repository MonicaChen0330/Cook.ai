import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from 'tailwindcss' 
import autoprefixer from 'autoprefixer' 

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001,
    host: true,
  },
  css: {
    postcss: {
      plugins: [
        tailwindcss(),
        autoprefixer(),
      ],
    },
  },
})
