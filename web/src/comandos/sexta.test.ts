/**
 * 6ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): o rio agora, de cima a baixo — quanto falta para
 * a cota, tendência, máximo das 24 h, panorama da bacia, o que vem de cima e o filtro "acima do normal".
 */
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { executar, limparRetratos, type Ambiente, type DadosDoChat } from './executar'
import { textoDeAjuda } from './ajuda'
import { textoDeCima, textoMaximo24h, textoPanorama, textoQuantoFalta, textoSubindoOuBaixando, type CidadeAgora } from './rioAgora'
import { faixaAcimaDoNormal } from '../logica/filtroSemLeitura'
import type { LeituraAoVivo } from '../dados/tempoReal'
import { estadoDaCidade, type AoVivo } from '../dados/usarAoVivo'
import type { NivelSc } from '../dados/nivelSc'
import type { PontoSerie } from '../dados/serie'
import type { Cidade, Trecho, TrechoExperimental } from '../dados/tipos'
import type { ControleMonitor, FiltroMonitor, Retrato } from './ponte'
import type { Contexto, Fundo } from './tipos'

const ler = (c: string) => JSON.parse(readFileSync(new URL(`../../../data/${c}`, import.meta.url), 'utf8'))
const estacoes = ler('estacoes.json')
const transito = ler('transito.json') as { trechos: Trecho[]; trechos_experimentais: TrechoExperimental[] }
const cat = catalogoDoCadastro(estacoes)
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const AGORA = new Date('2026-10-06T18:00:00Z') // 15h00 em Brasília
const minAtras = (m: number) => new Date(AGORA.getTime() - m * 60_000)

const cidadeDoCadastro = (id: string): { cidade: Cidade; rioId: string } | null => {
  for (const [rioId, r] of Object.entries(estacoes.rios as Record<string, { cidades: Cidade[] }>)) {
    const c = r.cidades.find((x) => x.id === id)
    if (c) return { cidade: c, rioId }
  }
  return null
}

const passos = (texto: string, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', `"${texto}" devia virar comando, veio ${JSON.stringify(r)}`)
  return r.passos
}

const leitura = (cidade: string, nivel_m: number, min: number): LeituraAoVivo => ({
  estacao: cidade === 'blumenau' ? 'Blumenau' : cidade,
  rio: 'itajai-acu',
  cidade,
  nivel_m,
  medidoEm: minAtras(min),
  resgateDe: null,
})
// Blumenau sobe 3 cm a cada 15 min (12 cm/h) por quase 24 h, até 6,40 m às 14h50.
const serieBlumenau: PontoSerie[] = Array.from({ length: 96 }, (_, j) => ({
  medidoEm: minAtras(10 + 15 * j),
  nivel_m: Math.round((6.4 - 0.03 * j) * 100) / 100,
  regua: 'Blumenau',
})).reverse()

const aoVivo: AoVivo = {
  tempoReal: {
    situacao: 'ok',
    leituras: [leitura('blumenau', 6.4, 10), leitura('rio-do-sul', 4.8, 20), leitura('gaspar', 4.0, 15), leitura('taio', 5.5, 300)],
    chuva: [],
    chuvaOk: true,
    coletadoEm: AGORA,
    fonte: null,
  },
  nivelSc: new Map() as NivelSc,
  serie: { situacao: 'ok', series: { 'itajai-acu': { blumenau: serieBlumenau } }, resgates: {}, janelaHoras: 48, geradoEm: AGORA },
  agora: AGORA,
}
const agoraDe = (id: string): CidadeAgora => {
  const c = cidadeDoCadastro(id)!
  return { cidade: c.cidade, estado: estadoDaCidade(c.cidade, c.rioId, aoVivo) }
}

// ---------------------------------------------------------------- interpretar

test('frases da 6ª entrega; previsão continua fora dos comandos', () => {
  assert.deepEqual(passos('quanto falta para a cota de alerta em Blumenau?'), [{ tipo: 'quanto_falta', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quanto falta para a próxima cota?'), [{ tipo: 'quanto_falta' }])
  assert.deepEqual(passos('quanto falta em Rio do Sul'), [{ tipo: 'quanto_falta', cidadeId: 'rio-do-sul' }])
  assert.deepEqual(passos('o rio está subindo ou descendo?'), [{ tipo: 'tendencia' }])
  assert.deepEqual(passos('Blumenau está subindo?'), [{ tipo: 'tendencia', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('o rio está baixando em Gaspar?'), [{ tipo: 'tendencia', cidadeId: 'gaspar' }])
  assert.deepEqual(passos('qual a tendência em Brusque?'), [{ tipo: 'tendencia', cidadeId: 'brusque' }])
  assert.deepEqual(passos('qual foi o máximo das últimas 24 h em Blumenau?'), [{ tipo: 'maximo_24h', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('pico de hoje'), [{ tipo: 'maximo_24h' }])
  assert.deepEqual(passos('quais cidades estão em alerta?'), [{ tipo: 'panorama' }])
  assert.deepEqual(passos('como está a bacia agora?'), [{ tipo: 'panorama' }])
  assert.deepEqual(passos('o que vem de cima para Blumenau?'), [{ tipo: 'de_cima', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('como estão as cidades de cima?'), [{ tipo: 'de_cima' }])
  assert.deepEqual(passos('mostrar só as cidades em alerta'), [{ tipo: 'filtro', filtro: 'acima_do_normal' }])
  // A maré continua sendo da 5ª entrega; a previsão continua no motor, com a barreira do presente.
  assert.deepEqual(passos('a maré está subindo?'), [{ tipo: 'mare' }])
  for (const q of ['o rio vai subir?', 'quando vai chegar na cota de alerta?', 'maior cheia de Blumenau', 'quanto falta para a rua XV alagar?']) {
    assert.equal(interpretar(q, cat, fora), null, q)
  }
  // Cidade fora do cadastro não vira comando com cidade errada.
  assert.equal(interpretar('Pomerode está subindo?', cat, fora), null)
})

// ---------------------------------------------------------------- textos

test('quanto falta: a frase do cartão "Agora", com o nome da Defesa Civil; nunca sobre leitura velha', () => {
  const b = agoraDe('blumenau')
  const t = textoQuantoFalta(b.cidade, b.estado, AGORA)
  assert.match(t, /Régua de Blumenau: 6,40 m, medido às 14:50 de 06\/10 \(há 10 min\)\./)
  assert.match(t, /Está 40 cm acima da cota de Alerta \(6,00 m\)\. Faltam 1,60 m para a cota de Alerta Máximo \(8,00 m\)\./)
  assert.match(t, /não previsão/)
  const taio = agoraDe('taio')
  assert.match(textoQuantoFalta(taio.cidade, taio.estado, AGORA), /só sai com leitura de agora/)
  const g = agoraDe('gaspar')
  assert.match(textoQuantoFalta(g.cidade, g.estado, AGORA), /"maior que"[^]*não faz a conta/)
  const asc = agoraDe('ascurra')
  assert.match(textoQuantoFalta(asc.cidade, asc.estado, AGORA), /C18/)
  const ita = agoraDe('itajai')
  assert.match(textoQuantoFalta(ita.cidade, ita.estado, AGORA), /várias réguas/)
  const ind = agoraDe('indaial')
  assert.match(textoQuantoFalta(ind.cidade, ind.estado, AGORA), /não tem leitura/)
})

test('tendência: a seta do cartão (D7); sem série que case com a leitura, não diz', () => {
  const b = agoraDe('blumenau')
  assert.match(textoSubindoOuBaixando(b.cidade, b.estado, AGORA), /Régua de Blumenau: ▲ subindo 12 cm\/h na última hora medida, até 14:50 \(6,40 m\)/)
  const r = agoraDe('rio-do-sul')
  assert.match(textoSubindoOuBaixando(r.cidade, r.estado, AGORA), /não chega até a leitura de 14:40/)
  const taio = agoraDe('taio')
  assert.match(textoSubindoOuBaixando(taio.cidade, taio.estado, AGORA), /não digo se o rio sobe ou desce agora/)
  const ita = agoraDe('itajai')
  assert.match(textoSubindoOuBaixando(ita.cidade, ita.estado, AGORA), /várias réguas/)
})

test('máximo das 24 h: da série de uma régua, com a hora de cada ponto', () => {
  const t = textoMaximo24h({ nome: 'Blumenau', cidadeId: 'blumenau', pontos: serieBlumenau, publicacao: null, agora: AGORA })
  assert.match(t, /• máximo: 6,40 m às 14:50 de 06\/10;/)
  assert.match(t, /• mínimo: 3,55 m às 15:05 de 05\/10;/)
  assert.match(t, /do primeiro ao último ponto: \+2,85 m/)
  assert.match(t, /régua de Blumenau: não compare com outras cidades/)
  assert.match(textoMaximo24h({ nome: 'Taió', cidadeId: 'taio', pontos: [], publicacao: null, agora: AGORA }), /não tem pontos suficientes/)
  // Ponto mais velho que 24 h não entra.
  const velho = [{ medidoEm: minAtras(60 * 30), nivel_m: 9.9, regua: 'Blumenau' }, ...serieBlumenau]
  assert.doesNotMatch(textoMaximo24h({ nome: 'Blumenau', cidadeId: 'blumenau', pontos: velho, publicacao: null, agora: AGORA }), /9,90/)
})

test('panorama: faixa na régua de cada cidade, da mais alta para a mais baixa; cinza à parte', () => {
  const todas = cat.cidades.map((c) => agoraDe(c.id))
  const t = textoPanorama(todas, [], AGORA)
  assert.match(t, /mesma faixa não é mesmo metro/)
  assert.match(t, /• Alerta: Blumenau \(Alerta: 6,40 m às 14:50, há 10 min\)\n• Atenção: Rio do Sul \(Atenção: 4,80 m às 14:40, há 20 min\)/)
  assert.match(t, /Abaixo da atenção \(1\): Gaspar\./)
  assert.match(t, /Sem cor agora[^]*Taió/)
  assert.ok(!/Itajaí \(/.test(t), 'Itajaí não entra como uma cidade de número só')
  // Sem nada acima do normal, diz que isso não quer dizer que não há alagamento.
  const calma = textoPanorama([agoraDe('gaspar')], [], AGORA)
  assert.match(calma, /Nenhuma cidade com leitura municipal de agora está acima/)
  assert.match(calma, /não quer dizer que não há alagamento/)
  // Só a rede estadual acima do normal: aparece, da faixa mais alta para a mais baixa, e o chat não diz "calmo".
  const g = agoraDe('gaspar')
  const est = (id: string, f: 'normal' | 'alerta' | 'atencao'): CidadeAgora => ({ ...agoraDe(id), estado: { ...agoraDe(id).estado, faixaEstadual: f } })
  const soEstadual = textoPanorama([g, est('timbo', 'normal'), est('ituporanga', 'alerta'), est('ibirama', 'atencao')], [], AGORA)
  assert.match(soEstadual, /zero próprio\): Ituporanga: Alerta; Ibirama: Atenção; Timbó: Normal\./)
  assert.doesNotMatch(soEstadual, /não quer dizer que não há alagamento/)
})

test('o que vem de cima: a árvore do cadastro, a leitura de cada cidade e o tempo de descida em intervalo', () => {
  const de = (alvo: string) =>
    textoDeCima({ cat, alvo, estado: (id) => (cidadeDoCadastro(id) ? agoraDe(id) : null), trechos: transito.trechos, experimentais: transito.trechos_experimentais, agora: AGORA })
  const b = de('blumenau')
  assert.match(b, /Itajaí-Açu, acima de Blumenau \(a mais perto primeiro\):/)
  assert.match(b, /• Rio do Sul: 4,80 m \(Atenção, na régua de Rio do Sul\), medido às 14:40 de 06\/10 \(há 20 min\) · leva 7–10 h até Blumenau\./)
  assert.match(b, /• Taió \(cabeceira\): sem leitura de agora · leva 13–18 h até Blumenau\./)
  assert.match(b, /• Indaial: sem leitura de agora · sem tempo de descida até Blumenau no cadastro\./)
  assert.ok(b.indexOf('• Indaial') < b.indexOf('• Rio do Sul'), 'a mais perto primeiro')
  assert.match(b, /Ligação não é previsão/)
  const i = de('itajai')
  assert.match(i, /Itajaí-Açu, acima de Itajaí/)
  assert.match(i, /Itajaí-Mirim, acima de Itajaí[^]*• Brusque: [^\n]* · leva cerca de 6 h até Itajaí\./)
  assert.match(de('brusque'), /Vidal Ramos[^\n]*em estudo \(dados insuficientes\)/)
  assert.match(de('taio'), /cabeceira; nenhuma régua do cadastro fica acima/)
  assert.match(de('timbo'), /afluente que entra no Itajaí-Açu perto de/)
})

test('o filtro "acima do normal" usa só faixa afirmada: cinza, várias réguas e sem cor ficam de fora', () => {
  for (const f of ['monitoramento', 'atencao', 'alerta', 'inundacao', 'emergencia'] as const) assert.ok(faixaAcimaDoNormal(f), f)
  for (const f of ['normal', 'sem-dado', 'varias', null, undefined] as const) assert.ok(!faixaAcimaDoNormal(f), String(f))
})

// ---------------------------------------------------------------- executar

function monitorFalso(cidade: string | null) {
  const filtros: FiltroMonitor[] = []
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
    filtrar: (f) => {
      filtros.push(f)
      return { ok: true, texto: `filtro ${f}` }
    },
    explicar: () => null,
    retrato: (): Retrato => ({ rota: `/monitor/${cidade}`, cidade }),
    restaurar: () => ({ ok: true, texto: 'ok' }),
  }
  return { c, filtros }
}

const dados: DadosDoChat = {
  aoVivo: async () => aoVivo,
  cidade: cidadeDoCadastro,
  reguasNoMapa: () => [],
  tracado: async () => null,
  base: () => '',
  transito: () => ({ trechos: transito.trechos, experimentais: transito.trechos_experimentais }),
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

test('executor: respostas de texto não mexem no mapa; o contexto dá a cidade', async () => {
  const { amb, navegacoes } = ambiente()
  const q = await rodar('quanto falta para a cota?', amb, { cidadeAtual: 'blumenau', naMonitor: false, reguaAtual: null })
  assert.match(q.texto, /Faltam 1,60 m para a cota de Alerta Máximo/)
  assert.equal(q.link?.para, '/acu/blumenau')
  assert.match((await rodar('quanto falta para a cota?', amb)).texto, /Em qual cidade\?/)
  assert.match((await rodar('Blumenau está subindo?', amb)).texto, /subindo 12 cm\/h/)
  assert.match((await rodar('máximo das últimas 24 h em Blumenau', amb)).texto, /máximo: 6,40 m/)
  const p = await rodar('quais cidades estão em alerta?', amb)
  assert.match(p.texto, /• Alerta: Blumenau/)
  assert.equal(p.link?.para, '/monitor')
  assert.match((await rodar('o que vem de cima para Gaspar?', amb)).texto, /• Blumenau: 6,40 m \(Alerta, na régua de Blumenau\), ▲ subindo 12 cm\/h[^\n]* · leva cerca de 2 h até Gaspar\./)
  assert.deepEqual(navegacoes, [])
})

test('executor: o filtro abre o Monitor e pede "acima do normal"', async () => {
  const { amb, navegacoes, monitor } = ambiente()
  const s = await rodar('mostrar só as cidades em alerta', amb)
  assert.deepEqual(navegacoes, ['/monitor'])
  assert.deepEqual(monitor()!.filtros, ['acima_do_normal'])
  assert.match(s.texto, /filtro acima_do_normal/)
})

test('a ajuda lista os pedidos da 6ª entrega', () => {
  const t = textoDeAjuda({ cidadeAtual: null, naMonitor: true, reguaAtual: null }, null).texto
  for (const f of ['quanto falta para a cota?', 'está subindo ou descendo?', 'quais cidades estão em alerta?', 'o que vem de cima?', 'mostrar só as cidades em alerta']) assert.ok(t.includes(f), f)
})
