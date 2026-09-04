import type { LonLat } from './mapaCanvas'

/**
 * Traçados que são O MESMO RIO do tronco, em outro canal — não afluentes.
 *
 * O CANAL RETIFICADO É O ITAJAÍ-MIRIM. Quem diz isso é o cadastro: as quatro
 * réguas dali têm `rio: "itajai-mirim"`, e os títulos separam apenas o canal
 * ("canal retificado", DC-03) do leito velho ("curso antigo", DC-05 e DC-06).
 * Pelo JICA, o canal leva 2/3 da vazão do Mirim — é o canal PRINCIPAL, não um
 * braço menor. `conferir_afluentes_chegam.py` sempre o tratou como tronco.
 *
 * Carregá-lo como afluente produzia uma contradição na tela: o curso antigo,
 * cuja geometria está dentro de `itajai-mirim.geojson`, saía pintado pela faixa
 * de Brusque e animado, enquanto o canal, ao lado, no mesmo trecho do rio, saía
 * cinza e parado. Mesma água, duas afirmações opostas — e a cinzenta era a do
 * canal que leva mais água.
 *
 * Nada disto mexe na régua DC-03: ela continua `alerta_automatico: false`, por
 * ser de estuário. O canal é pintado pela âncora de MONTANTE (Brusque), como o
 * curso antigo já era.
 */
export const CANAIS_DO_TRONCO: Record<string, readonly string[]> = {
  'itajai-mirim': ['mirim-canal-retificado'],
}

/** Todos os canais de tronco, achatados — para baixar e para não repetir na cena. */
export const CANAIS: string[] = Object.values(CANAIS_DO_TRONCO).flat()

export interface Baixado {
  rioId: string
  coords: LonLat[][] | null
}

/**
 * Funde cada canal na lista de coordenadas do seu tronco e remove-o da lista de
 * rios. É esta junção que faz a espinha do Mirim pintar os DOIS canais igual —
 * desenhá-lo como rio à parte deixa-o sem âncora a menos de `LIMITE_ANCORA_KM`
 * (Brusque fica a 25 km do canal) e portanto cinza e parado.
 *
 * Canal que não baixou simplesmente não entra: o tronco continua igual, nunca
 * some.
 */
export function juntarCanais(baixados: Baixado[]): { rioId: string; coords: LonLat[][] }[] {
  const porId = new Map<string, LonLat[][]>()
  for (const b of baixados) if (b.coords) porId.set(b.rioId, b.coords)

  const saida: { rioId: string; coords: LonLat[][] }[] = []
  for (const b of baixados) {
    if (!b.coords) continue
    if (CANAIS.includes(b.rioId)) continue
    const canais = (CANAIS_DO_TRONCO[b.rioId] ?? []).flatMap((c) => porId.get(c) ?? [])
    saida.push({ rioId: b.rioId, coords: canais.length ? [...b.coords, ...canais] : b.coords })
  }
  return saida
}
