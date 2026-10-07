/**
 * Os traçados dos rios como OPÇÕES do menu "Camadas do mapa" (redesenho do Monitor, etapa 1 —
 * docs/REDESENHO-MONITOR-MOBILE-2026-10-07.md).
 *
 * Cada arquivo de `data/rios/*.geojson` é um curso real (OSM, conferido em
 * docs/TRACADOS-AFLUENTES-2026-10-06.md e docs/tracado-ribeiroes.md). Aqui só se dá NOME a cada um e se
 * decide o que a pessoa pode esconder: o tronco (Açu e Mirim) fica sempre, porque é nele que estão as
 * cidades que pintam o mapa — sem o traçado, os pinos sumiriam junto. Os afluentes e ribeirões são
 * opcionais, cada um com a sua caixa. Rio Benedito e Rio dos Cedros são DOIS cursos e duas caixas
 * (correção do Jefferson sobre a maquete, 07/10/2026, que os tinha juntado).
 *
 * Nada aqui muda coordenada nem geometria: esconder um traçado é só não desenhá-lo.
 */

/** Nome que a pessoa lê, por `rioId` (o nome do arquivo sem `.geojson`). */
export const NOME_TRACADO: Record<string, string> = {
  'itajai-acu': 'Itajaí-Açu (com o Itajaí do Oeste)',
  'itajai-mirim': 'Itajaí-Mirim',
  'mirim-canal-retificado': 'Canal retificado do Mirim',
  'itajai-do-sul': 'Itajaí do Sul',
  benedito: 'Rio Benedito',
  'rio-dos-cedros': 'Rio dos Cedros',
  hercilio: 'Rio Hercílio',
  'luiz-alves': 'Rio Luís Alves',
  trombudo: 'Rio Trombudo',
  guabiruba: 'Rio Guabiruba (e Guabiruba Norte)',
  'ribeiro-taquaras': 'Ribeirão Taquaras',
  'ribeirao-taquaras': 'Ribeirão Taquaras',
  'rio-rafael': 'Rio Rafael (e braços)',
  'ribeirao-murta': 'Ribeirão da Murta (Itajaí)',
  'ribeirao-canhanduba': 'Ribeirão Canhanduba (Itajaí)',
  'rio-conceicao': 'Rio Conceição (Itajaí)',
}

/** Tronco: fica sempre no mapa (as cidades que pintam estão nele). */
export const TRACADOS_FIXOS = new Set(['itajai-acu', 'itajai-mirim', 'mirim-canal-retificado'])

/**
 * Arquivos que são o MESMO curso para a pessoa: os braços do Rio Rafael entram na caixa do Rio Rafael.
 * Devolve o id do grupo (o próprio id quando o curso está sozinho).
 */
export function grupoDoTracado(rioId: string): string {
  if (rioId.startsWith('rio-rafael')) return 'rio-rafael'
  return rioId
}

export interface OpcaoDeTracado {
  /** O id do grupo (chave da caixa). */
  id: string
  nome: string
  /** Os arquivos que a caixa liga e desliga juntos. */
  ids: string[]
  /** Tronco: aparece marcado e não desliga. */
  fixo: boolean
}

/** Um nome legível para um id sem ficha: "rio-dos-cedros" → "Rio dos cedros". Nunca inventa curso. */
function nomeDeReserva(id: string): string {
  const texto = id.replace(/-/g, ' ')
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

/**
 * As opções do menu a partir dos traçados REALMENTE carregados (não da lista de nomes): um rio só
 * aparece aqui se o arquivo dele existe e foi baixado. Tronco primeiro; o resto em ordem alfabética.
 */
export function opcoesDeTracado(rios: readonly { rioId: string }[]): OpcaoDeTracado[] {
  const grupos = new Map<string, string[]>()
  for (const r of rios) {
    const g = grupoDoTracado(r.rioId)
    grupos.set(g, [...(grupos.get(g) ?? []), r.rioId])
  }
  const lista = [...grupos].map(([id, ids]) => ({
    id,
    nome: NOME_TRACADO[id] ?? nomeDeReserva(id),
    ids: ids.sort(),
    fixo: ids.every((x) => TRACADOS_FIXOS.has(x)),
  }))
  return lista.sort((a, b) => Number(b.fixo) - Number(a.fixo) || a.nome.localeCompare(b.nome, 'pt-BR'))
}

/** Os traçados que ficam no mapa: tira os grupos escondidos; o tronco nunca sai. */
export function tracadosVisiveis<T extends { rioId: string }>(rios: readonly T[], ocultos: ReadonlySet<string>): T[] {
  return rios.filter((r) => TRACADOS_FIXOS.has(r.rioId) || !ocultos.has(grupoDoTracado(r.rioId)))
}

/** "5 de 6": quantos grupos estão ligados, para o título da seção. */
export function contagemDeTracados(opcoes: readonly OpcaoDeTracado[], ocultos: ReadonlySet<string>): string {
  const ligados = opcoes.filter((o) => o.fixo || !ocultos.has(o.id)).length
  return `${ligados} de ${opcoes.length}`
}
