/**
 * Que régua pode colorir cada traçado fora do tronco, e até onde (pedido do Jefferson, 07/10/2026 —
 * "Monitor: Ituporanga e barragens", seção 1/1B; auditoria em docs/VINCULOS-DOS-TRACADOS.md).
 *
 * O DEFEITO. O Monitor dava cidades só ao tronco (Açu e Mirim); todo afluente e a cabeceira Sul entravam
 * com `cidades: []` e ficavam cinza por configuração, não por falta de dado. Ituporanga aparecia com o pino
 * vermelho (faixa estadual da DCSC-00039) e o Itajaí do Sul — desenhado até a régua dela desde que o traçado
 * foi completado (58 km, a régua a 19 m) — cinza ao lado.
 *
 * A REGRA. Cada traçado tem um vínculo EXPLÍCITO, escrito aqui com a prova, ou fica sem vínculo com o
 * motivo. O vínculo diz:
 *  - a cidade do cadastro que decide a cor, e o grupo (`itajai-acu`/`itajai-mirim`) em que a leitura e a
 *    classificação dela moram — o id do traçado (`itajai-do-sul`) não é o grupo dos dados;
 *  - a estação que decide (a mesma do pino) e onde ela toca o traçado;
 *  - o FIM do alcance: a confluência com o rio que recebe a água ou a próxima estação rio abaixo, o que vier
 *    primeiro. Uma régua representa só esse trecho: nunca o rio acima dela, nem o rio que recebe a água,
 *    nem segmento desconectado (o alcance é o caminho no próprio traçado, e sem caminho não há cor).
 *
 * A COR é a mesma decisão do pino (mesma estação, medição, frescor e origem): este módulo não calcula
 * faixa nenhuma. Distância geométrica aqui é conferência, não prova de régua: quem decide o vínculo é o
 * cadastro (código da estação) e a decisão escrita.
 */
import type { Cidade } from '../dados/tipos'
import type { LonLat } from './mapaCanvas'
import type { RioParaCena } from './mapaMotor'

export interface VinculoDeTracado {
  /** O traçado (`data/rios/<id>.geojson`). */
  tracado: string
  /** A cidade do cadastro cuja decisão de cor vale para o trecho. */
  cidade: string
  /** O rio do cadastro em que a cidade, a leitura e a classificação dela moram. */
  grupo: 'itajai-acu' | 'itajai-mirim'
  /** A estação que decide a cor do pino da cidade. */
  estacao: string
  /** Onde a estação está ([lon, lat]): o começo do alcance. */
  inicio: LonLat
  /** O fim do alcance ([lon, lat]). */
  fim: LonLat
  /** O que é o fim, como a pessoa lê. */
  fimDescricao: string
  /** O comprimento medido do alcance no traçado de 07/10/2026, para o texto e o teste. */
  km: number
  /** De onde vêm o vínculo e os dois pontos. */
  fonte: string
}

const FONTE_ESTACOES = 'coordenadas das estações no ultimo_nivel_sc.json (Defesa Civil de SC), 07/10/2026'
const FONTE_TRACADO = 'vértice comum dos traçados OSM em data/rios/ (distância 0 m), medido em 07/10/2026'

export const VINCULOS: readonly VinculoDeTracado[] = [
  {
    tracado: 'itajai-do-sul',
    cidade: 'ituporanga',
    grupo: 'itajai-acu',
    estacao: 'DCSC-00039',
    inicio: [-49.582481, -27.482246],
    fim: [-49.64828, -27.21617],
    fimDescricao: 'a confluência com o Itajaí do Oeste em Rio do Sul, onde nasce o Itajaí-Açu',
    km: 39.2,
    fonte: `Ituporanga: codigo_dcsc DCSC-00039 no cadastro (a régua da cidade é a estação estadual). ` +
      `Início: ${FONTE_ESTACOES}. Fim: confluencia_cabeceiras do cadastro (Asthon, 04/09/2026) = ${FONTE_TRACADO}.`,
  },
  {
    tracado: 'hercilio',
    cidade: 'ibirama',
    grupo: 'itajai-acu',
    estacao: 'DCSC-00020',
    inicio: [-49.519951, -27.056997],
    fim: [-49.49557, -27.07881],
    fimDescricao: 'a confluência com o Itajaí-Açu',
    km: 4.6,
    fonte: `Ibirama: codigo_dcsc DCSC-00020, régua confirmada pela COMPDEC (C26, 05/10/2026). ` +
      `Início: ${FONTE_ESTACOES}. Fim: ${FONTE_TRACADO}.`,
  },
  {
    tracado: 'rio-dos-cedros',
    cidade: 'rio-dos-cedros',
    grupo: 'itajai-acu',
    estacao: 'DCSC-00011',
    inicio: [-49.272686, -26.740013],
    fim: [-49.275219, -26.822939],
    fimDescricao: 'a estação estadual Timbó 2 (DCSC-00034), a próxima rio abaixo',
    km: 15.6,
    fonte: `Rio dos Cedros: DCSC-00011, equivalência confirmada pela COMPDEC (C29, 07/10/2026). ` +
      `Início e fim: ${FONTE_ESTACOES}. O alcance pára na próxima estação, antes da confluência com o Benedito.`,
  },
  {
    tracado: 'trombudo',
    cidade: 'trombudo-central',
    grupo: 'itajai-acu',
    estacao: 'DCSC-00035',
    inicio: [-49.796768, -27.312159],
    fim: [-49.712193, -27.257998],
    fimDescricao: 'a estação estadual de Agronômica (DCSC-00001), a próxima rio abaixo',
    km: 17.2,
    fonte: `Trombudo Central: a cor do pino é a faixa estadual da própria DCSC-00035 (a equivalência com a ` +
      `régua municipal NÃO está confirmada; nenhuma conversão). Início e fim: ${FONTE_ESTACOES}.`,
  },
  {
    tracado: 'guabiruba',
    cidade: 'guabiruba',
    grupo: 'itajai-mirim',
    estacao: 'DCSC-00029',
    inicio: [-48.977394, -27.086782],
    fim: [-48.92983, -27.09784],
    fimDescricao: 'a confluência com o Itajaí-Mirim',
    km: 6.7,
    fonte: `Guabiruba: codigo_dcsc DCSC-00029 (ribeirão Guabiruba, zero local). Início: ${FONTE_ESTACOES}. ` +
      `Fim: ${FONTE_TRACADO}.`,
  },
]

/** Traçados que ficam sem cor, com o porquê. Mostrado no painel quando a pessoa toca no trecho cinza. */
export const SEM_VINCULO: Readonly<Record<string, string>> = {
  benedito:
    'A régua municipal de Timbó tem coordenada não confirmada, e a equivalência com a estação estadual ' +
    'DCSC-00023 também não está confirmada (decisão de 06/10/2026). Proximidade não basta para ligar a ' +
    'régua ao Benedito.',
  'luiz-alves': 'Não há régua cadastrada neste rio.',
  'ribeirao-taquaras': 'Não há régua cadastrada neste ribeirão.',
  'rio-rafael': 'Não há régua cadastrada neste rio.',
  'rio-rafael-braco-grande': 'Não há régua cadastrada neste rio.',
  'rio-rafael-braco-pequeno': 'Não há régua cadastrada neste rio.',
  'rio-conceicao': 'Não há régua cadastrada neste rio.',
  'ribeirao-murta':
    'As réguas de Itajaí neste ribeirão (DC-07 e DC-09) estão sem aviso automático: cota ainda não conferida ' +
    'contra a série (DC-07) e régua de estuário com oscilação de maré (DC-09). Sem respaldo, não colorem o ' +
    'ribeirão.',
  'ribeirao-canhanduba':
    'A régua de Itajaí neste ribeirão (DC-08) está sem aviso automático: a cota parece baixa demais e precisa ' +
    'ser conferida com a COMPDEC. Sem respaldo, não colore o ribeirão.',
}

export function vinculoDoTracado(tracado: string): VinculoDeTracado | null {
  return VINCULOS.find((v) => v.tracado === tracado) ?? null
}

/** Por que um traçado fora do tronco ficou cinza por falta de vínculo. */
export function motivoSemVinculo(tracado: string): string {
  return SEM_VINCULO[tracado] ?? 'Não há régua vinculada a este curso.'
}

/** O vínculo em que esta cidade colore um curso fora do tronco (para o painel dizer até onde vale). */
export function vinculoDaCidade(cidadeId: string): VinculoDeTracado | null {
  return VINCULOS.find((v) => v.cidade === cidadeId) ?? null
}

/** Distância em km entre dois [lon, lat] (equiretangular; basta na escala da bacia). */
export function kmEntre(a: LonLat, b: LonLat): number {
  const lat = (((a[1] + b[1]) / 2) * Math.PI) / 180
  return Math.hypot((a[0] - b[0]) * 111.32 * Math.cos(lat), (a[1] - b[1]) * 110.57)
}

/** Chave de uma aresta do traçado: linha `li`, do vértice `i - 1` ao vértice `i`, na ordem do arquivo. */
export function chaveDaAresta(li: number, i: number): string {
  return `${li}:${i}`
}

/** Tolerância para casar a estação e o fim com um vértice do traçado. As cinco de hoje casam a ≤ 67 m. */
export const TOLERANCIA_PONTO_KM = 0.3

/**
 * As arestas que a régua pode colorir: o caminho mais curto, NO traçado, do vértice da estação ao vértice do
 * fim. Sem caminho (segmento desconectado) ou com ponto longe do traçado, devolve `null` — e o curso fica
 * cinza, com o motivo. Nada acima da estação entra: o caminho vai da estação para o fim, não para os lados.
 */
export function arestasDoAlcance(
  coords: LonLat[][],
  inicio: LonLat,
  fim: LonLat,
  tolerancia = TOLERANCIA_PONTO_KM,
): { arestas: Set<string>; km: number } | null {
  const chave = (p: LonLat) => `${p[0].toFixed(6)},${p[1].toFixed(6)}`
  const adj = new Map<string, { para: string; km: number; aresta: string }[]>()
  const pos = new Map<string, LonLat>()
  coords.forEach((linha, li) => {
    for (let i = 1; i < linha.length; i++) {
      const a = chave(linha[i - 1]!)
      const b = chave(linha[i]!)
      const km = kmEntre(linha[i - 1]!, linha[i]!)
      const aresta = chaveDaAresta(li, i)
      pos.set(a, linha[i - 1]!)
      pos.set(b, linha[i]!)
      if (!adj.has(a)) adj.set(a, [])
      if (!adj.has(b)) adj.set(b, [])
      adj.get(a)!.push({ para: b, km, aresta })
      adj.get(b)!.push({ para: a, km, aresta })
    }
  })
  const maisPerto = (alvo: LonLat): string | null => {
    let melhor: string | null = null
    let d = tolerancia
    for (const [k, p] of pos) {
      const dd = kmEntre(p, alvo)
      if (dd <= d) {
        d = dd
        melhor = k
      }
    }
    return melhor
  }
  const s = maisPerto(inicio)
  const f = maisPerto(fim)
  if (!s || !f) return null

  // Dijkstra simples: os traçados têm poucos milhares de vértices.
  const dist = new Map<string, number>([[s, 0]])
  const veio = new Map<string, { de: string; aresta: string }>()
  const abertos = new Set<string>([s])
  while (abertos.size > 0) {
    let u: string | null = null
    for (const k of abertos) if (u === null || dist.get(k)! < dist.get(u)!) u = k
    abertos.delete(u!)
    if (u === f) break
    for (const { para, km, aresta } of adj.get(u!) ?? []) {
      const nd = dist.get(u!)! + km
      if (nd < (dist.get(para) ?? Infinity)) {
        dist.set(para, nd)
        veio.set(para, { de: u!, aresta })
        abertos.add(para)
      }
    }
  }
  if (!dist.has(f)) return null
  const arestas = new Set<string>()
  for (let k = f; k !== s; k = veio.get(k)!.de) arestas.add(veio.get(k)!.aresta)
  return { arestas, km: dist.get(f)! }
}

/** "No mapa, esta régua colore só …": o limite da representação, dito no painel da cidade. */
export function textoDoAlcance(v: VinculoDeTracado, nomeDoCurso: string): string {
  const km = v.km.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
  return `No mapa, a cor desta régua vale só para o ${nomeDoCurso}, da estação ${v.estacao} até ` +
    `${v.fimDescricao} (${km} km). Não vale para o rio acima da estação nem para o rio que recebe a água.`
}

/** Por que um trecho ficou cinza mesmo com cor no pino da cidade. */
export type MotivoDoTrecho = 'sem-vinculo' | 'fora-do-alcance' | 'acima-da-primeira-regua'

export function textoDoTrechoCinza(motivo: MotivoDoTrecho, tracado: string): string {
  if (motivo === 'sem-vinculo') return motivoSemVinculo(tracado)
  if (motivo === 'acima-da-primeira-regua') {
    return 'Este trecho fica rio acima da primeira régua do rio. A régua mede o rio a partir dela; ' +
      'o que corre acima não tem medição no mapa.'
  }
  const v = vinculoDoTracado(tracado)
  return v
    ? `Fora do trecho que a régua ${v.estacao} representa (da estação até ${v.fimDescricao}). Sem medição ` +
      'aqui, o trecho fica sem cor.'
    : motivoSemVinculo(tracado)
}

/**
 * Quanto rio acima da primeira âncora uma aresta do TRONCO pode ficar e ainda receber a cor dela. A projeção
 * na espinha é uma reta entre réguas: um meandro logo abaixo da régua pode recuar um pouco nela. 0,5 km
 * absorve isso; acima disso o trecho é do rio que a régua não mede (o Itajaí do Oeste acima de Taió, 71 km,
 * com a Barragem Oeste; o Mirim acima de Vidal Ramos, 25 km — medidos em 07/10/2026).
 */
export const FOLGA_ACIMA_DA_REGUA_KM = 0.5

/**
 * Quantos km rio ACIMA do ponto `a` (na direção oposta a `b`) o ponto `p` fica, pela projeção na reta a→b.
 * Negativo ou zero = não está acima.
 */
export function kmAcimaDe(p: LonLat, a: LonLat, b: LonLat): number {
  const lat = (a[1] * Math.PI) / 180
  const kx = 111.32 * Math.cos(lat)
  const ky = 110.57
  const abx = (b[0] - a[0]) * kx
  const aby = (b[1] - a[1]) * ky
  const len = Math.hypot(abx, aby)
  if (len === 0) return 0
  const apx = (p[0] - a[0]) * kx
  const apy = (p[1] - a[1]) * ky
  return -(apx * abx + apy * aby) / len
}

/**
 * Um traçado baixado → o que o motor desenha. É a montagem do Monitor, aqui para o teste usar a MESMA:
 *  - tronco: as cidades do cadastro pela espinha, com o eixo, como sempre;
 *  - fora do tronco, com vínculo e caminho: só a cidade do vínculo, no grupo dela, e só as arestas do alcance;
 *  - fora do tronco sem vínculo, ou sem caminho (desconectado, estação longe): cinza, `semVinculo`.
 */
export function rioParaCena(
  b: { rioId: string; coords: LonLat[][] },
  ehTronco: boolean,
  cidadesDoRio: (rioId: string) => Cidade[],
  eixoDoRio: (rioId: string) => string[] | undefined,
): RioParaCena {
  if (ehTronco) {
    return { rioId: b.rioId, coords: b.coords, cidades: cidadesDoRio(b.rioId), eixo: eixoDoRio(b.rioId) }
  }
  const v = vinculoDoTracado(b.rioId)
  const cidade = v ? cidadesDoRio(v.grupo).find((c) => c.id === v.cidade) ?? null : null
  const alcance = v && cidade ? arestasDoAlcance(b.coords, v.inicio, v.fim) : null
  if (v && cidade && alcance) {
    return {
      rioId: b.rioId,
      coords: b.coords,
      cidades: [cidade],
      grupo: v.grupo,
      eixo: [cidade.id],
      arestasAutorizadas: alcance.arestas,
    }
  }
  return { rioId: b.rioId, coords: b.coords, cidades: [], semVinculo: true }
}
