import { useRef, useState } from 'react'
import url from '@dados/vias/itajai.geojson?url'
import { pesquisarVias } from '../logica/viasItajai'

export default function BuscaViaItajai({ onSelecionar }: {
  onSelecionar: (dados: GeoJSON.FeatureCollection | null) => void
}) {
  const cache = useRef<GeoJSON.FeatureCollection | null>(null)
  const [termo, setTermo] = useState('')
  const [resultados, setResultados] = useState<string[]>([])
  const [estado, setEstado] = useState('')
  return <section aria-label="Localizar rua em Itajaí">
    <form onSubmit={async e => {
      e.preventDefault()
      if (termo.trim().length < 3) { setEstado('Digite pelo menos três letras.'); return }
      setEstado('Buscando…')
      setResultados([])
      try {
        if (!cache.current) {
          const r = await fetch(url)
          if (!r.ok) throw new Error('download')
          cache.current = await r.json() as GeoJSON.FeatureCollection
        }
        const nomes = pesquisarVias(cache.current, termo)
        setResultados(nomes)
        setEstado(nomes.length ? 'Selecione a rua (até 20 resultados).' : 'Rua não encontrada nesta base.')
      } catch { setEstado('Não foi possível carregar as ruas. Tente novamente.') }
    }}>
      <label htmlFor="busca-via-itajai">Localizar rua no mapa histórico</label>{' '}
      <input id="busca-via-itajai" value={termo} onChange={e => setTermo(e.target.value)} placeholder="Nome da rua" />{' '}
      <button type="submit">Buscar</button>{' '}
      <button type="button" onClick={() => { onSelecionar(null); setResultados([]); setEstado(''); }}>Limpar destaque</button>
    </form>
    <p role="status">{estado}</p>
    {resultados.length > 0 && <ul>{resultados.map(nome => <li key={nome}>
      <button type="button" onClick={() => onSelecionar({ type: 'FeatureCollection',
        features: cache.current!.features.filter(f => f.properties?.nome === nome) })}>{nome}</button>
    </li>)}</ul>}
    <p>Fonte: <a href="https://geoitajai.github.io/sie/dcitajai.html" target="_blank" rel="noreferrer">GeoItajaí / SIE</a>.
      {' '}O destaque localiza a via; não indica alagamento atual nem que toda a rua foi atingida.</p>
  </section>
}
