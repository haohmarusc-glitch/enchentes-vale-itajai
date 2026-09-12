export function normalizarVia(texto: string): string {
  return texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR').trim()
}

export function pesquisarVias(dados: GeoJSON.FeatureCollection, termo: string): string[] {
  const busca = normalizarVia(termo)
  if (busca.length < 3) return []
  return [...new Set(dados.features.map(f => f.properties?.nome)
    .filter((nome): nome is string => typeof nome === 'string' && normalizarVia(nome).includes(busca)))]
    .sort((a, b) => a.localeCompare(b, 'pt-BR')).slice(0, 20)
}
