/**
 * A conta do zoom do Monitor.
 *
 * O que estes testes protegem não é geometria bonita: é a diferença entre o
 * zoom do mapa e a lupa do navegador. A lupa estica o bitmap — o rio fica
 * borrado e os rótulos saem da tela. Aqui a janela geográfica encolhe e o
 * desenho é REFEITO, então o traçado continua fino e nítido e o rótulo continua
 * do tamanho de sempre.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { aplicarVista, desprojetar, enquadrar, projetar, VISTA_INTEIRA } from './mapaCanvas'

const BACIA = { minLon: -50, maxLon: -48, minLat: -28, maxLat: -26 }

test('zoom 1 devolve a bacia inteira, sem tocar em nada', () => {
  assert.deepEqual(aplicarVista(BACIA, VISTA_INTEIRA), BACIA)
  assert.deepEqual(aplicarVista(BACIA, { zoom: 1, centroLon: -49.5, centroLat: -27.5 }), BACIA)
})

test('zoom 2 mostra metade da largura e metade da altura', () => {
  const v = aplicarVista(BACIA, { zoom: 2, centroLon: -49, centroLat: -27 })
  assert.equal(v.maxLon - v.minLon, 1)
  assert.equal(v.maxLat - v.minLat, 1)
  assert.equal((v.minLon + v.maxLon) / 2, -49)
})

test('sem centro escolhido, o zoom cai no meio da bacia', () => {
  const v = aplicarVista(BACIA, { zoom: 4, centroLon: NaN, centroLat: NaN })
  assert.equal((v.minLon + v.maxLon) / 2, -49)
  assert.equal((v.minLat + v.maxLat) / 2, -27)
})

test('o centro é preso dentro da bacia: arrasto longo não leva ao mar aberto', () => {
  const v = aplicarVista(BACIA, { zoom: 2, centroLon: -10, centroLat: 10 })
  // Preso no canto nordeste da bacia, não em (-10, 10).
  assert.equal((v.minLon + v.maxLon) / 2, -48)
  assert.equal((v.minLat + v.maxLat) / 2, -26)
})

test('zoom menor que 1 não encolhe o mapa para fora da bacia', () => {
  assert.deepEqual(aplicarVista(BACIA, { zoom: 0.2, centroLon: -49, centroLat: -27 }), BACIA)
})

test('desprojetar é o inverso de projetar — é assim que se sabe onde o dedo tocou', () => {
  const e = enquadrar(BACIA, 400, 300, 12)
  for (const p of [
    [-49.5, -27.5],
    [-48.1, -26.2],
    [-50, -28],
  ] as [number, number][]) {
    const [x, y] = projetar(e, p)
    const [lon, lat] = desprojetar(e, x, y)
    assert.ok(Math.abs(lon - p[0]) < 1e-9, `lon ${lon} != ${p[0]}`)
    assert.ok(Math.abs(lat - p[1]) < 1e-9, `lat ${lat} != ${p[1]}`)
  }
})

test('com zoom, um grau de longitude ocupa MAIS pixels — é o desenho que cresce', () => {
  const semZoom = enquadrar(aplicarVista(BACIA, VISTA_INTEIRA), 400, 400, 0)
  const comZoom = enquadrar(
    aplicarVista(BACIA, { zoom: 4, centroLon: -49, centroLat: -27 }),
    400,
    400,
    0,
  )
  assert.ok(
    comZoom.escala > semZoom.escala * 3.9,
    `escala ${comZoom.escala} devia ser ~4x ${semZoom.escala}`,
  )
})
