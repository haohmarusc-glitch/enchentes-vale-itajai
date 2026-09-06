import type { CotaRua } from '../dados/tipos'

/**
 * As COTAS DE RUA no mapa ao vivo — a partir de que nível do rio cada rua alaga.
 *
 * É o dado mais direto do projeto (leitura de tabela, sem modelo) e o que mais
 * ganha com o zoom. Também é o mais perigoso de desenhar errado, e por isso
 * este módulo carrega quatro travas:
 *
 1. **A COMPARAÇÃO só onde o par cota↔leitura foi PROVADO.** A cota de rua
 *    descreve UMA régua; o nível ao vivo vem de OUTRA fonte. Se não forem a
 *    mesma, dizer "a sua rua alagou" usaria o metro de outro lugar — a regra
 *    nº 1 do projeto. O cadastro separa: Gaspar tem `cotas_verificado: true`;
 *    **Brusque tem `false`**, porque as cotas dela são da Ponte Estaiada
 *    (provado: cota + lâmina = 8,96 m, o pico de 17/11/2023, em 183 dos 184
 *    pontos) e as duas estações ao vivo dela têm `regua: null`.
 *
 *    Mas a cidade não comparável **não some do mapa**: os pontos aparecem com a
 *    cota de cada rua e **sem estado** — que é informação boa ("esta rua alaga
 *    com o rio em 8,20 m") sem a afirmação que não se pode fazer. Ficar
 *    invisível não protegeria ninguém: esconde o levantamento e não impede a
 *    conta, que a pessoa faria de cabeça com o número do pino ao lado.
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

/** Por que um ponto não tem estado. `null` = tem estado. */
export type SemEstado =
  /** Não há leitura do rio agora (ou está velha demais). */
  | 'sem-leitura'
  /** A régua da leitura ao vivo não é, comprovadamente, a das cotas. */
  | 'regua-nao-provada'

export interface PontoDeRua {
  rua: string
  lat: number
  lon: number
  cotaM: number
  /** `true` já alagou, `false` ainda não, `null` quando não dá para dizer. */
  atingida: boolean | null
  /** Quando `atingida` é null, o motivo — a tela diz qual dos dois é. */
  motivo: SemEstado | null
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

/**
 * Cidades com cota de rua LEVANTADA e sem coordenada na fonte, e quantas.
 *
 * POR QUE ISTO É UMA CONSTANTE, e não uma contagem. O `cotas-ruas.json` tem
 * 3 MB e é carregado só quando o zoom já permite desenhar os pontos. Mas a
 * frase que o mapa mostra ANTES disso precisa saber a diferença entre "esta
 * cidade não tem levantamento" e "tem, e não dá para pôr no mapa" — e carregar
 * 3 MB no celular de alguém no meio da chuva só para escolher uma frase seria
 * cobrar caro pela honestidade. São dois números que mudam quando a fonte
 * mudar, e `scripts/validar_dados.py::valida_ruas_sem_coordenada` reprova o
 * commit em que eles deixarem de bater com o arquivo.
 *
 * O QUE ELES CORRIGEM. Blumenau tem o MAIOR levantamento do projeto — 2.042
 * ruas — e nenhuma com coordenada: a lista da Defesa Civil publicada pela
 * imprensa traz rua, bairro e cota, sem ponto. Rio do Sul tem 555 na mesma
 * situação. Até aqui o mapa dizia a essas duas cidades "aproxime para ver as
 * cotas de rua": a pessoa aproximava, não achava nada, e podia concluir que a
 * rua dela não foi levantada. Foi — só não está no mapa, e está na tela da
 * cidade, por nome.
 */
export const RUAS_SEM_COORDENADA: Readonly<Record<string, number>> = {
  blumenau: 2042,
  'rio-do-sul': 555,
}

/** O que o mapa tem a dizer quando não há ponto de rua para desenhar. */
export type AvisoDeRuas =
  /** Pode haver levantamento; de perto ele aparece. */
  | { tipo: 'aproxime' }
  /** Há levantamento, e ele não vai aparecer aqui por falta de coordenada. */
  | { tipo: 'sem-coordenada'; ruas: number }

/**
 * Qual aviso a cidade merece quando o mapa não tem ponto para mostrar.
 *
 * Fica aqui, e não no componente, porque é uma DECISÃO sobre o que se pode
 * afirmar — e decisão dentro de `.tsx` é decisão que teste nenhum alcança.
 */
export function avisoDeRuas(cidadeId: string | null | undefined): AvisoDeRuas {
  const ruas = cidadeId ? RUAS_SEM_COORDENADA[cidadeId] : undefined
  return typeof ruas === 'number' ? { tipo: 'sem-coordenada', ruas } : { tipo: 'aproxime' }
}

/** O zoom de agora permite ver os pontos como pontos? Ver trava 2. */
export function zoomPermiteRuas(kmNaTela: number, limite: number = KM_PARA_MOSTRAR): boolean {
  return Number.isFinite(kmNaTela) && kmNaTela > 0 && kmNaTela <= limite
}

/**
 * Os pontos de rua de uma cidade, comparados com o nível de agora QUANDO PODE.
 *
 * Cidade sem par provado devolve os pontos com `atingida: null` e
 * `motivo: 'regua-nao-provada'`. O mapa mostra a cota de cada rua e não afirma
 * se ela alagou.
 */
export function pontosDeRua(
  cotas: readonly CotaRua[],
  cidade: CidadeParaRuas | null | undefined,
  nivelM: number | null | undefined,
): PontoDeRua[] {
  if (!cidade?.id) return []
  const podeComparar = cidadePodeMostrarRuas(cidade)
  const temNivel = typeof nivelM === 'number' && Number.isFinite(nivelM)
  const motivo: SemEstado | null = !podeComparar
    ? 'regua-nao-provada'
    : temNivel
      ? null
      : 'sem-leitura' 
  const saida: PontoDeRua[] = []
  for (const c of cotas) {
    if (c.cidade !== cidade.id) continue
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
      atingida: motivo === null ? c.cota_m <= (nivelM as number) : null,
      motivo,
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
