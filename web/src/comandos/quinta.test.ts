/**
 * 5ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): reprodução, chuva, barragens, maré e a fonte
 * de cada leitura.
 */
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { executar, limparRetratos, type Ambiente, type DadosDoChat } from './executar'
import { textoDeAjuda } from './ajuda'
import { instantePedido, textoBarragens, textoChuvaAgora, textoFonteDaLeitura, textoMare } from './bacia'
import type { Barragem } from '../dados/barragens'
import type { ChuvaAoVivo, LeituraAoVivo } from '../dados/tempoReal'
import type { AoVivo } from '../dados/usarAoVivo'
import type { NivelSc } from '../dados/nivelSc'
import type { TabuaMare } from '../dados/tipos'
import type { ControleMonitor, Retrato } from './ponte'
import type { Contexto, Fundo } from './tipos'

const ler = (c: string) => JSON.parse(readFileSync(new URL(`../../../data/${c}`, import.meta.url), 'utf8'))
const cat = catalogoDoCadastro(ler('estacoes.json'))
const tabua = ler('mare-itajai.json') as TabuaMare
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const AGORA = new Date('2026-10-06T18:00:00Z') // 15h00 em Brasília
const minAtras = (m: number) => new Date(AGORA.getTime() - m * 60_000)

const passos = (texto: string, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', `"${texto}" devia virar comando, veio ${JSON.stringify(r)}`)
  return r.passos
}

function pluv(cidade: string, h1: number, h24: number, min = 10): ChuvaAoVivo {
  return { estacao: `P ${cidade}`, rio: 'itajai-acu', cidade, mm: { min10: 0, h1, h12: h24, h24, h48: h24 }, medidoEm: minAtras(min), coerente: true, incoerencias: [] }
}

// ---------------------------------------------------------------- interpretar

test('frases da 5ª entrega; "parar a reprodução" continua voltando ao agora', () => {
  assert.deepEqual(passos('reproduzir as últimas 24 h'), [{ tipo: 'reproducao', acao: 'tocar' }])
  assert.deepEqual(passos('pausar'), [{ tipo: 'reproducao', acao: 'pausar' }])
  assert.deepEqual(passos('como estava às 14h?'), [{ tipo: 'reproducao', acao: 'ir', hora: 14 }])
  assert.deepEqual(passos('mostrar o mapa das 9h30'), [{ tipo: 'reproducao', acao: 'ir', hora: 9, minuto: 30 }])
  assert.deepEqual(passos('voltar 3 horas'), [{ tipo: 'reproducao', acao: 'ir', horasAtras: 3 }])
  assert.deepEqual(passos('como estava o rio há 2 horas?'), [{ tipo: 'reproducao', acao: 'ir', horasAtras: 2 }])
  assert.deepEqual(passos('onde está chovendo mais?'), [{ tipo: 'chuva_agora' }])
  assert.deepEqual(passos('como estão as barragens?'), [{ tipo: 'barragens' }])
  assert.deepEqual(passos('as comportas estão abertas?'), [{ tipo: 'barragens' }])
  assert.deepEqual(passos('como está a maré?'), [{ tipo: 'mare' }])
  assert.deepEqual(passos('qual a próxima preamar?'), [{ tipo: 'mare' }])
  assert.deepEqual(passos('de onde vem a leitura de Blumenau?'), [{ tipo: 'fonte_leitura', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('parar a reprodução'), [{ tipo: 'ao_vivo' }])
  for (const q of ['vai chover amanhã?', 'a barragem vai abrir?', 'a maré vai subir à noite?', 'choveu muito em 2008?']) {
    assert.equal(interpretar(q, cat, fora), null, q)
  }
})

// ---------------------------------------------------------------- textos

test('instante pedido: hora de Brasília, a última vez que foi aquela hora; horas atrás', () => {
  assert.equal(instantePedido({ hora: 14 }, AGORA)?.toISOString(), '2026-10-06T17:00:00.000Z')
  assert.equal(instantePedido({ hora: 16 }, AGORA)?.toISOString(), '2026-10-05T19:00:00.000Z')
  assert.equal(instantePedido({ hora: 9, minuto: 30 }, AGORA)?.toISOString(), '2026-10-06T12:30:00.000Z')
  assert.equal(instantePedido({ horasAtras: 3 }, AGORA)?.toISOString(), '2026-10-06T15:00:00.000Z')
  assert.equal(instantePedido({ hora: 25 }, AGORA), null)
})

test('chuva: os pluviômetros de leitura recente, do mais chuvoso para o menos; velho fica de fora', () => {
  const t = textoChuvaAgora([pluv('blumenau', 4.2, 30), pluv('gaspar', 12.6, 41), pluv('ilhota', 0, 8), pluv('taio', 50, 90, 400)], true, cat, AGORA)
  const ordem = ['Gaspar', 'Blumenau'].map((n) => t.indexOf(`• ${n}:`))
  assert.ok(ordem[0]! > 0 && ordem[0]! < ordem[1]!, t)
  assert.match(t, /• Gaspar: 1 h: 12,6 mm · 24 h: 41,0 mm \(1 pluviômetro, até 14:50\)/)
  assert.ok(!t.includes('Taió:'), 'leitura velha não entra no ranking')
  assert.match(t, /1 cidade\(s\) com pluviômetro ficaram de fora por leitura velha/)
  assert.match(t, /não previsão[^]*A fonte não publica 6 h/)
  assert.match(textoChuvaAgora([pluv('blumenau', 0, 0)], true, cat, AGORA), /Nenhum pluviômetro com leitura recente marcou chuva na última hora nem em 24 h/)
  assert.match(textoChuvaAgora([], false, cat, AGORA), /Não consegui buscar a chuva/)
})

test('barragens: comportas e uso como a fonte publica, nunca o nível em metros nem veredito', () => {
  const b = (nome: string, abertas: number, min: number, uso: number | null): Barragem => ({ nome, rio: null, abertas, total: 7, fechadas: [], percentUso: uso, medidoEm: minAtras(min), lat: null, lon: null })
  const t = textoBarragens(new Map([['o', b('Barragem Oeste Taió', 0, 20, 12.5)], ['s', b('Barragem Sul Ituporanga', 7, 200, null)]]), AGORA)
  assert.match(t, /Barragem Oeste Taió: comportas 7 de 7 fechadas · 12,5% de ocupação, como a fonte publica, às 14:40/)
  assert.match(t, /Barragem Sul Ituporanga: comportas 7 de 7 abertas, às 11:40 de 06\/10 \(há 3 h 20\) — pode ter mudado desde então/)
  assert.match(t, /não diz se a cheia já passou/)
  assert.ok(!/\d,\d\d m\b/.test(t), 'nenhum nível em metros')
  assert.match(textoBarragens(new Map(), AGORA), /Não consegui/)
})

test('maré: pela tábua do site (a fonte vem do arquivo), subindo ou baixando, a próxima preamar; maré não é cheia', () => {
  const t = textoMare(tabua, AGORA)
  // A fonte é a do próprio `mare-itajai.json` (UNIVALI desde 08/10/2026), nunca um nome fixo no código.
  assert.match(t, /^Pela tábua de maré do porto de Itajaí \(Laboratório de Oceanografia Física da UNIVALI.*\), a maré está baixando \(vazante\) agora\./)
  assert.ok(!/Marinha/.test(t), 'o chat não crava a Marinha como fonte')
  // 06/10/2026, 15h00 em Brasília: a UNIVALI dá a preamar às 23:05 e a baixa-mar às 18:35 (a Marinha dava 22:59 e
  // 18:49). Sem altura: a planilha não declara a referência vertical.
  assert.match(t, /Próxima preamar: 23:05 de 06\/10\. Próxima baixamar: 18:35 de 06\/10\./)
  assert.ok(!/na tábua\)/.test(t), 'sem altura, nenhum "(x m na tábua)"')
  assert.match(t, /previsão astronômica[^]*Maré alta não é cheia/)
  const sem = textoMare({ ...tabua, preamares: [], baixamares: [] }, AGORA)
  assert.match(sem, /não cobre este horário/)
  assert.match(sem, /UNIVALI/)
  // Uma tábua com outra fonte no arquivo muda o texto junto.
  assert.match(textoMare({ ...tabua, _meta: { fonte_curta: 'Fonte X' } }, AGORA), /^Pela tábua de maré do porto de Itajaí \(Fonte X\)/)
})

test('fonte da leitura: estação e hora de cada leitura, a estadual com zero próprio e as fontes cadastradas', () => {
  const l: LeituraAoVivo = { estacao: 'Blumenau (AlertaBlu)', rio: 'itajai-acu', cidade: 'blumenau', nivel_m: 3.2, medidoEm: minAtras(25), resgateDe: 'Blumenau' }
  const t = textoFonteDaLeitura({ nome: 'Blumenau', leituras: [l], estadual: null, fontesCadastradas: ['https://alertablu.blumenau.sc.gov.br/'], agora: AGORA })
  assert.match(t, /• Blumenau \(AlertaBlu\) \(resgate da "Blumenau"\): medida às 14:35 de 06\/10 \(há 25 min\)/)
  assert.match(t, /Fontes de tempo real cadastradas para Blumenau:\n• https:\/\/alertablu/)
  assert.match(textoFonteDaLeitura({ nome: 'Lontras', leituras: [], estadual: null, fontesCadastradas: [], agora: AGORA }), /não recebeu leitura municipal de Lontras/)
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
    reproducao: (p) => {
      chamadas.push(p.acao === 'ir' ? `ir:${p.instante.toISOString()}` : p.acao)
      return { ok: true, texto: `reprodução ${p.acao}` }
    },
    explicar: () => null,
    retrato: (): Retrato => ({ rota: `/monitor/${cidade}`, cidade }),
    restaurar: () => ({ ok: true, texto: 'ok' }),
  }
  return { c, chamadas }
}

const aoVivo: AoVivo = {
  tempoReal: { situacao: 'ok', leituras: [], chuva: [pluv('gaspar', 3, 20)], chuvaOk: true, coletadoEm: AGORA, fonte: null },
  nivelSc: new Map() as NivelSc,
  serie: { situacao: 'ok', series: {}, resgates: {}, janelaHoras: 48, geradoEm: AGORA },
  agora: AGORA,
}
const dados: DadosDoChat = {
  aoVivo: async () => aoVivo,
  cidade: () => null,
  reguasNoMapa: () => [],
  tracado: async () => null,
  base: () => '',
  barragens: async () => new Map(),
  mare: () => tabua,
  fontesDaCidade: () => [],
}

function ambiente(inicial: ReturnType<typeof monitorFalso> | null, rota = '/') {
  const montados = new Map<string | null, ReturnType<typeof monitorFalso>>()
  let atual = inicial
  if (inicial) montados.set(inicial.c.cidade, inicial)
  let r = rota
  const navegacoes: string[] = []
  const amb: Ambiente = {
    navegar: (para) => {
      navegacoes.push(para)
      r = para
      const m = para.match(/^\/monitor(?:\/([a-z-]+))?/)
      if (m) {
        const cid = m[1] ?? null
        if (!montados.has(cid)) montados.set(cid, monitorFalso(cid))
        atual = montados.get(cid)!
      } else atual = null
    },
    rotaAtual: () => r,
    monitor: () => atual?.c ?? null,
    esperarMonitor: async (cid) => (atual && atual.c.cidade === cid ? atual.c : null),
    dados,
  }
  return { amb, navegacoes, montados }
}
const ajuda = () => textoDeAjuda(fora, null)
const rodar = (texto: string, amb: Ambiente, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', texto)
  return executar(r.passos, amb, cat, ctx, ajuda)
}

beforeEach(() => limparRetratos())

test('reprodução: abre o Monitor se preciso e passa o instante de Brasília', async () => {
  const { amb, navegacoes, montados } = ambiente(null)
  await rodar('reproduzir as últimas 24 h', amb)
  assert.deepEqual(navegacoes, ['/monitor'])
  await rodar('como estava às 14h?', amb, { cidadeAtual: null, naMonitor: true, reguaAtual: null })
  await rodar('pausar', amb, { cidadeAtual: null, naMonitor: true, reguaAtual: null })
  assert.deepEqual(montados.get(null)!.chamadas, ['tocar', 'ir:2026-10-06T17:00:00.000Z', 'pausar'])
})

test('chuva, barragens e maré: texto, sem mexer no mapa', async () => {
  const { amb, navegacoes } = ambiente(null)
  assert.match((await rodar('onde está chovendo mais?', amb)).texto, /Gaspar: 1 h: 3,0 mm/)
  assert.match((await rodar('como estão as barragens?', amb)).texto, /Não consegui buscar o estado das barragens/)
  const m = await rodar('como está a maré?', amb)
  assert.match(m.texto, /tábua de maré do porto de Itajaí \(Laboratório de Oceanografia Física da UNIVALI/)
  assert.equal(m.link?.para, '/itajai')
  assert.deepEqual(navegacoes, [])
})

test('a ajuda lista os pedidos da 5ª entrega', () => {
  const t = textoDeAjuda({ cidadeAtual: null, naMonitor: true, reguaAtual: null }, null).texto
  for (const f of ['reproduzir as últimas 24 h', 'como estava às 14h', 'onde está chovendo mais?', 'como estão as barragens?', 'como está a maré?']) assert.ok(t.includes(f), f)
})
