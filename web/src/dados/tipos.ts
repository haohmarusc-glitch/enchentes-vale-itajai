/** Tipos dos JSONs de `data/`, que são a fonte de verdade do projeto. */

export type Confianca = 'alta' | 'media' | 'baixa'

export type RioId = 'itajai-acu' | 'itajai-mirim'

export interface Cidade {
  id: string
  nome: string
  ordem: number
  /** Sub-bacia a que a cidade pertence (Itajaí do Oeste, Benedito, …). */
  sub_bacia?: string
  /** Distância até a foz, em km, quando conhecida. */
  km_da_foz?: number
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

/**
 * Cidade com régua própria que NÃO está na sequência do eixo — o pico dela vem
 * da chuva na sub-bacia, não da mesma cheia que desce o rio principal.
 */
export interface AfluenteMonitorado {
  id: string
  nome: string
  rio: string
  desagua_em: string
  observacao: string
  codigo_ana: string | null
  verificado: boolean
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
  afluentes_monitorados?: AfluenteMonitorado[]
  fontes_gerais: Record<string, string>
}

/** Outro valor publicado para o MESMO pico, por outra fonte. */
export interface Divergencia {
  pico_m: number
  fonte: string
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
  /** Ressalva sobre o registro, exibida junto do número. */
  nota?: string
  /**
   * Outros valores publicados para o mesmo pico. `pico_m` é o adotado; estes
   * ficam guardados para que ninguém "corrija" o arquivo de volta sem saber
   * que a divergência já foi analisada.
   */
  divergencias?: Divergencia[]
  /**
   * Em que referência o nível foi medido.
   *
   * Ausente = régua local. `IBGE (régua + 0,20 m)` = a série longa de Blumenau,
   * que vem da tabela de Cordero & Medeiros e está 20 cm acima da régua. `null`
   * = a fonte não declara — e para Blumenau isso importa, porque as duas
   * referências circulam e a diferença entra direto na comparação com as cotas,
   * que estão na régua.
   */
  referencia?: string | null
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

/** Uma preamar ou baixa-mar da tábua oficial. `quando` é horário local, sem fuso. */
export interface EntradaMare {
  quando: string
  altura_m?: number
}

export interface TabuaMare {
  _meta: unknown
  porto: string
  /** ISO UTC da coleta, ou null quando a tábua ainda não foi coletada. */
  coletado_em: string | null
  preamares: EntradaMare[]
  baixamares: EntradaMare[]
}

/**
 * Nível do rio, na régua da PRÓPRIA cidade, a partir do qual uma rua alaga.
 *
 * `cota_m` nulo é resposta legítima: a fonte cita a rua e não publica o número.
 * Nesse caso `nota` diz por quê. Nulo NÃO é zero, e não foi estimado.
 */
export interface CotaRua {
  cidade: string
  /**
   * Sempre `régua`, quando presente.
   *
   * Cotas de rua são levantadas contra a régua da cidade, e o nível ao vivo da
   * Defesa Civil também é régua — por isso a busca "minha rua" e o simulador
   * comparam maçã com maçã. Um valor diferente aqui significaria comparar uma
   * cota de rua com um nível 20 cm deslocado, e o carregador descarta.
   */
  referencia?: string
  rio: string
  rua: string
  bairro: string | null
  ponto: string | null
  cota_m: number | null
  fonte: string
  data_fonte: string
  confianca: Confianca
  nota?: string
}

export interface CotasRuas {
  _meta: { descricao: string; aviso: string[]; campos: Record<string, string> }
  cotas: CotaRua[]
}
