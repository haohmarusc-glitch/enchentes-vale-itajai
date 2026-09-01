import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Cidade } from '../dados/tipos'
import type { EstadoTempoReal } from '../dados/tempoReal'
import { leituraDaCidade, leiturasDaCidade } from '../dados/tempoReal'
import { faixaDaCidade, type Faixa } from '../logica/tempoReal'
import { ROTULO_FAIXA, ACAO_FAIXA } from './LegendaFaixas'
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

// Longitude e latitude não têm o mesmo comprimento em metros: perto de 27° S um
// grau de longitude vale ~0,89 grau de latitude. Sem corrigir isso, o "mais
// próximo" entortaria nos trechos leste–oeste (a maior parte do Vale). Escala só
// para comparar distâncias; nada disso vai para a tela.
const K_LON = Math.cos((27 * Math.PI) / 180)
function dist2(a: LonLat, b: LonLat): number {
  return ((a[0] - b[0]) * K_LON) ** 2 + (a[1] - b[1]) ** 2
}

/** Ponto do traçado mais próximo de uma coordenada — encaixa o marcador no rio. */
function maisProximoNoRio(coords: LonLat[][], alvo: LonLat): LonLat | null {
  let melhor: LonLat | null = null
  let dist = Infinity
  for (const linha of coords) {
    for (const p of linha) {
      const d = dist2(p, alvo)
      if (d < dist) {
        dist = d
        melhor = p
      }
    }
  }
  return melhor
}

/**
 * Distância² de um ponto ao segmento a–b e onde caiu (t em 0..1). Usada para
 * projetar cada pedaço do rio na "espinha" das cidades em ordem.
 */
function projetarNoSegmento(p: LonLat, a: LonLat, b: LonLat): number {
  const abx = (b[0] - a[0]) * K_LON
  const aby = b[1] - a[1]
  const apx = (p[0] - a[0]) * K_LON
  const apy = p[1] - a[1]
  const len2 = abx * abx + aby * aby
  const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, (apx * abx + apy * aby) / len2))
  const cx = abx * t - apx
  const cy = aby * t - apy
  return cx * cx + cy * cy
}

/**
 * Em qual trecho entre cidades consecutivas este ponto do rio cai. A espinha são
 * os pontos das cidades (já encaixados no rio), na ordem montante→jusante. Devolve
 * o índice da cidade A MONTANTE do trecho — é ela quem dá a cor, como no diagrama.
 */
function trechoDoPonto(espinha: LonLat[], p: LonLat): number {
  if (espinha.length < 2) return 0
  let melhor = 0
  let dist = Infinity
  for (let i = 0; i < espinha.length - 1; i++) {
    const d = projetarNoSegmento(p, espinha[i]!, espinha[i + 1]!)
    if (d < dist) {
      dist = d
      melhor = i
    }
  }
  return melhor
}

/** Desenha um pedaço contínuo do rio ([lon,lat]…) numa cor só. */
function desenharRun(mapa: L.Map, pontos: LonLat[], cor: string): void {
  if (pontos.length < 2) return
  L.polyline(
    pontos.map((p) => [p[1], p[0]] as [number, number]),
    { color: cor, weight: 4, opacity: 0.9 },
  ).addTo(mapa)
}

/**
 * Mapa geográfico do rio, no espírito do Kikikuru: o traçado real (OpenStreetMap)
 * pintado por trecho — cada trecho na cor da faixa da cidade a montante, a mesma
 * regra do diagrama linear — com um marcador colorido por cidade por cima. Onde
 * não há cidade que pinte (nascentes, pontas soltas), o rio fica cinza. Cidade
 * sem coordenada cadastrada não vira âncora. Carrega sob botão, para não pesar no
 * celular.
 */
// Longe, o mapa mostra só o rio colorido e os pontos das cidades — "onde está o
// perigo". Ao aproximar deste zoom, os nomes das cidades aparecem, e o toque
// numa cidade abre as cotas de rua e o abrigo dela (detalhe). É a transição
// visão geral→detalhe do Kikikuru, com o dado que temos por cidade — rua e
// abrigo não têm coordenada, então não viram pino no mapa.
const ZOOM_ROTULOS = 11

export default function MapaRios({
  rioId,
  cidades,
  tempoReal,
  agora,
  aoSelecionar,
}: {
  rioId: string
  cidades: Cidade[]
  tempoReal: EstadoTempoReal
  agora: Date
  /** Chamado ao tocar numa cidade — abre o detalhe dela na tela do rio. */
  aoSelecionar?: (cidadeId: string) => void
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

        // Cada cidade com coordenada vira uma âncora encaixada no rio, na ordem
        // montante→jusante. A espinha por essas âncoras diz, para cada pedaço do
        // traçado, entre quais cidades ele está — e a faixa da cidade a montante
        // dá a cor daquele trecho, a mesma regra do diagrama linear.
        const ancoras = cidades
          .filter((c) => c.coordenadas)
          .map((cidade) => {
            const coord = cidade.coordenadas!
            const alvo: LonLat = [coord[1], coord[0]] // [lon,lat] para casar com o rio
            const aoVivo = leituraDaCidade(tempoReal, rioId, cidade.id)
            const temVarias =
              aoVivo === null && leiturasDaCidade(tempoReal, rioId, cidade.id).length > 1
            return {
              cidade,
              aoVivo,
              faixa: faixaDaCidade(cidade, aoVivo, temVarias, agora),
              ponto: maisProximoNoRio(coords, alvo) ?? alvo,
            }
          })
        const espinha = ancoras.map((a) => a.ponto)

        // Fundo cinza-azulado do rio inteiro, para o traçado nunca sumir mesmo
        // onde não há cidade que o pinte (nascentes, pontas soltas do OSM).
        const fundo = L.geoJSON(geo as unknown as GeoJSON.GeoJsonObject, {
          style: { color: '#9aa7b2', weight: 3, opacity: 0.55 },
        }).addTo(mapa)
        mapa.fitBounds(fundo.getBounds(), { padding: [16, 16] })

        // Por cima, cada trecho na cor da faixa da cidade a montante. Agrupa
        // arestas vizinhas de mesma cor numa só linha, para não criar milhares
        // de camadas no celular.
        if (espinha.length >= 2) {
          for (const linha of coords) {
            if (linha.length < 2) continue
            let inicio = 0
            let corAtual = ancoras[trechoDoPonto(espinha, linha[0]!)]!.faixa
            for (let i = 1; i < linha.length; i++) {
              const meio: LonLat = [
                (linha[i - 1]![0] + linha[i]![0]) / 2,
                (linha[i - 1]![1] + linha[i]![1]) / 2,
              ]
              const cor = ancoras[trechoDoPonto(espinha, meio)]!.faixa
              if (cor !== corAtual) {
                desenharRun(mapa, linha.slice(inicio, i + 1), COR_FAIXA[corAtual])
                inicio = i
                corAtual = cor
              }
            }
            desenharRun(mapa, linha.slice(inicio), COR_FAIXA[corAtual])
          }
        }

        // Marcadores das cidades por cima de tudo, com o número e a ação. O nome
        // fica num rótulo que só aparece quando o mapa está aproximado; o toque
        // seleciona a cidade e abre o detalhe (cotas de rua e abrigo) na tela.
        for (const a of ancoras) {
          const marcador = L.circleMarker([a.ponto[1], a.ponto[0]], {
            radius: 8,
            color: '#111827',
            weight: 2,
            fillColor: COR_FAIXA[a.faixa],
            fillOpacity: 1,
          }).addTo(mapa)
          marcador.bindPopup(
            `<strong>${a.cidade.nome}</strong><br>${ROTULO_FAIXA[a.faixa]}` +
              (a.aoVivo ? `<br>${metros(a.aoVivo.nivel_m)}` : '') +
              `<br><em>${ACAO_FAIXA[a.faixa]}</em>` +
              (aoSelecionar
                ? `<br><span class="${estilos.dicaDetalhe ?? ''}">Toque para ver as cotas de rua e o abrigo</span>`
                : ''),
          )
          marcador.bindTooltip(a.cidade.nome, {
            permanent: true,
            direction: 'top',
            className: estilos.rotuloCidade,
          })
          if (aoSelecionar) marcador.on('click', () => aoSelecionar(a.cidade.id))
        }

        // Zoom troca a informação: os rótulos das cidades só aparecem de perto.
        const ajustarRotulos = () => {
          const cls = estilos.semRotulos
          if (cls) divRef.current?.classList.toggle(cls, mapa.getZoom() < ZOOM_ROTULOS)
        }
        mapa.on('zoomend', ajustarRotulos)
        ajustarRotulos()
      })
      .catch((e: Error) => vivo && setErro(e.message))

    return () => {
      vivo = false
      mapa.remove()
      mapaRef.current = null
    }
  }, [rioId, cidades, tempoReal, agora, aoSelecionar])

  return (
    <div className={estilos.bloco}>
      {erro ? <p className={estilos.erro}>Mapa indisponível: {erro}</p> : null}
      <div ref={divRef} className={estilos.mapa} role="img" aria-label={`Mapa do ${rioId}`} />
      <p className={estilos.credito}>
        Aproxime para ver os nomes; toque numa cidade para as cotas de rua e o
        abrigo dela. Traçado dos rios: © colaboradores do OpenStreetMap (ODbL).
        Cada trecho tem a cor da faixa da cidade a montante; o marcador, a faixa
        da cidade — nunca o nível em metros. Trecho cinza é onde ainda não há
        régua que o pinte.
      </p>
    </div>
  )
}
