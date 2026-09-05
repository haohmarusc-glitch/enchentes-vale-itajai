import test from 'node:test'
import assert from 'node:assert/strict'
import {
  FRESCA_MIN,
  PERIODO_COMPORTA_S,
  barragensNoMapa,
  comportaAberta,
  comportas,
  faseComporta,
  rotuloComportas,
} from './barragensNoMapa'
import type { Barragem } from '../dados/barragens'

const AGORA = new Date('2026-09-05T17:30:00Z')

const oeste = (extra: Partial<Barragem> = {}): Barragem => ({
  nome: 'Barragem Oeste Taió', rio: 'Itajaí do Oeste',
  abertas: 7, total: 7, fechadas: [], percentUso: 31.79,
  medidoEm: new Date('2026-09-05T17:05:06Z'),
  lat: -27.09743881225586, lon: -50.03879165649414,
  ...extra,
})

test('barragem fresca com coordenada vira marcador', () => {
  const [m] = barragensNoMapa([oeste()], AGORA, 'itajai-acu')
  assert.ok(m)
  assert.equal(m.lat, -27.09743881225586)
  assert.equal(m.fresca, true)
  assert.equal(m.idadeMin, 25)
})

test('só aparece nos mapas do Açu e da bacia — no Mirim não existe', () => {
  assert.equal(barragensNoMapa([oeste()], AGORA, 'itajai-mirim').length, 0)
  assert.equal(barragensNoMapa([oeste()], AGORA, 'itajai-acu').length, 1)
  assert.equal(barragensNoMapa([oeste()], AGORA, 'bacia').length, 1)
})

test('sem coordenada não vai ao mapa — chutar posição é pior que não desenhar', () => {
  assert.equal(barragensNoMapa([oeste({ lat: null, lon: null })], AGORA, 'bacia').length, 0)
})

/*
 * "Cinza não corre" para a comporta: leitura velha não anima. A fonte publica a
 * cada 15 min; uma hora sem leitura nova é sinal de parada, e uma comporta
 * animando com estado de duas horas atrás afirma uma operação que não sabemos.
 */
test('leitura velha NÃO é fresca — a comporta para de animar', () => {
  const velha = new Date(AGORA.getTime() - (FRESCA_MIN + 1) * 60_000)
  const [m] = barragensNoMapa([oeste({ medidoEm: velha })], AGORA, 'bacia')
  assert.equal(m!.fresca, false)
  assert.equal(m!.idadeMin, FRESCA_MIN + 1)
})

test('no limite exato ainda é fresca; um minuto depois não', () => {
  const limite = new Date(AGORA.getTime() - FRESCA_MIN * 60_000)
  assert.equal(barragensNoMapa([oeste({ medidoEm: limite })], AGORA, 'bacia')[0]!.fresca, true)
})

test('sem carimbo não é "fresca por padrão" — é não sei, e não sei não anima', () => {
  const [m] = barragensNoMapa([oeste({ medidoEm: null })], AGORA, 'bacia')
  assert.equal(m!.fresca, false)
  assert.equal(m!.idadeMin, null)
})

test('carimbo no futuro não é fresca (relógio errado não vira animação)', () => {
  const futuro = new Date(AGORA.getTime() + 30 * 60_000)
  assert.equal(barragensNoMapa([oeste({ medidoEm: futuro })], AGORA, 'bacia')[0]!.fresca, false)
})

test('a fase da comporta anda com o tempo e dá uma volta por período', () => {
  assert.equal(faseComporta(0), 0)
  assert.ok(faseComporta(PERIODO_COMPORTA_S * 0.25) > 0.24 && faseComporta(PERIODO_COMPORTA_S * 0.25) < 0.26)
  // Uma volta inteira volta a zero (módulo), então quadros seguem girando.
  assert.ok(faseComporta(PERIODO_COMPORTA_S) < 1e-9)
  assert.notEqual(faseComporta(1), faseComporta(1.3), 'quadros diferentes têm fases diferentes')
})

test('tempo zero (reduced-motion) e valores inválidos dão fase 0 — quadro parado, sem sorteio', () => {
  for (const t of [0, -5, Number.NaN, Number.POSITIVE_INFINITY]) assert.equal(faseComporta(t), 0)
})

test('comportas: nomes C1..Cn na ordem, estado pela lista de fechadas', () => {
  const lista = comportas(7, ['C4'])
  assert.equal(lista.length, 7)
  assert.deepEqual(lista.map((c) => c.nome), ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7'])
  assert.deepEqual(lista.filter((c) => !c.aberta).map((c) => c.nome), ['C4'])
})

test('comporta que está na lista de fechadas está fechada; fora dela, aberta', () => {
  assert.equal(comportaAberta('C2', ['C2']), false)
  assert.equal(comportaAberta('C2', ['C1']), true)
  assert.equal(comportaAberta('C2', []), true)
})

test('o rótulo diz quantas abertas — e "fechadas" quando são todas', () => {
  assert.equal(rotuloComportas({ abertas: 7, total: 7 }), '7 de 7 abertas')
  assert.equal(rotuloComportas({ abertas: 3, total: 7 }), '3 de 7 abertas')
  assert.equal(rotuloComportas({ abertas: 0, total: 5 }), '5 de 5 fechadas')
})

test('funciona com um Map (como o hook devolve) e com N barragens, não só duas', () => {
  const tres = new Map<string, Barragem>([
    ['a', oeste({ nome: 'A' })],
    ['b', oeste({ nome: 'B', lat: -27.5, lon: -49.55 })],
    ['c', oeste({ nome: 'C', lat: -26.95, lon: -49.6 })],
  ])
  assert.equal(barragensNoMapa(tres.values(), AGORA, 'bacia').length, 3)
})
