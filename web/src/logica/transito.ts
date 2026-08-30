/**
 * Tempo de trânsito da onda de cheia entre duas cidades.
 *
 * `transito.json` cobre só alguns trechos, e alguns deles "pulam" cidades
 * (ex.: Blumenau → Itajaí passa por Gaspar e Ilhota sem registro intermediário).
 * A busca abaixo usa o trecho direto quando existe e, na falta dele, encadeia
 * trechos consecutivos. Quando não dá para cobrir o caminho inteiro, o retorno
 * é `null` e a tela diz "sem dado de trânsito" — nunca um palpite.
 *
 * O resultado é sempre uma FAIXA de horas (CLAUDE.md), mesmo quando a fonte
 * traz um valor único: nesse caso mínimo e máximo coincidem e a tela mostra
 * "cerca de N h".
 */
import type { Confianca, Trecho } from '../dados/tipos'

export interface Caminho {
  horasMin: number
  horasMax: number
  /** true quando existe um trecho direto entre as duas cidades. */
  direto: boolean
  trechos: Trecho[]
  /** A pior confiança do caminho — um elo fraco derruba o conjunto. */
  confianca: Confianca
  fontes: string[]
}

const PESO: Record<Confianca, number> = { alta: 0, media: 1, baixa: 2 }

function piorConfianca(cs: Confianca[]): Confianca {
  return cs.reduce((pior, c) => (PESO[c] > PESO[pior] ? c : pior), 'alta' as Confianca)
}

function montar(trechos: Trecho[], direto: boolean): Caminho {
  return {
    horasMin: trechos.reduce((s, t) => s + t.horas_min, 0),
    horasMax: trechos.reduce((s, t) => s + t.horas_max, 0),
    direto,
    trechos,
    confianca: piorConfianca(trechos.map((t) => t.confianca)),
    fontes: [...new Set(trechos.map((t) => t.fonte))],
  }
}

/**
 * Menor cadeia de trechos de `de` até `para`, dentro do mesmo rio.
 * Busca em largura: prefere o caminho com menos elos (menos incerteza acumulada).
 */
export function caminho(
  trechos: Trecho[],
  rioId: string,
  de: string,
  para: string,
): Caminho | null {
  if (de === para) return null
  const doRio = trechos.filter((t) => t.rio === rioId)

  const direto = doRio.find((t) => t.de === de && t.para === para)
  if (direto) return montar([direto], true)

  const fila: { cidade: string; rota: Trecho[] }[] = [{ cidade: de, rota: [] }]
  const visitadas = new Set<string>([de])

  while (fila.length > 0) {
    const atual = fila.shift()!
    for (const t of doRio) {
      if (t.de !== atual.cidade || visitadas.has(t.para)) continue
      const rota = [...atual.rota, t]
      if (t.para === para) return montar(rota, false)
      visitadas.add(t.para)
      fila.push({ cidade: t.para, rota })
    }
  }
  return null
}

/** `14–17 h` ou `cerca de 6 h` quando a fonte traz valor único. */
export function faixaHoras(c: Pick<Caminho, 'horasMin' | 'horasMax'>): string {
  const fmt = (h: number) => h.toLocaleString('pt-BR', { maximumFractionDigits: 1 })
  if (c.horasMin === c.horasMax) return `cerca de ${fmt(c.horasMin)} h`
  return `${fmt(c.horasMin)}–${fmt(c.horasMax)} h`
}

/** Janela de chegada a partir de um horário de pico informado pelo usuário. */
export function janelaChegada(
  partida: Date,
  c: Pick<Caminho, 'horasMin' | 'horasMax'>,
): { inicio: Date; fim: Date } {
  const ms = 3_600_000
  return {
    inicio: new Date(partida.getTime() + c.horasMin * ms),
    fim: new Date(partida.getTime() + c.horasMax * ms),
  }
}
