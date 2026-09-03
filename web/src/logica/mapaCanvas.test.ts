import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  acumuladoEspinha,
  enquadrar,
  limitesDe,
  maisProximoNoRio,
  posicoesCorrenteza,
  progressoNaEspinha,
  projetar,
  trechoDoPonto,
  VEL_FAIXA,
  type LonLat,
} from './mapaCanvas'

test('projeção enquadra os cantos dentro da área, norte para cima', () => {
  const lim = { minLon: -49, maxLon: -48, minLat: -27, maxLat: -26 }
  const e = enquadrar(lim, 200, 200, 10)
  const [xSO, ySO] = projetar(e, [-49, -27]) // sudoeste
  const [xNE, yNE] = projetar(e, [-48, -26]) // nordeste
  // Dentro da área com margem.
  assert.ok(xSO >= 10 - 0.01 && xNE <= 200 - 10 + 0.01)
  // Oeste à esquerda do leste; norte ACIMA do sul (y menor).
  assert.ok(xSO < xNE)
  assert.ok(yNE < ySO)
})

test('limitesDe cobre todos os pontos', () => {
  const l = limitesDe([
    [-49, -27],
    [-48.5, -26.5],
    [-48.8, -26.9],
  ])
  assert.deepEqual(l, { minLon: -49, maxLon: -48.5, minLat: -27, maxLat: -26.5 })
  assert.equal(limitesDe([]), null)
})

test('progresso na espinha cresce montante→jusante e orienta o sentido do rio', () => {
  // Espinha reta de oeste (montante) para leste (jusante).
  const espinha: LonLat[] = [
    [-49.4, -27],
    [-49.0, -27],
    [-48.6, -27],
  ]
  const cum = acumuladoEspinha(espinha)
  const montante = progressoNaEspinha(espinha, cum, [-49.35, -27])
  const jusante = progressoNaEspinha(espinha, cum, [-48.65, -27])
  assert.ok(jusante > montante, 'jusante tem progresso maior')
  // Um way desenhado ao contrário (jusante→montante) é detectável: progresso do
  // primeiro ponto MAIOR que o do último ⇒ o render inverte para a correnteza descer.
  const wayInvertido: LonLat[] = [
    [-48.7, -27],
    [-49.3, -27],
  ]
  const pa = progressoNaEspinha(espinha, cum, wayInvertido[0]!)
  const pb = progressoNaEspinha(espinha, cum, wayInvertido[1]!)
  assert.ok(pb < pa, 'primeiro ponto está a jusante do último ⇒ inverter')
})

test('trechoDoPonto atribui o ponto à cidade a montante do trecho', () => {
  const espinha: LonLat[] = [
    [-49.4, -27], // cidade 0
    [-49.0, -27], // cidade 1
    [-48.6, -27], // cidade 2
  ]
  // Perto do meio do primeiro trecho ⇒ índice 0 (cidade a montante).
  assert.equal(trechoDoPonto(espinha, [-49.2, -27]), 0)
  // Perto do meio do segundo trecho ⇒ índice 1.
  assert.equal(trechoDoPonto(espinha, [-48.8, -27]), 1)
})

test('maisProximoNoRio encaixa a cidade no ponto mais próximo do traçado', () => {
  const rio: LonLat[][] = [
    [
      [-49, -27],
      [-48.9, -27],
      [-48.8, -27],
    ],
  ]
  assert.deepEqual(maisProximoNoRio(rio, [-48.91, -27.02]), [-48.9, -27])
  assert.equal(maisProximoNoRio([], [-48, -27]), null)
})

test('cinza (sem-dado) não corre — honestidade virada em animação', () => {
  // A regra que o render depende: água desconhecida fica parada.
  assert.equal(VEL_FAIXA['sem-dado'], 0)
  // E gravidade maior corre mais rápido (a animação significa o nível).
  assert.ok(VEL_FAIXA.normal < VEL_FAIXA.atencao)
  assert.ok(VEL_FAIXA.atencao < VEL_FAIXA.alerta)
  assert.ok(VEL_FAIXA.alerta < VEL_FAIXA.inundacao)
})

test('as setas da correnteza ANDAM com o tempo e param no cinza', () => {
  const total = 200
  const espaco = 26
  const velPx = 24
  const t0 = posicoesCorrenteza(total, VEL_FAIXA.alerta, 0, espaco, velPx)
  const t1 = posicoesCorrenteza(total, VEL_FAIXA.alerta, 0.2, espaco, velPx)
  assert.ok(t0.length > 0, 'faixa com corrente tem setas')
  // Alguma seta avançou: o conjunto de posições mudou de um quadro para o outro.
  assert.notDeepEqual(t0, t1)
  // A primeira seta deslizou para jusante (posição maior), sem passar do espaço.
  assert.ok(t1[0]! > t0[0]! && t1[0]! - t0[0]! < espaco)
  // Cinza (velocidade 0): nenhuma seta, em qualquer tamanho.
  assert.deepEqual(posicoesCorrenteza(total, VEL_FAIXA['sem-dado'], 5, espaco, velPx), [])
  // Trecho curtíssimo (< 6 px): não comporta seta.
  assert.deepEqual(posicoesCorrenteza(4, VEL_FAIXA.inundacao, 5, espaco, velPx), [])
  // Trecho colorido menor que o espaçamento AINDA recebe uma seta (senão o rio
  // ficava parado, pois os trechos do OSM são curtos) — e ela anda com o tempo.
  const curtoA = posicoesCorrenteza(15, VEL_FAIXA.alerta, 0, espaco, velPx)
  const curtoB = posicoesCorrenteza(15, VEL_FAIXA.alerta, 0.3, espaco, velPx)
  assert.equal(curtoA.length, 1)
  assert.notDeepEqual(curtoA, curtoB)
})
