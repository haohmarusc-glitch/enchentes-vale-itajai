/**
 * C7, camada 2 (14/09/2026): a classificação que a Defesa Civil de SC publica
 * por estação pinta o trecho — contínuo, com brilho e correnteza desde 08/10/2026; o pino é pontilhado e
 * rotulado — SÓ onde a cidade
 * não tem faixa municipal. Os testes constroem a cena pelo MOTOR de verdade
 * (`construirCena`), num rio de brinquedo com duas cidades em cima do traçado.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { PONTILHADO_PINO_ESTADUAL, construirCena, desenharBase, desenharPinos, faixaEstadualDe, textoDoPino } from './mapaMotor'
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

test('sem faixa municipal, a classificação estadual pinta: rotulada e correndo como a municipal', () => {
  const c = cena(vazio, new Map([['lontras', bruto('lontras', 'atencao')]]))
  const pino = c.pinos.find((p) => p.cidade.id === 'lontras')!
  assert.equal(pino.faixa, 'atencao')
  assert.equal(pino.origemFaixa, 'estadual')
  const trechos = c.trechos.filter((t) => t.cidadeId === 'lontras')
  assert.ok(trechos.length > 0, 'Lontras tem de ser âncora de algum trecho')
  for (const t of trechos) {
    assert.equal(t.faixa, 'atencao')
    assert.equal(t.origemFaixa, 'estadual')
    // 08/10/2026 (decisão do Jefferson): a faixa estadual corre como a municipal; antes ficava parada.
    assert.equal(t.animacao, 'direcional', 'faixa estadual tem correnteza')
  }
  const { sub } = textoDoPino(pino, { mostrarIdade: true, agora })
  assert.match(sub, /classificação estadual/)
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
  assert.doesNotMatch(sub, /classificação estadual/)
})

test('faixaEstadualDe é puro e recusa o que não pode pintar', () => {
  assert.equal(faixaEstadualDe(null, agora), null)
  assert.equal(faixaEstadualDe(bruto('x', null), agora), null)
  assert.equal(faixaEstadualDe({ ...bruto('x', 'alerta'), medidoEm: null }, agora), null)
  assert.equal(faixaEstadualDe(bruto('x', 'alerta', new Date(agora.getTime() - 200 * 60_000)), agora), null)
  assert.equal(faixaEstadualDe(bruto('x', 'emergencia'), agora), 'emergencia')
})

/** Um contexto de canvas que anota cada traço: o tracejado e o brilho em vigor no momento do `stroke`. */
function ctxQueAnota() {
  const tracos: { dash: number[]; blur: number }[] = []
  let dash: number[] = []
  let blur = 0
  const nada = () => {}
  const objeto = new Proxy({}, { get: () => nada })
  const ctx = new Proxy({}, {
    get: (_a, k) => k === 'setLineDash' ? (d: number[]) => { dash = d }
      : k === 'stroke' ? () => tracos.push({ dash, blur })
      : k === 'createLinearGradient' || k === 'createRadialGradient' ? () => objeto
      : k === 'measureText' ? (t: string) => ({ width: t.length * 6 })
      : nada,
    set: (_a, k, v) => { if (k === 'shadowBlur') blur = v as number; return true },
  })
  return { ctx: ctx as unknown as CanvasRenderingContext2D, tracos }
}

test('o rio da faixa estadual é traço contínuo e com brilho; só o pino fica pontilhado (08/10/2026)', () => {
  const c = cena(vazio, new Map([['lontras', bruto('lontras', 'atencao')]]))
  assert.ok(c.trechos.some((t) => t.origemFaixa === 'estadual'))
  const base = ctxQueAnota()
  desenharBase(base.ctx, c, 1, { sobreImagem: true })
  assert.ok(base.tracos.length > 0)
  assert.ok(base.tracos.every((t) => t.dash.length === 0), 'nenhum traço do rio sai tracejado')
  assert.ok(base.tracos.some((t) => t.blur > 0), 'o rio colorido tem brilho')
  const pinos = ctxQueAnota()
  desenharPinos(pinos.ctx, c, null)
  assert.ok(pinos.tracos.some((t) => t.dash.length === 2 && t.dash[0] === PONTILHADO_PINO_ESTADUAL[0]),
    'o pino estadual continua pontilhado')
})
