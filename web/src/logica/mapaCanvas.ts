/**
 * Geometria pura do mapa-canvas do rio — a parte que dá para testar sem DOM.
 *
 * O render (MapaRios.tsx) desenha num <canvas>: o traçado real do OSM pintado
 * por trecho na cor da FAIXA da cidade a montante (a mesma regra do diagrama
 * linear), com a correnteza animada descendo no sentido do rio. Aqui ficam as
 * contas que decidem ONDE cada coisa cai — projeção, encaixe da cidade no rio,
 * a que trecho um ponto pertence e para que lado é "jusante" — para o
 * componente só orquestrar rAF e pixels.
 *
 * REGRAS que este módulo carrega do projeto (não são detalhe de desenho):
 *  - cor = faixa da cidade, nunca metro entre cidades (quem dá a faixa é o
 *    componente, via faixaDaCidade; aqui só se decide QUAL cidade pinta o trecho);
 *  - sem cidade que pinte (nascente, ponta solta) → trecho cinza, sem correnteza:
 *    não sabemos o estado ali, então não se anima uma água que não se conhece
 *    (VEL_FAIXA['sem-dado'] = 0).
 */
import type { Faixa } from './tempoReal'

export type LonLat = [number, number]

/**
 * Longitude encolhe com a latitude: perto de 27° S um grau de longitude vale
 * ~0,89 grau de latitude. Sem corrigir, o mapa entortaria os trechos
 * leste–oeste (a maior parte do Vale) e o "mais próximo" erraria. Uma escala só,
 * para projeção e para distância — nada disso vira número na tela.
 */
export const K_LON = Math.cos((27 * Math.PI) / 180)

export function dist2(a: LonLat, b: LonLat): number {
  return ((a[0] - b[0]) * K_LON) ** 2 + (a[1] - b[1]) ** 2
}

/** Distância em QUILÔMETROS entre duas coordenadas, na mesma escala do resto. */
export function kmEntre(a: LonLat, b: LonLat): number {
  return Math.sqrt(dist2(a, b)) * 111.32
}

/** Ponto do traçado mais próximo de uma coordenada — encaixa o marcador no rio. */
export function maisProximoNoRio(coords: LonLat[][], alvo: LonLat): LonLat | null {
  let melhor: LonLat | null = null
  let dist = Infinity
  for (const linha of coords) {
    for (const p of linha) {
      const d = dist2(p, alvo)
      if (d < dist) {
        dist = d
        melhor = p
      }
    }
  }
  return melhor
}

/**
 * Distância² de um ponto ao segmento a–b e onde caiu (t em 0..1). A base para
 * projetar cada pedaço do rio na "espinha" das cidades em ordem.
 */
export function projetarNoSegmento(
  p: LonLat,
  a: LonLat,
  b: LonLat,
): { dist2: number; t: number } {
  const abx = (b[0] - a[0]) * K_LON
  const aby = b[1] - a[1]
  const apx = (p[0] - a[0]) * K_LON
  const apy = p[1] - a[1]
  const len2 = abx * abx + aby * aby
  const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, (apx * abx + apy * aby) / len2))
  const cx = abx * t - apx
  const cy = aby * t - apy
  return { dist2: cx * cx + cy * cy, t }
}

/**
 * Em qual trecho entre cidades consecutivas este ponto do rio cai. A espinha são
 * os pontos das cidades (já encaixados no rio), na ordem montante→jusante.
 * Devolve o índice da cidade A MONTANTE do trecho — é ela quem dá a cor, como no
 * diagrama linear.
 */
export function trechoDoPonto(espinha: LonLat[], p: LonLat): number {
  if (espinha.length < 2) return 0
  let melhor = 0
  let dist = Infinity
  for (let i = 0; i < espinha.length - 1; i++) {
    const d = projetarNoSegmento(p, espinha[i]!, espinha[i + 1]!).dist2
    if (d < dist) {
      dist = d
      melhor = i
    }
  }
  return melhor
}

/**
 * "Progresso" montante→jusante de um ponto, medido na espinha das cidades: 0 na
 * nascente, cresce até a foz. Serve para saber para que lado corre a água num
 * pedaço do traçado — os ways do OSM não vêm todos orientados no sentido do rio,
 * então a correnteza é orientada por ESTE número, não pela ordem do arquivo.
 */
export function progressoNaEspinha(
  espinha: LonLat[],
  cumEspinha: number[],
  p: LonLat,
): number {
  if (espinha.length < 2) return 0
  let melhor = 0
  let dist = Infinity
  let tMelhor = 0
  for (let i = 0; i < espinha.length - 1; i++) {
    const { dist2: d, t } = projetarNoSegmento(p, espinha[i]!, espinha[i + 1]!)
    if (d < dist) {
      dist = d
      melhor = i
      tMelhor = t
    }
  }
  const base = cumEspinha[melhor]!
  const passo = cumEspinha[melhor + 1]! - base
  return base + tMelhor * passo
}

/** Comprimento acumulado (em unidades geográficas corrigidas) ao longo da espinha. */
export function acumuladoEspinha(espinha: LonLat[]): number[] {
  const cum = [0]
  for (let i = 1; i < espinha.length; i++) {
    cum.push(cum[i - 1]! + Math.sqrt(dist2(espinha[i - 1]!, espinha[i]!)))
  }
  return cum
}

/**
 * Correnteza por faixa. VELOCIDADE do fluxo animado cresce com a gravidade —
 * água mais rápida onde o rio está mais alto —, então a animação SIGNIFICA o
 * nível real, não é enfeite. `sem-dado` e `normal` extremos:
 *  - `sem-dado` = 0: cinza não corre. Não sabemos o estado ali; animar seria
 *    fingir uma água conhecida. É a honestidade da tela virada em pixel.
 *  - `normal` corre devagar: rio baixo tem correnteza, só mansa.
 */
export const VEL_FAIXA: Record<Faixa, number> = {
  normal: 0.35,
  // Entre normal e atenção, como a fase é. A correnteza SIGNIFICA o nível:
  // acelerar mais aqui diria um perigo que a COMPDEC não declarou.
  monitoramento: 0.45,
  atencao: 0.6,
  alerta: 0.95,
  inundacao: 1.35,
  emergencia: 1.35,
  'sem-dado': 0,
  varias: 0.5,
}

/** Largura relativa do traço por faixa — sutil, reforça a cor sem gritar sozinha. */
export const LARGURA_FAIXA: Record<Faixa, number> = {
  normal: 0.85,
  monitoramento: 0.92,
  atencao: 1,
  alerta: 1.15,
  inundacao: 1.4,
  emergencia: 1.4,
  'sem-dado': 0.7,
  varias: 1,
}

/**
 * Posições (distância ao longo do trecho, em px) onde desenhar as setas da
 * correnteza, dado o tamanho do trecho, a velocidade da faixa, o tempo e o
 * espaçamento. As setas ANDAM: a fase desliza com o tempo × velocidade, então
 * quadros diferentes dão posições diferentes — é o movimento que a tela mostra.
 * Faixa parada (velocidade 0, o cinza) ou trecho curto demais → nenhuma seta.
 */
export function posicoesCorrenteza(
  total: number,
  vel: number,
  tempo: number,
  espaco: number,
  velPx: number,
): number[] {
  // Trecho curtíssimo (< 6 px) não comporta seta; faixa parada (cinza) não
  // corre. Fora isso, SEMPRE ao menos uma seta: os trechos coloridos, partidos
  // por way do OSM e por faixa, são muitas vezes menores que o espaçamento —
  // exigir `total >= espaco` deixava a maioria sem seta nenhuma, e o rio parado.
  if (vel <= 0 || total < 6 || espaco <= 0) return []
  const avanco = tempo * vel * velPx
  const desloc = ((avanco % espaco) + espaco) % espaco
  const saida: number[] = []
  for (let pos = desloc; pos < total; pos += espaco) saida.push(pos)
  if (saida.length === 0) saida.push(((avanco % total) + total) % total)
  return saida
}

export interface Enquadramento {
  minLon: number
  maxLat: number
  cosLat: number
  escala: number
  deslocX: number
  deslocY: number
}

/**
 * Enquadra os limites geográficos na área de desenho (equiretangular, com a
 * longitude corrigida pela latitude para não esticar). Centraliza e deixa uma
 * margem. Devolve os fatores que `projetar` usa.
 */
export function enquadrar(
  limites: { minLon: number; maxLon: number; minLat: number; maxLat: number },
  largura: number,
  altura: number,
  margem: number,
): Enquadramento {
  const cosLat = Math.cos(((limites.minLat + limites.maxLat) / 2) * (Math.PI / 180))
  const geoW = Math.max(1e-9, (limites.maxLon - limites.minLon) * cosLat)
  const geoH = Math.max(1e-9, limites.maxLat - limites.minLat)
  const escala = Math.min((largura - 2 * margem) / geoW, (altura - 2 * margem) / geoH)
  const usadoW = geoW * escala
  const usadoH = geoH * escala
  return {
    minLon: limites.minLon,
    maxLat: limites.maxLat,
    cosLat,
    escala,
    deslocX: margem + (largura - 2 * margem - usadoW) / 2,
    deslocY: margem + (altura - 2 * margem - usadoH) / 2,
  }
}

/** [lon,lat] → [x,y] em pixels, com o y invertido (norte para cima). */
export function projetar(e: Enquadramento, p: LonLat): [number, number] {
  return [
    e.deslocX + (p[0] - e.minLon) * e.cosLat * e.escala,
    e.deslocY + (e.maxLat - p[1]) * e.escala,
  ]
}

/** Limites geográficos de um conjunto de pontos, ou null se vazio. */
export function limitesDe(
  pontos: LonLat[],
): { minLon: number; maxLon: number; minLat: number; maxLat: number } | null {
  if (pontos.length === 0) return null
  let minLon = Infinity
  let maxLon = -Infinity
  let minLat = Infinity
  let maxLat = -Infinity
  for (const [lon, lat] of pontos) {
    if (lon < minLon) minLon = lon
    if (lon > maxLon) maxLon = lon
    if (lat < minLat) minLat = lat
    if (lat > maxLat) maxLat = lat
  }
  return { minLon, maxLon, minLat, maxLat }
}

/**
 * Onde o mapa está olhando: quanto de zoom e em torno de que ponto.
 *
 * `zoom: 1` é a bacia inteira, que é como o Monitor sempre abriu. Acima disso a
 * janela geográfica encolhe em torno de `centro` — e o traçado, os pinos e os
 * tiles do fundo crescem JUNTOS, porque tudo sai da mesma projeção. É a
 * diferença entre isto e a lupa do navegador, que estica o bitmap: ali o rio
 * fica borrado e os rótulos saem da tela; aqui o desenho é refeito.
 */
export interface Vista {
  zoom: number
  centroLon: number
  centroLat: number
}

/** A bacia inteira: o que o mapa mostra antes de alguém tocar nele. */
export const VISTA_INTEIRA: Vista = { zoom: 1, centroLon: NaN, centroLat: NaN }

/**
 * Recorta os limites da bacia conforme a vista.
 *
 * O centro é preso DENTRO dos limites da bacia: sem isso, um arrasto longo
 * levaria a tela para o mar aberto ou para o meio de Santa Catarina, e o mapa
 * ficaria vazio sem dizer por quê — num aplicativo de enchente, tela vazia é
 * pior que tela sem zoom.
 */
export function aplicarVista(
  limites: { minLon: number; maxLon: number; minLat: number; maxLat: number },
  vista: Vista,
): { minLon: number; maxLon: number; minLat: number; maxLat: number } {
  const zoom = Math.max(1, vista.zoom)
  if (zoom === 1) return limites
  const meioLon = (limites.maxLon - limites.minLon) / 2 / zoom
  const meioLat = (limites.maxLat - limites.minLat) / 2 / zoom
  const centroLon = Number.isFinite(vista.centroLon)
    ? Math.min(limites.maxLon, Math.max(limites.minLon, vista.centroLon))
    : (limites.minLon + limites.maxLon) / 2
  const centroLat = Number.isFinite(vista.centroLat)
    ? Math.min(limites.maxLat, Math.max(limites.minLat, vista.centroLat))
    : (limites.minLat + limites.maxLat) / 2
  return {
    minLon: centroLon - meioLon,
    maxLon: centroLon + meioLon,
    minLat: centroLat - meioLat,
    maxLat: centroLat + meioLat,
  }
}

/** [x,y] em pixels → [lon,lat]. O inverso de `projetar`, para saber onde o dedo tocou. */
export function desprojetar(e: Enquadramento, x: number, y: number): LonLat {
  return [
    e.minLon + (x - e.deslocX) / (e.cosLat * e.escala),
    e.maxLat - (y - e.deslocY) / e.escala,
  ]
}
