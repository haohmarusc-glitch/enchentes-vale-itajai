import { useEffect, useMemo, useRef, useState } from 'react'
import type { Cidade, TabuaMare } from '../dados/tipos'
import type { EstadoTempoReal } from '../dados/tempoReal'
import { leituraDaCidade, leiturasDaCidade } from '../dados/tempoReal'
import { deBrasilia, faixaDaCidade, type Faixa } from '../logica/tempoReal'
import { estadoMareAgora, type EstadoMare } from '../logica/mare'
import { ROTULO_FAIXA, ACAO_FAIXA } from './LegendaFaixas'
import { metros } from '../logica/formato'
import {
  acumuladoEspinha,
  enquadrar,
  limitesDe,
  maisProximoNoRio,
  posicoesCorrenteza,
  progressoNaEspinha,
  projetar,
  trechoDoPonto,
  LARGURA_FAIXA,
  VEL_FAIXA,
  type Enquadramento,
  type LonLat,
} from '../logica/mapaCanvas'
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

// A cor de cada faixa vem da MESMA variável CSS que a legenda e o diagrama usam
// (fonte única). 'varias' não tem variável própria: usa o azul da água, como no
// mapa antigo. Fallbacks só para o caso improvável de a variável não resolver.
const VAR_FAIXA: Record<Faixa, string> = {
  normal: '--faixa-normal',
  atencao: '--faixa-atencao',
  alerta: '--faixa-alerta',
  inundacao: '--faixa-inundacao',
  emergencia: '--faixa-emergencia',
  'sem-dado': '--faixa-sem-dado',
  varias: '--agua-clara',
}
const FALLBACK_FAIXA: Record<Faixa, string> = {
  normal: '#2e7d32',
  atencao: '#e6a700',
  alerta: '#e2661a',
  inundacao: '#c62828',
  emergencia: '#c62828',
  'sem-dado': '#9aa7b2',
  varias: '#1c6ea4',
}

/** Um pedaço contínuo do rio de uma só faixa, já projetado em pixels. */
interface Trecho {
  pts: [number, number][]
  faixa: Faixa
  cum: number[]
  total: number
}
/** Uma cidade âncora, já projetada, para o pino e o toque. */
interface Pino {
  cidade: Cidade
  x: number
  y: number
  faixa: Faixa
  nivel: number | null
}
/** O MAR na foz, colorido pela MARÉ (escala própria, nunca a de cheia). */
interface MarVis {
  estado: EstadoMare
  corSea: string
  rotulo: string
  x: number
  y: number
}
interface Cena {
  trechos: Trecho[]
  pinos: Pino[]
  cores: Record<Faixa, string>
  mar: MarVis | null
  largura: number
  altura: number
}

const MARGEM = 18
const ESPACO_SETA = 22 // px entre setas de correnteza
const VEL_PX = 24 // px/s da correnteza na faixa de referência

function corDaFaixa(el: Element, f: Faixa): string {
  const v = getComputedStyle(el).getPropertyValue(VAR_FAIXA[f]).trim()
  return v || FALLBACK_FAIXA[f]
}

function acumularPixels(pts: [number, number][]): { cum: number[]; total: number } {
  const cum = [0]
  for (let i = 1; i < pts.length; i++) {
    const dx = pts[i]![0] - pts[i - 1]![0]
    const dy = pts[i]![1] - pts[i - 1]![1]
    cum.push(cum[i - 1]! + Math.hypot(dx, dy))
  }
  return { cum, total: cum[cum.length - 1] ?? 0 }
}

/** Ponto e direção a uma distância `pos` ao longo de um trecho já acumulado. */
function amostrar(
  t: Trecho,
  pos: number,
): { x: number; y: number; dx: number; dy: number } | null {
  if (t.pts.length < 2) return null
  let j = 0
  while (j < t.cum.length - 1 && t.cum[j + 1]! < pos) j++
  const a = t.pts[j]!
  const b = t.pts[j + 1]!
  const seg = (t.cum[j + 1]! - t.cum[j]!) || 1
  const u = Math.max(0, Math.min(1, (pos - t.cum[j]!) / seg))
  const len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1
  return {
    x: a[0] + (b[0] - a[0]) * u,
    y: a[1] + (b[1] - a[1]) * u,
    dx: (b[0] - a[0]) / len,
    dy: (b[1] - a[1]) / len,
  }
}

/**
 * Monta a cena: cada cidade com coordenada vira âncora encaixada no rio (ordem
 * montante→jusante); a "espinha" por essas âncoras diz, para cada pedaço do
 * traçado, entre quais cidades ele está — e a faixa da cidade a MONTANTE dá a
 * cor daquele trecho, a mesma regra do diagrama. Sem âncora que pinte, o trecho
 * é `sem-dado` (cinza, e sem correnteza).
 */
/** Azul do mar por altura de maré: fundo (baixamar) → claro (preamar). */
function azulMare(altura01: number): string {
  const lo = [18, 50, 74]
  const hi = [47, 134, 201]
  const c = lo.map((v, i) => Math.round(v + (hi[i]! - v) * altura01))
  return `rgba(${c[0]},${c[1]},${c[2]},0.5)`
}

function construirCena(
  el: Element,
  coords: LonLat[][],
  cidades: Cidade[],
  rioId: string,
  tempoReal: EstadoTempoReal,
  agora: Date,
  largura: number,
  altura: number,
  mare: TabuaMare | null,
): Cena {
  const cores = {} as Record<Faixa, string>
  ;(Object.keys(VAR_FAIXA) as Faixa[]).forEach((f) => (cores[f] = corDaFaixa(el, f)))

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
        faixa: faixaDaCidade(cidade, aoVivo, temVarias, agora),
        nivel: aoVivo?.nivel_m ?? null,
        ponto: maisProximoNoRio(coords, alvo) ?? alvo,
      }
    })
  const espinha = ancoras.map((a) => a.ponto)
  const cumEspinha = acumuladoEspinha(espinha)

  const faixaEm = (p: LonLat): Faixa =>
    ancoras.length === 0 ? 'sem-dado' : ancoras[trechoDoPonto(espinha, p)]!.faixa

  const todos = coords.flat()
  const lim = limitesDe(todos.length ? todos : espinha)
  const enq: Enquadramento = enquadrar(
    lim ?? { minLon: -49.5, maxLon: -48.5, minLat: -27.5, maxLat: -26.5 },
    largura,
    altura,
    MARGEM,
  )

  const trechos: Trecho[] = []
  for (const linha of coords) {
    if (linha.length < 2) continue
    // Orienta o way no sentido do rio pela espinha (o OSM não os entrega todos
    // montante→jusante). A cor é por trecho e independe disso; só a correnteza
    // precisa do sentido certo.
    let seq = linha
    if (espinha.length >= 2) {
      const pa = progressoNaEspinha(espinha, cumEspinha, linha[0]!)
      const pb = progressoNaEspinha(espinha, cumEspinha, linha[linha.length - 1]!)
      if (pb < pa) seq = [...linha].reverse()
    }
    // A cor de cada aresta vem do MEIO dela (mesma regra do mapa antigo). Agrupa
    // arestas vizinhas de mesma faixa num trecho só.
    const faixaAresta = (i: number): Faixa =>
      faixaEm([(seq[i - 1]![0] + seq[i]![0]) / 2, (seq[i - 1]![1] + seq[i]![1]) / 2])
    let pts: [number, number][] = [projetar(enq, seq[0]!)]
    let cur = faixaAresta(1)
    for (let i = 1; i < seq.length; i++) {
      pts.push(projetar(enq, seq[i]!))
      const prox = i + 1 < seq.length ? faixaAresta(i + 1) : null
      if (prox !== null && prox !== cur) {
        const { cum, total } = acumularPixels(pts)
        trechos.push({ pts, faixa: cur, cum, total })
        pts = [projetar(enq, seq[i]!)]
        cur = prox
      }
    }
    const { cum, total } = acumularPixels(pts)
    trechos.push({ pts, faixa: cur, cum, total })
  }

  const pinos: Pino[] = ancoras.map((a) => {
    const [x, y] = projetar(enq, a.ponto)
    return { cidade: a.cidade, x, y, faixa: a.faixa, nivel: a.nivel }
  })

  // O MAR na foz. A foz é a cidade mais a LESTE (o oceano fica a leste; Itajaí
  // é o ponto de maior longitude da bacia), então o âncora do mar é o pino de
  // maior x. A cor vem da MARÉ, na sua própria escala azul — nunca a faixa de
  // cheia. Sem tábua, ou instante fora do trecho informado: mar cinza, "sem dado".
  let mar: MarVis | null = null
  const pinoFoz = pinos.reduce<Pino | null>((m, p) => (m === null || p.x > m.x ? p : m), null)
  if (pinoFoz) {
    const paraData = (e: { quando: string; altura_m?: number }) => ({
      quando: deBrasilia(e.quando),
      altura_m: e.altura_m,
    })
    const ma = mare
      ? estadoMareAgora(
          (mare.preamares ?? []).map(paraData),
          (mare.baixamares ?? []).map(paraData),
          agora,
        )
      : { estado: 'sem-dado' as EstadoMare, altura01: null, proxima: null }
    const corSea =
      ma.altura01 === null ? 'rgba(58,76,94,0.42)' : azulMare(ma.altura01)
    const rotulo =
      ma.estado === 'subindo'
        ? 'Maré subindo ▲'
        : ma.estado === 'baixando'
          ? 'Maré baixando ▼'
          : 'Maré: sem dado'
    mar = { estado: ma.estado, corSea, rotulo, x: pinoFoz.x, y: pinoFoz.y }
  }

  return { trechos, pinos, cores, mar, largura, altura }
}

/** Traça a poligonal de um trecho — reusado pelo brilho e pelo núcleo. */
function caminhoTrecho(ctx: CanvasRenderingContext2D, pts: [number, number][]): void {
  ctx.beginPath()
  ctx.moveTo(pts[0]![0], pts[0]![1])
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i]![0], pts[i]![1])
}

/**
 * Fundo escuro + rio luminoso: o que não muda entre quadros. Desenhado uma vez.
 *
 * O visual escuro com o leito brilhando (halo na cor da faixa + núcleo claro)
 * veio do protótipo estudado e do pedido "animação moderna". O brilho é da COR
 * da faixa — logo diz o nível, não decora. O trecho `sem-dado` foge de tudo
 * isso: cinza apagado, SEM brilho e mais fino, para nunca parecer um leito
 * "aceso"/seguro onde não há medida.
 */
function desenharBase(ctx: CanvasRenderingContext2D, cena: Cena): void {
  ctx.clearRect(0, 0, cena.largura, cena.altura)
  const g = ctx.createLinearGradient(0, 0, 0, cena.altura)
  g.addColorStop(0, '#0c1c2e')
  g.addColorStop(1, '#081019')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, cena.largura, cena.altura)

  // O MAR entra ANTES do rio (fica atrás do leito e dos pinos). É a leste da
  // foz — como Itajaí é o ponto mais a leste da bacia, o mar ocupa a faixa
  // direita do mapa.
  desenharMar(ctx, cena)

  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'

  // 1) Halo: traço largo na cor da faixa, com sombra da mesma cor (bloom). Cinza
  //    não entra aqui.
  for (const t of cena.trechos) {
    if (t.pts.length < 2 || t.faixa === 'sem-dado') continue
    caminhoTrecho(ctx, t.pts)
    ctx.strokeStyle = cena.cores[t.faixa]
    ctx.shadowColor = cena.cores[t.faixa]
    ctx.shadowBlur = 12 * LARGURA_FAIXA[t.faixa]
    ctx.globalAlpha = 0.9
    ctx.lineWidth = 3.4 * LARGURA_FAIXA[t.faixa]
    ctx.stroke()
  }
  ctx.shadowBlur = 0

  // 2) O cinza (sem-dado), apagado e sem brilho, por baixo dos núcleos claros.
  for (const t of cena.trechos) {
    if (t.pts.length < 2 || t.faixa !== 'sem-dado') continue
    caminhoTrecho(ctx, t.pts)
    ctx.strokeStyle = cena.cores['sem-dado']
    ctx.globalAlpha = 0.5
    ctx.lineWidth = 2.4
    ctx.stroke()
  }

  // 3) Núcleo claro no leito colorido, para o "quente" do neon.
  for (const t of cena.trechos) {
    if (t.pts.length < 2 || t.faixa === 'sem-dado') continue
    caminhoTrecho(ctx, t.pts)
    ctx.strokeStyle = 'rgba(255,255,255,0.5)'
    ctx.globalAlpha = 1
    ctx.lineWidth = 1.4 * LARGURA_FAIXA[t.faixa]
    ctx.stroke()
  }
  ctx.globalAlpha = 1

  // A etiqueta da maré, por cima de tudo da base (mas ainda sob os pinos).
  desenharEtiquetaMare(ctx, cena)
}

/**
 * O MAR na foz, colorido pela MARÉ (escala azul PRÓPRIA, jamais a de cheia).
 * Ocupa a faixa direita (leste) do mapa a partir da foz, com transparência para
 * não cobrir o leito. Cinza translúcido quando não há tábua — o mar continua
 * ali, só sem número.
 */
function desenharMar(ctx: CanvasRenderingContext2D, cena: Cena): void {
  const mar = cena.mar
  if (!mar) return
  const x0 = Math.min(mar.x - 6, cena.largura * 0.72)
  const g = ctx.createLinearGradient(x0, 0, cena.largura, 0)
  g.addColorStop(0, 'rgba(0,0,0,0)')
  g.addColorStop(1, mar.corSea)
  ctx.fillStyle = g
  ctx.fillRect(x0, 0, cena.largura - x0, cena.altura)
}

/** Chip "Mar / Maré subindo·baixando·sem dado" no alto, ancorado à direita. */
function desenharEtiquetaMare(ctx: CanvasRenderingContext2D, cena: Cena): void {
  const mar = cena.mar
  if (!mar) return
  ctx.font = '600 11px system-ui, sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  const texto = `Mar · ${mar.rotulo}`
  const w = ctx.measureText(texto).width
  const padX = 8
  const h = 20
  const x = cena.largura - (w + padX * 2) - 8
  const y = 8
  ctx.fillStyle = 'rgba(6,16,26,0.72)'
  const r = 6
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.arcTo(x + w + padX * 2, y, x + w + padX * 2, y + h, r)
  ctx.arcTo(x + w + padX * 2, y + h, x, y + h, r)
  ctx.arcTo(x, y + h, x, y, r)
  ctx.arcTo(x, y, x + w + padX * 2, y, r)
  ctx.closePath()
  ctx.fill()
  ctx.fillStyle = mar.estado === 'sem-dado' ? '#9fb2c4' : '#bfe0ff'
  ctx.fillText(texto, x + padX, y + h / 2 + 0.5)
}

/**
 * Setas da correnteza descendo o rio — o movimento que significa o nível. Cada
 * seta é desenhada duas vezes: um traço escuro por baixo (halo, para contrastar
 * tanto no laranja quanto no vermelho) e o branco por cima. Tamanho e largura
 * crescem um pouco com a faixa, junto com a velocidade, para o olhar captar o
 * sentido do fluxo de imediato.
 */
function desenharCorrenteza(ctx: CanvasRenderingContext2D, cena: Cena, tempo: number): void {
  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'
  for (const t of cena.trechos) {
    // cinza não corre; trecho curto não recebe seta — regra na função pura.
    const posicoes = posicoesCorrenteza(t.total, VEL_FAIXA[t.faixa], tempo, ESPACO_SETA, VEL_PX)
    if (posicoes.length === 0) continue
    const h = 4.6 * LARGURA_FAIXA[t.faixa] // meia-altura da seta
    for (let camada = 0; camada < 2; camada++) {
      ctx.strokeStyle = camada === 0 ? 'rgba(0,0,0,0.28)' : 'rgba(255,255,255,0.97)'
      ctx.lineWidth = camada === 0 ? 3.4 : 2.2
      for (const pos of posicoes) {
        const a = amostrar(t, pos)
        if (!a) continue
        const px = -a.dy // perpendicular
        const py = a.dx
        ctx.beginPath()
        ctx.moveTo(a.x - a.dx * h + px * h, a.y - a.dy * h + py * h)
        ctx.lineTo(a.x + a.dx * h, a.y + a.dy * h) // ponta, no sentido de jusante
        ctx.lineTo(a.x - a.dx * h - px * h, a.y - a.dy * h - py * h)
        ctx.stroke()
      }
    }
  }
}

// Gravidade da faixa, para o rótulo da cidade MAIS grave ganhar o espaço quando
// os nomes se amontoam (é numa cheia que o nome da cidade em alerta precisa
// aparecer). 'sem-dado'/'varias' por último: não são pontos da escala.
const GRAVIDADE: Record<Faixa, number> = {
  emergencia: 6,
  inundacao: 5,
  alerta: 4,
  atencao: 3,
  normal: 2,
  varias: 1,
  'sem-dado': 0,
}

/** Pinos das cidades por cima, cada um na cor da faixa; o selecionado com anel. */
function desenharPinos(
  ctx: CanvasRenderingContext2D,
  cena: Cena,
  selecionada: string | null,
): void {
  // 1) Os pontos (sempre todos — nenhuma cidade some do mapa). Sobre o fundo
  // escuro, o pino tem brilho na cor da faixa e um anel claro; o cinza não brilha.
  for (const p of cena.pinos) {
    const sel = p.cidade.id === selecionada
    const cinza = p.faixa === 'sem-dado'
    if (sel) {
      ctx.beginPath()
      ctx.arc(p.x, p.y, 12, 0, Math.PI * 2)
      ctx.strokeStyle = 'rgba(230,240,250,0.9)'
      ctx.lineWidth = 2
      ctx.stroke()
    }
    ctx.beginPath()
    ctx.arc(p.x, p.y, sel ? 8 : 7, 0, Math.PI * 2)
    ctx.fillStyle = cena.cores[p.faixa]
    ctx.shadowColor = cinza ? 'transparent' : cena.cores[p.faixa]
    ctx.shadowBlur = cinza ? 0 : 10
    ctx.fill()
    ctx.shadowBlur = 0
    ctx.lineWidth = 2
    ctx.strokeStyle = cinza ? 'rgba(180,195,210,0.8)' : 'rgba(255,255,255,0.92)'
    ctx.stroke()
  }

  // 2) Os nomes, com anticolisão: onde os pinos se amontoam (a foz do Açu), o
  // rótulo da faixa MAIS grave (e a cidade selecionada) tem prioridade; um nome
  // que cairia por cima de outro é omitido — o ponto continua lá e o toque abre
  // o detalhe. O texto é preso dentro do canvas para não cortar na borda.
  ctx.font = '600 11px system-ui, sans-serif'
  ctx.textBaseline = 'bottom'
  const ordem = [...cena.pinos].sort((a, b) => {
    const sa = a.cidade.id === selecionada ? 100 : GRAVIDADE[a.faixa]
    const sb = b.cidade.id === selecionada ? 100 : GRAVIDADE[b.faixa]
    return sb - sa
  })
  const caixas: { x0: number; y0: number; x1: number; y1: number }[] = []
  const alt = 13
  const pad = 3
  for (const p of ordem) {
    const w = ctx.measureText(p.cidade.nome).width
    const meia = w / 2
    const cx = Math.max(pad + meia, Math.min(cena.largura - pad - meia, p.x))
    const baseY = p.y - 9
    const caixa = { x0: cx - meia - 1, y0: baseY - alt, x1: cx + meia + 1, y1: baseY + 1 }
    const bate = caixas.some(
      (c) => caixa.x0 < c.x1 && caixa.x1 > c.x0 && caixa.y0 < c.y1 && caixa.y1 > c.y0,
    )
    if (bate && p.cidade.id !== selecionada) continue
    caixas.push(caixa)
    ctx.textAlign = 'center'
    // Texto claro com contorno escuro — legível sobre o fundo escuro e sobre o
    // leito luminoso.
    ctx.lineWidth = 3.2
    ctx.strokeStyle = 'rgba(4,12,20,0.92)'
    ctx.strokeText(p.cidade.nome, cx, baseY)
    ctx.fillStyle = '#eaf1f8'
    ctx.fillText(p.cidade.nome, cx, baseY)
  }
}

/**
 * Mapa geográfico do rio em <canvas>, no espírito do Kikikuru: o traçado real
 * (OpenStreetMap) pintado por trecho — cada trecho na cor da faixa da cidade a
 * montante — com a correnteza animada descendo no sentido do rio, MAIS RÁPIDA
 * onde o nível está mais alto (a animação significa o nível, não enfeita).
 * Trecho sem cidade que o pinte fica cinza e PARADO — não fingimos conhecer uma
 * água que não medimos. Toque numa cidade abre as cotas de rua e o abrigo dela.
 *
 * Substitui o mapa Leaflet do rio: dispensa o mapa-base de ruas (que aqui só
 * mostrava "onde é"), fica mais leve nesse ponto e desenha a árvore do Açu com
 * cada braço na sua linha. (O Leaflet segue no pacote pelo mapa de manchas de
 * Itajaí, onde as ruas do fundo são essenciais.)
 */
export default function MapaRios({
  rioId,
  cidades,
  tempoReal,
  agora,
  aoSelecionar,
  mare = null,
}: {
  rioId: string
  cidades: Cidade[]
  tempoReal: EstadoTempoReal
  agora: Date
  /** Chamado ao tocar numa cidade — abre o detalhe dela na tela do rio. */
  aoSelecionar?: (cidadeId: string) => void
  /** Tábua de maré de Itajaí — colore o MAR na foz. Ausente = mar cinza. */
  mare?: TabuaMare | null
}) {
  const divRef = useRef<HTMLDivElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [coords, setCoords] = useState<LonLat[][] | null>(null)
  const [tam, setTam] = useState<{ w: number; h: number }>({ w: 0, h: 0 })
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
  // precisa de 60vh de altura com o traçado numa faixa fina no meio. Calcula da
  // largura atual e da razão geográfica; a CSS ainda impõe um piso.
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

    const cena = construirCena(canvas, coords, cidades, rioId, tempoReal, agora, tam.w, tam.h, mare)
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
      desenharCorrenteza(ctx, cena, reduz ? 0 : (t - inicio) / 1000)
      desenharPinos(ctx, cena, selRef.current)
      if (!reduz) raf = requestAnimationFrame(quadro)
    }
    raf = requestAnimationFrame(quadro)
    return () => cancelAnimationFrame(raf)
  }, [coords, cidades, tempoReal, agora, tam, rioId, mare])

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
