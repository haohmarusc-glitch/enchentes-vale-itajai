import { useState } from 'react'
import { carregarViasItajai } from '../dados/viasItajai'
import { pesquisarVias } from '../logica/viasItajai'

/**
 * A busca de rua do mapa das manchas. Escolher uma rua grava `?rua=` no endereço, o mesmo caminho do chat
 * ("mostrar a rua X em Itajaí"): o destaque é um só, e a página o desenha (`MapaManchas`).
 */
export default function BuscaViaItajai({ onSelecionar }: {
  onSelecionar: (nome: string | null) => void
}) {
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
        const nomes = pesquisarVias(await carregarViasItajai(), termo)
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
      <button type="button" onClick={() => onSelecionar(nome)}>{nome}</button>
    </li>)}</ul>}
    <p>Fonte: <a href="https://geoitajai.github.io/sie/dcitajai.html" target="_blank" rel="noreferrer">GeoItajaí / SIE</a>.
      {' '}O destaque localiza a via; não indica alagamento atual nem que toda a rua foi atingida.</p>
  </section>
}
