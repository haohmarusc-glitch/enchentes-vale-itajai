import { VISTA_INTEIRA, type Vista } from './mapaCanvas'

/**
 * Abrir o Monitor JÁ ENQUADRADO numa cidade.
 *
 * POR QUE REAPROVEITAR O MONITOR, e não fazer uma segunda tela: o mapa ao vivo
 * decide cor por faixa, velocidade por nível e o que cada régua pode afirmar.
 * Duas implementações disso divergem com o tempo, e o dia em que divergirem é
 * o dia em que a mesma cidade aparece verde numa tela e laranja na outra. Aqui
 * é o MESMO mapa, só com o enquadramento inicial em outro lugar — nada do que
 * ele afirma muda por causa do zoom.
 *
 * O que este módulo NÃO faz: inventar posição. Cidade sem coordenada no
 * cadastro devolve `null`, e a tela cai na bacia inteira dizendo por quê —
 * mapa em branco, num aplicativo de enchente, é pior que mapa sem zoom.
 */

/**
 * Largura que a tela deve mostrar, em km, ao abrir numa cidade.
 *
 * 24 km não é gosto: é para caber a cidade e os VIZINHOS de montante e jusante
 * na mesma imagem. Quem abre o monitor de Gaspar precisa ver Blumenau acima e
 * Ilhota abaixo — a cheia vem de cima, e enquadrar só o município esconderia
 * exatamente o trecho de onde a água está chegando. Os trechos do tronco medem
 * entre 8 e 30 km, então 24 km mostra ao menos um vizinho em quase todos.
 */
export const KM_NA_TELA = 24

/** Grau de longitude em km no paralelo 27 (o cosseno encurta o leste-oeste). */
const KM_POR_GRAU_LON = 111.32 * Math.cos((27 * Math.PI) / 180)

export interface Limites {
  minLon: number
  maxLon: number
  minLat: number
  maxLat: number
}

/**
 * O zoom que faz a tela mostrar aproximadamente `kmAlvo` de largura.
 *
 * O zoom do mapa é RELATIVO aos limites da bacia (`aplicarVista` divide o vão
 * por ele), então o número depende do tamanho da bacia — calcular, e não
 * cravar uma constante, é o que mantém o enquadramento igual se a bacia mudar.
 * Nunca devolve menos que 1: abaixo disso o mapa mostraria além da bacia.
 */
export function zoomParaKm(limites: Limites, kmAlvo: number = KM_NA_TELA): number {
  const larguraKm = (limites.maxLon - limites.minLon) * KM_POR_GRAU_LON
  if (!Number.isFinite(larguraKm) || larguraKm <= 0 || !Number.isFinite(kmAlvo) || kmAlvo <= 0) {
    return 1
  }
  return Math.max(1, larguraKm / kmAlvo)
}

/**
 * A vista centrada na cidade — ou `null` quando não dá para saber onde ela é.
 *
 * `coordenadas` vem do cadastro no formato [lat, lon].
 */
export function vistaDaCidade(
  coordenadas: readonly number[] | null | undefined,
  limites: Limites,
  kmAlvo: number = KM_NA_TELA,
): Vista | null {
  if (!coordenadas || coordenadas.length !== 2) return null
  const [lat, lon] = coordenadas
  if (typeof lat !== 'number' || typeof lon !== 'number') return null
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null
  return { zoom: zoomParaKm(limites, kmAlvo), centroLon: lon, centroLat: lat }
}

/** Grau de latitude em km — constante, ao contrário do de longitude. */
const KM_POR_GRAU_LAT = 110.57

/**
 * Folga em volta do que precisa caber. Um ponto exatamente na borda fica
 * metade fora do desenho e colado no rótulo do canto; 20% o traz para dentro.
 */
export const MARGEM_ENQUADRAMENTO = 1.2

/** O mínimo para entrar no enquadramento: onde o ponto fica. */
export interface PontoNoMapa {
  lat: number
  lon: number
}

/**
 * A vista da cidade que CABE as réguas dela — e não só o pino.
 *
 * POR QUE EXISTE (06/09/2026). O enquadramento por cidade era uma janela fixa
 * de 24 km centrada no PINO. Medido contra o cadastro: as onze réguas de Itajaí
 * se espalham por **20,8 x 17,6 km**, e a DC-10 (Bairro Limoeiro) fica a
 * **24,2 km do pino** — ou seja, FORA da janela. Abrir o monitor de Itajaí
 * escondia uma das onze réguas da própria cidade, justamente a de um bairro
 * afastado, e não havia nada na tela dizendo que faltava uma.
 *
 * Uma tela chamada "Itajaí" que não mostra a régua do Limoeiro não está
 * apertada: está errada. E o erro cai para o lado ruim — quem mora lá abre a
 * cidade dele e não encontra o número que existe.
 *
 * O mínimo de `KM_NA_TELA` continua valendo, pelo motivo original (caber os
 * vizinhos de montante e jusante). O que muda é que ele passa a ser PISO, não
 * teto: cidade cujas réguas se espalham mais que isso abre mais aberta.
 *
 * `proporcaoTela` é altura/largura do canvas em pixels. Sem ela o cálculo só
 * garantiria a largura, e numa tela deitada (16:9 -> 0,56) uma dispersão de
 * 17,6 km de norte a sul continuaria cortada mesmo com 24 km de leste a oeste.
 */
export function vistaQueCabeAsReguas(
  coordenadas: readonly number[] | null | undefined,
  reguas: readonly PontoNoMapa[],
  limites: Limites,
  proporcaoTela: number,
  kmMinimo: number = KM_NA_TELA,
): Vista | null {
  const pontos: PontoNoMapa[] = []
  const lat = coordenadas?.length === 2 ? coordenadas[0] : undefined
  const lon = coordenadas?.length === 2 ? coordenadas[1] : undefined
  if (typeof lat === 'number' && typeof lon === 'number' && Number.isFinite(lat) && Number.isFinite(lon)) {
    pontos.push({ lat, lon })
  }
  for (const r of reguas) {
    if (Number.isFinite(r?.lat) && Number.isFinite(r?.lon)) pontos.push({ lat: r.lat, lon: r.lon })
  }
  // Sem NENHUM ponto não se enquadra em lugar nenhum: devolve null e a tela cai
  // na bacia inteira. Inventar um centro seria pior que não ter zoom.
  if (pontos.length === 0) return null

  const lats = pontos.map((p) => p.lat)
  const lons = pontos.map((p) => p.lon)
  const minLat = Math.min(...lats)
  const maxLat = Math.max(...lats)
  const minLon = Math.min(...lons)
  const maxLon = Math.max(...lons)

  const larguraKm = (maxLon - minLon) * KM_POR_GRAU_LON
  const alturaKm = (maxLat - minLat) * KM_POR_GRAU_LAT
  const prop = Number.isFinite(proporcaoTela) && proporcaoTela > 0 ? proporcaoTela : 1
  // A tela mostra `alturaKm = larguraKm * prop`. Para caber a dispersão
  // norte-sul, a LARGURA precisa ser ao menos a altura dividida pela proporção.
  const precisa = Math.max(larguraKm, alturaKm / prop) * MARGEM_ENQUADRAMENTO
  const kmAlvo = Math.max(kmMinimo, precisa)

  return vistaDaCidade([(minLat + maxLat) / 2, (minLon + maxLon) / 2], limites, kmAlvo)
}

/**
 * Quantos km de largura a tela mostra num dado zoom — o inverso de `zoomParaKm`.
 *
 * Serve para decidir o que só pode aparecer de perto (as cotas de rua: de longe
 * viram nuvem, e nuvem lê-se como mancha).
 */
export function kmDaVista(limites: Limites, zoom: number): number {
  const larguraKm = (limites.maxLon - limites.minLon) * KM_POR_GRAU_LON
  if (!Number.isFinite(larguraKm) || larguraKm <= 0) return Number.NaN
  return larguraKm / Math.max(1, Number.isFinite(zoom) ? zoom : 1)
}

/** A vista de abertura: a da cidade quando ela existe, a bacia inteira quando não. */
export function vistaInicial(
  coordenadas: readonly number[] | null | undefined,
  limites: Limites,
  kmAlvo: number = KM_NA_TELA,
): Vista {
  return vistaDaCidade(coordenadas, limites, kmAlvo) ?? VISTA_INTEIRA
}
