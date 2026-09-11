import { test } from 'node:test'
import assert from 'node:assert/strict'
import { montarNivelSc } from './nivelSc'

/*
 * O nível bruto estadual preenche as lacunas do site, mas NUNCA como cota. O que
 * estes casos travam: uma leitura por cidade (a mais fresca), lixo recusado, e o
 * mapa vazio quando o arquivo não existe — jamais um número inventado.
 */

test('monta uma leitura por cidade a partir do JSON', () => {
  const mapa = montarNivelSc({
    leituras: [
      { cidade: 'ibirama', estacao: 'SDC-SC Ibirama', nivel_bruto_m: 2.83, medido_em: '2026-09-01T20:10:00' },
    ],
  })
  const ibirama = mapa.get('ibirama')
  assert.equal(ibirama?.nivelBrutoM, 2.83)
  assert.equal(ibirama?.estacao, 'SDC-SC Ibirama')
  assert.ok(ibirama?.medidoEm instanceof Date)
})

test('a mais fresca vence quando a cidade tem duas', () => {
  const mapa = montarNivelSc({
    leituras: [
      { cidade: 'taio', estacao: 'A', nivel_bruto_m: 6.6, medido_em: '2026-09-01T18:00:00' },
      { cidade: 'taio', estacao: 'B', nivel_bruto_m: 6.7, medido_em: '2026-09-01T20:00:00' },
    ],
  })
  assert.equal(mapa.get('taio')?.nivelBrutoM, 6.7)
})

test('recusa leitura sem cidade, sem estação ou fora da faixa', () => {
  const mapa = montarNivelSc({
    leituras: [
      { cidade: '', estacao: 'X', nivel_bruto_m: 1 },
      { cidade: 'y', estacao: '', nivel_bruto_m: 1 },
      { cidade: 'z', estacao: 'Z', nivel_bruto_m: 399 },
      { cidade: 'w', estacao: 'W', nivel_bruto_m: 0 },
    ],
  })
  assert.equal(mapa.size, 0)
})

test('arquivo ausente ou quebrado vira mapa vazio, nunca número inventado', () => {
  assert.equal(montarNivelSc(null).size, 0)
  assert.equal(montarNivelSc({}).size, 0)
  assert.equal(montarNivelSc({ leituras: 'nao-e-lista' }).size, 0)
})

test('chuva estadual distingue zero medido de acumulado ausente ou inválido', () => {
  for (const [entrada, esperado] of [[0, 0], [12.4, 12.4], [null, null], [undefined, null], [-1, null], [NaN, null], [Infinity, null], ['12', null], [1001, null]]) {
    const mapa = montarNivelSc({leituras:[{cidade:'ascurra',estacao:'DCSC Ascurra',nivel_bruto_m:8,chuva_24h_mm:entrada}]})
    assert.equal(mapa.get('ascurra')?.chuva24hMm, esperado)
  }
})

test('acumulado acompanha a estação selecionada, sem somar janelas móveis', () => {
  const mapa = montarNivelSc({leituras:[
    {cidade:'ascurra',estacao:'A',nivel_bruto_m:8,chuva_24h_mm:20,medido_em:'2026-09-11T08:00:00'},
    {cidade:'ascurra',estacao:'B',nivel_bruto_m:8,chuva_24h_mm:2,medido_em:'2026-09-11T09:00:00'},
  ]})
  assert.equal(mapa.get('ascurra')?.chuva24hMm, 2)
  assert.equal(mapa.get('ascurra')?.estacao, 'B')
})
