import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  cidadesDoRio,
  eixoDoRio,
  estacoes,
  estacoesTempoReal,
  mareItajai,
  temReguaCadastrada,
  topologiaDoRio,
  trechos,
} from '../dados/carregar'
import { caixasDosControles } from '../logica/controlesSobreOMapa'
import { menuDasCidades } from '../logica/menuDasCidades'
import { vizinhosNoEixo } from '../logica/vizinhosNoEixo'
import { resumo24h } from '../logica/resumo24h'
import { CANAIS, juntarCanais } from '../logica/canaisDoTronco'
import { kmDaVista, vistaQueCabeAsReguas } from '../logica/vistaDaCidade'
import { reguasComRotulo } from '../logica/rotulosDasReguas'
import {
  COR_COTA_RUA,
  avisoDeRuas,
  contarRuas,
  pontosDeRua,
  zoomPermiteRuas,
  type PontoDeRua,
} from '../logica/cotasNoMapa'
import type { Cidade } from '../dados/tipos'
import { leiturasDaCidade, useTempoReal } from '../dados/tempoReal'
import { useNivelSc } from '../dados/nivelSc'
import { useBarragens } from '../dados/barragens'
import { barragensNoMapa } from '../logica/barragensNoMapa'
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
  cidadeNoTrecho,
  construirCena,
  desenharBase,
  desenharCorrenteza,
  desenharBarragens,
  desenharCotasDeRua,
  desenharOnda,
  caixaDaEtiquetaMare,
  desenharPinos,
  desenharReguas,
  medidorDe,
  planejarRotulosDosPinos,
  type Caixa,
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
  urlDosRotulos,
  zoomPara,
  type ChaveFundo,
} from '../logica/tiles'
import VariasReguas from '../componentes/VariasReguas'
import ArvoreDaBacia from '../componentes/ArvoreDaBacia'
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
  // A CABECEIRA do Sul. Não é afluente — é uma das duas cabeceiras paralelas
  // que se juntam em Rio do Sul e ali fazem nascer o Açu —, mas entra por esta
  // mesma porta porque a mecânica é a mesma: traçado opcional, que some sem
  // quebrar nada.
  //
  // POR QUE FALTAVA (05/09/2026): a consulta original do Overpass pediu Açu,
  // Mirim e Oeste, nunca o Sul. Na tela, Ituporanga e a Barragem Sul flutuavam
  // a 28 e 31 km de qualquer linha, e a linha perto delas era o OESTE — o mapa
  // sugerindo Taió -> Ituporanga -> Rio do Sul em SÉRIE, a fila que o projeto
  // desmontou nos dados. O desenho é o que o morador lê primeiro.
  //
  // ⚠️ PARCIAL: 10,5 km, da Defesa Civil de Rio do Sul (Asthon). Mostra as duas
  // cabeceiras CHEGANDO à confluência, que é a afirmação que corrige o erro;
  // não alcança Ituporanga, 21 km acima. Ituporanga segue fora da guarda de
  // 5 km, então continua sem pintar traçado — que é o certo enquanto o rio dela
  // não estiver desenhado até lá.
  'itajai-do-sul',
  'benedito',
  'luiz-alves',
  'hercilio',
  'ribeirao-murta',
  'ribeirao-canhanduba',
  // O trecho que FECHA o vão do Canhanduba até o Mirim. Sem ele desenhado, o
  // Canhanduba morre a 578 m do rio — e o mapa AFIRMA que a água pára ali.
  // Entra como curso próprio porque é assim que o OSM o nomeia: fundir os dois
  // faria a tela dizer que 650 m de Rio Conceição são Canhanduba.
  'rio-conceicao',
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

/**
 * O Monitor, opcionalmente ABERTO NUMA CIDADE (`/monitor/:cidadeId`).
 *
 * É o MESMO mapa, e de propósito: uma segunda implementação do mapa ao vivo
 * divergiria com o tempo, e o dia da divergência é o dia em que a mesma cidade
 * aparece verde numa tela e laranja na outra. Só muda o ENQUADRAMENTO inicial e
 * qual pino já vem aberto — nada do que o mapa afirma depende do zoom.
 *
 * Cidade sem coordenada no cadastro abre na bacia inteira, como sempre. Não se
 * inventa posição, e não se deixa a tela em branco.
 */
export default function MonitorBacia() {
  const navigate = useNavigate()
  const { cidadeId: cidadeFoco } = useParams()
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
  /**
   * Onde o mapa está olhando. Começa na bacia inteira — ou na cidade da rota.
   *
   * O enquadramento da cidade só pode ser calculado depois que a cena existe
   * (o zoom é relativo aos limites da bacia), então ele é aplicado uma vez, no
   * efeito abaixo, e não aqui.
   */
  const [vista, setVista] = useState<Vista>(VISTA_INTEIRA)
  // O laço de animação precisa do zoom de AGORA para decidir quais réguas
  // mostram o número (`logica/rotulosDasReguas`); `vista` é estado e não chega
  // lá dentro. Mesma convenção dos outros refs deste arquivo.
  const vistaRef = useRef(vista)
  vistaRef.current = vista
  /** Já enquadrou na cidade da rota? Uma vez por cidade: depois o zoom é de quem mexe. */
  const enquadrou = useRef(false)
  /** O menu de cidades, na ordem do rio (logica/menuDasCidades). */
  const [menuAberto, setMenuAberto] = useState(false)
  const menu = useMemo(
    () =>
      menuDasCidades(
        Object.entries(estacoes.rios).map(([id, r]) => ({
          id,
          nome: r.nome,
          cidades: r.cidades,
          _topologia: r._topologia,
        })),
      ),
    [],
  )
  /**
   * A legenda aberta ou só o título. Nasce FECHADA quando a tela abre numa
   * cidade ou é estreita: no celular, legenda aberta mais painel da cidade
   * cobriam o mapa inteiro (visto em 06/09/2026) — e o mapa é o motivo de
   * alguém estar aqui.
   */
  const [legendaAberta, setLegendaAberta] = useState<boolean>(
    () => !cidadeFoco && (typeof window === 'undefined' || window.innerWidth > 700),
  )
  /**
   * As cotas de rua da cidade em foco, como pontos no mapa.
   *
   * Carregadas SOB DEMANDA (`import()` dinâmico): a tabela tem 4.593 registros
   * e vive num pedaço à parte justamente para que quem abre o mapa só para ver
   * o nível do rio não a baixe. Só entram quando a cidade tem o par
   * cota↔leitura provado E o zoom está perto o bastante.
   */
  const [pontosRua, setPontosRua] = useState<PontoDeRua[]>([])
  const pontosRuaRef = useRef<PontoDeRua[]>([])
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
  const mapaBarragens = useBarragens()
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

  /**
   * As barragens como marcadores, comporta a comporta. O Monitor é a bacia
   * inteira, então mostra as três (as que a fonte trouxer). A regra da
   * animação — aberta anima, fechada não, leitura velha não anima nenhuma —
   * está em `logica/barragensNoMapa.ts`.
   */
  const barragensDoMapa = useMemo(
    () => barragensNoMapa(mapaBarragens.values(), agora, 'bacia'),
    [mapaBarragens, agora],
  )
  const barragensRef = useRef(barragensDoMapa)
  barragensRef.current = barragensDoMapa
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
      ...CANAIS.map(async (rioId) => ({ rioId, coords: await baixarTracado(rioId) })),
      ...AFLUENTES.map(async (rioId) => ({ rioId, coords: await baixarTracado(rioId) })),
    ]).then((baixados) => {
      if (!vivo) return
      // `juntarCanais` funde o canal retificado no traçado do Mirim e o tira da
      // lista: é o que faz a espinha do Mirim pintar os dois canais igual.
      const lista: RioParaCena[] = juntarCanais(baixados).map((b) => ({
        rioId: b.rioId,
        coords: b.coords,
        // Tronco tem cidades que o pintam; afluente entra só como linha (sem
        // cidade própria no cadastro → fica cinza, honesto).
        cidades: (RIOS_TRONCO as readonly string[]).includes(b.rioId)
          ? cidadesDoRio(b.rioId)
          : [],
        // O eixo diz quem pode PINTAR. Sem ele, Timbó (no Benedito, a 8,2 km)
        // e Rio dos Cedros (16,6 km) coloriam trechos do Açu com o nível de
        // outro rio.
        eixo: eixoDoRio(b.rioId),
      }))
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
    // `dpr`: em tela 2x o tile da largura CSS chegava com metade dos pixels
    // do vidro — fundo borrado justamente no celular. Ver `zoomPara`.
    const z = zoomPara(cena.enq, camada.maxZoom, Math.min(3, window.devicePixelRatio || 1))
    const pedacos = tilesVisiveis(cena.enq, tam.w, tam.h, z)
    const cache = tilesRef.current
    let vivo = true

    // Base e, por cima dela, os rótulos — nesta ordem, senão o nome do bairro
    // fica embaixo do desenho e some. Fundo sem `rotulos` passa direto.
    const urls = (t: (typeof pedacos)[number]): string[] => {
      const rotulos = urlDosRotulos(camada, t.x, t.y, t.z)
      return rotulos ? [urlDoTile(camada, t.x, t.y, t.z), rotulos] : [urlDoTile(camada, t.x, t.y, t.z)]
    }

    const pintarTiles = (c: CanvasRenderingContext2D) => {
      for (const camadaUrl of [0, 1]) {
        for (const t of pedacos) {
          const url = urls(t)[camadaUrl]
          if (!url) continue
          const im = cache.get(url)
          if (im && im !== 'erro' && im.complete && im.naturalWidth > 0) {
            // +1 px cobre a costura de arredondamento entre vizinhos.
            c.drawImage(im, t.px, t.py, t.largura + 1, t.altura + 1)
          }
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

    for (const url of pedacos.flatMap(urls)) {
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
      // Barragens antes das réguas e dos pinos: são estrutura no leito, ficam por baixo.
      // As ruas por BAIXO de tudo: são o fundo da cidade, e nenhum ponto de
      // rua pode cobrir o pino que traz o número do rio.
      desenharCotasDeRua(ctx, cena, pontosRuaRef.current, COR_COTA_RUA, escala)

      // ANTICOLISÃO ENTRE OS TRÊS DESENHISTAS. Cada um tinha a sua lista de
      // rótulos e nenhum enxergava os outros: "Taió" saía por cima de "Oeste
      // Taió · 7 de 7 abertas", e as onze réguas de Itajaí por cima do nome da
      // cidade. A lista agora é UMA, e os NOMES DAS CIDADES reservam primeiro —
      // são a âncora do mapa; barragem e régua cedem espaço a eles, nunca o
      // contrário.
      const opcoesPinos = {
        escala,
        mostrarIdade: true,
        agora: instante,
        temRegua: temReguaCadastrada,
      }
      const caixas: Caixa[] = []
      // O chip da maré é fixo no topo-direito e não cede: reserva antes de todos.
      const chipMare = caixaDaEtiquetaMare(medidorDe(ctx), cena, escala)
      if (chipMare) caixas.push(chipMare)
      // OS CONTROLES DE HTML TAMBÉM OCUPAM O MAPA. Eles são DOM por cima do
      // vidro, e até aqui o canvas não os enxergava: "Timbó" saía atrás do
      // botão +, "Blumenau" atrás do −, sobrando "…mbó" e "…nau" na tela
      // (capturas de 07/09/2026). Reservam ANTES dos nomes das cidades porque
      // não têm como ceder — são opacos e o toque é deles.
      const caixaMapa = canvas.getBoundingClientRect()
      for (const el of divRef.current?.querySelectorAll<HTMLElement>('[data-tapa-mapa]') ?? []) {
        caixas.push(...caixasDosControles([el.getBoundingClientRect()], caixaMapa, 4))
      }
      const rotulos = planejarRotulosDosPinos(
        medidorDe(ctx),
        cena,
        selRef.current,
        opcoesPinos,
        caixas,
      )
      desenharBarragens(ctx, cena, barragensRef.current, seg, escala, caixas)
      // As réguas ANTES dos pinos das cidades: o pino maior fica por cima.
      // Quais réguas mostram o NÚMERO neste zoom. Em Itajaí são onze, e de
      // longe elas escreviam umas por cima das outras e por cima do nome da
      // cidade. Ver `logica/rotulosDasReguas`.
      desenharReguas(
        ctx,
        cena,
        reguasRef.current,
        escala,
        reguaSelRef.current,
        caixas,
        reguasComRotulo(
          reguasRef.current,
          kmDaVista(cena.limitesBase, vistaRef.current.zoom),
          reguaSelRef.current,
        ),
      )
      desenharPinos(ctx, cena, selRef.current, { ...opcoesPinos, rotulos })
      if (!reduz) raf = requestAnimationFrame(quadro)
    }
    raf = requestAnimationFrame(quadro)
    return () => {
      vivo = false // tile que chegar depois não redesenha canvas morto
      cancelAnimationFrame(raf)
    }
  }, [rios, tempoReal, nivelSc, agora, tam, cidadesBacia, idxRepro, grade, serie, fundo, vista])

  useEffect(() => {
    pontosRuaRef.current = pontosRua
  }, [pontosRua])

  /**
   * Enquadra na cidade da rota, UMA VEZ, quando a cena existir.
   *
   * Depois disso o zoom é de quem mexe: reaplicar a cada quadro roubaria o
   * mapa da mão da pessoa no meio de uma cheia, que é quando ela mais precisa
   * arrastar para ver o vizinho de montante.
   *
   * Abre também o painel daquela cidade, para a tela já responder à pergunta
   * que levou alguém até este endereço — em que pé está a minha cidade.
   */
  // A troca de cidade pelo MENU acontece com o componente montado: o
  // `enquadrou` de uma cidade não pode valer para a seguinte. E voltar para
  // /monitor é voltar à bacia inteira — não ficar preso no zoom da última.
  useEffect(() => {
    enquadrou.current = false
    setMenuAberto(false)
    if (!cidadeFoco) {
      setVista(VISTA_INTEIRA)
      setSel(null)
    } else {
      setLegendaAberta(false)
    }
  }, [cidadeFoco])

  useEffect(() => {
    if (!cidadeFoco || enquadrou.current) return
    const cena = cenaRef.current
    if (!cena || cena.pinos.length === 0) return
    const pino = cena.pinos.find((p) => p.cidade.id === cidadeFoco)
    // Cidade que não está no mapa (id errado no endereço, ou sem coordenada):
    // fica a bacia inteira. Melhor do que zoom num lugar inventado.
    //
    // O enquadramento cabe o pino E AS RÉGUAS DA CIDADE. Itajaí tem onze,
    // espalhadas por 20,8 x 17,6 km: com a janela fixa de 24 km centrada no
    // pino, a DC-10 (Bairro Limoeiro) ficava a 24,2 km do centro, fora da tela.
    // Ver `vistaQueCabeAsReguas`.
    const daCidade = reguasRef.current.filter((r) => r.cidade === cidadeFoco)
    const v = vistaQueCabeAsReguas(
      pino?.cidade.coordenadas,
      daCidade,
      cena.limitesBase,
      cena.largura > 0 ? cena.altura / cena.largura : 1,
    )
    enquadrou.current = true
    if (!v) return
    setVista(v)
    if (pino) setSel(pino)
  }, [cidadeFoco, tam, rios, tempoReal])

  /**
   * Carrega e recalcula as cotas de rua da cidade em foco.
   *
   * As três condições são de segurança, não de desempenho (ver
   * `logica/cotasNoMapa.ts`): a cidade precisa do par cota↔leitura provado, o
   * zoom precisa deixar os pontos serem PONTOS — de longe eles viram nuvem, e
   * nuvem num mapa de enchente lê-se como mancha —, e sem leitura o estado de
   * cada rua fica indefinido em vez de "não alagou".
   */
  useEffect(() => {
    const cena = cenaRef.current
    const pino = cidadeFoco ? cena?.pinos.find((p) => p.cidade.id === cidadeFoco) : undefined
    const perto = cena ? zoomPermiteRuas(kmDaVista(cena.limitesBase, vista.zoom)) : false
    if (!pino || !perto) {
      setPontosRua([])
      return
    }
    let vivo = true
    void import('../dados/cotasRuas').then((m) => {
      if (!vivo) return
      setPontosRua(pontosDeRua(m.cotasRuas, pino.cidade, pino.nivel))
    })
    return () => {
      vivo = false
    }
  }, [cidadeFoco, vista, tam, tempoReal])

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

  /**
   * Cidade do TRECHO DE RIO sob o ponteiro — o toque no rio, não no pino.
   *
   * Devolve o PINO daquela cidade, para o painel ser exatamente o mesmo que o
   * toque no pino abre: quem encosta no rio perto de casa quer a cidade dali, e
   * não uma segunda tela com outro formato.
   */
  function pinoDoTrechoNoPonto(ev: React.PointerEvent<HTMLCanvasElement>): Pino | null {
    const cena = cenaRef.current
    const canvas = canvasRef.current
    if (!cena || !canvas) return null
    const r = canvas.getBoundingClientRect()
    const achado = cidadeNoTrecho(cena.trechos, ev.clientX - r.left, ev.clientY - r.top)
    if (!achado) return null
    return cena.pinos.find((p) => p.cidade.id === achado.cidadeId) ?? null
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
    // Régua, pino, e só então o rio. A ordem é do alvo mais preciso para o mais
    // largo: quem mira o pino de Gaspar não pode receber o trecho que passa por
    // baixo dele.
    setSel(pinoNoPonto(ev) ?? pinoDoTrechoNoPonto(ev))
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
      <div ref={divRef} className={`${estilos.palco} ${!reguaSel && (sel ?? hover) ? estilos.temPainel : ''}`}>
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

        {/* RODAPÉ — uma coluna só, e é isso que impede a sobreposição.

            O DEFEITO QUE ISTO CORRIGE (07/09/2026, relatado pelo Jefferson:
            "não é possível mudar o fundo do mapa"). A barra de reprodução era
            centrada embaixo e a legenda ficava no canto inferior esquerdo: no
            celular as duas ocupam a MESMA faixa, e a barra tinha `z-index: 5`.
            O z-index não separa nada — só decide quem recebe o toque. Quem
            recebia era a barra, então Escuro/Satélite/Mapa ficavam visíveis e
            INERTES, e o mapa ainda cobria a atribuição do OpenStreetMap, que é
            condição de licença.

            Empilhar numa coluna resolve por geometria: em largura nenhuma os
            dois podem se cobrir, porque um está ABAIXO do outro no fluxo. */}
        <div className={estilos.rodape}>
          {/* Reprodução das últimas 24 h: a onda de cor descendo, do MEDIDO. Só
              aparece quando há série publicada. */}
          {grade.length > 0 ? (
            <div className={estilos.controles} data-tapa-mapa>
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
        {/* Legenda sempre visível, canto inferior esquerdo. O painel da cidade
            vai para o canto direito, então os dois não se cobrem. */}
        <div
          className={`${estilos.legenda} ${legendaAberta ? '' : estilos.legendaFechada}`}
          data-tapa-mapa
        >
          <strong className={estilos.legendaTitulo}>
            <span>{legendaAberta ? 'Faixa (na régua de cada cidade)' : 'Legenda'}</span>
            <button
              type="button"
              className={estilos.botaoLegenda}
              aria-expanded={legendaAberta}
              onClick={() => setLegendaAberta((v) => !v)}
            >
              {legendaAberta ? 'recolher' : 'abrir'}
            </button>
          </strong>
          {legendaAberta ? (
            <>
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
          {/* Sem esta linha, quem vê onze pontos e dois números em Itajaí não
              tem como saber por quê — e some do mapa é o que mais parece
              "não existe". */}
          <p className={estilos.legendaNota}>
            Com o mapa afastado, <strong>só as réguas que podem virar aviso mostram o
            número</strong> — as demais aparecem como ponto. Itajaí tem onze, e nove são de
            estuário. <strong>Aproxime para ver todas</strong>, ou toque numa para ler a dela.
          </p>
            </>
          ) : null}

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
        </div>

        {/* Título e aviso no topo-esquerdo (o chip da maré fica no topo-direito,
            desenhado no canvas). O botão de tela cheia vai no canto inferior
            direito para não colidir com o chip. */}
        <div className={estilos.cantoEsquerdo}>
        <div className={estilos.topo} data-tapa-mapa>
          <strong>Monitoramento da bacia</strong>
          <button
            type="button"
            className={estilos.botaoMenu}
            aria-expanded={menuAberto}
            aria-controls="menu-cidades"
            onClick={() => setMenuAberto((v) => !v)}
          >
            {menuAberto ? 'Fechar' : 'Cidades ▾'}
          </button>
          <span className={estilos.aviso}>
            Não é alerta oficial. Emergência: <strong>199</strong>. Siga a Defesa Civil.
          </span>
          <button type="button" className={estilos.botaoCheia} onClick={telaCheia}>
            Tela cheia
          </button>
        </div>

        {/* MENU DE CIDADES, na ordem do rio — em GRUPOS, porque o Açu é árvore:
            Taió e Ituporanga correm em paralelo, e uma lista "Taió → Ituporanga
            → Rio do Sul" afirmaria uma sequência que não existe. Toque numa
            cidade abre o monitor DELA (o mesmo mapa, enquadrado nela). */}
        {menuAberto ? (
          <nav
            id="menu-cidades"
            className={estilos.menuCidades}
            data-tapa-mapa
            aria-label="Cidades, na ordem do rio"
            onKeyDown={(e) => {
              if (e.key === 'Escape') setMenuAberto(false)
            }}
          >
            <div className={estilos.menuTopo}>
              <strong>Cidades, na ordem do rio</strong>
              <button type="button" className={estilos.botaoLegenda} onClick={() => setMenuAberto(false)}>
                fechar
              </button>
            </div>
            {menu.map((rio) => (
              <div key={rio.id} className={estilos.menuRio}>
                <strong>{rio.nome}</strong>
                {rio.grupos.map((g) => (
                  <div key={g.titulo}>
                    <div className={estilos.menuGrupo}>
                      {g.titulo}
                      {g.ordenado ? '' : ' (sem ordem entre si)'}
                    </div>
                    <ul className={`${estilos.menuLista} ${g.ordenado ? estilos.menuOrdenado : ''}`}>
                      {g.itens.map((item) => (
                        <li key={item.id}>
                          <button
                            type="button"
                            className={`${estilos.menuCidade} ${item.id === cidadeFoco ? estilos.menuAtual : ''}`}
                            aria-current={item.id === cidadeFoco ? 'page' : undefined}
                            onClick={() => navigate(`/monitor/${item.id}`)}
                          >
                            {item.nome}
                            {item.detalhe ? <span className={estilos.menuDetalhe}>{item.detalhe}</span> : null}
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            ))}
            <p className={estilos.menuNota}>
              A seta ↓ é a ordem em que a água desce. Cabeceiras e afluentes não têm
              ordem entre si: a cheia deles não é a mesma que desce o tronco.
            </p>
          </nav>
        ) : null}

        {/* ZOOM. Os botões existem além da pinça porque nem todo mundo usa dois
            dedos, e porque no computador não há pinça nenhuma. "Ver tudo" volta
            à bacia inteira: sem ele, quem se perde no zoom fica sem saber que
            existe mapa fora da tela. */}
        <div className={estilos.zoom} role="group" aria-label="Zoom do mapa" data-tapa-mapa>
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
        </div>


        {/* Painel de UMA RÉGUA, quando o toque foi nela. Vem antes do painel de
            cidade e o substitui: dois no mesmo canto se cobrem. */}
        {reguaSel ? (() => {
          const g = reguasDoMapa.find((r) => (r.codigo || r.titulo) === reguaSel)
          if (!g) return null
          const cotas = cotasOrdenadas(g.cotas)
          return (
            <div className={estilos.painel} data-tapa-mapa>
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
          // De onde a água vem e para onde vai — só DENTRO do eixo (tronco no
          // Açu, fila no Mirim). O mesmo cálculo da tela da cidade.
          const cidadesDoFoco = cidadesDoRio(foco.rioId)
          const eixo = topologiaDoRio(foco.rioId)?.tronco_sequencia ?? cidadesDoFoco.map((c) => c.id)
          const viz = vizinhosNoEixo(foco.rioId, cid.id, eixo, cidadesDoFoco, trechos)
          const pinoDe = (id: string) => cenaRef.current?.pinos.find((p) => p.cidade.id === id) ?? null
          const ultimas = resumo24h(serieDaCidade(serie, foco.rioId, cid.id))
          return (
            <div className={estilos.painel} data-tapa-mapa>
              <div className={estilos.painelTopo}>
                <strong>{cid.nome}</strong>
                {/* FECHAR: no celular o painel é uma folha que cobre metade do
                    mapa, e não havia como dispensá-la — quem abria uma cidade
                    ficava sem o mapa até recarregar a página. */}
                <button
                  type="button"
                  className={estilos.botaoFechar}
                  aria-label={`Fechar o painel de ${cid.nome}`}
                  onClick={() => { setSel(null); setHover(null) }}
                >
                  ✕
                </button>
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
              {/* VIZINHOS NO EIXO. "A água que está em Rio do Sul chega aqui
                  quando?" — o painel não respondia. O tempo é sempre um
                  INTERVALO (transito.json), nunca horário; e o nível do vizinho
                  é na régua DELE, que não se compara com a daqui. */}
              {viz.noEixo ? (
                <div className={estilos.painelBloco}>
                  <span className={estilos.painelRotulo}>De onde a água vem, para onde vai</span>
                  <ul className={estilos.painelVizinhos}>
                    {[
                      { v: viz.montante, rotulo: 'Acima', sufixo: 'para chegar aqui' },
                      { v: viz.jusante, rotulo: 'Abaixo', sufixo: 'daqui até lá' },
                    ].map(({ v, rotulo, sufixo }) => {
                      if (!v) {
                        return (
                          <li key={rotulo}>
                            <strong>{rotulo}</strong>
                            {rotulo === 'Acima' ? 'início do tronco nesta tela' : 'fim do curso nesta tela'}
                          </li>
                        )
                      }
                      const pv = pinoDe(v.id)
                      return (
                        <li key={rotulo}>
                          <strong>{rotulo}</strong>
                          <button type="button" onClick={() => navigate(`/monitor/${v.id}`)}>
                            {v.nome}
                          </button>
                          {pv?.nivel != null ? (
                            <>
                              {' '}— {metros(pv.nivel)} na régua de lá ({ROTULO_FAIXA[pv.faixa]})
                            </>
                          ) : null}
                          {v.janela ? (
                            <>
                              {' '}· leva <strong>{v.janela}</strong> {sufixo}
                            </>
                          ) : (
                            <> · tempo de descida ainda não levantado</>
                          )}
                        </li>
                      )
                    })}
                  </ul>
                </div>
              ) : (
                <p className={estilos.painelExtra}>
                  Fora do tronco: a cheia daqui <strong>não é a mesma</strong> que desce o rio
                  principal, então não se encadeia tempo de descida por esta cidade.
                </p>
              )}
              {/* ÚLTIMAS 24 H: três números lidos da série, sem modelo. Recusa
                  quando a série mistura réguas (Itajaí tem onze). */}
              {ultimas.resumo ? (
                <div className={estilos.painelBloco}>
                  <span className={estilos.painelRotulo}>Últimas 24 h nesta régua</span>
                  <p className={estilos.painelExtra}>
                    mín <strong>{metros(ultimas.resumo.min)}</strong> · máx{' '}
                    <strong>{metros(ultimas.resumo.max)}</strong> ·{' '}
                    {ultimas.resumo.variacao > 0 ? 'subiu' : ultimas.resumo.variacao < 0 ? 'desceu' : 'estável'}
                    {ultimas.resumo.variacao !== 0 ? <> {metros(Math.abs(ultimas.resumo.variacao))}</> : null}{' '}
                    ({ultimas.resumo.pontos} leituras)
                  </p>
                </div>
              ) : ultimas.motivo === 'varias-reguas' ? (
                <p className={estilos.painelRessalva}>
                  Sem resumo das últimas horas: esta cidade tem várias réguas com zeros
                  diferentes, e um mínimo e um máximo misturariam duas réguas.
                </p>
              ) : null}
              <p className={estilos.painelAcao}>{ACAO_FAIXA[foco.faixa]}</p>
              {/* As cotas de rua, quando esta cidade as tem e o zoom permite.
                  A conta é aritmética pura — cota levantada menos nível medido
                  —, e por isso pode ser dita com todas as letras. */}
              {pontosRua.length > 0 ? (
                  (() => {
                    const c = contarRuas(pontosRua)
                    const naoProvada = pontosRua[0]?.motivo === 'regua-nao-provada'
                    return (
                      <p className={estilos.painelExtra}>
                        {naoProvada ? (
                          <>
                            {pontosRua.length} ruas levantadas, cada ponto com a cota em que
                            começa a alagar. <strong>O mapa não diz quais já alagaram</strong>:
                            estas cotas são de uma régua e a leitura ao vivo vem de outra
                            fonte, que ainda não foi identificada — comparar as duas seria
                            usar o metro de outro lugar.
                          </>
                        ) : c.semLeitura > 0 ? (
                          <>
                            {c.semLeitura} ruas levantadas; sem leitura do rio agora, não dá
                            para dizer quais alagaram.
                          </>
                        ) : (
                          <>
                            {c.atingidas} de {c.atingidas + c.aguardando} ruas levantadas já
                            estão abaixo do nível de agora. Cada ponto é uma rua; cheio, o rio
                            já passou da cota dela.
                          </>
                        )}{' '}
                        O vazio entre os pontos não é área seca — é onde não há levantamento.
                      </p>
                    )
                  })()
              ) : (
                (() => {
                  // A frase é decidida em `logica/cotasNoMapa`, não aqui: dizer
                  // "aproxime" a quem tem levantamento sem coordenada faz a
                  // pessoa aproximar, não achar nada e concluir que a rua dela
                  // não foi levantada. Blumenau tem 2.042 ruas nesse caso.
                  const aviso = avisoDeRuas(cid.id)
                  return aviso.tipo === 'sem-coordenada' ? (
                    <p className={estilos.painelExtra}>
                      Esta cidade tem <strong>{aviso.ruas} ruas levantadas</strong>, mas a
                      fonte publica rua e bairro <strong>sem a coordenada</strong> de cada
                      ponto — por isso elas não entram no mapa. Aproximar não vai fazê-las
                      aparecer. Elas estão na tela da cidade, buscáveis por nome.
                    </p>
                  ) : (
                    <p className={estilos.painelExtra}>
                      Aproxime o mapa para ver as cotas de rua, onde houver levantamento. De
                      longe os pontos virariam uma nuvem, e nuvem parece mancha de inundação,
                      que é coisa diferente.
                    </p>
                  )
                })()
              )}
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

      {/* A árvore da bacia, embaixo do mapa: quem vê os pinos precisa saber
          QUEM ESTÁ ACIMA DE QUEM, e que a barragem não é o rio da cidade. */}
      <ArvoreDaBacia />

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
