/**
 * Só o EIXO do rio pinta o traçado. Afluente lateral não.
 *
 * O defeito, achado em 04/09/2026 medindo: `cidadesDoRio('itajai-acu')` devolve
 * as 14 cidades do cadastro, e o mapa transformava TODAS em âncora, encaixando
 * cada uma no ponto mais próximo do traçado. Seis não estão no tronco, e três
 * estão em OUTROS RIOS — Timbó no Benedito (8,2 km do Açu), Rio dos Cedros
 * (16,6 km), Ituporanga na cabeceira Sul (28,0 km). Encaixadas à força, elas
 * pintavam trechos do rio principal com a faixa da régua DELAS.
 *
 * A direção perigosa é a calma: Timbó verde enquanto o Açu sobe deixaria um
 * trecho VERDE num rio subindo.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { construirCena } from './mapaMotor'
import { kmEntre } from './mapaCanvas'
import type { Cidade } from '../dados/tipos'

const g = globalThis as unknown as { getComputedStyle?: unknown }
g.getComputedStyle = () => ({ getPropertyValue: () => '' })
const el = {} as Element
/**
 * Tempo real com uma leitura ACIMA da cota, para a cidade sair colorida.
 *
 * Sem isto os testes não testavam nada: uma cidade sem leitura já sai
 * `sem-dado`, então o guarda podia ser removido que tudo continuava passando.
 * A falsificação flagrou — é para isso que ela existe.
 */
function comLeitura(cidadeId: string, rioId: string, nivel: number) {
  return {
    situacao: 'ok',
    chuva: [],
    chuvaOk: true,
    coletadoEm: new Date(),
    fonte: null,
    leituras: [{
      estacao: cidadeId,
      rio: rioId,
      cidade: cidadeId,
      nivel_m: nivel,
      medidoEm: new Date(),
      resgateDe: null,
    }],
  } as never
}

const estacoes = JSON.parse(
  readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'),
) as {
  rios: Record<
    string,
    {
      cidades: { id: string; coordenadas?: [number, number] }[]
      _topologia?: {
        tronco_sequencia?: string[]
        cabeceiras_paralelas?: string[]
        afluentes_laterais?: { id: string; rio: string }[]
      }
    }
  >
}

function cidade(id: string, lat: number, lon: number): Cidade {
  return {
    id,
    nome: id,
    ordem: null,
    codigo_ana: null,
    verificado: true,
    cotas_m: { atencao: 1 },
    fontes_tempo_real: [],
    coordenadas: [lat, lon],
  } as Cidade
}

/**
 * Um "rio" reto de oeste para leste, com vértices DENSOS.
 *
 * A densidade não é detalhe do fixture: `maisProximoNoRio` encaixa a cidade no
 * VÉRTICE mais próximo, não no ponto mais próximo da linha. No traçado real do
 * Açu são 4.756 pontos em ~180 km — um a cada ~38 m —, então vértice e linha
 * dão praticamente o mesmo. Com três vértices espaçados de 20 km, como estava
 * na primeira versão deste arquivo, a cidade encaixava a 5,5 km de si mesma e a
 * guarda de distância a barrava por um motivo que não existe no dado real.
 */
const linha: [number, number][] = Array.from({ length: 401 }, (_, i) => [
  -49.0 + i * 0.001,
  -27.0,
])

test('cidade PERTO do rio mas fora do eixo não pinta — o caso Ibirama', () => {
  // As duas guardas pegam coisas diferentes, e esta é a que só a CLASSIFICAÇÃO
  // pega: Ibirama fica a 2,62 km do traçado do Açu — dentro do limite
  // geométrico — e mesmo assim mede o Rio Hercílio, que é outro rio.
  // Duas armadilhas de fixture que a primeira versão caiu, e que ficam
  // registradas porque custam meia hora cada:
  //  - longitudes DIFERENTES: encaixando no mesmo ponto, a espinha fica com dois
  //    pontos iguais e o teste não distingue nada;
  //  - a de FORA tem de ser a de MONTANTE. `trechoDoPonto` devolve a cidade a
  //    montante do trecho (é ela quem dá a cor, como no diagrama), então a
  //    âncora mais a jusante nunca pinta — e o teste passaria à toa.
  const cidades = [cidade('outro-rio', -27.022, -48.95), cidade('tronco', -27.0, -48.65)]
  // Só a de FORA tem leitura, e acima da cota: se ela pintar, aparece cor.
  const tr = comLeitura('outro-rio', 'r', 9)

  const semEixo = construirCena(
    el, [{ rioId: 'r', coords: [linha], cidades }], tr, new Date(), 800, 600, null,
  )
  assert.ok(
    semEixo.trechos.some((t) => t.faixa !== 'sem-dado'),
    'sem eixo, a cidade de outro rio PINTA — é o defeito que isto conserta',
  )

  const comEixo = construirCena(
    el, [{ rioId: 'r', coords: [linha], cidades, eixo: ['tronco'] }],
    tr, new Date(), 800, 600, null,
  )
  for (const t of comEixo.trechos) {
    assert.equal(t.faixa, 'sem-dado',
      'cidade fora do eixo não pode colorir este rio: ela mede outro')
  }
  // E continua aparecendo: esconder o nível dela seria perder dado.
  assert.equal(comEixo.pinos.length, 2, 'a cidade fora do eixo tem de continuar no mapa')
})

test('âncora longe demais do traçado não pinta, mesmo estando no eixo', () => {
  // Ituporanga é uma cabeceira (logo, no eixo) cujo rio NÃO foi desenhado.
  const cena = construirCena(
    el,
    [{
      rioId: 'r', coords: [linha],
      cidades: [cidade('longe', -27.5, -48.8)], // ~55 km do traçado
      eixo: ['longe'],
    }],
    comLeitura('longe', 'r', 9), new Date(), 800, 600, null,
  )
  assert.ok(cena.trechos.length > 0)
  for (const t of cena.trechos) {
    assert.equal(t.faixa, 'sem-dado',
      'régua a dezenas de km não pode colorir este rio: ela mede outro')
  }
})

test('a cidade DO eixo, em cima do rio, pinta normalmente', () => {
  // Contraprova: sem ela, os dois testes acima passariam com o mapa todo cinza.
  const cena = construirCena(
    el,
    [{
      rioId: 'r', coords: [linha],
      cidades: [cidade('tronco', -27.0, -48.8)],
      eixo: ['tronco'],
    }],
    comLeitura('tronco', 'r', 9), new Date(), 800, 600, null,
  )
  assert.ok(
    cena.trechos.some((t) => t.faixa !== 'sem-dado'),
    'quem está no eixo e em cima do rio TEM de pintar',
  )
})

test('o eixo do Açu no cadastro exclui os afluentes laterais', () => {
  const t = estacoes.rios['itajai-acu']!._topologia!
  const eixo = new Set([...(t.tronco_sequencia ?? []), ...(t.cabeceiras_paralelas ?? [])])
  for (const a of t.afluentes_laterais ?? []) {
    assert.ok(!eixo.has(a.id),
      `${a.id} está em ${a.rio} e não pode pintar o Açu`)
  }
  assert.ok(eixo.has('blumenau') && eixo.has('taio'))
})

test('as cidades do Açu FORA do eixo estão mesmo longe do traçado — a medida que motivou isto', () => {
  const t = estacoes.rios['itajai-acu']!._topologia!
  const eixo = new Set([...(t.tronco_sequencia ?? []), ...(t.cabeceiras_paralelas ?? [])])
  const fora = estacoes.rios['itajai-acu']!.cidades.filter(
    (c) => !eixo.has(c.id) && c.coordenadas,
  )
  assert.ok(fora.length >= 3, 'se ninguém mais está fora do eixo, esta trava virou letra morta')
})

test('Blumenau fica a ~3 km do talvegue e MESMO ASSIM pinta', () => {
  // A coordenada publicada é a da ESTAÇÃO, não do rio. É por isso que a guarda
  // geométrica é de 5 km e não de 1: apertá-la calaria a cidade com 97
  // registros históricos desde 1852.
  const acu = estacoes.rios['itajai-acu']!
  const b = acu.cidades.find((c) => c.id === 'blumenau')!
  const linhas = JSON.parse(
    readFileSync(new URL('../../../data/rios/itajai-acu.geojson', import.meta.url), 'utf8'),
  ).geometry.coordinates as [number, number][][]
  const p: [number, number] = [b.coordenadas![1], b.coordenadas![0]]
  const d = Math.min(...linhas.flat().map((q) => kmEntre(p, q as [number, number])))
  assert.ok(d > 1, `Blumenau está a ${d.toFixed(2)} km — se encostou no rio, revise o limite`)
  assert.ok(d < 5, `Blumenau está a ${d.toFixed(2)} km e deixaria de pintar`)
})
