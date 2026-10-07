/**
 * PR 3 da classificação estadual × municipal (07/10/2026): o mapa do Monitor segue a mesma decisão do
 * motor que os cartões seguem (`estadoDaCidade`, PR 2), com os mesmos portões, e o painel diz qual
 * classificação pintou. Os casos vêm do gabarito compartilhado com o motor Python
 * (`data/classificacao-esperada.json`), com a saída REAL dele em `motor`.
 */
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { montarClassificacao } from '../dados/classificacao'
import { montarNivelSc } from '../dados/nivelSc'
import { buscarTempoReal } from '../dados/tempoReal'
import type { Cidade } from '../dados/tipos'
import { estadoDaCidade, type AoVivo } from '../dados/usarAoVivo'
import { construirCena, type RioParaCena } from './mapaMotor'
import { deBrasilia } from './tempoReal'
import { textoDaOrigemDaCor } from './textosDoPainel'

const g = globalThis as unknown as { getComputedStyle?: unknown }
g.getComputedStyle = () => ({ getPropertyValue: () => '' })
const el = {} as unknown as Element

interface Caso { id: string; agora_brasilia: string; leituras: unknown[]; nivel_sc: unknown; motor: unknown }
const gabarito = JSON.parse(
  readFileSync(new URL('../../../data/classificacao-esperada.json', import.meta.url), 'utf8'),
) as { casos: Caso[] }
const estacoes = JSON.parse(
  readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'),
) as { rios: Record<string, { cidades: Cidade[] }> }
const brusque = estacoes.rios['itajai-mirim']!.cidades.find((c) => c.id === 'brusque')!
const [lat, lon] = brusque.coordenadas as [number, number]
// Um rio reto passando pela régua de Brusque.
const rio: RioParaCena = {
  rioId: 'itajai-mirim',
  coords: [[[lon - 0.1, lat], [lon, lat], [lon + 0.1, lat]]],
  cidades: [brusque],
}

async function montar(id: string, comMotor: boolean) {
  const caso = gabarito.casos.find((c) => c.id === id)!
  const corpo = { coletado_em: '2026-10-07T16:05:00+00:00', leituras: caso.leituras }
  const tempoReal = await buscarTempoReal(undefined, async () => new Response(JSON.stringify(corpo), { status: 200 }))
  const nivelSc = montarNivelSc(caso.nivel_sc)
  const classificacao = comMotor ? montarClassificacao(caso.motor) : null
  const agora = deBrasilia(caso.agora_brasilia)
  return { tempoReal, nivelSc, classificacao, agora }
}

function pinoDe(m: Awaited<ReturnType<typeof montar>>, repro = false) {
  const cena = construirCena(
    el, [rio], m.tempoReal, m.agora, 400, 300, null,
    repro ? () => ({ nivel_m: 3.5, medidoEm: m.agora }) : undefined,
    m.nivelSc, undefined, undefined, m.classificacao,
  )
  return cena.pinos.find((p) => p.cidade.id === 'brusque')!
}

test('com o motor desta coleta, o mapa e o cartão pintam igual em todos os casos do gabarito', async () => {
  const divergentes: string[] = []
  for (const caso of gabarito.casos) {
    const m = await montar(caso.id, true)
    const pino = pinoDe(m)
    const v: AoVivo = { tempoReal: m.tempoReal, nivelSc: m.nivelSc, serie: { series: {} } as unknown as AoVivo['serie'], agora: m.agora, classificacao: m.classificacao }
    const e = estadoDaCidade(brusque, 'itajai-mirim', v)
    const doCartao = e.faixaEstadual ?? e.faixa
    if (pino.classificadaPor !== 'motor') divergentes.push(`${caso.id}: o mapa não usou o motor`)
    if (pino.faixa !== doCartao) divergentes.push(`${caso.id}: mapa ${pino.faixa} × cartão ${doCartao}`)
    if ((pino.origemFaixa === 'estadual') !== (e.faixaEstadual !== null)) divergentes.push(`${caso.id}: origem diferente`)
  }
  assert.deepEqual(divergentes, [])
})

test('leitura de outra régua: sem o motor o mapa pinta (regra antiga); com o motor, cinza como o cartão', async () => {
  assert.equal(pinoDe(await montar('leitura-de-outra-regua', false)).faixa, 'atencao')
  const pino = pinoDe(await montar('leitura-de-outra-regua', true))
  assert.equal(pino.faixa, 'sem-dado')
  assert.equal(textoDaOrigemDaCor(pino), null, 'sem cor, nada a atribuir: o "Por que está cinza?" explica')
})

test('fallback estadual pelo motor: tracejado no mapa e "Não representa as cotas municipais" no painel', async () => {
  const pino = pinoDe(await montar('so-estadual', true))
  assert.equal(pino.faixa, 'alerta')
  assert.equal(pino.origemFaixa, 'estadual')
  assert.equal(pino.origemDoMotor?.reguaId, 'DCSC-00019')
  assert.equal(
    textoDaOrigemDaCor(pino),
    'Cor do rio: classificação estadual (Defesa Civil de SC) — DCSC-00019. Não representa as cotas municipais.',
  )
})

test('municipal pelo motor: o painel nomeia a régua das cotas', async () => {
  const pino = pinoDe(await montar('exatamente-na-atencao', true))
  assert.equal(pino.faixa, 'atencao')
  assert.equal(textoDaOrigemDaCor(pino), 'Cor do rio: classificação municipal — Ponte Estaiada – DCSC (DCSC-00019).')
})

test('na reprodução o motor não entra: ele só fala da coleta de agora', async () => {
  const pino = pinoDe(await montar('exatamente-na-atencao', true), true)
  assert.equal(pino.classificadaPor, 'site')
  assert.equal(pino.origemDoMotor, null)
})

test('pela regra de sempre, o painel diz só o tipo — sem afirmar uma régua que a conta não conferiu', async () => {
  const pino = pinoDe(await montar('exatamente-na-atencao', false))
  assert.equal(pino.classificadaPor, 'site')
  assert.equal(textoDaOrigemDaCor(pino), 'Cor do rio: classificação municipal — cotas da cidade.')
  const estadual = pinoDe(await montar('so-estadual', false))
  assert.equal(
    textoDaOrigemDaCor({ ...estadual, codigoEstadual: 'DCSC-00019' }),
    'Cor do rio: classificação estadual (Defesa Civil de SC) — DCSC-00019. Não representa as cotas municipais.',
  )
})

test('cinza e várias réguas não têm origem de cor', () => {
  assert.equal(textoDaOrigemDaCor({ faixa: 'sem-dado' }), null)
  assert.equal(textoDaOrigemDaCor({ faixa: 'varias' }), null)
})
