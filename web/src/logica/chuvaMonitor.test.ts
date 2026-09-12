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

test('rótulo identifica cada janela, zero e horário da chuva', () => {
  const c = leitura('A', '2026-09-11T20:00:00Z', null)
  const linhas = linhasChuva([c], 'ascurra', new Date('2026-09-11T20:05:00Z'))
  assert.deepEqual(linhas.slice(0, 3), ['1 h: 0 mm', '12 h: — mm', '24 h: 20 mm'])
  assert.match(linhas[3]!, /5 min/)
})
