/**
 * Datas em ISO parcial: `AAAA`, `AAAA-MM` ou `AAAA-MM-DD`.
 *
 * Quando o dia é desconhecido o registro guarda só o que se sabe. Nada aqui
 * completa o que falta — a granularidade é preservada e usada para decidir se
 * dois registros podem ou não ser tratados como o mesmo evento.
 */

export type Granularidade = 'dia' | 'mes' | 'ano'

export function granularidade(data: string): Granularidade {
  if (data.length === 10) return 'dia'
  if (data.length === 7) return 'mes'
  return 'ano'
}

export function ano(data: string): number {
  return Number(data.slice(0, 4))
}

/**
 * Intervalo de dias que uma data ISO parcial pode representar, em ms UTC.
 * `2011-09-09` é um único dia; `1983-07` é o mês inteiro; `1855`, o ano inteiro.
 */
function intervalo(data: string): { inicio: number; fim: number } {
  const g = granularidade(data)
  const a = ano(data)
  if (g === 'ano') return { inicio: Date.UTC(a, 0, 1), fim: Date.UTC(a, 11, 31) }
  const m = Number(data.slice(5, 7)) - 1
  if (g === 'mes') return { inicio: Date.UTC(a, m, 1), fim: Date.UTC(a, m + 1, 0) }
  const d = Number(data.slice(8, 10))
  return { inicio: Date.UTC(a, m, d), fim: Date.UTC(a, m, d) }
}

const DIA_MS = 86_400_000

/**
 * Folga máxima, em dias, entre dois registros do mesmo evento.
 *
 * O pico não acontece no mesmo dia em todas as cidades: da cabeceira à foz a
 * cheia leva mais de um dia. Sem essa folga, o pico de Blumenau (09/09) e o de
 * Itajaí (10/09) seriam tratados como eventos diferentes e o pareamento
 * devolveria lista vazia. Sete dias cobrem a bacia inteira com sobra e ainda
 * separam eventos distintos, que na região vêm com semanas de intervalo.
 */
export const TOLERANCIA_DIAS = 7

/**
 * Dois registros descrevem o mesmo evento?
 *
 * Compara os intervalos possíveis das duas datas e aceita um vão de até
 * `TOLERANCIA_DIAS` — aplicado ao vão inteiro, não a cada lado, para que a
 * folga efetiva seja mesmo de sete dias.
 *
 * Entre duas datas de mês conhecido a folga é zero: julho e agosto são
 * eventos distintos, ainda que 31/07 e 01/08 se toquem no calendário.
 *
 * Data só com o ano NUNCA pareia: 2023 teve duas enchentes no mesmo rio
 * (outubro e novembro), e juntar registros de eventos diferentes produziria
 * uma correlação falsa.
 */
export function mesmoEvento(a: string, b: string): boolean {
  const ga = granularidade(a)
  const gb = granularidade(b)
  if (ga === 'ano' || gb === 'ano') return false

  const ia = intervalo(a)
  const ib = intervalo(b)
  const vaoDias = Math.max(0, Math.max(ia.inicio, ib.inicio) - Math.min(ia.fim, ib.fim)) / DIA_MS
  const folga = ga === 'mes' && gb === 'mes' ? 0 : TOLERANCIA_DIAS
  return vaoDias <= folga
}

const MESES = [
  'janeiro',
  'fevereiro',
  'março',
  'abril',
  'maio',
  'junho',
  'julho',
  'agosto',
  'setembro',
  'outubro',
  'novembro',
  'dezembro',
]

/** `2011-09-09` → `9 de setembro de 2011`; `1983-07` → `julho de 1983`; `1855` → `1855`. */
export function dataLegivel(data: string): string {
  const g = granularidade(data)
  const a = data.slice(0, 4)
  if (g === 'ano') return a
  const mes = MESES[Number(data.slice(5, 7)) - 1] ?? data.slice(5, 7)
  if (g === 'mes') return `${mes} de ${a}`
  return `${Number(data.slice(8, 10))} de ${mes} de ${a}`
}

/** Rótulo curto para eixo de gráfico. */
export function dataCurta(data: string): string {
  const g = granularidade(data)
  if (g === 'ano') return data
  if (g === 'mes') return `${data.slice(5, 7)}/${data.slice(0, 4)}`
  return `${data.slice(8, 10)}/${data.slice(5, 7)}/${data.slice(0, 4)}`
}

/** Ordenação cronológica estável para datas de granularidade mista. */
export function comparaData(a: string, b: string): number {
  return a.padEnd(10, '0').localeCompare(b.padEnd(10, '0'))
}
