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
  /**
   * Em que rio o curso da cidade deságua, com fonte, quando a cidade NÃO tem posição na árvore
   * (Trombudo → Itajaí do Oeste, OSM, decisão de 06/10/2026). `posicao_na_arvore` é sempre null.
   */
  rio_chega_a?: {
    rio: string
    ponto: [number, number]
    fonte: string
    metodo?: string
    incerteza: string
    posicao_na_arvore: null
    decisao?: string
  }
  /** Distância até a foz, em km, quando conhecida. */
  km_da_foz?: number
  codigo_ana: string | null
  verificado: boolean
  regua?: string
  /** Declaração da referência do histórico de picos, quando só parte dele está na
   *  régua da cidade (Brusque, decisão de 04/10/2026). Picos antes de `desde`
   *  aparecem à parte no gráfico, com a referência dita como não conferida. */
  historico_referencia?: HistoricoReferencia
  barragem?: string
  observacao?: string
  afluentes?: string[]
  /** [lat, lon] da estação de nível (Defesa Civil de SC) — posição da régua no
   *  rio, não o centro da cidade. O pino do mapa fica AQUI, sem encaixe no
   *  traçado (`pontoDoPino`). Exceções: Itajaí (foz, sem estação estadual) e
   *  Vidal Ramos (Asthon, = DCSC). */
  coordenadas?: [number, number]
  /**
   * `true` quando a coordenada É a régua, com a fonte em `coordenadas_fonte` (Blumenau desde 06/10/2026:
   * Ponte Adolfo Konder, confirmada pela Prefeitura). `false` quando o cadastro sabe que não é: o pino vai
   * para o rio e sai "aproximado". Ausente: não se sabe.
   */
  coordenadas_sao_da_regua?: boolean
  /** De onde veio a coordenada da régua, quando não é a ficha da estação estadual. */
  coordenadas_fonte?: string
  /**
   * "não confirmada": o pino fica na coordenada do cadastro, mas nenhuma fonte situa a régua ali (Timbó, decisão
   * de 06/10/2026). Não move o pino nem vincula estação; o painel diz isso. O porquê vai em `coordenadas_status_nota`.
   */
  coordenadas_status?: 'não confirmada'
  coordenadas_status_nota?: string
  /**
   * A estação estadual perto da cidade e se ela é a régua das cotas (decisão de 06/10/2026). "não confirmada"
   * até existir documento, código comum ou comparação de referência/zero da régua.
   */
  equivalencia_estadual?: {
    codigo: string
    nome_na_dcsc?: string
    distancia_km?: number
    status: 'não confirmada' | 'confirmada'
    fonte?: string
  }
  /** Cotas de referência na régua LOCAL. Cada cidade tem seu próprio zero. */
  cotas_m: Record<string, number>
  /**
   * Ressalva sobre as cotas ESCRITA PARA QUEM LÊ A TELA, não para quem lê o
   * JSON. Existe onde a cor desta tela pode divergir do que a Defesa Civil do
   * município declara — e a pessoa precisa saber disso antes de decidir.
   *
   * Hoje em três cidades, por dois motivos diferentes:
   *
   * - **Brusque** opera por BACIA: a Defesa Civil olha Vidal Ramos → Botuverá
   *   → Brusque e a tendência, e pode declarar atenção ANTES de o número daqui
   *   subir. A régua sozinha não é o critério dela.
   * - **Ituporanga** e **Vidal Ramos** têm escala publicada por OUTRA régua
   *   (a 9,6 km e a 6,8 km), com zero próprio. A tela não pinta cor, e sem
   *   dizer por quê a ausência de cor parece ausência de rio.
   *
   * Os campos `cotas_ressalva`, `cotas_pendencia` e `cotas_m_por_que_vazio` do
   * JSON continuam existindo e são o registro INTERNO, longo e datado. Este é
   * o que a tela mostra. Nunca despejar aqueles: são escritos para o projeto,
   * citam campos e arquivos, e em cheia ninguém lê parágrafo de auditoria.
   */
  cotas_aviso_publico?: string
  /**
   * O nome que a FONTE dá a cada faixa, quando difere do nosso. As chaves de
   * `cotas_m` são quatro degraus fixos; a Defesa Civil de Blumenau chama o topo
   * de "Alerta Máximo", a de Ilhota chama o `alerta` de "Prontidão", a de Taió
   * chama o `monitoramento` de "Observação". A tela escreve o nome da fonte,
   * porque é o nome que a pessoa vai ouvir no rádio e ler no site oficial —
   * chamar de "Emergência" o que a COMPDEC chama de "Alerta Máximo" faz a tela
   * parecer outra escala. Chaves que começam com `_` são anotação, não nome.
   */
  cotas_nomes_na_fonte?: Record<string, string>
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
 * A árvore de um rio ramificado (Açu e Mirim). Diz qual é a ÚNICA sequência
 * que a tela pode afirmar (o tronco), quais cidades são cabeceiras paralelas e
 * quais são afluentes laterais — que entram no tronco, não são elos da fila.
 */
/** Ver `Cidade.historico_referencia`. */
export interface HistoricoReferencia {
  /** O título do gráfico, que declara a referência ("Histórico na régua da Ponte Estaiada"). */
  rotulo: string
  /** Data ISO a partir da qual os picos estão nessa régua (inclusiva). */
  desde: string
  /** De onde vêm os picos desde `desde`. */
  fonte_desde: string
  /** De onde vêm os anteriores, e o que se sabe da referência deles. */
  antes: string
  nota?: string
}

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
  /** Presente só em rio ramificado (hoje os dois). Ausente = rio em fila. */
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
  /**
   * `false` quando a medição mostrou que a régua NÃO sente a maré (DC-02,
   * DC-05, DC-07, DC-08, em 03/10/2026). O aviso automático pode continuar
   * desligado por outro motivo, mas a tela não diz "maré". Ausente = sente.
   */
  sente_mare?: boolean
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

/**
 * Estado de um link do rodapé, conferido no navegador.
 *
 * As chaves que começam com `_` são documentação do bloco, não fontes — por
 * isso o tipo aceita `string` além do registro.
 */
export interface EstadoDeFonte {
  estado: 'ok' | 'fora_do_ar' | 'exige_cadastro'
  observado: string
  por_que_importa?: string
  o_que_resolve?: string
}

export type EstadoDasFontes = Record<string, EstadoDeFonte | string | unknown>

export interface Estacoes {
  _meta: unknown
  rios: Record<string, Rio>
  afluentes_monitorados?: AfluenteMonitorado[]
  estacoes_tempo_real?: EstacaoTempoReal[]
  fontes_gerais: Record<string, string>
  fontes_gerais_estado?: EstadoDasFontes
}

/** Outro valor publicado para o MESMO pico, por outra fonte. */
export interface Divergencia {
  pico_m: number
  fonte: string
  /**
   * Só em divergência de registro convertido (Blumenau, 03/10/2026): em que
   * referência ESTE valor foi publicado. `null` = a fonte não diz. O valor fica
   * como publicado — não é convertido.
   */
  referencia_publicada?: string | null
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
   * da tabela de Cordero & Medeiros: 20 cm acima da régua ANTIGA e 20 cm abaixo
   * da régua de hoje (FURB, 02/10/2026). `null` = a fonte não declara — e para
   * Blumenau isso importa, porque a diferença entra direto na comparação com as
   * cotas, que estão na régua de hoje.
   */
  referencia?: string | null
  /**
   * Só em registro CONVERTIDO para a régua de hoje (Blumenau, 03/10/2026): o
   * valor como a fonte publicou. `pico_m` já é a régua de hoje.
   */
  pico_publicado_m?: number
  /** Em que referência `pico_publicado_m` foi publicado (`IBGE (régua + 0,20 m)`, `régua antiga`, `régua de hoje`). */
  referencia_publicada?: string
  /** O que foi somado, quando, por decisão de quem e com que fonte. */
  conversao?: string
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

/**
 * Trecho EM ESTUDO (decisão de 04/10/2026): tem medição e evidência, mas não tem
 * faixa operacional — nunca vira tempo de descida na tela. A tela diz "dados
 * insuficientes" no lugar.
 */
export interface TrechoExperimental {
  rio: string
  de: string
  para: string
  status: 'experimental'
  eventos_pareados_com_hora: number
  minimo_eventos_pareados: number
}

export interface Transito {
  _meta: unknown
  trechos: Trecho[]
  trechos_experimentais?: TrechoExperimental[]
}

/** Uma preamar ou baixa-mar da tábua oficial. `quando` é horário local, sem fuso. */
export interface EntradaMare {
  quando: string
  altura_m?: number
}

/**
 * Metadados da tábua — a tela usa `fonte_curta` (e `aviso_interino`, quando
 * presente) para creditar a fonte de verdade em vez de cravar "Defesa Civil"
 * como se fosse sempre ela. Os demais campos são para quem lê o JSON/audita,
 * não para a UI.
 */
export interface MetaTabuaMare {
  fonte_curta?: string
  /** Link da fonte, só quando ela tem uma página pública (a DC tem; a
   *  planilha da UNIVALI não). */
  fonte_url?: string
  /** Presente só na tábua INTERINA (não veio do endpoint oficial da Defesa
   *  Civil) — a tela mostra isto como aviso, não some em silêncio. */
  aviso_interino?: string
}

export interface TabuaMare {
  _meta: MetaTabuaMare
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
   * `régua` para entrar na tela. `null` = a fonte não declara.
   *
   * Cotas de rua são levantadas contra a régua da cidade, e o nível ao vivo da
   * Defesa Civil também é régua — por isso a busca "minha rua" e o simulador
   * comparam maçã com maçã. Um valor diferente aqui significaria comparar uma
   * cota de rua com um nível 20 cm deslocado, e o carregador descarta.
   *
   * CORRIGIDO em 06/09/2026, e o erro estava AQUI, no tipo: ele dizia "sempre
   * régua, QUANDO PRESENTE", e o carregador implementou exatamente isso —
   * ausência do campo virava permissão. Só que ausência nunca provou nada; em
   * todo o resto do projeto ela significa "ninguém conferiu ainda". Eram 39
   * cotas entrando sem rótulo. O tipo também proibia `null`, que é justamente a
   * resposta que o CLAUDE.md manda usar quando a fonte não declara — ou seja,
   * não dava para escrever a resposta certa.
   */
  referencia?: string | null
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
  /** Coordenada do PONTO, quando a fonte publica (Gaspar, Brusque). Nunca geocodificada aqui. */
  lat?: number
  lon?: number
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
