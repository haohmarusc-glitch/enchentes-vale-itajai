/**
 * O PICO DE HOJE EM BLUMENAU — para cruzar com a maré em Itajaí no dia da cheia.
 *
 * Pedido do Jefferson (03/10/2026): "a pessoa precisa saber no dia se coincide
 * com a maré, e não data histórica". O simulador só aceitava uma data digitada;
 * agora ele também lê a série das últimas horas de Blumenau e diz em que
 * situação o rio está.
 *
 * O cuidado que continua valendo: A ÚLTIMA LEITURA NÃO É O PICO. Enquanto o rio
 * sobe, o pico ainda não aconteceu — o horário dele é desconhecido, e o que se
 * mostra é um "se o pico fosse agora", rotulado assim. O pico só é dado como
 * PASSADO quando o rio já desceu claramente abaixo do máximo, em mais de uma
 * leitura. E um pico de Blumenau costuma ser um PLATÔ de horas (em 12/09/2026 o
 * rio ficou a menos de 5 cm do máximo das 00h às 06h): a janela de chegada usa o
 * platô inteiro, não um minuto escolhido nele.
 */
import type { PontoSerie } from '../dados/serie'
import { tendencia, type Tendencia } from '../dados/serie'
import { frescorDaCidade, idadeMin } from './tempoReal'

/** Janela olhada para trás: uma cheia em Blumenau sobe e desce em um a dois dias. */
export const JANELA_H = 36
/** Quanto o rio precisa ter descido do máximo para o pico contar como passado. */
export const QUEDA_PICO_M = 0.1
/** Faixa em torno do máximo que conta como o mesmo platô. */
export const PLATO_M = 0.05

export type SituacaoPico =
  | { tipo: 'sem-dado' }
  | {
      tipo: 'subindo' | 'no-alto'
      ultimo: PontoSerie
      tendencia: Tendencia | null
    }
  | {
      tipo: 'passou'
      pico: PontoSerie
      /** Começo e fim do platô em torno do máximo. */
      platoInicio: Date
      platoFim: Date
      /** O máximo é o primeiro ponto da janela: o pico pode ter sido antes. */
      inicioIncerto: boolean
      ultimo: PontoSerie
    }

/**
 * A situação do pico em Blumenau, a partir de UMA publicação da régua (a série
 * de duas fontes intercaladas mediria a diferença entre elas, não o rio).
 */
export function situacaoDoPico(pontos: PontoSerie[], agora: Date): SituacaoPico {
  const desde = agora.getTime() - JANELA_H * 3_600_000
  const serie = pontos
    .filter((p) => p.medidoEm.getTime() >= desde && p.medidoEm.getTime() <= agora.getTime() + 15 * 60_000)
    .filter((p) => Number.isFinite(p.nivel_m))
    .sort((a, b) => a.medidoEm.getTime() - b.medidoEm.getTime())
  if (serie.length < 2) return { tipo: 'sem-dado' }
  const ultimo = serie[serie.length - 1]!
  if (frescorDaCidade(idadeMin(ultimo.medidoEm, agora), 'blumenau') === 'velha') return { tipo: 'sem-dado' }

  let iMax = 0
  serie.forEach((p, i) => {
    if (p.nivel_m > serie[iMax]!.nivel_m) iMax = i
  })
  const maximo = serie[iMax]!
  const t = tendencia(serie)
  const depois = serie.slice(iMax + 1)
  const desceu =
    maximo.nivel_m - ultimo.nivel_m >= QUEDA_PICO_M &&
    depois.length >= 2 &&
    depois.slice(-2).every((p) => p.nivel_m <= maximo.nivel_m - PLATO_M) &&
    t?.rotulo !== 'subindo'
  if (!desceu) return { tipo: t?.rotulo === 'subindo' ? 'subindo' : 'no-alto', ultimo, tendencia: t }

  // O platô: os pontos contíguos ao máximo que ficam a até PLATO_M dele.
  let a = iMax
  while (a > 0 && serie[a - 1]!.nivel_m >= maximo.nivel_m - PLATO_M) a--
  let b = iMax
  while (b < serie.length - 1 && serie[b + 1]!.nivel_m >= maximo.nivel_m - PLATO_M) b++
  return {
    tipo: 'passou',
    pico: maximo,
    platoInicio: serie[a]!.medidoEm,
    platoFim: serie[b]!.medidoEm,
    inicioIncerto: a === 0,
    ultimo,
  }
}

/**
 * A publicação de Blumenau a usar: a que tem a leitura mais recente. Blumenau
 * chega por duas fontes da mesma régua (Defesa Civil de Itajaí e AlertaBlu);
 * misturá-las faria serrilhado (ver `PontoSerie.regua`).
 */
export function publicacaoMaisRecente(porRegua: Map<string, PontoSerie[]>): PontoSerie[] {
  let melhor: PontoSerie[] = []
  let quando = -Infinity
  for (const pontos of porRegua.values()) {
    const ultimo = pontos[pontos.length - 1]
    if (ultimo && ultimo.medidoEm.getTime() > quando) {
      quando = ultimo.medidoEm.getTime()
      melhor = pontos
    }
  }
  return melhor
}
