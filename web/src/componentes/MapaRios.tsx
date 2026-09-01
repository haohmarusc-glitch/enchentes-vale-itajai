import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Cidade } from '../dados/tipos'
import type { EstadoTempoReal } from '../dados/tempoReal'
import { leituraDaCidade, leiturasDaCidade } from '../dados/tempoReal'
import { faixaDaCidade, type Faixa } from '../logica/tempoReal'
import LegendaFaixas, { ROTULO_FAIXA, ACAO_FAIXA } from './LegendaFaixas'
import { metros } from '../logica/formato'
import estilos from './MapaRios.module.css'

// O traçado entra como URL (não como import de dado), como o mapa de manchas:
// são arquivos grandes, e o Vite os emite à parte para a tela buscar só o do
// rio aberto.
const TRACADOS = import.meta.glob('@dados/rios/*.geojson', {
  query: '?url',
  import: 'default',
  eager: true,
}) as Record<string, string>

function urlDoRio(rioId: string): string | undefined {
  const chave = Object.keys(TRACADOS).find((k) => k.endsWith(`/${rioId}.geojson`))
  return chave ? TRACADOS[chave] : undefined
}

const COR_FAIXA: Record<Faixa, string> = {
  normal: '#2e7d32',
  atencao: '#e6a700',
  alerta: '#e2661a',
  inundacao: '#c62828',
  emergencia: '#c62828',
  'sem-dado': '#9aa7b2',
  varias: '#1c6ea4',
}

type LonLat = [number, number]

/** Ponto do traçado mais próximo de uma coordenada — encaixa o marcador no rio. */
function maisProximoNoRio(coords: LonLat[][], alvo: LonLat): LonLat | null {
  let melhor: LonLat | null = null
  let dist = Infinity
  for (const linha of coords) {
    for (const p of linha) {
      const d = (p[0] - alvo[0]) ** 2 + (p[1] - alvo[1]) ** 2
      if (d < dist) {
        dist = d
        melhor = p
      }
    }
  }
  return melhor
}

/**
 * Mapa geográfico do rio, no espírito do Kikikuru: o traçado real (OpenStreetMap)
 * com um marcador colorido por cidade — a cor é a faixa da PRÓPRIA cidade, a
 * mesma do diagrama. Cidade sem coordenada cadastrada ainda não aparece; cidade
 * sem faixa aparece cinza. Carrega sob botão, para não pesar no celular.
 */
export default function MapaRios({
  rioId,
  cidades,
  tempoReal,
  agora,
}: {
  rioId: string
  cidades: Cidade[]
  tempoReal: EstadoTempoReal
  agora: Date
}) {
  const divRef = useRef<HTMLDivElement | null>(null)
  const mapaRef = useRef<L.Map | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    if (!divRef.current || mapaRef.current) return
    const mapa = L.map(divRef.current, { scrollWheelZoom: false })
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '© colaboradores do OpenStreetMap',
    }).addTo(mapa)
    mapaRef.current = mapa

    const url = urlDoRio(rioId)
    if (!url) {
      setErro('traçado deste rio ainda não disponível')
      mapa.setView([-27.0, -49.2], 9)
      return () => {
        mapa.remove()
        mapaRef.current = null
      }
    }

    let vivo = true
    fetch(url)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((geo: { geometry: { coordinates: LonLat[][] } }) => {
        if (!vivo) return
        const coords = geo.geometry.coordinates
        // O rio, em azul, por baixo dos marcadores.
        const linha = L.geoJSON(geo as unknown as GeoJSON.GeoJsonObject, {
          style: { color: '#1c6ea4', weight: 3, opacity: 0.85 },
        }).addTo(mapa)
        mapa.fitBounds(linha.getBounds(), { padding: [16, 16] })

        for (const cidade of cidades) {
          const coord = cidade.coordenadas
          if (!coord) continue
          const alvo: LonLat = [coord[1], coord[0]] // [lon,lat] para casar com o rio
          const ponto = maisProximoNoRio(coords, alvo) ?? alvo
          const aoVivo = leituraDaCidade(tempoReal, rioId, cidade.id)
          const temVarias = aoVivo === null && leiturasDaCidade(tempoReal, rioId, cidade.id).length > 1
          const faixa = faixaDaCidade(cidade, aoVivo, temVarias, agora)
          L.circleMarker([ponto[1], ponto[0]], {
            radius: 8,
            color: '#111827',
            weight: 2,
            fillColor: COR_FAIXA[faixa],
            fillOpacity: 1,
          })
            .addTo(mapa)
            .bindPopup(
              `<strong>${cidade.nome}</strong><br>${ROTULO_FAIXA[faixa]}` +
                (aoVivo ? `<br>${metros(aoVivo.nivel_m)}` : '') +
                `<br><em>${ACAO_FAIXA[faixa]}</em>`,
            )
        }
      })
      .catch((e: Error) => vivo && setErro(e.message))

    return () => {
      vivo = false
      mapa.remove()
      mapaRef.current = null
    }
  }, [rioId, cidades, tempoReal, agora])

  return (
    <div className={estilos.bloco}>
      <LegendaFaixas />
      {erro ? <p className={estilos.erro}>Mapa indisponível: {erro}</p> : null}
      <div ref={divRef} className={estilos.mapa} role="img" aria-label={`Mapa do ${rioId}`} />
      <p className={estilos.credito}>
        Traçado dos rios: © colaboradores do OpenStreetMap (ODbL). A cor de cada
        cidade é a faixa da régua dela — não o nível em metros.
      </p>
    </div>
  )
}
