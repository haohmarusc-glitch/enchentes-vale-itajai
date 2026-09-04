/**
 * O CANAL RETIFICADO É O ITAJAÍ-MIRIM — e tem de ser pintado e animado como ele.
 *
 * O relato do morador foi curto: "itajaí mirim canal retificado não está com
 * animação". Está certo, e a causa era uma incoerência minha, não uma decisão:
 *
 *   `conferir_afluentes_chegam.py`   TRONCOS inclui 'mirim-canal-retificado'
 *   `MonitorBacia.tsx`               o mesmo id estava em AFLUENTES
 *   cadastro (DC-03…DC-06)           as quatro réguas dizem rio: "itajai-mirim"
 *
 * O efeito na tela era pior que o erro: o CURSO ANTIGO, ao lado, saía pintado
 * pela faixa de Brusque e animado — porque a geometria dele está dentro de
 * `itajai-mirim.geojson` —, enquanto o canal, que pelo JICA leva 2/3 da vazão,
 * saía cinza e parado. Mesma água, duas afirmações opostas na mesma tela, e a
 * cinzenta era a do canal que leva MAIS água.
 *
 * O que este arquivo NÃO afirma: nada mudou na régua DC-03. Ela continua
 * `alerta_automatico: false` (é de estuário, a maré cruza a cota sem enchente).
 * O canal é pintado pela âncora de MONTANTE — Brusque —, exatamente como já
 * acontecia com o curso antigo no mesmo trecho. Ver `afluenteNaoCorre.test.ts`.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { construirCena } from './mapaMotor'
import { CANAIS, CANAIS_DO_TRONCO, juntarCanais } from './canaisDoTronco'
import type { LonLat } from './mapaCanvas'
import type { Cidade } from '../dados/tipos'

const g = globalThis as unknown as { getComputedStyle?: unknown }
g.getComputedStyle = () => ({ getPropertyValue: () => '' })
const el = {} as Element

const MONITOR = readFileSync(new URL('../telas/MonitorBacia.tsx', import.meta.url), 'utf8')

function afluentes(): string[] {
  const i = MONITOR.indexOf('const AFLUENTES')
  assert.ok(i >= 0, 'AFLUENTES sumiu do MonitorBacia')
  return [...MONITOR.slice(i, MONITOR.indexOf(']', i)).matchAll(/'([a-z-]+)'/g)].map((m) => m[1]!)
}

function tracado(rioId: string): LonLat[][] {
  const f = JSON.parse(
    readFileSync(new URL(`../../../data/rios/${rioId}.geojson`, import.meta.url), 'utf8'),
  ) as { geometry: { type: string; coordinates: number[][] | number[][][] } }
  return f.geometry.type === 'MultiLineString'
    ? (f.geometry.coordinates as number[][][] as LonLat[][])
    : [f.geometry.coordinates as number[][] as LonLat[]]
}

const estacoes = JSON.parse(
  readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'),
) as { rios: Record<string, { cidades: Cidade[]; _topologia?: { tronco_sequencia?: string[] } }> }

const mirim = estacoes.rios['itajai-mirim']!
const eixo = mirim._topologia?.tronco_sequencia ?? mirim.cidades.map((c) => c.id)

/** Brusque ACIMA da cota: sem leitura, tudo já sairia cinza e o teste não testaria nada. */
const tempoReal = {
  situacao: 'ok',
  chuva: [],
  chuvaOk: true,
  coletadoEm: new Date(),
  fonte: null,
  leituras: [
    {
      estacao: 'brusque',
      rio: 'itajai-mirim',
      cidade: 'brusque',
      nivel_m: 99,
      medidoEm: new Date(),
      resgateDe: null,
    },
  ],
} as never

function cena(coords: LonLat[][]) {
  return construirCena(
    el,
    [{ rioId: 'itajai-mirim', coords, cidades: mirim.cidades, eixo }],
    tempoReal,
    new Date(),
    900,
    700,
    null,
  )
}

/** Comprimento desenhado (px) somado por faixa. */
function porFaixa(c: ReturnType<typeof cena>): Record<string, number> {
  const s: Record<string, number> = {}
  for (const t of c.trechos) s[t.faixa] = (s[t.faixa] ?? 0) + t.total
  return s
}

test('o canal retificado é canal do tronco, não afluente', () => {
  assert.deepEqual(CANAIS_DO_TRONCO['itajai-mirim'], ['mirim-canal-retificado'])
  assert.ok(
    !afluentes().includes('mirim-canal-retificado'),
    'o canal voltou para AFLUENTES do Monitor: afluente entra sem cidade ' +
      '(cidades: []), cai todo em sem-dado e VEL_FAIXA["sem-dado"] = 0',
  )
  assert.ok(
    MONITOR.includes('juntarCanais(baixados)'),
    'o Monitor deixou de fundir os canais: baixar o canal sem juntá-lo ao ' +
      'tronco é exatamente o defeito de antes',
  )
})

test('juntarCanais funde o canal no Mirim e o tira da lista de rios', () => {
  const tronco = tracado('itajai-mirim')
  const canal = tracado('mirim-canal-retificado')
  const saida = juntarCanais([
    { rioId: 'itajai-mirim', coords: tronco },
    { rioId: 'mirim-canal-retificado', coords: canal },
    { rioId: 'ribeirao-murta', coords: [[[-48.7, -26.9], [-48.69, -26.9]]] },
    { rioId: 'benedito', coords: null },
  ])
  assert.deepEqual(
    saida.map((r) => r.rioId),
    ['itajai-mirim', 'ribeirao-murta'],
    'o canal tem de sair da lista (foi fundido) e o que não baixou não entra',
  )
  const mirimSaida = saida.find((r) => r.rioId === 'itajai-mirim')!
  assert.equal(mirimSaida.coords.length, tronco.length + canal.length)
})

test('canal que não baixou não apaga o tronco', () => {
  // A rede cai no meio da chuva: o Mirim tem de continuar desenhado inteiro.
  const tronco = tracado('itajai-mirim')
  const saida = juntarCanais([
    { rioId: 'itajai-mirim', coords: tronco },
    { rioId: 'mirim-canal-retificado', coords: null },
  ])
  assert.equal(saida.length, 1)
  assert.equal(saida[0]!.coords.length, tronco.length)
})

test('CANAIS é o que o Monitor baixa — nem a mais nem a menos', () => {
  assert.deepEqual(CANAIS, ['mirim-canal-retificado'])
})

test('juntar o canal ao tronco PINTA o canal — e não cria cinza novo', () => {
  const so = cena(tracado('itajai-mirim'))
  const com = cena([...tracado('itajai-mirim'), ...tracado('mirim-canal-retificado')])

  const a = porFaixa(so)
  const b = porFaixa(com)
  const pintado = (s: Record<string, number>) =>
    Object.entries(s)
      .filter(([f]) => f !== 'sem-dado')
      .reduce((t, [, v]) => t + v, 0)

  assert.ok(pintado(a) > 0, 'o tronco tem de sair pintado — senão o teste é vazio')
  assert.ok(
    pintado(b) > pintado(a),
    `o canal entrou sem pintar nada: pintado ${pintado(a).toFixed(0)} → ${pintado(b).toFixed(0)} px`,
  )
  assert.ok(
    (b['sem-dado'] ?? 0) <= (a['sem-dado'] ?? 0) + 1e-6,
    `o canal entrou CINZA (${((b['sem-dado'] ?? 0) - (a['sem-dado'] ?? 0)).toFixed(0)} px ` +
      'de sem-dado a mais) — é exatamente o defeito relatado',
  )
})

test('o canal desenhado como rio à parte fica cinza — o defeito, reproduzido', () => {
  // A prova de que a correção é a JUNÇÃO, e não outra coisa: entregue como rio
  // próprio (que é como AFLUENTES o entregava), o canal não tem cidade a menos
  // de LIMITE_ANCORA_KM — Brusque está a 25 km — e sai todo em sem-dado.
  const solto = construirCena(
    el,
    [{
      rioId: 'mirim-canal-retificado',
      coords: tracado('mirim-canal-retificado'),
      cidades: [],
      eixo: undefined,
    }],
    tempoReal,
    new Date(),
    900,
    700,
    null,
  )
  assert.ok(solto.trechos.length > 0)
  for (const t of solto.trechos) assert.equal(t.faixa, 'sem-dado')
})
