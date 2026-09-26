import { test } from 'node:test'
import assert from 'node:assert/strict'
import type { ChuvaAoVivo } from '../dados/tempoReal'
import {
  chuvaMonitor,
  mmChuva,
  linhasChuva,
  KM_CHUVA_NO_MAPA,
  KM_CHUVA_DETALHE,
} from './chuvaMonitor'

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

test('no mapa só 24 h; 1 h e 12 h ficam no painel', () => {
  const c = leitura('A', '2026-09-11T20:00:00Z', null)
  const linhas = linhasChuva([c], 'ascurra', new Date('2026-09-11T20:05:00Z'), 24)
  assert.deepEqual(linhas, ['24 h: 20 mm'])
  assert.ok(!linhas.some((l) => l.startsWith('1 h:') || l.startsWith('12 h:')))
})

test('vista de bacia (larga) não desenha chuva no pino', () => {
  const c = leitura('A', '2026-09-11T20:00:00Z', 10)
  assert.deepEqual(linhasChuva([c], 'ascurra', new Date('2026-09-11T20:05:00Z'), KM_CHUVA_NO_MAPA + 1), [])
  assert.deepEqual(linhasChuva([c], 'ascurra', new Date('2026-09-11T20:05:00Z'), 150), [])
})

test('zoom perto inclui a idade da MEDIÇÃO de chuva', () => {
  const agora = new Date('2026-09-13T22:10:00-03:00')
  const c = { cidade: 'rio-do-sul', estacao: 'A', coerente: true, medidoEm: new Date(agora.getTime() - 10 * 60_000),
    mm: { h1: 0, h12: 0, h24: 0.1 } } as unknown as Parameters<typeof linhasChuva>[0][number]
  const linhas = linhasChuva([c], 'rio-do-sul', agora, KM_CHUVA_DETALHE)
  assert.deepEqual(linhas, ['24 h: 0,1 mm', 'Chuva atualizada há 10 min'])
  assert.deepEqual(linhasChuva([], 'rio-do-sul', agora, KM_CHUVA_DETALHE), [
    '24 h: — mm',
    'Chuva indisponível',
  ])
})
