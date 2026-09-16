/**
 * A anticolisão dos rótulos NA BACIA DE VERDADE (14/09/2026).
 *
 * O defeito: na captura do celular do Jefferson, "Ituporanga" (alerta ESTADUAL,
 * tracejado) escreveu por cima de "Rio do Sul" (atenção na cota MUNICIPAL). Os
 * testes de `rotulosDoMapa.test.ts` usam pinos inventados; este monta a cena
 * pelo motor de verdade, com as cidades e os traçados do repositório, em
 * várias telas, e confere o que o morador vê: nenhum rótulo cobre a bolinha de
 * outra cidade e nenhum rótulo cobre outro rótulo. Quem não cabe SOME — nunca
 * escreve por cima.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { construirCena, planejarRotulosDosPinos, pinoNaTela, type Caixa, type RioParaCena, type Pino } from './mapaMotor'
import { juntarCanais } from './canaisDoTronco'
import type { EstadoTempoReal, LeituraAoVivo as Leitura } from '../dados/tempoReal'
import type { BrutoEstadual, NivelSc } from '../dados/nivelSc'
import type { Cidade, Estacoes } from '../dados/tipos'
import type { LonLat } from './mapaCanvas'

const g = globalThis as unknown as { getComputedStyle?: unknown }
g.getComputedStyle = () => ({ getPropertyValue: () => '' })

const agora = new Date('2026-09-14T10:00:00-03:00')
const el = {} as unknown as Element

const estacoes: Estacoes = JSON.parse(
  readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'),
)
function geojson(rioId: string): LonLat[][] | null {
  try {
    const geo = JSON.parse(readFileSync(new URL(`../../../data/rios/${rioId}.geojson`, import.meta.url), 'utf8'))
    return geo.geometry.coordinates as LonLat[][]
  } catch {
    return null
  }
}
const eixo = (rioId: string): string[] | undefined => {
  const t = estacoes.rios[rioId]?._topologia
  return t ? [...(t.tronco_sequencia ?? []), ...(t.cabeceiras_paralelas ?? [])] : undefined
}
// A mesma montagem do MonitorBacia: tronco com cidades, canal fundido no Mirim,
// afluentes só como linha.
const rios: RioParaCena[] = juntarCanais(
  ['itajai-acu', 'itajai-mirim', 'mirim-canal-retificado', 'itajai-do-sul', 'ribeirao-murta', 'ribeirao-canhanduba', 'rio-conceicao']
    .map((rioId) => ({ rioId, coords: geojson(rioId) })),
).map((b) => ({
  rioId: b.rioId,
  coords: b.coords,
  cidades: ['itajai-acu', 'itajai-mirim'].includes(b.rioId) ? (estacoes.rios[b.rioId]!.cidades as Cidade[]) : [],
  eixo: eixo(b.rioId),
}))

/** Aproxima a fonte do mapa (system-ui 600): ~0,62 em por caractere. */
const medir = (texto: string, fonte: number) => texto.length * 0.62 * fonte

/** Toda cidade com leitura na PRÓPRIA régua (o pior caso: todos os pinos com sub-linha). */
function leiturasEmTodas(): Leitura[] {
  const saida: Leitura[] = []
  for (const rioId of ['itajai-acu', 'itajai-mirim']) {
    for (const c of estacoes.rios[rioId]!.cidades) {
      const cotas = c.cotas_m ?? {}
      const nivel = cotas.atencao ?? cotas.alerta ?? 2.5
      saida.push({ estacao: `Régua de ${c.nome}`, rio: rioId, cidade: c.id, nivel_m: nivel + 0.2, medidoEm: agora, resgateDe: null } as Leitura)
    }
  }
  return saida
}
/** O cenário da captura de 14/09: Ituporanga em alerta ESTADUAL, Rio do Sul em atenção MUNICIPAL. */
function cenarioDaCaptura(): { tempoReal: EstadoTempoReal; nivelSc: NivelSc } {
  const rioDoSul = estacoes.rios['itajai-acu']!.cidades.find((c) => c.id === 'rio-do-sul')!
  const tempoReal: EstadoTempoReal = {
    situacao: 'ok', chuva: [], chuvaOk: true, coletadoEm: agora, fonte: null,
    leituras: [{ estacao: 'Rio do Sul, Ponte Dom Tito Buss (Asthon)', rio: 'itajai-acu', cidade: 'rio-do-sul', nivel_m: (rioDoSul.cotas_m?.atencao ?? 3) + 0.1, medidoEm: agora, resgateDe: null } as Leitura],
  }
  const bruto: BrutoEstadual = { cidade: 'ituporanga', codigo: 'DCSC-00013', estacao: 'SDC-SC Ituporanga', nivelBrutoM: 4.12, medidoEm: agora, faixaEstadual: 'alerta', motivoFaixaEstadual: null }
  return { tempoReal, nivelSc: new Map([['ituporanga', bruto]]) }
}

const TELAS: [number, number][] = [[390, 640], [400, 300], [820, 600], [1400, 800]]
const escalaDe = (largura: number) => Math.max(1, Math.min(1.7, largura / 820))

function bolinha(p: Pino, escala: number): Caixa {
  const r = 7 * escala
  return { x0: p.x - r, y0: p.y - r, x1: p.x + r, y1: p.y + r }
}
function cruza(a: Caixa, b: Caixa): boolean {
  return a.x0 < b.x1 && a.x1 > b.x0 && a.y0 < b.y1 && a.y1 > b.y0
}

function conferir(tempoReal: EstadoTempoReal, nivelSc: NivelSc | undefined, selecionada: string | null) {
  const escondidos: Record<string, string[]> = {}
  for (const [w, h] of TELAS) {
    const cena = construirCena(el, rios, tempoReal, agora, w, h, null, undefined, nivelSc)
    const escala = escalaDe(w)
    const plano = planejarRotulosDosPinos(medir, cena, selecionada, { escala, mostrarIdade: true, agora }, [])
    const rotulos = [...plano.entries()]
    for (const [id, r] of rotulos) {
      // A selecionada fica no lugar de sempre, caiba ou não — é a que o
      // morador tocou, e o painel dela está aberto.
      if (id === selecionada) continue
      const proprio = cena.pinos.find((p) => p.cidade.id === id)!
      for (const q of cena.pinos) {
        if (q.cidade.id === id || !pinoNaTela(q, cena, escala)) continue
        // Regra: rótulo com nível pode cobrir pino CINZA (sem-dado) quando não
        // há outro lugar; nunca um pino colorido. "Sem leitura" não cobre nenhum.
        const permitido = q.faixa === 'sem-dado' && proprio.faixa !== 'sem-dado'
        if (permitido) continue
        assert.ok(!cruza(r.caixa, bolinha(q, escala)), `${w}×${h}: o rótulo de ${id} cobre o pino de ${q.cidade.id}`)
      }
      for (const [outro, s] of rotulos) {
        if (outro === id) continue
        assert.ok(!cruza(r.caixa, s.caixa), `${w}×${h}: o rótulo de ${id} cobre o rótulo de ${outro}`)
      }
    }
    escondidos[`${w}×${h}`] = [...new Set(cena.pinos.filter((p) => pinoNaTela(p, cena, escala) && !plano.has(p.cidade.id)).map((p) => p.cidade.id))]
  }
  return escondidos
}

test('a bacia carrega: os dois troncos e as cidades do cadastro', () => {
  assert.ok(rios.find((r) => r.rioId === 'itajai-acu')?.coords.length, 'traçado do Açu')
  assert.ok(rios.find((r) => r.rioId === 'itajai-mirim')?.coords.length, 'traçado do Mirim')
  assert.ok(rios.find((r) => r.rioId === 'itajai-acu')!.cidades.length >= 12)
})

test('o cenário da captura de 14/09: Ituporanga (estadual) nunca cobre Rio do Sul (municipal)', () => {
  const { tempoReal, nivelSc } = cenarioDaCaptura()
  const escondidos = conferir(tempoReal, nivelSc, null)
  for (const [tela, lista] of Object.entries(escondidos)) {
    assert.ok(!lista.includes('rio-do-sul'), `${tela}: Rio do Sul, com cota municipal, ficou sem rótulo (${lista.join(', ')})`)
  }
  // A cena de celular: se só um dos dois cabe, é a municipal que fica.
  const cena = construirCena(el, rios, tempoReal, agora, 390, 640, null, undefined, nivelSc)
  const plano = planejarRotulosDosPinos(medir, cena, null, { escala: 1, mostrarIdade: true, agora }, [])
  assert.ok(plano.has('rio-do-sul'))
  const rds = cena.pinos.find((p) => p.cidade.id === 'rio-do-sul')!
  assert.equal(rds.origemFaixa, 'municipal')
  assert.equal(cena.pinos.find((p) => p.cidade.id === 'ituporanga')!.origemFaixa, 'estadual')
})

test('com leitura em TODAS as cidades, nenhum rótulo cobre pino ou rótulo de outra, em nenhuma tela', () => {
  const tempoReal: EstadoTempoReal = { situacao: 'ok', chuva: [], chuvaOk: true, coletadoEm: agora, fonte: null, leituras: leiturasEmTodas() }
  const escondidos = conferir(tempoReal, undefined, null)
  console.log('# rótulos escondidos por falta de espaço (todas com leitura):', JSON.stringify(escondidos))
  // Só some quem tem vizinho COLADO: na tela grande, um pino isolado sempre
  // tem lugar para o nome. (Timbó e Rio dos Cedros caem no mesmo ponto do
  // traçado; Guabiruba fica a 20 px de Brusque; Trombudo Central a 40 px de
  // Ituporanga; Itajaí encosta em Ilhota e no chip da maré.)
  for (const [w, h] of TELAS) {
    const cena = construirCena(el, rios, tempoReal, agora, w, h, null)
    const escala = escalaDe(w)
    for (const id of escondidos[`${w}×${h}`]!) {
      const p = cena.pinos.find((q) => q.cidade.id === id)!
      const vizinho = cena.pinos.some((q) => q.cidade.id !== id && Math.hypot(q.x - p.x, q.y - p.y) < 80 * escala)
      assert.ok(vizinho, `${w}×${h}: ${id} ficou sem rótulo sem ter vizinho colado`)
    }
  }
})

test('a cidade selecionada sempre tem rótulo e nenhum outro rótulo cobre o dela', () => {
  const tempoReal: EstadoTempoReal = { situacao: 'ok', chuva: [], chuvaOk: true, coletadoEm: agora, fonte: null, leituras: leiturasEmTodas() }
  for (const sel of ['rio-do-sul', 'blumenau', 'itajai', 'brusque']) {
    const escondidos = conferir(tempoReal, undefined, sel)
    for (const [tela, lista] of Object.entries(escondidos)) assert.ok(!lista.includes(sel), `${tela}: a selecionada ${sel} ficou sem rótulo`)
  }
})

test('Timbó e Rio dos Cedros caem no mesmo ponto do traçado e são postos lado a lado — os dois com nome', () => {
  const tempoReal: EstadoTempoReal = { situacao: 'ok', chuva: [], chuvaOk: true, coletadoEm: agora, fonte: null, leituras: leiturasEmTodas() }
  const cena = construirCena(el, rios, tempoReal, agora, 1400, 800, null)
  const timbo = cena.pinos.find((p) => p.cidade.id === 'timbo')!
  const cedros = cena.pinos.find((p) => p.cidade.id === 'rio-dos-cedros')!
  assert.ok(timbo && cedros)
  assert.ok(Math.abs(timbo.x - cedros.x) >= 20, `os pinos ficaram a ${Math.abs(timbo.x - cedros.x).toFixed(1)} px um do outro`)
  assert.equal(timbo.y, cedros.y)
  const plano = planejarRotulosDosPinos(medir, cena, null, { escala: escalaDe(1400), mostrarIdade: true, agora }, [])
  assert.ok(plano.has('timbo') && plano.has('rio-dos-cedros'), 'os dois ganham nome na tela grande')
})
