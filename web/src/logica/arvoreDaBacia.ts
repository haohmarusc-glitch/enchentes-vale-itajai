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
  municipio_nome?: string
  rio?: string
  rio_id?: string
  a_montante_de?: string
  ano?: number
  armazenamento_Mm3?: number
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
  comportas: number | null
  semComporta: number | null
  chuvaEquivalenteMm: number | null
}

export interface CabeceiraNaArvore {
  cidade: string
  /** O curso em que ela corre — ainda não é o Açu. */
  rio: string | null
  barragem: BarragemNaArvore | null
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
}

export interface RioParaArvore {
  cidades: { id: string; nome: string; sub_bacia?: string | null }[]
  _topologia?: {
    tronco_sequencia?: string[]
    cabeceiras_paralelas?: string[]
    confluencia_cabeceiras?: { nasce?: string; lat?: number; lon?: number }
    afluentes_laterais?: { id: string; rio?: string; entra_perto_de?: string }[]
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
  if (!b.nome || !b.municipio_nome || !b.rio || !b.a_montante_de) return null
  return {
    nome: b.nome,
    municipio: b.municipio_nome,
    rio: b.rio,
    acimaDe: nomeDaCidade(b.a_montante_de),
    ano: numero(b.ano),
    volumeMm3: numero(b.armazenamento_Mm3),
    comportas: numero(b.condutos_com_comporta),
    semComporta: numero(b.condutos_sem_comporta),
    chuvaEquivalenteMm: numero(b.chuva_equivalente_mm),
  }
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

  // Barragens deste rio, indexadas pela cidade logo abaixo da parede.
  const porCidade = new Map<string, BarragemNaArvore>()
  const usadas = new Set<string>()
  for (const [chave, cru] of Object.entries(barragensBrutas)) {
    if (chave.startsWith('_') || typeof cru !== 'object' || cru === null) continue
    const b = cru as BarragemBruta
    if (b.rio_id !== rioId) continue
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

  return {
    cabeceiras,
    nasce,
    tronco: (t.tronco_sequencia ?? []).map(nome),
    laterais,
    barragensSoltas,
  }
}
