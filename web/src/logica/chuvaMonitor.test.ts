import { test } from 'node:test'
import assert from 'node:assert/strict'
import type { ChuvaAoVivo } from '../dados/tempoReal'
import { chuvaMonitor, mmChuva, linhasChuva } from './chuvaMonitor'

const leitura = (estacao: string, hora: string, h12: number | null): ChuvaAoVivo => ({
  estacao, cidade: 'ascurra', rio: null, medidoEm: new Date(hora),
  mm: { min10: null, h1: 0, h12, h24: 20, h48: null }, coerente: true, incoerencias: [],
})
test('seleciona mais recente sem misturar janelas entre pluviômetros', () => {
  const antiga = leitura('A', '2026-09-11T20:00:00Z', 10)
  const nova = leitura('B', '2026-09-11T21:00:00Z', null)
  assert.equal(chuvaMonitor([antiga, nova], 'ascurra'), nova)
  assert.equal(chuvaMonitor([antiga, nova], 'ascurra')?.mm.h12, null)
})
test('não apresenta estação incoerente ou de outra cidade', () => {
  const c = leitura('A', '2026-09-11T20:00:00Z', 10)
  assert.equal(chuvaMonitor([{ ...c, coerente: false }], 'ascurra'), null)
  assert.equal(chuvaMonitor([c], 'blumenau'), null)
})
test('zero medido difere de ausência', () => {
  assert.equal(mmChuva(0), '0')
  assert.equal(mmChuva(null), '—')
  assert.equal(mmChuva(12.34), '12,3')
})

test('no mapa só 24 h em mm; 1 h, 12 h e idade ficam no painel', () => {
  const c = leitura('A', '2026-09-11T20:00:00Z', 10)
  const linhas = linhasChuva([c], 'ascurra', new Date('2026-09-11T20:05:00Z'))
  assert.deepEqual(linhas, ['24 h: 20 mm'])
})

test('sem pluviômetro na cidade, o pino diz que não há número', () => {
  assert.deepEqual(linhasChuva([], 'rio-do-sul', new Date('2026-09-11T20:05:00Z')), ['24 h: — mm'])
})

test('decimal em pt-BR e zero medido aparece como zero', () => {
  const agora = new Date('2026-09-11T20:05:00Z')
  const c = leitura('A', '2026-09-11T20:00:00Z', 0)
  assert.deepEqual(linhasChuva([{ ...c, mm: { ...c.mm, h24: 0.1 } }], 'ascurra', agora), ['24 h: 0,1 mm'])
  assert.deepEqual(linhasChuva([{ ...c, mm: { ...c.mm, h24: 0 } }], 'ascurra', agora), ['24 h: 0 mm'])
})

test('leitura velha NÃO aparece no pino: sem idade à vista, vira "—"', () => {
  // O pino não mostra a idade; um acumulado de ontem lido como de agora é o
  // erro que este teste trava. Até 3 h (MIN_VELHA) o número vale.
  const c = leitura('A', '2026-09-11T20:00:00Z', 10)
  assert.deepEqual(linhasChuva([c], 'ascurra', new Date('2026-09-11T23:00:00Z')), ['24 h: 20 mm'])
  assert.deepEqual(linhasChuva([c], 'ascurra', new Date('2026-09-11T23:01:00Z')), ['24 h: — mm'])
  assert.deepEqual(linhasChuva([c], 'ascurra', new Date('2026-09-12T20:00:00Z')), ['24 h: — mm'])
})

test('leitura do futuro (fuso trocado) também vira "—"', () => {
  const c = leitura('A', '2026-09-11T22:00:00Z', 10)
  assert.deepEqual(linhasChuva([c], 'ascurra', new Date('2026-09-11T20:00:00Z')), ['24 h: — mm'])
})
