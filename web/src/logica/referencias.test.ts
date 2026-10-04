import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  ehIBGE,
  legendaDaEscala,
  antesDaReguaDeclarada,
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

// Brusque, decisão do Jefferson de 04/10/2026 (opção B do item 4 da auditoria).
const BRUSQUE = {
  rotulo: 'Histórico na régua da Ponte Estaiada',
  desde: '2019-01-01',
  fonte_desde: 'boletins da Defesa Civil de Brusque',
  antes: 'da ANA (estação 83900000), com referência não conferida',
}

test('pico antes de "desde" fica fora da régua declarada, inclusive com data só de ano ou mês', () => {
  assert.equal(antesDaReguaDeclarada('1961-11-01', BRUSQUE), true)
  assert.equal(antesDaReguaDeclarada('1984-08', BRUSQUE), true)
  assert.equal(antesDaReguaDeclarada('2011', BRUSQUE), true)
  assert.equal(antesDaReguaDeclarada('2019-01-01', BRUSQUE), false)
  assert.equal(antesDaReguaDeclarada('2023-11-17', BRUSQUE), false)
  assert.equal(antesDaReguaDeclarada('1961-11-01', undefined), false)
})

test('Brusque: o título declara a régua e diz quantos picos ficam à parte', () => {
  const l = legendaDaEscala('Brusque', 'Ponte Estaiada – DCSC', [undefined, undefined, undefined], {
    declaracao: BRUSQUE,
    datas: ['1961-11-01', '2008-11', '2023-11-17'],
  })
  assert.equal(l.ehAviso, false)
  assert.ok(l.texto.startsWith('Histórico na régua da Ponte Estaiada: picos desde 2019'), l.texto)
  assert.ok(l.texto.includes('Os 2 picos anteriores'), l.texto)
  assert.ok(l.texto.includes('à parte'), l.texto)
  assert.ok(!/nível histórico de Brusque/i.test(l.texto), 'nunca o rótulo genérico')
  assert.ok(!l.texto.startsWith('Alturas na régua de Brusque'), 'não afirma a régua para a série inteira')
})

test('Brusque sem pico anterior a 2019 não fala em "à parte"', () => {
  const l = legendaDaEscala('Brusque', 'Ponte Estaiada – DCSC', [undefined], {
    declaracao: BRUSQUE,
    datas: ['2023-11-17'],
  })
  assert.ok(!l.texto.includes('à parte'), l.texto)
})

test('declaração do histórico não esconde mistura de referências', () => {
  const l = legendaDaEscala('Brusque', 'Ponte Estaiada – DCSC', ['régua', null], {
    declaracao: BRUSQUE,
    datas: ['2020-12-15', '2023-11-17'],
  })
  assert.equal(l.ehAviso, true)
})
