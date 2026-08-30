/**
 * Previsão empírica do nível a jusante (v1).
 *
 * Método: regressão linear simples entre o pico da cidade de MONTANTE (x) e o
 * pico da cidade de JUSANTE (y) nos MESMOS eventos históricos de `enchentes.json`.
 *
 * Este arquivo é o ponto mais perigoso do projeto. As travas abaixo existem
 * para que a tela prefira dizer "não sei" a dizer um número errado:
 *
 *  1. Pares vêm só de eventos com mês coincidente (ver `datas.mesmoEvento`).
 *  2. Menos de 5 pares  → `dados-insuficientes` (regra do CLAUDE.md).
 *  3. r² abaixo de 0,50 → `correlacao-fraca`, sem número na tela.
 *  4. Inclinação <= 0   → `relacao-implausivel`: rio a jusante não desce quando
 *     o de montante sobe; sinal de pareamento ruim ou régua trocada.
 *  5. O resultado é sempre um INTERVALO de previsão (95%), nunca um ponto.
 *  6. Entrada fora da faixa observada é marcada como extrapolação.
 *
 * Os metros de x e y estão em RÉGUAS DIFERENTES. A regressão é justamente o que
 * traduz uma na outra; por isso os dois números nunca podem ser comparados
 * diretamente na tela.
 */
import type { Confianca, Evento } from '../dados/tipos'
import { mesmoEvento } from './datas'

/** Mínimo de pares para arriscar qualquer estimativa. */
export const MIN_PARES = 5
/** r² mínimo para exibir um número. */
export const R2_MINIMO = 0.5
/** Margem de extrapolação tolerada antes de marcar o aviso, como fração da faixa observada. */
const MARGEM_EXTRAPOLACAO = 0.1

export interface Par {
  data: string
  x: number
  y: number
  confianca: Confianca
}

export interface Ajuste {
  /** y = a + b·x */
  a: number
  b: number
  r2: number
  n: number
  /** Desvio padrão residual (erro típico da estimativa, em metros da régua de jusante). */
  s: number
  xMedio: number
  sxx: number
  xMin: number
  xMax: number
}

export type Previsao =
  | { status: 'dados-insuficientes'; pares: Par[] }
  | { status: 'correlacao-fraca'; ajuste: Ajuste; pares: Par[] }
  | { status: 'relacao-implausivel'; ajuste: Ajuste; pares: Par[] }
  | {
      status: 'ok'
      ajuste: Ajuste
      pares: Par[]
      /** Nível informado para a cidade de montante. */
      entrada: number
      /** Centro da estimativa — nunca mostrar sozinho. */
      central: number
      minimo: number
      maximo: number
      extrapolacao: boolean
    }

/**
 * Pares (pico montante, pico jusante) do mesmo evento.
 *
 * Se uma cidade tiver mais de um registro para o mesmo evento, o par é
 * descartado: não há como saber qual dos dois é o pico correto, e escolher um
 * seria inventar dado.
 */
export function parear(
  eventos: Evento[],
  cidadeMontante: string,
  cidadeJusante: string,
): Par[] {
  const montante = eventos.filter((e) => e.cidade === cidadeMontante)
  const jusante = eventos.filter((e) => e.cidade === cidadeJusante)
  const pares: Par[] = []

  for (const m of montante) {
    const candidatos = jusante.filter((j) => mesmoEvento(m.data, j.data))
    if (candidatos.length !== 1) continue
    const j = candidatos[0]!
    const irmaos = montante.filter((o) => mesmoEvento(o.data, j.data))
    if (irmaos.length !== 1) continue
    pares.push({
      data: m.data.length >= j.data.length ? m.data : j.data,
      x: m.pico_m,
      y: j.pico_m,
      confianca: piorConfianca(m.confianca, j.confianca),
    })
  }
  return pares
}

function piorConfianca(a: Confianca, b: Confianca): Confianca {
  const peso: Record<Confianca, number> = { alta: 0, media: 1, baixa: 2 }
  return peso[a] >= peso[b] ? a : b
}

export function ajustar(pares: Par[]): Ajuste | null {
  const n = pares.length
  if (n < 3) return null

  const xMedio = pares.reduce((s, p) => s + p.x, 0) / n
  const yMedio = pares.reduce((s, p) => s + p.y, 0) / n

  let sxx = 0
  let sxy = 0
  let syy = 0
  for (const p of pares) {
    sxx += (p.x - xMedio) ** 2
    sxy += (p.x - xMedio) * (p.y - yMedio)
    syy += (p.y - yMedio) ** 2
  }
  // Todos os x iguais: a reta é indefinida.
  if (sxx === 0) return null

  const b = sxy / sxx
  const a = yMedio - b * xMedio

  const sqr = pares.reduce((s, p) => s + (p.y - (a + b * p.x)) ** 2, 0)
  const r2 = syy === 0 ? 0 : Math.max(0, 1 - sqr / syy)
  const s = Math.sqrt(sqr / (n - 2))

  const xs = pares.map((p) => p.x)
  return {
    a,
    b,
    r2,
    n,
    s,
    xMedio,
    sxx,
    xMin: Math.min(...xs),
    xMax: Math.max(...xs),
  }
}

/** t de Student, 95% bicaudal, por graus de liberdade. */
const T_95: Record<number, number> = {
  1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
  8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.16, 14: 2.145,
  15: 2.131, 16: 2.12, 17: 2.11, 18: 2.101, 19: 2.093, 20: 2.086, 21: 2.08,
  22: 2.074, 23: 2.069, 24: 2.064, 25: 2.06, 26: 2.056, 27: 2.052, 28: 2.048,
  29: 2.045, 30: 2.042,
}

function t95(gl: number): number {
  if (gl <= 0) return Number.POSITIVE_INFINITY
  return T_95[gl] ?? 1.96
}

export function prever(
  eventos: Evento[],
  cidadeMontante: string,
  cidadeJusante: string,
  nivelMontante: number,
): Previsao {
  const pares = parear(eventos, cidadeMontante, cidadeJusante)
  const ajuste = pares.length >= MIN_PARES ? ajustar(pares) : null
  if (!ajuste) return { status: 'dados-insuficientes', pares }
  if (ajuste.r2 < R2_MINIMO) return { status: 'correlacao-fraca', ajuste, pares }
  if (ajuste.b <= 0) return { status: 'relacao-implausivel', ajuste, pares }

  const central = ajuste.a + ajuste.b * nivelMontante
  // Intervalo de PREVISÃO (uma nova observação), não intervalo da média.
  const erro =
    t95(ajuste.n - 2) *
    ajuste.s *
    Math.sqrt(1 + 1 / ajuste.n + (nivelMontante - ajuste.xMedio) ** 2 / ajuste.sxx)

  const faixa = ajuste.xMax - ajuste.xMin
  const folga = faixa * MARGEM_EXTRAPOLACAO
  const extrapolacao = nivelMontante < ajuste.xMin - folga || nivelMontante > ajuste.xMax + folga

  return {
    status: 'ok',
    ajuste,
    pares,
    entrada: nivelMontante,
    central,
    minimo: Math.max(0, central - erro),
    maximo: central + erro,
    extrapolacao,
  }
}
