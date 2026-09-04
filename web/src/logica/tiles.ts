/**
 * Fundo de mapa (tiles XYZ) para o canvas do Monitor — a geometria, sem DOM.
 *
 * O Monitor não é Leaflet: é canvas próprio (`mapaMotor.ts`), com projeção
 * equirretangular corrigida por `cos(latitude média)`. Tiles XYZ são Web
 * Mercator. A pergunta que decidiu este arquivo era se as duas alinham.
 *
 * ALINHAM, e por um motivo que vale escrever: na latitude central as duas
 * projeções têm exatamente a mesma proporção — o `cos(27°) = 0,89101` do
 * enquadramento é o mesmo fator que o Mercator aplica ali. O que sobra é a
 * curvatura, e ela foi medida na bacia inteira (-27,6 a -26,4): **1,2 px de
 * erro máximo num canvas de 900 px de altura**, 0,13%.
 *
 * Por isso cada tile é desenhado na caixa que a PRÓPRIA `projetar` devolve para
 * os cantos dele — o erro por tile vira uma fração de pixel, e a projeção do
 * mapa não precisou mudar. Trocá-la mexeria no traçado do rio, no encaixe das
 * cidades e na correnteza, tudo para ganhar um pixel.
 *
 * ATRIBUIÇÃO É CONDIÇÃO DE LICENÇA, não cortesia: ela troca junto com a camada.
 * Ver `docs/CAMADAS-DE-MAPA.md`.
 */
import { projetar, type Enquadramento, type LonLat } from './mapaCanvas'

export type ChaveFundo = 'escuro' | 'satelite' | 'mapa'

export type Fundo = {
  nome: string
  url: string
  atribuicao: string
  maxZoom: number
  /** Esri inverte a ordem: `{z}/{y}/{x}`. Errar isto devolve tile de outro lugar. */
  invertido?: boolean
  /** Fundo com textura, onde o cinza "sem dado" some sem contorno escuro. */
  texturado?: boolean
  /**
   * Segunda camada, desenhada POR CIMA da base: nomes de rua, bairro e cidade.
   *
   * Os "canvas" do Esri separam desenho e rótulo em serviços diferentes. Sem
   * esta camada o fundo escuro fica bonito e MUDO — e num mapa de enchente
   * saber que aquele bairro é Santa Regina não é enfeite, é o que orienta quem
   * está decidindo se sai de casa.
   */
  rotulos?: string
}

export const FUNDOS: Record<ChaveFundo, Fundo> = {
  /**
   * FUNDO ESCURO — trocado do CARTO para o Esri em 04/09/2026.
   *
   * O `basemaps.cartocdn.com/dark_all` passou a servir os tiles com a marca
   * d'água "API KEY REQUIRED" repetida por cima de tudo (visto no celular do
   * Jefferson em 04/09, com o mapa aberto). Os tiles ainda carregam, então não
   * é falha de segurança — é o mapa da cidade coberto de aviso comercial na
   * hora em que alguém está olhando onde a água está.
   *
   * O Esri não pede chave e JÁ É o provedor do Satélite aqui, então a
   * atribuição e os termos que o projeto aceita não mudam. O preço é o teto de
   * zoom: o Dark Gray Canvas é publicado até o nível 16, contra 19 do CARTO.
   * Quem precisar de mais perto tem o "Mapa" (OpenStreetMap, até 19) ao lado.
   */
  escuro: {
    nome: 'Escuro',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
    rotulos:
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
    atribuicao: 'Esri, HERE, Garmin, © colaboradores do OpenStreetMap',
    maxZoom: 16,
    invertido: true,
  },
  satelite: {
    nome: 'Satélite',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    atribuicao: 'Imagem: Esri, Maxar, Earthstar Geographics',
    maxZoom: 18,
    invertido: true,
    texturado: true,
  },
  mapa: {
    nome: 'Mapa',
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    atribuicao: '© colaboradores do OpenStreetMap',
    maxZoom: 19,
    texturado: true,
  },
}

export const FUNDO_PADRAO: ChaveFundo = 'escuro'

/** Lado do tile em pixels, como os três provedores servem. */
export const LADO_TILE = 256

export function ehChaveDeFundo(v: unknown): v is ChaveFundo {
  return typeof v === 'string' && v in FUNDOS
}

/** Longitude da borda oeste do tile x, no zoom z. */
export function lonDoTile(x: number, z: number): number {
  return (x / 2 ** z) * 360 - 180
}

/** Latitude da borda norte do tile y, no zoom z. */
export function latDoTile(y: number, z: number): number {
  const n = Math.PI * (1 - (2 * y) / 2 ** z)
  return (180 / Math.PI) * Math.atan(Math.sinh(n))
}

/** Coluna de tile que contém esta longitude. Pode sair fracionária de propósito. */
export function tileX(lon: number, z: number): number {
  return ((lon + 180) / 360) * 2 ** z
}

/** Linha de tile que contém esta latitude (Web Mercator). */
export function tileY(lat: number, z: number): number {
  const rad = (lat * Math.PI) / 180
  const y = Math.log(Math.tan(rad) + 1 / Math.cos(rad))
  return ((1 - y / Math.PI) / 2) * 2 ** z
}

/**
 * O zoom em que um tile fica com ~`LADO_TILE` pixels na tela.
 *
 * Pedir zoom demais multiplica requisições por quatro a cada nível e não
 * acrescenta nada visível; pedir de menos deixa o fundo borrado. O teto é o do
 * provedor — passar dele devolve 404, não imagem melhor.
 */
export function zoomPara(e: Enquadramento, maxZoom: number): number {
  // Largura em pixels de 360° de longitude, na escala deste enquadramento.
  const mundoPx = 360 * e.cosLat * e.escala
  const z = Math.round(Math.log2(Math.max(1, mundoPx / LADO_TILE)))
  return Math.max(0, Math.min(maxZoom, z))
}

export type TileNaTela = {
  x: number
  y: number
  z: number
  /** Caixa em pixels do canvas, já projetada. */
  px: number
  py: number
  largura: number
  altura: number
}

/**
 * Os tiles que cobrem a área visível, com a caixa em pixels de cada um.
 *
 * A caixa sai de `projetar` aplicada aos cantos do PRÓPRIO tile — é isso que
 * absorve a diferença entre Mercator e a projeção do canvas, tile a tile.
 *
 * `limite` corta o resultado: uma janela absurda (canvas gigante, zoom alto)
 * pediria milhares de imagens e travaria o navegador numa noite de chuva, que é
 * exatamente quando ele não pode travar. Estourando, devolve vazio — o mapa
 * desenha sem fundo, que é o comportamento de sempre.
 */
export function tilesVisiveis(
  e: Enquadramento,
  largura: number,
  altura: number,
  z: number,
  limite = 256,
): TileNaTela[] {
  const canto = (px: number, py: number): LonLat => [
    e.minLon + (px - e.deslocX) / (e.cosLat * e.escala),
    e.maxLat - (py - e.deslocY) / e.escala,
  ]
  const [lonO, latN] = canto(0, 0)
  const [lonL, latS] = canto(largura, altura)

  const x0 = Math.floor(tileX(lonO, z))
  const x1 = Math.ceil(tileX(lonL, z))
  const y0 = Math.floor(tileY(latN, z))
  const y1 = Math.ceil(tileY(latS, z))
  const n = 2 ** z
  if ((x1 - x0) * (y1 - y0) > limite) return []

  const saida: TileNaTela[] = []
  for (let x = x0; x < x1; x++) {
    for (let y = y0; y < y1; y++) {
      if (x < 0 || y < 0 || x >= n || y >= n) continue
      const [ax, ay] = projetar(e, [lonDoTile(x, z), latDoTile(y, z)])
      const [bx, by] = projetar(e, [lonDoTile(x + 1, z), latDoTile(y + 1, z)])
      saida.push({ x, y, z, px: ax, py: ay, largura: bx - ax, altura: by - ay })
    }
  }
  return saida
}

/** URL do tile, respeitando a inversão do Esri. */
export function urlDoTile(fundo: Fundo, x: number, y: number, z: number): string {
  return preencher(fundo.url, x, y, z)
}

/** URL da camada de RÓTULOS do fundo, quando ele tem uma. */
export function urlDosRotulos(fundo: Fundo, x: number, y: number, z: number): string | null {
  return fundo.rotulos ? preencher(fundo.rotulos, x, y, z) : null
}

function preencher(molde: string, x: number, y: number, z: number): string {
  return molde
    .replace('{z}', String(z))
    .replace('{x}', String(x))
    .replace('{y}', String(y))
}
