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
  const pagina = await navegador.newPage()
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

await navegador.close()
await servidor.close()

console.log(falhas.length ? `\n${falhas.length} FALHA(S)\n` : '\nfumaça limpa\n')
process.exit(falhas.length ? 1 : 0)
