import type { TabuaMare } from '../dados/tipos'
import { deBrasilia } from './tempoReal'

const HORA = 3_600_000
const FUSO = 'America/Sao_Paulo'
export function entradaBrasilia(data: Date): string {
  const partes = new Intl.DateTimeFormat('en-CA', {
    timeZone: FUSO, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(data)
  const p = (tipo: string) => partes.find((x) => x.type === tipo)?.value
  return `${p('year')}-${p('month')}-${p('day')}T${p('hour')}:${p('minute')}`
}

/** Rejeita normalização silenciosa de 30/02 e hora inexistente no horário de verão. */
export function instanteLocal(valor: string): Date | null {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(valor)) return null
  const data = deBrasilia(valor)
  return Number.isFinite(data.getTime()) && entradaBrasilia(data) === valor ? data : null
}

export interface ExtremoSimulacao {
  tipo: 'preamar' | 'baixamar'
  quando: Date
  altura: number | null
  dentro: boolean
}
export type ResultadoSimulacao = { erro: string } | {
  inicio: Date
  fim: Date
  cobertura: boolean
  preamaresDentro: number
  extremos: ExtremoSimulacao[]
}

/** Cenário condicional; não detecta um pico nem infere risco de inundação.
 * Cruza extremos da tábua SEM a tolerância arbitrária de ±2 h do módulo antigo.
 * Sem extremos que cerquem toda a janela, ou com lacuna >12 h, não conclui ausência
 * de coincidência. A altura permanece a da tábua, nunca interpolada como medição.
 */
export function simularChegada(
  partida: string, minimo: number, maximo: number,
  tabua: Pick<TabuaMare, 'preamares' | 'baixamares'>,
): ResultadoSimulacao {
  const pico = instanteLocal(partida)
  if (!pico) return { erro: 'Informe uma data e hora válidas para o pico em Blumenau, no horário de Brasília.' }
  if (!Number.isFinite(minimo) || !Number.isFinite(maximo) || minimo <= 0 || maximo > 72 || minimo >= maximo) {
    return { erro: 'Informe um intervalo maior que zero, com mínimo menor que o máximo e máximo de até 72 horas.' }
  }
  const inicio = new Date(pico.getTime() + minimo * HORA)
  const fim = new Date(pico.getTime() + maximo * HORA)
  const extremos: ExtremoSimulacao[] = []
  for (const [tipo, entradas] of [['preamar', tabua.preamares], ['baixamar', tabua.baixamares]] as const) {
    for (const e of entradas) {
      const quando = instanteLocal(e.quando)
      if (!quando) continue
      extremos.push({ tipo, quando, altura: typeof e.altura_m === 'number' && Number.isFinite(e.altura_m) ? e.altura_m : null,
        dentro: quando >= inicio && quando <= fim })
    }
  }
  extremos.sort((a, b) => a.quando.getTime() - b.quando.getTime())
  let antes = -1
  extremos.forEach((e, i) => { if (e.quando <= inicio) antes = i })
  const depois = extremos.findIndex((e) => e.quando >= fim)
  let cobertura = antes >= 0 && depois >= 0
  if (cobertura) {
    for (let i = antes + 1; i <= depois; i++) {
      const a = extremos[i - 1]!, b = extremos[i]!
      const distancia = b.quando.getTime() - a.quando.getTime()
      if (distancia <= 0 || distancia > 12 * HORA || a.tipo === b.tipo) cobertura = false
    }
  }
  return {
    inicio, fim, cobertura,
    preamaresDentro: extremos.filter((e) => e.dentro && e.tipo === 'preamar').length,
    extremos: extremos.filter((e, i) => e.dentro
      || (i === antes && inicio.getTime() - e.quando.getTime() <= 12 * HORA)
      || (i === depois && e.quando.getTime() - fim.getTime() <= 12 * HORA)),
  }
}
