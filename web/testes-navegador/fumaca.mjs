#!/usr/bin/env node
/**
 * Fumaça: o site MONTA num navegador de verdade?
 *
 * POR QUE EXISTE (08/09/2026). Numa manhã de trabalho o `npm run build` passou,
 * os 494 testes passaram, e o site abriu no celular do Jefferson mostrando só
 * isto:
 *
 *     Emergência: ligue 199 (Defesa Civil) ou 193 (Bombeiros).
 *     Carregando os dados dos rios…
 *
 * Aquele "Carregando" é a CASCA ESTÁTICA do index.html — o texto que existe
 * antes de o React montar. Ou seja: o app não montou, e nenhuma verificação do
 * repositório sabia dizer isso. Build compila; teste de unidade roda a lógica
 * fora do navegador; nada carregava a página.
 *
 * Naquele caso a causa era o endereço (o site usa HashRouter e o link foi dado
 * sem o `#`), não um defeito do código. Mas o buraco que ele revelou é real: um
 * import circular, um erro em tempo de módulo ou um asset com caminho errado
 * derrubariam o site inteiro com todas as luzes verdes.
 *
 * O QUE ESTE ARQUIVO GARANTE, e é pouco de propósito — fumaça, não fiscal:
 *
 *   1. O React monta: a casca estática SAI da tela.
 *   2. O aviso do 199 continua lá depois de montar. Ele é o único bloco que
 *      vive no HTML estático justamente para sobreviver a uma falha de
 *      JavaScript, e foi o que apareceu sozinho naquela manhã.
 *   3. Uma rota profunda renderiza a cidade — é o link que alguém compartilha.
 *   4. Nenhum erro de página (`pageerror`) e nenhum erro de console.
 *   5. SEM REDE, o site ainda renderiza. Toda chamada externa é bloqueada aqui
 *      de propósito: numa noite de cheia o GitHub pode estar fora, e a tela
 *      precisa continuar mostrando cotas, histórico e o telefone da Defesa
 *      Civil — sem leitura ao vivo, e dizendo que não tem.
 *
 * Uso:
 *     npm run build && npm run fumaca
 */
import { existsSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { chromium } from 'playwright'
import { preview } from 'vite'

/** O texto da casca do index.html. Se ele continua na tela, o React não montou. */
const CASCA = 'Carregando os dados dos rios'
const TELEFONE = '199'

/**
 * O Chromium, onde quer que ele esteja.
 *
 * Em CI o `playwright install chromium` põe onde o playwright espera. Neste
 * ambiente de desenvolvimento existe um Chromium pré-instalado de OUTRA versão
 * (build 1194 contra o 1243 que o pacote pede), e a resolução padrão falha. Em
 * vez de fixar a versão do pacote na do ambiente — que quebraria no dia em que
 * a imagem mudar —, procura-se o binário.
 */
function acharNavegador() {
  const padrao = chromium.executablePath()
  if (existsSync(padrao)) return undefined // deixa o playwright resolver
  const raiz = process.env.PLAYWRIGHT_BROWSERS_PATH
  if (raiz && existsSync(raiz)) {
    for (const pasta of readdirSync(raiz).filter((d) => d.startsWith('chromium-'))) {
      const bin = join(raiz, pasta, 'chrome-linux', 'chrome')
      if (existsSync(bin)) return bin
    }
  }
  throw new Error(
    'Chromium não encontrado. Em CI: npx playwright install --with-deps chromium',
  )
}

const falhas = []
const ok = (m) => console.log(`  ✓ ${m}`)
const falhou = (m) => { falhas.push(m); console.log(`  ✗ ${m}`) }

const servidor = await preview({ preview: { port: 4318, strictPort: true } })
const base = servidor.resolvedUrls.local[0].replace(/\/$/, '')
const executablePath = acharNavegador()
const navegador = await chromium.launch({ executablePath, args: ['--no-sandbox'] })

/** Abre uma rota com a rede externa cortada e devolve o que a tela mostra. */
async function abrir(rota) {
  // O service worker (modo aplicativo) tem teste próprio, pwa.mjs.
  const pagina = await navegador.newPage({ serviceWorkers: 'block' })
  const erros = []
  pagina.on('pageerror', (e) => erros.push(`pageerror: ${e.message}`))
  pagina.on('console', (m) => {
    // "Failed to load resource" é o ruído do bloqueio abaixo: o navegador
    // registra um erro de console por requisição externa cortada. Ignorar a
    // MENSAGEM é seguro porque a mesma falha é pega com precisão em
    // `requestfailed`, que sabe a URL — e é lá que o caso importante mora.
    if (m.type() === 'error' && !m.text().includes('Failed to load resource')) {
      erros.push(`console: ${m.text()}`)
    }
  })
  // Requisição DO PRÓPRIO SITE que falha é defeito nosso, sempre. Foi assim
  // que o site quebrou em 08/09: o bundle era pedido em `/mirim/assets/…` e
  // devolvia 404. Externa que falha é o bloqueio de propósito, logo abaixo.
  pagina.on('requestfailed', (r) => {
    if (r.url().startsWith(base)) erros.push(`asset do site falhou: ${r.url()}`)
  })
  // Corta TUDO que não é o próprio site. O teste passa a medir o nosso código,
  // não a rede do runner — e de quebra prova o item 5.
  await pagina.route('**/*', (r) => (r.request().url().startsWith(base) ? r.continue() : r.abort()))
  await pagina.goto(`${base}/#/${rota}`, { waitUntil: 'load', timeout: 30_000 })
  // Espera a casca sair em vez de dormir um tempo fixo: dormir pouco dá falso
  // vermelho em runner lento, e dormir muito atrasa todo mundo.
  await pagina.waitForFunction(
    (casca) => !document.querySelector('#root')?.textContent?.includes(casca),
    CASCA,
    { timeout: 20_000 },
  ).catch(() => {})
  const texto = await pagina.locator('#root').innerText().catch(() => '')
  await pagina.close()
  return { texto, erros }
}

console.log(`\nfumaça em ${base}\n`)

console.log('início (/)')
{
  const { texto, erros } = await abrir('')
  texto.includes(CASCA) ? falhou('o React NÃO montou — a casca estática continua na tela') : ok('o React montou')
  texto.includes(TELEFONE) ? ok('o telefone 199 está na tela') : falhou('o 199 SUMIU da tela')
  texto.includes('Escolha o rio') ? ok('a tela inicial renderizou') : falhou('a tela inicial não renderizou')
  erros.length ? falhou(`erros no navegador: ${erros.join(' | ')}`) : ok('sem erro de página nem de console')
}

console.log('\nrota profunda (/#/mirim/brusque) — o link que se compartilha')
{
  const { texto, erros } = await abrir('mirim/brusque')
  texto.includes(CASCA) ? falhou('rota profunda não montou') : ok('montou')
  texto.includes('Brusque') ? ok('a cidade renderizou') : falhou('a cidade não renderizou')
  texto.includes(TELEFONE) ? ok('o telefone 199 está na tela') : falhou('o 199 SUMIU da tela')
  // Sem rede não há leitura ao vivo, e a tela tem de DIZER isso em vez de
  // ficar em branco ou, pior, mostrar um número velho como se fosse de agora.
  texto.includes('Sem leitura ao vivo') || texto.includes('Cotas de referência')
    ? ok('sem rede, a tela ainda diz o que sabe e o que não sabe')
    : falhou('sem rede, a tela não explicou a ausência da leitura')
  erros.length ? falhou(`erros no navegador: ${erros.join(' | ')}`) : ok('sem erro de página nem de console')
}

console.log('\nversão 2: aviso completo na primeira visita e faixa do 199 em toda tela')
{
  // Decisão D1 (03/10/2026): a regra do CLAUDE.md fica. A faixa curta diz que o
  // site não substitui a Defesa Civil; o texto completo abre sozinho na
  // primeira visita e só sai com "Entendi".
  const ctx = await navegador.newContext({ serviceWorkers: 'block' })
  await ctx.route('**/*', (r) => (r.request().url().startsWith(base) ? r.continue() : r.abort()))
  const pagina = await ctx.newPage()
  await pagina.goto(`${base}/#/`, { waitUntil: 'load' })
  const folha = pagina.locator('dialog[open]')
  await folha.waitFor({ timeout: 10_000 }).catch(() => {})
  const textoFolha = (await folha.count()) ? await folha.innerText() : ''
  textoFolha.includes('não substitui') && textoFolha.includes('199')
    ? ok('a folha do aviso completo abre na primeira visita')
    : falhou('a folha do aviso completo NÃO abriu na primeira visita')
  const faixa = await pagina.locator('[role="note"]').first().innerText().catch(() => '')
  ;/199/.test(faixa) && /não substitui a Defesa Civil/.test(faixa)
    ? ok('a faixa do topo tem o 199 e diz que não substitui a Defesa Civil')
    : falhou(`a faixa do topo perdeu o 199 ou o "não substitui" (${faixa})`)
  await pagina.getByRole('button', { name: 'Entendi' }).click().catch(() => {})
  await pagina.reload({ waitUntil: 'load' })
  await pagina.waitForTimeout(800)
  ;(await pagina.locator('dialog[open]').count()) === 0
    ? ok('depois do "Entendi", a folha não volta sozinha')
    : falhou('a folha voltou depois do "Entendi"')
  const corpo = await pagina.locator('#root').innerText()
  corpo.includes('Leia antes de usar') ? ok('o aviso completo continua no fim da página') : falhou('o aviso completo sumiu da página')
  await pagina.goto(`${base}/#/monitor`, { waitUntil: 'load' })
  await pagina.waitForTimeout(800)
  ;(await pagina.getByText('Emergência: ligue 199').count()) > 0 &&
  (await pagina.locator('nav[aria-label="Principal"]').count()) === 0
    ? ok('o Monitor mantém a casca antiga, sem a barra nova (D2)')
    : falhou('o Monitor perdeu a casca antiga ou ganhou a barra nova')
  await ctx.close()
}

console.log('\n"Minha rua alaga?" leva ao que promete, com a tela no lugar certo')
{
  // Relato do Jefferson (04/10/2026), no celular: o botão "Minha rua alaga?" da
  // Início "só subia a tela". A página da cidade abria na MESMA rolagem da Início,
  // com as abas fora da tela e o título por baixo da faixa do 199; em Itajaí, o
  // botão levava ao topo da foz, longe do mapa. A pessoa rola até o botão (no
  // celular ele fica embaixo) e clica: o que ela pediu tem de estar à vista.
  for (const [rio, id, esperado] of [
    ['acu', 'blumenau', 'A minha rua alaga com quantos metros?'],
    ['mirim', 'brusque', 'A minha rua alaga com quantos metros?'],
    ['acu', 'itajai', 'Até onde a água chegou'],
  ]) {
    const ctx = await navegador.newContext({ serviceWorkers: 'block', viewport: { width: 390, height: 844 } })
    await ctx.route('**/*', (r) => (r.request().url().startsWith(base) ? r.continue() : r.abort()))
    await ctx.addInitScript((c) => localStorage.setItem('enchentes:cidades', JSON.stringify([c])), { id, rio })
    const pagina = await ctx.newPage()
    await pagina.goto(`${base}/#/`, { waitUntil: 'load' })
    await pagina.getByRole('button', { name: 'Entendi' }).click({ timeout: 5_000 }).catch(() => {})
    const botao = pagina.getByRole('link', { name: 'Minha rua alaga?' }).first()
    await botao.waitFor({ timeout: 10_000 }).catch(() => {})
    await botao.evaluate((el) => el.scrollIntoView({ block: 'end' })).catch(() => {})
    await pagina.evaluate(() => window.scrollBy(0, 200))
    await botao.click({ timeout: 5_000 }).catch(() => {})
    const titulo = pagina.getByRole('heading', { name: esperado }).first()
    await titulo.waitFor({ timeout: 10_000 }).catch(() => {})
    const caixa = await titulo.boundingBox().catch(() => null)
    // Abaixo da faixa presa no topo (≈ 70 px) e dentro da primeira tela.
    caixa && caixa.y > 70 && caixa.y < 844
      ? ok(`${id}: "${esperado}" à vista depois do clique (y = ${Math.round(caixa.y)})`)
      : falhou(`${id}: depois do clique, "${esperado}" não ficou à vista (${caixa ? `y = ${Math.round(caixa.y)}` : 'não achado'})`)
    await ctx.close()
  }
}

console.log('\no chat do histórico tem botão na tela inicial')
{
  // Pedido do Jefferson (04/10/2026): o chat só existia no fim da aba Histórico.
  // A Início ganhou o cartão "Pergunte sobre as cheias", que abre /perguntas.
  const ctx = await navegador.newContext({ serviceWorkers: 'block', viewport: { width: 390, height: 844 } })
  await ctx.route('**/*', (r) => (r.request().url().startsWith(base) ? r.continue() : r.abort()))
  const pagina = await ctx.newPage()
  await pagina.goto(`${base}/#/`, { waitUntil: 'load' })
  await pagina.getByRole('button', { name: 'Entendi' }).click({ timeout: 5_000 }).catch(() => {})
  const cartao = pagina.getByRole('link', { name: /Pergunte sobre as cheias/ })
  ;(await cartao.count()) > 0 ? ok('a Início tem o cartão do chat') : falhou('a Início perdeu o cartão do chat')
  await cartao.click({ timeout: 5_000 }).catch(() => {})
  const chat = pagina.locator('section[aria-label="Perguntas sobre o histórico de enchentes"]')
  await chat.waitFor({ timeout: 15_000 }).catch(() => {})
  ;(await chat.count()) > 0 && pagina.url().endsWith('#/perguntas')
    ? ok('o cartão abre a página do chat (/perguntas)')
    : falhou(`o cartão não abriu o chat (${pagina.url()})`)
  await ctx.close()
}

console.log('\nchat com IA: botão só com o servidor ligado; o presente nunca vai à IA')
{
  // docs/CHAT-IA.md. O `vite preview` não roda as funções: o /api/chat-ia é simulado aqui.
  async function chatCom(ligado, enviados) {
    const ctx = await navegador.newContext({ serviceWorkers: 'block', viewport: { width: 390, height: 844 } })
    await ctx.route('**/*', (r) => (r.request().url().startsWith(base) ? r.continue() : r.abort()))
    await ctx.route('**/api/chat-ia', (r) => {
      if (r.request().method() === 'GET') return r.fulfill({ json: { ligado } })
      enviados.push(JSON.parse(r.request().postData() ?? '{}'))
      return r.fulfill({ json: { tipo: 'ia', texto: 'Resposta simulada da IA.' } })
    })
    const pagina = await ctx.newPage()
    await pagina.goto(`${base}/#/perguntas`, { waitUntil: 'load' })
    await pagina.getByRole('button', { name: 'Entendi' }).click({ timeout: 5_000 }).catch(() => {})
    const caixa = pagina.getByRole('textbox', { name: 'Sua pergunta' })
    await pagina.waitForFunction(() => !document.querySelector('input[aria-label="Sua pergunta"]')?.disabled, null, { timeout: 15_000 }).catch(() => {})
    return { ctx, pagina, caixa }
  }
  async function perguntar(pagina, caixa, q) {
    await caixa.fill(q)
    await pagina.getByRole('button', { name: 'Perguntar', exact: true }).click()
  }

  const nada = []
  const desligado = await chatCom(false, nada)
  await perguntar(desligado.pagina, desligado.caixa, 'Qual foi a maior cheia de Gaspar?')
  await desligado.pagina.waitForTimeout(500)
  ;(await desligado.pagina.getByRole('button', { name: 'Perguntar à IA' }).count()) === 0
    ? ok('servidor desligado: nenhum botão "Perguntar à IA"')
    : falhou('botão da IA apareceu com o servidor desligado')
  await desligado.ctx.close()

  const enviados = []
  const { ctx, pagina, caixa } = await chatCom(true, enviados)
  ;(await pagina.getByText(/envia o texto da pergunta à Anthropic/).count()) > 0
    ? ok('aviso de envio à Anthropic visível')
    : falhou('faltou o aviso de envio à Anthropic')
  await perguntar(pagina, caixa, 'O rio vai encher hoje?')
  await pagina.waitForTimeout(500)
  ;(await pagina.getByRole('button', { name: 'Perguntar à IA' }).count()) === 0
    ? ok('pergunta sobre agora: sem botão da IA')
    : falhou('pergunta sobre agora ganhou botão da IA')
  // "Como está Blumenau?" (05/10/2026): resposta do presente com o 199 e o atalho para a cidade.
  // O tempo real vem de fora e é bloqueado aqui: a resposta diz que não há leitura recente.
  await perguntar(pagina, caixa, 'como está Blumenau?')
  await pagina.getByRole('link', { name: 'Ver Blumenau agora →' }).waitFor({ timeout: 5_000 }).catch(() => {})
  const presente = (await pagina.locator('[role="log"] > div').allInnerTexts()).at(-2) ?? ''
  ;(await pagina.getByRole('link', { name: 'Ver Blumenau agora →' }).count()) > 0 && /199/.test(presente) && !/maior cheia/i.test(presente)
    ? ok('"como está Blumenau?": 199 e atalho para a cidade, sem a maior cheia')
    : falhou(`"como está Blumenau?": ${presente.slice(0, 120)}`)
  await pagina.getByRole('link', { name: 'Ver Blumenau agora →' }).click({ timeout: 5_000 }).catch(() => {})
  await pagina.waitForTimeout(500)
  pagina.url().includes('#/acu/blumenau') ? ok('o atalho abre a página de Blumenau') : falhou(`o atalho abriu ${pagina.url()}`)
  await pagina.goBack()
  await pagina.waitForFunction(() => !document.querySelector('input[aria-label="Sua pergunta"]')?.disabled, null, { timeout: 15_000 }).catch(() => {})
  // Rua de Itajaí pelas manchas da Prefeitura (05/10/2026): baixa a tabela só agora e dá o atalho do mapa.
  await perguntar(pagina, caixa, 'em 2011 a rua jose domingos machado em itajai teve cheias?')
  await pagina.getByText(/Rua José Domingos Machado \(cerca de 1\.014 m/).waitFor({ timeout: 10_000 }).catch(() => {})
  ;(await pagina.getByText(/setembro de 2011: a rua toda/).count()) > 0 && (await pagina.getByRole('link', { name: 'Ver no mapa das manchas de Itajaí →' }).count()) > 0
    ? ok('rua de Itajaí: resposta pelas manchas e atalho para o mapa')
    : falhou('rua de Itajaí: faltou a resposta pelas manchas ou o atalho')
  await perguntar(pagina, caixa, 'Qual foi a maior cheia de Gaspar?')
  const botao = pagina.getByRole('button', { name: 'Perguntar à IA' })
  await botao.last().click({ timeout: 5_000 }).catch(() => {})
  await pagina.getByText('Resposta simulada da IA.').waitFor({ timeout: 5_000 }).catch(() => {})
  ;(await pagina.getByText('Resposta simulada da IA.').count()) > 0 &&
  (await pagina.getByText(/Resposta da IA com os dados do site/).count()) > 0 &&
  enviados.length === 1 &&
  enviados[0].pergunta === 'Qual foi a maior cheia de Gaspar?'
    ? ok('o botão envia uma pergunta e mostra a resposta com o rótulo da IA')
    : falhou(`envio à IA não funcionou (${JSON.stringify(enviados)})`)
  await ctx.close()
}

console.log('\npiloto do classificador: "Entendi", Correto/Não era isso, falha vira "não consegui interpretar"')
{
  // docs/PILOTO-CLASSIFICADOR.md. O /api/chat-classificar é simulado (o preview não roda funções).
  const CLASSIF = { intencao: 'maiores_cheias', cidade: 'blumenau', cidade2: null, rio: null, ano: null, ano_final: null, mes: null, nivel_m: null, quantidade: 1, rua: null }
  const ID = '2026-10-05_00000000-0000-4000-8000-000000000001'
  const enviados = []
  let quebrar = false
  const ctx = await navegador.newContext({ serviceWorkers: 'block', viewport: { width: 390, height: 844 } })
  await ctx.route('**/*', (r) => (r.request().url().startsWith(base) ? r.continue() : r.abort()))
  await ctx.route('**/api/chat-classificar', (r) => {
    if (r.request().method() === 'GET') return r.fulfill({ json: { ligado: true } })
    const corpo = JSON.parse(r.request().postData() ?? '{}')
    enviados.push(corpo)
    if ('correcao' in corpo) return r.fulfill({ json: { ok: true } })
    if (quebrar) return r.fulfill({ status: 504, json: { erro: 'tempo' } })
    if (/medo/.test(corpo.pergunta)) return r.fulfill({ json: { id: ID, decisao: { tipo: 'agora', origem: 'classificador' } } })
    return r.fulfill({ json: { id: ID, decisao: { tipo: 'ok', classificacao: CLASSIF } } })
  })
  const pagina = await ctx.newPage()
  await pagina.goto(`${base}/#/perguntas`, { waitUntil: 'load' })
  await pagina.getByRole('button', { name: 'Entendi' }).click({ timeout: 5_000 }).catch(() => {})
  const caixa = pagina.getByRole('textbox', { name: 'Sua pergunta' })
  await pagina.waitForFunction(() => !document.querySelector('input[aria-label="Sua pergunta"]')?.disabled, null, { timeout: 15_000 }).catch(() => {})
  const perguntar = async (q) => {
    await caixa.fill(q)
    await pagina.getByRole('button', { name: 'Perguntar', exact: true }).click()
  }
  ;(await pagina.getByText(/Piloto: quando o chat não entende/).count()) > 0 ? ok('aviso do piloto visível') : falhou('faltou o aviso do piloto')

  // Pergunta que o motor entende: não vai ao classificador.
  await perguntar('Qual foi a maior cheia de Gaspar?')
  await pagina.waitForTimeout(500)
  enviados.length === 0 ? ok('pergunta entendida pelo motor não vai ao classificador') : falhou(`foi ao classificador: ${JSON.stringify(enviados)}`)

  await perguntar('qual foi a enchente mais feia que blumenal já viu?')
  await pagina.getByText('Entendi:').waitFor({ timeout: 5_000 }).catch(() => {})
  ;(await pagina.getByText(/a maior cheia de Blumenau\./).count()) > 0 && (await pagina.getByText(/A maior cheia registrada de Blumenau foi de 17,3 m/).count()) > 0
    ? ok('"Entendi: a maior cheia de Blumenau" + resposta do motor')
    : falhou('faltou o "Entendi" ou a resposta do motor')
  await pagina.getByRole('button', { name: 'Não era isso' }).click({ timeout: 5_000 }).catch(() => {})
  await pagina.getByText('Marcado como entendido errado.').waitFor({ timeout: 5_000 }).catch(() => {})
  const corr = enviados.find((x) => 'correcao' in x)
  corr?.correcao === 'nao_era_isso' && corr.id === ID && (await pagina.getByText(/Obrigado por avisar/).count()) > 0 && (await pagina.getByRole('button', { name: 'Correto' }).count()) === 0
    ? ok('"Não era isso" envia a correção, some com os botões e dá os exemplos')
    : falhou(`correção não funcionou (${JSON.stringify(enviados)})`)

  // Palpite + situacao_atual: o aviso da Defesa Civil, nunca a maior cheia.
  await perguntar('Estou com medo do rio em Blumenau, o que você acha?')
  await pagina.waitForTimeout(800)
  const ultimas = await pagina.locator('[role="log"] > div').allInnerTexts()
  ;/ligue 199/.test(ultimas.at(-2) ?? '') && enviados.some((x) => x.origem === 'palpite')
    ? ok('palpite com situacao_atual: aviso da Defesa Civil')
    : falhou(`palpite do presente: ${JSON.stringify(ultimas.slice(-2))}`)

  quebrar = true
  await perguntar('top 3 enchentes de rio do sul')
  await pagina.getByText(/Não consegui interpretar a pergunta/).waitFor({ timeout: 10_000 }).catch(() => {})
  const fim = await pagina.locator('[role="log"] > div').allInnerTexts()
  ;/Não consegui interpretar a pergunta/.test(fim.at(-2) ?? '') && !/maiores cheias registradas de Rio do Sul/.test(fim.at(-2) ?? '')
    ? ok('falha do servidor: "não consegui interpretar", sem o palpite')
    : falhou(`falha do servidor: ${JSON.stringify(fim.slice(-2))}`)
  await ctx.close()
}

await navegador.close()
await servidor.close()

console.log(falhas.length ? `\n${falhas.length} FALHA(S)\n` : '\nfumaça limpa\n')
process.exit(falhas.length ? 1 : 0)
