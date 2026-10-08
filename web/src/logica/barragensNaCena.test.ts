/**
 * Barragens no Monitor (07/10/2026, "Monitor: Ituporanga e barragens", seção 2): o armazenamento, o nível e as
 * comportas NÃO mudam a classificação do rio, e o rótulo do mapa nunca leva o nível em metros.
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import type { EstadoTempoReal } from '../dados/tempoReal'
import type { Cidade } from '../dados/tipos'
import { montarBarragens } from '../dados/barragens'
import { barragensNoMapa } from './barragensNoMapa'
import { barragemNoPonto, construirCena, desenharBarragens, type RioParaCena } from './mapaMotor'
import { projetar } from './mapaCanvas'

const g = globalThis as unknown as { getComputedStyle?: unknown }
g.getComputedStyle = () => ({ getPropertyValue: () => '' })
const el = {} as unknown as Element
const agora = new Date('2026-10-07T19:50:00-03:00')

const cidade = { id: 'taio', nome: 'Taió', ordem: null, cotas_m: { atencao: 6 }, coordenadas: [-27.1, -50.0] } as unknown as Cidade
// Vértices a cada ~5 km: a âncora encaixa no vértice mais próximo, e a régua fica em cima de um.
const rio: RioParaCena = { rioId: 'itajai-acu', coords: [[[-50.1, -27.1], [-50.05, -27.1], [-50.0, -27.1], [-49.95, -27.1], [-49.9, -27.1]]], cidades: [cidade] }
const tempoReal = {
  situacao: 'ok',
  coletadoEm: agora,
  leituras: [{ estacao: 'Taió', rio: 'itajai-acu', cidade: 'taio', nivel_m: 7.2, medidoEm: new Date('2026-10-07T19:45:00-03:00') }],
} as unknown as EstadoTempoReal

function barragens(percent: number, abertas: number) {
  return barragensNoMapa(montarBarragens({
    barragens: [{
      nome: 'Barragem Oeste Taió', lat: -27.1, lon: -50.0, medido_em: '2026-10-07T19:40:00',
      altitude_montante_m: 347.97, nivel_na_regua_da_barragem_m: 8.97, zero_da_regua_m: 339, jusante_m: 5.14,
      percent_use: percent, comportas_abertas: abertas, comportas_total: 7,
      comportas: Array.from({ length: 7 }, (_, i) => ({ nome: `C${i + 1}`, aberta: i < abertas })),
    }],
  }).values(), agora, 'bacia')
}

/** Um contexto de canvas que só anota o texto escrito. */
function ctxFalso() {
  const textos: string[] = []
  const nada = () => {}
  const ctx = new Proxy({ textos }, {
    get: (_alvo, k) => k === 'textos' ? textos
      : k === 'fillText' ? (t: string) => textos.push(t)
      : k === 'measureText' ? (t: string) => ({ width: t.length * 6 })
      : nada,
    set: () => true,
  })
  return ctx as unknown as CanvasRenderingContext2D & { textos: string[] }
}

test('ocupação, nível, comportas e o número a jusante não mudam a cor do rio', () => {
  const cena = construirCena(el, [rio], tempoReal, agora, 800, 600, null)
  const antes = JSON.stringify(cena.trechos.map((t) => [t.faixa, t.cidadeId, t.animacao]))
  for (const [p, a] of [[0, 0], [50, 3], [104, 7]] as const) {
    desenharBarragens(ctxFalso(), cena, barragens(p, a), 1, 1, [], true)
    assert.equal(JSON.stringify(cena.trechos.map((t) => [t.faixa, t.cidadeId, t.animacao])), antes)
  }
  assert.ok(cena.trechos.some((t) => t.faixa === 'atencao'), 'a régua de Taió continua decidindo a cor')
})

test('o rótulo leva o percentual real, nunca o nível em metros', () => {
  const cena = construirCena(el, [rio], tempoReal, agora, 800, 600, null)
  const ctx = ctxFalso()
  desenharBarragens(ctx, cena, barragens(104.2, 7), 1, 1, [], true)
  assert.equal(ctx.textos.length, 1)
  assert.match(ctx.textos[0]!, /104 %/, 'acima de 100 foi cortado')
  assert.doesNotMatch(ctx.textos[0]!, /8,97|347|339|5,14/)
  // Camada desligada: sem percentual no rótulo.
  const sem = ctxFalso()
  desenharBarragens(sem, cena, barragens(104.2, 7), 1, 1, [], false)
  assert.doesNotMatch(sem.textos[0]!, /%/)
})

test('o toque acha a barragem pelo marcador', () => {
  const cena = construirCena(el, [rio], tempoReal, agora, 800, 600, null)
  const b = barragens(4.5, 7)
  const [x, y] = projetar(cena.enq, [b[0]!.lon, b[0]!.lat])
  assert.equal(barragemNoPonto(cena, b, x + 3, y - 2)?.nome, 'Barragem Oeste Taió')
  assert.equal(barragemNoPonto(cena, b, x + 80, y), null)
})
