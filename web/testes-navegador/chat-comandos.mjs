/**
 * O CHAT NO TOPO E OS COMANDOS DO MONITOR (docs/CHAT-GLOBAL-COMANDOS.md, 06/10/2026).
 *
 * O que reprova:
 *  - a caixa não aparece uma vez só (zero, ou duas na mesma tela);
 *  - um pedido não faz o que diz ("zoom na régua DC-05" e o seletor não muda; "voltar" e nada volta);
 *  - pergunta mudando o mapa;
 *  - o painel do chat aberto cobrindo o zoom, a legenda ou o menu no Monitor;
 *  - erro de JavaScript na página;
 *  - 2ª entrega: link sem régua/fundo ou sem o aviso de acesso; filtro dito e não mostrado (ou o contrário);
 *    confluência sem a coordenada do cadastro, ou ponto marcado para rio sem ponto gravado; traçado sem a
 *    data da base; montante sem o aviso de que ligação não é previsão; gráfico que não abre a página;
 *  - 3ª entrega: rua de Itajaí sem o traçado magenta, sem a legenda de destaque ou sem a interseção; cenário que
 *    apaga a rua; "remover destaque" que não remove; rua de Gaspar sem a marca e o aviso de localização
 *    aproximada; rua de Blumenau mexendo no mapa.
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
/** Pede e espera a resposta casar com `re` (respostas que leem as leituras ao vivo podem levar segundos). */
async function pedirAte(pg, texto, re, ms = 15000) {
  await pedir(pg, texto)
  const fim = Date.now() + ms
  let r = await ultimaResposta(pg)
  while (!re.test(r) && Date.now() < fim) {
    await pg.waitForTimeout(500)
    r = await ultimaResposta(pg)
  }
  return r
}
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
  // 3. 2ª entrega: link, filtro, confluência, traçado, árvore, leituras, gráfico.
  {
    const { b, pg, erros } = await abrir('#/monitor/itajai', { largura: w, altura: h })
    await pedir(pg, 'zoom na régua DC-05')
    let r = await pedirAte(pg, 'copiar link desta visualização', /Link desta visualização/)
    ok(/#\/monitor\/itajai\?regua=DC-05&fundo=/.test(r) && /e-mail cadastrado/.test(r), 'copiar link: régua e fundo no endereço, com o aviso do acesso')
    ok((await pg.getByRole('button', { name: 'Copiar' }).count()) >= 1, 'copiar link: o botão "Copiar" fica à vista (a conversa não recolhe)')
    r = await pedirAte(pg, 'mostrar só as réguas sem leitura', /Filtro ligado|têm leitura de agora/)
    const chipFiltro = await pg.getByText('Filtro: só cidades e réguas sem leitura de agora').count()
    ok(/Filtro ligado/.test(r) ? chipFiltro === 1 : chipFiltro === 0, `filtro: o que o chat diz é o que a tela mostra (${r.slice(0, 60)}…)`)
    await pedirAte(pg, 'limpar filtros', /Filtro limpo|Não há filtro/)
    ok((await pg.getByText('Filtro: só cidades e réguas sem leitura de agora').count()) === 0, 'limpar filtros: o aviso do filtro saiu da tela')
    r = await pedirAte(pg, 'ver a confluência do Benedito', /Benedito/)
    ok(/−26,89134, −49,23557/.test(r) && (await pg.getByText(/^Marca: Confluência do Rio Benedito/).count()) === 1, 'confluência do Benedito: coordenada do cadastro e a marca escrita na tela')
    r = await pedirAte(pg, 'confluência do Luís Alves', /Luís Alves/)
    ok(/não tem ponto de confluência gravado/.test(r), 'Luís Alves: diz que não há ponto, não marca nada')
    r = await pedirAte(pg, 'de onde vem o traçado do Benedito?', /Traçado do Rio Benedito/)
    ok(/Base do OpenStreetMap: 06\/10\/2026/.test(r), 'origem do traçado: a data da base do OSM')
    r = await pedirAte(pg, 'o que fica a montante de Blumenau?', /montante|Rio do Sul/)
    ok(/Rio do Sul → Lontras/.test(r) && /não é previsão/.test(r), 'montante: pela árvore, com o aviso de que ligação não é previsão')
    r = await pedirAte(pg, 'quais leituras estão atrasadas?', /Réguas municipais|Não consegui|nenhuma leitura/)
    ok(/Réguas municipais|Não consegui|nenhuma leitura/.test(r), `leituras atrasadas: responde com a regra de idade ou diz que não conseguiu (${r.slice(0, 50)}…)`)
    await pedirAte(pg, 'gráfico de Blumenau', /gráfico/)
    await pg.waitForTimeout(1000)
    ok(pg.url().endsWith('#/acu/blumenau?secao=grafico'), `gráfico: abriu ${pg.url().split('#')[1]}`)
    ok(excecoes(erros).length === 0, `sem exceção de JavaScript (${excecoes(erros).join(' | ')})`)
    await b.close()
  }
  // 4. 3ª entrega: a rua no mapa.
  {
    const { b, pg, erros } = await abrir('#/itajai', { largura: w, altura: h })
    await entender(pg)
    let r = await pedirAte(pg, 'mostrar a Avenida 7 de Setembro em Itajaí', /destacada|Não consegui/)
    await pg.waitForTimeout(2500)
    ok(pg.url().includes('#/itajai?secao=manchas&rua=Av.7+de+Setembro'), `rua de Itajaí: o endereço leva a rua (${pg.url().split('#')[1]})`)
    ok(/Interseção com as manchas/.test(r) && /não quer dizer rua segura/.test(r), 'rua de Itajaí: interseção com os cenários e a ressalva')
    const traco = await pg.evaluate(() => [...document.querySelectorAll('.leaflet-rua-pane path, .leaflet-pane path')].some((p) => p.getAttribute('stroke') === '#ff3db8'))
    ok(traco, 'rua de Itajaí: o traçado magenta está no mapa')
    ok((await pg.getByText('rua selecionada, destaque de localização').count()) >= 1, 'rua de Itajaí: a legenda diz que é destaque, não risco')
    ok((await pg.getByText(/^Avenida 7 de Setembro$/).count()) >= 1, 'rua de Itajaí: o nome escrito sobre o mapa')
    await pedirAte(pg, 'mancha de 2008 na Avenida 7 de Setembro em Itajaí', /novembro de 2008/)
    await pg.waitForTimeout(2000)
    ok((await pg.locator('#mancha').inputValue()).includes('2008'), 'cenário de 2008 escolhido, a rua continua')
    ok((await pg.getByText(/Interseção com o cenário de novembro de 2008: 32% do trecho/).count()) >= 1, 'a interseção do cenário aparece embaixo do mapa')
    await pedirAte(pg, 'remover destaque', /Destaque da rua tirado/)
    await pg.waitForTimeout(1200)
    ok(!pg.url().includes('rua=') && (await pg.getByText('rua selecionada, destaque de localização').count()) === 0, 'remover destaque: a rua saiu do endereço e do mapa')
    r = await pedirAte(pg, 'mostrar a rua Adriano Kormann em Gaspar', /Localização aproximada|Não consegui/, 20000)
    await pg.waitForTimeout(1500)
    ok(pg.url().endsWith('#/monitor/gaspar') && /Localização aproximada/.test(r), 'rua de Gaspar: Monitor de Gaspar, com o aviso de localização aproximada')
    ok((await pg.getByText(/^Marca: Rua Adriano Kormann, Gaspar — localização aproximada/).count()) === 1, 'rua de Gaspar: a marca escrita na tela')
    r = await pedirAte(pg, 'mostrar a rua São Rafael em Blumenau', /Blumenau/)
    ok(/não publica a coordenada/.test(r) && pg.url().endsWith('#/monitor/gaspar'), 'Blumenau: só diz que não há coordenada, o mapa não muda')
    await pg.screenshot({ path: `${process.env.SAIDA || '.'}/chat-rua-gaspar-${w}.png` })
    ok(excecoes(erros).length === 0, `sem exceção de JavaScript (${excecoes(erros).join(' | ')})`)
    await b.close()
  }
  // 5. Página com chat próprio: a barra do topo some.
  {
    const { b, pg } = await abrir('#/perguntas', { largura: w, altura: h })
    ok((await caixas(pg).count()) === 1, '/perguntas: só o chat da página, sem a barra do topo')
    await b.close()
  }
}

console.log(`\n${falhas} falha(s).`)
process.exit(falhas ? 1 : 0)
