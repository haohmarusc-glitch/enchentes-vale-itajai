import { test } from 'node:test'
import assert from 'node:assert/strict'
import { estadoDeEsvaziamento } from './esvaziamento'

test('comportas fechadas ou sem tendência: nada a afirmar além da comporta', () => {
  assert.equal(estadoDeEsvaziamento(0, 12, { rotulo: 'descendo', cmh: -5 }), null)
  assert.equal(estadoDeEsvaziamento(12, 12, null), null)
  assert.equal(estadoDeEsvaziamento(Number.NaN, 12, { rotulo: 'estável', cmh: 0 }), null)
})

test('soltando com o rio parado ou baixando é "esvaziando" — e a frase diz que a cor fica', () => {
  for (const rotulo of ['descendo', 'estável'] as const) {
    const e = estadoDeEsvaziamento(12, 12, { rotulo, cmh: rotulo === 'descendo' ? -8 : 0 })!
    assert.equal(e.rotulo, 'esvaziando')
    assert.match(e.frase, /a cor continua sendo a do nível/)
  }
})

test('soltando com o rio SUBINDO nunca vira "esvaziando": é a direção perigosa', () => {
  const e = estadoDeEsvaziamento(3, 12, { rotulo: 'subindo', cmh: 20 })!
  assert.equal(e.rotulo, 'vertendo com o rio subindo')
  assert.match(e.frase, /continua subindo/)
  assert.doesNotMatch(e.frase, /esvaziando/)
})
