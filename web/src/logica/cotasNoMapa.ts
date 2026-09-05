import type { CotaRua } from '../dados/tipos'

/**
 * As COTAS DE RUA no mapa ao vivo — a partir de que nível do rio cada rua alaga.
 *
 * É o dado mais direto do projeto (leitura de tabela, sem modelo) e o que mais
 * ganha com o zoom. Também é o mais perigoso de desenhar errado, e por isso
 * este módulo carrega quatro travas:
 *
 * 1. **Só onde o par cota↔leitura foi PROVADO.** A cota de rua descreve UMA
 *    régua; o nível ao vivo vem de OUTRA fonte. Se não forem a mesma régua, o
 *    mapa estaria dizendo "a sua rua alagou" com o metro de outro lugar — a
 *    regra nº 1 do projeto. O cadastro já separa isso: Gaspar tem
 *    `cotas_verificado: true`; Brusque, que TEM 348 ruas georreferenciadas,
 *    tem `false`, porque a régua da leitura ao vivo não é a das cotas dela.
 *    Coordenada não é passaporte.
 * 2. **Só de perto.** 1.613 pontos no zoom da bacia viram uma nuvem, e nuvem de
 *    pontos num mapa de enchente lê-se como MANCHA — a área alagada que este
 *    projeto se recusa a inventar. Abaixo de `KM_PARA_MOSTRAR` os pontos são
 *    distinguíveis como pontos; acima, não são.
 * 3. **Sem leitura, sem estado.** `atingida` vira `null`, e a tela desenha os
 *    pontos sem afirmar nada. "Não sei" não é "não alagou".
 * 4. **Nunca uma cor por METRO.** São dois estados (o rio já chegou nesta rua,
 *    ou ainda não), como a cor do rio é faixa e nunca metro. Um degradê por
 *    cota afirmaria uma precisão de interpolação que ponto nenhum tem — e o
 *    vazio ENTRE as ruas continua vazio, porque ali não se sabe.
 */

/** Largura máxima de tela, em km, para os pontos aparecerem. Ver trava 2. */
export const KM_PARA_MOSTRAR = 8

/**
 * Cor das cotas de rua. Deliberadamente FORA da paleta de faixa
 * (`--faixa-*`: verde, amarelo, laranja, vermelho) e do violeta do nível bruto
 * (`COR_BRUTO`): rua alagada não é faixa de rio, e confundir as duas leituras
 * na mesma cor seria dizer uma pela outra. O ESTADO é o preenchimento, não o
 * tom — mesma cor, cheia ou vazada.
 */
export const COR_COTA_RUA = '#6d1f6d'

export interface PontoDeRua {
  rua: string
  lat: number
  lon: number
  cotaM: number
  /** `true` já alagou, `false` ainda não, `null` sem leitura para comparar. */
  atingida: boolean | null
}

export interface CidadeParaRuas {
  id: string
  cotas_verificado?: boolean | null
}

/**
 * A cidade pode ter as ruas desenhadas no mapa ao vivo?
 *
 * `cotas_verificado` é o campo que o cadastro usa para dizer que as cotas
 * daquela cidade foram conferidas contra a régua que o site lê. Ausente
 * (`null`) NÃO é permissão: é "ninguém conferiu ainda".
 */
export function cidadePodeMostrarRuas(cidade: CidadeParaRuas | null | undefined): boolean {
  return cidade?.cotas_verificado === true
}

/** O zoom de agora permite ver os pontos como pontos? Ver trava 2. */
export function zoomPermiteRuas(kmNaTela: number, limite: number = KM_PARA_MOSTRAR): boolean {
  return Number.isFinite(kmNaTela) && kmNaTela > 0 && kmNaTela <= limite
}

/**
 * Os pontos de rua de uma cidade, comparados com o nível de agora.
 *
 * Sai vazio quando a cidade não passa na trava 1 — e sai vazio de propósito,
 * não com os pontos "sem estado": desenhar as ruas de Brusque já sugeriria que
 * o número ao lado vale para elas.
 */
export function pontosDeRua(
  cotas: readonly CotaRua[],
  cidade: CidadeParaRuas | null | undefined,
  nivelM: number | null | undefined,
): PontoDeRua[] {
  if (!cidadePodeMostrarRuas(cidade)) return []
  const temNivel = typeof nivelM === 'number' && Number.isFinite(nivelM)
  const saida: PontoDeRua[] = []
  for (const c of cotas) {
    if (c.cidade !== cidade!.id) continue
    if (typeof c.cota_m !== 'number' || !Number.isFinite(c.cota_m)) continue
    const lat = (c as { lat?: unknown }).lat
    const lon = (c as { lon?: unknown }).lon
    if (typeof lat !== 'number' || typeof lon !== 'number') continue
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue
    saida.push({
      rua: c.ponto && c.ponto !== c.rua ? `${c.rua} (${c.ponto})` : c.rua,
      lat,
      lon,
      cotaM: c.cota_m,
      atingida: temNivel ? c.cota_m <= (nivelM as number) : null,
    })
  }
  return saida
}

/** Quantas já alagaram, quantas faltam, quantas sem saber. Para a legenda. */
export function contarRuas(pontos: readonly PontoDeRua[]): {
  atingidas: number
  aguardando: number
  semLeitura: number
} {
  let atingidas = 0
  let aguardando = 0
  let semLeitura = 0
  for (const p of pontos) {
    if (p.atingida === null) semLeitura++
    else if (p.atingida) atingidas++
    else aguardando++
  }
  return { atingidas, aguardando, semLeitura }
}
