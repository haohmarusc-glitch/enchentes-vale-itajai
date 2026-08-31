import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'
import {
  dentroDaColecao,
  dentroDaGeometria,
  dentroDoAnel,
  dentroDoPoligono,
} from './pontoNaMancha.ts'
import type { Anel, Coordenada } from './pontoNaMancha.ts'

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), '../../..')

/** Um quadrado de (0,0) a (10,10). */
const QUADRADO: Anel = [
  [0, 0],
  [10, 0],
  [10, 10],
  [0, 10],
  [0, 0],
]

test('ponto no meio do quadrado está dentro', () => {
  assert.equal(dentroDoAnel([5, 5], QUADRADO), true)
})

test('ponto fora do quadrado está fora', () => {
  for (const p of [[-1, 5], [11, 5], [5, -1], [5, 11]] as Coordenada[]) {
    assert.equal(dentroDoAnel(p, QUADRADO), false, JSON.stringify(p))
  }
})

test('ponto na altura exata de um vértice não é contado duas vezes', () => {
  // O caso clássico que quebra contagem de cruzamentos ingênua: a semirreta
  // passa por (0,10) e (10,10) ao mesmo tempo. Um ponto à esquerda, na mesma
  // altura, tem de continuar fora.
  assert.equal(dentroDoAnel([-1, 10], QUADRADO), false)
  assert.equal(dentroDoAnel([-1, 0], QUADRADO), false)
})

test('buraco no polígono é fora', () => {
  const buraco: Anel = [
    [4, 4],
    [6, 4],
    [6, 6],
    [4, 6],
    [4, 4],
  ]
  assert.equal(dentroDoPoligono([5, 5], [QUADRADO, buraco]), false)
  assert.equal(dentroDoPoligono([2, 2], [QUADRADO, buraco]), true)
})

test('polígono vazio não engole ponto nenhum', () => {
  assert.equal(dentroDoPoligono([5, 5], []), false)
})

test('MultiPolygon: dentro de qualquer uma das partes', () => {
  const longe: Anel = [
    [100, 100],
    [110, 100],
    [110, 110],
    [100, 110],
    [100, 100],
  ]
  const geo = { type: 'MultiPolygon', coordinates: [[QUADRADO], [longe]] }
  assert.equal(dentroDaGeometria([5, 5], geo), true)
  assert.equal(dentroDaGeometria([105, 105], geo), true)
  assert.equal(dentroDaGeometria([50, 50], geo), false)
})

test('geometria que não é polígono devolve falso em vez de adivinhar', () => {
  assert.equal(dentroDaGeometria([5, 5], { type: 'Point', coordinates: [5, 5] }), false)
  assert.equal(dentroDaGeometria([5, 5], null), false)
  assert.equal(dentroDaGeometria([5, 5], { type: 'MultiPolygon' }), false)
})

test('coleção sem feições não devolve dentro', () => {
  assert.equal(dentroDaColecao([5, 5], { type: 'FeatureCollection', features: [] }), false)
  assert.equal(dentroDaColecao([5, 5], null), false)
})

test('nas manchas reais de Itajaí, o mar fica fora e a mancha de 2008 tem área', () => {
  // 2008 é a maior mancha do acervo. O teste não escolhe um ponto "que deu
  // certo": varre uma grade sobre a cidade e cobra que ALGUM ponto caia dentro
  // e que um ponto a 50 km mar adentro fique fora. Se a leitura de coordenada
  // inverter lat/lon, as duas coisas quebram.
  const geo = JSON.parse(
    readFileSync(resolve(RAIZ, 'data/manchas/itajai/enchente2008.geojson'), 'utf8'),
  )
  let dentro = 0
  for (let lon = -48.75; lon <= -48.6; lon += 0.005) {
    for (let lat = -26.98; lat <= -26.86; lat += 0.005) {
      if (dentroDaColecao([lon, lat], geo)) dentro += 1
    }
  }
  assert.ok(dentro > 20, `só ${dentro} pontos da grade caíram na mancha de 2008`)
  assert.equal(dentroDaColecao([-48.0, -26.9], geo), false, 'mar aberto não alagou')
})

test('a mancha de 1983 é menor que a de 2008 na mesma grade', () => {
  const conta = (arquivo: string) => {
    const geo = JSON.parse(readFileSync(resolve(RAIZ, arquivo), 'utf8'))
    let n = 0
    for (let lon = -48.75; lon <= -48.6; lon += 0.005) {
      for (let lat = -26.98; lat <= -26.86; lat += 0.005) {
        if (dentroDaColecao([lon, lat], geo)) n += 1
      }
    }
    return n
  }
  assert.ok(conta('data/manchas/itajai/enchente1983.geojson') <
    conta('data/manchas/itajai/enchente2008.geojson'))
})
