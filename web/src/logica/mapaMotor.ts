/**
 * Motor do mapa em <canvas> — construção da cena e desenho, compartilhados pelo
 * mapa de UM rio (`MapaRios`) e pela tela cheia da BACIA inteira (`MonitorBacia`).
 *
 * A geometria pura (projeção, encaixe no rio, orientação jusante, trecho,
 * movimento das setas) fica em `mapaCanvas.ts` e é testada lá. Aqui é a camada
 * que junta essa geometria com o dado ao vivo (faixa por cidade, maré na foz) e
 * pinta o fundo escuro com o leito luminoso.
 *
 * REGRAS que este módulo carrega (não são detalhe de desenho):
 *  - cor = faixa da régua da cidade, NUNCA metro entre cidades;
 *  - trecho sem régua que o pinte = cinza, apagado e PARADO (não se anima uma
 *    água que não se mede — `VEL_FAIXA['sem-dado'] = 0`);
 *  - o MAR na foz é colorido pela MARÉ, escala azul PRÓPRIA, jamais a de cheia
 *    (maré alta não é cheia; ela trava o escoamento).
 */
import type { Cidade, TabuaMare } from '../dados/tipos'
import type { EstadoTempoReal } from '../dados/tempoReal'
import { leituraDaCidade, leiturasDaCidade } from '../dados/tempoReal'
import type { BrutoEstadual, NivelSc } from '../dados/nivelSc'
import { deBrasilia, faixaDaCidade, idadeMin, textoIdade, type Faixa } from '../logica/tempoReal'
import { estadoMareAgora, type EstadoMare } from '../logica/mare'
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

// A cor de cada faixa vem da MESMA variável CSS que a legenda e o diagrama usam
// (fonte única). 'varias' não tem variável própria: usa o azul da água.
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

/** Gravidade da faixa, para o rótulo da cidade MAIS grave ganhar o espaço. */
const GRAVIDADE: Record<Faixa, number> = {
  emergencia: 6,
  inundacao: 5,
  alerta: 4,
  atencao: 3,
  normal: 2,
  varias: 1,
  'sem-dado': 0,
}

export const MARGEM = 18
const ESPACO_SETA = 22 // px entre setas de correnteza
const VEL_PX = 24 // px/s da correnteza na faixa de referência

/** Um pedaço contínuo do rio de uma só faixa, já projetado em pixels. */
export interface Trecho {
  pts: [number, number][]
  faixa: Faixa
  cum: number[]
  total: number
  /** Posição montante→jusante do trecho no rio, 0 (nascente) a 1 (foz). É o que
   *  a onda usa para descer o rio até o mar. */
  progMid: number
}
/** Uma cidade âncora, já projetada, para o pino e o toque. */
export interface Pino {
  cidade: Cidade
  rioId: string
  x: number
  y: number
  faixa: Faixa
  nivel: number | null
  medidoEm: Date | null
  /**
   * Nível BRUTO da rede estadual (DCSC), quando existir para a cidade — datum
   * PRÓPRIO da estação, nunca comparável às cotas municipais (`cidade.cotas_m`)
   * nem usado para calcular `faixa`. Só preenche a lacuna das cidades sem
   * fonte municipal (a maioria das cabeceiras do Açu): o pino mostra este
   * valor, claramente rotulado como bruto, em vez de ficar sem número nenhum.
   */
  nivelBruto: BrutoEstadual | null
}
/** O MAR na foz, colorido pela MARÉ (escala própria, nunca a de cheia). */
export interface MarVis {
  estado: EstadoMare
  corSea: string
  rotulo: string
  x: number
  y: number
}
export interface Cena {
  trechos: Trecho[]
  pinos: Pino[]
  cores: Record<Faixa, string>
  mar: MarVis | null
  enq: Enquadramento
  largura: number
  altura: number
}

/** Um rio a desenhar: seu traçado e as cidades que o pintam. */
export interface RioParaCena {
  rioId: string
  coords: LonLat[][]
  cidades: Cidade[]
}

export function corDaFaixa(el: Element, f: Faixa): string {
  const v = getComputedStyle(el).getPropertyValue(VAR_FAIXA[f]).trim()
  return v || FALLBACK_FAIXA[f]
}

/** Azul do mar por altura de maré: fundo (baixamar) → claro (preamar). */
function azulMare(altura01: number): string {
  const lo = [18, 50, 74]
  const hi = [47, 134, 201]
  const c = lo.map((v, i) => Math.round(v + (hi[i]! - v) * altura01))
  return `rgba(${c[0]},${c[1]},${c[2]},0.5)`
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
  const seg = t.cum[j + 1]! - t.cum[j]! || 1
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
 * Monta a cena de UM OU VÁRIOS rios sobre um enquadramento comum. Cada rio é
 * colorido pelas SUAS cidades (espinha própria, montante→jusante); os traçados e
 * pinos de todos entram na mesma cena. O MAR ancora na foz (a cidade mais a
 * leste, pois o oceano fica a leste — Itajaí é o ponto de maior longitude).
 */
/**
 * Leitura de uma cidade num instante do passado, para a REPRODUÇÃO (playback):
 * o nível medido ATÉ aquele instante, nunca o futuro. Quando presente, substitui
 * a leitura ao vivo; ausente, o mapa usa o `tempoReal` (o agora).
 */
export type LeituraNaHora = (
  rioId: string,
  cidadeId: string,
) => { nivel_m: number; medidoEm: Date | null } | null

export function construirCena(
  el: Element,
  rios: RioParaCena[],
  tempoReal: EstadoTempoReal,
  agora: Date,
  largura: number,
  altura: number,
  mare: TabuaMare | null,
  leituraNaHora?: LeituraNaHora,
  /**
   * Nível bruto da rede estadual (DCSC), por cidade. Só usado AO VIVO (não na
   * reprodução — a série do bruto não está encaixada no playback, e mostrar um
   * valor "atual" durante o passado seria inventar). Opcional: quem não passa
   * (MapaRios, hoje) mantém o comportamento de sempre.
   */
  nivelBrutoSc?: NivelSc,
): Cena {
  const cores = {} as Record<Faixa, string>
  ;(Object.keys(VAR_FAIXA) as Faixa[]).forEach((f) => (cores[f] = corDaFaixa(el, f)))

  // Enquadramento comum: cobre o traçado de TODOS os rios.
  const todos = rios.flatMap((r) => r.coords.flat())
  const lim = limitesDe(todos)
  const enq: Enquadramento = enquadrar(
    lim ?? { minLon: -50.2, maxLon: -48.5, minLat: -27.6, maxLat: -26.7 },
    largura,
    altura,
    MARGEM,
  )

  const trechos: Trecho[] = []
  const pinosPorId = new Map<string, Pino>()

  for (const rio of rios) {
    const ancoras = rio.cidades
      .filter((c) => c.coordenadas)
      .map((cidade) => {
        const coord = cidade.coordenadas!
        const alvo: LonLat = [coord[1], coord[0]] // [lon,lat] para casar com o rio
        // Na reprodução, a leitura vem da série no instante t; ao vivo, do tempoReal.
        const aoVivo = leituraNaHora
          ? leituraNaHora(rio.rioId, cidade.id)
          : leituraDaCidade(tempoReal, rio.rioId, cidade.id)
        const temVarias =
          !leituraNaHora &&
          aoVivo === null &&
          leiturasDaCidade(tempoReal, rio.rioId, cidade.id).length > 1
        // Bruto só entra AO VIVO (não em leituraNaHora/reprodução — ver o
        // parâmetro nivelBrutoSc).
        const bruto = !leituraNaHora ? (nivelBrutoSc?.get(cidade.id) ?? null) : null
        return {
          cidade,
          faixa: faixaDaCidade(cidade, aoVivo, temVarias, agora),
          nivel: aoVivo?.nivel_m ?? null,
          medidoEm: aoVivo?.medidoEm ?? null,
          nivelBruto: bruto,
          ponto: maisProximoNoRio(rio.coords, alvo) ?? alvo,
        }
      })
    const espinha = ancoras.map((a) => a.ponto)
    const cumEspinha = acumuladoEspinha(espinha)
    const faixaEm = (p: LonLat): Faixa =>
      ancoras.length === 0 ? 'sem-dado' : ancoras[trechoDoPonto(espinha, p)]!.faixa

    for (const linha of rio.coords) {
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
      const faixaAresta = (i: number): Faixa =>
        faixaEm([(seq[i - 1]![0] + seq[i]![0]) / 2, (seq[i - 1]![1] + seq[i]![1]) / 2])
      // Progresso 0..1 (nascente→foz) do trecho seq[a..b], para a onda descer.
      const progMax = cumEspinha[cumEspinha.length - 1] || 1
      const progMidDe = (a: number, b: number): number => {
        if (espinha.length < 2) return 0.5
        const pa = progressoNaEspinha(espinha, cumEspinha, seq[a]!)
        const pb = progressoNaEspinha(espinha, cumEspinha, seq[b]!)
        return Math.max(0, Math.min(1, (pa + pb) / 2 / progMax))
      }
      let pts: [number, number][] = [projetar(enq, seq[0]!)]
      let cur = faixaAresta(1)
      let ini = 0
      const empurra = (fim: number) => {
        const { cum, total } = acumularPixels(pts)
        trechos.push({ pts, faixa: cur, cum, total, progMid: progMidDe(ini, fim) })
      }
      for (let i = 1; i < seq.length; i++) {
        pts.push(projetar(enq, seq[i]!))
        const prox = i + 1 < seq.length ? faixaAresta(i + 1) : null
        if (prox !== null && prox !== cur) {
          empurra(i)
          pts = [projetar(enq, seq[i]!)]
          cur = prox
          ini = i
        }
      }
      empurra(seq.length - 1)
    }

    for (const a of ancoras) {
      // Cidade que aparece em dois rios (a foz, Itajaí) entra uma vez só. Fica
      // com a leitura mais informativa (a que não é sem-dado).
      const existente = pinosPorId.get(a.cidade.id)
      if (existente && existente.faixa !== 'sem-dado') continue
      const [x, y] = projetar(enq, a.ponto)
      pinosPorId.set(a.cidade.id, {
        cidade: a.cidade,
        rioId: rio.rioId,
        x,
        y,
        faixa: a.faixa,
        nivel: a.nivel,
        medidoEm: a.medidoEm,
        nivelBruto: a.nivelBruto,
      })
    }
  }

  const pinos = [...pinosPorId.values()]

  // O MAR na foz (pino mais a leste).
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
    const corSea = ma.altura01 === null ? 'rgba(58,76,94,0.42)' : azulMare(ma.altura01)
    const rotulo =
      ma.estado === 'subindo'
        ? 'Maré subindo ▲'
        : ma.estado === 'baixando'
          ? 'Maré baixando ▼'
          : 'Maré: sem dado'
    mar = { estado: ma.estado, corSea, rotulo, x: pinoFoz.x, y: pinoFoz.y }
  }

  return { trechos, pinos, cores, mar, enq, largura, altura }
}

function caminhoTrecho(ctx: CanvasRenderingContext2D, pts: [number, number][]): void {
  ctx.beginPath()
  ctx.moveTo(pts[0]![0], pts[0]![1])
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i]![0], pts[i]![1])
}

/** Fundo escuro + rio luminoso + mar: o que não muda entre quadros. */
export function desenharBase(ctx: CanvasRenderingContext2D, cena: Cena, escala = 1): void {
  ctx.clearRect(0, 0, cena.largura, cena.altura)
  const g = ctx.createLinearGradient(0, 0, 0, cena.altura)
  g.addColorStop(0, '#0c1c2e')
  g.addColorStop(1, '#081019')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, cena.largura, cena.altura)

  // O MAR entra ANTES do rio (fica atrás do leito e dos pinos).
  desenharMar(ctx, cena)

  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'

  // 1) Halo: traço largo na cor da faixa, com sombra da mesma cor (bloom).
  for (const t of cena.trechos) {
    if (t.pts.length < 2 || t.faixa === 'sem-dado') continue
    caminhoTrecho(ctx, t.pts)
    ctx.strokeStyle = cena.cores[t.faixa]
    ctx.shadowColor = cena.cores[t.faixa]
    ctx.shadowBlur = 12 * LARGURA_FAIXA[t.faixa] * escala
    ctx.globalAlpha = 0.9
    ctx.lineWidth = 3.4 * LARGURA_FAIXA[t.faixa] * escala
    ctx.stroke()
  }
  ctx.shadowBlur = 0

  // 2) O cinza (sem-dado), apagado e sem brilho.
  for (const t of cena.trechos) {
    if (t.pts.length < 2 || t.faixa !== 'sem-dado') continue
    caminhoTrecho(ctx, t.pts)
    ctx.strokeStyle = cena.cores['sem-dado']
    ctx.globalAlpha = 0.5
    ctx.lineWidth = 2.4 * escala
    ctx.stroke()
  }

  // 3) Núcleo claro no leito colorido.
  for (const t of cena.trechos) {
    if (t.pts.length < 2 || t.faixa === 'sem-dado') continue
    caminhoTrecho(ctx, t.pts)
    ctx.strokeStyle = 'rgba(255,255,255,0.5)'
    ctx.globalAlpha = 1
    ctx.lineWidth = 1.4 * LARGURA_FAIXA[t.faixa] * escala
    ctx.stroke()
  }
  ctx.globalAlpha = 1

  desenharEtiquetaMare(ctx, cena, escala)
}

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

function desenharEtiquetaMare(ctx: CanvasRenderingContext2D, cena: Cena, escala: number): void {
  const mar = cena.mar
  if (!mar) return
  ctx.font = `600 ${Math.round(11 * escala)}px system-ui, sans-serif`
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  const texto = `Mar · ${mar.rotulo}`
  const w = ctx.measureText(texto).width
  const padX = 8 * escala
  const h = 20 * escala
  const x = cena.largura - (w + padX * 2) - 8 * escala
  const y = 8 * escala
  ctx.fillStyle = 'rgba(6,16,26,0.72)'
  const r = 6 * escala
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

/** Setas da correnteza descendo o rio — o movimento que significa o nível. */
export function desenharCorrenteza(
  ctx: CanvasRenderingContext2D,
  cena: Cena,
  tempo: number,
  escala = 1,
): void {
  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'
  for (const t of cena.trechos) {
    const posicoes = posicoesCorrenteza(
      t.total,
      VEL_FAIXA[t.faixa],
      tempo,
      ESPACO_SETA * escala,
      VEL_PX * escala,
    )
    if (posicoes.length === 0) continue
    const h = 4.6 * LARGURA_FAIXA[t.faixa] * escala
    for (let camada = 0; camada < 2; camada++) {
      ctx.strokeStyle = camada === 0 ? 'rgba(0,0,0,0.28)' : 'rgba(255,255,255,0.97)'
      ctx.lineWidth = (camada === 0 ? 3.4 : 2.2) * escala
      for (const pos of posicoes) {
        const a = amostrar(t, pos)
        if (!a) continue
        const px = -a.dy
        const py = a.dx
        ctx.beginPath()
        ctx.moveTo(a.x - a.dx * h + px * h, a.y - a.dy * h + py * h)
        ctx.lineTo(a.x + a.dx * h, a.y + a.dy * h)
        ctx.lineTo(a.x - a.dx * h - px * h, a.y - a.dy * h - py * h)
        ctx.stroke()
      }
    }
  }
}

/** Uma volta da onda (nascente → mar), em segundos. */
const PERIODO_ONDA = 5.5
/** Largura da crista, em fração do curso (0..1). */
const SIGMA_ONDA = 0.09

/**
 * A ONDA descendo o rio até o mar: uma crista de luz (azul-água, NÃO a cor de
 * faixa) que varre cada rio da nascente à foz e repete. É o "a água desce para o
 * mar" que o mapa mostra por cima do leito colorido — direção e movimento, sem
 * afirmar nível (a faixa continua sendo o sinal honesto; a onda é o fluxo ao
 * mar). No trecho cinza a crista é mais fraca, para não competir com o dado.
 */
export function desenharOnda(
  ctx: CanvasRenderingContext2D,
  cena: Cena,
  tempo: number,
  escala = 1,
): void {
  const frente = ((tempo / PERIODO_ONDA) % 1 + 1) % 1
  ctx.lineJoin = 'round'
  ctx.lineCap = 'round'
  for (const t of cena.trechos) {
    if (t.pts.length < 2) continue
    let d = t.progMid - frente
    if (d > 0.5) d -= 1
    else if (d < -0.5) d += 1
    const alpha = Math.exp(-((d / SIGMA_ONDA) ** 2)) * (t.faixa === 'sem-dado' ? 0.32 : 0.62)
    if (alpha < 0.03) continue
    caminhoTrecho(ctx, t.pts)
    ctx.strokeStyle = `rgba(150,220,255,${alpha.toFixed(3)})`
    ctx.lineWidth = (t.faixa === 'sem-dado' ? 2 : 3) * escala
    ctx.stroke()
  }
}

export interface OpcoesPinos {
  escala?: number
  /** Mostra a idade da leitura sob o nome (para a tela de monitoramento). */
  mostrarIdade?: boolean
  agora?: Date
}

/** Pinos das cidades por cima, cada um na cor da faixa; o selecionado com anel. */
export function desenharPinos(
  ctx: CanvasRenderingContext2D,
  cena: Cena,
  selecionada: string | null,
  opcoes: OpcoesPinos = {},
): void {
  const escala = opcoes.escala ?? 1
  const raio = 7 * escala
  for (const p of cena.pinos) {
    const sel = p.cidade.id === selecionada
    const cinza = p.faixa === 'sem-dado'
    if (sel) {
      ctx.beginPath()
      ctx.arc(p.x, p.y, raio + 5 * escala, 0, Math.PI * 2)
      ctx.strokeStyle = 'rgba(230,240,250,0.9)'
      ctx.lineWidth = 2 * escala
      ctx.stroke()
    }
    ctx.beginPath()
    ctx.arc(p.x, p.y, sel ? raio + 1 * escala : raio, 0, Math.PI * 2)
    ctx.fillStyle = cena.cores[p.faixa]
    ctx.shadowColor = cinza ? 'transparent' : cena.cores[p.faixa]
    ctx.shadowBlur = cinza ? 0 : 10 * escala
    ctx.fill()
    ctx.shadowBlur = 0
    ctx.lineWidth = 2 * escala
    ctx.strokeStyle = cinza ? 'rgba(180,195,210,0.8)' : 'rgba(255,255,255,0.92)'
    ctx.stroke()
  }

  // Nomes com anticolisão: a faixa MAIS grave (e a selecionada) tem prioridade.
  const fonte = Math.round(11 * escala)
  ctx.font = `600 ${fonte}px system-ui, sans-serif`
  ctx.textBaseline = 'bottom'
  const ordem = [...cena.pinos].sort((a, b) => {
    const sa = a.cidade.id === selecionada ? 100 : GRAVIDADE[a.faixa]
    const sb = b.cidade.id === selecionada ? 100 : GRAVIDADE[b.faixa]
    return sb - sa
  })
  const caixas: { x0: number; y0: number; x1: number; y1: number }[] = []
  const alt = 13 * escala
  const pad = 3 * escala
  for (const p of ordem) {
    const nome = p.cidade.nome
    const idade =
      opcoes.mostrarIdade && opcoes.agora && p.medidoEm
        ? textoIdade(idadeMin(p.medidoEm, opcoes.agora))
        : null
    // Sem leitura calibrada (municipal), mas com bruto DCSC: mostra o bruto em
    // vez de deixar a cidade sem número — é a lacuna que a rede estadual
    // preenche na maioria das cabeceiras do Açu. Nunca soma nem substitui o
    // calibrado; só aparece quando ele falta.
    const usaBruto = p.nivel == null && p.nivelBruto != null
    const idadeBruto =
      usaBruto && opcoes.mostrarIdade && opcoes.agora && p.nivelBruto?.medidoEm
        ? textoIdade(idadeMin(p.nivelBruto.medidoEm, opcoes.agora))
        : null
    // Sub-linha ao lado do ponto: o NÍVEL na régua da própria cidade (quando há
    // leitura fresca) e a idade. Nível em metros é da régua DELA — a comparação
    // entre cidades continua sendo só pela faixa (cor), nunca pelo metro.
    const sub =
      p.nivel != null
        ? idade
          ? `${metros(p.nivel)} · ${idade}`
          : metros(p.nivel)
        : usaBruto
          ? idadeBruto
            ? `≈${metros(p.nivelBruto!.nivelBrutoM)} bruto · ${idadeBruto}`
            : `≈${metros(p.nivelBruto!.nivelBrutoM)} bruto`
          : idade
    const w = ctx.measureText(nome).width
    const meia = w / 2
    const cx = Math.max(pad + meia, Math.min(cena.largura - pad - meia, p.x))
    const baseY = p.y - (raio + 2 * escala)
    const altTotal = sub ? alt + fonte * 0.95 : alt
    const caixa = { x0: cx - meia - 1, y0: baseY - altTotal, x1: cx + meia + 1, y1: baseY + 1 }
    const bate = caixas.some(
      (c) => caixa.x0 < c.x1 && caixa.x1 > c.x0 && caixa.y0 < c.y1 && caixa.y1 > c.y0,
    )
    if (bate && p.cidade.id !== selecionada) continue
    caixas.push(caixa)
    ctx.textAlign = 'center'
    ctx.lineWidth = 3.2 * escala
    ctx.strokeStyle = 'rgba(4,12,20,0.92)'
    ctx.font = `600 ${fonte}px system-ui, sans-serif`
    ctx.strokeText(nome, cx, baseY)
    ctx.fillStyle = '#eaf1f8'
    ctx.fillText(nome, cx, baseY)
    if (sub) {
      const fy = baseY - fonte - 1 * escala
      ctx.font = `600 ${Math.round(fonte * 0.85)}px system-ui, sans-serif`
      ctx.lineWidth = 3 * escala
      ctx.strokeStyle = 'rgba(4,12,20,0.92)'
      ctx.strokeText(sub, cx, fy)
      // Nível calibrado em destaque (claro); bruto DCSC em violeta (marca visual
      // de "outro tipo de dado", nunca as cores de faixa/severidade); sem
      // nenhum dos dois, só a idade, acinzentada.
      ctx.fillStyle = p.nivel != null ? '#dff0ff' : usaBruto ? '#c9a6f0' : '#9fb2c4'
      ctx.fillText(sub, cx, fy)
    }
  }
}
