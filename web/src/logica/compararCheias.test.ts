import { test } from 'node:test'
import assert from 'node:assert/strict'
import { cheiaMaisProxima, type EventoComparavel } from './compararCheias'
const agora = new Date('2026-09-11T03:00:00Z')
const e = (pico: number, ano: string): EventoComparavel => ({ cidade: 'itajai', evento: ano, arquivo: ano,
  pico_registrado: { pico_m: pico, regua: 'DC-10', fonte: 'fonte oficial' } })
const l = { cidade: 'itajai', estacao: 'DC-10', nivel_m: 4.8, medidoEm: agora }
test('escolhe por distância de nível, não por ano, e informa diferença', () => {
  const r = cheiaMaisProxima([e(3, '2011'), e(5, '1983')], [l], agora)!
  assert.equal(r.evento.evento, '1983')
  assert.ok(Math.abs(r.diferencaM + 0.2) < 1e-9)
})
test('recusa outra régua, leitura antiga e pico sem referência', () => {
  assert.equal(cheiaMaisProxima([e(5, '1983')], [{ ...l, estacao: 'DC-11' }], agora), null)
  assert.equal(cheiaMaisProxima([e(5, '1983')], [{ ...l, medidoEm: new Date('2026-09-10T20:00:00Z') }], agora), null)
  assert.equal(cheiaMaisProxima([{ ...e(5, '1983'), pico_registrado: null }], [l], agora), null)
})
