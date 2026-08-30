/**
 * Manchas de inundação: onde a água chegou em cada evento.
 *
 * Os GeoJSON vêm da organização GeoItajaí, mantida pela prefeitura de Itajaí,
 * sob licença MIT. São dado oficial e aberto — o oposto do resto que este
 * projeto raspa de HTML.
 *
 * O QUE A MANCHA NÃO É, e a tela precisa dizer:
 *
 * * **Não é previsão.** Mostra onde a água chegou naquele evento, na cidade
 *   que existia naquele ano. Aterro, drenagem e construção mudaram o terreno.
 * * **Não traz nível de rio.** Os polígonos não têm cota. A ligação com o pico
 *   é feita pela data, e só aparece quando aquele pico está em `enchentes.json`
 *   — hoje, em nenhum dos nove eventos. Inventar essa ligação faria alguém
 *   olhar o mapa de 2011 e concluir que a sua rua alaga a tal metro.
 * * **Ausência de mancha não é ausência de risco.** O levantamento cobre o que
 *   foi mapeado, não tudo o que alagou.
 */

/** Uma classe de profundidade da lâmina d'água, como a fonte publica. */
export interface ClasseLamina {
  rotulo: string
  lamina_min_m: number | null
  lamina_max_m: number | null
}

export interface Mancha {
  cidade: string
  evento: string
  tipo: string
  arquivo: string
  tem_lamina: boolean
  pico_registrado: { data: string; pico_m: number | null; fonte?: string } | null
  licenca: string
  fonte: string
  feicoes: number
  crs: string | null
  classes_lamina: ClasseLamina[]
  classes_sobrepostas: boolean
}

/**
 * Cor por profundidade, do raso ao fundo.
 *
 * Azul progressivamente mais escuro, não uma escala vermelho-amarelo: a água
 * não é "pior" quando é mais funda de um jeito que justifique semáforo, e o
 * vermelho já é usado no site para cota de inundação. Escala sequencial única
 * também é legível para quem não distingue vermelho de verde.
 */
const ESCALA = ['#cfe3f5', '#9dc6e8', '#6aa8db', '#3d87c4', '#1f5f96', '#123f66']

/**
 * A cor de uma classe, pela profundidade máxima.
 *
 * Classe sem número reconhecido fica cinza — e cinza aqui significa "a fonte
 * não disse", não "raso".
 */
export function corDaLamina(classe: ClasseLamina): string {
  const topo = classe.lamina_max_m
  if (topo === null) return '#b9c0c8'
  if (topo <= 0.2) return ESCALA[0]!
  if (topo <= 0.4) return ESCALA[1]!
  if (topo <= 0.6) return ESCALA[2]!
  if (topo <= 1) return ESCALA[3]!
  if (topo <= 2) return ESCALA[4]!
  return ESCALA[5]!
}

/** `jul/2013`, `2001` — o rótulo do evento a partir de `AAAA-MM` ou `AAAA`. */
const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun',
               'jul', 'ago', 'set', 'out', 'nov', 'dez']

export function rotuloEvento(evento: string): string {
  const [ano, mes] = evento.split('-')
  if (!mes) return ano ?? evento
  const i = Number(mes) - 1
  return `${MESES[i] ?? mes}/${ano}`
}

/**
 * As manchas em ordem cronológica, a mais recente primeiro.
 *
 * Quando o mesmo evento tem dois arquivos — a mancha total e a de lâmina —, a
 * de lâmina vem antes: ela diz quanto de água, não só onde.
 */
export function ordenar(manchas: Mancha[]): Mancha[] {
  return [...manchas].sort((a, b) => {
    if (a.evento !== b.evento) return b.evento.localeCompare(a.evento)
    if (a.tem_lamina !== b.tem_lamina) return a.tem_lamina ? -1 : 1
    return a.arquivo.localeCompare(b.arquivo)
  })
}

/** Classes da mancha, do raso para o fundo, para a legenda. */
export function legenda(mancha: Mancha): ClasseLamina[] {
  return [...mancha.classes_lamina].sort(
    (a, b) => (a.lamina_max_m ?? 99) - (b.lamina_max_m ?? 99),
  )
}
