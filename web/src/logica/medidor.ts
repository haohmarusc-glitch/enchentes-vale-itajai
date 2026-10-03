/**
 * A RÉGUA DESENHADA do cartão "Agora": uma barra com as cotas da PRÓPRIA cidade
 * em segmentos coloridos e um marcador no nível. Mostra onde o rio está dentro
 * da escala dela — nunca ao lado da escala de outra cidade.
 *
 * Cada segmento tem a cor da faixa que a cota abre (monitoramento, atenção,
 * alerta, inundação/emergência), na ordem de `ORDEM_COTAS`; abaixo da primeira
 * cota, a cor de "abaixo da atenção". Só entram as cotas que pintam faixa —
 * marca de comportamento (Lontras, Timbó) não vira degrau.
 */
import { cotasOperacionais } from './cotasOperacionais'
import type { Faixa } from './tempoReal'

export interface Segmento {
  faixa: Faixa
  /** Início e fim em fração da largura (0–1). */
  de: number
  ate: number
}

export interface Marca {
  chave: string
  valor: number
  /** Posição em fração da largura (0–1). */
  pos: number
}

export interface Escala {
  min: number
  max: number
  segmentos: Segmento[]
  marcas: Marca[]
  /** Posição do nível, ou null quando não há nível para marcar. */
  nivel: number | null
}

/**
 * A escala da barra, ou `null` com menos de uma cota de acionamento.
 *
 * O começo da barra não é o zero da régua: com cotas entre 8,5 e 10,8 m, a
 * barra a partir do zero seria quase toda verde e esconderia a parte que
 * importa. Começa um pouco abaixo da primeira cota e termina um pouco acima da
 * última — e estica para caber o nível, quando ele está fora disso.
 */
export function escalaDoMedidor(cotas: Record<string, unknown>, nivel: number | null): Escala | null {
  const ops = cotasOperacionais(cotas)
  if (ops.length === 0) return null
  const primeira = ops[0]![1]
  const ultima = ops[ops.length - 1]![1]
  const vao = Math.max(ultima - primeira, 1)
  let min = Math.max(0, primeira - vao * 0.6)
  let max = ultima + Math.max(vao * 0.15, 0.5)
  const temNivel = nivel !== null && Number.isFinite(nivel)
  if (temNivel && nivel! < min) min = Math.max(0, nivel! - 0.3)
  if (temNivel && nivel! > max) max = nivel! + 0.3
  const pos = (v: number) => Math.min(1, Math.max(0, (v - min) / (max - min)))

  const segmentos: Segmento[] = [{ faixa: 'normal', de: 0, ate: pos(primeira) }]
  ops.forEach(([chave, valor], i) => {
    const proxima = ops[i + 1]
    segmentos.push({
      faixa: chave as Faixa,
      de: pos(valor),
      ate: proxima ? pos(proxima[1]) : 1,
    })
  })
  return {
    min,
    max,
    segmentos: segmentos.filter((s) => s.ate > s.de),
    marcas: ops.map(([chave, valor]) => ({ chave, valor, pos: pos(valor) })),
    nivel: temNivel ? pos(nivel!) : null,
  }
}
