/**
 * Ligar a MANCHA de inundação ao NÍVEL do rio agora — quando isso for possível.
 *
 * O pedido: "quando os rios encherem, a mancha aparece no mapa". A forma
 * honesta disso NÃO é prever onde a água vai chegar; é dizer o que já se viu:
 *
 *     "o rio está em 3,20 m. No evento de 2011, quando marcou 3,05 m,
 *      a água cobriu esta área."
 *
 * A diferença não é de redação. Mancha é o registro do que aconteceu numa
 * cidade que existia naquele ano — antes de obra, de aterro, de canal. Chamá-la
 * de "a área alagada agora" afirmaria uma previsão que polígono nenhum carrega,
 * e o erro cairia para o lado de fazer alguém se sentir seguro fora dela.
 *
 * ⛔ ESTADO EM 05/09/2026: ISTO NÃO ACENDE, e o motivo é dado, não código.
 * As dez manchas de Itajaí têm `pico_registrado: null`, porque Itajaí tem ZERO
 * registros em `enchentes.json` (medido: Blumenau 113, Rio do Sul 9, Brusque 9,
 * Itajaí 0). Sem o pico do evento não existe número para comparar com o nível de
 * hoje, e inventá-lo seria o pior desfecho possível numa tela de enchente.
 * O mecanismo fica pronto e ESCURO: no dia em que os picos de Itajaí entrarem no
 * cadastro, ele acende sozinho. Há teste provando as duas metades.
 *
 * A SEGUNDA TRAVA, que sobrevive à primeira: Itajaí tem ONZE réguas com zeros
 * diferentes. Um pico medido na régua A não se compara com a leitura da régua B
 * — é a regra nº 1 do projeto. Por isso `reguaDoPico` tem de bater com
 * `reguaDaLeitura`, e um pico sem régua declarada NÃO é usado.
 */

export interface ManchaComparavel {
  evento: string
  arquivo: string
  /** O pico daquele evento, se registrado. `null` = não se sabe. */
  picoM: number | null
  /** Em que régua o pico foi medido. `null` = não declarado, e aí não serve. */
  reguaDoPico: string | null
}

export interface ManchaNoNivel extends ManchaComparavel {
  /** O pico deste evento, comparado com o nível de agora. */
  picoM: number
  /** Quanto o nível de hoje está abaixo (negativo) ou acima (positivo) do pico. */
  diferencaM: number
}

export interface LeituraDeManchas {
  /** Eventos cujo pico o rio JÁ ULTRAPASSOU, do maior para o menor. */
  jaPassou: ManchaNoNivel[]
  /** O próximo evento acima do nível de agora — o mais perto, ainda não atingido. */
  proximo: ManchaNoNivel | null
  /** Manchas sem pico ou sem régua: existem, e não entram na conta. */
  semPico: ManchaComparavel[]
}

/**
 * Separa as manchas em "o rio já passou disto" e "ainda não", pelo nível atual.
 *
 * `nivelM` nulo ou não finito devolve tudo em `semPico`: sem leitura não há
 * comparação, e "sem leitura" não é o mesmo que "abaixo de tudo".
 */
export function manchasPorNivel(
  manchas: readonly ManchaComparavel[],
  nivelM: number | null | undefined,
  reguaDaLeitura: string | null,
): LeituraDeManchas {
  const semPico: ManchaComparavel[] = []
  const comparaveis: ManchaNoNivel[] = []
  const temLeitura = typeof nivelM === 'number' && Number.isFinite(nivelM)

  for (const m of manchas) {
    const picoOk = typeof m.picoM === 'number' && Number.isFinite(m.picoM)
    // Régua diferente é régua diferente: zeros distintos, metros que não se
    // comparam. Pico sem régua declarada também não serve — não se sabe de onde.
    const mesmaRegua =
      m.reguaDoPico != null && reguaDaLeitura != null && m.reguaDoPico === reguaDaLeitura
    if (!picoOk || !mesmaRegua || !temLeitura) {
      semPico.push(m)
      continue
    }
    comparaveis.push({ ...m, picoM: m.picoM as number, diferencaM: (nivelM as number) - (m.picoM as number) })
  }

  const jaPassou = comparaveis.filter((m) => m.diferencaM >= 0).sort((a, b) => b.picoM - a.picoM)
  const acima = comparaveis.filter((m) => m.diferencaM < 0).sort((a, b) => a.picoM - b.picoM)
  return { jaPassou, proximo: acima[0] ?? null, semPico }
}

/**
 * A frase da tela para um evento já alcançado. Sempre no PASSADO, sempre com o
 * número dos dois lados, e sempre dizendo a régua — quem lê tem de poder
 * conferir a conta.
 */
export function frasePassado(m: ManchaNoNivel, evento: string): string {
  const n = (v: number) => v.toFixed(2).replace('.', ',')
  return `Em ${evento} o rio marcou ${n(m.picoM)} m nesta régua e a água cobriu esta área.`
}

/** A frase para o próximo evento acima: quanto falta, sem prometer que chega. */
export function fraseFalta(m: ManchaNoNivel, evento: string): string {
  const n = (v: number) => v.toFixed(2).replace('.', ',')
  return `Faltam ${n(Math.abs(m.diferencaM))} m para o nível de ${evento} (${n(m.picoM)} m).`
}
