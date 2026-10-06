export function normalizarVia(texto: string): string {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLocaleLowerCase('pt-BR').trim()
}

export function pesquisarVias(dados: GeoJSON.FeatureCollection, termo: string): string[] {
  const busca = normalizarVia(termo)
  if (busca.length < 3) return []
  return [...new Set(dados.features.map(f => f.properties?.nome)
    .filter((nome): nome is string => typeof nome === 'string' && normalizarVia(nome).includes(busca)))]
    .sort((a, b) => a.localeCompare(b, 'pt-BR')).slice(0, 20)
}

/**
 * O TIPO de via, do jeito que a base de vias da Prefeitura de Itajaí abrevia ("R.", "Av.", "Trav.", "Serv.",
 * "Rod.", "Al.") e do jeito que a pessoa escreve ("rua", "avenida", "travessa"…). É o que separa os homônimos
 * da base: "R.Carlos Drumond de Andrade" e "Av.Carlos Drumond de Andrade" são vias diferentes.
 */
export type TipoDeVia = 'r' | 'av' | 'trav' | 'serv' | 'rod' | 'al' | 'est'

const TIPOS: [RegExp, TipoDeVia][] = [
  [/^(?:r|rua)$/, 'r'],
  [/^(?:av|avenida)$/, 'av'],
  [/^(?:trav|tv|travessa)$/, 'trav'],
  [/^(?:serv|servidao)$/, 'serv'],
  [/^(?:rod|rodovia)$/, 'rod'],
  [/^(?:al|alameda)$/, 'al'],
  [/^(?:est|estrada)$/, 'est'],
]

const simples = (s: string) =>
  normalizarVia(s).replace(/[^a-z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim()

/** "R.Hamilton Pimentel" → { tipo: 'r', nucleo: 'hamilton pimentel' }; "Rua Lino" → { tipo: 'r', nucleo: 'lino' }. */
export function partesDaVia(nome: string): { tipo: TipoDeVia | null; nucleo: string } {
  const s = simples(nome)
  const primeira = s.split(' ')[0] ?? ''
  const tipo = TIPOS.find(([r]) => r.test(primeira))?.[1] ?? null
  return { tipo, nucleo: tipo ? s.slice(primeira.length).trim() : s }
}

/** "R.Hamilton Pimentel" → "Rua Hamilton Pimentel", para o texto do chat. */
export function nomeLegivelDaVia(nome: string): string {
  return nome
    .replace(/^R\.\s*/, 'Rua ')
    .replace(/^Av\.\s*/, 'Avenida ')
    .replace(/^Trav\.\s*/, 'Travessa ')
    .replace(/^Serv\.\s*/, 'Servidão ')
    .replace(/^Rod\.\s*/, 'Rodovia ')
    .replace(/^Al\.\s*/, 'Alameda ')
}

/**
 * As vias cujo nome casa com o que a pessoa escreveu ("rua hamilton pimentel", "avenida brasil"). Mesma
 * ordem de preferência do chat de perguntas: nome inteiro igual; senão, as palavras inteiras; senão, pedaço.
 * Com o tipo escrito ("avenida"), os homônimos de outro tipo saem — se algum do tipo casar.
 */
export function acharVias(texto: string, nomes: readonly string[]): string[] {
  const pedido = partesDaVia(texto)
  const alvo = pedido.nucleo
  if (alvo.length < 2) return []
  const porNome = nomes.map((n) => ({ n, p: partesDaVia(n) }))
  const escapado = alvo.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const inteira = new RegExp(`(^|\\s)${escapado}(\\s|$)`)
  const exatas = porNome.filter((x) => x.p.nucleo === alvo)
  const porPalavra = porNome.filter((x) => inteira.test(x.p.nucleo))
  let achadas = exatas.length ? exatas : porPalavra.length ? porPalavra : porNome.filter((x) => x.p.nucleo.includes(alvo))
  if (pedido.tipo) {
    const doTipo = achadas.filter((x) => x.p.tipo === pedido.tipo)
    if (doTipo.length) achadas = doTipo
  }
  return [...new Set(achadas.map((x) => x.n))].sort((a, b) => a.localeCompare(b, 'pt-BR'))
}
