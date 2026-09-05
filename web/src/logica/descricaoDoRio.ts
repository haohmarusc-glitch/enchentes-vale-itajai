/**
 * As linhas "de onde vem a água" do cartão de cada rio na tela de início.
 *
 * Eram um texto fixo — e ficaram para trás quando a tela do Açu virou árvore:
 * a home continuou afirmando "Taió e Rio do Sul → Ibirama → Indaial → …", uma
 * fila em que Ibirama é elo do tronco (não é: fica no Rio Hercílio), Lontras e
 * Ascurra, que SÃO tronco, não existem, e Taió encabeça a seta como se o Açu
 * começasse lá (o Açu nasce em Rio do Sul). Achado em 05/09/2026 numa captura
 * de tela do celular. É o dado mais grave da home, porque ensina o caminho da
 * água a quem mora a jusante. Agora tudo sai do `estacoes.json`, a fonte de
 * verdade, e não pode divergir da tela do rio nem de docs/TOPOLOGIA-CANONICA.md.
 *
 * Rio ramificado (tem `_topologia`), três linhas, cada uma dizendo o que é:
 * - tronco: a única sequência que a tela pode afirmar, na ordem em que a água desce;
 * - cabeceiras: as paralelas, com o rio de cada uma, e onde se encontram;
 * - laterais: quem entra pelo lado, e por qual rio. NUNCA na seta do tronco.
 * - barragens: as de contenção que controlam o rio, com município e curso —
 *   vêm do `hidraulica.json`, e só entram as do `rio_id` deste rio.
 * Rio em fila (sem `_topologia`): só o tronco, as cidades por `ordem`.
 *
 * Id sem nome no cadastro aparece pelo próprio id, em vez de sumir calado: o
 * teste pega, e na tela um "rio-do-sul" é pior de ler mas não mente.
 */

export interface RioParaDescrever {
  cidades: { id: string; nome: string; ordem?: number | null; sub_bacia?: string | null }[]
  _topologia?: {
    tronco_sequencia?: string[]
    cabeceiras_paralelas?: string[]
    confluencia_cabeceiras?: { nasce?: string }
    afluentes_laterais?: { id: string; rio?: string }[]
  }
}

export interface BarragemParaDescrever {
  nome: string
  municipio_nome: string
  rio: string
}

export interface DescricaoDoRio {
  /** "Rio do Sul → Lontras → … → Itajaí". Num rio em fila, a fila inteira. */
  tronco: string
  /** "Taió (Itajaí do Oeste) e Ituporanga (Itajaí do Sul) se encontram em Rio do Sul", ou null. */
  cabeceiras: string | null
  /** "Ibirama, pelo Rio Hercílio (…); Timbó, pelo Rio Benedito; …", ou null. */
  laterais: string | null
  /** "Barragem Oeste em Taió, no Itajaí do Oeste; …", ou null quando o rio não tem nenhuma. */
  barragens: string | null
}

/** "Barragem Oeste em Taió, no Itajaí do Oeste; Barragem Sul em …" — ou null sem barragem. */
export function descreverBarragens(barragens: BarragemParaDescrever[]): string | null {
  if (!barragens.length) return null
  return barragens.map((b) => `${b.nome} em ${b.municipio_nome}, no ${b.rio}`).join('; ')
}

export const SETA = ' → '

/** "A", "A e B", "A, B e C" — a lista como se fala. */
export function listarComE(itens: string[]): string {
  if (itens.length <= 1) return itens.join('')
  return `${itens.slice(0, -1).join(', ')} e ${itens[itens.length - 1]}`
}

export function descricaoDoRio(
  rio: RioParaDescrever,
  barragens: BarragemParaDescrever[] = [],
): DescricaoDoRio {
  const linhaBarragens = descreverBarragens(barragens)
  const porId = new Map(rio.cidades.map((c) => [c.id, c]))
  const n = (id: string) => porId.get(id)?.nome ?? id
  const t = rio._topologia
  if (!t) {
    const fila = rio.cidades
      .filter((c) => typeof c.ordem === 'number')
      .sort((a, b) => (a.ordem as number) - (b.ordem as number))
      .map((c) => c.nome)
    return { tronco: fila.join(SETA), cabeceiras: null, laterais: null, barragens: linhaBarragens }
  }

  const troncoIds = t.tronco_sequencia ?? []
  const tronco = troncoIds.map(n).join(SETA)

  const cabIds = t.cabeceiras_paralelas ?? []
  let cabeceiras: string | null = null
  if (cabIds.length) {
    const nomes = cabIds.map((id) => {
      const sb = porId.get(id)?.sub_bacia
      return sb ? `${n(id)} (${sb})` : n(id)
    })
    const nasce = t.confluencia_cabeceiras?.nasce ?? troncoIds[0]
    const verbo = cabIds.length === 1 ? 'chega a' : 'se encontram em'
    cabeceiras = nasce ? `${listarComE(nomes)} ${verbo} ${n(nasce)}` : listarComE(nomes)
  }

  const lat = t.afluentes_laterais ?? []
  let laterais: string | null = null
  if (lat.length) {
    laterais = lat
      .map((a) => {
        const nome = n(a.id)
        if (!a.rio) return nome
        // "Rio dos Cedros, pelo Rio dos Cedros (…)" repetiria o nome: quando o
        // rio do afluente É a cidade, o campo `rio` já diz tudo.
        return a.rio.startsWith(nome) ? a.rio : `${nome}, pelo ${a.rio}`
      })
      .join('; ')
  }
  return { tronco, cabeceiras, laterais, barragens: linhaBarragens }
}
