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

/** Um extremo de maré da tábua: preamar (alta) ou baixamar (baixa). */
export interface ExtremoMare {
  tipo: 'preamar' | 'baixamar'
  quando: Date
  altura_m?: number
}

/** Está a maré subindo (enchente), baixando (vazante), ou não dá para dizer? */
export type EstadoMare = 'subindo' | 'baixando' | 'sem-dado'

export interface MareAgora {
  estado: EstadoMare
  /**
   * Altura relativa da maré AGORA, 0 (baixamar) a 1 (preamar), por interpolação
   * de cosseno entre os dois extremos que cercam o instante. Null quando não há
   * como saber (tábua vazia, ou o instante fora do trecho informado). NÃO é
   * centímetro de rio nem de maré — é só a posição no ciclo, para colorir o mar.
   */
  altura01: number | null
  /** O próximo extremo (a preamar ou baixamar que vem a seguir), se houver. */
  proxima: ExtremoMare | null
}

/** Meio ciclo de maré semidiurna ~6,2 h; acima de 12 h entre extremos é lacuna. */
const MAX_ENTRE_EXTREMOS_MS = 12 * 3_600_000

/**
 * O que a maré está fazendo AGORA, na foz — para o MAR no mapa.
 *
 * Junta preamares e baixamares informadas, acha o par que cerca o instante e diz
 * se a maré sobe ou desce e a que altura do ciclo está. Sem par que cerque o
 * agora — tábua vazia, ou só cobrindo outro dia — devolve `sem-dado`: o mar fica
 * cinza e nada é inventado. Isto é DELIBERADAMENTE separado da faixa de cheia:
 * maré alta NÃO é cheia (as réguas do estuário nem disparam alerta por isso). O
 * mar muda de cor pela maré na sua PRÓPRIA escala; o perigo que ela carrega é
 * outro — maré alta trava o escoamento do rio.
 */
export function estadoMareAgora(
  preamares: { quando: Date; altura_m?: number }[],
  baixamares: { quando: Date; altura_m?: number }[],
  agora: Date,
): MareAgora {
  const extremos: ExtremoMare[] = [
    ...preamares.map((p) => ({ tipo: 'preamar' as const, quando: p.quando, altura_m: p.altura_m })),
    ...baixamares.map((b) => ({ tipo: 'baixamar' as const, quando: b.quando, altura_m: b.altura_m })),
  ]
    .filter((e) => !Number.isNaN(e.quando.getTime()))
    .sort((a, b) => a.quando.getTime() - b.quando.getTime())

  let antes: ExtremoMare | null = null
  let depois: ExtremoMare | null = null
  for (const e of extremos) {
    if (e.quando.getTime() <= agora.getTime()) antes = e
    else {
      depois = e
      break
    }
  }
  // Sem cercar o instante dos dois lados: não há como dizer sobe/desce agora.
  if (!antes || !depois) return { estado: 'sem-dado', altura01: null, proxima: depois }
  // Extremos consecutivos deviam alternar; se não, a tábua tem buraco. E um vão
  // grande demais entre eles é lacuna, não meia-maré real.
  if (antes.tipo === depois.tipo) return { estado: 'sem-dado', altura01: null, proxima: depois }
  if (depois.quando.getTime() - antes.quando.getTime() > MAX_ENTRE_EXTREMOS_MS)
    return { estado: 'sem-dado', altura01: null, proxima: depois }

  const fase =
    (agora.getTime() - antes.quando.getTime()) /
    (depois.quando.getTime() - antes.quando.getTime())
  const subindo = antes.tipo === 'baixamar' // baixamar → preamar
  const altura01 = subindo ? (1 - Math.cos(Math.PI * fase)) / 2 : (1 + Math.cos(Math.PI * fase)) / 2
  return { estado: subindo ? 'subindo' : 'baixando', altura01, proxima: depois }
}
