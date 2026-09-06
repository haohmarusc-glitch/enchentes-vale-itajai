/**
 * O menu de cidades do Monitor — na ORDEM DO RIO, sem linearizar a árvore.
 *
 * Pedido de 06/09/2026: "um menu com os nomes das cidades, com ordem conforme
 * o rio; clica na cidade e abre a tela da cidade". A ordem certa não é uma
 * fila. O Itajaí-Açu é uma ÁRVORE (docs/TOPOLOGIA-CANONICA.md): Taió e
 * Ituporanga correm EM PARALELO até Rio do Sul; Ibirama, Timbó e Rio dos
 * Cedros entram de lado; só o tronco é sequência. Um menu que listasse
 * "Taió → Ituporanga → Rio do Sul" afirmaria uma ordem que não existe — a
 * mesma crítica que já valeu para a tela de início (adendo A6).
 *
 * Por isso o menu vem em GRUPOS, e cada grupo diz o que é: cabeceiras (sem
 * ordem entre si), tronco (montante → jusante), afluentes (com onde entram) e
 * "outros pontos" para o que a fonte não posicionou. O Mirim, que é fila, sai
 * na ordem do cadastro.
 *
 * Tudo aqui sai do `estacoes.json`; nada é escrito à mão.
 */

export interface CidadeParaMenu {
  id: string
  nome: string
  ordem?: number | null
  sub_bacia?: string | null
}

export interface TopologiaParaMenu {
  tronco_sequencia?: string[]
  cabeceiras_paralelas?: string[]
  afluentes_laterais?: { id: string; entra_perto_de?: string; rio?: string }[]
}

export interface RioParaMenu {
  id: string
  nome: string
  cidades: CidadeParaMenu[]
  _topologia?: TopologiaParaMenu | null
}

export interface ItemDoMenu {
  id: string
  nome: string
  /** O que distingue este item dentro do grupo — o curso, ou onde entra. */
  detalhe: string | null
}

export interface GrupoDoMenu {
  titulo: string
  /** Se os itens têm ordem entre si. Cabeceiras e afluentes NÃO têm. */
  ordenado: boolean
  itens: ItemDoMenu[]
}

export interface RioNoMenu {
  id: string
  nome: string
  grupos: GrupoDoMenu[]
}

export function menuDasCidades(rios: RioParaMenu[]): RioNoMenu[] {
  return rios.map((rio) => ({ id: rio.id, nome: rio.nome, grupos: gruposDoRio(rio) }))
}

function gruposDoRio(rio: RioParaMenu): GrupoDoMenu[] {
  const porId = new Map(rio.cidades.map((c) => [c.id, c]))
  const nome = (id: string) => porId.get(id)?.nome ?? id
  const usados = new Set<string>()
  const grupos: GrupoDoMenu[] = []
  const t = rio._topologia

  if (t && (t.tronco_sequencia?.length || t.cabeceiras_paralelas?.length)) {
    const cabeceiras = (t.cabeceiras_paralelas ?? []).filter((id) => porId.has(id))
    if (cabeceiras.length > 0) {
      grupos.push({
        titulo: 'Cabeceiras',
        ordenado: false,
        itens: cabeceiras.map((id) => {
          usados.add(id)
          return { id, nome: nome(id), detalhe: porId.get(id)?.sub_bacia ?? null }
        }),
      })
    }
    const tronco = (t.tronco_sequencia ?? []).filter((id) => porId.has(id))
    if (tronco.length > 0) {
      grupos.push({
        titulo: 'Tronco',
        ordenado: true,
        itens: tronco.map((id) => {
          usados.add(id)
          return { id, nome: nome(id), detalhe: null }
        }),
      })
    }
    const laterais = (t.afluentes_laterais ?? []).filter((a) => porId.has(a.id))
    if (laterais.length > 0) {
      grupos.push({
        titulo: 'Afluentes',
        ordenado: false,
        itens: laterais.map((a) => {
          usados.add(a.id)
          const onde = a.entra_perto_de ? `entra perto de ${nome(a.entra_perto_de)}` : null
          const curso = a.rio ?? porId.get(a.id)?.sub_bacia ?? null
          return { id: a.id, nome: nome(a.id), detalhe: [curso, onde].filter(Boolean).join(' · ') || null }
        }),
      })
    }
  } else {
    // Rio em fila: a ordem do cadastro. Quem não tem `ordem` vai para "outros",
    // porque inventar posição numa fila é inventar montante e jusante.
    const emFila = rio.cidades
      .filter((c) => typeof c.ordem === 'number' && Number.isFinite(c.ordem))
      .sort((a, b) => (a.ordem as number) - (b.ordem as number))
    if (emFila.length > 0) {
      grupos.push({
        titulo: 'Montante → jusante',
        ordenado: true,
        itens: emFila.map((c) => {
          usados.add(c.id)
          return { id: c.id, nome: c.nome, detalhe: null }
        }),
      })
    }
  }

  const sobra = rio.cidades.filter((c) => !usados.has(c.id))
  if (sobra.length > 0) {
    grupos.push({
      titulo: 'Outros pontos',
      ordenado: false,
      itens: sobra.map((c) => ({ id: c.id, nome: c.nome, detalhe: c.sub_bacia ?? 'sem posição na árvore' })),
    })
  }
  return grupos
}
