import { test } from 'node:test'
import assert from 'node:assert/strict'
import { resumo24h } from './resumo24h'

const p = (h: number, nivel: number, regua: string | null = 'A') => ({
  medidoEm: new Date(Date.UTC(2026, 8, 6, h)), nivel_m: nivel, regua,
})

test('mín, máx e variação do primeiro ao último, na ordem do tempo', () => {
  const r = resumo24h([p(3, 2.1), p(1, 1.8), p(2, 2.4)])
  assert.equal(r.motivo, null)
  assert.deepEqual([r.resumo!.min, r.resumo!.max, r.resumo!.variacao, r.resumo!.pontos], [1.8, 2.4, 0.3, 3])
})

test('série de VÁRIAS réguas não vira uma amplitude — é o caso das onze de Itajaí', () => {
  const r = resumo24h([p(1, 0.92, 'DC-03'), p(2, 4.82, 'DC-10')])
  assert.equal(r.motivo, 'varias-reguas')
  assert.equal(r.resumo, null)
})

test('régua desconhecida em todos os pontos ainda é UMA série', () => {
  assert.equal(resumo24h([p(1, 1, null), p(2, 1.2, null)]).motivo, null)
})

test('sem pontos, ou com um só, não há resumo', () => {
  assert.equal(resumo24h([]).motivo, 'sem-pontos')
  assert.equal(resumo24h([p(1, 1)]).motivo, 'um-ponto-so')
})

test('ponto inválido é ignorado, não vira zero', () => {
  const r = resumo24h([p(1, 1), { medidoEm: new Date('x'), nivel_m: 9, regua: 'A' }, p(2, 1.5)])
  assert.equal(r.resumo!.max, 1.5)
})
