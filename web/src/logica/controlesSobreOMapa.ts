import type { Caixa } from './mapaMotor'

/**
 * Os CONTROLES DE HTML que ficam por cima do canvas, como caixas do canvas.
 *
 * O DEFEITO QUE ISTO CORRIGE (06/09/2026, capturas do Jefferson no celular).
 * A anticolisão do mapa só conhecia o que o próprio canvas desenha — pinos,
 * barragens, réguas, chip da maré. Os botões são DOM por cima do vidro, e o
 * canvas não os enxergava: "Timbó" saía atrás do botão +, "Blumenau" atrás do
 * −, e sobrava "…mbó" e "…nau" na tela. Nome de cidade cortado pela metade num
 * mapa de cheia é pior que nome nenhum — quem lê "nau" não sabe se é Blumenau
 * ou Navegantes, e são lados opostos da bacia.
 *
 * A conversão é só de sistema de coordenadas: o retângulo do elemento vem em
 * coordenadas da JANELA (`getBoundingClientRect`), e o canvas desenha em
 * pixels CSS a partir do próprio canto. Daí a subtração.
 *
 * A `folga` afasta o rótulo da borda do botão: encostar não é colidir, mas
 * texto colado num botão opaco se lê mal.
 */
export interface Retangulo {
  left: number
  top: number
  right: number
  bottom: number
}

export function caixaDoControle(
  el: Retangulo,
  mapa: Retangulo,
  folga = 0,
): Caixa | null {
  const caixa: Caixa = {
    x0: el.left - mapa.left - folga,
    y0: el.top - mapa.top - folga,
    x1: el.right - mapa.left + folga,
    y1: el.bottom - mapa.top + folga,
  }
  // Elemento de tamanho zero (botão que não está na tela, como o "Ver tudo"
  // quando o zoom é 1) não reserva nada: reservar seria esconder rótulo por
  // causa de um controle que ninguém vê.
  if (el.right <= el.left || el.bottom <= el.top) return null
  return caixa
}

export function caixasDosControles(
  els: readonly Retangulo[],
  mapa: Retangulo,
  folga = 0,
): Caixa[] {
  const fora: Caixa[] = []
  for (const el of els) {
    const c = caixaDoControle(el, mapa, folga)
    if (c) fora.push(c)
  }
  return fora
}
