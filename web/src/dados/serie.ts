/**
 * Busca a série das últimas horas de nível, publicada em tempo de execução.
 *
 * Irmã de `tempoReal.ts`: o `ultimo.json` é um instante; este é a linha do
 * tempo. Vem do mesmo branch `tempo-real`, no arquivo `serie-recente.json` que
 * `scripts/coleta_niveis.py` monta e `publicar_tempo_real.sh` publica —
 * `raw.githubusercontent.com` serve com CORS aberto.
 *
 * `medido_em` é hora de Brasília SEM fuso, igual ao resto do projeto, e é lido
 * com `deBrasilia()` — nada de converter em outro lugar. Falhar aqui é normal:
 * sem o arquivo (coleta antiga, série ainda vazia), a tela não mostra a linha
 * do tempo, e nunca inventa uma.
 */
import { useEffect, useState } from 'react'
import { deBrasilia } from '../logica/tempoReal'

const PADRAO =
  'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/serie-recente.json'

export const URL_SERIE = import.meta.env?.VITE_URL_SERIE || PADRAO

const TEMPO_LIMITE_MS = 8000

export interface PontoSerie {
  /** Instante da medição (Brasília, já resolvido para o momento real). */
  medidoEm: Date
  nivel_m: number
}

export type SituacaoSerie = 'carregando' | 'ok' | 'indisponivel'

export interface EstadoSerie {
  situacao: SituacaoSerie
  /** rio -> cidade -> pontos ordenados no tempo. */
  series: Record<string, Record<string, PontoSerie[]>>
  janelaHoras: number | null
  geradoEm: Date | null
}

const VAZIO: EstadoSerie = {
  situacao: 'indisponivel',
  series: {},
  janelaHoras: null,
  geradoEm: null,
}

function pontoValido(bruto: unknown): PontoSerie | null {
  if (typeof bruto !== 'object' || bruto === null) return null
  const d = bruto as Record<string, unknown>
  if (typeof d.medido_em !== 'string') return null
  if (typeof d.nivel_m !== 'number' || Number.isNaN(d.nivel_m)) return null
  const medidoEm = deBrasilia(d.medido_em)
  if (Number.isNaN(medidoEm.getTime())) return null
  return { medidoEm, nivel_m: d.nivel_m }
}

export type Transporte = (url: string, init: RequestInit) => Promise<Response>

export async function buscarSerie(
  sinal?: AbortSignal,
  transporte: Transporte = (url, init) => fetch(url, init),
): Promise<EstadoSerie> {
  try {
    const resposta = await transporte(URL_SERIE, { cache: 'no-store', signal: sinal })
    if (!resposta.ok) return VAZIO
    const corpo: unknown = await resposta.json()
    if (typeof corpo !== 'object' || corpo === null) return VAZIO
    const dados = corpo as Record<string, unknown>
    const brutoSeries = dados.series
    if (typeof brutoSeries !== 'object' || brutoSeries === null) return VAZIO

    const series: Record<string, Record<string, PontoSerie[]>> = {}
    for (const [rio, porCidade] of Object.entries(brutoSeries as Record<string, unknown>)) {
      if (typeof porCidade !== 'object' || porCidade === null) continue
      for (const [cidade, pontos] of Object.entries(porCidade as Record<string, unknown>)) {
        if (!Array.isArray(pontos)) continue
        const validos = pontos
          .map(pontoValido)
          .filter((p): p is PontoSerie => p !== null)
          .sort((a, b) => a.medidoEm.getTime() - b.medidoEm.getTime())
        if (validos.length > 0) {
          ;(series[rio] ??= {})[cidade] = validos
        }
      }
    }

    const gerado =
      typeof dados.gerado_em === 'string' ? new Date(dados.gerado_em) : null
    return {
      situacao: 'ok',
      series,
      janelaHoras: typeof dados.janela_horas === 'number' ? dados.janela_horas : null,
      geradoEm: gerado && !Number.isNaN(gerado.getTime()) ? gerado : null,
    }
  } catch {
    return VAZIO
  }
}

export async function buscarSerieComLimite(
  limiteMs: number = TEMPO_LIMITE_MS,
  transporte?: Transporte,
  registrar?: (c: AbortController) => void,
): Promise<EstadoSerie> {
  const controle = new AbortController()
  registrar?.(controle)
  const limite = setTimeout(() => controle.abort(), limiteMs)
  try {
    return await buscarSerie(controle.signal, transporte)
  } finally {
    clearTimeout(limite)
  }
}

/** Busca ao abrir e a cada `intervaloMin` — a série cresce enquanto a chuva cai. */
export function useSerieRecente(intervaloMin = 5): EstadoSerie {
  const [estado, setEstado] = useState<EstadoSerie>({
    situacao: 'carregando',
    series: {},
    janelaHoras: null,
    geradoEm: null,
  })

  useEffect(() => {
    let vivo = true
    const emVoo = new Set<AbortController>()
    const buscar = async () => {
      let meu: AbortController | null = null
      const novo = await buscarSerieComLimite(TEMPO_LIMITE_MS, undefined, (c) => {
        meu = c
        emVoo.add(c)
      })
      if (meu) emVoo.delete(meu)
      if (vivo) setEstado(novo)
    }
    void buscar()
    const relogio = setInterval(() => void buscar(), intervaloMin * 60_000)
    return () => {
      vivo = false
      clearInterval(relogio)
      for (const c of emVoo) c.abort()
    }
  }, [intervaloMin])

  return estado
}

/** Os pontos de uma cidade naquele rio, ou lista vazia. */
export function serieDaCidade(estado: EstadoSerie, rioId: string, cidadeId: string): PontoSerie[] {
  return estado.series[rioId]?.[cidadeId] ?? []
}
