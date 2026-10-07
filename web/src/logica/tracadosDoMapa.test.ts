import { test } from 'node:test'
import assert from 'node:assert/strict'
import { contagemDeTracados, opcoesDeTracado, tracadosVisiveis } from './tracadosDoMapa'

const rios = ['itajai-acu', 'itajai-mirim', 'benedito', 'rio-dos-cedros', 'hercilio', 'rio-rafael', 'rio-rafael-braco-grande', 'rio-rafael-braco-pequeno', 'trombudo'].map((rioId) => ({ rioId }))

test('as opções saem dos traçados carregados: Benedito e Rio dos Cedros separados, tronco fixo, braços do Rafael juntos', () => {
  const op = opcoesDeTracado(rios)
  assert.deepEqual(op.filter((o) => o.fixo).map((o) => o.id), ['itajai-acu', 'itajai-mirim'])
  const benedito = op.find((o) => o.id === 'benedito')!
  const cedros = op.find((o) => o.id === 'rio-dos-cedros')!
  assert.equal(benedito.nome, 'Rio Benedito')
  assert.equal(cedros.nome, 'Rio dos Cedros')
  assert.notEqual(benedito, cedros)
  const rafael = op.find((o) => o.id === 'rio-rafael')!
  assert.deepEqual(rafael.ids, ['rio-rafael', 'rio-rafael-braco-grande', 'rio-rafael-braco-pequeno'])
  assert.equal(op.length, 7)
  // Só o que existe: um rio sem arquivo não vira opção (nem "em breve").
  assert.equal(op.some((o) => o.id === 'luiz-alves'), false)
})

test('esconder um grupo tira os arquivos dele; o tronco nunca sai; a contagem conta grupos ligados', () => {
  const op = opcoesDeTracado(rios)
  const ocultos = new Set(['rio-rafael', 'benedito', 'itajai-acu'])
  const vis = tracadosVisiveis(rios, ocultos).map((r) => r.rioId)
  assert.deepEqual(vis, ['itajai-acu', 'itajai-mirim', 'rio-dos-cedros', 'hercilio', 'trombudo'])
  assert.equal(contagemDeTracados(op, ocultos), '5 de 7')
  assert.equal(contagemDeTracados(op, new Set()), '7 de 7')
})
