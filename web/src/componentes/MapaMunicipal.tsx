import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import CamadasMonitor, { type CamadaDesenhada } from './CamadasMonitor'
import type { LeituraAoVivo } from '../dados/tempoReal'

export default function MapaMunicipal({ cidade, centro, leituras, agora }: { cidade: string; centro: [number, number]; leituras: LeituraAoVivo[]; agora: Date }) {
  const div = useRef<HTMLDivElement>(null)
  const mapa = useRef<L.Map | null>(null)
  const [camada, setCamada] = useState<CamadaDesenhada>(null)
  const [lat, lon] = centro
  useEffect(() => {
    if (!div.current) return
    const m = L.map(div.current, {scrollWheelZoom: false}).setView([lat, lon], 14)
    // Sem base de ruas externa neste piloto de fontes governamentais.
    L.circleMarker([lat, lon], {radius: 8, color: '#425466'}).bindTooltip('Localização cadastrada da régua').addTo(m)
    mapa.current = m
    const resize = new ResizeObserver(() => m.invalidateSize())
    resize.observe(div.current)
    return () => { resize.disconnect(); m.remove(); mapa.current = null }
  }, [lat, lon])
  useEffect(() => {
    if (!mapa.current || !camada) return
    const layer = L.geoJSON(camada.geo, {style:{color:'#176ead',weight:1,fillOpacity:.4}}).addTo(mapa.current)
    if (layer.getBounds().isValid()) mapa.current.fitBounds(layer.getBounds())
    return () => { layer.remove() }
  }, [camada])
  return <section aria-label="Mapa de manchas municipal"><h2>Manchas e comparação histórica</h2>
    <p>Camada histórica é referência do evento indicado. Não representa observação de alagamento atual. A seleção por nível exige régua e pico documentados.</p>
    <div ref={div} style={{height:380,background:'#edf2f5',border:'1px solid #bacbd7'}} role="region" aria-label="Mapa de camadas e localização da régua" />
    <p>{camada ? camada.rotulo : 'Sem mancha desenhada. O ponto indica somente a localização da régua; a base de ruas ainda não foi integrada.'}</p>
    <CamadasMonitor cidade={cidade} leituras={leituras} agora={agora} reproduzindo={false} onCamada={setCamada} somenteDados />
  </section>
}
