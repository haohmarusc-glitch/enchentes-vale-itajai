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
import { cidadeNoTrecho, construirCena, reguaNoTrecho, trechoCinzaNoPonto, type Cena, type RioParaCena } from './mapaMotor'
import type { ReguaNoMapa } from './reguasNoMapa'
import {
  SEM_VINCULO,
  VINCULOS,
  VINCULOS_DE_REGUA,
  arestasAJusanteDe,
  arestasDoAlcance,
  kmEntre,
  rioParaCena,
  textoDoAlcance,
  textoDoAlcanceDaRegua,
  textoDoTrechoCinza,
  vinculoDaRegua,
  vinculoDeReguaDoTracado,
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

function cena(rios: RioParaCena[], sc = nivelSc({}), leituraNaHora?: Parameters<typeof construirCena>[7], reguas?: ReguaNoMapa[]): Cena {
  return construirCena(el, rios, semLeitura, AGORA, 1200, 900, null, leituraNaHora, sc, undefined, undefined, undefined, reguas)
}

/** A DC-08 como `reguasNoMapa` a entrega: com a faixa decidida, ou sem cor e com o motivo. */
function dc08(faixa: ReguaNoMapa['faixa'], motivoSemCor: string | null = null): ReguaNoMapa {
  return {
    codigo: 'DC-08', titulo: 'DC-08 Ribeirão Canhanduba - Rua Benjamin Dagnoni', cidade: 'itajai', nome: 'Rio do Meio',
    lon: -48.711948, lat: -26.979694, nivel: 1.15, medidoEm: new Date('2026-10-07T19:00:00-03:00'),
    faixa, motivoSemCor, cotas: { atencao: 1.7, alerta: 2.3, emergencia: 2.89 },
  }
}
const doRio = (c: Cena, id: string) => c.trechos.filter((t) => t.rioId === id)
const pintados = (c: Cena, id: string) => doRio(c, id).filter((t) => t.faixa !== 'sem-dado')

test('a jusante da DC-11 pelo traçado real do Açu: a Volta de Cima inteira entra, o rio acima não (08/10/2026)', () => {
  const acu = JSON.parse(readFileSync(new URL('../../../data/rios/itajai-acu.geojson', import.meta.url), 'utf8'))
  const coords = acu.geometry.coordinates as LonLat[][]
  const dc11: LonLat = [-48.761549, -26.879641]
  const foz = coords.flat().reduce((a, p) => (p[0] > a[0] ? p : a))
  const arestas = arestasAJusanteDe(coords, dc11, foz, 0.5)
  assert.ok(arestas && arestas.size > 0)
  // As nove arestas da volta para o norte logo abaixo da régua (linha 50, arestas 7–15), que a projeção na reta
  // Ilhota→Itajaí deixava cinza: 2,86 km ao longo da Rua Santa Regina.
  for (let i = 7; i <= 15; i++) assert.ok(arestas.has(`50:${i}`), `linha 50, aresta ${i} fica a jusante da DC-11`)
  // O rio acima da régua, na mesma linha, não entra.
  assert.ok(!arestas.has('50:1') && !arestas.has('50:2'), 'o rio acima da DC-11 não pinta')
  // Nada acima de Ilhota entra: toda aresta a jusante está a leste de −48,80.
  let km = 0
  coords.forEach((linha, li) => {
    for (let i = 1; i < linha.length; i++) {
      if (!arestas.has(`${li}:${i}`)) continue
      assert.ok(linha[i]![0] > -48.80 && linha[i - 1]![0] > -48.80, `aresta ${li}:${i} longe demais da foz`)
      km += kmEntre(linha[i - 1]!, linha[i]!)
    }
  })
  // O comprimento a jusante da DC-11 pelo canal é 27,3 km (medido em 08/10/2026); braços de ilha somam um pouco.
  assert.ok(km >= 27 && km <= 32, `${km.toFixed(1)} km a jusante da DC-11`)
  // Ponto longe de qualquer vértice: sem referência, nada pintado.
  assert.equal(arestasAJusanteDe(coords, [-48.9, -26.5], foz, 0.5), null)
})

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
  for (const id of ['ribeirao-murta', 'ribeirao-taquaras', 'rio-rafael']) {
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

/*
 * Vínculo traçado × RÉGUA (08/10/2026, decisão do Jefferson: "ribeirões com cota devem pintar conforme cota").
 * O Canhanduba pinta pela DC-08 de Itajaí — a mesma decisão do pino da régua —, só da régua para baixo, e PARADO.
 */
test('cada vínculo de régua tem caminho no traçado real, da régua até o fim, com o comprimento declarado', () => {
  assert.ok(VINCULOS_DE_REGUA.length > 0)
  for (const v of VINCULOS_DE_REGUA) {
    const r = arestasDoAlcance(tracado(v.tracado), v.inicio, v.fim)
    assert.ok(r, `${v.tracado}: sem caminho`)
    assert.ok(Math.abs(r.km - v.km) < 0.2, `${v.tracado}: ${r.km.toFixed(1)} km × ${v.km} declarados`)
    assert.ok(!(v.tracado in SEM_VINCULO), `${v.tracado} está em SEM_VINCULO e em VINCULOS_DE_REGUA ao mesmo tempo`)
    assert.ok(!vinculoDoTracado(v.tracado), `${v.tracado} tem vínculo de cidade e de régua ao mesmo tempo`)
    assert.ok(cidadesDoRio('itajai-mirim').some((c) => c.id === v.cidade) || cidadesDoRio('itajai-acu').some((c) => c.id === v.cidade))
  }
  assert.equal(vinculoDaRegua('DC-08')?.tracado, 'ribeirao-canhanduba')
  assert.equal(vinculoDeReguaDoTracado('ribeirao-canhanduba')?.regua, 'DC-08')
  assert.equal(vinculoDaRegua('DC-07'), null, 'a Murta continua sem vínculo: DC-07 sem cota conferida, DC-09 de estuário')
})

test('o Canhanduba pinta pela DC-08: a cor do pino da régua, da régua para baixo, sem cidade e parado', () => {
  const r = rio('ribeirao-canhanduba')
  assert.equal(r.semVinculo, undefined)
  assert.equal(r.cidades.length, 0, 'o ribeirão não ganhou cidade: a cor vem da régua')
  assert.deepEqual(r.reguaVinculada, { codigo: 'DC-08', cidade: 'itajai' })
  const c = cena([r], undefined, undefined, [dc08('atencao')])
  const cor = pintados(c, 'ribeirao-canhanduba')
  assert.ok(cor.length > 0, 'o Canhanduba continuou cinza com a DC-08 em atenção')
  for (const t of cor) {
    assert.equal(t.faixa, 'atencao')
    assert.equal(t.cidadeId, null, 'trecho de régua não tem cidade')
    assert.equal(t.reguaCodigo, 'DC-08')
    assert.equal(t.animacao, 'parada', 'pintar pela cota não faz o curso correr (decisão à parte)')
  }
  const acima = doRio(c, 'ribeirao-canhanduba').filter((t) => t.motivoCinza === 'fora-do-alcance')
  assert.ok(acima.length > 0, 'o ribeirão acima da régua recebeu a cor')
  assert.ok(acima.every((t) => t.faixa === 'sem-dado' && !t.reguaCodigo))
  assert.equal(c.pinos.length, 0, 'régua não vira pino de cidade')
  // O toque no trecho pintado devolve a régua, não uma cidade.
  const t = cor[0]!
  const [x, y] = [(t.pts[0]![0] + t.pts[1]![0]) / 2, (t.pts[0]![1] + t.pts[1]![1]) / 2]
  assert.equal(reguaNoTrecho(c.trechos, x, y, 2)?.codigo, 'DC-08')
  assert.equal(cidadeNoTrecho(c.trechos, x, y, 2), null)
})

test('DC-08 sem cor (leitura velha, maré, sem cota) deixa o Canhanduba cinza com o motivo da régua', () => {
  const c = cena([rio('ribeirao-canhanduba')], undefined, undefined, [dc08(null, 'leitura velha demais para dizer a faixa')])
  assert.equal(pintados(c, 'ribeirao-canhanduba').length, 0)
  const semCor = doRio(c, 'ribeirao-canhanduba').filter((t) => t.motivoCinza === 'regua-sem-cor')
  assert.ok(semCor.length > 0)
  assert.ok(semCor.every((t) => t.animacao === 'parada' && !t.reguaCodigo))
  assert.match(semCor[0]!.motivoDetalhe ?? '', /DC-08 \(Rio do Meio\): leitura velha/)
  const t = semCor[0]!
  const achado = trechoCinzaNoPonto(c.trechos, (t.pts[0]![0] + t.pts[1]![0]) / 2, (t.pts[0]![1] + t.pts[1]![1]) / 2, 2)
  assert.equal(achado?.motivo, 'regua-sem-cor')
  assert.match(textoDoTrechoCinza('regua-sem-cor', 'ribeirao-canhanduba', achado?.detalhe), /régua DC-08.*sem cor — DC-08 \(Rio do Meio\)/)
  assert.match(textoDoTrechoCinza('fora-do-alcance', 'ribeirao-canhanduba'), /régua DC-08 representa/)
})

test('sem as réguas (reprodução), o Canhanduba fica cinza: a régua não tem faixa histórica', () => {
  const c = cena([rio('ribeirao-canhanduba')])
  assert.equal(pintados(c, 'ribeirao-canhanduba').length, 0)
  assert.ok(doRio(c, 'ribeirao-canhanduba').some((t) => t.motivoCinza === 'regua-sem-cor' && /reprodução/.test(t.motivoDetalhe ?? '')))
})

test('o painel da régua diz até onde a cor dela vale, e que o curso fica parado', () => {
  const v = vinculoDaRegua('DC-08')!
  const texto = textoDoAlcanceDaRegua(v, 'Ribeirão Canhanduba')
  assert.match(texto, /Ribeirão Canhanduba, da régua até o fim do traçado/)
  assert.match(texto, /6,3 km/)
  assert.match(texto, /Rio Conceição, que o continua até a confluência com o Itajaí-Mirim \(0,7 km\)/)
  assert.match(texto, /fica parado/)
})

/*
 * Rio Conceição (decisão do Jefferson de 09/10/2026, que revê a de 08/10): os 665 m que o OSM chama de Rio
 * Conceição levam o Canhanduba até o Itajaí-Mirim. Pintam pela DC-08, parados, como o Canhanduba.
 */
test('o Rio Conceição continua o Canhanduba: começa no último vértice dele e acaba num vértice do Mirim', () => {
  const v = vinculoDeReguaDoTracado('rio-conceicao')!
  assert.equal(v.regua, 'DC-08')
  assert.equal(v.continuacaoDe, 'ribeirao-canhanduba')
  // Emenda sem vão: o primeiro vértice do Conceição é um vértice do traçado do Canhanduba, a < 1 m do fim declarado.
  const conceicao = tracado('rio-conceicao')
  assert.deepEqual(conceicao[0]![0], v.inicio)
  assert.ok(tracado('ribeirao-canhanduba').flat().some((p) => p[0] === v.inicio[0] && p[1] === v.inicio[1]),
    'o início do Conceição não é vértice do Canhanduba')
  const canhanduba = vinculoDeReguaDoTracado('ribeirao-canhanduba')!
  assert.ok(Math.hypot(canhanduba.fim[0] - v.inicio[0], canhanduba.fim[1] - v.inicio[1]) < 1e-5)
  const vertices = tracado('itajai-mirim').flat()
  assert.ok(vertices.some((p) => p[0] === v.fim[0] && p[1] === v.fim[1]), 'o fim não é vértice do Mirim')
  assert.equal(vinculoDaRegua('DC-08')?.tracado, 'ribeirao-canhanduba', 'o painel parte do vínculo principal')
})

test('o Rio Conceição pinta pela DC-08, parado, e fica cinza quando a régua está sem cor', () => {
  const r = rio('rio-conceicao')
  assert.equal(r.semVinculo, undefined)
  assert.deepEqual(r.reguaVinculada, { codigo: 'DC-08', cidade: 'itajai' })
  const c = cena([rio('ribeirao-canhanduba'), r], undefined, undefined, [dc08('atencao')])
  const cor = pintados(c, 'rio-conceicao')
  assert.ok(cor.length > 0, 'o Rio Conceição continuou cinza com a DC-08 em atenção')
  for (const t of cor) {
    assert.equal(t.faixa, 'atencao')
    assert.equal(t.reguaCodigo, 'DC-08')
    assert.equal(t.cidadeId, null)
    assert.equal(t.animacao, 'parada')
  }
  assert.equal(doRio(c, 'rio-conceicao').filter((t) => t.motivoCinza === 'fora-do-alcance').length, 0,
    'o vínculo vai do primeiro ao último vértice: nada do Conceição fica fora')
  const sem = cena([r], undefined, undefined, [dc08(null, 'leitura velha demais para dizer a faixa')])
  assert.equal(pintados(sem, 'rio-conceicao').length, 0)
  assert.ok(doRio(sem, 'rio-conceicao').every((t) => t.motivoCinza === 'regua-sem-cor'))
  assert.equal(pintados(cena([r]), 'rio-conceicao').length, 0, 'na reprodução fica cinza')
})
