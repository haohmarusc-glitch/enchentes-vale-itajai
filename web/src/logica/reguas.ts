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
    })
  }
  return saida
}
