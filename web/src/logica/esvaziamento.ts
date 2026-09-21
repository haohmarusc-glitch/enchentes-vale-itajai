import type { Tendencia } from '../dados/serie'

/**
 * O que dizer quando a barragem acima está soltando água.
 *
 * Decisão do Jefferson (21/09/2026), no lugar da regra proposta em 09/2026
 * ("comportas abertas e nível estável ou caindo → sem cor de alerta"):
 * **a cor do nível continua a do nível.** Tirar a cor poderia transmitir
 * segurança antes de a água baixar. O que se acrescenta é um ESTADO,
 * "esvaziando", ao lado do número — e só quando o rio a jusante não está
 * subindo. Com o rio subindo e comportas abertas, o estado é o oposto: a
 * barragem está vertendo numa cheia nova, e isso se diz, sem suavizar.
 *
 * Sem tendência (série misturada, ou curta demais) não se afirma nada além
 * do fato da comporta, que o bloco já mostra.
 */
export type EstadoDeEsvaziamento =
  | { rotulo: 'esvaziando'; frase: string }
  | { rotulo: 'vertendo com o rio subindo'; frase: string }
  | null

export function estadoDeEsvaziamento(
  abertas: number,
  total: number,
  tendencia: Tendencia | null,
): EstadoDeEsvaziamento {
  if (!Number.isFinite(abertas) || !Number.isFinite(total) || total <= 0 || abertas <= 0) return null
  if (!tendencia) return null
  if (tendencia.rotulo === 'subindo') {
    return {
      rotulo: 'vertendo com o rio subindo',
      frase: 'a barragem solta água e o rio abaixo continua subindo — a cor do nível vale como está',
    }
  }
  return {
    rotulo: 'esvaziando',
    frase:
      tendencia.rotulo === 'descendo'
        ? 'a barragem solta água e o rio abaixo está baixando — a cor continua sendo a do nível, até a água baixar de verdade'
        : 'a barragem solta água e o rio abaixo está parado — a cor continua sendo a do nível, até a água baixar de verdade',
  }
}
