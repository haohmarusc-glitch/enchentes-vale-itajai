/**
 * Em quais enchentes um ponto do mapa ficou dentro da mancha de inundação.
 *
 * Esta é a única parte do "meu ponto" de Itajaí que dá para fazer hoje, e a
 * razão é o que ela NÃO faz: não compara altura de terreno com nível de rio.
 * A elevação dos pontos cotados de Itajaí é altura acima do nível do mar; o
 * nível das estações DC é leitura na régua de cada uma, com zero próprio e não
 * publicado. Subtrair um do outro daria um número com duas casas decimais,
 * nenhum significado e toda a aparência de medição — ver `docs/tela-itajai.md`.
 *
 * Já "este ponto ficou dentro da mancha de 2008" é um fato sobre polígonos que
 * estão no repositório. Não depende de referência nenhuma, e é verdadeiro ou
 * falso, não estimado.
 *
 * O que continua valendo, e a tela repete: mancha não é previsão, e ausência de
 * mancha não é ausência de risco — o levantamento cobre o que foi mapeado.
 */

export type Coordenada = [number, number]
/** Anel: primeiro o externo, depois os buracos. */
export type Anel = Coordenada[]
export type Poligono = Anel[]

/**
 * Está dentro deste anel? Traça uma semirreta para a direita e conta quantas
 * arestas ela cruza: ímpar é dentro.
 *
 * A comparação `(yi > y) !== (yj > y)` trata cada aresta como fechada embaixo e
 * aberta em cima. É o que impede um vértice exatamente na altura do ponto de
 * ser contado duas vezes — e, com ele, um ponto de fora aparecer como dentro.
 */
export function dentroDoAnel(ponto: Coordenada, anel: Anel): boolean {
  const [x, y] = ponto
  let dentro = false
  for (let i = 0, j = anel.length - 1; i < anel.length; j = i++) {
    const atual = anel[i]
    const anterior = anel[j]
    if (!atual || !anterior) continue
    const [xi, yi] = atual
    const [xj, yj] = anterior
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) {
      dentro = !dentro
    }
  }
  return dentro
}

/** Dentro do anel externo e fora de todos os buracos. */
export function dentroDoPoligono(ponto: Coordenada, poligono: Poligono): boolean {
  const externo = poligono[0]
  if (!externo || !dentroDoAnel(ponto, externo)) return false
  return !poligono.slice(1).some((buraco) => dentroDoAnel(ponto, buraco))
}

/**
 * Dentro de uma geometria de GeoJSON. Aceita `Polygon` e `MultiPolygon`, que
 * são os dois tipos que as manchas de Itajaí usam; qualquer outro devolve
 * `false` em vez de tentar adivinhar.
 */
export function dentroDaGeometria(ponto: Coordenada, geometria: unknown): boolean {
  const g = geometria as { type?: string; coordinates?: unknown }
  if (!g || !Array.isArray(g.coordinates)) return false
  if (g.type === 'Polygon') return dentroDoPoligono(ponto, g.coordinates as Poligono)
  if (g.type === 'MultiPolygon') {
    return (g.coordinates as Poligono[]).some((p) => dentroDoPoligono(ponto, p))
  }
  return false
}

/** Dentro de qualquer feição da coleção. */
export function dentroDaColecao(ponto: Coordenada, geojson: unknown): boolean {
  const f = geojson as { features?: { geometry?: unknown }[] }
  if (!f || !Array.isArray(f.features)) return false
  return f.features.some((feicao) => dentroDaGeometria(ponto, feicao?.geometry))
}
