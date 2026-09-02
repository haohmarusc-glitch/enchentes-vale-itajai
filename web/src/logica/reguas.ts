/**
 * As réguas de uma cidade, com as cotas oficiais de cada uma.
 *
 * Por que isto existe: `Cidade.cotas_m` guarda a cota da cidade quando ela tem
 * UMA régua de referência. Itajaí tem onze e Ilhota tem uma que só aparece em
 * `estacoes_tempo_real` — nesses casos as cotas existem, são oficiais (Plano de
 * Contingência da COMPDEC de Itajaí), mas ficavam invisíveis na tela, que dizia
 * "cotas de referência não levantadas" para uma cidade cujas cotas estão
 * publicadas. Dizer que não há dado quando há é o mesmo tipo de erro que
 * inventar um: as duas coisas fazem alguém decidir com informação falsa.
 *
 * O que este módulo NÃO faz: escolher uma régua como "a régua da cidade". Cada
 * uma tem seu próprio zero — na foz, umas medem o estuário e sobem com a maré,
 * outra mede o rio 20 km acima. Somar, comparar ou eleger uma delas produziria
 * um número que não existe em lugar nenhum. A tela mostra todas, dizendo qual é
 * qual.
 */
import type { EstacaoTempoReal } from '../dados/tipos'

/** Uma régua pronta para a tela: identificada, com cotas e com as ressalvas. */
export interface ReguaComCota {
  /** `DC-10`, quando a fonte publica código; senão o título. */
  id: string
  /**
   * O título EXATO que a fonte publica — é por ele que a leitura ao vivo se
   * liga à régua. Casar por código seria casar por prefixo, e prefixo casa
   * errado calado.
   */
  titulo: string
  /** Como chamar a régua na tela. */
  nome: string
  cotas: [string, number][]
  /**
   * `false` quando a régua não serve para disparar aviso a partir de uma
   * travessia isolada — hoje, as do estuário de Itajaí, que sobem e descem com
   * a maré. A tela precisa dizer isso junto da cota, ou o número engana.
   */
  alertaAutomatico: boolean
  motivoSemAlerta: string | null
  referencia: string | null
  /** Calha que a régua mede — inclui os ribeirões, que não têm tela própria. */
  rio: string | null
  /** Documento de onde a cota veio, como escrito no arquivo. */
  fonteCotas: string | null
  /**
   * Posição na descida do curso (1 = mais a montante). `null` quando a fonte
   * não deu coordenada. Réguas co-locadas (braços paralelos) compartilham o
   * valor e trazem `ordemNota`.
   */
  ordemDescida: number | null
  ordemNota: string | null
}

/** Nome de cada curso d'água, para o subtítulo do agrupamento. */
export const NOME_CURSO: Record<string, string> = {
  'itajai-acu': 'Rio Itajaí-Açu',
  'itajai-mirim': 'Rio Itajaí-Mirim',
  'ribeirao-murta': 'Ribeirão da Murta',
  'ribeirao-canhanduba': 'Ribeirão Canhanduba',
}

/** Ordem de exibição dos cursos: os dois rios, depois os ribeirões. */
const ORDEM_CURSO = ['itajai-acu', 'itajai-mirim', 'ribeirao-murta', 'ribeirao-canhanduba']

/** Um curso d'água com suas réguas já na ordem da descida (montante → foz). */
export interface GrupoDeCurso {
  rio: string
  nome: string
  reguas: ReguaComCota[]
}

/**
 * Agrupa as réguas por curso e ordena cada grupo pela descida do rio.
 *
 * É o mesmo desenho do `/rios` do bot: numa cidade com réguas em vários cursos
 * (Itajaí tem quatro), amontoá-las numa lista faz o morador ler a régua errada.
 * Cada curso vira um bloco com nome; dentro dele, montante → foz por
 * `ordemDescida`. As co-locadas (DC-04 × DC-06) ficam juntas, sem fila.
 */
export function agruparPorCurso(reguas: ReguaComCota[]): GrupoDeCurso[] {
  const porCurso = new Map<string, ReguaComCota[]>()
  for (const r of reguas) {
    const chave = r.rio ?? ''
    const lista = porCurso.get(chave)
    if (lista) lista.push(r)
    else porCurso.set(chave, [r])
  }
  const posicao = (rio: string) => {
    const i = ORDEM_CURSO.indexOf(rio)
    return i < 0 ? ORDEM_CURSO.length : i
  }
  return [...porCurso.keys()]
    .sort((a, b) => posicao(a) - posicao(b))
    .map((rio) => ({
      rio,
      nome: NOME_CURSO[rio] ?? rio ?? '—',
      reguas: [...porCurso.get(rio)!].sort(porDescida),
    }))
}

/**
 * Montante → foz por `ordemDescida`. Sem ela (fonte sem coordenada), cai para o
 * id, que é estável — nunca inventa uma ordem física a partir do código.
 */
function porDescida(a: ReguaComCota, b: ReguaComCota): number {
  if (a.ordemDescida != null && b.ordemDescida != null && a.ordemDescida !== b.ordemDescida) {
    return a.ordemDescida - b.ordemDescida
  }
  return a.id.localeCompare(b.id)
}

/**
 * Separa o texto da fonte da URL que vem no fim dele, para a tela poder
 * mostrar o documento com link em vez de despejar a URL crua no meio da frase.
 * Sem URL, devolve o texto inteiro e `url` nulo — nunca inventa link.
 */
export function separarFonte(texto: string): { texto: string; url: string | null } {
  const m = /^(.*?)\s*[—-]?\s*(https?:\/\/\S+)\s*$/s.exec(texto.trim())
  if (!m) return { texto: texto.trim(), url: null }
  return { texto: m[1]!.trim().replace(/[—-]$/, '').trim(), url: m[2]! }
}

function nomeDaRegua(e: EstacaoTempoReal): string {
  // `nome_no_plano` é como a Defesa Civil chama a régua no documento oficial;
  // `titulo` é como ela aparece na página de tempo real. Quem confere numa
  // fonte precisa achar o mesmo nome lá, então o do plano vem primeiro.
  const nome = e.nome_no_plano ?? e.titulo
  if (e.codigo && !nome.startsWith(e.codigo)) return `${e.codigo} — ${nome}`
  return nome
}

/**
 * As réguas COM cota de uma cidade, num rio. Pluviômetro não entra: ele mede
 * chuva, não nível, e uma cota ao lado dele seria leitura de outra grandeza.
 */
export function reguasComCota(
  estacoes: EstacaoTempoReal[],
  rioId: string,
  cidadeId: string,
): ReguaComCota[] {
  return todasAsReguas(estacoes, cidadeId).filter((r) => r.rio === rioId)
}

/**
 * TODAS as réguas com cota de uma cidade, em qualquer calha.
 *
 * Itajaí tem três réguas em ribeirões — Murta e Canhanduba — que não estão em
 * nenhum dos dois eixos e por isso não aparecem nas telas de rio. Elas alagam
 * bairro, e a cota delas é oficial: ficar de fora de toda tela seria esconder
 * o dado de quem mora lá.
 */
export function todasAsReguas(
  estacoes: EstacaoTempoReal[],
  cidadeId: string,
): ReguaComCota[] {
  const saida: ReguaComCota[] = []
  for (const e of estacoes) {
    if (e.cidade !== cidadeId) continue
    if (e.tipo === 'pluviometro') continue
    const cotas = Object.entries(e.cotas_m ?? {}).filter(
      ([, v]) => typeof v === 'number' && Number.isFinite(v),
    )
    if (cotas.length === 0) continue
    saida.push({
      id: e.codigo ?? e.titulo,
      titulo: e.titulo,
      nome: nomeDaRegua(e),
      cotas,
      // Só `false` explícito tira a régua do aviso automático. Ausente quer
      // dizer régua comum de rio, como a de Ilhota.
      alertaAutomatico: e.alerta_automatico !== false,
      motivoSemAlerta: e.motivo_sem_alerta ?? null,
      referencia: e.referencia ?? null,
      rio: e.rio,
      fonteCotas: e.fonte_cotas ?? null,
      ordemDescida: e.ordem_descida ?? null,
      ordemNota: e.ordem_nota ?? null,
    })
  }
  return saida
}
