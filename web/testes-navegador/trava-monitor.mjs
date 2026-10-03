#!/usr/bin/env node
/**
 * TRAVA DO MONITOR — a geometria do mapa não pode mudar por tabela.
 *
 * POR QUE EXISTE (03/10/2026). A versão 2 do site troca a casca (faixa do 199,
 * cabeçalho, barra de navegação embaixo) das telas que NÃO são o Monitor. O
 * Monitor depende dessa casca sem saber: o mapa (`.palco`) mede
 * `calc(100vh - 8.5rem)` no desktop, e `8.5rem` é a soma, escrita à mão, da
 * faixa de emergência com o cabeçalho. Qualquer centímetro a mais em cima, ou
 * uma barra fixa embaixo, encolhe o mapa ou cobre os controles — e nenhum
 * teste de lógica vê isso. Decisão do Jefferson (D2, opção ③): nas rotas do
 * Monitor a casca continua a antiga, e esta trava prova que continua.
 *
 * O QUE REPROVA, em 360×740, 390×844, 1280×800 e 1366×768, nas rotas
 * `/monitor`, `/monitor/blumenau` e `/municipal/ascurra`:
 *   1. o retângulo do mapa diferente do `baseline-monitor.json` (±1 px);
 *   2. elemento `position: fixed` fora do mapa cruzando o retângulo dele;
 *   3. o ponto da base visível do mapa pertencendo a outro elemento;
 *   4. a barra de navegação nova (`nav[aria-label="Principal"]`) nessas rotas.
 * E, numa rota que não é do Monitor: 5. a barra nova com `z-index` acima de
 * 1000 (o modo ampliado do Monitor usa 10000 e precisa ficar por cima).
 *
 * Uso:
 *     npm run build && node testes-navegador/trava-monitor.mjs
 *     node testes-navegador/trava-monitor.mjs --gravar   # refaz o baseline
 *
 * Refazer o baseline é decisão, não conserto: só depois de uma mudança no
 * Monitor autorizada pelo Jefferson.
 */
import { existsSync, readFileSync, readdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { chromium } from 'playwright'
import { preview } from 'vite'

const BASELINE = new URL('./baseline-monitor.json', import.meta.url)
const GRAVAR = process.argv.includes('--gravar')
const TELAS = [[360, 740], [390, 844], [1280, 800], [1366, 768]]
const ROTAS = ['/monitor', '/monitor/blumenau', '/municipal/ascurra']
const TOLERANCIA = 1

function acharNavegador() {
  const padrao = chromium.executablePath()
  if (existsSync(padrao)) return undefined
  const raiz = process.env.PLAYWRIGHT_BROWSERS_PATH
  if (raiz && existsSync(raiz)) {
    for (const pasta of readdirSync(raiz).filter((d) => d.startsWith('chromium-'))) {
      const bin = join(raiz, pasta, 'chrome-linux', 'chrome')
      if (existsSync(bin)) return bin
    }
  }
  throw new Error('Chromium não encontrado. Em CI: npx playwright install --with-deps chromium')
}

const servidor = await preview({ preview: { port: 4321, strictPort: true } })
const base = servidor.resolvedUrls.local[0].replace(/\/$/, '')
const navegador = await chromium.launch({ executablePath: acharNavegador(), args: ['--no-sandbox'] })
const falhas = []
const medidas = {}

for (const [largura, altura] of TELAS) {
  const ctx = await navegador.newContext({ viewport: { width: largura, height: altura }, locale: 'pt-BR', serviceWorkers: 'block' })
  // Rede externa cortada: a geometria não pode depender do dado do dia.
  await ctx.route('**/*', (r) => (r.request().url().startsWith(base) ? r.continue() : r.abort()))
  for (const rota of ROTAS) {
    const chave = `${largura}x${altura} ${rota}`
    const page = await ctx.newPage()
    await page.goto(`${base}/#${rota}`, { waitUntil: 'load' })
    await page.waitForTimeout(1500)
    const r = await page.evaluate(() => {
      const palco = document.querySelector('[class*="_palco_"]')
      if (!palco) return null
      const k = palco.getBoundingClientRect()
      const ret = { x: Math.round(k.left), y: Math.round(k.top + scrollY), largura: Math.round(k.width), altura: Math.round(k.height) }
      const cruza = (a, c) => a.left < c.right && c.left < a.right && a.top < c.bottom && c.top < a.bottom
      const fixosPorCima = []
      for (const el of document.querySelectorAll('body *')) {
        if (palco.contains(el) || el.contains(palco)) continue
        if (getComputedStyle(el).position !== 'fixed') continue
        const e = el.getBoundingClientRect()
        if (e.width && e.height && cruza(e, k)) fixosPorCima.push((el.getAttribute('aria-label') || el.className || el.tagName).toString().slice(0, 40))
      }
      const yBase = Math.min(k.bottom, innerHeight) - 4
      const alvo = document.elementFromPoint(k.left + k.width / 2, yBase)
      return {
        ret,
        fixosPorCima,
        baseDoMapa: !!alvo && palco.contains(alvo),
        barraNova: !!document.querySelector('nav[aria-label="Principal"]'),
      }
    })
    await page.close()
    if (!r) { falhas.push(`${chave}: mapa (.palco) não encontrado`); continue }
    medidas[chave] = r.ret
    if (r.fixosPorCima.length) falhas.push(`${chave}: elemento fixo sobre o mapa — ${r.fixosPorCima.join(', ')}`)
    if (!r.baseDoMapa) falhas.push(`${chave}: a base visível do mapa é de outro elemento`)
    if (r.barraNova) falhas.push(`${chave}: a barra de navegação nova apareceu no Monitor`)
  }
  await ctx.close()
}

// A barra nova, fora do Monitor, fica abaixo do modo ampliado (z-index 10000).
{
  const ctx = await navegador.newContext({ viewport: { width: 390, height: 844 }, serviceWorkers: 'block' })
  await ctx.route('**/*', (r) => (r.request().url().startsWith(base) ? r.continue() : r.abort()))
  const page = await ctx.newPage()
  await page.goto(`${base}/#/acu`, { waitUntil: 'load' })
  await page.waitForTimeout(1000)
  const z = await page.evaluate(() => {
    const nav = document.querySelector('nav[aria-label="Principal"]')
    return nav ? Number.parseInt(getComputedStyle(nav).zIndex, 10) || 0 : null
  })
  if (z !== null && z > 1000) falhas.push(`barra de navegação com z-index ${z} (máximo 1000)`)
  await ctx.close()
}

if (GRAVAR) {
  writeFileSync(BASELINE, JSON.stringify(medidas, null, 2) + '\n')
  console.log(`Baseline gravado: ${Object.keys(medidas).length} medidas.`)
} else {
  const esperado = JSON.parse(readFileSync(BASELINE, 'utf8'))
  for (const [chave, ret] of Object.entries(esperado)) {
    const agora = medidas[chave]
    if (!agora) continue
    const difere = ['x', 'y', 'largura', 'altura'].filter((k) => Math.abs(agora[k] - ret[k]) > TOLERANCIA)
    if (difere.length) falhas.push(`${chave}: mapa mudou (${difere.map((k) => `${k} ${ret[k]}→${agora[k]}`).join(', ')})`)
    else console.log(`  ✓ ${chave}`)
  }
}

await navegador.close()
await servidor.close()
console.log(falhas.length ? `\n${falhas.length} falha(s):\n - ${falhas.join('\n - ')}` : '\nMonitor intacto.')
process.exit(falhas.length ? 1 : 0)
