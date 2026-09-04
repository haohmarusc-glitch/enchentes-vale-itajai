import { useEffect, useMemo, useRef, useState } from 'react'
import type { Cidade, TabuaMare } from '../dados/tipos'
import type { EstadoTempoReal } from '../dados/tempoReal'
import { ROTULO_FAIXA, ACAO_FAIXA } from './LegendaFaixas'
import { metros } from '../logica/formato'
import { eixoDoRio, temReguaCadastrada } from '../dados/carregar'
import { limitesDe, VISTA_INTEIRA, type LonLat, type Vista } from '../logica/mapaCanvas'
import {
  construirCena,
  desenharBase,
  desenharCorrenteza,
  desenharOnda,
  desenharPinos,
  MARGEM,
  type Cena,
  type Pino,
} from '../logica/mapaMotor'
import estilos from './MapaRios.module.css'

// O traçado entra como URL (não como import de dado): são arquivos grandes, e o
// Vite os emite à parte para a tela buscar só o do rio aberto.
const TRACADOS = import.meta.glob('@dados/rios/*.geojson', {
  query: '?url',
  import: 'default',
  eager: true,
}) as Record<string, string>

function urlDoRio(rioId: string): string | undefined {
  const chave = Object.keys(TRACADOS).find((k) => k.endsWith(`/${rioId}.geojson`))
  return chave ? TRACADOS[chave] : undefined
}

/**
 * Mapa geográfico do rio em <canvas>, no espírito do Kikikuru: o traçado real
 * (OpenStreetMap) pintado por trecho — cada trecho na cor da faixa da cidade a
 * montante — com a correnteza animada descendo no sentido do rio, MAIS RÁPIDA
 * onde o nível está mais alto (a animação significa o nível, não enfeita).
 * Trecho sem cidade que o pinte fica cinza e PARADO — não fingimos conhecer uma
 * água que não medimos. Na foz, o mar é colorido pela maré (escala própria).
 * Toque numa cidade abre as cotas de rua e o abrigo dela.
 *
 * O desenho e a montagem da cena moram em `logica/mapaMotor.ts`, dividido com a
 * tela cheia da bacia (`MonitorBacia`). Aqui é só um rio.
 */
export default function MapaRios({
  rioId,
  cidades,
  tempoReal,
  agora,
  aoSelecionar,
  mare = null,
  focarEm,
  zoomDoFoco = 8,
}: {
  rioId: string
  cidades: Cidade[]
  tempoReal: EstadoTempoReal
  agora: Date
  /** Chamado ao tocar numa cidade — abre o detalhe dela na tela do rio. */
  aoSelecionar?: (cidadeId: string) => void
  /** Tábua de maré de Itajaí — colore o MAR na foz. Ausente = mar cinza. */
  mare?: TabuaMare | null
  /**
   * Abre o mapa já aproximado nesta cidade, em vez do rio inteiro.
   *
   * A tela de uma cidade não precisa mostrar 180 km de rio para dizer onde a
   * régua está: precisa mostrar o trecho DELA. O rio inteiro continua desenhado
   * — só a janela é menor —, então quem rolar para os lados vê de onde a água
   * vem e para onde vai, que é a informação que o zoom não pode custar.
   */
  focarEm?: Cidade
  /** Quanto aproximar quando há foco. 8 ≈ 25 km de tela na bacia do Itajaí. */
  zoomDoFoco?: number
}) {
  const divRef = useRef<HTMLDivElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [coords, setCoords] = useState<LonLat[][] | null>(null)
  const [tam, setTam] = useState<{ w: number; h: number }>({ w: 0, h: 0 })
  /**
   * A janela do mapa. Sem foco, a bacia inteira — exatamente como sempre foi.
   * Com foco, aproximada na régua da cidade; sem coordenada não há onde
   * aproximar, e chutar uma posição num mapa de enchente é pior que não
   * aproximar.
   */
  const vista: Vista = useMemo(
    () =>
      focarEm?.coordenadas
        ? {
            zoom: zoomDoFoco,
            centroLon: focarEm.coordenadas[1],
            centroLat: focarEm.coordenadas[0],
          }
        : VISTA_INTEIRA,
    [focarEm, zoomDoFoco],
  )
  const [sel, setSel] = useState<Pino | null>(null)
  const cenaRef = useRef<Cena | null>(null)
  // A seleção é lida por ref dentro do laço de animação, para trocar o anel do
  // pino sem reconstruir a cena (o que reiniciaria a correnteza a cada toque).
  const selRef = useRef<string | null>(null)
  useEffect(() => {
    selRef.current = sel?.cidade.id ?? null
  }, [sel])

  // Busca o traçado do rio aberto.
  useEffect(() => {
    const url = urlDoRio(rioId)
    if (!url) {
      setErro('traçado deste rio ainda não disponível')
      setCoords(null)
      return
    }
    let vivo = true
    setErro(null)
    setCoords(null)
    setSel(null)
    fetch(url)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((geo: { geometry: { coordinates: LonLat[][] } }) => {
        if (vivo) setCoords(geo.geometry.coordinates)
      })
      .catch((e: Error) => vivo && setErro(e.message))
    return () => {
      vivo = false
    }
  }, [rioId])

  // Altura ideal pela PROPORÇÃO da bacia: um rio largo e baixo (o Açu) não
  // precisa de 60vh de altura com o traçado numa faixa fina no meio.
  const alturaIdeal = useMemo(() => {
    if (!coords || tam.w < 2) return null
    const lim = limitesDe(coords.flat())
    if (!lim) return null
    const cosLat = Math.cos((((lim.minLat + lim.maxLat) / 2) * Math.PI) / 180)
    const geoW = Math.max(1e-9, (lim.maxLon - lim.minLon) * cosLat)
    const geoH = Math.max(1e-9, lim.maxLat - lim.minLat)
    const alvo = (tam.w - 2 * MARGEM) * (geoH / geoW) + 2 * MARGEM
    return Math.round(Math.max(280, Math.min(560, alvo)))
  }, [coords, tam.w])

  // Mede o container e reage a mudança de tamanho (rotação do celular etc.).
  useEffect(() => {
    const div = divRef.current
    if (!div) return
    const medir = () => setTam({ w: div.clientWidth, h: div.clientHeight })
    medir()
    const ro = new ResizeObserver(medir)
    ro.observe(div)
    return () => ro.disconnect()
  }, [])

  // Monta a cena e roda a animação. Reconstrói quando muda o rio, os dados, o
  // horário ou o tamanho; a correnteza corre entre reconstruções.
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !coords || tam.w < 2 || tam.h < 2) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = Math.min(2, window.devicePixelRatio || 1)
    canvas.width = Math.round(tam.w * dpr)
    canvas.height = Math.round(tam.h * dpr)

    const cena = construirCena(
      canvas,
      [{ rioId, coords, cidades, eixo: eixoDoRio(rioId) }],
      tempoReal,
      agora,
      tam.w,
      tam.h,
      mare,
      undefined,
      undefined,
      vista,
    )
    cenaRef.current = cena

    // Base (fundo escuro + leito luminoso) numa camada só, desenhada uma vez; a
    // correnteza e os pinos vão por cima a cada quadro.
    const fundo = document.createElement('canvas')
    fundo.width = canvas.width
    fundo.height = canvas.height
    const fctx = fundo.getContext('2d')!
    fctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    desenharBase(fctx, cena)

    const reduz =
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches

    let raf = 0
    const inicio = performance.now()
    const quadro = (t: number) => {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, cena.largura, cena.altura)
      ctx.drawImage(fundo, 0, 0, cena.largura, cena.altura)
      const seg = reduz ? 0 : (t - inicio) / 1000
      desenharOnda(ctx, cena, seg) // a onda descendo até o mar
      desenharCorrenteza(ctx, cena, seg)
      desenharPinos(ctx, cena, selRef.current, { temRegua: temReguaCadastrada })
      if (!reduz) raf = requestAnimationFrame(quadro)
    }
    raf = requestAnimationFrame(quadro)
    return () => cancelAnimationFrame(raf)
  }, [coords, cidades, tempoReal, agora, tam, rioId, mare, vista])

  // Toque/clique: acha o pino mais próximo e abre o detalhe da cidade.
  function aoTocar(ev: React.PointerEvent<HTMLCanvasElement>) {
    const cena = cenaRef.current
    const canvas = canvasRef.current
    if (!cena || !canvas) return
    const r = canvas.getBoundingClientRect()
    const x = ev.clientX - r.left
    const y = ev.clientY - r.top
    let melhor: Pino | null = null
    let d = 22 * 22
    for (const p of cena.pinos) {
      const dd = (p.x - x) ** 2 + (p.y - y) ** 2
      if (dd < d) {
        d = dd
        melhor = p
      }
    }
    if (melhor) {
      setSel(melhor)
      aoSelecionar?.(melhor.cidade.id)
    } else {
      setSel(null)
    }
  }

  return (
    <div className={estilos.bloco}>
      {erro ? <p className={estilos.erro}>Mapa indisponível: {erro}</p> : null}
      <div
        ref={divRef}
        className={estilos.mapa}
        style={alturaIdeal ? { height: `${alturaIdeal}px` } : undefined}
      >
        <canvas
          ref={canvasRef}
          className={estilos.tela}
          style={{ width: '100%', height: '100%' }}
          onPointerDown={aoTocar}
          role="img"
          aria-label={`Mapa do rio ${rioId}: traçado colorido pela faixa de cada cidade, com a correnteza descendo`}
        />
        {sel ? (
          <div
            className={estilos.balao}
            style={{
              left: `${(sel.x / (tam.w || 1)) * 100}%`,
              top: `${(sel.y / (tam.h || 1)) * 100}%`,
            }}
          >
            <strong>{sel.cidade.nome}</strong>
            <br />
            {ROTULO_FAIXA[sel.faixa]}
            {sel.nivel != null ? (
              <>
                <br />
                {metros(sel.nivel)}
              </>
            ) : null}
            <br />
            <em>{ACAO_FAIXA[sel.faixa]}</em>
            {aoSelecionar ? (
              <button
                type="button"
                className={estilos.dicaDetalhe}
                onClick={() => {
                  aoSelecionar(sel.cidade.id)
                  setSel(null)
                }}
              >
                Ver as cotas de rua e o abrigo
              </button>
            ) : null}
          </div>
        ) : null}
      </div>

      {/* Acesso por teclado/leitor de tela: o canvas não é focável por cidade,
          então as âncoras viram botões (fora da vista) que fazem o mesmo toque. */}
      {aoSelecionar ? (
        <ul className={estilos.foraDaVista}>
          {cidades
            .filter((c) => c.coordenadas)
            .map((c) => (
              <li key={c.id}>
                <button type="button" onClick={() => aoSelecionar(c.id)}>
                  Ver detalhe de {c.nome}
                </button>
              </li>
            ))}
        </ul>
      ) : null}

      <p className={estilos.credito}>
        Cada trecho tem a cor da faixa da cidade a montante; a correnteza desce no
        sentido do rio e corre mais rápido onde o nível está mais alto — nunca o
        nível em metros. Trecho <strong>cinza</strong> é onde ainda não há régua
        que o pinte, e por isso fica parado. Na foz, a faixa <strong>azul</strong>{' '}
        é a <strong>maré</strong> (escala própria, não a de cheia): maré alta
        trava o escoamento do rio. Toque numa cidade para as cotas de rua e o
        abrigo dela. Traçado: © colaboradores do OpenStreetMap (ODbL).
      </p>
    </div>
  )
}
