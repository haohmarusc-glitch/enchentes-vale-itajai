/** Tipos dos JSONs de `data/`, que são a fonte de verdade do projeto. */

export type Confianca = 'alta' | 'media' | 'baixa'

export type RioId = 'itajai-acu' | 'itajai-mirim'

export interface Cidade {
  id: string
  nome: string
  ordem: number
  codigo_ana: string | null
  verificado: boolean
  regua?: string
  barragem?: string
  observacao?: string
  afluentes?: string[]
  /** Cotas de referência na régua LOCAL. Cada cidade tem seu próprio zero. */
  cotas_m: Record<string, number>
  fontes_tempo_real: string[]
}

export interface Rio {
  nome: string
  foz: string
  cidades: Cidade[]
}

export interface Estacoes {
  _meta: unknown
  rios: Record<string, Rio>
  fontes_gerais: Record<string, string>
}

export interface Evento {
  rio: string
  cidade: string
  /** ISO parcial: `AAAA`, `AAAA-MM` ou `AAAA-MM-DD`. */
  data: string
  pico_m: number
  confianca: Confianca
  fonte: string
  /** Horário do pico, quando conhecido (`HH:MM`). Ainda ausente na maioria dos registros. */
  hora?: string
}

export interface Enchentes {
  _meta: unknown
  eventos: Evento[]
}

export interface Trecho {
  rio: string
  de: string
  para: string
  horas_min: number
  horas_max: number
  confianca: Confianca
  fonte: string
}

export interface Transito {
  _meta: unknown
  trechos: Trecho[]
}
