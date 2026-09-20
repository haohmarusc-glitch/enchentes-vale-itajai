/**
 * A árvore da bacia do Açu, montada do cadastro: o que chega em cada barragem,
 * as barragens de contenção, e só então o tronco.
 *
 * POR QUE ELA EXISTE: a home afirmava uma fila ("Taió e Rio do Sul → Ibirama →
 * Indaial → …") que ensinava o caminho errado da água — Ibirama como elo do
 * tronco (fica no Hercílio, atrás da Barragem Norte) e Taió como começo do Açu
 * (o Açu nasce na confluência, em Rio do Sul). A tela do rio já era árvore; a
 * home e o Monitor não. Aqui a árvore vem do `estacoes.json._topologia` e do
 * `hidraulica.json.barragens`, então nenhuma tela pode divergir da outra.
 *
 * DUAS CLASSES DE BARRAGEM, nunca somadas: as três de CONTENÇÃO da bacia
 * (Oeste, Sul, Norte), que existem para amortecer a cheia do Açu e têm
 * operação publicada, e as LOCAIS (Pinhal e Rio Bonito, no município de Rio dos
 * Cedros), que o PLANCON de lá cita e que não fazem esse papel. Listá-las lado
 * a lado diria que a bacia tem cinco barragens de contenção. Tem três. Por isso
 * a local entra em campo próprio, sem ficha, e a tela diz o que ela não é.
 *
 * A REGRA QUE ELA CARREGA: a barragem NÃO é o rio da cidade. O nível do
 * reservatório (cota de lago, centenas de metros acima do mar) e a régua urbana
 * logo abaixo da parede são escalas diferentes — em Taió, 17 m de reservatório
 * convivem com 5 m na régua do centro. Por isso a árvore guarda a barragem e a
 * cidade em campos SEPARADOS, e nenhum número de barragem entra no campo da
 * cidade. As três são manivelas distintas: Oeste e Sul mudam o hidrograma que
 * NASCE em Rio do Sul; a Norte muda o que entra no MEIO do tronco, e é o que
 * Blumenau vê.
 */

export interface BarragemBruta {
  nome?: string
  tipo?: string
  localidade?: string
  no_municipio?: string
  municipio_nome?: string
  rio?: string
  rio_id?: string
  a_montante_de?: string
  ano?: number
  armazenamento_Mm3?: number
  capacidade_maxima_hm3_api_estadual?: number
  area_drenagem_km2_jica?: number
  area_drenagem_km2_api_estadual?: number
  condutos_com_comporta?: number
  condutos_sem_comporta?: number
  chuva_equivalente_mm?: number
}

export interface BarragemNaArvore {
  nome: string
  municipio: string
  rio: string
  /** A cidade COM RÉGUA logo abaixo da parede. A régua dela não é o lago. */
  acimaDe: string
  ano: number | null
  volumeMm3: number | null
  volumeEstadualHm3: number | null
  comportas: number | null
  semComporta: number | null
  chuvaEquivalenteMm: number | null
  /**
   * Área de drenagem. Duas delimitações COEXISTEM na Oeste e na Sul (JICA Vol.
   * II × API estadual) e o cadastro proíbe fundi-las ou escolher em silêncio —
   * por isso são dois campos, e a tela mostra as duas quando divergem.
   */
  areaJicaKm2: number | null
  areaEstadualKm2: number | null
}

/**
 * Barragem local: onde fica, e nada mais. Sem ficha e sem posição em relação à
 * régua — a fonte municipal não dá nenhuma das duas, e inventá-las seria pior
 * que omitir.
 */
export interface BarragemLocal {
  nome: string
  localidade: string | null
  municipio: string
  rio: string
}

export interface CabeceiraNaArvore {
  cidade: string
  /** O curso em que ela corre — ainda não é o Açu. */
  rio: string | null
  barragem: BarragemNaArvore | null
}

/**
 * Rio que entra no tronco mas NÃO tem régua no cadastro — o Benedito e o Luís
 * Alves. Sem régua eles somem da árvore montada por cidades, e quem lê o mapa
 * conclui que entre Ascurra e Indaial nada entra. Entra: o Benedito, com toda
 * a chuva da sub-bacia dele.
 */
export interface AfluenteSemRegua {
  nome: string
  entraPertoDe: string
  /** O que a fonte diz sobre o ponto — inclusive quando ela diz "a confirmar". */
  pontoExato: string | null
}

export interface LateralNaArvore {
  cidade: string
  rio: string
  entraPertoDe: string
  barragem: BarragemNaArvore | null
}

export interface ArvoreDaBacia {
  cabeceiras: CabeceiraNaArvore[]
  /** Onde as cabeceiras se encontram e o rio nasce. */
  nasce: { cidade: string; lat: number | null; lon: number | null } | null
  tronco: string[]
  laterais: LateralNaArvore[]
  /** Barragens do rio que não puderam ser penduradas em nenhuma cidade. */
  barragensSoltas: BarragemNaArvore[]
  /** Barragens LOCAIS, por cidade. Não são de contenção da bacia. */
  locaisPorCidade: { cidade: string; barragens: BarragemLocal[] }[]
  /** Rios que entram no tronco sem régua própria (Benedito, Luís Alves). */
  afluentesSemRegua: AfluenteSemRegua[]
}

export interface RioParaArvore {
  cidades: { id: string; nome: string; sub_bacia?: string | null }[]
  _topologia?: {
    tronco_sequencia?: string[]
    cabeceiras_paralelas?: string[]
    confluencia_cabeceiras?: { nasce?: string; lat?: number; lon?: number }
    afluentes_laterais?: { id: string; rio?: string; entra_perto_de?: string }[]
    afluentes_rios?: { nome: string; entra_perto_de?: string; ponto_exato?: string }[]
  }
}

function numero(v: unknown): number | null {
  return typeof v === 'number' && Number.isFinite(v) ? v : null
}

/** Converte a entrada crua do `hidraulica.json`, ou `null` se faltar o mínimo. */
export function barragemDaBacia(
  b: BarragemBruta,
  nomeDaCidade: (id: string) => string,
): BarragemNaArvore | null {
  // Só a de CONTENÇÃO vira ficha na árvore. A local não tem `a_montante_de` de
  // propósito, então cairia aqui de qualquer jeito; o `tipo` diz por quê.
  if (b.tipo !== 'contencao_estadual') return null
  if (!b.nome || !b.municipio_nome || !b.rio || !b.a_montante_de) return null
  return {
    nome: b.nome,
    municipio: b.municipio_nome,
    rio: b.rio,
    acimaDe: nomeDaCidade(b.a_montante_de),
    ano: numero(b.ano),
    volumeMm3: numero(b.armazenamento_Mm3),
    volumeEstadualHm3: numero(b.capacidade_maxima_hm3_api_estadual),
    comportas: numero(b.condutos_com_comporta),
    semComporta: numero(b.condutos_sem_comporta),
    chuvaEquivalenteMm: numero(b.chuva_equivalente_mm),
    areaJicaKm2: numero(b.area_drenagem_km2_jica),
    areaEstadualKm2: numero(b.area_drenagem_km2_api_estadual),
  }
}

/**
 * As barragens de CONTENÇÃO de um rio, do bloco cru do `hidraulica.json`.
 *
 * Mora aqui, e não no `dados/carregar`, porque o `carregar` importa pelo alias
 * `@dados` do Vite, que o executor de testes não resolve — e um filtro que o
 * teste não alcança é um filtro que ninguém pode falsificar. Foi o que uma
 * sabotagem mostrou em 05/09/2026: desligar o filtro no `carregar` não quebrou
 * teste nenhum, porque o teste tinha a sua própria cópia dele.
 */
export function barragensDeContencao(
  barragensBrutas: Record<string, unknown>,
  rioId: string,
): { nome: string; municipio_nome: string; rio: string }[] {
  const saida: { nome: string; municipio_nome: string; rio: string }[] = []
  for (const [chave, cru] of Object.entries(barragensBrutas)) {
    if (chave.startsWith('_') || typeof cru !== 'object' || cru === null) continue
    const b = cru as BarragemBruta
    if (b.tipo !== 'contencao_estadual' || b.rio_id !== rioId) continue
    if (!b.nome || !b.municipio_nome || !b.rio) continue
    saida.push({ nome: b.nome, municipio_nome: b.municipio_nome, rio: b.rio })
  }
  return saida
}

/**
 * A área de drenagem em texto.
 *
 * Quando as duas delimitações DIVERGEM, mostra as duas: o `hidraulica.json`
 * proíbe fundi-las ou escolher em silêncio, e a divergência é grande (Oeste:
 * 1.042 km² no JICA Vol. II contra 851 na API estadual, que o próprio JICA
 * Vol. III-A confirma). Uma média inventaria um número que fonte nenhuma
 * publica.
 *
 * Mora aqui, e não no componente, pela mesma razão do `barragensDeContencao`:
 * no `.tsx` nenhum teste a alcança, e uma sabotagem que fundia as duas numa
 * média não quebrava nada.
 */
export function areaEmTexto(b: {
  areaJicaKm2: number | null
  areaEstadualKm2: number | null
}): string | null {
  const km = (v: number) => `${v.toLocaleString('pt-BR')} km²`
  if (b.areaJicaKm2 != null && b.areaEstadualKm2 != null) {
    return b.areaJicaKm2 === b.areaEstadualKm2
      ? `drena ${km(b.areaJicaKm2)}`
      : `drena ${km(b.areaEstadualKm2)} (rede estadual) ou ${km(b.areaJicaKm2)} (JICA Vol. II) — delimitações diferentes`
  }
  const so = b.areaEstadualKm2 ?? b.areaJicaKm2
  return so != null ? `drena ${km(so)}` : null
}

/**
 * O volume do reservatório em texto — as DUAS fontes quando divergem.
 *
 * Mesmo caso de `areaEmTexto`, e apontado pela auditoria externa de
 * 19/09/2026: a ficha mostrava só os 83 hm³ do JICA 2011, enquanto a API
 * estadual publica 99,96 (+20,4%). Não se sabe se medem a mesma grandeza —
 * volume ÚTIL de amortecimento contra capacidade TOTAL é hipótese plausível e
 * não verificada —, então trocar um pelo outro seria escolher em silêncio.
 * `hidraulica.json._capacidade_divergente` guarda o porquê.
 *
 * Mora aqui, e não no `.tsx`, pela mesma razão: no componente nenhum teste
 * alcança, e uma fusão silenciosa não quebraria nada.
 */
export function volumeEmTexto(b: {
  volumeMm3: number | null
  volumeEstadualHm3: number | null
}): string | null {
  const hm = (v: number) => `${v.toLocaleString('pt-BR')} hm³`
  if (b.volumeMm3 != null && b.volumeEstadualHm3 != null) {
    return b.volumeMm3 === b.volumeEstadualHm3
      ? hm(b.volumeMm3)
      : `${hm(b.volumeEstadualHm3)} (rede estadual) ou ${hm(b.volumeMm3)} (JICA 2011) — medidas diferentes`
  }
  const so = b.volumeEstadualHm3 ?? b.volumeMm3
  return so != null ? hm(so) : null
}

/**
 * A chuva equivalente, dita como EQUIVALÊNCIA e não como limiar.
 *
 * A ficha dizia "enche com ~80 mm de chuva sobre a bacia dela". O número é o do
 * JICA e está certo; a frase é que transformava uma divisão (armazenamento ÷
 * área de drenagem) em previsão de enchimento. Chuva não vira armazenamento na
 * proporção de 1 para 1: o coeficiente de escoamento, o quanto o reservatório
 * já tinha e a operação das comportas ficam todos de fora da conta.
 *
 * O que a divisão SERVE para dizer continua valendo, e é o que a tela passa a
 * dizer: comparar as três entre si.
 */
export function chuvaEquivalenteEmTexto(b: { chuvaEquivalenteMm: number | null }): string | null {
  if (b.chuvaEquivalenteMm == null) return null
  // A NEGAÇÃO É EXPLÍCITA, e a atribuição vai junto. Tirar o "enche com" removeu
  // a afirmação falsa; o auditor pediu mais — que a frase DIGA que não é limiar,
  // porque "equivale a 80 mm de chuva" ainda se lê como "80 mm e ela enche" por
  // quem passa o olho. A redação abaixo segue a que ele sugeriu, encurtada para
  // caber na ficha.
  return (
    `armazenamento equivalente a ~${b.chuvaEquivalenteMm} mm de chuva sobre a área considerada no JICA 2011, volume II` +
    ' — não é o tanto de chuva que a enche'
  )
}

export function arvoreDaBacia(
  rioId: string,
  rio: RioParaArvore,
  barragensBrutas: Record<string, unknown>,
): ArvoreDaBacia | null {
  const t = rio._topologia
  if (!t) return null
  const porId = new Map(rio.cidades.map((c) => [c.id, c]))
  const nome = (id: string) => porId.get(id)?.nome ?? id

  // Barragens deste rio: as de contenção pela cidade logo abaixo da parede; as
  // locais pelo município em que ficam. Duas listas, nunca uma.
  const porCidade = new Map<string, BarragemNaArvore>()
  const locais = new Map<string, BarragemLocal[]>()
  const usadas = new Set<string>()
  for (const [chave, cru] of Object.entries(barragensBrutas)) {
    if (chave.startsWith('_') || typeof cru !== 'object' || cru === null) continue
    const b = cru as BarragemBruta
    if (b.rio_id !== rioId) continue
    if (b.tipo === 'local') {
      if (!b.nome || !b.municipio_nome || !b.rio || !b.no_municipio) continue
      const lista = locais.get(b.no_municipio) ?? []
      lista.push({
        nome: b.nome,
        localidade: b.localidade ?? null,
        municipio: b.municipio_nome,
        rio: b.rio,
      })
      locais.set(b.no_municipio, lista)
      continue
    }
    const pronta = barragemDaBacia(b, nome)
    if (pronta && b.a_montante_de) porCidade.set(b.a_montante_de, pronta)
  }

  const cabeceiras: CabeceiraNaArvore[] = (t.cabeceiras_paralelas ?? []).map((id) => {
    const b = porCidade.get(id) ?? null
    if (b) usadas.add(id)
    return { cidade: nome(id), rio: porId.get(id)?.sub_bacia ?? null, barragem: b }
  })

  const conf = t.confluencia_cabeceiras
  const idNasce = conf?.nasce ?? (t.tronco_sequencia ?? [])[0]
  const nasce = idNasce
    ? { cidade: nome(idNasce), lat: numero(conf?.lat), lon: numero(conf?.lon) }
    : null

  const laterais: LateralNaArvore[] = (t.afluentes_laterais ?? []).map((a) => {
    const b = porCidade.get(a.id) ?? null
    if (b) usadas.add(a.id)
    return {
      cidade: nome(a.id),
      rio: a.rio ?? '',
      entraPertoDe: a.entra_perto_de ? nome(a.entra_perto_de) : '',
      barragem: b,
    }
  })

  // Barragem cuja cidade não é cabeceira nem lateral não some calada.
  const barragensSoltas = [...porCidade.entries()]
    .filter(([id]) => !usadas.has(id))
    .map(([, b]) => b)

  const afluentesSemRegua: AfluenteSemRegua[] = (t.afluentes_rios ?? []).map((r) => ({
    nome: r.nome,
    entraPertoDe: r.entra_perto_de ? nome(r.entra_perto_de) : '',
    pontoExato: r.ponto_exato ?? null,
  }))

  const locaisPorCidade = [...locais.entries()].map(([id, barragens]) => ({
    cidade: nome(id),
    barragens,
  }))

  return {
    cabeceiras,
    nasce,
    tronco: (t.tronco_sequencia ?? []).map(nome),
    laterais,
    barragensSoltas,
    locaisPorCidade,
    afluentesSemRegua,
  }
}
