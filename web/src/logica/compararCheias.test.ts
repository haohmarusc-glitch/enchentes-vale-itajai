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

test('Blumenau fica velha aos 120 min, as outras cidades aos 180 — como o bot', () => {
  const ha150min = new Date(agora.getTime() - 150 * 60_000)
  const blu = { cidade: 'blumenau', estacao: 'Ponte Adolfo Konder', nivel_m: 9.5, medidoEm: ha150min }
  const ita = { ...l, medidoEm: ha150min }
  const evBlu = { ...e(9, '2011'), cidade: 'blumenau', pico_registrado: { pico_m: 9, regua: 'Ponte Adolfo Konder', fonte: 'x' } }
  assert.equal(cheiaMaisProxima([evBlu], [blu], agora), null)
  assert.ok(cheiaMaisProxima([e(5, '1983')], [ita], agora))
  const ha100min = new Date(agora.getTime() - 100 * 60_000)
  assert.ok(cheiaMaisProxima([evBlu], [{ ...blu, medidoEm: ha100min }], agora))
})
