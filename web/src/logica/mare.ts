/**
 * Maré na foz do Itajaí.
 *
 * Por que isto existe: em Itajaí a maré alta **trava o escoamento** do rio. A
 * UNIVALI/CTTMAR e a Defesa Civil de Itajaí ampliaram o marégrafo justamente
 * para ler esse efeito, e a UNIVALI descreve o mecanismo no Mirim — quando os
 * dois leitos já estão cheios, o Itajaí-Mirim não consegue entregar água ao
 * Itajaí-Açu e transborda. Uma cheia que chega na preamar é pior que a mesma
 * cheia chegando na vazante.
 *
 * O que este módulo NÃO faz: dizer quantos centímetros a maré acrescenta. Não
 * existe, nos dados deste projeto, nada que calibre isso — e um número inventado
 * aqui seria pior que nenhum. O módulo responde a uma pergunta mais modesta e
 * verificável: **a cheia chega junto com a preamar?** e **este é um período de
 * maré de sizígia?**
 *
 * As preamares vêm da tábua oficial (Marinha/DHN ou Defesa Civil de Itajaí),
 * informadas por quem usa a tela. Nada de tábua é estimado aqui.
 */

const DIA_MS = 86_400_000
const MES_SINODICO_DIAS = 29.530588853

/** Lua nova de referência: 6 de janeiro de 2000, 18:14 UTC. */
const LUA_NOVA_REF = Date.UTC(2000, 0, 6, 18, 14)

/**
 * Distância em dias até a sizígia (lua nova ou cheia) mais próxima.
 *
 * Usa o mês sinódico MÉDIO. A lunação real varia com a excentricidade da órbita,
 * então as datas saem com erro de até cerca de um dia — conferido contra as
 * lunações de 2026. Isso basta para dizer se o período é de maré grande ou
 * pequena, e não basta para nada mais fino. Quem manda no horário da preamar é
 * a tábua oficial, não este cálculo.
 */
export function diasAteSizigia(quando: Date): number {
  const ciclos = (quando.getTime() - LUA_NOVA_REF) / (MES_SINODICO_DIAS * DIA_MS)
  const fase = ((ciclos % 1) + 1) % 1 // 0 = nova, 0,5 = cheia
  const ateNova = Math.min(fase, 1 - fase)
  const ateCheia = Math.abs(fase - 0.5)
  return Math.min(ateNova, ateCheia) * MES_SINODICO_DIAS
}

export type RegimeMare = 'sizigia' | 'quadratura' | 'intermediaria'

/**
 * Sizígia (lua nova ou cheia) traz as marés de maior amplitude — preamares mais
 * altas, que seguram mais o rio. Quadratura (quartos) traz as menores.
 *
 * A amplitude máxima costuma vir 1 a 2 dias DEPOIS da lua nova ou cheia exata;
 * a janela abaixo é simétrica e larga o bastante para cobrir isso.
 */
export function regimeMare(quando: Date): RegimeMare {
  const d = diasAteSizigia(quando)
  if (d <= 2.5) return 'sizigia'
  if (d >= 5.5) return 'quadratura'
  return 'intermediaria'
}

/** Uma preamar da tábua oficial, informada por quem usa a tela. */
export interface Preamar {
  quando: Date
  /** Altura da tábua, em metros, quando informada. Não é o nível do rio. */
  altura_m?: number
}

/**
 * Janela em torno da preamar em que o escoamento fica represado.
 *
 * A maré não estanca só no instante da preamar: o efeito se estende pelas horas
 * de enchente e de estofo. Duas horas para cada lado é uma janela conservadora —
 * conservadora aqui significa avisar mais, não menos.
 */
export const JANELA_PREAMAR_H = 2

export interface CruzamentoMare {
  regime: RegimeMare
  /** Preamares cuja janela encosta na janela de chegada da cheia. */
  coincidentes: Preamar[]
  /** true quando a chegada da cheia cai dentro da janela de alguma preamar. */
  coincide: boolean
  /** Quantas preamares foram informadas para o período. */
  informadas: number
}

/**
 * Cruza a janela de chegada da cheia com as preamares informadas.
 *
 * `inicio`/`fim` são a janela de chegada calculada a partir do tempo de descida.
 */
export function cruzarComMare(
  inicio: Date,
  fim: Date,
  preamares: Preamar[],
): CruzamentoMare {
  const folga = JANELA_PREAMAR_H * 3_600_000
  const coincidentes = preamares.filter(
    (p) => p.quando.getTime() - folga <= fim.getTime() && p.quando.getTime() + folga >= inicio.getTime(),
  )
  // O regime é lido no meio da janela de chegada.
  const meio = new Date((inicio.getTime() + fim.getTime()) / 2)
  return {
    regime: regimeMare(meio),
    coincidentes,
    coincide: coincidentes.length > 0,
    informadas: preamares.length,
  }
}

export type NivelAgravamento = 'agrava' | 'atencao' | 'nao-agrava' | 'sem-tabua'

/**
 * Quanto a maré agrava a chegada desta cheia.
 *
 * É uma classificação qualitativa, de propósito. Sem tábua informada não há
 * classificação nenhuma — a fase da lua sozinha não diz a que horas a preamar
 * acontece.
 */
export function agravamento(c: CruzamentoMare): NivelAgravamento {
  if (c.informadas === 0) return 'sem-tabua'
  if (c.coincide && c.regime === 'sizigia') return 'agrava'
  if (c.coincide || c.regime === 'sizigia') return 'atencao'
  return 'nao-agrava'
}

export const TEXTO_REGIME: Record<RegimeMare, string> = {
  sizigia: 'maré de sizígia (lua nova ou cheia) — preamares mais altas do mês',
  quadratura: 'maré de quadratura (lua em quarto) — preamares mais baixas do mês',
  intermediaria: 'maré intermediária, entre sizígia e quadratura',
}
