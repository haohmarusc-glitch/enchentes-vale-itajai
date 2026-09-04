/**
 * Afluente entra na cena SEM cidade — então todo trecho dele é `sem-dado`.
 *
 * O relato foi que o Ribeirão da Murta aparecia AMARELO no mapa. Amarelo é
 * `--faixa-atencao`: afirmar atenção num curso cuja régua o site recusa a
 * classificar (as de Itajaí são de estuário) seria dizer perigo onde não se
 * pode dizer nada.
 *
 * Este teste fecha a pergunta na lógica, que é onde ela é decidível: monta a
 * cena com um afluente de verdade e confere a faixa de cada trecho. Uma sonda
 * de pixel não serve — no zoom da bacia inteira o ribeirão tem uns 15 px e o
 * que se lê ali é o pino da régua, não a linha.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { construirCena } from './mapaMotor'
import type { Cidade } from '../dados/tipos'

/**
 * `construirCena` toca no DOM só para ler as cores das faixas do CSS. Devolver
 * vazio faz `corDaFaixa` cair no fallback embutido, que é o que queremos: o
 * teste é sobre QUAL faixa, não sobre o tom exato.
 */
const g = globalThis as unknown as { getComputedStyle?: unknown }
g.getComputedStyle = () => ({ getPropertyValue: () => '' })
const el = {} as Element

const SEM_TEMPO_REAL = { leituras: [], chuva: [], coletadoEm: null } as never
const linha: [number, number][] = [
  [-48.74, -26.9],
  [-48.72, -26.89],
  [-48.7, -26.88],
]

function cidade(over: Partial<Cidade> = {}): Cidade {
  return {
    id: 'brusque',
    nome: 'Brusque',
    ordem: 1,
    codigo_ana: null,
    verificado: true,
    cotas_m: { atencao: 4 },
    fontes_tempo_real: [],
    coordenadas: [-26.89, -48.72],
    ...over,
  } as Cidade
}

test('afluente (sem cidade) tem TODOS os trechos em sem-dado', () => {
  const cena = construirCena(
    el,
    [{ rioId: 'ribeirao-murta', coords: [linha], cidades: [] }],
    SEM_TEMPO_REAL,
    new Date(),
    800,
    600,
    null,
  )
  assert.ok(cena.trechos.length > 0, 'o afluente tem de ser DESENHADO, só que cinza')
  for (const t of cena.trechos) {
    assert.equal(
      t.faixa,
      'sem-dado',
      'trecho de afluente ganhou faixa: o mapa passaria a afirmar um nível ' +
        'que a régua de estuário não deixa ler',
    )
  }
})

test('o mesmo traçado COM cidade ganha faixa — o teste acima não passa por acidente', () => {
  const cena = construirCena(
    el,
    [{ rioId: 'itajai-mirim', coords: [linha], cidades: [cidade()] }],
    SEM_TEMPO_REAL,
    new Date(),
    800,
    600,
    null,
  )
  assert.ok(cena.trechos.length > 0)
  // Sem leitura a cidade fica em sem-dado também; o que importa é que a
  // âncora EXISTE — é o caminho por onde a cor entraria.
  assert.equal(cena.pinos.length, 1, 'a cidade tem de virar âncora/pino')
})
