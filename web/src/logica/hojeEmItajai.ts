/**
 * O "HOJE" DO PAINEL DE CHEGADA × MARÉ EM ITAJAÍ, sem a tela.
 *
 * A decisão que o painel `SimulacaoChegada` (aba "Hoje") toma sobre a série de Blumenau, separada da
 * renderização para que o chat (7ª entrega, docs/CHAT-GLOBAL-COMANDOS.md) diga exatamente o mesmo que a
 * tela: as mesmas funções (`situacaoDoPico`, `simularChegada`, `janelaJaPassou`), os mesmos ramos e a mesma
 * referência de estudo. Nada aqui é previsão: enquanto o rio sobe, a janela é a de "se o pico fosse agora".
 */
import type { PontoSerie } from '../dados/serie'
import type { TabuaMare } from '../dados/tipos'
import type { SituacaoPico } from './picoBlumenau'
import { entradaBrasilia, janelaJaPassou, simularChegada, type ResultadoSimulacao } from './simulacaoChegada'

const HORA = 3_600_000

export type HojeEmItajai =
  | { tipo: 'sem-dado' }
  /** Blumenau abaixo da primeira cota, e não passou dela na janela: não há pico de cheia descendo. */
  | { tipo: 'abaixo-da-cota'; ultimo: PontoSerie }
  /** A maior leitura é a primeira da janela: o pico pode ter sido antes. A janela sai como hipótese. */
  | { tipo: 'nao-confirmado'; pico: PontoSerie; ultimo: PontoSerie; resultado: ResultadoSimulacao; janelaPassou: boolean }
  /** O pico passou, com o platô inteiro na janela de chegada. */
  | {
      tipo: 'passou'
      pico: PontoSerie
      ultimo: PontoSerie
      platoInicio: Date
      platoFim: Date
      horasPlato: number
      resultado: ResultadoSimulacao
      janelaPassou: boolean
    }
  /** Ainda subindo, ou perto do alto sem descida confirmada: a janela é a de "se o pico fosse agora". */
  | { tipo: 'subindo' | 'no-alto'; ultimo: PontoSerie; cmh: number | null; resultado: ResultadoSimulacao }

export function hojeEmItajai(
  situacao: SituacaoPico,
  cota: { valor: number } | null,
  referencia: { horas_min: number; horas_max: number },
  tabua: Pick<TabuaMare, 'preamares' | 'baixamares'>,
  agora: Date,
): HojeEmItajai {
  if (situacao.tipo === 'sem-dado') return { tipo: 'sem-dado' }
  if (!('pico' in situacao)) {
    // Ainda subindo, ou perto do alto sem descida confirmada.
    if (cota && situacao.ultimo.nivel_m < cota.valor) return { tipo: 'abaixo-da-cota', ultimo: situacao.ultimo }
    const resultado = simularChegada(entradaBrasilia(situacao.ultimo.medidoEm), referencia.horas_min, referencia.horas_max, tabua)
    return { tipo: situacao.tipo, ultimo: situacao.ultimo, cmh: situacao.tendencia ? Math.abs(situacao.tendencia.cmh) : null, resultado }
  }
  if (cota && situacao.pico.nivel_m < cota.valor) return { tipo: 'abaixo-da-cota', ultimo: situacao.ultimo }
  if (situacao.tipo === 'nao-confirmado') {
    const resultado = simularChegada(entradaBrasilia(situacao.pico.medidoEm), referencia.horas_min, referencia.horas_max, tabua)
    return { tipo: 'nao-confirmado', pico: situacao.pico, ultimo: situacao.ultimo, resultado, janelaPassou: janelaJaPassou(resultado, agora) }
  }
  const horasPlato = (situacao.platoFim.getTime() - situacao.platoInicio.getTime()) / HORA
  const resultado = simularChegada(
    entradaBrasilia(situacao.platoInicio),
    referencia.horas_min,
    referencia.horas_max + Math.round(horasPlato * 10) / 10,
    tabua,
  )
  return {
    tipo: 'passou',
    pico: situacao.pico,
    ultimo: situacao.ultimo,
    platoInicio: situacao.platoInicio,
    platoFim: situacao.platoFim,
    horasPlato,
    resultado,
    janelaPassou: janelaJaPassou(resultado, agora),
  }
}
