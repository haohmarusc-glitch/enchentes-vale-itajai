/**
 * O CHAT NO TOPO E OS COMANDOS DO MONITOR (docs/CHAT-GLOBAL-COMANDOS.md, 06/10/2026).
 *
 * O que reprova:
 *  - a caixa não aparece uma vez só (zero, ou duas na mesma tela);
 *  - um pedido não faz o que diz ("zoom na régua DC-05" e o seletor não muda; "voltar" e nada volta);
 *  - pergunta mudando o mapa;
 *  - o painel do chat aberto cobrindo o zoom, a legenda ou o menu no Monitor;
 *  - erro de JavaScript na página.
 *
 * Uso (com o site servido em :4173, como as outras sondas):
 *   npx vite preview --port 4173 &
 *   CHROMIUM=/caminho/chrome PLAYWRIGHT=playwright node testes-navegador/chat-comandos.mjs
 */
import { abrir } from './base.mjs'

let falhas = 0
const ok = (cond, msg) => {
  console.log(`  ${cond ? '✓' : '✗'} ${msg}`)
  if (!cond) falhas++
}
const caixas = (pg) => pg.locator('input[aria-label="Pergunte ou peça"]:not([disabled]), input[aria-label="Sua pergunta"]')

/** A folha do aviso abre na primeira visita e só sai com "Entendi" (regra D1): a pessoa leria antes. */
async function entender(pg) {
  const b = pg.getByRole('button', { name: 'Entendi' })
  if (await b.count()) await b.first().click()
  await pg.waitForTimeout(300)
}

async function pedir(pg, texto) {
  const campo = pg.locator('input[aria-label="Pergunte ou peça"]:not([disabled])').first()
  await campo.click()
  await campo.fill(texto)
  await campo.press('Enter')
  await pg.waitForTimeout(2500)
}
/** A última resposta: no painel aberto, ou na linha de status quando ele recolheu (celular, depois de um pedido). */
const ultimaResposta = (pg) => pg.evaluate(() => {
  const noPainel = [...document.querySelectorAll('[role="log"] [class*="chat-assistente"]')].at(-1)
  const naLinha = document.querySelector('[class*="global-ultima"] p')
  return (noPainel ?? naLinha)?.innerText ?? ''
})
/** Só exceção da página conta: sem rede, os mosaicos do fundo falham por certificado, e isso não é do chat. */
const excecoes = (erros) => erros.filter((e) => e.startsWith('PAGEERROR'))

for (const [w, h] of [[390, 844], [1280, 800]]) {
  console.log(`\n=== ${w}x${h} ===`)
  // 1. Início: uma barra; "mostrar Blumenau" abre o Monitor dela.
  {
    const { b, pg, erros } = await abrir('#/', { largura: w, altura: h })
    await entender(pg)
    ok((await caixas(pg).count()) === 1, 'Início: a caixa aparece uma vez')
    await pedir(pg, 'mostrar Blumenau')
    await pg.waitForTimeout(2000)
    ok(pg.url().endsWith('#/monitor/blumenau'), `"mostrar Blumenau" abriu ${pg.url().split('#')[1]}`)
    ok((await caixas(pg).count()) === 1, 'Monitor: a caixa aparece uma vez, no bloco do topo')
    ok(/Monitor de Blumenau aberto e enquadrado/.test(await ultimaResposta(pg)), 'a conversa continuou no Monitor e disse o que fez')
    ok(excecoes(erros).length === 0, `sem exceção de JavaScript (${excecoes(erros).join(' | ')})`)
    await b.close()
  }
  // 2. Itajaí: régua por código, fundo, voltar, ambiguidade e leitura do estado.
  {
    const { b, pg, erros } = await abrir('#/monitor/itajai', { largura: w, altura: h })
    await pedir(pg, 'aproxime a régua')
    ok(/11 réguas\. Qual delas\?/.test(await ultimaResposta(pg)), 'Itajaí sem régua escolhida: pergunta qual das onze')
    ok((await pg.locator('#seletor-regua').inputValue()) !== 'DC-05', 'pergunta não mexeu no seletor')
    await pedir(pg, 'zoom na régua DC-05')
    ok((await pg.locator('#seletor-regua').inputValue()) === 'DC-05', 'o seletor foi para DC-05')
    ok(/Mapa centralizado na régua DC-05/.test(await ultimaResposta(pg)), 'o chat disse o resultado real')
    // No celular, o pedido recolhe a conversa (o resultado está no mapa); a linha de status mostra a resposta.
    if (w <= 700) ok((await pg.locator('#chat-painel').count()) === 0 && (await pg.locator('[class*="global-ultima"]').count()) === 1, 'celular: conversa recolhida depois do pedido, com a última resposta à vista')
    await pedir(pg, 'satélite')
    const satelite = await pg.locator('[aria-label="Fundo do mapa"] button[aria-pressed="true"]').innerText().catch(() => '')
    ok(/Fundo do mapa: satélite/.test(await ultimaResposta(pg)), `fundo trocado (botão ativo: ${satelite.trim() || '?'})`)
    await pedir(pg, 'o que estou vendo?')
    const visto = await ultimaResposta(pg)
    ok(/Monitor de Itajaí/.test(visto) && /DC-05/.test(visto) && /satélite/.test(visto), 'o que estou vendo: cidade, régua e fundo de agora')
    await pedir(pg, 'voltar ao mapa de antes')
    ok(/Voltei ao mapa de antes/.test(await ultimaResposta(pg)), 'voltar: confirmado')
    ok((await pg.locator('#seletor-regua').inputValue()) === 'DC-05', 'voltar desfez só o fundo (a régua era de antes)')
    await pedir(pg, 'qual a maior cheia de Blumenau?')
    ok(pg.url().endsWith('#/monitor/itajai'), 'pergunta não navegou nem mexeu no mapa')
    await pg.locator('input[aria-label="Pergunte ou peça"]:not([disabled])').first().focus()
    await pg.waitForTimeout(400)
    // Painel aberto não cobre os controles.
    const cobre = await pg.evaluate(() => {
      const cruza = (a, c) => a.left < c.right && c.left < a.right && a.top < c.bottom && c.top < a.bottom
      const painel = document.querySelector('#chat-painel')?.getBoundingClientRect()
      const zoom = document.querySelector('[aria-label="Zoom do mapa"]')?.getBoundingClientRect()
      const fundos = document.querySelector('[aria-label="Fundo do mapa"]')?.getBoundingClientRect()
      return {
        temPainel: !!painel,
        zoom: !!(painel && zoom && cruza(painel, zoom)),
        fundos: !!(painel && fundos && cruza(painel, fundos)),
      }
    })
    ok(cobre.temPainel && !cobre.zoom && !cobre.fundos, `painel aberto não cobre zoom nem fundos (${JSON.stringify(cobre)})`)
    await pg.screenshot({ path: `${process.env.SAIDA || '.'}/chat-monitor-itajai-${w}.png` })
    ok(excecoes(erros).length === 0, `sem exceção de JavaScript (${excecoes(erros).join(' | ')})`)
    await b.close()
  }
  // 3. Página com chat próprio: a barra do topo some.
  {
    const { b, pg } = await abrir('#/perguntas', { largura: w, altura: h })
    ok((await caixas(pg).count()) === 1, '/perguntas: só o chat da página, sem a barra do topo')
    await b.close()
  }
}

console.log(`\n${falhas} falha(s).`)
process.exit(falhas ? 1 : 0)
