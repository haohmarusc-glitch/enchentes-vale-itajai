#!/usr/bin/env node
/**
 * Varredura: TODAS as rotas e TODOS os controles, num navegador de verdade.
 *
 * POR QUE EXISTE (14/09/2026). A fumaça (`fumaca.mjs`) prova que o site monta;
 * a auditoria (`auditoria.mjs`) trava regressões pontuais. Faltava o passeio
 * que o Jefferson pediu — "faça um teste em todas as funções do site" —,
 * repetível: descobrir as rotas a partir do início (seguindo os links, como
 * um morador), abrir cada uma no celular e no desktop, e mexer em cada
 * controle do Monitor e das telas de rio/cidade/Itajaí.
 *
 * O QUE ESTE ARQUIVO GARANTE, em cada rota e tamanho:
 *   1. nenhum `pageerror` e nenhum erro de console que não seja de rede
 *      cortada (a rede externa é bloqueada de propósito, como na fumaça);
 *   2. a página não rola na horizontal (celular de 390 px);
 *   3. o telefone 199 continua na tela.
 * E, no Monitor: zoom, menu de cidades e painel, reprodução de 24 h (quando
 * há série), fundos do mapa, camadas de cheia, toque e arrasto no mapa. Nas
 * telas: cartões de cidade, busca "minha rua", busca de rua de Itajaí,
 * detalhes de Ascurra, rota inexistente voltando ao início.
 *
 * DADO AO VIVO (opcional). Com DADOS apontando para uma pasta com os JSONs do
 * branch `tempo-real` (ver `base.mjs`), a varredura passa a exercitar mapa
 * colorido, painel com nível e reprodução de 24 h. Com SAIDA, grava uma
 * captura por rota e por interação nessa pasta.
 *
 * Uso:
 *     npm run build && npm run varredura
 *     DADOS=/tmp/tr SAIDA=/tmp/capturas npm run varredura
 */
import { existsSync, mkdirSync, readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { chromium } from 'playwright'
import { preview } from 'vite'

const RAW = 'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/'
const DADOS = process.env.DADOS || null
const SAIDA = process.env.SAIDA || null
if (SAIDA) mkdirSync(SAIDA, { recursive: true })
const TELEFONE = '199'
const TELAS = {
  celular: { width: 390, height: 844, isMobile: true, hasTouch: true },
  desktop: { width: 1366, height: 800 },
}
/** Erros de console que a rede cortada produz e que não são defeito do site. */
const ERRO_DE_REDE = /Failed to load resource|ERR_FAILED|ERR_ABORTED|net::/

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

const servidor = await preview({ preview: { port: 4319, strictPort: true } })
const base = servidor.resolvedUrls.local[0].replace(/\/$/, '')
const navegador = await chromium.launch({ executablePath: acharNavegador(), args: ['--no-sandbox'] })

/** Contexto com a rede externa cortada; com DADOS, serve os JSONs do tempo-real. */
async function contexto(tela) {
  const ctx = await navegador.newContext({
    viewport: { width: tela.width, height: tela.height },
    isMobile: !!tela.isMobile, hasTouch: !!tela.hasTouch, locale: 'pt-BR',
  })
  await ctx.route('**/*', (route) => {
    const url = route.request().url()
    if (url.startsWith(base)) return route.continue()
    if (DADOS && url.startsWith(RAW)) {
      const caminho = join(DADOS, url.slice(RAW.length).split('?')[0])
      if (existsSync(caminho)) return route.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' }, body: readFileSync(caminho) })
    }
    return route.abort()
  })
  return ctx
}
function vigiar(page) {
  const reg = { erros: [], pageerrors: [] }
  page.on('console', (m) => { if (m.type() === 'error' && !ERRO_DE_REDE.test(m.text())) reg.erros.push(m.text().slice(0, 160)) })
  page.on('pageerror', (e) => reg.pageerrors.push(String(e).slice(0, 160)))
  return reg
}
const espera = (page, ms = 1200) => page.waitForTimeout(ms)
async function abrir(ctx, rota, ms = 1500) {
  const page = await ctx.newPage()
  const reg = vigiar(page)
  await page.goto(`${base}/#${rota}`, { waitUntil: 'load' })
  await espera(page, ms)
  return { page, reg }
}
async function captura(page, nome) {
  if (SAIDA) await page.screenshot({ path: join(SAIDA, `${nome}.png`) })
}
async function passo(nome, fn) {
  try { const extra = await fn(); ok(`${nome}${extra ? ` — ${extra}` : ''}`) }
  catch (e) { falhou(`${nome}: ${String(e).split('\n')[0].slice(0, 200)}`) }
}

// 1. Descobre as rotas a partir do início, seguindo os links internos (#/...).
const rotas = new Set(['/'])
{
  const ctx = await contexto(TELAS.desktop)
  const fila = ['/']
  while (fila.length) {
    const rota = fila.shift()
    const { page } = await abrir(ctx, rota, 800)
    for (const h of await page.$$eval('a[href]', (as) => as.map((a) => a.getAttribute('href')))) {
      if (!h || !h.startsWith('#/')) continue
      const limpa = h.slice(1).split('?')[0]
      if (!rotas.has(limpa)) { rotas.add(limpa); fila.push(limpa) }
    }
    await page.close()
  }
  await ctx.close()
}
console.log(`Rotas descobertas a partir do início: ${rotas.size}`)
if (rotas.size < 20) falhou(`só ${rotas.size} rotas descobertas — o início perdeu links?`)

// 2. Cada rota, no celular e no desktop.
for (const [nomeTela, tela] of Object.entries(TELAS)) {
  console.log(`\n${nomeTela} (${tela.width}×${tela.height})`)
  const ctx = await contexto(tela)
  for (const rota of [...rotas].sort()) {
    const { page, reg } = await abrir(ctx, rota)
    const problemas = []
    if (reg.pageerrors.length) problemas.push(`pageerror: ${reg.pageerrors[0]}`)
    if (reg.erros.length) problemas.push(`console: ${reg.erros[0]}`)
    const texto = await page.evaluate(() => document.body.innerText)
    if (!texto.includes(TELEFONE)) problemas.push('sem o telefone 199')
    if (await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1)) problemas.push('rola na horizontal')
    if (texto.length < 200) problemas.push(`quase sem texto (${texto.length} caracteres)`)
    await captura(page, `${nomeTela}${rota.replace(/\//g, '_') || '_inicio'}`)
    if (problemas.length) falhou(`${rota}: ${problemas.join('; ')}`); else ok(rota)
    await page.close()
  }
  await ctx.close()
}

// 3. Os controles do Monitor, nos dois tamanhos.
for (const [nomeTela, tela] of Object.entries(TELAS)) {
  console.log(`\nMonitor no ${nomeTela}`)
  const ctx = await contexto(tela)
  const { page, reg } = await abrir(ctx, '/monitor', 3000)
  await passo('zoom + e −', async () => {
    for (const nome of ['Aproximar', 'Aproximar', 'Afastar', 'Afastar']) { await page.getByRole('button', { name: nome }).click(); await espera(page, 400) }
    await captura(page, `${nomeTela}_monitor_zoom`)
  })
  await passo('menu de cidades abre, Blumenau abre o painel, painel fecha', async () => {
    await page.getByRole('button', { name: /Cidades/ }).click(); await espera(page, 400)
    const menu = page.locator('#menu-cidades')
    const itens = await menu.locator('a, button').count()
    await menu.getByText('Blumenau', { exact: false }).first().click(); await espera(page, 1500)
    await captura(page, `${nomeTela}_monitor_painel`)
    if (!(await page.evaluate(() => document.body.innerText.includes('Blumenau')))) throw new Error('painel não mostra Blumenau')
    await page.getByRole('button', { name: /Fechar o painel de/ }).first().click(); await espera(page, 400)
    return `${itens} itens no menu`
  })
  await passo('reprodução de 24 h', async () => {
    const b = page.getByRole('button', { name: /Reproduzir 24 h/ })
    if (!(await b.count())) return 'sem série — botão ausente (esperado sem DADOS)'
    await b.first().click(); await espera(page, 2000)
    await captura(page, `${nomeTela}_monitor_reproducao`)
    const pausar = page.getByRole('button', { name: /Pausar/ })
    if (!(await pausar.count())) throw new Error('sem botão Pausar durante a reprodução')
    await pausar.first().click()
    const barra = page.getByLabel('Instante da reprodução')
    if (await barra.count()) { await barra.first().focus(); await page.keyboard.press('End'); await espera(page, 600) }
    return 'tocou, pausou e voltou ao vivo'
  })
  await passo('fundos do mapa', async () => {
    const botoes = page.getByRole('group', { name: 'Fundo do mapa' }).getByRole('button')
    const n = await botoes.count()
    if (n < 2) throw new Error(`só ${n} fundo(s)`)
    const nomes = []
    for (let i = 0; i < n; i++) { nomes.push(await botoes.nth(i).innerText()); await botoes.nth(i).click(); await espera(page, 600) }
    await botoes.nth(0).click()
    return nomes.join(', ')
  })
  await passo('camadas de cheia', async () => {
    const det = page.locator('details', { has: page.locator('summary', { hasText: 'Camadas de cheia' }) })
    await det.first().locator('summary').click(); await espera(page, 400)
    const controles = det.first().locator('input, button, select')
    const n = await controles.count()
    if (!n) throw new Error('sem controles dentro de Camadas de cheia')
    await captura(page, `${nomeTela}_monitor_camadas`)
    return `${n} controle(s)`
  })
  await passo('toque e arrasto no mapa', async () => {
    const box = await page.locator('canvas').first().boundingBox()
    await page.mouse.click(box.x + box.width * 0.55, box.y + box.height * 0.45); await espera(page, 500)
    await page.mouse.move(box.x + box.width * 0.3, box.y + box.height * 0.5)
    await page.mouse.down(); await page.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.6, { steps: 6 }); await page.mouse.up()
    await espera(page, 500)
  })
  if (reg.pageerrors.length || reg.erros.length) falhou(`Monitor no ${nomeTela}: ${[...reg.pageerrors, ...reg.erros][0]}`)
  await page.close()
  await ctx.close()
}

// 4. As telas de rio, cidade e Itajaí (desktop). Quase todo passo abre a rota
//    numa página nova, que é como o link chega ao morador — e por isso mesmo
//    não exercita a troca de cidade SEM recarregar, que tem armadilha própria:
//    o passo "trocar de cidade sem recarregar" abaixo cobre exatamente isso.
{
  console.log('\nTelas de rio, cidade e Itajaí')
  const ctx = await contexto(TELAS.desktop)
  await passo('trocar de cidade sem recarregar não escreve NaN no gráfico', async () => {
    // Estado interno de componente que sobrevive à troca de cidade vira
    // atributo NaN no SVG — foi o que o <Brush> da linha do tempo fez até
    // 15/09/2026, com o endIndex da cidade anterior. Não aparece na tela e
    // some no quadro seguinte, então só um vigia no setAttribute o pega.
    const page = await ctx.newPage()
    await page.addInitScript(() => {
      window.__nan = []
      const original = Element.prototype.setAttribute
      Element.prototype.setAttribute = function (nome, valor) {
        if (String(valor) === 'NaN') {
          window.__nan.push(`<${this.tagName}> ${nome} em .${this.parentElement?.getAttribute('class') || '?'}`)
        }
        return original.call(this, nome, valor)
      }
    })
    const reg = vigiar(page)
    // Gaspar → Blumenau é o par que quebrava: séries de tamanhos diferentes,
    // as duas com cotas, então os dois gráficos montam nas duas cidades.
    await page.goto(`${base}/#/acu/gaspar`, { waitUntil: 'load' })
    await espera(page, 2000)
    await page.evaluate(() => { window.__nan = [] })
    const link = page.locator('a[href="#/acu/blumenau"]').first()
    if (await link.count()) await link.click()
    else await page.evaluate(() => { window.location.hash = '#/acu/blumenau' })
    await espera(page, 2200)
    const nan = await page.evaluate(() => window.__nan)
    if (nan.length) throw new Error(`${nan.length} atributo(s) NaN — ${nan[0]}`)
    if (reg.pageerrors.length) throw new Error(reg.pageerrors[0])
    const graficos = await page.locator('.recharts-surface').count()
    await page.close()
    if (graficos === 0) return 'sem gráfico na tela (esperado sem DADOS)'
    return `${graficos} gráfico(s) redesenhado(s), nenhum NaN`
  })
  await passo('/acu: "Ver detalhe" por teclado seleciona a cidade no mapa do rio', async () => {
    const { page, reg } = await abrir(ctx, '/acu', 2000)
    // Os botões "Ver detalhe de …" ficam fora da vista de propósito: são o
    // acesso por teclado e leitor de tela ao toque no canvas. Por isso o
    // teste usa foco + Enter, não clique.
    const botoes = page.getByRole('button', { name: /^Ver detalhe de/, includeHidden: true })
    const n = await botoes.count()
    if (n < 10) throw new Error(`só ${n} botão(ões) "Ver detalhe"`)
    const blumenau = botoes.filter({ hasText: 'Blumenau' }).first()
    await blumenau.focus(); await page.keyboard.press('Enter'); await espera(page, 1500)
    const texto = await page.evaluate(() => document.body.innerText)
    if (!/minha rua alaga com quantos metros\? — Blumenau/i.test(texto)) throw new Error('a seleção não abriu o cartão "minha rua" de Blumenau')
    if (reg.pageerrors.length) throw new Error(reg.pageerrors[0])
    await page.close()
    return `${n} cidades acessíveis por teclado`
  })
  for (const rota of ['/acu/blumenau', '/acu/gaspar', '/mirim/brusque']) {
    await passo(`${rota}: busca "minha rua" e simulador de nível`, async () => {
      const { page, reg } = await abrir(ctx, rota, 2000)
      const rua = page.getByPlaceholder('Nome da rua')
      if (!(await rua.count())) throw new Error('sem campo "Nome da rua"')
      await rua.first().fill('Rua'); await espera(page, 800)
      const itens = await page.locator('li').count()
      const barra = page.locator('input[type=range]')
      if (await barra.count()) { await barra.first().focus(); await page.keyboard.press('End'); await espera(page, 500) }
      await captura(page, `desktop${rota.replace(/\//g, '_')}_busca`)
      if (reg.pageerrors.length || reg.erros.length) throw new Error([...reg.pageerrors, ...reg.erros][0])
      await page.close()
      return `${itens} resultado(s) para "Rua"`
    })
  }
  await passo('/itajai: réguas, cotas e mapa das áreas atingidas', async () => {
    const { page, reg } = await abrir(ctx, '/itajai', 2500)
    const texto = await page.evaluate(() => document.body.innerText)
    for (const frase of ['Como estão as réguas de Itajaí agora', 'Cotas oficiais das réguas de Itajaí', 'maré']) {
      if (!texto.includes(frase)) throw new Error(`faltou "${frase}"`)
    }
    // O mapa das manchas fica fora do carregamento inicial; o botão o monta.
    await page.getByRole('button', { name: 'Ver o mapa das áreas atingidas' }).click(); await espera(page, 2500)
    await page.locator('[aria-label^="Mapa das áreas atingidas"]').first().waitFor({ timeout: 10000 })
    await captura(page, 'desktop_itajai_manchas')
    if (reg.pageerrors.length || reg.erros.length) throw new Error([...reg.pageerrors, ...reg.erros][0])
    await page.close()
  })
  await passo('/municipal/ascurra e /municipal/ascurra/dados', async () => {
    const a = await abrir(ctx, '/municipal/ascurra', 2500)
    if (!(await a.page.evaluate(() => document.body.innerText.includes('Ascurra')))) throw new Error('monitor municipal sem Ascurra')
    if (a.reg.pageerrors.length) throw new Error(a.reg.pageerrors[0])
    await a.page.close()
    const d = await abrir(ctx, '/municipal/ascurra/dados', 2000)
    await d.page.getByRole('combobox', { name: 'Camada sobre o mapa' }).waitFor({ timeout: 5000 })
    if (d.reg.pageerrors.length) throw new Error(d.reg.pageerrors[0])
    await d.page.close()
  })
  await passo('rota inexistente volta ao início', async () => {
    const { page } = await abrir(ctx, '/nao-existe', 1000)
    if (!page.url().endsWith('#/')) throw new Error(`ficou em ${page.url()}`)
    await page.close()
  })
  await ctx.close()
}

await navegador.close()
await servidor.close()
console.log(falhas.length ? `\n${falhas.length} falha(s):\n - ${falhas.join('\n - ')}` : '\nVarredura sem falhas.')
process.exit(falhas.length ? 1 : 0)
