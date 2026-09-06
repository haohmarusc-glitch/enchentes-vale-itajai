/**
 * Quantos rótulos de RÉGUA o mapa mostra, conforme o zoom.
 *
 * POR QUE EXISTE (06/09/2026). Itajaí tem ONZE réguas espalhadas por 20 km, e
 * todas tentavam escrever o número ao mesmo tempo: nas capturas do celular do
 * Jefferson elas saíam umas por cima das outras e por cima do nome da cidade.
 * A anticolisão sozinha não resolve — ela só decide QUEM some, e quem some é
 * quem chegou depois, sem critério nenhum. O resultado é uma pilha ilegível, e
 * pilha ilegível num mapa de cheia é pior que dado escondido: parece
 * informação e não se lê.
 *
 * A REGRA É PELO QUE O NÚMERO SIGNIFICA, não por contagem:
 *
 *  - **de longe** (bacia inteira): nenhum rótulo de régua. Os PONTOS ficam, e
 *    quem carrega a história naquele zoom é o pino da cidade;
 *  - **no meio** (a tela de uma cidade): só as réguas que podem VIRAR AVISO —
 *    as que têm faixa. Em Itajaí, nove das onze são de estuário e o número
 *    delas sobe e desce com a maré sem enchente nenhuma (`alerta_automatico:
 *    false`); elas não perdem nada por não gritar o número de longe;
 *  - **de perto**: todas, porque aí cabem.
 *
 * A régua SELECIONADA mantém o rótulo em qualquer zoom — quem tocou nela quer
 * o número dela.
 *
 * O que este módulo NÃO faz: decidir por quantidade ("mostre no máximo 5").
 * Um teto arbitrário esconderia justamente a régua que subiu, num dia de
 * chuva, porque ela era a sexta da lista.
 */

/** Abaixo desta largura de tela, em km, todos os rótulos cabem. */
export const KM_TODAS_AS_REGUAS = 6

/**
 * Acima desta largura, nenhum rótulo de régua.
 *
 * 45 km deixa a tela de uma cidade (24 km de piso, mais aberta em Itajaí por
 * causa da dispersão das réguas) na faixa do meio, que é onde ela deve estar:
 * mostrando as que podem virar aviso. A bacia inteira tem ~158 km e cai fora.
 */
export const KM_SEM_ROTULO_DE_REGUA = 45

export type DetalheDasReguas = 'todas' | 'so-as-que-avisam' | 'nenhuma'

/**
 * Quanto detalhe este zoom comporta.
 *
 * Medida desconhecida (NaN, zero, infinito) devolve `todas`: é o
 * comportamento de antes desta regra, e na dúvida não se esconde dado.
 */
export function detalheDasReguas(kmNaTela: number): DetalheDasReguas {
  if (!Number.isFinite(kmNaTela) || kmNaTela <= 0) return 'todas'
  if (kmNaTela <= KM_TODAS_AS_REGUAS) return 'todas'
  if (kmNaTela > KM_SEM_ROTULO_DE_REGUA) return 'nenhuma'
  return 'so-as-que-avisam'
}

/** O mínimo que a regra precisa saber de cada régua. */
export interface ReguaParaRotular {
  codigo: string
  /** `null` = não pode virar aviso agora (maré, sem cota, sem leitura fresca). */
  faixa: unknown
}

/**
 * Os códigos das réguas que mostram o número neste zoom.
 *
 * Devolver um conjunto, e não uma lista filtrada, é de propósito: o PONTO de
 * toda régua continua sendo desenhado. O que este módulo decide é só quem fala.
 */
export function reguasComRotulo(
  reguas: readonly ReguaParaRotular[],
  kmNaTela: number,
  selecionada: string | null = null,
): Set<string> {
  const detalhe = detalheDasReguas(kmNaTela)
  const saida = new Set<string>()
  for (const r of reguas) {
    if (!r.codigo) continue
    const pode =
      detalhe === 'todas' ||
      (detalhe === 'so-as-que-avisam' && r.faixa != null) ||
      r.codigo === selecionada
    if (pode) saida.add(r.codigo)
  }
  // A selecionada entra mesmo que não esteja na lista de visíveis do quadro.
  if (selecionada) saida.add(selecionada)
  return saida
}
