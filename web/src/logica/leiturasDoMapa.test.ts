/**
 * Auditoria de 03/10/2026, item 1: leitura velha não vira número seco no pino
 * do mapa do rio. A cena é montada pelo motor de verdade, como faz `MapaRios`.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { construirCena, textoDoPino } from './mapaMotor'
import type { RioParaCena } from './mapaMotor'
import type { EstadoTempoReal, LeituraAoVivo } from '../dados/tempoReal'
import type { Cidade } from '../dados/tipos'
import { semLeiturasVelhas } from './leiturasDoMapa'

const g = globalThis as unknown as { getComputedStyle?: unknown }
g.getComputedStyle = () => ({ getPropertyValue: () => '' })

const agora = new Date('2026-10-03T21:30:00-03:00')
const el = {} as unknown as Element
const indaial = {
  id: 'indaial', nome: 'Indaial', ordem: null, codigo_ana: null, verificado: false, fontes_tempo_real: [],
  regua: 'Régua municipal', cotas_m: { atencao: 5, alerta: 6, emergencia: 7 }, coordenadas: [-26.9, -49.25],
} as unknown as Cidade
const rio: RioParaCena = { rioId: 'itajai-acu', coords: [[[-49.5, -26.9], [-49.0, -26.9]]], cidades: [indaial] }

function leitura(cidade: string, nivel: number, medidoEm: Date | null): LeituraAoVivo {
  return { estacao: 'Régua municipal', rio: 'itajai-acu', cidade, nivel_m: nivel, medidoEm, resgateDe: null }
}
function tempo(...leituras: LeituraAoVivo[]): EstadoTempoReal {
  return { situacao: 'ok', leituras, chuva: [], chuvaOk: true, coletadoEm: agora, fonte: null }
}
function pinoDe(t: EstadoTempoReal) {
  const cena = construirCena(el, [rio], semLeiturasVelhas(t, agora), agora, 400, 300, null)
  return cena.pinos.find((p) => p.cidade.id === 'indaial')!
}

test('leitura de 20 dias numa cidade com cota: o pino não devolve só os metros', () => {
  const p = pinoDe(tempo(leitura('indaial', 4.1, new Date('2026-09-12T22:00:00-03:00'))))
  const { sub } = textoDoPino(p)
  assert.notEqual(sub, '4,10 m')
  assert.doesNotMatch(sub, /4,10/)
  assert.equal(sub, 'sem leitura')
  assert.equal(p.faixa, 'sem-dado')
})

test('leitura de agora continua no pino, com a faixa dela', () => {
  const p = pinoDe(tempo(leitura('indaial', 5.4, new Date(agora.getTime() - 20 * 60_000))))
  assert.equal(textoDoPino(p).sub, '5,40 m')
  assert.equal(p.faixa, 'atencao')
})

test('a idade é a da cidade: Blumenau vence aos 120 min, as outras aos 180', () => {
  const aos = (min: number) => new Date(agora.getTime() - min * 60_000)
  const t = tempo(leitura('blumenau', 3, aos(150)), leitura('indaial', 3, aos(150)), leitura('gaspar', 3, aos(181)))
  assert.deepEqual(semLeiturasVelhas(t, agora).leituras.map((l) => l.cidade), ['indaial'])
})

test('sem carimbo de hora não entra no mapa', () => {
  assert.equal(semLeiturasVelhas(tempo(leitura('indaial', 4.1, null)), agora).leituras.length, 0)
})

test('o mapa do rio passa pelo filtro antes do motor', () => {
  const fonte = readFileSync(new URL('../componentes/MapaRios.tsx', import.meta.url), 'utf8')
  assert.match(fonte, /construirCena\(\s*canvas,\s*\[[^\]]*\],\s*tempoRealDoMapa,/)
})
