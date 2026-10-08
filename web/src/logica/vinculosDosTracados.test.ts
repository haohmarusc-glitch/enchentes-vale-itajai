/**
 * Vínculo traçado × cidade × régua (07/10/2026, "Monitor: Ituporanga e barragens", seções 1/1B). Os testes
 * montam a cena pelo MOTOR de verdade (`construirCena`), com os traçados REAIS de `data/rios/` e o cadastro
 * real, pela mesma `rioParaCena` que o Monitor usa.
 */
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { montarNivelSc } from '../dados/nivelSc'
import type { EstadoTempoReal } from '../dados/tempoReal'
import type { Cidade } from '../dados/tipos'
import type { LonLat } from './mapaCanvas'
import { cidadeNoTrecho, construirCena, trechoCinzaNoPonto, type Cena, type RioParaCena } from './mapaMotor'
import {
  SEM_VINCULO,
  VINCULOS,
  arestasDoAlcance,
  kmEntre,
  rioParaCena,
  textoDoAlcance,
  textoDoTrechoCinza,
  vinculoDoTracado,
} from './vinculosDosTracados'

const g = globalThis as unknown as { getComputedStyle?: unknown }
g.getComputedStyle = () => ({ getPropertyValue: () => '' })
const el = {} as unknown as Element

const raiz = new URL('../../../data/', import.meta.url)
const estacoes = JSON.parse(readFileSync(new URL('estacoes.json', raiz), 'utf8')) as {
  rios: Record<string, { cidades: Cidade[]; _topologia?: { tronco_sequencia?: string[]; cabeceiras_paralelas?: string[] } }>
}
const cidadesDoRio = (id: string): Cidade[] => estacoes.rios[id]?.cidades ?? []
const eixoDoRio = (id: string): string[] | undefined => {
  const t = estacoes.rios[id]?._topologia
  return t ? [...(t.tronco_sequencia ?? []), ...(t.cabeceiras_paralelas ?? [])] : undefined
}
const tracado = (id: string): LonLat[][] =>
  JSON.parse(readFileSync(new URL(`rios/${id}.geojson`, raiz), 'utf8')).geometry.coordinates
const TRONCO = new Set(['itajai-acu', 'itajai-mirim'])
const rio = (id: string): RioParaCena => rioParaCena({ rioId: id, coords: tracado(id) }, TRONCO.has(id), cidadesDoRio, eixoDoRio)

const AGORA = new Date('2026-10-07T19:10:00-03:00')
const semLeitura: EstadoTempoReal = { situacao: 'ok', leituras: [], coletadoEm: AGORA } as unknown as EstadoTempoReal

/** A rede estadual com as faixas pedidas, todas medidas às 19:00 (fresca às 19:10). */
function nivelSc(faixas: Record<string, string | null>, medido = '2026-10-07T19:00:00') {
  return montarNivelSc({
    leituras: Object.entries(faixas).map(([cidade, faixa]) => ({
      cidade, estacao: `SDC-SC ${cidade}`, codigo: 'DCSC-X', nivel_bruto_m: 2.5, medido_em: medido,
      classificacao_estadual: faixa ? { faixa } : null,
    })),
  })
}

function cena(rios: RioParaCena[], sc = nivelSc({}), leituraNaHora?: Parameters<typeof construirCena>[7]): Cena {
  return construirCena(el, rios, semLeitura, AGORA, 1200, 900, null, leituraNaHora, sc)
}
const doRio = (c: Cena, id: string) => c.trechos.filter((t) => t.rioId === id)
const pintados = (c: Cena, id: string) => doRio(c, id).filter((t) => t.faixa !== 'sem-dado')

test('cada vínculo tem caminho no traçado real, da estação até o fim, com o comprimento declarado', () => {
  for (const v of VINCULOS) {
    const r = arestasDoAlcance(tracado(v.tracado), v.inicio, v.fim)
    assert.ok(r, `${v.tracado}: sem caminho`)
    assert.ok(Math.abs(r.km - v.km) < 0.2, `${v.tracado}: ${r.km.toFixed(1)} km × ${v.km} declarados`)
    assert.ok(r.km < tracado(v.tracado).flat().length, v.tracado)
    assert.ok(cidadesDoRio(v.grupo).some((c) => c.id === v.cidade), `${v.cidade} não está em ${v.grupo}`)
  }
})

test('Ituporanga com faixa válida colore só o trecho dela do Itajaí do Sul; o Açu fica independente', () => {
  const c = cena([rio('itajai-acu'), rio('itajai-do-sul')], nivelSc({ ituporanga: 'emergencia' }))
  const sul = pintados(c, 'itajai-do-sul')
  assert.ok(sul.length > 0, 'o Sul continuou cinza')
  for (const t of sul) {
    assert.equal(t.faixa, 'emergencia')
    assert.equal(t.origemFaixa, 'estadual', 'a origem estadual se mantém no trecho')
    assert.equal(t.cidadeId, 'ituporanga')
    assert.equal(t.animacao, 'parada', 'cor estadual não autoriza correnteza')
  }
  // Rio acima da estação: cinza, com o motivo.
  const fora = doRio(c, 'itajai-do-sul').filter((t) => t.motivoCinza === 'fora-do-alcance')
  assert.ok(fora.length > 0, 'o trecho acima da estação recebeu a cor')
  assert.ok(fora.every((t) => t.faixa === 'sem-dado' && t.cidadeId === null))
  // Nada do Açu leva a cor de Ituporanga.
  assert.ok(doRio(c, 'itajai-acu').every((t) => t.cidadeId !== 'ituporanga'))
  // O pino continua um só, no grupo de dados da cidade.
  const pinos = c.pinos.filter((p) => p.cidade.id === 'ituporanga')
  assert.equal(pinos.length, 1)
  assert.equal(pinos[0]!.rioId, 'itajai-acu')
  assert.equal(pinos[0]!.faixa, 'emergencia')
})

test('o toque no trecho devolve a cidade que decidiu a cor', () => {
  const c = cena([rio('itajai-acu'), rio('itajai-do-sul')], nivelSc({ ituporanga: 'alerta' }))
  const t = pintados(c, 'itajai-do-sul')[0]!
  const [x, y] = t.pts[Math.floor(t.pts.length / 2)]!
  assert.equal(cidadeNoTrecho(c.trechos, x, y, 2)?.cidadeId, 'ituporanga')
})

test('vínculo cujo grupo de dados é outro rio: Guabiruba (traçado guabiruba, dados no Mirim)', () => {
  const c = cena([rio('itajai-mirim'), rio('guabiruba')], nivelSc({ guabiruba: 'atencao' }))
  assert.ok(pintados(c, 'guabiruba').every((t) => t.faixa === 'atencao' && t.cidadeId === 'guabiruba'))
  assert.ok(pintados(c, 'guabiruba').length > 0)
  assert.ok(doRio(c, 'itajai-mirim').every((t) => t.cidadeId !== 'guabiruba'), 'Guabiruba voltou ao tronco do Mirim')
})

test('sem faixa publicada (Guabiruba hoje), o trecho fica cinza: falta de faixa não é nível normal', () => {
  const c = cena([rio('guabiruba')], nivelSc({ guabiruba: null }))
  assert.equal(pintados(c, 'guabiruba').length, 0)
})

test('leitura velha não pinta o trecho', () => {
  const c = cena([rio('itajai-do-sul')], nivelSc({ ituporanga: 'emergencia' }, '2026-10-07T14:00:00'))
  assert.equal(pintados(c, 'itajai-do-sul').length, 0)
})

test('na reprodução o trecho não usa a classificação de agora', () => {
  const c = cena([rio('itajai-do-sul')], nivelSc({ ituporanga: 'emergencia' }), () => null)
  assert.equal(pintados(c, 'itajai-do-sul').length, 0)
})

test('Timbó e Rio dos Cedros separados: o Cedros colore só o Cedros; o Benedito fica sem vínculo', () => {
  const c = cena([rio('benedito'), rio('rio-dos-cedros')], nivelSc({ timbo: 'alerta', 'rio-dos-cedros': 'atencao' }))
  assert.equal(pintados(c, 'benedito').length, 0, 'Timbó coloriu o Benedito por proximidade')
  assert.ok(doRio(c, 'benedito').every((t) => t.motivoCinza === 'sem-vinculo'))
  assert.ok(pintados(c, 'rio-dos-cedros').length > 0)
  assert.ok(pintados(c, 'rio-dos-cedros').every((t) => t.cidadeId === 'rio-dos-cedros' && t.origemFaixa === 'estadual'))
  // O alcance do Cedros pára na próxima estação (Timbó 2), antes do Benedito.
  assert.ok(doRio(c, 'rio-dos-cedros').some((t) => t.motivoCinza === 'fora-do-alcance'))
})

test('Ibirama colore o Hercílio só da estação até a confluência', () => {
  const c = cena([rio('hercilio')], nivelSc({ ibirama: 'atencao' }))
  assert.ok(pintados(c, 'hercilio').length > 0)
  const km = (t: { pts: [number, number][] }) => t.pts.length
  const total = doRio(c, 'hercilio').reduce((s, t) => s + km(t), 0)
  const cor = pintados(c, 'hercilio').reduce((s, t) => s + km(t), 0)
  assert.ok(cor < total / 2, 'a cor de Ibirama subiu o Hercílio')
})

test('Trombudo Central: a faixa estadual da própria estação, até Agronômica; sem conversão municipal', () => {
  const c = cena([rio('trombudo')], nivelSc({ 'trombudo-central': 'normal' }))
  const t = pintados(c, 'trombudo')
  assert.ok(t.length > 0)
  assert.ok(t.every((x) => x.origemFaixa === 'estadual' && x.faixa === 'normal'))
  assert.ok(doRio(c, 'trombudo').some((x) => x.motivoCinza === 'fora-do-alcance'))
})

test('ramos Oeste e Sul: Taió não pinta o Sul, e Ituporanga não pinta o Oeste', () => {
  const c = cena([rio('itajai-acu'), rio('itajai-do-sul')], nivelSc({ taio: 'alerta', ituporanga: 'normal' }))
  assert.ok(doRio(c, 'itajai-do-sul').every((t) => t.cidadeId !== 'taio'))
  assert.ok(doRio(c, 'itajai-acu').every((t) => t.cidadeId !== 'ituporanga'))
})

test('tronco: a primeira régua não pinta o rio acima dela (Taió no Oeste; Vidal Ramos no Mirim)', () => {
  const c = cena([rio('itajai-acu'), rio('itajai-mirim')], nivelSc({ taio: 'alerta', 'vidal-ramos': 'atencao' }))
  const acimaTaio = doRio(c, 'itajai-acu').filter((t) => t.motivoCinza === 'acima-da-primeira-regua')
  assert.ok(acimaTaio.length > 0, 'nada ficou cinza acima de Taió')
  assert.ok(acimaTaio.every((t) => t.faixa === 'sem-dado' && t.cidadeId === null))
  assert.ok(doRio(c, 'itajai-acu').some((t) => t.cidadeId === 'taio' && t.faixa === 'alerta'), 'Taió parou de pintar o rio abaixo')
  assert.ok(doRio(c, 'itajai-mirim').some((t) => t.motivoCinza === 'acima-da-primeira-regua'))
  assert.ok(doRio(c, 'itajai-mirim').some((t) => t.cidadeId === 'vidal-ramos' && t.faixa === 'atencao'))
})

test('ribeirões de Itajaí sem respaldo e cursos sem régua ficam sem classificação, com o motivo', () => {
  for (const id of ['ribeirao-murta', 'ribeirao-canhanduba', 'rio-conceicao', 'ribeirao-taquaras', 'rio-rafael']) {
    const r = rio(id)
    assert.equal(r.semVinculo, true, id)
    assert.equal(r.cidades.length, 0, id)
    assert.ok(SEM_VINCULO[id], `${id}: sem motivo escrito`)
  }
  assert.match(textoDoTrechoCinza('sem-vinculo', 'ribeirao-murta'), /DC-07 e DC-09/)
})

test('segmento desconectado ou estação longe do traçado: sem caminho, sem cor', () => {
  const dois: LonLat[][] = [[[-49.0, -27.0], [-48.99, -27.0]], [[-48.9, -27.0], [-48.89, -27.0]]]
  assert.equal(arestasDoAlcance(dois, [-49.0, -27.0], [-48.89, -27.0]), null, 'atravessou o vão')
  assert.equal(arestasDoAlcance(dois, [-49.5, -27.0], [-48.99, -27.0]), null, 'estação a 50 km casou com o traçado')
  assert.ok(arestasDoAlcance(dois, [-49.0, -27.0], [-48.99, -27.0]))
})

test('o toque no trecho cinza devolve o motivo', () => {
  const c = cena([rio('benedito')])
  const t = doRio(c, 'benedito')[0]!
  const [x, y] = t.pts[0]!
  assert.deepEqual(trechoCinzaNoPonto(c.trechos, x, y, 2), { rioId: 'benedito', motivo: 'sem-vinculo' })
})

test('o painel diz até onde a cor vale', () => {
  const v = vinculoDoTracado('itajai-do-sul')!
  const texto = textoDoAlcance(v, 'Itajaí do Sul')
  assert.match(texto, /DCSC-00039/)
  assert.match(texto, /39,2 km/)
  assert.match(texto, /Não vale para o rio acima da estação/)
  assert.ok(kmEntre(v.inicio, v.fim) > 20)
})
