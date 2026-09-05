/**
 * O Monitor por cidade é o MESMO mapa, enquadrado noutro lugar. Estes testes
 * travam as duas coisas que o zoom não pode fazer: inventar posição de cidade
 * sem coordenada, e deixar a tela em branco.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { VISTA_INTEIRA } from './mapaCanvas'
import { KM_NA_TELA, kmDaVista, vistaDaCidade, vistaInicial, zoomParaKm } from './vistaDaCidade'

/** Um retângulo do tamanho da bacia do Itajaí: ~1,6° de longitude (~158 km). */
const BACIA = { minLon: -50.2, maxLon: -48.6, minLat: -27.7, maxLat: -26.5 }

test('o zoom sai da LARGURA da bacia, não de uma constante cravada', () => {
  const z = zoomParaKm(BACIA, KM_NA_TELA)
  const larguraKm = (BACIA.maxLon - BACIA.minLon) * 111.32 * Math.cos((27 * Math.PI) / 180)
  assert.ok(Math.abs(z - larguraKm / KM_NA_TELA) < 1e-9)
  // Uma bacia DUAS vezes maior pede o dobro do zoom para mostrar os mesmos km.
  const maior = { ...BACIA, maxLon: BACIA.minLon + (BACIA.maxLon - BACIA.minLon) * 2 }
  assert.ok(Math.abs(zoomParaKm(maior, KM_NA_TELA) - 2 * z) < 1e-9)
})

test('o zoom nunca fica abaixo de 1 — não se mostra além da bacia', () => {
  assert.equal(zoomParaKm(BACIA, 10_000), 1)
  assert.equal(zoomParaKm({ minLon: 0, maxLon: 0, minLat: 0, maxLat: 0 }), 1)
  assert.equal(zoomParaKm(BACIA, 0), 1)
  assert.equal(zoomParaKm(BACIA, Number.NaN), 1)
})

test('a vista centra na cidade, invertendo [lat, lon] do cadastro', () => {
  const v = vistaDaCidade([-26.92, -48.66], BACIA)
  assert.equal(v?.centroLat, -26.92)
  assert.equal(v?.centroLon, -48.66)
  assert.ok((v?.zoom ?? 0) > 1)
})

test('cidade SEM coordenada não vira uma posição inventada', () => {
  for (const c of [null, undefined, [], [-26.9], [-26.9, -48.6, 0], ['a', 'b'], [Number.NaN, -48.6]]) {
    assert.equal(vistaDaCidade(c as never, BACIA), null, JSON.stringify(c))
  }
})

test('sem coordenada a tela abre na BACIA INTEIRA, nunca em branco', () => {
  // Mapa vazio num aplicativo de enchente é pior que mapa sem zoom.
  assert.deepEqual(vistaInicial(null, BACIA), VISTA_INTEIRA)
  assert.notDeepEqual(vistaInicial([-26.92, -48.66], BACIA), VISTA_INTEIRA)
})

test('o enquadramento cabe a cidade E os vizinhos de montante e jusante', () => {
  // 24 km: os trechos do tronco medem de 8 a 30 km, então quase sempre entra ao
  // menos um vizinho. Enquadrar só o município esconderia o trecho de onde a
  // água está chegando.
  assert.ok(KM_NA_TELA >= 16, 'apertado demais esconderia o vizinho de montante')
  assert.ok(KM_NA_TELA <= 40, 'largo demais e volta a ser a bacia inteira')
})

test('kmDaVista é o inverso exato de zoomParaKm', () => {
  for (const km of [4, 8, 24, 60]) {
    assert.ok(Math.abs(kmDaVista(BACIA, zoomParaKm(BACIA, km)) - km) < 1e-6, String(km))
  }
  // Zoom 1 é a bacia inteira; zoom inválido não vira NaN silencioso.
  assert.ok(Math.abs(kmDaVista(BACIA, 1) - kmDaVista(BACIA, 0.5)) < 1e-9)
  assert.ok(Number.isNaN(kmDaVista({ minLon: 0, maxLon: 0, minLat: 0, maxLat: 0 }, 2)))
})
