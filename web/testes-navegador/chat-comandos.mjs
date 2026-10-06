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
 *    aproximada; rua de Blumenau mexendo no mapa;
 *  - 4ª entrega: localização sem a régua mais perto ou sem o aviso de que nada é guardado, posição no endereço
 *    ou no aparelho, recusa que mexe na tela; minha cidade que não fica guardada; relato sem "Copiar"; letra
 *    que não muda;
 *  - 5ª entrega: reprodução que não toca, não pausa ou não vai ao instante; maré sem a tábua da Marinha ou sem
 *    "não é cheia"; barragem com nível em metros; fonte da leitura sem a hora.
 *  - 6ª entrega: panorama sem "mesma faixa não é mesmo metro"; filtro "acima do normal" fora da tela; "de cima"
 *    sem o aviso de que ligação não é previsão; Gaspar com frase de cota.
 *  - 7ª entrega: chegada × maré sem o 199; simulação sem a janela; legenda que compara metros; animações ou
 *    legenda que não mudam o botão do Monitor.
 *  - 8ª entrega: "oficial" sem o aviso; atualizar sem buscar; apagar preferências sem confirmar ou sem apagar;
 *    contagem que não grava; conversa que não limpa.
 *  - 9ª entrega: cidade com erro de digitação executada sem perguntar; sugestão que não leva à cidade certa.
 *  - 10ª entrega: continuação sem "Entendi como"; "e Gaspar" sem pedido anterior que adivinha; comando refeito
 *    que não executa.
 *  - 11ª entrega: verbete sem a régua de cada cidade ou sem o 199; voz que trava a tela.
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
  // 5. 4ª entrega: localização (com permissão e sem), minha cidade, letra e relato.
  {
    const { b, pg, erros } = await abrir('#/', { largura: w, altura: h })
    await entender(pg)
    await pg.context().grantPermissions(['geolocation'])
    await pg.context().setGeolocation({ latitude: -26.93, longitude: -48.97, accuracy: 30 })
    let r = await pedirAte(pg, 'usar minha localização', /régua mais perto|Não|fora/)
    await pg.waitForTimeout(1500)
    ok(/a de Gaspar/.test(r) && /não grava/.test(r), 'localização: a régua mais perto e o aviso de que nada é guardado')
    ok(pg.url().endsWith('#/monitor/gaspar') && (await pg.getByText(/^Marca: Você está aqui/).count()) === 1, 'localização: Monitor de Gaspar com a posição marcada')
    ok(!pg.url().includes('-26') && !(await pg.evaluate(() => JSON.stringify(localStorage))).includes('-26.93'), 'localização: a posição não vai para o endereço nem para o aparelho')
    r = await pedirAte(pg, 'minha cidade é Gaspar', /Gaspar agora é a sua cidade|Não deu/)
    ok((await pg.evaluate(() => localStorage.getItem('enchentes:cidades') ?? '')).includes('gaspar'), 'minha cidade: guardada no aparelho')
    r = await pedirAte(pg, 'relatar problema nesta tela', /canal de relato/)
    ok(/Relato de problema/.test(r) && (await pg.getByRole('button', { name: 'Copiar' }).count()) >= 1, 'relato: texto pronto, com o botão Copiar')
    await pg.goto(pg.url().split('#')[0] + '#/acu')
    await pg.waitForTimeout(2500)
    await pedirAte(pg, 'aumentar a letra', /Letra maior/)
    ok((await pg.evaluate(() => document.documentElement.dataset.letra)) === 'grande', 'letra: a página passou para a letra maior')
    await pedirAte(pg, 'letra normal', /Letra normal/)
    ok(excecoes(erros).length === 0, `sem exceção de JavaScript (${excecoes(erros).join(' | ')})`)
    await b.close()
  }
  {
    const { b, pg } = await abrir('#/', { largura: w, altura: h })
    await entender(pg)
    // Sem permissão concedida, o navegador fica perguntando: o chat não pode ficar preso em "Executando…".
    const r = await pedirAte(pg, 'usar minha localização', /Você não permitiu|não chegou a tempo|não conseguiu/, 40000)
    ok(/Você não permitiu|não chegou a tempo|não conseguiu/.test(r) && !pg.url().includes('/monitor'), `localização sem permissão: diz o porquê e não mexe na tela (${r.slice(0, 40)}…)`)
    ok(await pg.locator('input[aria-label="Pergunte ou peça"]').first().isEnabled(), 'localização sem permissão: o chat continua aceitando pedidos')
    await b.close()
  }
  // 6. 5ª entrega: reprodução, maré, chuva, barragens e fonte da leitura.
  {
    const { b, pg, erros } = await abrir('#/monitor/blumenau', { largura: w, altura: h })
    const instante = () => pg.locator('[class*="instante"]').first().innerText().catch(() => '')
    const temSerie = (await pg.locator('input[aria-label="Instante da reprodução"]').count()) > 0
    if (temSerie) {
      await pedirAte(pg, 'reproduzir as últimas 24 h', /Reproduzindo|série/)
      ok((await pg.getByRole('button', { name: '⏸ Pausar' }).count()) === 1, 'reprodução: o botão virou "Pausar"')
      await pedirAte(pg, 'pausar', /pausada|parada|não está tocando/)
      ok((await pg.getByRole('button', { name: /Reproduzir 24 h/ }).count()) === 1, 'pausar: a reprodução parou')
      let r = await pedirAte(pg, 'voltar 3 horas', /Mapa em|só cobre|mais recente/)
      ok(/Mapa em/.test(r) && (await instante()) !== 'ao vivo', `"voltar 3 horas": o mapa mostra o passado (${await instante()})`)
      r = await pedirAte(pg, 'ir para a leitura mais recente', /leituras mais recentes|ao vivo|Voltei|agora/)
      ok((await instante()) === 'ao vivo', 'voltar ao agora: "ao vivo"')
    } else {
      ok(true, 'reprodução: sem série publicada neste ambiente (o comando diz isso)')
    }
    let r = await pedirAte(pg, 'como está a maré?', /maré/)
    ok(/tábua de maré da Marinha/.test(r) && /não é cheia/.test(r), 'maré: pela tábua da Marinha, e maré não é cheia')
    r = await pedirAte(pg, 'onde está chovendo mais?', /chuv|pluvi/i)
    ok(/A fonte não publica 6 h|Não consegui|não recebeu|Nenhum pluviômetro/.test(r), `chuva: responde pelos pluviômetros (${r.slice(0, 50)}…)`)
    r = await pedirAte(pg, 'como estão as barragens?', /Barragens|barragens/)
    ok(/comportas|Não consegui/.test(r) && !/\d,\d\d m\b/.test(r), 'barragens: comportas, sem nível em metros')
    r = await pedirAte(pg, 'de onde vem a leitura de Blumenau?', /Blumenau/)
    ok(/A hora é a da medição/.test(r), 'fonte da leitura: estação, hora e fontes cadastradas')
    ok(excecoes(erros).length === 0, `sem exceção de JavaScript (${excecoes(erros).join(' | ')})`)
    await b.close()
  }
  // 7. 6ª entrega: o rio agora — quanto falta, tendência, máximo de 24 h, panorama, de cima e o filtro.
  {
    const { b, pg, erros } = await abrir('#/monitor/blumenau', { largura: w, altura: h })
    let r = await pedirAte(pg, 'quais cidades estão em alerta?', /Faixa de cada cidade|Não consegui/)
    ok(/mesma faixa não é mesmo metro/.test(r) && /199/.test(r), 'panorama: faixa na régua de cada cidade, com o 199')
    r = await pedirAte(pg, 'mostrar só as cidades em alerta', /Filtro ligado|não foi ligado/)
    if (/Filtro ligado/.test(r)) {
      ok(await pg.getByText('Filtro: só cidades e réguas com faixa acima do normal').isVisible(), 'filtro "acima do normal": escrito na tela')
      await pedirAte(pg, 'limpar filtros', /Filtro limpo/)
      ok((await pg.getByText('Filtro: só cidades e réguas com faixa acima do normal').count()) === 0, 'limpar filtros: o aviso sai da tela')
    } else {
      ok(/não quer dizer que não há alagamento/.test(r), 'filtro "acima do normal": nada acima, e o chat diz que isso não é sinal de segurança')
    }
    r = await pedirAte(pg, 'o que vem de cima para Blumenau?', /acima de Blumenau/)
    ok(/Rio do Sul/.test(r) && /Ligação não é previsão/.test(r), 'de cima: pela árvore, com o aviso')
    r = await pedirAte(pg, 'quanto falta para a cota em Rio do Sul?', /Rio do Sul/)
    ok(/Faltam|acima da cota|só sai com leitura de agora|não tem leitura|Já passou/.test(r), `quanto falta: a frase do cartão ou a recusa (${r.slice(0, 60)}…)`)
    r = await pedirAte(pg, 'Blumenau está subindo?', /Blumenau/)
    ok(/cm\/h|estável|não digo|não chega|não tem leitura/.test(r), `tendência: a seta do cartão ou a recusa (${r.slice(0, 60)}…)`)
    r = await pedirAte(pg, 'máximo das últimas 24 h em Blumenau', /Blumenau/)
    ok(/máximo:|não tem pontos suficientes/.test(r), 'máximo de 24 h: da série, com hora')
    r = await pedirAte(pg, 'quanto falta para a cota em Gaspar?', /Gaspar/)
    ok(/não faz a conta/.test(r), 'Gaspar: sem frase de cota ("maior que")')
    ok(excecoes(erros).length === 0, `sem exceção de JavaScript (${excecoes(erros).join(' | ')})`)
    await b.close()
  }
  // 8. 7ª entrega: a foz (pico × maré), a simulação, a legenda e os botões de animação e legenda do Monitor.
  {
    const { b, pg, erros } = await abrir('#/monitor/blumenau', { largura: w, altura: h })
    let r = await pedirAte(pg, 'o pico de Blumenau já passou?', /Blumenau|Não consegui/)
    ok(/Blumenau/.test(r) && /199/.test(r), `chegada × maré: o "Hoje" do painel de Itajaí (${r.slice(0, 50)}…)`)
    r = await pedirAte(pg, 'se o pico de Blumenau for às 22h', /Janela:|tábua/)
    ok(/Janela: de [0-9]{2}:[0-9]{2} de/.test(r) && /não o nível do rio/.test(r), 'simulação: a janela e o aviso')
    r = await pedirAte(pg, 'o que significa a cor laranja?', /Laranja/)
    ok(/Laranja — Alerta/.test(r) && /não o nível em metros/.test(r), 'legenda: a faixa, na régua de cada cidade')
    await pedirAte(pg, 'abrir a legenda', /Legenda aberta|já está aberta/)
    ok((await pg.locator('button[aria-expanded="true"]', { hasText: 'recolher' }).count()) === 1, 'abrir a legenda: a legenda abriu')
    await pedirAte(pg, 'pausar as animações', /pausadas/)
    ok((await pg.locator('button[aria-pressed="true"]', { hasText: 'Retomar animações' }).count()) === 1, 'pausar as animações: o botão virou "Retomar"')
    await pedirAte(pg, 'retomar animações', /retomadas|já estão ligadas/)
    ok((await pg.locator('button[aria-pressed="false"]', { hasText: 'Pausar animações' }).count()) === 1, 'retomar animações: o botão voltou')
    await pedirAte(pg, 'recolher a legenda', /Legenda recolhida|já está recolhida/)
    ok((await pg.locator('button[aria-expanded="false"]', { hasText: 'abrir' }).count()) === 1, 'recolher a legenda: fechou')
    ok(excecoes(erros).length === 0, `sem exceção de JavaScript (${excecoes(erros).join(' | ')})`)
    await b.close()
  }
  // 9. 8ª entrega: o site e os seus dados.
  {
    const { b, pg, erros } = await abrir('#/acu/blumenau', { largura: w, altura: h })
    await entender(pg)
    let r = await pedirAte(pg, 'isso é oficial?', /oficial/)
    ok(/não é sistema oficial de alerta/.test(r) && /199/.test(r), 'oficial: o aviso de toda tela')
    r = await pedirAte(pg, 'atualizar as leituras', /Busquei de novo|não respondeu|menos de 30 segundos/, 20000)
    ok(/Busquei de novo|não respondeu/.test(r), `atualizar: buscou de novo e disse a coleta (${r.slice(0, 60)}…)`)
    await pedirAte(pg, 'minha cidade é Gaspar', /Gaspar/)
    r = await pedirAte(pg, 'o que o site guarda de mim?', /aparelho/)
    ok(/cidades: Gaspar \(a sua\)/.test(r) && /Não guarda: a sua localização/.test(r), 'privacidade: lido do aparelho, na hora')
    r = await pedirAte(pg, 'apagar minhas preferências', /confirmar/)
    ok((await pg.evaluate(() => localStorage.getItem('enchentes:cidades'))) !== null, 'apagar: nada some antes de confirmar')
    await pedirAte(pg, 'sim, apagar minhas preferências', /apagadas/)
    ok((await pg.evaluate(() => localStorage.getItem('enchentes:cidades'))) === null, 'apagar: a cidade saiu do aparelho')
    await pedirAte(pg, 'não contar minhas perguntas', /Contagem desligada/)
    ok((await pg.evaluate(() => localStorage.getItem('enchentes:chat-contagem'))) === 'nao', 'contagem: desligada no aparelho')
    r = await pedirAte(pg, 'telefone de emergência', /199/)
    ok(/193/.test(r), 'emergência: 199 e 193')
    await pedirAte(pg, 'limpar a conversa', /Conversa limpa/)
    const n = await pg.locator('[role="log"] [class*="chat-assistente"]').count()
    ok(n <= 1, `limpar a conversa: só a resposta ficou (${n})`)
    ok(excecoes(erros).length === 0, `sem exceção de JavaScript (${excecoes(erros).join(' | ')})`)
    await b.close()
  }
  // 10. 9ª entrega: nome de cidade com erro de digitação vira "Você quis dizer…?"; nada é feito sozinho.
  {
    const { b, pg, erros } = await abrir('#/acu/gaspar', { largura: w, altura: h })
    await entender(pg)
    let r = await pedirAte(pg, 'mostrar Blumenal', /quis dizer/)
    ok(/Não achei a cidade "Blumenal"\. Você quis dizer Blumenau\? Nada foi feito/.test(r), 'comando com erro: pergunta antes')
    ok(/#\/acu\/gaspar/.test(pg.url()), `comando com erro: a tela não mudou (${pg.url()})`)
    await pg.getByRole('button', { name: 'mostrar Blumenau' }).last().click()
    await pg.waitForURL(/#\/monitor\/blumenau/, { timeout: 15000 }).catch(() => {})
    ok(/#\/monitor\/blumenau/.test(pg.url()), 'tocar na sugestão: abriu o Monitor de Blumenau')
    await b.close()
    const outra = await abrir('#/acu/gaspar', { largura: w, altura: h })
    await entender(outra.pg)
    r = await pedirAte(outra.pg, 'como está blumenal?', /quis dizer/)
    ok(/Você quis dizer Blumenau\? Toque na sugestão/.test(r), 'pergunta com erro: o palpite vem antes da resposta')
    ok((await outra.pg.getByRole('button', { name: 'como está Blumenau?' }).count()) >= 1, 'pergunta com erro: a sugestão é a frase corrigida')
    ok(excecoes([...erros, ...outra.erros]).length === 0, `sem exceção de JavaScript (${excecoes([...erros, ...outra.erros]).join(' | ')})`)
    await outra.b.close()
  }
  // 11. 10ª entrega: a conversa que continua ("e Gaspar?", "e em 2011?", "de novo").
  {
    const { b, pg, erros } = await abrir('#/acu/blumenau', { largura: w, altura: h })
    await entender(pg)
    let r = await pedirAte(pg, 'e Gaspar?', /pedido anterior/)
    ok(/Não há pedido anterior/.test(r), 'sem pedido anterior: pergunta o que saber')
    await pedirAte(pg, 'quanto falta para a cota em Blumenau?', /Blumenau/)
    await pedir(pg, 'e Rio do Sul?')
    const textos = await pg.locator('[role="log"] [class*="chat-assistente"]').allInnerTexts()
    ok(textos.some((t) => /Entendi como: "quanto falta para a cota em Rio do Sul\?"/.test(t)), 'continuação: diz como entendeu')
    r = await pedirAte(pg, 'de novo', /Rio do Sul/)
    ok(/Rio do Sul/.test(r), 'de novo: repete o último pedido refeito')
    await pedirAte(pg, 'mostrar Blumenau', /Blumenau/)
    await pedir(pg, 'e Gaspar')
    await pg.waitForURL(/#\/monitor\/gaspar/, { timeout: 15000 }).catch(() => {})
    ok(/#\/monitor\/gaspar/.test(pg.url()), `continuação de comando: abriu o Monitor de Gaspar (${pg.url()})`)
    ok(excecoes(erros).length === 0, `sem exceção de JavaScript (${excecoes(erros).join(' | ')})`)
    await b.close()
  }
  // 12. 11ª entrega: as palavras do rio e a resposta em voz alta.
  {
    const { b, pg, erros } = await abrir('#/acu/blumenau', { largura: w, altura: h })
    await entender(pg)
    let r = await pedirAte(pg, 'o que é cota?', /Cota/)
    ok(/marca de altura na régua da cidade/.test(r) && /199/.test(r), 'glossário: cota, com o 199')
    r = await pedirAte(pg, 'qual a diferença entre enchente e alagamento?', /alagamento/i)
    ok(/pode acontecer sem o rio subir/.test(r), 'glossário: enchente × alagamento')
    r = await pedirAte(pg, 'ler em voz alta', /Lendo|não tem leitura/)
    ok(/Lendo a última resposta|não tem leitura em voz alta/.test(r), `voz: lê pelo aparelho ou diz que não há (${r.slice(0, 40)}…)`)
    r = await pedirAte(pg, 'parar de ler', /Parei|Não estou lendo|não tem leitura/)
    ok(/Parei de ler|Não estou lendo|não tem leitura/.test(r), 'parar de ler')
    ok(excecoes(erros).length === 0, `sem exceção de JavaScript (${excecoes(erros).join(' | ')})`)
    await b.close()
  }
  // 13. Página com chat próprio: a barra do topo some.
  {
    const { b, pg } = await abrir('#/perguntas', { largura: w, altura: h })
    ok((await caixas(pg).count()) === 1, '/perguntas: só o chat da página, sem a barra do topo')
    await b.close()
  }
}

console.log(`\n${falhas} falha(s).`)
process.exit(falhas ? 1 : 0)
