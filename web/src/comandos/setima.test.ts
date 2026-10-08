/**
 * 7ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): a foz (chegada do pico de Blumenau × maré em
 * Itajaí), a simulação com horário informado, a legenda do mapa e os botões de animação e legenda do Monitor.
 */
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { executar, limparRetratos, type Ambiente, type DadosDoChat } from './executar'
import { textoDeAjuda } from './ajuda'
import { instanteDoPico, textoChegadaItajai, textoLegenda, textoSimulacao } from './foz'
import { hojeEmItajai } from '../logica/hojeEmItajai'
import { situacaoDoPico } from '../logica/picoBlumenau'
import { entradaBrasilia, simularChegada } from '../logica/simulacaoChegada'
import type { AoVivo } from '../dados/usarAoVivo'
import type { NivelSc } from '../dados/nivelSc'
import type { PontoSerie } from '../dados/serie'
import type { Cidade, TabuaMare } from '../dados/tipos'
import type { ControleMonitor, Retrato } from './ponte'
import type { Contexto, Fundo } from './tipos'

const ler = (c: string) => JSON.parse(readFileSync(new URL(`../../../data/${c}`, import.meta.url), 'utf8'))
const estacoes = ler('estacoes.json')
const tabua = ler('mare-itajai.json') as TabuaMare
const REF = ler('historico-chegada-itajai.json').referencia_estudo as { horas_min: number; horas_max: number }
const cat = catalogoDoCadastro(estacoes)
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const AGORA = new Date('2026-10-06T18:00:00Z') // 15h00 em Brasília
const H = 3_600_000
const blumenau = (estacoes.rios['itajai-acu'].cidades as Cidade[]).find((c) => c.id === 'blumenau')!
const COTA = { valor: 3, nome: 'Observação' }

const passos = (texto: string, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', `"${texto}" devia virar comando, veio ${JSON.stringify(r)}`)
  return r.passos
}

/** Uma série de 15 em 15 min, das `horas` atrás até agora, com o nível dado por `nivel(h)` (h = horas atrás). */
const serie = (horas: number, nivel: (h: number) => number): PontoSerie[] =>
  Array.from({ length: horas * 4 + 1 }, (_, i) => {
    const h = horas - i / 4
    return { medidoEm: new Date(AGORA.getTime() - h * H), nivel_m: Math.round(nivel(h) * 1000) / 1000, regua: 'Blumenau (AlertaBlu)' }
  })
// Sobe de 3 m (30 h atrás) a 6 m (10 h atrás, 05h00) e desce a 5 m agora.
const passou = serie(30, (h) => (h >= 10 ? 3 + ((30 - h) / 20) * 3 : 6 - ((10 - h) / 10) * 1))
const subindo = serie(30, (h) => 3 + ((30 - h) / 30) * 3)
const baixo = serie(30, () => 2)
const caindoDesdeOInicio = serie(30, (h) => 3 + (h / 30) * 3)

// ---------------------------------------------------------------- interpretar

test('frases da 7ª entrega; "pausar a animação" continua sendo a reprodução', () => {
  assert.deepEqual(passos('o pico de Blumenau já passou?'), [{ tipo: 'chegada_itajai' }])
  assert.deepEqual(passos('quando a cheia chega em Itajaí?'), [{ tipo: 'chegada_itajai' }])
  assert.deepEqual(passos('a cheia vai pegar maré alta?'), [{ tipo: 'chegada_itajai' }])
  assert.deepEqual(passos('pico x maré'), [{ tipo: 'chegada_itajai' }])
  assert.deepEqual(passos('se o pico de Blumenau for às 22h'), [{ tipo: 'simular_chegada', hora: 22 }])
  assert.deepEqual(passos('se o pico em Blumenau for amanhã às 3h30, quando chega em Itajaí?'), [{ tipo: 'simular_chegada', hora: 3, minuto: 30, dia: 'amanha' }])
  assert.deepEqual(passos('o que significa a cor laranja?'), [{ tipo: 'legenda', tema: 'alerta' }])
  assert.deepEqual(passos('o que quer dizer verde claro?'), [{ tipo: 'legenda', tema: 'monitoramento' }])
  assert.deepEqual(passos('o que é alerta máximo?'), [{ tipo: 'legenda', tema: 'inundacao' }])
  assert.deepEqual(passos('o que significa o roxo no mapa?'), [{ tipo: 'legenda', tema: 'violeta' }])
  assert.deepEqual(passos('por que o trecho está tracejado?'), [{ tipo: 'legenda', tema: 'tracejado' }])
  assert.deepEqual(passos('por que a água se mexe?'), [{ tipo: 'legenda', tema: 'ondas' }])
  assert.deepEqual(passos('explicar as cores'), [{ tipo: 'legenda', tema: 'cores' }])
  assert.deepEqual(passos('pausar as animações'), [{ tipo: 'animacoes', acao: 'pausar' }])
  assert.deepEqual(passos('retomar animações'), [{ tipo: 'animacoes', acao: 'retomar' }])
  assert.deepEqual(passos('abrir a legenda'), [{ tipo: 'legenda_mapa', acao: 'abrir' }])
  assert.deepEqual(passos('recolher a legenda'), [{ tipo: 'legenda_mapa', acao: 'fechar' }])
  assert.deepEqual(passos('pausar a animação'), [{ tipo: 'reproducao', acao: 'pausar' }])
  // "Por que essa régua está cinza?" continua sendo a da cidade (1ª entrega).
  assert.deepEqual(passos('por que essa régua está cinza?'), [{ tipo: 'por_que_cinza' }])
  for (const q of ['vai alagar em Itajaí?', 'devo sair de casa?', 'o pico vai ser maior que 2011?']) assert.equal(interpretar(q, cat, fora), null, q)
})

// ---------------------------------------------------------------- a decisão do painel (a mesma da tela)

test('o "Hoje" de Itajaí: cada ramo do painel, pela função que a tela também usa', () => {
  const h = (pontos: PontoSerie[]) => hojeEmItajai(situacaoDoPico(pontos, AGORA), COTA, REF, tabua, AGORA)
  assert.equal(h([]).tipo, 'sem-dado')
  assert.equal(h(baixo).tipo, 'abaixo-da-cota')
  const s = h(subindo)
  assert.equal(s.tipo, 'subindo')
  const p = h(passou)
  assert.equal(p.tipo, 'passou')
  assert.ok(p.tipo === 'passou' && p.pico.nivel_m === 6 && !p.janelaPassou)
  assert.equal(h(caindoDesdeOInicio).tipo, 'nao-confirmado')
  // A janela do pico que passou começa no platô + 12 h, como no painel.
  if (p.tipo === 'passou' && !('erro' in p.resultado)) {
    assert.equal(p.resultado.inicio.getTime(), p.platoInicio.getTime() + REF.horas_min * H)
  }
})

test('texto da chegada × maré: o pico, a janela, as marés dentro dela e o aviso', () => {
  const t = (pontos: PontoSerie[]) => textoChegadaItajai(hojeEmItajai(situacaoDoPico(pontos, AGORA), COTA, REF, tabua, AGORA), { cota: COTA, referencia: REF, agora: AGORA })
  const p = t(passou)
  assert.match(p, /^O pico já passou por Blumenau: 6,00 m às 05:00 de 06\/10/)
  assert.match(p, /Pela referência de estudo \(12 a 17 h\), o pico chegaria a Itajaí:\nJanela: de 16:45 de 06\/10 a /)
  // Tábua da UNIVALI (08/10/2026): baixa-mar às 18:35 (a Marinha dava 18:49) e sem altura, porque a planilha não declara a referência.\n  assert.match(p, /maré baixa às 18:35 de 06\/10 \(sem altura na tábua\)/)
  assert.match(p, /não previsão[^]*não o nível do rio[^]*199/)
  const s = t(subindo)
  assert.match(s, /^Blumenau ainda está subindo: 6,00 m às 15:00 \(\+10 cm\/h\)\. O pico ainda não aconteceu/)
  assert.match(s, /Se o pico fosse agora, pela referência de estudo \(12 a 17 h\), chegaria a Itajaí:\nJanela: de 03:00 de 07\/10 a 08:00 de 07\/10/)
  assert.match(t(baixo), /abaixo da cota de Observação \(3,00 m\)[^]*não há pico de cheia descendo agora/)
  assert.match(t(caindoDesdeOInicio), /^Pico não confirmado\./)
  assert.match(t([]), /Sem leitura recente de Blumenau/)
})

test('simulação com horário informado: hora de Brasília, hoje por padrão; janela vencida é dita', () => {
  assert.equal(instanteDoPico({ hora: 22 }, AGORA)?.toISOString(), '2026-10-07T01:00:00.000Z')
  assert.equal(instanteDoPico({ hora: 3, minuto: 30, dia: 'amanha' }, AGORA)?.toISOString(), '2026-10-07T06:30:00.000Z')
  assert.equal(instanteDoPico({ hora: 25 }, AGORA), null)
  const pico = instanteDoPico({ hora: 10 }, AGORA)!
  const r = simularChegada(entradaBrasilia(pico), REF.horas_min, REF.horas_max, tabua)
  const t = textoSimulacao(pico, r, REF, AGORA)
  assert.match(t, /^Se o pico em Blumenau for às 10:00 de 06\/10, pela referência de estudo \(12 a 17 h\), chegaria a Itajaí:\nJanela: de 22:00 de 06\/10 a 03:00 de 07\/10/)
  assert.match(t, /maré alta às 23:05 de 06\/10 \(sem altura na tábua\)/)
  assert.match(t, /Há preamar dentro da janela simulada\. A coincidência de horários não determina a altura/)
  const velho = instanteDoPico({ hora: 1, dia: 'ontem' }, AGORA)!
  assert.match(textoSimulacao(velho, simularChegada(entradaBrasilia(velho), REF.horas_min, REF.horas_max, tabua), REF, AGORA), /teria chegado[^]*Essa janela já terminou/)
})

test('legenda: os textos de faixas.json e da legenda do Monitor; cor é faixa, nunca metro', () => {
  assert.match(textoLegenda('alerta'), /^Laranja — Alerta: Nível na faixa de alerta desta régua\. Siga a Defesa Civil; ligue 199 em emergência\.\nA cor é a faixa de cada cidade na régua dela/)
  assert.match(textoLegenda('sem-dado'), /não conclua que está seguro[^]*não é seguro, é sem afirmação/)
  assert.match(textoLegenda('ondas'), /velocidade visual constante\. Não representam a velocidade da água/)
  assert.match(textoLegenda('violeta'), /zero próprio[^]*não vira faixa/)
  const todas = textoLegenda('cores')
  for (const c of ['Verde —', 'Verde-claro —', 'Amarelo —', 'Laranja —', 'Vermelho — Inundação / Emergência', 'Cinza —', 'Pino pontilhado', 'Violeta']) assert.ok(todas.includes(c), c)
  assert.match(todas, /não é alerta oficial[^]*199/)
})

// ---------------------------------------------------------------- executar

function monitorFalso(cidade: string | null) {
  const chamadas: string[] = []
  const c: ControleMonitor = {
    cidade,
    pronto: true,
    estado: () => ({ cidade, cidadeNome: cidade, regua: null, reguas: [], fundo: 'escuro' as Fundo, camada: null, camadasDisponiveis: [], reproducao: null }),
    escolherRegua: () => ({ ok: true, texto: '' }),
    enquadrarCidade: () => ({ ok: true, texto: '' }),
    zoom: () => ({ ok: true, texto: '' }),
    verBacia: () => ({ ok: true, texto: '' }),
    fundo: () => ({ ok: true, texto: '' }),
    camada: () => ({ ok: true, texto: '' }),
    aoVivo: () => ({ ok: true, texto: '' }),
    animacoes: (a) => {
      chamadas.push(`animacoes:${a}`)
      return { ok: true, texto: `animações ${a}` }
    },
    legendaDoMapa: (a) => {
      chamadas.push(`legenda:${a}`)
      return { ok: true, texto: `legenda ${a}` }
    },
    explicar: () => null,
    retrato: (): Retrato => ({ rota: `/monitor/${cidade}`, cidade }),
    restaurar: () => ({ ok: true, texto: 'ok' }),
  }
  return { c, chamadas }
}

const aoVivo: AoVivo = {
  tempoReal: { situacao: 'ok', leituras: [], chuva: [], chuvaOk: true, coletadoEm: AGORA, fonte: null },
  nivelSc: new Map() as NivelSc,
  serie: { situacao: 'ok', series: { 'itajai-acu': { blumenau: passou } }, resgates: {}, janelaHoras: 48, geradoEm: AGORA },
  agora: AGORA,
}
const dados: DadosDoChat = {
  aoVivo: async () => aoVivo,
  cidade: (id) => (id === 'blumenau' ? { cidade: blumenau, rioId: 'itajai-acu' } : null),
  reguasNoMapa: () => [],
  tracado: async () => null,
  base: () => '',
  mare: () => tabua,
  referenciaChegada: () => REF,
}

function ambiente(rota = '/') {
  let atual: ReturnType<typeof monitorFalso> | null = null
  let r = rota
  const navegacoes: string[] = []
  const amb: Ambiente = {
    navegar: (para) => {
      navegacoes.push(para)
      r = para
      const m = para.match(/^\/monitor(?:\/([a-z-]+))?/)
      atual = m ? monitorFalso(m[1] ?? null) : null
    },
    rotaAtual: () => r,
    monitor: () => atual?.c ?? null,
    esperarMonitor: async (cid) => (atual && atual.c.cidade === cid ? atual.c : null),
    dados,
  }
  return { amb, navegacoes, monitor: () => atual }
}
const ajuda = () => textoDeAjuda(fora, null)
const rodar = (texto: string, amb: Ambiente, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', texto)
  return executar(r.passos, amb, cat, ctx, ajuda)
}

beforeEach(() => limparRetratos())

test('executor: chegada, simulação e legenda respondem em texto, sem mexer no mapa', async () => {
  const { amb, navegacoes } = ambiente()
  const c = await rodar('o pico de Blumenau já passou?', amb)
  assert.match(c.texto, /O pico já passou por Blumenau: 6,00 m às 05:00 de 06\/10/)
  assert.equal(c.link?.para, '/itajai')
  assert.match((await rodar('se o pico de Blumenau for às 22h', amb)).texto, /Se o pico em Blumenau for às 22:00 de 06\/10/)
  assert.match((await rodar('o que significa a cor amarelo?', amb)).texto, /^Amarelo — Atenção/)
  assert.deepEqual(navegacoes, [])
})

test('executor: animações e legenda abrem o Monitor e usam a ponte', async () => {
  const { amb, navegacoes, monitor } = ambiente()
  const s = await rodar('pausar as animações', amb)
  assert.deepEqual(navegacoes, ['/monitor'])
  assert.match(s.texto, /animações pausar/)
  await rodar('abrir a legenda', amb, { cidadeAtual: null, naMonitor: true, reguaAtual: null })
  assert.deepEqual(monitor()!.chamadas, ['animacoes:pausar', 'legenda:abrir'])
})

test('a ajuda lista os pedidos da 7ª entrega', () => {
  const t = textoDeAjuda({ cidadeAtual: null, naMonitor: true, reguaAtual: null }, null).texto
  for (const f of ['o pico de Blumenau já passou?', 'se o pico de Blumenau for às 22h', 'o que significa a cor laranja?', 'pausar as animações', 'abrir a legenda']) assert.ok(t.includes(f), f)
})

test('as perguntas do morador: "a água chega na hora da maré alta?" e as duas juntas vão para chegada × maré', () => {
  for (const q of [
    'a água chega na hora da maré alta?',
    'a água de Blumenau chega em Itajaí na maré alta?',
    'a cheia vai chegar junto com a maré alta?',
    'quanto tempo chega a água de Blumenau até Itajaí, a água chega na hora da maré alta?',
    'o pico pega a preamar?',
  ])
    assert.deepEqual(passos(q), [{ tipo: 'chegada_itajai' }], q)
  // Sem a cheia na frase, é a maré (5ª entrega) ou o tempo de descida (motor), como antes.
  assert.deepEqual(passos('como está a maré?'), [{ tipo: 'mare' }])
  assert.equal(interpretar('quanto tempo chega a água de Blumenau até Itajaí?', cat, fora), null)
  assert.notDeepEqual(interpretar('quando é a maré alta?', cat, fora), { tipo: 'comandos', passos: [{ tipo: 'chegada_itajai' }] })
  // Sem pico para pôr na janela, a resposta ainda diz quanto tempo a água leva.
  const t = (pontos: PontoSerie[]) => textoChegadaItajai(hojeEmItajai(situacaoDoPico(pontos, AGORA), COTA, REF, tabua, AGORA), { cota: COTA, referencia: REF, agora: AGORA })
  for (const x of [t([]), t(baixo)]) assert.match(x, /leva de 12 a 17 h de Blumenau até Itajaí[^]*não é previsão[^]*199/)
})
