/**
 * A base de vias de Itajaí (GeoItajaí / Prefeitura, ~570 kB), baixada uma vez por página e repartida entre a
 * busca do mapa das manchas e o chat ("mostrar a rua X em Itajaí"). Fica fora do pacote: só desce quando
 * alguém procura uma rua.
 */
import url from '@dados/vias/itajai.geojson?url'

let pedido: Promise<GeoJSON.FeatureCollection> | null = null

export function carregarViasItajai(): Promise<GeoJSON.FeatureCollection> {
  pedido ??= fetch(url)
    .then((r) => (r.ok ? (r.json() as Promise<GeoJSON.FeatureCollection>) : Promise.reject(new Error(`HTTP ${r.status}`))))
    .catch((e) => {
      pedido = null // a próxima busca tenta de novo
      throw e
    })
  return pedido
}

/** Os nomes distintos da base, para o chat casar o que a pessoa escreveu. */
export async function nomesDasViasItajai(): Promise<string[]> {
  const g = await carregarViasItajai()
  return [...new Set(g.features.map((f) => f.properties?.nome).filter((n): n is string => typeof n === 'string'))]
}

/** As feições de uma via pelo nome EXATO da base (ruas com o mesmo nome entram juntas). */
export async function feicoesDaVia(nome: string): Promise<GeoJSON.FeatureCollection> {
  const g = await carregarViasItajai()
  return { type: 'FeatureCollection', features: g.features.filter((f) => f.properties?.nome === nome) }
}
