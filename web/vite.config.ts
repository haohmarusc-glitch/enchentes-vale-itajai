import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Base relativa: funciona tanto em GitHub Pages (subdiretório) quanto na Vercel.
export default defineConfig({
  base: './',
  plugins: [react()],
  resolve: {
    alias: {
      // Os JSONs de data/ são a fonte de verdade; o site lê deles diretamente.
      '@dados': fileURLToPath(new URL('../data', import.meta.url)),
    },
  },
  server: {
    fs: {
      // Permite importar ../data de fora da raiz do Vite.
      allow: ['..'],
    },
  },
})
