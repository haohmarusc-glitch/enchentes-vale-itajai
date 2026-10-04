import { readFileSync } from 'node:fs'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Versão do build: a do package.json + o commit, quando o build sabe qual é
// (Cloudflare Pages: CF_PAGES_COMMIT_SHA; GitHub Actions: GITHUB_SHA). É igual
// para todo mundo que abre o site — vai na contagem agregada do chat
// (docs/TELEMETRIA-CHAT.md) e não identifica ninguém.
const pacote = JSON.parse(readFileSync(new URL('./package.json', import.meta.url), 'utf8')) as { version: string }
const commit = (process.env.CF_PAGES_COMMIT_SHA || process.env.GITHUB_SHA || '').slice(0, 7)
const versaoSite = commit ? `${pacote.version}+${commit}` : pacote.version

// Base relativa: funciona tanto em GitHub Pages (subdiretório) quanto na Vercel.
export default defineConfig({
  base: './',
  plugins: [react()],
  define: {
    __VERSAO_SITE__: JSON.stringify(versaoSite),
  },
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
