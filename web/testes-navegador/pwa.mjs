#!/usr/bin/env node
/**
 * MODO APLICATIVO (decisão D5, 03/10/2026) num navegador de verdade.
 *
 * O que este teste garante:
 *  1. o manifesto existe e é válido, com ícones e `start_url`;
 *  2. o service worker instala e passa a controlar a página;
 *  3. SEM REDE, o site abre com a cópia guardada: o 199 continua na tela, o
 *     aviso "Sem conexão" aparece, e o nível guardado vem com a hora da
 *     medição — que o site já marca como velho quando é velho;
 *  4. o Monitor também abre sem rede, sem os avisos da casca nova (D2);
 *  5. o interruptor: `pwa.json` com `"ativo": false` desliga o service worker
 *     e apaga o que ele guardou.
 *
 * Os outros testes de navegador bloqueiam o service worker (`serviceWorkers:
 * 'block'`), para o route() deles alcançar a rede da página; este aqui é o
 * único que o deixa rodar.
 *
 * Uso: npm run build && node testes-navegador/pwa.mjs
 */
import { existsSync, readdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { chromium } from 'playwright'
import { preview } from 'vite'

const RAW = 'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/'
const PWA_JSON = new URL('../dist/pwa.json', import.meta.url)

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

const falhas = []
const ok = (m) => console.log(`  ✓ ${m}`)
const falhou = (m) => { falhas.push(m); console.log(`  ✗ ${m}`) }

// Uma leitura de Blumenau de 20 min atrás, no horário de Brasília (sem fuso).
const agora = new Date()
const medido = new Date(agora.getTime() - 3 * 3600_000 - 20 * 60_000).toISOString().slice(0, 19)
const ULTIMO = JSON.stringify({
  coletado_em: agora.toISOString(),
  leituras: [{ cidade: 'blumenau', rio: 'itajai-acu', estacao: 'AlertaBlu', nivel_m: 4.37, medido_em: medido }],
  chuva: [],
  chuva_ok: true,
})

const original = readFileSync(PWA_JSON, 'utf8')
const servidor = await preview({ preview: { port: 4322, strictPort: true } })
const base = servidor.resolvedUrls.local[0].replace(/\/$/, '')
const navegador = await chromium.launch({ executablePath: acharNavegador(), args: ['--no-sandbox'] })

try {
  const ctx = await navegador.newContext({ viewport: { width: 390, height: 844 }, locale: 'pt-BR', serviceWorkers: 'allow' })
  await ctx.addInitScript(() => {
    try {
      localStorage.setItem('enchentes:aviso-lido', '2026-10-03')
      localStorage.setItem('enchentes:cidades', JSON.stringify([{ id: 'blumenau', rio: 'acu' }]))
    } catch {}
  })
  // O nível ao vivo vem da fixture; o resto de fora é cortado.
  await ctx.route('**/*', (r) => {
    const url = r.request().url()
    if (url.startsWith(base)) return r.continue()
    if (url === `${RAW}ultimo.json`) {
      return r.fulfill({ status: 200, contentType: 'text/plain; charset=utf-8', headers: { 'access-control-allow-origin': '*' }, body: ULTIMO })
    }
    return r.abort()
  })
  const page = await ctx.newPage()

  console.log('\nmanifesto e service worker')
  await page.goto(`${base}/#/`, { waitUntil: 'load' })
  const manifesto = await page.evaluate(async () => {
    const link = document.querySelector('link[rel="manifest"]')
    if (!link) return null
    const r = await fetch(link.href, { credentials: 'include' })
    return { crossorigin: link.getAttribute('crossorigin'), json: await r.json() }
  })
  manifesto?.json?.start_url && manifesto.json.icons?.length >= 2 && manifesto.json.display === 'standalone'
    ? ok('manifesto válido, com ícones e abrindo como aplicativo')
    : falhou('manifesto ausente ou incompleto')
  manifesto?.crossorigin === 'use-credentials'
    ? ok('manifesto pedido COM o cookie (Cloudflare Access)')
    : falhou('o link do manifesto perdeu crossorigin="use-credentials"')

  await page.evaluate(() => navigator.serviceWorker.ready)
  // Recarrega já sob o service worker: a página e o nível passam por ele e ficam guardados.
  await page.reload({ waitUntil: 'load' })
  await page.waitForFunction(() => Boolean(navigator.serviceWorker.controller), null, { timeout: 15_000 })
  ok('o service worker controla a página')
  await page.getByText('4,37', { exact: true }).first().waitFor({ timeout: 10_000 })
  await page.waitForTimeout(1000)
  const guardado = await page.evaluate(async () => {
    const nomes = await caches.keys()
    const itens = []
    for (const n of nomes) itens.push(...(await (await caches.open(n)).keys()).map((k) => k.url))
    return itens
  })
  guardado.some((u) => u.endsWith('/')) ? ok('a página ficou guardada no aparelho') : falhou('a página não foi guardada')
  guardado.some((u) => u.includes('/tempo-real/ultimo.json'))
    ? ok('o último nível ficou guardado no aparelho')
    : falhou(`o nível não foi guardado (guardados: ${guardado.length})`)

  console.log('\nsem rede')
  await ctx.setOffline(true)
  await page.reload({ waitUntil: 'load' }).catch(() => {})
  await page.waitForTimeout(2500)
  const texto = await page.locator('body').innerText()
  texto.includes('199') ? ok('o 199 continua na tela') : falhou('sem rede, o 199 sumiu')
  texto.includes('Sem conexão') ? ok('aparece o aviso "Sem conexão"') : falhou('sem rede, nada avisou que não há conexão')
  texto.includes('4,37') && /medido há \d+ min/.test(texto)
    ? ok('o nível guardado aparece com a hora da medição')
    : falhou('sem rede, o nível guardado não apareceu com a idade')

  await page.goto(`${base}/#/monitor`, { waitUntil: 'load' }).catch(() => {})
  await page.waitForTimeout(1500)
  const monitor = await page.locator('body').innerText()
  monitor.includes('Emergência: ligue 199') && !monitor.includes('Sem conexão')
    ? ok('o Monitor abre sem rede, com a casca antiga e sem os avisos novos')
    : falhou('sem rede, o Monitor não abriu como antes')
  await ctx.setOffline(false)

  console.log('\nsessão do Cloudflare Access vencida')
  // O Access responde à página com um desvio para o login dele. Isso não pode
  // virar "o site" guardado: sem rede depois, tem de abrir o site de verdade.
  const LOGIN = 'https://equipe.cloudflareaccess.com/cdn-cgi/access/login'
  // O pedido da página chega pelo service worker (tipo "fetch", não "document"):
  // desvia-se pela URL, que só a página usa.
  const desviar = (r) => r.fulfill({ status: 302, headers: { location: LOGIN } })
  await ctx.route(`${base}/`, desviar)
  await ctx.route(`${LOGIN}*`, (r) => r.fulfill({ status: 200, contentType: 'text/html', body: '<html><body>Entrar com e-mail</body></html>' }))
  await page.goto(`${base}/`, { waitUntil: 'load' }).catch(() => {})
  ;(await page.locator('body').innerText()).includes('Entrar com e-mail')
    ? ok('com a sessão vencida, a pessoa vê o login (o desvio passa)')
    : falhou('o desvio para o login não chegou à tela')
  // O que ficou guardado como "a página"? Lido de dentro do site, numa aba
  // aberta num arquivo qualquer dele (não na página, que ainda desviaria).
  const aba = await ctx.newPage()
  await aba.goto(`${base}/favicon.svg`, { waitUntil: 'load' })
  const copia = await aba.evaluate(async (chave) => {
    const r = await caches.match(chave)
    return r ? await r.text() : ''
  }, `${base}/`)
  await aba.close()
  await ctx.unroute(`${base}/`, desviar)
  !copia.includes('Entrar com e-mail') && copia.includes('antes-de-carregar')
    ? ok('o login não foi guardado: a cópia da página continua sendo o site')
    : falhou('o login do Access ficou guardado no lugar do site')

  console.log('\ninterruptor')
  writeFileSync(PWA_JSON, JSON.stringify({ ativo: false }))
  // Recarregar, não só trocar o `#`: é o pedido da página que faz o service
  // worker conferir o interruptor.
  await page.goto(`${base}/#/`, { waitUntil: 'load' })
  await page.reload({ waitUntil: 'load' })
  await page
    .waitForFunction(async () => (await navigator.serviceWorker.getRegistrations()).length === 0, null, { timeout: 15_000, polling: 500 })
    .catch(() => {})
  const depois = await page.evaluate(async () => ({
    registros: (await navigator.serviceWorker.getRegistrations()).length,
    caches: (await caches.keys()).filter((n) => n.startsWith('enchentes-')).length,
  }))
  depois.registros === 0 && depois.caches === 0
    ? ok('com "ativo": false, o service worker sai e apaga o que guardou')
    : falhou(`o interruptor não desligou (registros ${depois.registros}, caches ${depois.caches})`)
  await ctx.close()
} finally {
  writeFileSync(PWA_JSON, original)
  await navegador.close()
  await servidor.close()
}

console.log(falhas.length ? `\n${falhas.length} falha(s):\n - ${falhas.join('\n - ')}` : '\nModo aplicativo em ordem.')
process.exit(falhas.length ? 1 : 0)
