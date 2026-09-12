import { test } from 'node:test'
import assert from 'node:assert/strict'
import { pesquisarVias } from './viasItajai'

test('busca ignora acentos, agrupa segmentos e exige três letras', () => {
  const dados: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features:
    ['São João', 'São João', 'José Bonifácio', null].map(nome => ({ type: 'Feature', geometry: { type: "MultiLineString", coordinates: [] }, properties: { nome } })) }
  assert.deepEqual(pesquisarVias(dados, 'sao'), ['São João'])
  assert.deepEqual(pesquisarVias(dados, 'JOSE'), ['José Bonifácio'])
  assert.deepEqual(pesquisarVias(dados, 'jo'), [])
  assert.deepEqual(pesquisarVias(dados, 'inexistente'), [])
})
