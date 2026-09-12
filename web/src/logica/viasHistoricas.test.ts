import { describe, it } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import catalogo from '../../../data/manchas/itajai/vias-historicas.json'
import { cheiaMaisProxima } from './compararCheias'

describe('vias históricas de Itajaí', () => {
  it('preserva as contagens e usa apenas linhas com coordenadas locais', () => {
    assert.deepEqual(catalogo.camadas.map(c => c.feicoes), [555, 409])
    for (const c of catalogo.camadas) {
      const geo = JSON.parse(readFileSync(new URL('../../../data/' + c.arquivo, import.meta.url), 'utf8')) as GeoJSON.FeatureCollection
      assert.equal(geo.features.length, c.feicoes)
      for (const f of geo.features) {
        assert.ok(['LineString', 'MultiLineString'].includes(f.geometry.type))
        const g = f.geometry as GeoJSON.LineString | GeoJSON.MultiLineString
        const pontos = g.type === 'LineString' ? g.coordinates : g.coordinates.flat()
        for (const [lon, lat] of pontos) {
          assert.ok(lon! > -49)
          assert.ok(lon! < -48)
          assert.ok(lat! > -28)
          assert.ok(lat! < -26)
        }
      }
    }
  })
  it('não seleciona vias por nível atual sem pico e régua documentados', () => {
    assert.equal(cheiaMaisProxima(catalogo.camadas, [{ cidade: 'itajai', estacao: 'DC-01', nivel_m: 2, medidoEm: new Date() }], new Date()), null)
  })
})
