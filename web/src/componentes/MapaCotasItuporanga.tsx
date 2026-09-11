import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import indice from '@dados/manchas/ituporanga/index.json'
import estilos from './MapaManchas.module.css'

const arquivos = import.meta.glob('@dados/manchas/ituporanga/*.geojson', {
  query: '?url', import: 'default', eager: true,
}) as Record<string, string>

/** Consulta manual das camadas publicadas; não recebe o nível ao vivo. */
export default function MapaCotasItuporanga() {
  const [arquivo, setArquivo] = useState(indice.camadas[0]!.arquivo)
  const [visivel, setVisivel] = useState(true)
  const [estado, setEstado] = useState('Carregando camada…')
  const [erro, setErro] = useState(false)
  const [tentativa, setTentativa] = useState(0)
  const div = useRef<HTMLDivElement>(null)
  const mapa = useRef<L.Map | null>(null)
  const camada = useRef<L.GeoJSON | null>(null)
  const enquadrado = useRef(false)
  const selecionada = indice.camadas.find((c) => c.arquivo === arquivo)!
  const nivel = selecionada.nivel_m.toFixed(2).replace('.', ',')

  useEffect(() => {
    if (!div.current) return
    const m = L.map(div.current, { scrollWheelZoom: false, preferCanvas: true })
      .setView([-27.41, -49.60], 14)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(m)
    mapa.current = m
    const resize = new ResizeObserver(() => m.invalidateSize())
    resize.observe(div.current)
    return () => { resize.disconnect(); m.remove(); mapa.current = null; enquadrado.current = false }
  }, [])

  useEffect(() => {
    const m = mapa.current
    if (!m) return
    camada.current?.remove()
    camada.current = null
    setErro(false)
    if (!visivel) { setEstado('Camada ocultada.'); return }
    const url = Object.entries(arquivos).find(([k]) => k.endsWith(`/${arquivo}`))?.[1]
    if (!url) { setErro(true); setEstado('Camada não encontrada.'); return }
    const controller = new AbortController()
    let ativa = true
    setEstado('Carregando camada…')
    fetch(url, { signal: controller.signal })
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then((geo) => {
        if (!ativa) return
        const nova = L.geoJSON(geo, {
          interactive: false,
          style: { stroke: false, fillColor: '#1679ba', fillOpacity: 0.48, fillRule: 'nonzero' },
        }).addTo(m)
        camada.current = nova
        if (!enquadrado.current && nova.getBounds().isValid()) {
          m.fitBounds(nova.getBounds(), { padding: [16, 16] })
          enquadrado.current = true
        }
        setEstado(`Camada de ${nivel} m carregada. Azul: área desenhada na fonte para este nível.`)
      })
      .catch(() => { if (ativa) { setErro(true); setEstado('Não foi possível carregar a camada. Tente novamente.') } })
    return () => { ativa = false; controller.abort() }
  }, [arquivo, visivel, tentativa, nivel])

  return <section className="cartao">
    <h2>Áreas de inundação por nível — Ituporanga</h2>
    <p className={estilos.intro}>Explore as oito camadas do mapa divulgado pela Prefeitura.
      O nível abaixo é uma escolha para consulta, não uma medição atual.</p>
    <label className={estilos.rotulo} htmlFor="cota-ituporanga">Nível indicado no mapa de origem</label>
    <select id="cota-ituporanga" className={estilos.seletor} value={arquivo}
      onChange={(e) => setArquivo(e.target.value)}>
      {indice.camadas.map((c) => <option key={c.arquivo} value={c.arquivo}>
        {c.nivel_m.toFixed(2).replace('.', ',')} m
      </option>)}
    </select>
    <p><label><input type="checkbox" checked={visivel} onChange={(e) => setVisivel(e.target.checked)} /> Mostrar área no mapa</label></p>
    <div ref={div} className={estilos.mapa} role="region" aria-label={`Mapa de consulta de Ituporanga, camada de ${nivel} metros`} />
    <p role="status" className={erro ? estilos.erro : estilos.estado}>{estado}</p>
    {erro && <button type="button" onClick={() => setTentativa((v) => v + 1)}>Tentar novamente</button>}
    <p className={estilos.ressalva}>A referência destes níveis ainda precisa ser confirmada com a Defesa Civil.
      Por isso, as camadas não acompanham automaticamente a régua ao vivo. A área azul não confirma
      alagamento agora; fora dela também pode haver risco. Não substitui os avisos oficiais. Emergência: 199.</p>
    <p><a href={indice.fonte} target="_blank" rel="noreferrer">Consultar mapa de origem</a></p>
  </section>
}
