import { test } from 'node:test'
import assert from 'node:assert/strict'
import { caixaDoControle, caixasDosControles, type Retangulo } from './controlesSobreOMapa'
import { colide, type Caixa } from './mapaMotor'

/** O mapa não começa em 0,0 da janela: há cabeçalho e abas acima dele. */
const MAPA: Retangulo = { left: 8, top: 248, right: 928, bottom: 1720 }

const ret = (left: number, top: number, larg: number, alt: number): Retangulo => ({
  left,
  top,
  right: left + larg,
  bottom: top + alt,
})

test('converte de coordenadas da janela para as do canvas', () => {
  // O botão + da captura: encostado na esquerda, uns 500 px abaixo do topo do mapa.
  const c = caixaDoControle(ret(24, 748, 92, 78), MAPA)
  assert.deepEqual(c, { x0: 16, y0: 500, x1: 108, y1: 578 })
})

test('a folga afasta o rótulo da borda do botão', () => {
  const c = caixaDoControle(ret(24, 748, 92, 78), MAPA, 6)!
  assert.equal(c.x0, 10)
  assert.equal(c.y1, 584)
})

test('controle de tamanho zero não reserva nada', () => {
  // "Ver tudo" só existe com zoom > 1. Enquanto não existe, o retângulo é
  // 0×0 — e reservar espaço por um botão que ninguém vê esconderia o nome de
  // uma cidade de graça.
  assert.equal(caixaDoControle(ret(24, 900, 0, 0), MAPA), null)
  assert.equal(caixasDosControles([ret(24, 900, 0, 0)], MAPA).length, 0)
})

test('o rótulo que caía atrás do botão + agora colide, e por isso some', () => {
  // A captura de 06/09/2026: "Timbó" desenhado em x≈100, y≈590 do canvas,
  // exatamente onde vive o botão +. Antes o canvas não sabia do botão.
  const timbo: Caixa = { x0: 30, y0: 560, x1: 260, y1: 600 }
  const controles = caixasDosControles([ret(24, 748, 92, 78)], MAPA)
  assert.ok(colide(timbo, controles), 'sem isto o nome sai por baixo do botão')
})

test('rótulo longe dos controles continua passando', () => {
  const itajai: Caixa = { x0: 700, y0: 480, x1: 860, y1: 530 }
  const controles = caixasDosControles([ret(24, 748, 92, 78), ret(24, 990, 160, 90)], MAPA)
  assert.equal(colide(itajai, controles), false)
})

test('vários controles viram várias caixas, na ordem em que chegam', () => {
  const cs = caixasDosControles([ret(24, 300, 100, 50), ret(24, 748, 92, 78)], MAPA, 0)
  assert.equal(cs.length, 2)
  assert.equal(cs[0]!.y0, 52)
  assert.equal(cs[1]!.y0, 500)
})
