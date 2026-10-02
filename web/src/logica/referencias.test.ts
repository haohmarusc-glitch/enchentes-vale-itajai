import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  ehIBGE,
  legendaDaEscala,
  misturaReferencias,
  referenciasDistintas,
  textoDaReferencia,
} from './referencias'

test('campo ausente e campo nulo não são a mesma referência', () => {
  // Ausente = registro antigo, assumido na régua. Nulo = ninguém conferiu.
  // Juntar os dois esconderia a mistura, que é justamente o que se quer ver.
  assert.equal(referenciasDistintas([undefined, null]).size, 2)
  assert.ok(misturaReferencias([undefined, null]))
})

test('uma referência só não é mistura', () => {
  assert.ok(!misturaReferencias(['régua', 'régua']))
  assert.ok(!misturaReferencias([undefined, undefined]))
  assert.ok(!misturaReferencias([]))
})

test('régua e IBGE juntas são mistura', () => {
  assert.ok(misturaReferencias(['régua', 'IBGE (régua + 0,20 m)']))
})

test('com referência única o cabeçalho afirma a régua', () => {
  const l = legendaDaEscala('Blumenau', 'Ponte Adolfo Konder', ['régua', 'régua'])
  assert.equal(l.texto, 'Alturas na régua de Blumenau (Ponte Adolfo Konder). Não compare com outra cidade.')
  assert.equal(l.ehAviso, false)
})

test('com mistura o cabeçalho NÃO afirma a régua', () => {
  // Este é o defeito: o topo dizia "na régua de Blumenau" com barras em IBGE.
  const l = legendaDaEscala('Blumenau', 'Ponte Adolfo Konder', ['régua', 'IBGE (régua + 0,20 m)'])
  assert.ok(!l.texto.includes('na régua de'), l.texto)
  assert.ok(l.texto.includes('mais de uma referência'), l.texto)
  assert.equal(l.ehAviso, true)
})

test('o nome da régua some quando a escala está misturada', () => {
  // Citar a régua ao lado de barras que não são dela é a mesma afirmação falsa.
  const l = legendaDaEscala('Blumenau', 'Ponte Adolfo Konder', ['régua', null])
  assert.ok(!l.texto.includes('Ponte Adolfo Konder'), l.texto)
})

test('cidade sem régua cadastrada não inventa parênteses vazio', () => {
  const l = legendaDaEscala('Gaspar', null, ['régua'])
  assert.equal(l.texto, 'Alturas na régua de Gaspar. Não compare com outra cidade.')
})

test('o aviso de não comparar entre cidades vale nos dois casos', () => {
  for (const refs of [['régua'], ['régua', 'IBGE (régua + 0,20 m)']]) {
    assert.ok(legendaDaEscala('X', null, refs).texto.includes('Não compare com outra cidade'))
  }
})

test('rótulo IBGE na tela diz de QUAL régua são os 20 cm (planilha Cordero, 02/10/2026)', () => {
  // A régua de hoje lê 0,40 m acima da antiga: o IBGE fica 20 cm ABAIXO dela.
  // O rótulo cru "régua + 0,20 m" faria somar onde é preciso subtrair.
  const t = textoDaReferencia('IBGE (régua + 0,20 m)')
  assert.match(t, /régua antiga \+ 0,20 m/)
  assert.match(t, /régua de hoje − 0,20 m/)
  assert.ok(ehIBGE('IBGE (régua + 0,20 m)'))
  assert.ok(!ehIBGE('régua') && !ehIBGE(null) && !ehIBGE(undefined))
})

test('rótulos sem IBGE não mudam', () => {
  assert.equal(textoDaReferencia(undefined), 'régua')
  assert.equal(textoDaReferencia(null), 'não declarada')
  assert.equal(textoDaReferencia('régua'), 'régua')
})
