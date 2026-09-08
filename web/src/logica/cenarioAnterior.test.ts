import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { Evento } from '../dados/tipos'
import { cenarioDaCidade } from './cenarioAnterior'

const ev = (data: string, pico_m: number, extra: Partial<Evento> = {}): Evento => ({
  rio: 'itajai-mirim',
  cidade: 'brusque',
  data,
  pico_m,
  confianca: 'alta',
  fonte: 'teste',
  ...extra,
})

test('sem leitura não calcula nada', () => {
  const r = cenarioDaCidade(null, [ev('2011-09', 10.03)])
  assert.equal(r.cenario, null)
  assert.equal(r.motivo, 'sem-leitura')
})

test('sem pico nenhum não calcula nada', () => {
  assert.equal(cenarioDaCidade(4.2, []).motivo, 'sem-picos')
})

test('a distância é pico menos nível', () => {
  const { cenario } = cenarioDaCidade(4.69, [ev('2011-09', 10.03)])
  assert.equal(cenario!.marcas[0]!.diferenca, 5.34)
  assert.equal(cenario!.marcas[0]!.passou, false)
})

test('marca abaixo do nível conta como já passada, com diferença negativa', () => {
  const { cenario } = cenarioDaCidade(6.0, [ev('2020-12-15', 4.95)])
  assert.equal(cenario!.marcas[0]!.passou, true)
  assert.equal(cenario!.marcas[0]!.diferenca, -1.05)
})

test('a PRÓXIMA marca é a mais baixa das que estão acima, não a mais alta', () => {
  // O erro que este teste trava: anunciar "faltam 5,34 m" (a de 2011) quando
  // faltam 26 cm para a primeira marca que o rio encosta.
  const { cenario } = cenarioDaCidade(4.69, [
    ev('2011-09', 10.03),
    ev('2020-12-15', 4.95),
    ev('2022-06-23', 5.46),
  ])
  assert.equal(cenario!.proxima!.data, '2020-12-15')
  assert.equal(cenario!.proxima!.diferenca, 0.26)
})

test('sem nenhuma marca acima, proxima é nula', () => {
  const { cenario } = cenarioDaCidade(99, [ev('2011-09', 10.03)])
  assert.equal(cenario!.proxima, null)
  assert.equal(cenario!.ultimaPassada!.data, '2011-09')
})

test('as marcas saem da mais alta para a mais baixa', () => {
  const { cenario } = cenarioDaCidade(1.0, [ev('a', 5), ev('b', 10), ev('c', 7)])
  assert.deepEqual(cenario!.marcas.map((m) => m.pico), [10, 7, 5])
})

test('pico em IBGE não entra: é outra escala, 20 cm acima da régua', () => {
  const r = cenarioDaCidade(2.43, [ev('2011-09', 13.0, { referencia: 'IBGE (régua + 0,20 m)' })])
  assert.equal(r.cenario, null)
  assert.equal(r.motivo, 'referencia-de-outra-escala')
})

test('pico com referencia null não entra: ninguém conferiu a escala', () => {
  const r = cenarioDaCidade(2.43, [ev('1983-07', 15.34, { referencia: null })])
  assert.equal(r.motivo, 'referencia-de-outra-escala')
})

test('escala misturada não entra, mesmo que uma das duas sirva', () => {
  const r = cenarioDaCidade(2.43, [
    ev('1983-07', 15.34, { referencia: 'régua' }),
    ev('2011-09', 13.0, { referencia: 'IBGE (régua + 0,20 m)' }),
  ])
  assert.equal(r.motivo, 'referencia-misturada')
})

test('Blumenau inteira fica de fora — é a regra bloqueante, não um acaso', () => {
  const blumenau = [
    ev('1983-07', 15.34, { referencia: 'IBGE (régua + 0,20 m)' }),
    ev('2011-09', 12.8, { referencia: null }),
  ]
  assert.equal(cenarioDaCidade(2.43, blumenau).cenario, null)
})

test('campo AUSENTE passa, e a tela é avisada de que a referência não foi conferida', () => {
  const { cenario } = cenarioDaCidade(1.26, [ev('2011-09', 10.03)])
  assert.equal(cenario!.referenciaConferida, false)
  assert.equal(cenario!.marcas[0]!.referenciaConferida, false)
})

test('referencia régua declarada passa e vem marcada como conferida', () => {
  const { cenario } = cenarioDaCidade(3.0, [ev('2011-09', 8.0, { referencia: 'régua' })])
  assert.equal(cenario!.referenciaConferida, true)
})

test('pico não numérico é ignorado sem derrubar o resto', () => {
  const quebrado = { ...ev('x', 0), pico_m: undefined as unknown as number }
  const { cenario } = cenarioDaCidade(1, [quebrado, ev('2011-09', 10.03)])
  assert.equal(cenario!.marcas.length, 1)
})

// ── Contra o dado REAL, não contra fixture ────────────────────────────────
// A garantia que mais importa aqui é sobre Blumenau, e Blumenau é uma
// propriedade do arquivo, não do meu exemplo. Fixture provaria que a função
// funciona; isto prova que a REGRA está valendo no dado que vai ao ar.
import enchentes from '../../../data/enchentes.json'

const reais = (enchentes as { eventos: Evento[] }).eventos
const daCidade = (id: string) => reais.filter((e) => e.cidade === id)

test('REGRA BLOQUEANTE: Blumenau nunca produz distância, em nenhum nível', () => {
  // 113 picos e mesmo assim recusa: 72 em IBGE e 41 sem conferência, contra
  // uma leitura de régua. Se alguém "arrumar" as referências sem resolver os
  // 20 cm no HidroWeb, este teste cai — e tem de cair.
  for (const nivel of [0.5, 2.43, 8, 12.8, 15.5]) {
    const r = cenarioDaCidade(nivel, daCidade('blumenau'))
    assert.equal(r.cenario, null, `Blumenau produziu cenário em ${nivel} m`)
    assert.equal(r.motivo, 'referencia-misturada')
  }
})

test('Brusque compara, e sai marcada como referência não conferida', () => {
  const { cenario } = cenarioDaCidade(1.26, daCidade('brusque'))
  assert.ok(cenario)
  assert.equal(cenario.referenciaConferida, false)
  assert.equal(cenario.marcas.length, 8)
  assert.equal(cenario.marcas[0]!.pico, 10.5)
})

test('a marca mais alta de Brusque é a de 1984, e ela é única', () => {
  // Trava o conserto de 08/09/2026: o 10,30 m era divergência E registro, e
  // o duplicado empurrava todo o pódio uma posição.
  const { cenario } = cenarioDaCidade(0, daCidade('brusque'))
  assert.deepEqual(
    cenario!.marcas.slice(0, 3).map((m) => m.data),
    ['1984-08', '2011-09', '2023-11-17'],
  )
})

test('nenhuma cidade produz cenário com pico em IBGE, hoje ou depois', () => {
  const cidades = [...new Set(reais.map((e) => e.cidade))]
  for (const c of cidades) {
    const temIBGE = daCidade(c).some((e) => typeof e.referencia === 'string' && e.referencia.includes('IBGE'))
    if (!temIBGE) continue
    assert.equal(cenarioDaCidade(5, daCidade(c)).cenario, null, `${c} comparou com pico em IBGE`)
  }
})
