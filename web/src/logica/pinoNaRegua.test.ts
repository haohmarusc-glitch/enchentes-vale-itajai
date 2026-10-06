/**
 * O pino fica na régua, e a câmera da cidade o mostra (auditoria do Jefferson, 06/10/2026).
 *
 * O defeito: o pino era encaixado no traçado do rio da tela, e a câmera centrava na coordenada do
 * cadastro. Fora do tronco os dois ficavam longe (Ibirama 2,6 km, Ituporanga 28 km). Timbó e Rio dos
 * Cedros, ao norte da borda do traçado, abriam no MESMO lugar, porque a câmera é presa aos limites.
 *
 * Com dado real: os traçados de `data/rios/` e o cadastro, montados como o Monitor monta.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, readdirSync } from 'node:fs'
import { construirCena, pontoDoPino, type RioParaCena } from './mapaMotor'
import { kmEntre, maisProximoNoRio, type LonLat } from './mapaCanvas'
import { ALTURA_DO_PINO_COM_FOLHA, vistaAcimaDaFolha, vistaQueCabeAsReguas } from './vistaDaCidade'
import type { Cidade } from '../dados/tipos'

const g = globalThis as unknown as { getComputedStyle?: unknown }
g.getComputedStyle = () => ({ getPropertyValue: () => '' })
const el = {} as Element

const raiz = new URL('../../../data/', import.meta.url)
const ler = (caminho: string) => JSON.parse(readFileSync(new URL(caminho, raiz), 'utf8'))

function linhas(geo: unknown): LonLat[][] {
  const saida: LonLat[][] = []
  const anda = (o: unknown): void => {
    if (Array.isArray(o)) return o.forEach(anda)
    if (!o || typeof o !== 'object') return
    const x = o as { type?: string; coordinates?: unknown }
    if (x.type === 'LineString') saida.push(x.coordinates as LonLat[])
    else if (x.type === 'MultiLineString') saida.push(...(x.coordinates as LonLat[][]))
    else Object.values(x).forEach(anda)
  }
  anda(geo)
  return saida
}

const estacoes = ler('estacoes.json') as {
  rios: Record<
    string,
    { cidades: Cidade[]; _topologia?: { tronco_sequencia?: string[]; cabeceiras_paralelas?: string[] } }
  >
}

/** Os rios como o Monitor monta: tronco com cidades e eixo; os outros traçados só como linha. */
const rios: RioParaCena[] = readdirSync(new URL('rios/', raiz))
  .filter((f) => f.endsWith('.geojson'))
  .map((f) => {
    const rioId = f.replace('.geojson', '')
    const r = estacoes.rios[rioId]
    const t = r?._topologia
    return {
      rioId,
      coords: linhas(ler(`rios/${f}`)),
      cidades: r?.cidades ?? [],
      eixo: t ? [...(t.tronco_sequencia ?? []), ...(t.cabeceiras_paralelas ?? [])] : undefined,
    }
  })

const semLeitura = { situacao: 'ok', chuva: [], chuvaOk: true, coletadoEm: new Date(), fonte: null, leituras: [] } as never
const L = 1000
const A = 700
const cena = (vista?: Parameters<typeof construirCena>[9]) =>
  construirCena(el, rios, semLeitura, new Date(), L, A, null, undefined, undefined, vista)

const cidades = [...new Map(Object.values(estacoes.rios).flatMap((r) => r.cidades).map((c) => [c.id, c])).values()]

test('o pino de cada cidade fica na coordenada da régua (e a declarada sem régua, se houver, no rio)', () => {
  const base = cena()
  for (const c of cidades.filter((c) => c.coordenadas)) {
    const p = base.pinos.find((x) => x.cidade.id === c.id)
    assert.ok(p, `${c.id} sumiu do mapa`)
    const regua: LonLat = [c.coordenadas![1], c.coordenadas![0]]
    if (c.coordenadas_sao_da_regua === false) {
      assert.equal(p.aproximado, true, `${c.id}: posição aproximada tem de vir marcada`)
      const acu = rios.find((r) => r.rioId === 'itajai-acu')!.coords
      assert.deepEqual([p.lon, p.lat], maisProximoNoRio(acu, regua), `${c.id}: no rio, não no pluviômetro`)
    } else {
      assert.equal(p.aproximado, false, c.id)
      assert.ok(kmEntre(regua, [p.lon, p.lat]) < 0.001, `${c.id}: pino a ${kmEntre(regua, [p.lon, p.lat]).toFixed(2)} km da régua`)
    }
  }
})

test('na bacia inteira, todo pino cabe na tela — inclusive Timbó e Rio dos Cedros, ao norte do traçado', () => {
  const base = cena()
  for (const p of base.pinos) {
    assert.ok(p.x >= 0 && p.x <= L && p.y >= 0 && p.y <= A, `${p.cidade.id} fora da tela: ${p.x.toFixed(0)}, ${p.y.toFixed(0)}`)
  }
})

test('abrir cada cidade com a câmera dela deixa o pino dela no meio da tela', () => {
  const base = cena()
  for (const p of base.pinos) {
    const v = vistaQueCabeAsReguas([p.lat, p.lon], [], base.limitesBase, A / L)
    assert.ok(v, p.cidade.id)
    const foco = cena(v).pinos.find((x) => x.cidade.id === p.cidade.id)!
    assert.ok(
      Math.abs(foco.x - L / 2) < 2 && Math.abs(foco.y - A / 2) < 2,
      `${p.cidade.id}: pino em ${foco.x.toFixed(0)}, ${foco.y.toFixed(0)}, não no centro`,
    )
  }
})

test('Timbó e Rio dos Cedros abrem em lugares diferentes (a câmera não fica presa na borda)', () => {
  const base = cena()
  const centro = (id: string) => {
    const p = base.pinos.find((x) => x.cidade.id === id)!
    return vistaQueCabeAsReguas([p.lat, p.lon], [], base.limitesBase, A / L)!
  }
  const t = centro('timbo')
  const r = centro('rio-dos-cedros')
  assert.ok(kmEntre([t.centroLon, t.centroLat], [r.centroLon, r.centroLat]) > 5)
})

test('pontoDoPino: sem coordenada, nada; coordenada declarada sem régua, no rio e aproximada', () => {
  const rio: LonLat[][] = [[[-49, -27], [-48.9, -27]]]
  assert.equal(pontoDoPino({}, rio), null)
  assert.deepEqual(pontoDoPino({ coordenadas: [-27.02, -48.95] }, rio), { ponto: [-48.95, -27.02], aproximado: false })
  assert.deepEqual(pontoDoPino({ coordenadas: [-27.02, -48.95], coordenadas_sao_da_regua: false }, rio), {
    ponto: [-49, -27],
    aproximado: true,
  })
})

test('no celular, a câmera põe o pino acima da folha do painel; no computador, no meio', () => {
  const estreita = (w: number, h: number) =>
    construirCena(el, rios, semLeitura, new Date(), w, h, null)
  for (const [w, h] of [[390, 640], [360, 600]] as const) {
    const base = estreita(w, h)
    for (const p of base.pinos) {
      const v = vistaAcimaDaFolha(vistaQueCabeAsReguas([p.lat, p.lon], [], base.limitesBase, h / w)!, base.limitesBase, w, h)
      const foco = construirCena(el, rios, semLeitura, new Date(), w, h, null, undefined, undefined, v)
        .pinos.find((x) => x.cidade.id === p.cidade.id)!
      assert.ok(Math.abs(foco.y - h * ALTURA_DO_PINO_COM_FOLHA) < 3, `${w}×${h} ${p.cidade.id}: y=${foco.y.toFixed(0)}`)
      assert.ok(Math.abs(foco.x - w / 2) < 3, `${p.cidade.id}: x=${foco.x.toFixed(0)}`)
    }
  }
  const v = { zoom: 10, centroLon: -49, centroLat: -27 }
  assert.deepEqual(vistaAcimaDaFolha(v, cena().limitesBase, 1000, 700), v)
})

test('Blumenau: pino na régua da Ponte Adolfo Konder, sem "aproximado" (decisão de 06/10/2026)', () => {
  const p = cena().pinos.find((x) => x.cidade.id === 'blumenau')!
  assert.equal(p.aproximado, false)
  assert.deepEqual([p.lat, p.lon], [-26.9186, -49.0656])
  assert.equal(p.cidade.coordenadas_fonte, 'Prefeitura de Blumenau/Defesa Civil — Ponte Adolfo Konder, Beira-Rio')
})
