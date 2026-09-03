import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { cidadesDoRio, mareItajai } from '../dados/carregar'
import type { Cidade } from '../dados/tipos'
import { useTempoReal } from '../dados/tempoReal'
import { leituraEm, serieDaCidade, useSerieRecente } from '../dados/serie'
import { idadeMin, textoIdade, type Faixa } from '../logica/tempoReal'
import { ROTULO_FAIXA, ACAO_FAIXA } from '../componentes/LegendaFaixas'
import { dataHora, metros } from '../logica/formato'
import { projetar, type LonLat } from '../logica/mapaCanvas'
import {
  construirCena,
  desenharBase,
  desenharCorrenteza,
  desenharOnda,
  desenharPinos,
  type Cena,
  type LeituraNaHora,
  type Pino,
  type RioParaCena,
} from '../logica/mapaMotor'
import estilos from './MonitorBacia.module.css'

// Traçados como URL (o Vite emite à parte). A bacia toda: Açu + Mirim, mais os
// afluentes que existirem no pacote (Benedito, Luís Alves, Hercílio) — opcionais,
// porque dependem da coleta do Overpass na VPS.
const TRACADOS = import.meta.glob('@dados/rios/*.geojson', {
  query: '?url',
  import: 'default',
  eager: true,
}) as Record<string, string>

function urlDoRio(rioId: string): string | undefined {
  const chave = Object.keys(TRACADOS).find((k) => k.endsWith(`/${rioId}.geojson`))
  return chave ? TRACADOS[chave] : undefined
}

/** Rios do tronco (têm cidades que os pintam). Afluentes entram como linha extra. */
const RIOS_TRONCO = ['itajai-acu', 'itajai-mirim'] as const
const AFLUENTES = ['benedito', 'luiz-alves', 'hercilio'] as const

async function baixarTracado(rioId: string): Promise<LonLat[][] | null> {
  const url = urlDoRio(rioId)
  if (!url) return null
  try {
    const r = await fetch(url)
    if (!r.ok) return null
    const geo = (await r.json()) as { geometry: { coordinates: LonLat[][] } }
    return geo.geometry.coordinates
  } catch {
    return null
  }
}

interface MarcadorChuva {
  x: number
  y: number
  mm: number
  janela: string
  cidade: string
}

/** Marcadores de chuva: a intensidade recente por cidade, projetada no mapa. */
function marcadoresChuva(
  cena: Cena,
  cidades: Cidade[],
  chuva: { cidade: string | null; mm: { h1: number | null; h24: number | null } }[],
): MarcadorChuva[] {
  const porId = new Map(cidades.filter((c) => c.coordenadas).map((c) => [c.id, c]))
  const saida: MarcadorChuva[] = []
  for (const c of chuva) {
    if (!c.cidade) continue
    const cidade = porId.get(c.cidade)
    if (!cidade?.coordenadas) continue
    // Prefere a última hora; sem ela, as últimas 24 h. Só mostra chuva medível.
    const h1 = c.mm.h1
    const h24 = c.mm.h24
    const usa = h1 != null ? { mm: h1, janela: '1 h' } : h24 != null ? { mm: h24, janela: '24 h' } : null
    if (!usa || usa.mm < 0.2) continue
    const [x, y] = projetar(cena.enq, [cidade.coordenadas[1], cidade.coordenadas[0]])
    saida.push({ x, y, mm: usa.mm, janela: usa.janela, cidade: cidade.nome })
  }
  return saida
}

/** Uma gota de chuva com o acumulado, deslocada do pino para não o cobrir. */
function desenharChuva(ctx: CanvasRenderingContext2D, marcas: MarcadorChuva[], escala: number): void {
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  for (const m of marcas) {
    const gx = m.x + 11 * escala
    const gy = m.y - 11 * escala
    const raio = Math.min(3 + m.mm * 0.5, 9) * escala
    ctx.beginPath()
    ctx.arc(gx, gy, raio, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(56,170,226,0.85)'
    ctx.shadowColor = 'rgba(56,170,226,0.9)'
    ctx.shadowBlur = 6 * escala
    ctx.fill()
    ctx.shadowBlur = 0
    ctx.strokeStyle = 'rgba(210,238,252,0.9)'
    ctx.lineWidth = 1 * escala
    ctx.stroke()
    const txt = `${m.mm.toFixed(m.mm < 10 ? 1 : 0)} mm`
    ctx.font = `600 ${Math.round(10 * escala)}px system-ui, sans-serif`
    ctx.lineWidth = 3 * escala
    ctx.strokeStyle = 'rgba(4,12,20,0.9)'
    ctx.strokeText(txt, gx + raio + 2 * escala, gy)
    ctx.fillStyle = '#bfe6fb'
    ctx.fillText(txt, gx + raio + 2 * escala, gy)
  }
}

const FAIXAS_LEGENDA: Faixa[] = ['normal', 'atencao', 'alerta', 'inundacao', 'sem-dado', 'varias']
// Mesma variável CSS da legenda do resto do site (fonte única das cores).
const VAR_LEGENDA: Record<Faixa, string> = {
  normal: '--faixa-normal',
  atencao: '--faixa-atencao',
  alerta: '--faixa-alerta',
  inundacao: '--faixa-inundacao',
  emergencia: '--faixa-emergencia',
  'sem-dado': '--faixa-sem-dado',
  varias: '--agua-clara',
}

/**
 * Tela cheia de monitoramento da bacia do Itajaí: Açu + Mirim (+ afluentes) num
 * `<canvas>` só, em alta definição. Cada trecho na cor da faixa da cidade a
 * montante (nunca metro entre cidades), correnteza que corre mais rápido onde o
 * nível está mais alto, o mar na foz colorido pela maré (escala própria), a
 * chuva recente por cidade e a idade de cada leitura. Não é sistema de alerta.
 */
export default function MonitorBacia() {
  const navigate = useNavigate()
  const divRef = useRef<HTMLDivElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const cenaRef = useRef<Cena | null>(null)
  const chuvaRef = useRef<MarcadorChuva[]>([])
  const selRef = useRef<string | null>(null)

  const [rios, setRios] = useState<RioParaCena[] | null>(null)
  const [tam, setTam] = useState<{ w: number; h: number }>({ w: 0, h: 0 })
  const [sel, setSel] = useState<Pino | null>(null)

  const tempoReal = useTempoReal()
  const serie = useSerieRecente()
  const agora = useMemo(() => new Date(), [tempoReal])

  useEffect(() => {
    selRef.current = sel?.cidade.id ?? null
  }, [sel])

  // Todas as cidades da bacia, para casar a chuva com a coordenada.
  const cidadesBacia = useMemo(
    () => RIOS_TRONCO.flatMap((r) => cidadesDoRio(r)),
    [],
  )

  // Grade de instantes da REPRODUÇÃO (últimas ~24 h, passo de 30 min), a partir
  // da série de nível de todas as cidades. Vazia = sem série publicada ainda.
  const grade = useMemo(() => {
    let min = Infinity
    let max = -Infinity
    for (const c of cidadesBacia) {
      for (const r of RIOS_TRONCO) {
        for (const p of serieDaCidade(serie, r, c.id)) {
          const t = p.medidoEm.getTime()
          if (t < min) min = t
          if (t > max) max = t
        }
      }
    }
    if (!Number.isFinite(min)) return [] as number[]
    const inicio = Math.max(min, max - 24 * 3_600_000)
    const passos: number[] = []
    for (let t = inicio; t < max; t += 30 * 60_000) passos.push(t)
    passos.push(max)
    return passos
  }, [serie, cidadesBacia])

  // Índice na grade quando em REPRODUÇÃO; null = AO VIVO (usa o ultimo.json).
  const [idxRepro, setIdxRepro] = useState<number | null>(null)
  const [tocando, setTocando] = useState(false)

  // Avança a reprodução; ao chegar ao fim, volta AO VIVO.
  useEffect(() => {
    if (!tocando || grade.length === 0) return
    const id = setInterval(() => {
      setIdxRepro((x) => {
        const prox = (x ?? 0) + 1
        if (prox >= grade.length) {
          setTocando(false)
          return null // fim → ao vivo
        }
        return prox
      })
    }, 450)
    return () => clearInterval(id)
  }, [tocando, grade.length])

  // Baixa os traçados do tronco (obrigatórios) e dos afluentes (opcionais).
  useEffect(() => {
    let vivo = true
    Promise.all([
      ...RIOS_TRONCO.map(async (rioId) => ({ rioId, coords: await baixarTracado(rioId) })),
      ...AFLUENTES.map(async (rioId) => ({ rioId, coords: await baixarTracado(rioId) })),
    ]).then((baixados) => {
      if (!vivo) return
      const lista: RioParaCena[] = []
      for (const b of baixados) {
        if (!b.coords) continue
        // Tronco tem cidades que o pintam; afluente entra só como linha (sem
        // cidade própria no cadastro → fica cinza, honesto).
        const cidades = (RIOS_TRONCO as readonly string[]).includes(b.rioId)
          ? cidadesDoRio(b.rioId)
          : []
        lista.push({ rioId: b.rioId, coords: b.coords, cidades })
      }
      setRios(lista)
    })
    return () => {
      vivo = false
    }
  }, [])

  // Mede o container (tela cheia).
  useEffect(() => {
    const div = divRef.current
    if (!div) return
    const medir = () => setTam({ w: div.clientWidth, h: div.clientHeight })
    medir()
    const ro = new ResizeObserver(medir)
    ro.observe(div)
    return () => ro.disconnect()
  }, [])

  // Monta a cena da bacia e roda a animação em alta definição.
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !rios || rios.length === 0 || tam.w < 2 || tam.h < 2) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Alta definição: usa o dpr do aparelho (até 3) — texturas nítidas.
    const dpr = Math.min(3, window.devicePixelRatio || 1)
    canvas.width = Math.round(tam.w * dpr)
    canvas.height = Math.round(tam.h * dpr)
    // Escala do texto/pinos: numa tela grande, os rótulos crescem para caber a
    // bacia inteira sem virar formiguinha.
    const escala = Math.max(1, Math.min(1.7, tam.w / 820))

    // AO VIVO (idxRepro null) usa o ultimo.json e o agora; na REPRODUÇÃO, cada
    // cidade recebe a leitura da série ATÉ o instante escolhido (nunca a futura).
    const emRepro = idxRepro !== null && grade.length > 0
    const instante = emRepro ? new Date(grade[Math.min(idxRepro!, grade.length - 1)]!) : agora
    const override: LeituraNaHora | undefined = emRepro
      ? (rioId, cidadeId) => {
          const p = leituraEm(serieDaCidade(serie, rioId, cidadeId), instante.getTime())
          return p ? { nivel_m: p.nivel_m, medidoEm: p.medidoEm } : null
        }
      : undefined

    const cena = construirCena(canvas, rios, tempoReal, instante, tam.w, tam.h, mareItajai, override)
    cenaRef.current = cena
    // A chuva é do agora; na reprodução do passado, some (não fingimos chuva
    // num instante que não medimos).
    chuvaRef.current = emRepro ? [] : marcadoresChuva(cena, cidadesBacia, tempoReal.chuva)

    const fundo = document.createElement('canvas')
    fundo.width = canvas.width
    fundo.height = canvas.height
    const fctx = fundo.getContext('2d')!
    fctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    desenharBase(fctx, cena, escala)

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
      desenharOnda(ctx, cena, seg, escala) // a onda descendo até o mar
      desenharCorrenteza(ctx, cena, seg, escala)
      desenharChuva(ctx, chuvaRef.current, escala)
      desenharPinos(ctx, cena, selRef.current, {
        escala,
        mostrarIdade: true,
        agora: instante,
      })
      if (!reduz) raf = requestAnimationFrame(quadro)
    }
    raf = requestAnimationFrame(quadro)
    return () => cancelAnimationFrame(raf)
  }, [rios, tempoReal, agora, tam, cidadesBacia, idxRepro, grade, serie])

  function aoTocar(ev: React.PointerEvent<HTMLCanvasElement>) {
    const cena = cenaRef.current
    const canvas = canvasRef.current
    if (!cena || !canvas) return
    const r = canvas.getBoundingClientRect()
    const x = ev.clientX - r.left
    const y = ev.clientY - r.top
    let melhor: Pino | null = null
    let d = 24 * 24
    for (const p of cena.pinos) {
      const dd = (p.x - x) ** 2 + (p.y - y) ** 2
      if (dd < d) {
        d = dd
        melhor = p
      }
    }
    setSel(melhor)
  }

  function telaCheia() {
    const el = divRef.current
    if (!el) return
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
    else el.requestFullscreen?.().catch(() => {})
  }

  const rotaDoRio = (rioId: string) => (rioId === 'itajai-mirim' ? '/mirim' : '/acu')

  return (
    <div className={estilos.pagina}>
      <div ref={divRef} className={estilos.palco}>
        <canvas
          ref={canvasRef}
          className={estilos.tela}
          style={{ width: '100%', height: '100%' }}
          onPointerDown={aoTocar}
          role="img"
          aria-label="Monitoramento da bacia do Itajaí: Açu e Mirim, cada trecho na cor da faixa da cidade a montante, com correnteza, chuva e maré na foz"
        />

        {/* Legenda sempre visível. */}
        <div className={estilos.legenda}>
          <strong className={estilos.legendaTitulo}>Faixa (na régua de cada cidade)</strong>
          <ul>
            {FAIXAS_LEGENDA.map((faixa) => (
              <li key={faixa}>
                <span className={estilos.amostra} style={{ background: `var(${VAR_LEGENDA[faixa]})` }} />
                {ROTULO_FAIXA[faixa]}
              </li>
            ))}
            <li>
              <span className={estilos.amostra} style={{ background: '#38aae2' }} />
              Chuva recente (mm)
            </li>
            <li>
              <span className={estilos.amostra} style={{ background: '#2f86c9' }} />
              Mar / maré na foz
            </li>
          </ul>
          <p className={estilos.legendaNota}>
            Cor é a faixa na régua da cidade, <strong>nunca o metro</strong> entre
            cidades. Cinza = sem régua fresca (não é seguro, é sem dado).
          </p>
        </div>

        {/* Título e aviso no topo-esquerdo (o chip da maré fica no topo-direito,
            desenhado no canvas). O botão de tela cheia vai no canto inferior
            direito para não colidir com o chip. */}
        <div className={estilos.topo}>
          <strong>Monitoramento da bacia</strong>
          <span className={estilos.aviso}>
            Não é alerta oficial. Emergência: <strong>199</strong>. Siga a Defesa Civil.
          </span>
        </div>
        <button type="button" className={estilos.botaoCheia} onClick={telaCheia}>
          Tela cheia
        </button>

        {/* Reprodução das últimas 24 h: a onda de cor descendo, do MEDIDO. Só
            aparece quando há série publicada. */}
        {grade.length > 0 ? (
          <div className={estilos.controles}>
            <button
              type="button"
              className={estilos.botaoPlay}
              onClick={() => {
                if (tocando) {
                  setTocando(false)
                } else {
                  setIdxRepro((x) => (x == null ? 0 : x)) // começa do início da janela
                  setTocando(true)
                }
              }}
            >
              {tocando ? '⏸ Pausar' : '▶ Reproduzir 24 h'}
            </button>
            <input
              className={estilos.barra}
              type="range"
              min={0}
              max={grade.length - 1}
              value={idxRepro ?? grade.length - 1}
              onChange={(e) => {
                setTocando(false)
                const v = Number(e.target.value)
                setIdxRepro(v >= grade.length - 1 ? null : v)
              }}
              aria-label="Instante da reprodução"
            />
            <span className={estilos.instante}>
              {idxRepro == null ? 'ao vivo' : dataHora(new Date(grade[idxRepro]!))}
            </span>
          </div>
        ) : null}

        {/* Cartão da cidade tocada. */}
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
            {sel.nivel != null ? <> · {metros(sel.nivel)}</> : null}
            {sel.medidoEm ? (
              <>
                <br />
                <span className={estilos.idade}>{textoIdade(idadeMin(sel.medidoEm, agora))}</span>
              </>
            ) : null}
            <br />
            <em>{ACAO_FAIXA[sel.faixa]}</em>
            <button
              type="button"
              className={estilos.dicaDetalhe}
              onClick={() => navigate(rotaDoRio(sel.rioId))}
            >
              Abrir {sel.rioId === 'itajai-mirim' ? 'o Mirim' : 'o Açu'}
            </button>
          </div>
        ) : null}
      </div>

      {/* Acesso por teclado/leitor: as cidades viram botões fora da vista. */}
      <ul className={estilos.foraDaVista}>
        {cidadesBacia
          .filter((c) => c.coordenadas)
          .map((c) => (
            <li key={c.id}>
              <button type="button" onClick={() => setSel(null)}>
                {c.nome}
              </button>
            </li>
          ))}
      </ul>
    </div>
  )
}
