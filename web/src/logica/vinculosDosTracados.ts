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

/**
 * Vínculo traçado × RÉGUA de uma cidade (decisão do Jefferson, 08/10/2026: "ribeirões com cota devem pintar
 * conforme cota"). Itajaí tem onze réguas com coordenada própria, e as de ribeirão (Murta, Canhanduba) não são
 * a régua da cidade — `VINCULOS` só sabe cidade, e o Canhanduba ficava cinza ao lado do pino verde da DC-08.
 *
 * A cor do curso é a MESMA decisão do pino da régua (`reguasNoMapa`: cota de acionamento, leitura fresca, sem
 * maré): este módulo continua sem calcular faixa. Régua sem cor (maré, sem cota, leitura velha) deixa o curso
 * cinza com o motivo dela. O curso fica PARADO: correnteza animada é outra decisão (`afluenteNaoCorre.test.ts`).
 * O alcance segue a regra de sempre: da régua até a foz (ou o fim do traçado), nunca o ribeirão acima dela.
 */
export interface VinculoDeRegua {
  /** O traçado (`data/rios/<id>.geojson`). */
  tracado: string
  /** A cidade dona da régua (o painel e o enquadramento). */
  cidade: string
  /** O código da régua no cadastro (`estacoes_tempo_real[].codigo`) — o mesmo de `ReguaNoMapa.codigo`. */
  regua: string
  /** Onde a régua está ([lon, lat]): o começo do alcance. */
  inicio: LonLat
  /** O fim do alcance ([lon, lat]). */
  fim: LonLat
  /** O que é o fim, como a pessoa lê. */
  fimDescricao: string
  /** O comprimento medido do alcance no traçado, para o texto e o teste. */
  km: number
  /** De onde vêm o vínculo e os dois pontos. */
  fonte: string
}

export const VINCULOS_DE_REGUA: readonly VinculoDeRegua[] = [
  {
    tracado: 'ribeirao-canhanduba',
    cidade: 'itajai',
    regua: 'DC-08',
    inicio: [-48.711948, -26.979694],
    fim: [-48.694898, -26.939465],
    fimDescricao: 'o fim do traçado do ribeirão, 0,6 km antes do Itajaí-Mirim',
    km: 6.3,
    fonte: 'DC-08 "Ribeirão da Canhanduba - Rio do Meio": coordenada do cadastro (portal da Defesa Civil de Itajaí), ' +
      'a 13 m do traçado; cota de atenção provisória de 1,70 m (#520, 08/10/2026). Fim: o último vértice do ' +
      'traçado OSM rio abaixo, medido em 08/10/2026 (o traçado pára 574 m antes do Mirim; esses 574 m ficam sem ' +
      'linha e sem cor — nada é completado por aproximação, decisão do Jefferson de 08/10/2026). Os 11,5 km acima ' +
      'da régua ficam cinza: a régua não mede o que corre acima dela.',
  },
]

export function vinculoDeReguaDoTracado(tracado: string): VinculoDeRegua | null {
  return VINCULOS_DE_REGUA.find((v) => v.tracado === tracado) ?? null
}

/** O vínculo em que esta régua colore um curso (para o painel da régua dizer até onde vale). */
export function vinculoDaRegua(codigo: string): VinculoDeRegua | null {
  return VINCULOS_DE_REGUA.find((v) => v.regua === codigo) ?? null
}

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
    'ribeirão. (O traçado já é contínuo da DC-07 à foz desde 08/10/2026 — docs/VAO-MURTA.md; o trecho do futuro ' +
    'vínculo da DC-07, até a DC-09, está delimitado lá e só entra com a decisão sobre a cota.)',
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
/** O traçado como grafo: vértices (chave por coordenada) e arestas com o comprimento em km. */
function grafoDoTracado(coords: LonLat[][]): {
  adj: Map<string, { para: string; km: number; aresta: string }[]>
  pos: Map<string, LonLat>
} {
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
  return { adj, pos }
}

/** O vértice mais perto de `alvo` a até `tolerancia` km, entre os que `aceita` (todos, por padrão). */
function verticeMaisPerto(
  pos: Map<string, LonLat>,
  alvo: LonLat,
  tolerancia: number,
  aceita: (k: string) => boolean = () => true,
): string | null {
  let melhor: string | null = null
  let d = tolerancia
  for (const [k, p] of pos) {
    if (!aceita(k)) continue
    const dd = kmEntre(p, alvo)
    if (dd <= d) {
      d = dd
      melhor = k
    }
  }
  return melhor
}

/** Distância em km, pelo traçado, de cada vértice alcançável até `origem` (Dijkstra; poucos milhares de vértices). */
function distanciasNoTracado(
  adj: Map<string, { para: string; km: number; aresta: string }[]>,
  origem: string,
  parar?: string,
): { dist: Map<string, number>; veio: Map<string, { de: string; aresta: string }> } {
  const dist = new Map<string, number>([[origem, 0]])
  const veio = new Map<string, { de: string; aresta: string }>()
  const abertos = new Set<string>([origem])
  while (abertos.size > 0) {
    let u: string | null = null
    for (const k of abertos) if (u === null || dist.get(k)! < dist.get(u)!) u = k
    abertos.delete(u!)
    if (u === parar) break
    for (const { para, km, aresta } of adj.get(u!) ?? []) {
      const nd = dist.get(u!)! + km
      if (nd < (dist.get(para) ?? Infinity)) {
        dist.set(para, nd)
        veio.set(para, { de: u!, aresta })
        abertos.add(para)
      }
    }
  }
  return { dist, veio }
}

/**
 * As arestas do traçado que ficam a JUSANTE de `ponto`, pelo caminho do rio até `foz` (08/10/2026).
 *
 * Serve à referência da DC-11 no Açu: a cor valia para os trechos cuja PROJEÇÃO na reta entre os pinos de
 * Ilhota e Itajaí caía depois da régua, e a Volta de Cima, logo abaixo da DC-11, volta para trás nessa reta —
 * 2,86 km de rio ao longo da Rua Santa Regina ficavam cinza com a régua em atenção. Aqui "a jusante" é medido
 * NO traçado: uma aresta entra quando os dois vértices dela estão, pelo canal, mais perto da foz do que o
 * vértice da régua. Braços paralelos (ilhas) entram pelos dois lados; o rio acima da régua, não.
 *
 * O vértice da régua é o mais perto de `ponto` (até `tolerancia` km) entre os que alcançam a foz: um pedaço
 * solto do traçado não serve de referência. Sem vértice ou sem foz, devolve `null` (nenhuma aresta pintada).
 */
export function arestasAJusanteDe(
  coords: LonLat[][],
  ponto: LonLat,
  foz: LonLat,
  tolerancia = TOLERANCIA_PONTO_KM,
): Set<string> | null {
  const { adj, pos } = grafoDoTracado(coords)
  const f = verticeMaisPerto(pos, foz, tolerancia)
  if (!f) return null
  const { dist } = distanciasNoTracado(adj, f)
  const s = verticeMaisPerto(pos, ponto, tolerancia, (k) => dist.has(k))
  if (!s) return null
  const limite = dist.get(s)! + 1e-9
  const arestas = new Set<string>()
  for (const [a, vizinhos] of adj) {
    const da = dist.get(a)
    if (da === undefined || da > limite) continue
    for (const { para, aresta } of vizinhos) {
      const db = dist.get(para)
      if (db !== undefined && db <= limite) arestas.add(aresta)
    }
  }
  return arestas
}

export function arestasDoAlcance(
  coords: LonLat[][],
  inicio: LonLat,
  fim: LonLat,
  tolerancia = TOLERANCIA_PONTO_KM,
): { arestas: Set<string>; km: number } | null {
  const { adj, pos } = grafoDoTracado(coords)
  const s = verticeMaisPerto(pos, inicio, tolerancia)
  const f = verticeMaisPerto(pos, fim, tolerancia)
  if (!s || !f) return null

  const { dist, veio } = distanciasNoTracado(adj, s, f)
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

/** "No mapa, a cor desta régua vale só …": o limite da representação, dito no painel da RÉGUA (08/10/2026). */
export function textoDoAlcanceDaRegua(v: VinculoDeRegua, nomeDoCurso: string): string {
  const km = v.km.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
  return `No mapa, a cor desta régua vale só para o ${nomeDoCurso}, da régua até ${v.fimDescricao} (${km} km). ` +
    'É a classificação medida NA RÉGUA, aplicada ao trecho vinculado: não é medição em cada ponto do curso nem ' +
    'mancha de inundação. O curso fica parado (a correnteza animada é outra decisão). Não vale para o ribeirão ' +
    'acima da régua nem para o rio que recebe a água.'
}

/**
 * Por que um trecho ficou cinza mesmo com cor no pino da cidade. `regua-sem-cor` (08/10/2026): o curso tem
 * régua vinculada, mas a régua está sem cor agora (maré, sem cota, sem leitura, leitura velha, reprodução).
 */
export type MotivoDoTrecho = 'sem-vinculo' | 'fora-do-alcance' | 'acima-da-primeira-regua' | 'regua-sem-cor'

export function textoDoTrechoCinza(motivo: MotivoDoTrecho, tracado: string, detalhe?: string): string {
  if (motivo === 'sem-vinculo') return motivoSemVinculo(tracado)
  if (motivo === 'acima-da-primeira-regua') {
    return 'Este trecho fica rio acima da primeira régua do rio. A régua mede o rio a partir dela; ' +
      'o que corre acima não tem medição no mapa.'
  }
  if (motivo === 'regua-sem-cor') {
    const vr = vinculoDeReguaDoTracado(tracado)
    const quem = vr ? `a régua ${vr.regua}` : 'a régua vinculada'
    return `A cor deste curso é a de ${quem}, que agora está sem cor${detalhe ? ` — ${detalhe}` : '.'}`
  }
  const v = vinculoDoTracado(tracado)
  if (v) {
    return `Fora do trecho que a régua ${v.estacao} representa (da estação até ${v.fimDescricao}). Sem medição ` +
      'aqui, o trecho fica sem cor.'
  }
  const vr = vinculoDeReguaDoTracado(tracado)
  if (vr) {
    return `Fora do trecho que a régua ${vr.regua} representa (da régua até ${vr.fimDescricao}). Sem medição ` +
      'aqui, o trecho fica sem cor.'
  }
  return motivoSemVinculo(tracado)
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
 *  - fora do tronco com vínculo de RÉGUA (08/10/2026): sem cidade; a cor é a do pino da régua, nas arestas do
 *    alcance, e o motor a lê em `reguaVinculada`;
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
  const vr = vinculoDeReguaDoTracado(b.rioId)
  const alcanceDaRegua = vr ? arestasDoAlcance(b.coords, vr.inicio, vr.fim) : null
  if (vr && alcanceDaRegua) {
    return {
      rioId: b.rioId,
      coords: b.coords,
      cidades: [],
      eixo: [],
      reguaVinculada: { codigo: vr.regua, cidade: vr.cidade },
      arestasAutorizadas: alcanceDaRegua.arestas,
    }
  }
  return { rioId: b.rioId, coords: b.coords, cidades: [], semVinculo: true }
}
