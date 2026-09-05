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
  /** Como chamar a régua na tela. É o `titulo`, o nome que a fonte publica hoje. */
  nome: string
  /**
   * Como o Plano de Contingência chamava a régua, quando difere do `titulo`.
   * Só serve de nota de rodapé, para quem for conferir no documento — NUNCA
   * como rótulo: o nome do Plano nomeia lugar errado (ver `nomeDaRegua`).
   */
  nomeNoPlano: string | null
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

/**
 * Um braço paralelo de um curso, com seu nome e suas réguas na ordem da descida.
 *
 * Em Itajaí o Mirim se divide em dois braços — o curso antigo (meandros
 * naturais) e o canal retificado — que correm lado a lado e se reencontram
 * perto da foz. O rótulo do braço vem do PRÓPRIO título de cada régua, como a
 * Defesa Civil o escreve; não é dedução de coordenada (as coordenadas das réguas
 * ainda estão em disputa — ver `docs/coordenadas-dc-itajai.md`).
 */
export interface Braco {
  chave: string
  nome: string
  reguas: ReguaComCota[]
}

/** Um curso d'água com suas réguas já na ordem da descida (montante → foz). */
export interface GrupoDeCurso {
  rio: string
  nome: string
  reguas: ReguaComCota[]
  /**
   * Só quando o curso se divide em braços paralelos (hoje, o Mirim em Itajaí):
   * as réguas ANTES da divisão, os braços, e o par de réguas onde eles se
   * reencontram (uma de cada braço, na mesma posição da descida). Ausente nos
   * cursos que não bifurcam — a UI mostra a lista plana `reguas`.
   */
  divisao?: {
    antes: ReguaComCota[]
    bracos: Braco[]
    reencontro: ReguaComCota[]
  }
}

/** Rótulo de braço → nome na tela. A chave casa por substring no título. */
const NOME_BRACO: Record<string, string> = {
  'curso antigo': 'Braço do curso antigo (meandros)',
  'canal retificado': 'Braço do canal retificado',
}
/** Ordem de exibição dos braços: o curso natural primeiro, depois o canal. */
const ORDEM_BRACO = ['curso antigo', 'canal retificado']

/**
 * O braço a que uma régua pertence, lido do título (a Defesa Civil escreve
 * "(curso antigo)" / "(canal retificado)"). `null` = régua acima da divisão
 * (DC-10) ou curso que não bifurca. O canal é testado antes: a régua da junção
 * (DC-04, "canal retificado e curso antigo") entra como a ponta de baixo do
 * canal, onde ele reencontra o curso antigo.
 */
function bracoDaRegua(r: ReguaComCota): string | null {
  const t = r.titulo.toLowerCase()
  if (t.includes('canal retificado')) return 'canal retificado'
  if (t.includes('curso antigo')) return 'curso antigo'
  return null
}

/**
 * Se o curso se divide em braços (≥ 2 braços rotulados no título), devolve as
 * réguas de antes da divisão, os braços na ordem de exibição e o par de
 * reencontro (réguas de braços diferentes na MESMA posição da descida). Senão,
 * `undefined` — o curso é uma linha só.
 */
function dividirEmBracos(reguas: ReguaComCota[]): GrupoDeCurso['divisao'] {
  const chaves = new Set(reguas.map(bracoDaRegua).filter((c): c is string => c !== null))
  if (chaves.size < 2) return undefined
  const antes = reguas.filter((r) => bracoDaRegua(r) === null)
  const bracos: Braco[] = ORDEM_BRACO.filter((c) => chaves.has(c)).map((chave) => ({
    chave,
    nome: NOME_BRACO[chave] ?? chave,
    reguas: reguas.filter((r) => bracoDaRegua(r) === chave),
  }))
  // O reencontro: uma ordem de descida com réguas em mais de um braço.
  const porOrdem = new Map<number, ReguaComCota[]>()
  for (const b of bracos) {
    for (const r of b.reguas) {
      if (r.ordemDescida == null) continue
      const arr = porOrdem.get(r.ordemDescida) ?? []
      arr.push(r)
      porOrdem.set(r.ordemDescida, arr)
    }
  }
  let reencontro: ReguaComCota[] = []
  for (const arr of porOrdem.values()) if (arr.length > 1) reencontro = arr
  return { antes, bracos, reencontro }
}

/**
 * Agrupa as réguas por curso e ordena cada grupo pela descida do rio.
 *
 * É o mesmo desenho do `/rios` do bot: numa cidade com réguas em vários cursos
 * (Itajaí tem quatro), amontoá-las numa lista faz o morador ler a régua errada.
 * Cada curso vira um bloco com nome; dentro dele, montante → foz por
 * `ordemDescida`. O curso que se divide em braços (o Mirim) vem com `divisao`:
 * as réguas de antes da bifurcação e os dois braços paralelos, para não
 * intercalar curso antigo e canal numa fila só — que era ler a régua errada de
 * novo, agora dentro do mesmo rio.
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
    .map((rio) => {
      const ordenadas = [...porCurso.get(rio)!].sort(porDescida)
      return {
        rio,
        nome: NOME_CURSO[rio] ?? rio ?? '—',
        reguas: ordenadas,
        divisao: dividirEmBracos(ordenadas),
      }
    })
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

/**
 * Compara nomes ignorando o que não muda o LUGAR: acento, caixa, pontuação,
 * travessão contra hífen e o código na frente.
 *
 * Sem isto a nota de rodapé sairia nas onze réguas, porque quase todas diferem
 * do Plano só por grafia — a DC-11 é "Açú – Santa Regina" no título e
 * "Açu - Santa Regina" no Plano. Repetir isso embaixo de cada número é ruído
 * num celular, na chuva. A nota tem que aparecer onde muda o lugar, como na
 * DC-02: "Praça Celso Pereira da Silva" contra "Praça da Murta".
 */
function mesmoLugar(a: string, b: string): boolean {
  const limpo = (t: string) =>
    t
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/^dc-\d+\s*/, '')
      .replace(/[^a-z0-9]+/g, ' ')
      .trim()
  const x = limpo(a)
  const y = limpo(b)
  return x === y || x.includes(y) || y.includes(x)
}

function nomeDaRegua(e: EstacaoTempoReal): string {
  // O rótulo é o `titulo` — o nome que a fonte publica HOJE.
  //
  // Antes daqui saía `nome_no_plano`, com a intenção de que quem fosse
  // conferir achasse o mesmo nome no documento oficial. A intenção é boa e o
  // efeito era grave: o Plano é mais velho que a página, e o nome dele aponta
  // LUGAR ERRADO. A DC-02 fica no Rio Itajaí-Açu, na Praça Celso Pereira da
  // Silva; o Plano a chama "Praça da Murta", e a tela escrevia Murta. Só que a
  // Murta de verdade é outra calha e outras duas réguas — DC-07 e DC-09, no
  // `ribeirao-murta`. Quem mora na Murta lia o nível do Açu achando que era o
  // ribeirão do bairro dele. Também apagava o ICMBio da DC-01.
  //
  // O nome do Plano não se perde: vai em `nomeNoPlano`, como nota de rodapé.
  const nome = e.titulo
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
      // Só quando o Plano nomeia OUTRO lugar. Diferença de acento ou de
      // travessão não é diferença de lugar — ver `mesmoLugar`.
      nomeNoPlano:
        e.nome_no_plano?.trim() && !mesmoLugar(e.titulo, e.nome_no_plano.trim())
          ? e.nome_no_plano.trim()
          : null,
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
