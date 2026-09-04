import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { cidadesDoRio, estacoesTempoReal, mareItajai } from '../dados/carregar'
import type { Cidade } from '../dados/tipos'
import { leiturasDaCidade, useTempoReal } from '../dados/tempoReal'
import { useNivelSc } from '../dados/nivelSc'
import { leituraEm, serieDaCidade, useSerieRecente } from '../dados/serie'
import { idadeMin, textoIdade, type Faixa } from '../logica/tempoReal'
import { ROTULO_FAIXA, ACAO_FAIXA } from '../componentes/LegendaFaixas'
import { dataHora, metros } from '../logica/formato'
import {
  desprojetar,
  projetar,
  VISTA_INTEIRA,
  type LonLat,
  type Vista,
} from '../logica/mapaCanvas'
import {
  COR_BRUTO,
  construirCena,
  desenharBase,
  desenharCorrenteza,
  desenharOnda,
  desenharPinos,
  desenharReguas,
  COR_REGUA_SEM_GRAU,
  type Cena,
  type LeituraNaHora,
  type Pino,
  type RioParaCena,
} from '../logica/mapaMotor'
import { reguasComCota } from '../logica/reguas'
import { reguasNoMapa, type ReguaNoMapa } from '../logica/reguasNoMapa'
import {
  FUNDOS,
  FUNDO_PADRAO,
  ehChaveDeFundo,
  tilesVisiveis,
  urlDoTile,
  zoomPara,
  type ChaveFundo,
} from '../logica/tiles'
import VariasReguas from '../componentes/VariasReguas'
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
/**
 * Traçados OPCIONAIS: entram quando o geojson existe, e somem sem quebrar nada.
 *
 * Os três últimos são de ITAJAÍ e existem por medição, não por gosto. Com o
 * traçado de hoje (`scripts/conferir_reguas_no_tracado.py`), quatro das onze
 * réguas caem longe de qualquer curso desenhado:
 *
 *     DC-08 Rio do Meio    4,41 km   Rio Canhanduba
 *     DC-03 SEMASA         2,32 km   canal retificado do Mirim
 *     DC-07 Portal I       2,25 km   Ribeirão da Murta
 *     DC-09 Bairro Murta   0,87 km   Ribeirão da Murta
 *
 * As outras sete estão a menos de 0,2 km — inclusive a DC-11, na margem do
 * meandro da Volta de Cima, a 0,09 km: o tronco está certo, o que falta são os
 * cursos menores, que a consulta original do Overpass não pediu (só buscou
 * `waterway=river`). Ver `docs/tracado-ribeiroes.md`.
 */
const AFLUENTES = [
  'benedito',
  'luiz-alves',
  'hercilio',
  'ribeirao-murta',
  'ribeirao-canhanduba',
  'mirim-canal-retificado',
] as const

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

const FAIXAS_LEGENDA: Faixa[] = [
  'normal',
  'monitoramento',
  'atencao',
  'alerta',
  'inundacao',
  'sem-dado',
  'varias',
]
// Mesma variável CSS da legenda do resto do site (fonte única das cores).
const VAR_LEGENDA: Record<Faixa, string> = {
  normal: '--faixa-normal',
  monitoramento: '--faixa-monitoramento',
  atencao: '--faixa-atencao',
  alerta: '--faixa-alerta',
  inundacao: '--faixa-inundacao',
  emergencia: '--faixa-emergencia',
  'sem-dado': '--faixa-sem-dado',
  varias: '--agua-clara',
}

/** Rótulo legível de cada cota de referência, na ordem em que sobem. */
const ROTULO_COTA: Record<string, string> = {
  atencao: 'Atenção',
  alerta: 'Alerta',
  inundacao: 'Inundação',
  emergencia: 'Emergência',
  inundacao_historica: 'Inundação histórica',
}
const ORDEM_COTA = ['atencao', 'alerta', 'emergencia', 'inundacao', 'inundacao_historica']

/** Cotas da régua da cidade, ordenadas de baixo para cima. */
function cotasOrdenadas(cotas: Record<string, number>): [string, number][] {
  return Object.entries(cotas).sort((a, b) => {
    const ia = ORDEM_COTA.indexOf(a[0])
    const ib = ORDEM_COTA.indexOf(b[0])
    if (ia !== -1 && ib !== -1) return ia - ib
    return a[1] - b[1]
  })
}

/** Chuva recente da cidade (1 h e 24 h), da coleta ao vivo — null se não houver. */
function chuvaDaCidade(
  chuva: { rio: string | null; cidade: string | null; mm: { h1: number | null; h24: number | null } }[],
  rioId: string,
  cidadeId: string,
): { h1: number | null; h24: number | null } | null {
  const c = chuva.find((x) => x.rio === rioId && x.cidade === cidadeId)
  return c ? { h1: c.mm.h1, h24: c.mm.h24 } : null
}

/**
 * Tela cheia de monitoramento da bacia do Itajaí: Açu + Mirim (+ afluentes) num
 * `<canvas>` só, em alta definição. Cada trecho na cor da faixa da cidade a
 * montante (nunca metro entre cidades), correnteza que corre mais rápido onde o
 * nível está mais alto, o mar na foz colorido pela maré (escala própria), a
 * chuva recente por cidade e a idade de cada leitura. Não é sistema de alerta.
 */
/**
 * Até onde o zoom vai. A bacia tem ~1,9° de largura; dividida por 32 sobram
 * ~6 km de tela, que é a escala de bairro — o suficiente para ver de que lado
 * do Ribeirão da Murta está a régua, e não tanto que o traçado do OSM comece a
 * mostrar mais precisão do que ele tem.
 */
const ZOOM_MAX = 32

/**
 * Quantos pixels o dedo pode andar antes de virar arrasto.
 *
 * Abaixo disso o toque ainda seleciona. Sem essa folga, a mão trêmula de quem
 * olha o telefone numa noite de chuva moveria o mapa em vez de abrir o painel
 * da régua.
 */
const ARRASTO_MIN = 6

/**
 * O centro geográfico que a vista tem AGORA.
 *
 * Enquanto ninguém tocou no mapa, `centroLon/Lat` são NaN — "no meio, seja lá
 * onde for". Este é o único lugar que resolve esse NaN, e resolve pelos limites
 * da bacia, que é a mesma referência que `aplicarVista` usa para prender o
 * arrasto. Duas contas diferentes de "onde é o meio" fariam o primeiro arrasto
 * dar um salto.
 */
function centroAtual(cena: Cena, v: Vista): [number, number] {
  const b = cena.limitesBase
  return [
    Number.isFinite(v.centroLon) ? v.centroLon : (b.minLon + b.maxLon) / 2,
    Number.isFinite(v.centroLat) ? v.centroLat : (b.minLat + b.maxLat) / 2,
  ]
}

export default function MonitorBacia() {
  const navigate = useNavigate()
  const divRef = useRef<HTMLDivElement | null>(null)
  /**
   * As réguas com coordenada própria, como pontos no mapa.
   *
   * Hoje são as onze da Defesa Civil de Itajaí. Nove delas NÃO recebem cor —
   * são de estuário, e a maré cruza a cota sem enchente; `reguasNoMapa` aplica
   * essa regra. Ver o cabeçalho de `logica/reguasNoMapa.ts`.
   */
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const cenaRef = useRef<Cena | null>(null)
  /** Onde o mapa está olhando. Começa na bacia inteira, como sempre foi. */
  const [vista, setVista] = useState<Vista>(VISTA_INTEIRA)
  /** Dedos/ponteiros apertados agora, para separar toque de arrasto e de pinça. */
  const ponteiros = useRef<Map<number, { x: number; y: number }>>(new Map())
  /** Distância entre os dois dedos no quadro anterior da pinça. */
  const pinca = useRef<number | null>(null)
  const arrastou = useRef(false)
  /**
   * Cache de tiles, por URL, VIVO ENTRE RENDERS.
   *
   * Sem ele, cada redimensionamento ou tique do relógio pediria o mosaico
   * inteiro de novo — dezenas de imagens a cada quinze minutos, numa fonte
   * pública e gratuita que não nos deve nada. `'erro'` marca o que falhou, para
   * não repetir a tentativa em laço.
   */
  const tilesRef = useRef<Map<string, HTMLImageElement | 'erro'>>(new Map())
  const [fundo, setFundo] = useState<ChaveFundo>(() => {
    // `localStorage` pode estourar (janela anônima, site data bloqueado): a tela
    // tem de abrir igual, no escuro, que é o padrão por função.
    try {
      const v = localStorage.getItem('monitor-fundo')
      if (ehChaveDeFundo(v)) return v
    } catch {
      // sem preferência guardada é o caso comum, não erro
    }
    return FUNDO_PADRAO
  })
  useEffect(() => {
    try {
      localStorage.setItem('monitor-fundo', fundo)
    } catch {
      // guardar é conveniência; não guardar não quebra nada
    }
  }, [fundo])
  const chuvaRef = useRef<MarcadorChuva[]>([])
  const selRef = useRef<string | null>(null)

  const [rios, setRios] = useState<RioParaCena[] | null>(null)
  const [tam, setTam] = useState<{ w: number; h: number }>({ w: 0, h: 0 })
  const [sel, setSel] = useState<Pino | null>(null)
  const [hover, setHover] = useState<Pino | null>(null)
  /**
   * A régua individual em foco (as onze de Itajaí).
   *
   * Separada do pino de cidade porque as duas coisas convivem no mesmo lugar:
   * na foz, o pino de Itajaí fica no meio das réguas dela. Quem toca preciso
   * numa régua quer a régua; quem toca largo quer a cidade.
   */
  const [reguaSel, setReguaSel] = useState<string | null>(null)

  const tempoReal = useTempoReal()
  const nivelSc = useNivelSc()
  const serie = useSerieRecente()
  const agora = useMemo(() => new Date(), [tempoReal])

  // O anel destaca a cidade em FOCO: a selecionada (clique) ou a sob o mouse.
  useEffect(() => {
    selRef.current = (sel ?? hover)?.cidade.id ?? null
    reguaSelRef.current = reguaSel
  }, [sel, hover, reguaSel])

  // Todas as cidades da bacia, para casar a chuva com a coordenada.
  const cidadesBacia = useMemo(
    () => RIOS_TRONCO.flatMap((r) => cidadesDoRio(r)),
    [],
  )

  /**
   * As réguas com coordenada própria, como pontos no mapa.
   *
   * Hoje são as onze da Defesa Civil de Itajaí — duas no Açu, quatro no Mirim,
   * três em ribeirões (Murta, Canhanduba) e duas mais acima. O Monitor mostrava
   * a foz como UM pino azul de "várias réguas", e os ribeirões, onde a enxurrada
   * urbana acontece, não apareciam em lugar nenhum.
   *
   * NOVE delas NÃO recebem cor: são de estuário, e a maré cruza a cota sem
   * enchente. `reguasNoMapa` aplica essa regra — ver o cabeçalho de lá.
   */
  const reguasDoMapa = useMemo(
    () =>
      reguasNoMapa(
        estacoesTempoReal,
        tempoReal.leituras.map((l) => ({
          titulo: l.estacao,
          nivel_m: l.nivel_m,
          medidoEm: l.medidoEm,
        })),
        agora,
      ),
    [tempoReal, agora],
  )
  const reguasRef = useRef(reguasDoMapa)
  reguasRef.current = reguasDoMapa
  const reguaSelRef = useRef<string | null>(null)

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

    const cena = construirCena(
      canvas, rios, tempoReal, instante, tam.w, tam.h, mareItajai, override, nivelSc, vista,
    )
    cenaRef.current = cena
    // A chuva é do agora; na reprodução do passado, some (não fingimos chuva
    // num instante que não medimos).
    chuvaRef.current = emRepro ? [] : marcadoresChuva(cena, cidadesBacia, tempoReal.chuva)

    const fundoCanvas = document.createElement('canvas')
    fundoCanvas.width = canvas.width
    fundoCanvas.height = canvas.height
    const fctx = fundoCanvas.getContext('2d')!
    fctx.setTransform(dpr, 0, 0, dpr, 0, 0)

    // FUNDO DE MAPA (tiles). A geometria e o porquê de alinhar com a projeção
    // do canvas estão em `logica/tiles.ts`.
    const camada = FUNDOS[fundo]
    const z = zoomPara(cena.enq, camada.maxZoom)
    const pedacos = tilesVisiveis(cena.enq, tam.w, tam.h, z)
    const cache = tilesRef.current
    let vivo = true

    const pintarTiles = (c: CanvasRenderingContext2D) => {
      for (const t of pedacos) {
        const im = cache.get(urlDoTile(camada, t.x, t.y, t.z))
        if (im && im !== 'erro' && im.complete && im.naturalWidth > 0) {
          // +1 px cobre a costura de arredondamento entre vizinhos.
          c.drawImage(im, t.px, t.py, t.largura + 1, t.altura + 1)
        }
      }
    }

    const redesenharFundo = () => {
      fctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      desenharBase(fctx, cena, escala, {
        fundoTiles: pintarTiles,
        sobreImagem: !!camada.texturado,
      })
    }
    redesenharFundo()

    for (const t of pedacos) {
      const url = urlDoTile(camada, t.x, t.y, t.z)
      if (cache.has(url)) continue
      const im = new Image()
      // Sem `crossOrigin`: nada aqui lê pixel de volta (não há getImageData nem
      // toDataURL), então "sujar" o canvas não custa nada — e exigir CORS só
      // criaria uma forma nova de o fundo não carregar.
      im.onload = () => {
        if (vivo) redesenharFundo()
      }
      im.onerror = () => {
        cache.set(url, 'erro') // some o fundo ali, o mapa segue igual
      }
      im.src = url
      cache.set(url, im)
    }

    const reduz =
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches

    let raf = 0
    const inicio = performance.now()
    const quadro = (t: number) => {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, cena.largura, cena.altura)
      ctx.drawImage(fundoCanvas, 0, 0, cena.largura, cena.altura)
      const seg = reduz ? 0 : (t - inicio) / 1000
      desenharOnda(ctx, cena, seg, escala) // a onda descendo até o mar
      desenharCorrenteza(ctx, cena, seg, escala)
      desenharChuva(ctx, chuvaRef.current, escala)
      // As réguas ANTES dos pinos das cidades: o pino maior fica por cima.
      desenharReguas(ctx, cena, reguasRef.current, escala, reguaSelRef.current)
      desenharPinos(ctx, cena, selRef.current, {
        escala,
        mostrarIdade: true,
        agora: instante,
      })
      if (!reduz) raf = requestAnimationFrame(quadro)
    }
    raf = requestAnimationFrame(quadro)
    return () => {
      vivo = false // tile que chegar depois não redesenha canvas morto
      cancelAnimationFrame(raf)
    }
  }, [rios, tempoReal, nivelSc, agora, tam, cidadesBacia, idxRepro, grade, serie, fundo, vista])

  /** Pino mais próximo do ponteiro, dentro do raio — ou null. */
  function pinoNoPonto(ev: React.PointerEvent<HTMLCanvasElement>): Pino | null {
    const cena = cenaRef.current
    const canvas = canvasRef.current
    if (!cena || !canvas) return null
    const r = canvas.getBoundingClientRect()
    const x = ev.clientX - r.left
    const y = ev.clientY - r.top
    let melhor: Pino | null = null
    let d = 26 * 26
    for (const p of cena.pinos) {
      const dd = (p.x - x) ** 2 + (p.y - y) ** 2
      if (dd < d) {
        d = dd
        melhor = p
      }
    }
    return melhor
  }

  /**
   * Régua individual sob o ponteiro — raio MENOR que o da cidade (14 px contra
   * 26), porque o ponto é menor e porque há onze deles espremidos na foz. Testar
   * a régua ANTES da cidade é o que torna a DC-01 alcançável ao lado do pino de
   * Itajaí; um toque largo, fora do raio apertado, continua pegando a cidade.
   */
  function reguaNoPonto(ev: React.PointerEvent<HTMLCanvasElement>): ReguaNoMapa | null {
    const cena = cenaRef.current
    const canvas = canvasRef.current
    if (!cena || !canvas) return null
    const r = canvas.getBoundingClientRect()
    const x = ev.clientX - r.left
    const y = ev.clientY - r.top
    let melhor: ReguaNoMapa | null = null
    let d = 14 * 14
    for (const g of reguasRef.current) {
      const [gx, gy] = projetar(cena.enq, [g.lon, g.lat])
      const dd = (gx - x) ** 2 + (gy - y) ** 2
      if (dd < d) {
        d = dd
        melhor = g
      }
    }
    return melhor
  }

  function selecionar(ev: React.PointerEvent<HTMLCanvasElement>) {
    const g = reguaNoPonto(ev)
    if (g) {
      // Um painel por vez: dois abertos no mesmo canto se cobrem.
      setReguaSel(g.codigo || g.titulo)
      setSel(null)
      return
    }
    setReguaSel(null)
    setSel(pinoNoPonto(ev))
  }

  /**
   * ZOOM E ARRASTO — por que existem, e por que não bastava a lupa do navegador.
   *
   * Na foz, onde os dois rios chegam, há onze réguas em poucos quilômetros: os
   * rótulos se cobrem e o traçado some sob os pinos. Dando pinça na PÁGINA, o
   * navegador amplia o bitmap — o rio fica borrado, o rótulo continua ilegível e
   * a legenda sai da tela. Aqui a janela geográfica encolhe e a cena é
   * REDESENHADA: o traçado continua fino, os rótulos se separam e os tiles do
   * fundo vêm num nível de zoom maior, mais detalhado.
   *
   * O toque continua selecionando: só vira arrasto depois de {@link ARRASTO_MIN}
   * pixels. Sem essa folga, o dedo que treme ao tocar a régua moveria o mapa em
   * vez de abrir o painel — e numa cheia, quem olha o telefone tem a mão longe
   * de firme.
   */
  function aplicarZoom(fator: number, ancora?: { x: number; y: number }) {
    const cena = cenaRef.current
    setVista((v) => {
      const zoom = Math.min(ZOOM_MAX, Math.max(1, v.zoom * fator))
      if (!cena) return { ...v, zoom }
      // Sem âncora (botões), o centro fica onde está. Com âncora (pinça, roda),
      // o ponto sob o dedo é o que fica parado — é o que faz a pinça parecer
      // natural em vez de o mapa fugir.
      const centro = centroAtual(cena, v)
      if (!ancora) return { zoom, centroLon: centro[0], centroLat: centro[1] }
      const [lon, lat] = desprojetar(cena.enq, ancora.x, ancora.y)
      // O ponto sob o dedo fica parado: o centro se aproxima dele na mesma
      // razão em que a janela encolhe.
      const razao = v.zoom / zoom
      return {
        zoom,
        centroLon: lon + (centro[0] - lon) * razao,
        centroLat: lat + (centro[1] - lat) * razao,
      }
    })
  }

  function aoApontarBaixo(ev: React.PointerEvent<HTMLCanvasElement>) {
    ev.currentTarget.setPointerCapture?.(ev.pointerId)
    const r = ev.currentTarget.getBoundingClientRect()
    ponteiros.current.set(ev.pointerId, { x: ev.clientX - r.left, y: ev.clientY - r.top })
    arrastou.current = false
    if (ponteiros.current.size === 2) {
      const [a, b] = [...ponteiros.current.values()]
      pinca.current = Math.hypot(a!.x - b!.x, a!.y - b!.y)
      arrastou.current = true // pinça nunca é toque de seleção
    }
  }

  function aoApontarMove(ev: React.PointerEvent<HTMLCanvasElement>) {
    const cena = cenaRef.current
    const r = ev.currentTarget.getBoundingClientRect()
    const x = ev.clientX - r.left
    const y = ev.clientY - r.top
    const antes = ponteiros.current.get(ev.pointerId)

    // Sem botão apertado: é só o mouse passeando — destaca a cidade sob ele.
    if (!antes) {
      const p = pinoNoPonto(ev)
      setHover((atual) => (atual?.cidade.id === p?.cidade.id ? atual : p))
      return
    }
    ponteiros.current.set(ev.pointerId, { x, y })

    if (ponteiros.current.size >= 2 && cena) {
      const [a, b] = [...ponteiros.current.values()]
      const dist = Math.hypot(a!.x - b!.x, a!.y - b!.y)
      const anterior = pinca.current
      pinca.current = dist
      if (anterior && anterior > 4 && dist > 4) {
        aplicarZoom(dist / anterior, { x: (a!.x + b!.x) / 2, y: (a!.y + b!.y) / 2 })
      }
      return
    }

    const dx = x - antes.x
    const dy = y - antes.y
    if (!arrastou.current && Math.hypot(dx, dy) < ARRASTO_MIN) return
    arrastou.current = true
    if (!cena) return
    arrastarGeo(cena, dx, dy)
  }

  /** Move o centro por um deslocamento em PIXELS, convertido pela projeção atual. */
  function arrastarGeo(cena: Cena, dx: number, dy: number) {
    setVista((v) => {
      const centro = centroAtual(cena, v)
      return {
        zoom: v.zoom,
        centroLon: centro[0] - dx / (cena.enq.cosLat * cena.enq.escala),
        centroLat: centro[1] + dy / cena.enq.escala,
      }
    })
  }

  function aoApontarCima(ev: React.PointerEvent<HTMLCanvasElement>) {
    const tinha = ponteiros.current.delete(ev.pointerId)
    if (ponteiros.current.size < 2) pinca.current = null
    // Toque curto = seleção. Arrasto e pinça não selecionam nada.
    if (tinha && !arrastou.current) selecionar(ev)
  }

  function aoRolar(ev: React.WheelEvent<HTMLCanvasElement>) {
    const r = ev.currentTarget.getBoundingClientRect()
    aplicarZoom(ev.deltaY < 0 ? 1.18 : 1 / 1.18, {
      x: ev.clientX - r.left,
      y: ev.clientY - r.top,
    })
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
          onPointerDown={aoApontarBaixo}
          onPointerMove={aoApontarMove}
          onPointerUp={aoApontarCima}
          onPointerCancel={aoApontarCima}
          onPointerLeave={() => setHover(null)}
          onWheel={aoRolar}
          // O navegador não pode rolar a página nem dar a própria pinça em cima
          // do mapa: o gesto é do mapa, e a lupa do navegador borraria o rio.
          style={{ width: '100%', height: '100%', touchAction: 'none' }}
          role="img"
          aria-label="Monitoramento da bacia do Itajaí: Açu e Mirim, cada trecho na cor da faixa da cidade a montante, com correnteza, chuva e maré na foz"
        />

        {/* Legenda sempre visível, canto inferior esquerdo. O painel da cidade
            vai para o canto direito, então os dois não se cobrem. */}
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
            {/* O violeta estava no mapa sem entrada aqui: uma cor com
                significado e sem explicação. Fica FORA da escala de faixas de
                propósito — não é grau de perigo, é outro tipo de dado. */}
            <li>
              <span className={estilos.amostra} style={{ background: COR_BRUTO }} />
              ≈ nível bruto (rede estadual)
            </li>
            {/* As nove réguas de estuário de Itajaí. Mostram número e não
                afirmam faixa: a maré cruza a cota sem enchente, e uma cor que
                acende com a maré ensina a ignorar a cor. */}
            <li>
              <span
                className={estilos.amostra}
                style={{ background: 'transparent', border: `2px solid ${COR_REGUA_SEM_GRAU}` }}
              />
              Régua sem faixa (maré)
            </li>
          </ul>
          <p className={estilos.legendaNota}>
            Cor é a faixa na régua da cidade, <strong>nunca o metro</strong> entre
            cidades. Cinza = sem faixa para afirmar (não é seguro, é sem
            afirmação). O número em violeta vem da régua estadual, com zero
            próprio: aparece quando não há fonte municipal e{' '}
            <strong>não vira faixa</strong>.
          </p>
          {/* O cinza tem DUAS causas, e chamar as duas de "sem leitura" era
              falso justamente onde há leitura: o canal do Mirim mostra 0,41 m na
              SEMASA e mesmo assim fica cinza e parado. Não é falta de número — é
              recusa de transformar aquele número em faixa, porque a régua é de
              estuário. Como a correnteza SIGNIFICA a faixa, animá-la afirmaria o
              nível que a maré torna ilegível. */}
          <p className={estilos.legendaNota}>
            Ribeirões e canais (Murta, Canhanduba, canal do Mirim) ficam cinza e{' '}
            <strong>parados mesmo tendo régua com número</strong>: as réguas deles
            são de estuário, a maré cruza a cota sem enchente, e a correnteza
            animada significa a faixa — correr ali afirmaria um nível que a maré
            não deixa ler. O metro aparece no pino; a cor, não.
          </p>

          {/* Seletor de fundo. O ESCURO é o padrão por FUNÇÃO, não por estética:
              qualquer fundo com textura concorre visualmente com as faixas de
              alerta, e numa noite de chuva, com o celular na mão, isso pesa mais
              que parecer bonito. Satélite e mapa entram como escolha de quem
              olha — o satélite ganha na foz, onde reconhecer a barra e os molhes
              ajuda a se localizar. Ver `docs/CAMADAS-DE-MAPA.md`. */}
          <div className={estilos.fundos} role="group" aria-label="Fundo do mapa">
            {(Object.keys(FUNDOS) as ChaveFundo[]).map((k) => (
              <button
                key={k}
                type="button"
                aria-pressed={fundo === k}
                className={fundo === k ? estilos.fundoAtivo : estilos.fundoBotao}
                onClick={() => setFundo(k)}
              >
                {FUNDOS[k].nome}
              </button>
            ))}
          </div>
          {/* A ATRIBUIÇÃO É CONDIÇÃO DE LICENÇA, não cortesia: fica visível
              enquanto a camada estiver ativa, e troca junto com ela. */}
          <p className={estilos.atribuicao}>{FUNDOS[fundo].atribuicao}</p>
        </div>

        {/* Título e aviso no topo-esquerdo (o chip da maré fica no topo-direito,
            desenhado no canvas). O botão de tela cheia vai no canto inferior
            direito para não colidir com o chip. */}
        <div className={estilos.topo}>
          <strong>Monitoramento da bacia</strong>
          <span className={estilos.aviso}>
            Não é alerta oficial. Emergência: <strong>199</strong>. Siga a Defesa Civil.
          </span>
          <button type="button" className={estilos.botaoCheia} onClick={telaCheia}>
            Tela cheia
          </button>
        </div>

        {/* ZOOM. Os botões existem além da pinça porque nem todo mundo usa dois
            dedos, e porque no computador não há pinça nenhuma. "Ver tudo" volta
            à bacia inteira: sem ele, quem se perde no zoom fica sem saber que
            existe mapa fora da tela. */}
        <div className={estilos.zoom} role="group" aria-label="Zoom do mapa">
          <button
            type="button"
            className={estilos.botaoZoom}
            aria-label="Aproximar"
            onClick={() => aplicarZoom(1.6)}
          >
            +
          </button>
          <button
            type="button"
            className={estilos.botaoZoom}
            aria-label="Afastar"
            onClick={() => aplicarZoom(1 / 1.6)}
          >
            −
          </button>
          {vista.zoom > 1 ? (
            <button
              type="button"
              className={estilos.botaoVerTudo}
              onClick={() => setVista(VISTA_INTEIRA)}
            >
              Ver tudo
            </button>
          ) : null}
        </div>

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

        {/* Painel de UMA RÉGUA, quando o toque foi nela. Vem antes do painel de
            cidade e o substitui: dois no mesmo canto se cobrem. */}
        {reguaSel ? (() => {
          const g = reguasDoMapa.find((r) => (r.codigo || r.titulo) === reguaSel)
          if (!g) return null
          const cotas = cotasOrdenadas(g.cotas)
          return (
            <div className={estilos.painel}>
              <div className={estilos.painelTopo}>
                <strong>{g.nome}</strong>
                <span className={estilos.painelRio}>{g.codigo || 'régua'}</span>
              </div>
              <p className={estilos.painelNivel}>
                {g.nivel != null ? (
                  <>
                    <strong>{metros(g.nivel)}</strong>
                    {g.medidoEm ? <> · {textoIdade(idadeMin(g.medidoEm, agora))}</> : null}
                  </>
                ) : (
                  <span className={estilos.painelSemDado}>sem leitura fresca</span>
                )}
              </p>
              {cotas.length > 0 ? (
                <div className={estilos.painelBloco}>
                  <span className={estilos.painelRotulo}>Cotas DESTA régua</span>
                  <ul>
                    {cotas.map(([k, v]) => (
                      <li key={k}>
                        {ROTULO_COTA[k] ?? k}: {metros(v)}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {/* O porquê de não ter cor, por extenso. Omitir a razão faria a
                  ausência parecer falta de dado — e aqui o dado existe: o que
                  não afirmamos é a faixa. */}
              {g.motivoSemCor ? (
                <div className={estilos.painelBloco}>
                  <span className={estilos.painelRotulo}>Por que não tem cor</span>
                  <p className={estilos.painelRessalva}>{g.motivoSemCor}</p>
                </div>
              ) : null}
              <p className={estilos.painelRessalva}>
                Cada régua tem o zero dela: <strong>estes metros não se comparam</strong>{' '}
                com os de outra régua nem com a cota da cidade.
              </p>
              <button type="button" onClick={() => setReguaSel(null)}>
                fechar
              </button>
            </div>
          )
        })() : null}

        {/* Painel de dados da cidade em foco (mouse por cima ou toque), no canto
            superior direito, abaixo do chip da maré. Traz tudo o que temos dela. */}
        {!reguaSel && (sel ?? hover) ? (() => {
          const foco = (sel ?? hover)!
          const cid = foco.cidade
          const cotas = cotasOrdenadas(cid.cotas_m ?? {})
          const ch = chuvaDaCidade(tempoReal.chuva, foco.rioId, cid.id)
          const brutoSc = nivelSc.get(cid.id) ?? null
          // As réguas da cidade, quando são VÁRIAS. Itajaí tem onze, todas
          // publicadas e frescas, e o Monitor não mostrava nenhuma: o pino azul
          // dizia "várias réguas" e o painel dizia "sem leitura fresca" — falso,
          // e justamente na cidade da foz, que recebe os dois rios.
          const daCidade = leiturasDaCidade(tempoReal, foco.rioId, cid.id)
          const reguas = reguasComCota(estacoesTempoReal, foco.rioId, cid.id)
          return (
            <div className={estilos.painel}>
              <div className={estilos.painelTopo}>
                <strong>{cid.nome}</strong>
                <span className={estilos.painelRio}>
                  {foco.rioId === 'itajai-mirim' ? 'Itajaí-Mirim' : 'Itajaí-Açu'}
                </span>
              </div>
              <div className={estilos.painelFaixa}>
                <span
                  className={estilos.amostra}
                  style={{ background: `var(${VAR_LEGENDA[foco.faixa]})` }}
                />
                {ROTULO_FAIXA[foco.faixa]}
              </div>
              <p className={estilos.painelNivel}>
                {foco.nivel != null ? (
                  <>
                    <strong>{metros(foco.nivel)}</strong>
                    {foco.medidoEm ? <> · {textoIdade(idadeMin(foco.medidoEm, agora))}</> : null}
                  </>
                ) : daCidade.length > 1 ? null : (
                  <span className={estilos.painelSemDado}>sem leitura fresca</span>
                )}
              </p>
              {/* Cidade de várias réguas: todas, sem eleger nenhuma — o mesmo
                  componente da tela do rio, com o aviso de que os zeros são
                  diferentes e os números não se comparam. Dizer "sem leitura"
                  com onze réguas vivas era esconder o dado, não protegê-lo. */}
              {foco.nivel == null && daCidade.length > 1 ? (
                <div className={estilos.painelBloco}>
                  <VariasReguas
                    leituras={daCidade}
                    reguas={reguas}
                    cidade={cid}
                    agora={agora}
                  />
                </div>
              ) : null}
              {cotas.length > 0 ? (
                <div className={estilos.painelBloco}>
                  <span className={estilos.painelRotulo}>Cotas da régua</span>
                  <ul>
                    {cotas.map(([k, v]) => (
                      <li key={k}>
                        {ROTULO_COTA[k] ?? k}: {metros(v)}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className={estilos.painelSemCota}>
                  Sem cota de referência cadastrada — a faixa fica cinza.
                </p>
              )}
              {brutoSc ? (
                <div className={estilos.painelBloco}>
                  <span className={estilos.painelRotulo}>Nível bruto — rede estadual (DCSC)</span>
                  <p className={estilos.painelExtra}>
                    <strong>{metros(brutoSc.nivelBrutoM)}</strong>
                    {brutoSc.medidoEm ? <> · {textoIdade(idadeMin(brutoSc.medidoEm, agora))}</> : null}
                    {' — '}
                    {brutoSc.estacao}
                  </p>
                  <p className={estilos.painelRessalva}>
                    Régua PRÓPRIA da estação estadual, zero diferente da régua municipal —
                    não comparável às cotas acima nem à faixa de cor deste pino.
                  </p>
                </div>
              ) : null}
              <p className={estilos.painelChuva}>
                {ch && (ch.h1 != null || ch.h24 != null) ? (
                  <>
                    Chuva:{' '}
                    {ch.h1 != null ? (
                      <>
                        <strong>{ch.h1.toFixed(1)} mm</strong> (1 h)
                      </>
                    ) : null}
                    {ch.h1 != null && ch.h24 != null ? ' · ' : ''}
                    {ch.h24 != null ? <>{ch.h24.toFixed(0)} mm (24 h)</> : null}
                  </>
                ) : (
                  'Sem chuva recente medida aqui.'
                )}
              </p>
              {cid.sub_bacia ? (
                <p className={estilos.painelExtra}>Sub-bacia: {cid.sub_bacia}</p>
              ) : null}
              {cid.km_da_foz != null ? (
                <p className={estilos.painelExtra}>{cid.km_da_foz} km até a foz</p>
              ) : null}
              <p className={estilos.painelAcao}>{ACAO_FAIXA[foco.faixa]}</p>
              {/* A cidade primeiro, o rio depois. Quem toca no pino de Gaspar
                  quer Gaspar — o rio inteiro e a segunda pergunta, nao a
                  primeira. */}
              <button
                type="button"
                className={estilos.dicaDetalhe}
                onClick={() => navigate(`${rotaDoRio(foco.rioId)}/${cid.id}`)}
              >
                Abrir {cid.nome} →
              </button>
              <button
                type="button"
                className={estilos.dicaSecundaria}
                onClick={() => navigate(rotaDoRio(foco.rioId))}
              >
                Ver {foco.rioId === 'itajai-mirim' ? 'o Mirim' : 'o Açu'} inteiro
              </button>
              <p className={estilos.painelRessalva}>
                Nível na régua <strong>desta</strong> cidade. Não compare metros entre
                cidades — a comparação é pela faixa (cor).
              </p>
            </div>
          )
        })() : null}
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
