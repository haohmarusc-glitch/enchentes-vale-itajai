import { test } from 'node:test'
import assert from 'node:assert/strict'
import { vizinhosNoEixo } from './vizinhosNoEixo'
import type { Trecho } from '../dados/tipos'

const cidades = [
  { id: 'rio-do-sul', nome: 'Rio do Sul' }, { id: 'lontras', nome: 'Lontras' },
  { id: 'blumenau', nome: 'Blumenau' }, { id: 'taio', nome: 'Taió' },
]
const eixo = ['rio-do-sul', 'lontras', 'blumenau']
const trechos = [
  { rio: 'itajai-acu', de: 'rio-do-sul', para: 'lontras', horas_min: 2, horas_max: 4, confianca: 'media', fonte: 'JICA' },
] as unknown as Trecho[]

test('acima e abaixo saem do eixo, com a janela do trecho quando existe', () => {
  const v = vizinhosNoEixo('itajai-acu', 'lontras', eixo, cidades, trechos)
  assert.equal(v.noEixo, true)
  assert.equal(v.montante?.nome, 'Rio do Sul')
  assert.equal(v.montante?.janela, '2–4 h')
  assert.equal(v.montante?.confianca, 'media')
  assert.equal(v.jusante?.nome, 'Blumenau')
  assert.equal(v.jusante?.janela, null, 'trecho não levantado não vira número')
})

test('início e fim do eixo não inventam vizinho', () => {
  assert.equal(vizinhosNoEixo('itajai-acu', 'rio-do-sul', eixo, cidades, trechos).montante, null)
  assert.equal(vizinhosNoEixo('itajai-acu', 'blumenau', eixo, cidades, trechos).jusante, null)
})

test('cabeceira e afluente ficam FORA do eixo — a cheia deles não é a do tronco', () => {
  const v = vizinhosNoEixo('itajai-acu', 'taio', eixo, cidades, trechos)
  assert.deepEqual(v, { noEixo: false, montante: null, jusante: null })
})
