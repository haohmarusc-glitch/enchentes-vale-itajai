/**
 * O pino de uma cidade fora do eixo fica no rio DELA quando ele está desenhado (06/10/2026).
 *
 * O defeito, visto pelo Jefferson no satélite: o pino de Ibirama caía no Açu, 2,6 km ao sul, no meio
 * do mato. A régua (DCSC-00020) está no Hercílio. Com dado real: traçados de `data/rios/` e a
 * coordenada do cadastro.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { construirCena, pontoDoPino, LIMITE_PINO_NO_RIO_DELA_KM } from './mapaMotor'
import { kmEntre, projetar, type LonLat } from './mapaCanvas'
import type { Cidade } from '../dados/tipos'

const g = globalThis as unknown as { getComputedStyle?: unknown }
g.getComputedStyle = () => ({ getPropertyValue: () => '' })
const el = {} as Element

const ler = (caminho: string) => JSON.parse(readFileSync(new URL(caminho, import.meta.url), 'utf8'))

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

const acu = linhas(ler('../../../data/rios/itajai-acu.geojson'))
const hercilio = linhas(ler('../../../data/rios/hercilio.geojson'))
const estacoes = ler('../../../data/estacoes.json') as {
  rios: Record<string, { cidades: Cidade[] }>
}
const ibirama = estacoes.rios['itajai-acu']!.cidades.find((c) => c.id === 'ibirama')!
const alvo: LonLat = [ibirama.coordenadas![1], ibirama.coordenadas![0]]

test('Ibirama, fora do eixo: o pino vai para o Hercílio, não para o Açu', () => {
  const p = pontoDoPino(alvo, acu, hercilio, false)
  assert.ok(kmEntre(alvo, p) < 0.2, `pino a ${kmEntre(alvo, p).toFixed(2)} km da régua`)
  // Sem o Hercílio desenhado, continua como antes: no tronco.
  const semRio = pontoDoPino(alvo, acu, [], false)
  assert.ok(kmEntre(alvo, semRio) > 2, 'sem o rio dela, o pino fica no tronco')
})

test('cidade do eixo continua no tronco, mesmo com outro rio mais perto', () => {
  assert.deepEqual(pontoDoPino(alvo, acu, hercilio, true), pontoDoPino(alvo, acu, [], true))
})

test('outro traçado longe demais não puxa o pino', () => {
  const longe: LonLat[][] = [[[alvo[0] + 0.05, alvo[1]]]] // ~5 km a leste
  assert.ok(kmEntre(alvo, longe[0]![0]!) > LIMITE_PINO_NO_RIO_DELA_KM)
  assert.deepEqual(pontoDoPino(alvo, acu, longe, false), pontoDoPino(alvo, acu, [], false))
})

test('na cena: o pino de Ibirama fica sobre o Hercílio, e o Açu continua sem a cor dela', () => {
  const cena = construirCena(
    el,
    [
      { rioId: 'itajai-acu', coords: acu, cidades: [ibirama], eixo: ['rio-do-sul'] },
      { rioId: 'hercilio', coords: hercilio, cidades: [] },
    ],
    { situacao: 'ok', chuva: [], chuvaOk: true, coletadoEm: new Date(), fonte: null, leituras: [] } as never,
    new Date(),
    800,
    600,
    null,
  )
  const pino = cena.pinos.find((p) => p.cidade.id === 'ibirama')
  assert.ok(pino, 'Ibirama continua no mapa')
  const [x, y] = projetar(cena.enq, pontoDoPino(alvo, acu, hercilio, false))
  assert.ok(Math.hypot(pino.x - x, pino.y - y) < 0.5, 'o pino é desenhado no ponto do Hercílio')
  for (const t of cena.trechos) assert.equal(t.faixa, 'sem-dado')
})
