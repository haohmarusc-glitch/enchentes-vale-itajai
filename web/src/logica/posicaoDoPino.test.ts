import { readFileSync } from 'node:fs'
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

test('aproximada vence o código', () => {
  const t = textoDaPosicao({ codigo_dcsc: 'DCSC-00026' }, { ...pino, aproximado: true }, 0)
  assert.match(t, /^Posição aproximada/)
  assert.doesNotMatch(t, /DCSC-00026/)
})

test('fonte declarada vence o código: Blumenau, régua da ponte, com DCSC-00026 de chuva', () => {
  const t = textoDaPosicao(
    { codigo_dcsc: 'DCSC-00026', coordenadas_fonte: 'Prefeitura de Blumenau/Defesa Civil — Ponte Adolfo Konder, Beira-Rio' },
    { lat: -26.9186, lon: -49.0656, aproximado: false },
    0,
  )
  assert.equal(t, 'Pino na régua (−26,9186, −49,0656). Fonte: Prefeitura de Blumenau/Defesa Civil — Ponte Adolfo Konder, Beira-Rio.')
})

test('várias réguas: o pino é a cidade; sem código: não afirma o ponto da régua', () => {
  assert.match(textoDaPosicao({ codigo_dcsc: null }, pino, 11), /marca a cidade/)
  assert.match(textoDaPosicao({ codigo_dcsc: null }, pino, 0), /não confirma o ponto exato/)
})

test('coordenada não confirmada (Timbó, 06/10/2026): diz com essas palavras e não afirma a régua', () => {
  const t = textoDaPosicao(
    { codigo_dcsc: null, coordenadas_status: 'não confirmada', regua: 'Rio Benedito, Rua Equador' },
    { lat: -26.8231, lon: -49.2708, aproximado: false },
    0,
  )
  assert.match(t, /^Coordenada não confirmada \(−26,8231, −49,2708\)/)
  assert.match(t, /“Rio Benedito, Rua Equador”/)
  assert.doesNotMatch(t, /Pino na régua/)
})

test('o cadastro real marca Timbó, e só Timbó, como coordenada não confirmada', () => {
  const estacoes = JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8')) as {
    rios: Record<string, { cidades: { id: string; coordenadas_status?: string }[] }>
  }
  const marcadas = Object.values(estacoes.rios)
    .flatMap((r) => r.cidades)
    .filter((c) => c.coordenadas_status === 'não confirmada')
    .map((c) => c.id)
  assert.deepEqual(marcadas, ['timbo'])
})
