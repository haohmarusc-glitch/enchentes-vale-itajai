import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import {
  KM_SEM_ROTULO_DE_REGUA,
  KM_TODAS_AS_REGUAS,
  detalheDasReguas,
  reguasComRotulo,
  type ReguaParaRotular,
} from './rotulosDasReguas'

/** Itajaí como ela é: nove de maré (sem faixa) e duas que podem virar aviso. */
const ITAJAI: ReguaParaRotular[] = [
  { codigo: 'DC-11', faixa: 'atencao' },
  { codigo: 'DC-10', faixa: 'normal' },
  ...Array.from({ length: 9 }, (_, i) => ({ codigo: `DC-0${i + 1}`, faixa: null })),
]

test('de longe, nenhum rótulo de régua — o pino da cidade é quem fala', () => {
  assert.equal(detalheDasReguas(158), 'nenhuma') // a bacia inteira
  assert.equal(reguasComRotulo(ITAJAI, 158).size, 0)
})

test('na tela de uma cidade, só as réguas que podem virar aviso', () => {
  const mostradas = reguasComRotulo(ITAJAI, 25)
  assert.deepEqual([...mostradas].sort(), ['DC-10', 'DC-11'])
  assert.equal(mostradas.size, 2, 'as nove de maré não gritam o número de longe')
})

test('de perto, todas — porque aí cabem', () => {
  assert.equal(reguasComRotulo(ITAJAI, 4).size, 11)
})

test('a régua SELECIONADA mantém o rótulo em qualquer zoom', () => {
  for (const km of [4, 25, 158]) {
    assert.ok(reguasComRotulo(ITAJAI, km, 'DC-03').has('DC-03'), `perdeu em ${km} km`)
  }
  // Mesmo uma que nem está na lista do quadro (saiu da tela e voltou).
  assert.ok(reguasComRotulo([], 158, 'DC-07').has('DC-07'))
})

test('as fronteiras são inclusivas onde deviam ser', () => {
  assert.equal(detalheDasReguas(KM_TODAS_AS_REGUAS), 'todas')
  assert.equal(detalheDasReguas(KM_TODAS_AS_REGUAS + 0.1), 'so-as-que-avisam')
  assert.equal(detalheDasReguas(KM_SEM_ROTULO_DE_REGUA), 'so-as-que-avisam')
  assert.equal(detalheDasReguas(KM_SEM_ROTULO_DE_REGUA + 0.1), 'nenhuma')
})

test('medida inválida NÃO esconde dado — cai no comportamento de antes', () => {
  for (const ruim of [Number.NaN, 0, -5, Number.POSITIVE_INFINITY]) {
    assert.equal(detalheDasReguas(ruim), 'todas', String(ruim))
  }
})

test('a tela de cidade cai na faixa do meio, não na de "nenhuma"', () => {
  /**
   * O piso do enquadramento por cidade é 24 km, e Itajaí abre mais que isso
   * porque as onze réguas se espalham por 20,8 x 17,6 km. Se o teto de 45 km
   * ficasse abaixo disso, abrir a cidade da foz esconderia TODAS as réguas
   * dela — o contrário do que a tela existe para fazer.
   */
  for (const km of [24, 30, 42]) {
    assert.equal(detalheDasReguas(km), 'so-as-que-avisam', `${km} km`)
  }
})

test('o número de réguas de maré em Itajaí é o que o cadastro diz', () => {
  const d = JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf-8'))
  const daFoz = (d.estacoes_tempo_real as { cidade: string; lat?: number; alerta_automatico?: boolean }[])
    .filter((e) => e.cidade === 'itajai' && typeof e.lat === 'number')
  assert.equal(daFoz.length, 11)
  assert.equal(daFoz.filter((e) => e.alerta_automatico === false).length, 9,
    'se o cadastro mudar, a conta de quantas falam no zoom médio muda junto')
})
