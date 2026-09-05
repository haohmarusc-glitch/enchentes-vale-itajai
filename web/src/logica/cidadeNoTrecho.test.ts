/**
 * O toque no TRECHO DE RIO devolve a cidade que pintou aquele trecho.
 *
 * Antes disto o mapa só respondia ao PINO, que é pequeno. Quem está numa cheia
 * encosta no rio, perto de onde mora — e a tela não fazia nada, parecendo
 * travada. O risco do conserto é responder a cidade ERRADA: devolver a mais
 * próxima em linha reta daria um nome que não bate com a cor que a pessoa está
 * vendo. Por isso a resposta é a âncora que PINTOU, e por isso o trecho passou
 * a ser cortado por (faixa, âncora).
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  RAIO_TRECHO_PX,
  cidadeNoTrecho,
  construirCena,
  distanciaAoSegmento,
  type Trecho,
} from './mapaMotor'

function trecho(pts: [number, number][], cidadeId: string | null): Trecho {
  return { pts, faixa: 'normal', cum: [], total: 0, progMid: 0.5, cidadeId, rioId: 'itajai-acu' }
}

const reta = trecho([[0, 0], [100, 0]], 'gaspar')

test('o toque no MEIO de um trecho reto e longo pega — não só nos vértices', () => {
  // Ao vértice o meio ficaria a 50 px e nada seria selecionado.
  assert.equal(cidadeNoTrecho([reta], 50, 3)?.cidadeId, 'gaspar')
})

test('fora do raio não pega — o dedo longe do rio não escolhe cidade nenhuma', () => {
  assert.equal(cidadeNoTrecho([reta], 50, RAIO_TRECHO_PX + 1), null)
  assert.equal(cidadeNoTrecho([reta], 50, RAIO_TRECHO_PX - 1)?.cidadeId, 'gaspar')
})

test('devolve a cidade do trecho TOCADO, não a mais próxima em linha reta', () => {
  // Blumenau pinta o pedaço de cima; Gaspar, o de baixo. O toque cai no de
  // Gaspar, mas a linha de Blumenau passa perto por outro caminho.
  const doGaspar = trecho([[0, 100], [100, 100]], 'gaspar')
  const deBlumenau = trecho([[0, 0], [100, 0], [100, 90]], 'blumenau')
  assert.equal(cidadeNoTrecho([deBlumenau, doGaspar], 50, 102)?.cidadeId, 'gaspar')
})

test('trecho cinza (sem cidade) não devolve chute', () => {
  // `sem-dado` é "não se sabe de quem é". Atribuir a leitura de alguém a um
  // trecho que ninguém mediu é o erro que este projeto existe para não cometer.
  assert.equal(cidadeNoTrecho([trecho([[0, 0], [100, 0]], null)], 50, 1), null)
})

test('entre dois trechos, ganha o mais PERTO do dedo', () => {
  const a = trecho([[0, 0], [100, 0]], 'blumenau')
  const b = trecho([[0, 20], [100, 20]], 'gaspar')
  assert.equal(cidadeNoTrecho([a, b], 50, 4)?.cidadeId, 'blumenau')
  assert.equal(cidadeNoTrecho([a, b], 50, 16)?.cidadeId, 'gaspar')
})

test('leva junto o rio do trecho — a cidade da foz está em dois', () => {
  assert.equal(cidadeNoTrecho([reta], 50, 0)?.rioId, 'itajai-acu')
})

test('segmento degenerado (dois pontos iguais) não vira NaN', () => {
  assert.equal(distanciaAoSegmento(3, 4, [0, 0], [0, 0]), 5)
  assert.equal(cidadeNoTrecho([trecho([[0, 0], [0, 0]], 'x')], 0, 1)?.cidadeId, 'x')
})

test('a projeção é no segmento, não na reta infinita', () => {
  // Um ponto além da ponta mede até a PONTA, não até a reta prolongada.
  assert.equal(distanciaAoSegmento(110, 0, [0, 0], [100, 0]), 10)
})

/*
 * ------------------------------------------------------------------
 * O CORTE POR ÂNCORA, na cena de verdade.
 *
 * Os testes acima montam `Trecho` à mão, então não alcançam a regra que os
 * PRODUZ. Uma sabotagem provou a folga: voltar a cortar só por faixa não
 * quebrava nada, e nesse estado duas cidades vizinhas na mesma faixa viram UM
 * trecho — a metade de baixo devolvendo o nome da cidade de cima.
 * ------------------------------------------------------------------
 */
const g = globalThis as unknown as { getComputedStyle?: unknown }
g.getComputedStyle = () => ({ getPropertyValue: () => '' })
const el = {} as Element
const SEM_TEMPO_REAL = { leituras: [], chuva: [], coletadoEm: null } as never

/**
 * TRÊS cidades no mesmo rio, SEM leitura — logo, todas na MESMA faixa.
 *
 * A REGRA DE PINTURA, medida aqui e ANTERIOR a este trabalho: `trechoDoPonto`
 * devolve índice de SEGMENTO da espinha, e o segmento i vai da âncora i à i+1.
 * Então o trecho entre duas cidades é pintado pela de MONTANTE, e a última
 * cidade do rio não pinta trecho nenhum — quem colore a foz é a penúltima.
 *
 * O toque SEGUE essa regra de propósito: quem encosta num trecho laranja quer
 * saber de quem é aquele laranja. Devolver a cidade mais próxima em linha reta
 * daria um nome cuja faixa contradiz a cor debaixo do dedo. Perto do pino, o
 * teste do pino (26 px) roda ANTES e devolve a cidade dali.
 */
/** Duas cidades no mesmo rio, SEM leitura — logo, ambas na MESMA faixa. */
function cenaDeTresCidades() {
  const linha: [number, number][] = [
    [-49.0, -27.0],
    [-48.9, -27.0],
    [-48.8, -27.0],
    [-48.7, -27.0],
    [-48.6, -27.0],
  ]
  const cidade = (id: string, lon: number) =>
    ({
      id,
      nome: id,
      ordem: 1,
      codigo_ana: null,
      verificado: true,
      cotas_m: {},
      fontes_tempo_real: [],
      coordenadas: [-27.0, lon],
    }) as never
  return construirCena(
    el,
    [
      {
        rioId: 'itajai-acu',
        coords: [linha],
        cidades: [cidade('alta', -48.98), cidade('meio', -48.8), cidade('baixa', -48.62)],
      },
    ],
    SEM_TEMPO_REAL,
    new Date(),
    800,
    600,
    null,
  )
}

test('cidades na MESMA faixa não viram um trecho só — o corte é por âncora', () => {
  // O caso difícil: cor igual em todo o rio. Cortando só por faixa, sairia UM
  // trecho e o rio inteiro devolveria o nome da primeira cidade.
  const cena = cenaDeTresCidades()
  const faixas = new Set(cena.trechos.map((t) => t.faixa))
  assert.equal(faixas.size, 1, 'todas na mesma faixa — é esse o caso difícil')
  const donos = new Set(cena.trechos.map((t) => t.cidadeId))
  assert.ok(donos.size > 1, `o rio inteiro ficou com um dono só: ${[...donos]}`)
  assert.deepEqual([...donos].sort(), ['alta', 'meio'], 'a de jusante não pinta — regra de pintura')
})

test('o trecho de baixo devolve a cidade do MEIO, não a do alto', () => {
  // É o que a sabotagem "corte só por faixa" quebraria: lá, o trecho de baixo
  // herdaria o nome da cidade mais a montante.
  const cena = cenaDeTresCidades()
  const doMeio = cena.trechos.filter((t) => t.cidadeId === 'meio')
  assert.ok(doMeio.length > 0, 'a cidade do meio pinta algum trecho')
  // O MEIO do trecho, não a ponta: a ponta é o vértice compartilhado com o
  // trecho vizinho, e ali os dois estão a distância zero.
  const t = doMeio[0]!
  const a = t.pts[0]!
  const b = t.pts[t.pts.length - 1]!
  assert.equal(
    cidadeNoTrecho(cena.trechos, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2)?.cidadeId,
    'meio',
  )
})
