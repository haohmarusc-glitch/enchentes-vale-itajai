/**
 * O Monitor por cidade é o MESMO mapa, enquadrado noutro lugar. Estes testes
 * travam as duas coisas que o zoom não pode fazer: inventar posição de cidade
 * sem coordenada, e deixar a tela em branco.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { VISTA_INTEIRA } from './mapaCanvas'
import {
  KM_NA_TELA,
  kmDaVista,
  vistaDaCidade,
  vistaInicial,
  vistaQueCabeAsReguas,
  zoomParaKm,
} from './vistaDaCidade'

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

/* ------------------------------------------------------------------------- *
 * O enquadramento tem de CABER as réguas da cidade, não só o pino.
 * ------------------------------------------------------------------------- */

/** Quantos km de largura e de altura a tela mostra nesta vista. */
function janela(v: { zoom: number }, proporcaoTela: number) {
  const largura = kmDaVista(BACIA, v.zoom)
  return { largura, altura: largura * proporcaoTela }
}

/** O ponto cai dentro da janela desenhada? */
function cabe(
  v: { zoom: number; centroLat: number; centroLon: number },
  p: { lat: number; lon: number },
  proporcaoTela: number,
): boolean {
  const { largura, altura } = janela(v, proporcaoTela)
  const dx = Math.abs(p.lon - v.centroLon) * 111.32 * Math.cos((27 * Math.PI) / 180)
  const dy = Math.abs(p.lat - v.centroLat) * 110.57
  return dx <= largura / 2 && dy <= altura / 2
}

test('AS ONZE RÉGUAS DE ITAJAÍ cabem no enquadramento da cidade', () => {
  /**
   * O caso real que motivou a função. Medido em 06/09/2026 contra o cadastro:
   * as réguas de Itajaí se espalham por 20,8 x 17,6 km, e a DC-10 (Bairro
   * Limoeiro) fica a 24,2 km do pino — FORA da janela fixa de 24 km que o
   * enquadramento usava. Uma tela chamada "Itajaí" escondia uma das onze
   * réguas da própria cidade, sem dizer que faltava.
   *
   * A proporção 0,5 é a pior realista (tela deitada): é nela que a dispersão
   * norte-sul some primeiro.
   */
  const d = JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf-8'))
  const reguas = (d.estacoes_tempo_real as { cidade: string; lat?: number; lon?: number }[])
    .filter((e) => e.cidade === 'itajai' && typeof e.lat === 'number' && typeof e.lon === 'number')
    .map((e) => ({ lat: e.lat as number, lon: e.lon as number }))
  assert.equal(reguas.length, 11, 'o cadastro deveria ter 11 réguas de Itajaí com coordenada')

  const pino = (d.rios['itajai-acu'].cidades as { id: string; coordenadas: number[] }[]).find(
    (c) => c.id === 'itajai',
  )!.coordenadas as [number, number]

  for (const proporcao of [0.5, 1, 1.8]) {
    const v = vistaQueCabeAsReguas(pino, reguas, BACIA, proporcao)!
    assert.ok(v, `sem vista para proporção ${proporcao}`)
    for (const r of reguas) {
      assert.ok(cabe(v, r, proporcao), `régua ${r.lat},${r.lon} fora da tela (proporção ${proporcao})`)
    }
    assert.ok(cabe(v, { lat: pino[0], lon: pino[1] }, proporcao), 'o pino saiu da tela')
  }
})

test('a janela FIXA de 24 km deixava a DC-10 de fora — a prova do bug', () => {
  // Se este teste parar de falhar em espírito (ou seja, se a DC-10 passar a
  // caber em 24 km centrada no pino), é porque a coordenada dela mudou — e aí
  // é o cadastro que precisa de conferência, não este arquivo.
  const d = JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf-8'))
  const dez = (d.estacoes_tempo_real as { codigo?: string; lat?: number; lon?: number }[]).find(
    (e) => e.codigo === 'DC-10',
  )!
  const pino = (d.rios['itajai-acu'].cidades as { id: string; coordenadas: number[] }[]).find(
    (c) => c.id === 'itajai',
  )!.coordenadas
  const antiga = vistaDaCidade(pino, BACIA, KM_NA_TELA)!
  assert.equal(cabe(antiga, { lat: dez.lat!, lon: dez.lon! }, 1), false)
})

test('o piso de 24 km continua valendo para cidade de régua única', () => {
  // O motivo original não morreu: cabe o vizinho de montante e o de jusante.
  const uma = [{ lat: -26.92, lon: -49.06 }]
  const v = vistaQueCabeAsReguas([-26.92, -49.06], uma, BACIA, 1)!
  assert.ok(Math.abs(kmDaVista(BACIA, v.zoom) - KM_NA_TELA) < 1e-6)
})

test('a dispersão MAIOR que o piso abre a tela, em vez de cortar', () => {
  const largas = [
    { lat: -26.92, lon: -49.4 },
    { lat: -26.92, lon: -48.8 },
  ]
  const v = vistaQueCabeAsReguas([-26.92, -49.1], largas, BACIA, 1)!
  const km = kmDaVista(BACIA, v.zoom)
  assert.ok(km > KM_NA_TELA, `esperava mais que ${KM_NA_TELA} km, veio ${km}`)
  for (const p of largas) assert.ok(cabe(v, p, 1), 'ponto cortado mesmo com a tela aberta')
})

test('a proporção da tela entra na conta — deitada não corta o norte-sul', () => {
  // Dispersão só NORTE-SUL: numa tela deitada ela é a que some primeiro.
  const verticais = [
    { lat: -27.05, lon: -49.0 },
    { lat: -26.85, lon: -49.0 },
  ]
  for (const proporcao of [0.4, 0.56, 1, 2]) {
    const v = vistaQueCabeAsReguas([-26.95, -49.0], verticais, BACIA, proporcao)!
    for (const p of verticais) {
      assert.ok(cabe(v, p, proporcao), `cortado na proporção ${proporcao}`)
    }
  }
  // Proporção inválida não vira NaN silencioso nem tela em branco.
  for (const ruim of [0, -1, Number.NaN, Number.POSITIVE_INFINITY]) {
    assert.ok(vistaQueCabeAsReguas([-26.95, -49.0], verticais, BACIA, ruim as number))
  }
})

test('sem pino E sem régua não se inventa um centro', () => {
  assert.equal(vistaQueCabeAsReguas(null, [], BACIA, 1), null)
  assert.equal(vistaQueCabeAsReguas([Number.NaN, -49], [], BACIA, 1), null)
  // Régua sem pino ainda enquadra: o que não pode é não haver ponto nenhum.
  assert.ok(vistaQueCabeAsReguas(null, [{ lat: -26.9, lon: -49 }], BACIA, 1))
})
