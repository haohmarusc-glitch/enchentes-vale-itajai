import assert from 'node:assert/strict'
import { test } from 'node:test'
import type { Trecho } from '../dados/tipos'
import { caminho, faixaHoras, janelaChegada } from './transito'

const t = (de: string, para: string, min: number, max: number): Trecho => ({
  rio: 'itajai-acu',
  de,
  para,
  horas_min: min,
  horas_max: max,
  confianca: 'media',
  fonte: 'teste',
})

const TRECHOS: Trecho[] = [
  t('taio', 'rio-do-sul', 8, 8),
  t('rio-do-sul', 'blumenau', 7, 10),
  t('blumenau', 'itajai', 14, 17),
]

test('usa o trecho direto quando existe', () => {
  const c = caminho(TRECHOS, 'itajai-acu', 'blumenau', 'itajai')
  assert.ok(c)
  assert.equal(c.direto, true)
  assert.equal(c.horasMin, 14)
  assert.equal(c.horasMax, 17)
})

test('encadeia trechos quando não há direto', () => {
  const c = caminho(TRECHOS, 'itajai-acu', 'taio', 'itajai')
  assert.ok(c)
  assert.equal(c.direto, false)
  assert.equal(c.trechos.length, 3)
  assert.equal(c.horasMin, 29)
  assert.equal(c.horasMax, 35)
})

test('sem cadeia possível devolve null — a tela dirá "sem dado"', () => {
  assert.equal(caminho(TRECHOS, 'itajai-acu', 'gaspar', 'itajai'), null)
  assert.equal(caminho(TRECHOS, 'itajai-acu', 'itajai', 'blumenau'), null, 'não sobe o rio')
})

test('não cruza rios', () => {
  assert.equal(caminho(TRECHOS, 'itajai-mirim', 'blumenau', 'itajai'), null)
})

test('a pior confiança do caminho é a do conjunto', () => {
  const trechos = [...TRECHOS, { ...t('rio-do-sul', 'blumenau', 7, 10), confianca: 'baixa' as const }]
  const c = caminho(trechos, 'itajai-acu', 'taio', 'itajai')
  assert.ok(c)
  assert.equal(c.confianca, 'media')
})

test('faixa de horas nunca vira número exato falso', () => {
  assert.equal(faixaHoras({ horasMin: 14, horasMax: 17 }), '14–17 h')
  assert.equal(faixaHoras({ horasMin: 6, horasMax: 6 }), 'cerca de 6 h')
})

test('janela de chegada soma a faixa ao horário do pico', () => {
  const partida = new Date('2026-07-12T00:00:00Z')
  const { inicio, fim } = janelaChegada(partida, { horasMin: 14, horasMax: 17 })
  assert.equal(inicio.toISOString(), '2026-07-12T14:00:00.000Z')
  assert.equal(fim.toISOString(), '2026-07-12T17:00:00.000Z')
})
