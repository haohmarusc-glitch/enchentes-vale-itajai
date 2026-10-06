import { test } from 'node:test'
import assert from 'node:assert/strict'
import { textoDaPosicao } from './posicaoDoPino'

const pino = { lat: -27.057, lon: -49.52, aproximado: false }

test('estação estadual: diz o código e a coordenada', () => {
  assert.equal(
    textoDaPosicao({ codigo_dcsc: 'DCSC-00020' }, pino, 0),
    'Pino na coordenada da estação DCSC-00020 da Defesa Civil de SC (−27,0570, −49,5200).',
  )
})

test('aproximada vence o código: Blumenau tem DCSC-00026, que é pluviômetro', () => {
  const t = textoDaPosicao({ codigo_dcsc: 'DCSC-00026' }, { ...pino, aproximado: true }, 0)
  assert.match(t, /^Posição aproximada/)
  assert.doesNotMatch(t, /DCSC-00026/)
})

test('várias réguas: o pino é a cidade; sem código: não afirma o ponto da régua', () => {
  assert.match(textoDaPosicao({ codigo_dcsc: null }, pino, 11), /marca a cidade/)
  assert.match(textoDaPosicao({ codigo_dcsc: null }, pino, 0), /não confirma o ponto exato/)
})
