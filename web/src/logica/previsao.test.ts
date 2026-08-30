import assert from 'node:assert/strict'
import { test } from 'node:test'
import type { Evento } from '../dados/tipos'
import { MIN_PARES, agruparEmEventos, ajustar, parear, prever } from './previsao'

function ev(cidade: string, data: string, pico_m: number): Evento {
  return { rio: 'itajai-acu', cidade, data, pico_m, confianca: 'alta', fonte: 'teste' }
}

/** Série sintética: jusante = 0,5 + 0,8 × montante, com ruído mínimo. */
function serie(n: number, ruido = 0): Evento[] {
  const out: Evento[] = []
  for (let i = 0; i < n; i++) {
    const mes = String(i + 1).padStart(2, '0')
    const x = 5 + i
    out.push(ev('cima', `2000-${mes}-01`, x))
    out.push(ev('baixo', `2000-${mes}-01`, 0.5 + 0.8 * x + (i % 2 ? ruido : -ruido)))
  }
  return out
}

test('parear só junta registros do mesmo evento', () => {
  const pares = parear(serie(6), 'cima', 'baixo')
  assert.equal(pares.length, 6)
  assert.equal(pares[0]!.x, 5)
})

test('leituras próximas da mesma cidade viram um evento só, com o maior pico', () => {
  // O rio fica dias acima da cota e a Defesa Civil registra mais de um valor:
  // é a mesma cheia, e o pico dela é o maior — não dois eventos.
  const eventos = [...serie(6), ev('baixo', '2000-01-02', 99)]
  const pares = parear(eventos, 'cima', 'baixo')
  assert.equal(pares.length, 6)
  assert.equal(pares[0]!.y, 99, 'o pico do evento é a maior leitura do grupo')
})

test('agruparEmEventos junta o que é a mesma cheia e separa o que não é', () => {
  const grupos = agruparEmEventos([
    ev('x', '2011-08-31', 8.5),
    ev('x', '2011-09-08', 11.6),
    ev('x', '2011-09-09', 12.8),
  ])
  assert.equal(grupos.length, 2, '31/08 está a 8 dias de 08/09 — cheia diferente')
  assert.equal(grupos[1]!.pico_m, 12.8)
  assert.equal(grupos[1]!.leituras, 2)
})

test('evento de mês inteiro que casa com duas cheias distintas é descartado', () => {
  // Rio do Sul registra "agosto de 1957" sem dia; Blumenau teve DUAS cheias
  // naquele agosto. Não dá para saber qual corresponde — o par sai.
  const eventos = [
    ev('cima', '1957-08', 10.65),
    ev('baixo', '1957-08-02', 10.6),
    ev('baixo', '1957-08-18', 13.07),
  ]
  assert.equal(parear(eventos, 'cima', 'baixo').length, 0)
})

test('menos de 5 pares nunca vira número', () => {
  const r = prever(serie(4), 'cima', 'baixo', 10)
  assert.equal(r.status, 'dados-insuficientes')
  assert.equal(MIN_PARES, 5)
})

test('sem nenhum par também é dados-insuficientes', () => {
  const r = prever(serie(6), 'cima', 'inexistente', 10)
  assert.equal(r.status, 'dados-insuficientes')
})

test('ajuste recupera a reta que gerou os dados', () => {
  const a = ajustar(parear(serie(8), 'cima', 'baixo'))
  assert.ok(a)
  assert.ok(Math.abs(a.b - 0.8) < 1e-9)
  assert.ok(Math.abs(a.a - 0.5) < 1e-9)
  assert.ok(a.r2 > 0.999)
})

test('previsão devolve intervalo que contém o centro', () => {
  const r = prever(serie(8, 0.2), 'cima', 'baixo', 9)
  assert.equal(r.status, 'ok')
  if (r.status !== 'ok') return
  assert.ok(r.minimo < r.central && r.central < r.maximo)
  assert.ok(r.maximo - r.minimo > 0.1, 'o intervalo precisa ter largura real')
  assert.equal(r.extrapolacao, false)
})

test('nível acima de tudo que já se viu é marcado como extrapolação', () => {
  const r = prever(serie(8, 0.2), 'cima', 'baixo', 40)
  assert.equal(r.status, 'ok')
  if (r.status !== 'ok') return
  assert.equal(r.extrapolacao, true)
})

test('correlação fraca não vira número na tela', () => {
  const eventos: Evento[] = []
  const ys = [3, 9, 4, 8, 3.5, 9.5, 4.2, 8.1]
  ys.forEach((y, i) => {
    const mes = String(i + 1).padStart(2, '0')
    eventos.push(ev('cima', `2000-${mes}-01`, 5 + i))
    eventos.push(ev('baixo', `2000-${mes}-01`, y))
  })
  const r = prever(eventos, 'cima', 'baixo', 10)
  assert.equal(r.status, 'correlacao-fraca')
})

test('relação decrescente é tratada como implausível', () => {
  const eventos: Evento[] = []
  for (let i = 0; i < 8; i++) {
    const mes = String(i + 1).padStart(2, '0')
    eventos.push(ev('cima', `2000-${mes}-01`, 5 + i))
    eventos.push(ev('baixo', `2000-${mes}-01`, 20 - 0.9 * (5 + i)))
  }
  const r = prever(eventos, 'cima', 'baixo', 10)
  assert.equal(r.status, 'relacao-implausivel')
})
