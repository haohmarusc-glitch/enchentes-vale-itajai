/**
 * As quatro travas das cotas de rua no mapa. Cada uma existe porque quebrá-la
 * manda alguém para o lado errado numa cheia.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import {
  COR_COTA_RUA,
  KM_PARA_MOSTRAR,
  cidadePodeMostrarRuas,
  contarRuas,
  pontosDeRua,
  zoomPermiteRuas,
} from './cotasNoMapa'
import type { CotaRua } from '../dados/tipos'

const GASPAR = { id: 'gaspar', cotas_verificado: true }
const BRUSQUE = { id: 'brusque', cotas_verificado: false }

function cota(over: Partial<CotaRua> & { lat?: number; lon?: number }): CotaRua {
  return {
    cidade: 'gaspar',
    rio: 'itajai-acu',
    rua: 'Rua X',
    bairro: null,
    ponto: null,
    cota_m: 8,
    fonte: 'f',
    data_fonte: '2020',
    confianca: 'alta',
    ...over,
  } as CotaRua
}

test('trava 1 — cidade sem par provado APARECE, mas sem estado', () => {
  // Brusque tem 348 ruas com coordenada e as cotas dela são da Ponte Estaiada;
  // as duas estações ao vivo têm regua: null. Então o mapa mostra a cota de
  // cada rua e NÃO diz se alagou. Esconder não protegeria: a pessoa faria a
  // conta de cabeça com o número do pino ao lado.
  const cotas = [cota({ cidade: 'brusque', cota_m: 8.2, lat: -27.1, lon: -48.9 })]
  const p = pontosDeRua(cotas, BRUSQUE, 9)
  assert.equal(p.length, 1)
  assert.equal(p[0]?.cotaM, 8.2, 'a cota da rua é informação boa e continua visível')
  assert.equal(p[0]?.atingida, null, 'mesmo com nível 9 > cota 8,2, NÃO se afirma')
  assert.equal(p[0]?.motivo, 'regua-nao-provada')
  assert.equal(cidadePodeMostrarRuas(BRUSQUE), false)
})

test('os dois motivos de "sem estado" não se confundem', () => {
  // Régua não provada e leitura ausente são coisas diferentes, e a tela diz
  // qual é: uma se resolve com ofício, a outra com a próxima coleta.
  const gaspar = [cota({ lat: -26.9, lon: -49.0 })]
  assert.equal(pontosDeRua(gaspar, GASPAR, null)[0]?.motivo, 'sem-leitura')
  const brusque = [cota({ cidade: 'brusque', lat: -27.1, lon: -48.9 })]
  assert.equal(pontosDeRua(brusque, BRUSQUE, null)[0]?.motivo, 'regua-nao-provada')
  assert.equal(pontosDeRua(gaspar, GASPAR, 9)[0]?.motivo, null)
})

test('trava 1 — `cotas_verificado` ausente NÃO é permissão', () => {
  // null é "ninguém conferiu ainda", não "pode".
  assert.equal(cidadePodeMostrarRuas({ id: 'blumenau', cotas_verificado: null }), false)
  assert.equal(cidadePodeMostrarRuas({ id: 'x' }), false)
  assert.equal(cidadePodeMostrarRuas(null), false)
  assert.equal(cidadePodeMostrarRuas(GASPAR), true)
})

test('trava 2 — de longe não desenha: nuvem de pontos lê-se como MANCHA', () => {
  assert.equal(zoomPermiteRuas(158), false, 'bacia inteira')
  assert.equal(zoomPermiteRuas(24), false, 'a vista de cidade ainda é larga demais')
  assert.equal(zoomPermiteRuas(KM_PARA_MOSTRAR), true)
  assert.equal(zoomPermiteRuas(2), true)
  for (const n of [0, -1, Number.NaN, Number.POSITIVE_INFINITY]) {
    assert.equal(zoomPermiteRuas(n), false, String(n))
  }
})

test('trava 3 — sem leitura o estado é null, e null não é "não alagou"', () => {
  const cotas = [cota({ lat: -26.9, lon: -49.0 })]
  for (const n of [null, undefined, Number.NaN]) {
    const p = pontosDeRua(cotas, GASPAR, n as number | null)
    assert.equal(p.length, 1)
    assert.equal(p[0]?.atingida, null, String(n))
    assert.equal(p[0]?.motivo, 'sem-leitura', String(n))
  }
})

test('o estado é a comparação com a cota, e a igualdade conta como atingida', () => {
  const cotas = [
    cota({ rua: 'Baixa', cota_m: 6.2, lat: -26.9, lon: -49.0 }),
    cota({ rua: 'Igual', cota_m: 7.0, lat: -26.9, lon: -49.0 }),
    cota({ rua: 'Alta', cota_m: 9.9, lat: -26.9, lon: -49.0 }),
  ]
  const p = pontosDeRua(cotas, GASPAR, 7.0)
  assert.deepEqual(
    p.map((x) => [x.rua, x.atingida]),
    [['Baixa', true], ['Igual', true], ['Alta', false]],
  )
  assert.deepEqual(contarRuas(p), { atingidas: 2, aguardando: 1, semLeitura: 0 })
})

test('rua sem coordenada, ou sem cota, fica de fora — não vira ponto no (0,0)', () => {
  const cotas = [
    cota({ rua: 'Sem coord' }),
    cota({ rua: 'Só lat', lat: -26.9 }),
    cota({ rua: 'Sem cota', cota_m: null as never, lat: -26.9, lon: -49.0 }),
    cota({ rua: 'Boa', lat: -26.9, lon: -49.0 }),
  ]
  assert.deepEqual(pontosDeRua(cotas, GASPAR, 8).map((p) => p.rua), ['Boa'])
})

test('trava 4 — a cor das ruas não é de faixa nem a do nível bruto', () => {
  // Rua alagada não é faixa de rio; dizer uma pela outra na mesma cor seria
  // trocar as duas leituras. O ESTADO é o preenchimento, não o tom.
  const proibidas = ['#2e7d32', '#a3c93a', '#e6a700', '#e2661a', '#c62828', '#c9a6f0']
  assert.ok(!proibidas.includes(COR_COTA_RUA.toLowerCase()))
})

test('o nome carrega o PONTO quando ele existe — a rua é o par (nome, ponto)', () => {
  // A São Rafael alaga a 7,40 no final e a 7,75 no nº 169: sem o ponto, os dois
  // pontos do mapa teriam o mesmo nome e cotas diferentes.
  const p = pontosDeRua(
    [cota({ rua: 'Rua São Rafael', ponto: 'final da rua', lat: -26.9, lon: -49.0 })],
    GASPAR,
    8,
  )
  assert.equal(p[0]?.rua, 'Rua São Rafael (final da rua)')
})

test('no cadastro de verdade: Gaspar entra com 1.613 pontos, Brusque com zero', () => {
  const arq = JSON.parse(
    readFileSync(new URL('../../../data/cotas-ruas.json', import.meta.url), 'utf8'),
  ) as { cotas: CotaRua[] }
  assert.equal(pontosDeRua(arq.cotas, GASPAR, 5).length, 1613)
  const brusque = pontosDeRua(arq.cotas, BRUSQUE, 5)
  assert.equal(brusque.length, 348, 'Brusque aparece')
  assert.ok(
    brusque.every((p) => p.atingida === null && p.motivo === 'regua-nao-provada'),
    'e nenhuma das 348 afirma estado enquanto a régua não for provada',
  )
})
