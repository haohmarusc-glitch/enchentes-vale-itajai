/**
 * Base das sondas de layout do Monitor.
 *
 * POR QUE ISTO EXISTE. Os testes puros (`src/logica/*.test.ts`) alcançam a
 * decisão — qual rótulo cabe, qual régua fala em cada zoom. Não alcançam a
 * GEOMETRIA: dois blocos `position: absolute` que se cobrem, um `z-index` que
 * troca quem recebe o toque, um controle cortado pelo container que rola. Foi
 * assim que o seletor de fundo do mapa ficou visível e inerte, e que o botão
 * "−" (afastar) sumiu atrás da barra de reprodução. Nenhum teste podia
 * reprovar isso, porque nenhum teste olhava a tela.
 *
 * COMO RODAR (precisa de Chromium e do site servido):
 *
 *   cd web && npm run build && npx vite preview --port 4173 &
 *   npm i -D playwright-core   # ou aponte PLAYWRIGHT para uma instalação existente
 *   CHROMIUM=/caminho/para/chrome node testes-navegador/colisao-dos-controles.mjs
 *
 * Variáveis: CHROMIUM (binário), PLAYWRIGHT (módulo), SITE (endereço servido,
 * padrão http://localhost:4173/), DADOS (pasta com o tempo-real), SAIDA (onde
 * gravar as capturas das falhas).
 *
 * DADO AO VIVO. O site busca nível do branch `tempo-real` em tempo de
 * execução. Onde a rede do navegador não alcança o raw.githubusercontent,
 * baixe os quatro arquivos antes e aponte DADOS para a pasta deles:
 *
 *   mkdir -p /tmp/tr && for f in ultimo.json ultimo_barragens.json \
 *     ultimo_nivel_sc.json serie-recente.json; do curl -sL \
 *     "https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/$f" \
 *     -o /tmp/tr/$f; done
 *   DADOS=/tmp/tr node testes-navegador/colisao-dos-controles.mjs
 *
 * Sem DADOS a sonda roda igual, só que sem número na tela — o que basta para
 * a geometria, mas não para conferir rótulo de nível.
 */
import { readFileSync, existsSync } from 'node:fs'

/* O playwright NÃO é dependência do projeto: esta sonda é manual, e prender o
   `npm install` do site a um navegador seria caro para todo mundo por causa de
   um script que roda de vez em quando. Onde ele estiver instalado global (o
   caso do runner do Claude Code), aponte PLAYWRIGHT para o módulo. */
const { chromium } = await import(process.env.PLAYWRIGHT || 'playwright-core')

const CHROMIUM = process.env.CHROMIUM || undefined
const DADOS = process.env.DADOS || null
const SITE = process.env.SITE || 'http://localhost:4173/'
const RAW = 'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/'

/** Serve à página o MESMO dado do branch tempo-real, baixado com curl. */
export async function abrir(rota, { largura = 1280, altura = 900, semRede = false } = {}) {
  const b = await chromium.launch(CHROMIUM ? { executablePath: CHROMIUM } : {})
  const pg = await b.newPage({ viewport: { width: largura, height: altura }, deviceScaleFactor: 2 })
  const erros = []
  pg.on('console', m => { if (m.type() === 'error') erros.push(m.text().slice(0, 200)) })
  pg.on('pageerror', e => erros.push('PAGEERROR ' + e.message.slice(0, 200)))
  if (!semRede && DADOS) {
    for (const f of ['ultimo.json', 'ultimo_barragens.json', 'ultimo_nivel_sc.json', 'serie-recente.json']) {
      const caminho = `${DADOS}/${f}`
      if (!existsSync(caminho)) continue
      await pg.route(RAW + f, r => r.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'access-control-allow-origin': '*' },
        body: readFileSync(caminho),
      }))
    }
  }
  await pg.goto(SITE + rota, { waitUntil: 'domcontentloaded' })
  await pg.waitForTimeout(4000)
  return { b, pg, erros }
}
