/**
 * O seletor de régua de Itajaí, com o cadastro real das onze réguas (06/10/2026).
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { construirCena, MARGEM } from './mapaMotor'
import { reguasNoMapa } from './reguasNoMapa'
import { opcoesDoSeletor, TODAS, vistaDaRegua } from './seletorDeRegua'
import { ALTURA_DO_PINO_COM_FOLHA } from './vistaDaCidade'
import { projetar, type LonLat } from './mapaCanvas'
import type { EstacaoTempoReal } from '../dados/tipos'

const g = globalThis as unknown as { getComputedStyle?: unknown }
g.getComputedStyle = () => ({ getPropertyValue: () => '' })
const el = {} as Element

const estacoes = JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8')) as {
  estacoes_tempo_real: EstacaoTempoReal[]
}
const reguas = reguasNoMapa(estacoes.estacoes_tempo_real, [], new Date())
const acu = (JSON.parse(readFileSync(new URL('../../../data/rios/itajai-acu.geojson', import.meta.url), 'utf8'))
  .geometry.coordinates) as LonLat[][]

test('Itajaí: "Todas as 11 réguas" primeiro, depois DC-01 a DC-11 em ordem', () => {
  const op = opcoesDoSeletor(reguas, 'itajai')
  assert.deepEqual(op[0], { valor: TODAS, rotulo: 'Todas as 11 réguas' })
  assert.deepEqual(
    op.slice(1).map((o) => o.valor),
    ['DC-01', 'DC-02', 'DC-03', 'DC-04', 'DC-05', 'DC-06', 'DC-07', 'DC-08', 'DC-09', 'DC-10', 'DC-11'],
  )
  assert.match(op[1]!.rotulo, /^DC-01 · /)
})

test('cidade de uma régua só (ou nenhuma) não ganha seletor', () => {
  assert.deepEqual(opcoesDoSeletor(reguas, 'blumenau'), [])
  assert.deepEqual(opcoesDoSeletor(reguas, 'brusque'), [])
})

const semLeitura = { situacao: 'ok', chuva: [], chuvaOk: true, coletadoEm: new Date(), fonte: null, leituras: [] } as never
const cenaCom = (w: number, h: number, vista?: Parameters<typeof construirCena>[9]) =>
  construirCena(el, [{ rioId: 'itajai-acu', coords: acu, cidades: [] }], semLeitura, new Date(), w, h, null, undefined, undefined, vista)

test('escolher uma régua põe o ponto dela no centro (computador) e acima do painel (celular)', () => {
  const daCidade = reguas.filter((r) => r.cidade === 'itajai')
  for (const [w, h, alturaEsperada] of [[1000, 700, 0.5], [390, 640, ALTURA_DO_PINO_COM_FOLHA]] as const) {
    const base = cenaCom(w, h)
    for (const r of daCidade) {
      const cena = cenaCom(w, h, vistaDaRegua(r, base.limitesBase, w, h, MARGEM)!)
      const [x, y] = projetar(cena.enq, [r.lon, r.lat])
      assert.ok(Math.abs(x - w / 2) < 3, `${w}×${h} ${r.codigo}: x=${x.toFixed(0)}`)
      assert.ok(Math.abs(y - h * alturaEsperada) < 3, `${w}×${h} ${r.codigo}: y=${y.toFixed(0)}`)
    }
  }
})

