/**
 * C7, camada 2 (14/09/2026): a classificação que a Defesa Civil de SC publica
 * por estação pinta o trecho — tracejado, rotulado, parado — SÓ onde a cidade
 * não tem faixa municipal. Os testes constroem a cena pelo MOTOR de verdade
 * (`construirCena`), num rio de brinquedo com duas cidades em cima do traçado.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { construirCena, faixaEstadualDe, textoDoPino } from './mapaMotor'
import type { RioParaCena } from './mapaMotor'
import type { EstadoTempoReal } from '../dados/tempoReal'
import type { BrutoEstadual, NivelSc } from '../dados/nivelSc'
import type { Cidade } from '../dados/tipos'

const g = globalThis as unknown as { getComputedStyle?: unknown }
g.getComputedStyle = () => ({ getPropertyValue: () => '' })

const agora = new Date('2026-09-13T22:10:00-03:00')
const el = {} as unknown as Element

function cidade(id: string, lon: number, cotas: Record<string, number>): Cidade {
  return {
    id, nome: id, ordem: null, codigo_ana: null, verificado: false, fontes_tempo_real: [],
    cotas_m: cotas, coordenadas: [-27.0, lon],
  } as unknown as Cidade
}
// Um rio reto de oeste para leste; as cidades estão exatamente no traçado.
const semCota = cidade('lontras', -49.5, {})
const comCota = cidade('rio-do-sul', -49.0, { atencao: 3, alerta: 4 })
const rio: RioParaCena = {
  rioId: 'itajai-acu',
  coords: [[[-49.5, -27.0], [-49.25, -27.0], [-49.0, -27.0]]],
  cidades: [semCota, comCota],
}
const vazio: EstadoTempoReal = { situacao: 'ok', leituras: [], chuva: [], chuvaOk: true, coletadoEm: agora, fonte: null }
const bruto = (cidadeId: string, faixaEstadual: BrutoEstadual['faixaEstadual'], medidoEm = agora): BrutoEstadual =>
  ({ cidade: cidadeId, codigo: 'DCSC-00032', estacao: 'SDC-SC Lontras', nivelBrutoM: 5.39, medidoEm, faixaEstadual, motivoFaixaEstadual: null })

function cena(tempoReal: EstadoTempoReal, nivelSc: NivelSc) {
  return construirCena(el, [rio], tempoReal, agora, 400, 300, null, undefined, nivelSc)
}

test('sem faixa municipal, a classificação estadual pinta: tracejada, rotulada e parada', () => {
  const c = cena(vazio, new Map([['lontras', bruto('lontras', 'atencao')]]))
  const pino = c.pinos.find((p) => p.cidade.id === 'lontras')!
  assert.equal(pino.faixa, 'atencao')
  assert.equal(pino.origemFaixa, 'estadual')
  const trechos = c.trechos.filter((t) => t.cidadeId === 'lontras')
  assert.ok(trechos.length > 0, 'Lontras tem de ser âncora de algum trecho')
  for (const t of trechos) {
    assert.equal(t.faixa, 'atencao')
    assert.equal(t.origemFaixa, 'estadual')
    assert.equal(t.animacao, 'parada', 'cor estadual nunca autoriza correnteza')
  }
  const { sub } = textoDoPino(pino, { mostrarIdade: true, agora })
  assert.match(sub, /faixa estadual/)
  assert.match(sub, /5,39/)
})

test('"normal" do estado também pinta (decisão do Jefferson, 14/09/2026)', () => {
  const c = cena(vazio, new Map([['lontras', bruto('lontras', 'normal')]]))
  const pino = c.pinos.find((p) => p.cidade.id === 'lontras')!
  assert.equal(pino.faixa, 'normal')
  assert.equal(pino.origemFaixa, 'estadual')
})

test('leitura estadual velha (> 3 h) volta a cinza, como a municipal', () => {
  const velha = new Date(agora.getTime() - 4 * 3600_000)
  const c = cena(vazio, new Map([['lontras', bruto('lontras', 'atencao', velha)]]))
  const pino = c.pinos.find((p) => p.cidade.id === 'lontras')!
  assert.equal(pino.faixa, 'sem-dado')
  assert.notEqual(pino.origemFaixa, 'estadual')
})

test('a faixa municipal manda: com leitura na régua da cidade, a estadual é ignorada', () => {
  const comLeitura: EstadoTempoReal = {
    ...vazio,
    leituras: [{ estacao: 'Rio do Sul, Ponte Dom Tito Buss (Asthon)', rio: 'itajai-acu', cidade: 'rio-do-sul', nivel_m: 3.5, medidoEm: agora, resgateDe: null }],
  }
  const c = cena(comLeitura, new Map([['rio-do-sul', bruto('rio-do-sul', 'alerta')]]))
  const pino = c.pinos.find((p) => p.cidade.id === 'rio-do-sul')!
  assert.equal(pino.faixa, 'atencao', '3,5 m está entre a atenção (3) e o alerta (4) municipais')
  assert.equal(pino.origemFaixa, 'municipal')
  for (const t of c.trechos.filter((t) => t.cidadeId === 'rio-do-sul')) assert.notEqual(t.origemFaixa, 'estadual')
})

test('sem classificação estadual válida, nada muda: cinza continua cinza', () => {
  const c = cena(vazio, new Map([['lontras', bruto('lontras', null)]]))
  const pino = c.pinos.find((p) => p.cidade.id === 'lontras')!
  assert.equal(pino.faixa, 'sem-dado')
  const { sub } = textoDoPino(pino, { mostrarIdade: true, agora })
  assert.match(sub, /bruto/, 'sem faixa estadual o rótulo continua o do bruto')
  assert.doesNotMatch(sub, /faixa estadual/)
})

test('faixaEstadualDe é puro e recusa o que não pode pintar', () => {
  assert.equal(faixaEstadualDe(null, agora), null)
  assert.equal(faixaEstadualDe(bruto('x', null), agora), null)
  assert.equal(faixaEstadualDe({ ...bruto('x', 'alerta'), medidoEm: null }, agora), null)
  assert.equal(faixaEstadualDe(bruto('x', 'alerta', new Date(agora.getTime() - 200 * 60_000)), agora), null)
  assert.equal(faixaEstadualDe(bruto('x', 'emergencia'), agora), 'emergencia')
})
