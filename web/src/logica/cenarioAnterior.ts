import type { Confianca, Evento } from '../dados/tipos'

/**
 * A que distância o rio está de cada cheia que já aconteceu naquela cidade.
 *
 * A PERGUNTA QUE ESTE MÓDULO **NÃO** RESPONDE. "O nível de agora parece com
 * qual enchente?" — porque a pergunta contém um erro. Um nível qualquer não se
 * compara com um PICO: estar em 8,0 m subindo não é "igual" à cheia que picou
 * em 8,5 m, é possivelmente pior, porque ainda vai subir. Dizer "parecido com
 * 2008" a quem está com água chegando no portão é oferecer um fim conhecido
 * para uma história que ainda não terminou.
 *
 * O que ele responde: **quanto falta**. "O rio está em 4,69 m; a cheia de 2011
 * chegou a 10,03 m; faltam 5,34 m." Distância é um fato; semelhança é um
 * palpite.
 *
 * O PAR RÉGUA↔PICO É PRÉ-REQUISITO, NÃO DETALHE. Subtrair a leitura de agora de
 * um pico medido em outra referência dá um número com duas casas decimais e
 * nenhum significado — o erro que este projeto já cometeu em Ilhota, em Brusque
 * e na série de Blumenau. Por isso `cenarioDaCidade` devolve `pode: false` com
 * o motivo em vez de calcular, sempre que não puder provar que a escala é uma
 * só. Hoje isso exclui Blumenau inteira: 72 dos 113 picos dela estão em
 * `IBGE (régua + 0,20 m)` e 41 em `null`, e a leitura ao vivo é da régua — são
 * os 20 cm da REGRA BLOQUEANTE do CLAUDE.md, que só o HidroWeb resolve.
 */

/** Referências que convivem com a leitura ao vivo, que é sempre de régua. */
const REFERENCIAS_DE_REGUA = new Set(['régua'])

export type MotivoSemCenario =
  | 'sem-leitura'
  | 'sem-picos'
  | 'referencia-de-outra-escala'
  | 'referencia-misturada'

export interface Marca {
  data: string
  pico: number
  /** `pico − nível`. Positivo: falta subir isto. Negativo: o rio já passou. */
  diferenca: number
  passou: boolean
  confianca: Confianca
  /** A referência foi declarada na fonte, ou é a suposição de registro antigo? */
  referenciaConferida: boolean
}

export interface Cenario {
  nivel: number
  /** Todas as marcas, da mais alta para a mais baixa — a ordem do gráfico. */
  marcas: Marca[]
  /** A primeira marca ACIMA do nível de agora, se houver. */
  proxima: Marca | null
  /** A marca mais alta que o rio já passou, se houver. */
  ultimaPassada: Marca | null
  /**
   * Falso quando nenhum pico declara a referência e ela é suposta pela
   * convenção "campo ausente = régua local". A tela precisa dizer isso.
   */
  referenciaConferida: boolean
}

export function cenarioDaCidade(
  nivel: number | null | undefined,
  eventos: readonly Evento[],
): { cenario: Cenario; motivo: null } | { cenario: null; motivo: MotivoSemCenario } {
  if (typeof nivel !== 'number' || !Number.isFinite(nivel)) {
    return { cenario: null, motivo: 'sem-leitura' }
  }
  const comPico = eventos.filter((e) => Number.isFinite(e.pico_m))
  if (comPico.length === 0) return { cenario: null, motivo: 'sem-picos' }

  // `undefined` (campo ausente) = registro antigo, assumido na régua local — é
  // a mesma convenção que o cabeçalho do gráfico de picos já usa. `null` é
  // diferente: o campo existe e ninguém conferiu, e aí a escala é uma
  // incógnita, não uma suposição. Achatar os dois aqui seria repetir, num
  // simulador, o erro que `referenciasDistintas` existe para impedir.
  const escalas = new Set(
    comPico.map((e) => ('referencia' in e ? (e.referencia === null ? 'nao-declarada' : e.referencia) : 'ausente')),
  )
  if (escalas.size > 1) return { cenario: null, motivo: 'referencia-misturada' }
  const escala = [...escalas][0]!
  if (escala !== 'ausente' && !REFERENCIAS_DE_REGUA.has(escala)) {
    return { cenario: null, motivo: 'referencia-de-outra-escala' }
  }

  const referenciaConferida = escala !== 'ausente'
  const marcas: Marca[] = comPico
    .map((e) => ({
      data: e.data,
      pico: e.pico_m,
      diferenca: Number((e.pico_m - nivel).toFixed(2)),
      passou: e.pico_m <= nivel,
      confianca: e.confianca,
      referenciaConferida,
    }))
    .sort((a, b) => b.pico - a.pico)

  const acima = marcas.filter((m) => !m.passou)
  return {
    cenario: {
      nivel,
      marcas,
      // A PRÓXIMA é a mais baixa das que ainda estão acima: é a primeira que o
      // rio encosta se continuar subindo. Pegar a mais alta diria "faltam 5 m"
      // quando faltam 30 cm para a primeira.
      proxima: acima.length ? acima[acima.length - 1]! : null,
      ultimaPassada: marcas.find((m) => m.passou) ?? null,
      referenciaConferida,
    },
    motivo: null,
  }
}
