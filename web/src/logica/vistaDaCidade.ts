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
