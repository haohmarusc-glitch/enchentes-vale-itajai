import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  agravamento,
  cruzarComMare,
  diasAteSizigia,
  regimeMare,
} from './mare'

test('lua nova conhecida é sizígia', () => {
  // Lua nova de 6 de janeiro de 2000, 18:14 UTC — a própria referência.
  assert.ok(diasAteSizigia(new Date('2000-01-06T18:14:00Z')) < 0.01)
  assert.equal(regimeMare(new Date('2000-01-06T18:14:00Z')), 'sizigia')
})

test('lua cheia seguinte também é sizígia', () => {
  // Meio ciclo sinódico depois: ~21 de janeiro de 2000.
  const cheia = new Date(Date.UTC(2000, 0, 6, 18, 14) + 14.765 * 86_400_000)
  assert.ok(diasAteSizigia(cheia) < 0.1)
  assert.equal(regimeMare(cheia), 'sizigia')
})

test('quarto de lua é quadratura', () => {
  const quarto = new Date(Date.UTC(2000, 0, 6, 18, 14) + 7.38 * 86_400_000)
  assert.ok(diasAteSizigia(quarto) > 5.5)
  assert.equal(regimeMare(quarto), 'quadratura')
})

test('distância até a sizígia nunca passa de meio meio-ciclo', () => {
  for (let i = 0; i < 60; i++) {
    const d = diasAteSizigia(new Date(Date.UTC(2026, 0, 1) + i * 86_400_000))
    assert.ok(d >= 0 && d <= 7.4, `dia ${i}: ${d}`)
  }
})

test('preamar dentro da janela de chegada é detectada', () => {
  const inicio = new Date('2026-07-12T20:00:00Z')
  const fim = new Date('2026-07-12T23:00:00Z')
  const c = cruzarComMare(inicio, fim, [{ quando: new Date('2026-07-12T21:30:00Z') }])
  assert.equal(c.coincide, true)
  assert.equal(c.coincidentes.length, 1)
})

test('preamar até duas horas fora da janela ainda conta', () => {
  const inicio = new Date('2026-07-12T20:00:00Z')
  const fim = new Date('2026-07-12T23:00:00Z')
  const antes = cruzarComMare(inicio, fim, [{ quando: new Date('2026-07-12T18:30:00Z') }])
  assert.equal(antes.coincide, true, 'a maré já está enchendo antes da preamar')
  const longe = cruzarComMare(inicio, fim, [{ quando: new Date('2026-07-12T15:00:00Z') }])
  assert.equal(longe.coincide, false)
})

test('sem tábua informada não há classificação', () => {
  const c = cruzarComMare(new Date('2026-07-12T20:00:00Z'), new Date('2026-07-12T23:00:00Z'), [])
  assert.equal(c.informadas, 0)
  assert.equal(agravamento(c), 'sem-tabua')
})

test('coincidir com preamar em sizígia é o pior caso', () => {
  const nova = Date.UTC(2000, 0, 6, 18, 14)
  const inicio = new Date(nova)
  const fim = new Date(nova + 3 * 3_600_000)
  const c = cruzarComMare(inicio, fim, [{ quando: new Date(nova + 3_600_000) }])
  assert.equal(c.regime, 'sizigia')
  assert.equal(agravamento(c), 'agrava')
})

test('preamar longe e fora de sizígia não agrava', () => {
  const quarto = Date.UTC(2000, 0, 6, 18, 14) + 7.38 * 86_400_000
  const c = cruzarComMare(
    new Date(quarto),
    new Date(quarto + 3_600_000),
    [{ quando: new Date(quarto + 10 * 3_600_000) }],
  )
  assert.equal(c.regime, 'quadratura')
  assert.equal(agravamento(c), 'nao-agrava')
})
