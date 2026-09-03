/** Tipos dos JSONs de `data/`, que são a fonte de verdade do projeto. */

export type Confianca = 'alta' | 'media' | 'baixa'

export type RioId = 'itajai-acu' | 'itajai-mirim'

export interface Cidade {
  id: string
  nome: string
  /**
   * Sequência montante → jusante, SÓ em rio não ramificado (o Mirim). Em rio
   * ramificado (o Açu, uma árvore) é `null`: usar ordem global afirmaria uma
   * fila que não existe. Aí a posição vem de `ramo` + `ordem_no_ramo`, e a única
   * sequência afirmável é o tronco (`Rio._topologia.tronco_sequencia`).
   */
  ordem: number | null
  /** Braço da árvore: `tronco_acu`, `itajai_do_oeste`, `itajai_do_norte`… Só se
   *  compara posição DENTRO do mesmo ramo. Ausente em rio não ramificado. */
  ramo?: string
  /** Posição montante → jusante dentro do ramo (1 = mais a montante). */
  ordem_no_ramo?: number
  /** Estação da rede estadual (Defesa Civil de SC), `DCSC-NNNNN`. */
  codigo_dcsc?: string | null
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
  /** [lat, lon] da estação de nível (Defesa Civil de SC) — posição da régua no
   *  rio, não o centro da cidade; o mapa encaixa no traçado. Exceções: Itajaí
   *  (foz, sem estação estadual) e Vidal Ramos (Asthon, = DCSC). */
  coordenadas?: [number, number]
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

/**
 * A árvore de um rio ramificado (hoje só o Açu). Diz qual é a ÚNICA sequência
 * que a tela pode afirmar (o tronco), quais cidades são cabeceiras paralelas e
 * quais são afluentes laterais — que entram no tronco, não são elos da fila.
 */
export interface Topologia {
  tipo: 'arvore'
  /** A sequência montante → jusante que a água realmente segue. */
  tronco_sequencia: string[]
  /** Cabeceiras que correm em paralelo e se juntam no início do tronco. */
  cabeceiras_paralelas: string[]
  /** Afluentes que entram no tronco de lado — não são elos da sequência. */
  afluentes_laterais: { id: string; entra_perto_de: string; rio: string }[]
  /**
   * Rios tributários que entram no tronco mas NÃO têm régua própria no cadastro
   * (Benedito, Luís Alves). `ponto_exato` guarda a confirmação pendente de onde
   * exatamente entram — antes ou depois da régua da cidade vizinha.
   */
  afluentes_rios?: { nome: string; entra_perto_de: string; ponto_exato: string }[]
  /** Ids que saíram do eixo por não serem régua de rio (ex.: estação de altitude). */
  nao_e_regua_de_rio?: { id: string; motivo: string }[]
  nota?: string
  fonte?: string
}

export interface Rio {
  nome: string
  foz: string
  cidades: Cidade[]
  /** Presente só em rio ramificado. Ausente = rio em fila (Mirim). */
  _topologia?: Topologia
}

/**
 * Régua ou pluviômetro publicado em tempo real. Nem toda estação tem cota
 * cadastrada, e nem toda cota vale como gatilho de aviso: as do estuário de
 * Itajaí oscilam com a maré, e por isso trazem `alerta_automatico: false` com o
 * motivo escrito por extenso.
 */
export interface EstacaoTempoReal {
  /** Código da fonte (`DC-01`). Ausente nas estações que a fonte não numera. */
  codigo?: string
  titulo: string
  /** Nome da régua no Plano de Contingência, quando difere do título. */
  nome_no_plano?: string
  rio: string | null
  cidade: string | null
  /** `pluviometro` mede chuva, não nível. */
  tipo?: string
  cotas_m: Record<string, number>
  verificado: boolean
  referencia?: string | null
  fonte_cotas?: string
  alerta_automatico?: boolean
  motivo_sem_alerta?: string
  /** [lat, lon] da régua, quando a fonte publica — hoje as 11 réguas DC de
   *  Itajaí (marcadores da página Mapa.php da Defesa Civil). */
  lat?: number
  lon?: number
  /**
   * Posição na descida do curso (1 = mais a montante, cresce até a foz),
   * calculada pela distância à foz em `scripts/ordenar_estacoes_itajai.py`.
   * Duas réguas co-locadas (DC-04 × DC-06, braços paralelos) compartilham o
   * mesmo valor e trazem `ordem_nota` dizendo que a ordem entre elas é
   * indefinível. Ausente quando não há coordenada.
   */
  ordem_descida?: number
  ordem_nota?: string
}

export interface Estacoes {
  _meta: unknown
  rios: Record<string, Rio>
  afluentes_monitorados?: AfluenteMonitorado[]
  estacoes_tempo_real?: EstacaoTempoReal[]
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
  /**
   * Nível em que a rua alaga INTEIRA, quando a fonte publica os dois números.
   * Rio do Sul publica mínima e máxima por logradouro; as demais, só uma cota.
   * Nunca é usado no lugar de `cota_m`: quem decide sair de casa decide pela
   * mínima, que é quando a água chega.
   */
  cota_max_m?: number
  /**
   * `false` quando o número não serve para mover aviso — hoje, as cotas que a
   * fonte publica abaixo do nível normal do rio. Mesmo conceito do
   * `alerta_automatico: false` das réguas de estuário: o valor aparece na
   * tela, com a ressalva, e não dispara nada.
   */
  usar_para_aviso?: boolean
  /**
   * Abrigo que a Defesa Civil indica para aquele ponto, quando a fonte informa
   * — hoje só Blumenau, do PDF oficial de 2014.
   *
   * É a outra metade da mesma decisão: a cota diz que é hora de sair, o abrigo
   * diz para onde. Uma rua comprida pode ter abrigos diferentes em pontos
   * diferentes, por isso o campo é do REGISTRO e não da rua.
   */
  abrigo?: string | null
  /** O código do abrigo na fonte (ex.: `E9`). */
  abrigo_codigo?: string | null
  fonte: string
  data_fonte: string
  confianca: Confianca
  nota?: string
}

export interface CotasRuas {
  _meta: { descricao: string; aviso: string[]; campos: Record<string, string> }
  cotas: CotaRua[]
}

/**
 * Abrigo oficial da Defesa Civil de Itajaí, com coordenada.
 *
 * É CADASTRO, não estado atual: `situacao` e `lotacao` existem na fonte e foram
 * DELIBERADAMENTE deixados de fora do arquivo, para nunca serem lidos como
 * "aberto agora" numa tela de enchente. Quem ativa abrigo e manda evacuar é a
 * Defesa Civil. `nome`/`endereco` podem ser nulos num registro sem dado na fonte.
 */
export interface Abrigo {
  nome: string | null
  endereco: string | null
  zona_defesa_civil: string | null
  capacidade: number | null
  /** Pode vir nulo: a fonte tem 1 registro sem geometria. Quem consome filtra
   *  por `Number.isFinite` antes de usar (ver logica/abrigos.ts). */
  lat: number | null
  lon: number | null
}

export interface AbrigosItajai {
  _meta: { AVISO_EXIBICAO: string; total: number } & Record<string, unknown>
  abrigos: Abrigo[]
}
