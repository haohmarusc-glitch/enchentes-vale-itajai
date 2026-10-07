import { cotasOperacionais as cotasOrdenadas } from '../logica/cotasOperacionais'
import { comReferenciaAscurra } from '../dados/referenciaAscurra'
import { chuvaMonitor, linhasChuva, linhasChuvaCompactas, mmChuva } from '../logica/chuvaMonitor'
import { cotaDaFaixa, estadoDaLeitura, LEITURA_VARIAS_REGUAS, textoTendenciaCompacta } from '../logica/painelCompacto'
import { contagemDeTracados, opcoesDeTracado, tracadosVisiveis } from '../logica/tracadosDoMapa'
import { destaqueDaBacia } from '../logica/destaqueDaBacia'
import { estadoMareAgora } from '../logica/mare'
import { diaDeBrasilia, horaDeBrasilia, tendenciaDaLeitura } from '../logica/agora'
import ChuvaMonitor from '../componentes/ChuvaMonitor'
import { faixaAscurra } from '../logica/municipal'
import CamadasMonitor, { type CamadaDesenhada } from '../componentes/CamadasMonitor'
import { motivoSemCorNoMonitor } from '../logica/motivoSemCor'
import { MOTIVO_VARIAS_REGUAS, estacaoEhReguaDasCotas, ressalvaDoBruto, textoDaOrigemDaCor, textoEquivalencia, textoSemCota } from '../logica/textosDoPainel'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import ChatNoTopo from '../componentes/ChatNoTopo'
import { registrarMonitor, type FiltroMonitor, type MarcaNoMapa, type Retrato } from '../comandos/ponte'
import { faixaAcimaDoNormal, pinoSemLeituraDeAgora, reguaSemLeituraDeAgora } from '../logica/filtroSemLeitura'
import { useConversa } from '../chat-local/conversa'
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
import { kmDaVista, vistaAcimaDaFolha, vistaDaCidade, vistaQueCabeAsReguas, zoomMaximo } from '../logica/vistaDaCidade'
import { reguasComRotulo } from '../logica/rotulosDasReguas'
import {
  COR_COTA_RUA,
  avisoDeRuas,
  contarRuas,
  pontosDeRua,
  zoomPermiteRuas,
  type PontoDeRua,
} from '../logica/cotasNoMapa'
import { leiturasDaCidade, useTempoReal } from '../dados/tempoReal'
import { useNivelSc } from '../dados/nivelSc'
import { useClassificacao } from '../dados/classificacao'
import { useBarragens } from '../dados/barragens'
import { barragensNoMapa } from '../logica/barragensNoMapa'
import { leituraEm, serieDaCidade, useSerieRecente } from '../dados/serie'
import { deBrasilia, idadeMin, textoIdade, type Faixa, frescor, frescorDaCidade } from '../logica/tempoReal'
import { ROTULO_FAIXA, ACAO_FAIXA } from '../componentes/LegendaFaixas'
import { dataHora, metros, numero, rotuloCota } from '../logica/formato'
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
  desenharPinos,
  desenharReguas,
  MARGEM,
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
import { textoDaPosicao } from '../logica/posicaoDoPino'
import { chaveDaRegua, opcoesDoSeletor, TODAS, vistaDaRegua } from '../logica/seletorDeRegua'
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
import ReguasDoMonitor from '../componentes/ReguasDoMonitor'
import estilos from './MonitorBacia.module.css'

const NOME_DO_FUNDO: Record<ChaveFundo, string> = { escuro: 'escuro', satelite: 'satélite', mapa: 'mapa de ruas' }

/** Nomes das faixas que a Defesa Civil de SC publica (C7) — rotuladas como dela, nunca como nossas. */
const NOME_FAIXA_ESTADUAL = { normal: 'NORMAL', atencao: 'ATENÇÃO', alerta: 'ALERTA', emergencia: 'EMERGÊNCIA' } as const

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

/**
 * Todo traçado de `data/rios/` que não é tronco, canal nem afluente da lista
 * acima também entra, como linha extra (05/10/2026, autorizado pelo Jefferson
 * com o rótulo `monitor-autorizado`). Foi o que trouxe os rios que passam por
 * Ibirama sem uma lista nova aqui: um rio que ganha traçado aparece no Monitor
 * sem mexer neste arquivo. Sem cidade no cadastro, a linha fica cinza — só
 * mostra por onde a água corre, não pinta faixa.
 */
const OUTROS_TRACADOS: string[] = Object.keys(TRACADOS)
  .map((k) => k.replace(/^.*\//, '').replace(/\.geojson$/, ''))
  .filter((id) => !new Set<string>([...RIOS_TRONCO, ...CANAIS, ...AFLUENTES]).has(id))
  .sort()

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

/**
 * Tela cheia de monitoramento da bacia do Itajaí: Açu + Mirim (+ afluentes) num
 * `<canvas>` só, em alta definição. Cada trecho na cor da faixa da cidade a
 * montante (nunca metro entre cidades), correnteza que corre mais rápido onde o
 * nível está mais alto, o mar na foz colorido pela maré (escala própria), a
 * chuva recente por cidade e a idade de cada leitura. Não é sistema de alerta.
 */
// Até onde o zoom vai: `zoomMaximo` em `logica/vistaDaCidade.ts`. Na bacia inteira, o de sempre (escala de
// bairro); numa cidade, ~300 m de tela, o zoom de rua do satélite (pedido do Jefferson, 06/10/2026).

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
export default function MonitorBacia({ municipal = false }: { municipal?: boolean }) {
  const camadaHistorica = useRef<CamadaDesenhada>(null)
  const [rotuloCamada, setRotuloCamada] = useState<string | null>(null)
  const receberCamada = useCallback((camada: CamadaDesenhada) => {
    camadaHistorica.current = camada
    setRotuloCamada(camada?.rotulo ?? null)
  }, [])
  const navigate = useNavigate()
  const { cidadeId } = useParams()
  const [busca] = useSearchParams()
  // Conversa do chat aberta: no celular, o bloco do topo sobe acima da folha da cidade (ver o CSS).
  const { aberto: chatAberto } = useConversa()
  /**
   * Camadas de cheia comandadas pelo chat (docs/CHAT-GLOBAL-COMANDOS.md): o controle continua o de
   * `CamadasMonitor`; o chat só PEDE um modo, e lê as opções e o modo de agora para responder certo.
   */
  const [camadasDisponiveis, setCamadasDisponiveis] = useState<{ arquivo: string; rotulo: string }[]>([])
  const [modoCamada, setModoCamada] = useState<string | null>(null)
  const [pedidoCamada, setPedidoCamada] = useState<{ cidade: string; modo: string; n: number } | null>(null)
  /**
   * 2ª entrega do chat (docs/CHAT-GLOBAL-COMANDOS.md): o filtro "só sem leitura de agora" e a marca de um
   * ponto de confluência. Os dois aparecem ESCRITOS na tela, cada um com o botão de tirar; nenhum muda cor,
   * faixa ou número. Desligados (o padrão), o Monitor é o de sempre.
   */
  const [filtro, setFiltro] = useState<FiltroMonitor>(null)
  const [marca, setMarca] = useState<MarcaNoMapa | null>(null)
  const marcaRef = useRef<MarcaNoMapa | null>(null)
  marcaRef.current = marca
  /** Os pinos da cena SEM o filtro: o chat conta e encontra cidades por aqui, com ou sem filtro ligado. */
  const pinosTodosRef = useRef<Pino[]>([])
  const cidadeFoco = municipal ? 'ascurra' : cidadeId
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
  /**
   * Tocar de novo na cidade que já está aberta (menu "Cidades") volta a enquadrá-la. Antes o endereço
   * não mudava, nada acontecia, e quem tinha arrastado o mapa para longe não achava o caminho de volta
   * (auditoria de 06/10/2026).
   */
  const [pedidoDeEnquadrar, setPedidoDeEnquadrar] = useState(0)
  /** O menu de cidades, na ordem do rio (logica/menuDasCidades). */
  const [menuAberto, setMenuAberto] = useState(false)
  /**
   * ETAPA 3 do redesenho (docs/REDESENHO-MONITOR-MOBILE-2026-10-07.md): a barra de baixo do celular,
   * Mapa · Réguas · Perguntar. "Réguas" cobre o mapa com a lista compacta dos dois rios; "Perguntar" leva à
   * caixa do chat do topo (a mesma, com os mesmos comandos). Trocar de cidade volta ao mapa.
   */
  const [abaCelular, setAbaCelular] = useState<'mapa' | 'reguas'>('mapa')
  useEffect(() => { setAbaCelular('mapa') }, [cidadeId])
  /** A caixa do chat do topo com o foco: "Perguntar" acende, e "Mapa" apaga. */
  const [focoNoChat, setFocoNoChat] = useState(false)
  /**
   * REDESENHO DO MONITOR, etapa 1 (docs/REDESENHO-MONITOR-MOBILE-2026-10-07.md): o menu "Camadas do mapa"
   * reúne as camadas de cheia, a maré, a chuva, a legenda, os traçados e o fundo. Maré e chuva são só
   * VISIBILIDADE — desligar não apaga dado nenhum, e o painel da cidade continua mostrando a chuva dela.
   * Esconder um traçado é não desenhá-lo; o tronco fica sempre (`tracadosDoMapa`).
   */
  const [camadasAbertas, setCamadasAbertas] = useState(false)
  const [mostrarMare, setMostrarMare] = useState(true)
  const [mostrarChuva, setMostrarChuva] = useState(true)
  const [tracadosOcultos, setTracadosOcultos] = useState<ReadonlySet<string>>(() => new Set())
  const [mareAberta, setMareAberta] = useState(false)
  /** A cidade com a faixa mais grave AGORA (`destaqueDaBacia`); null sem faixa válida acima da atenção ou na reprodução. */
  const [destaque, setDestaque] = useState<Pino | null>(null)
  /**
   * ETAPA 2 do redesenho (docs/REDESENHO-MONITOR-MOBILE-2026-10-07.md): no celular o painel da cidade abre
   * COMPACTO (nível, horário, tendência) e "Mais detalhes" o expande. Volta a compacto a cada cidade nova.
   * No computador o painel é o de sempre, inteiro.
   */
  const [painelExpandido, setPainelExpandido] = useState(false)
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
  const [animacoesPausadas, setAnimacoesPausadas] = useState(false)
  const [paginaOculta, setPaginaOculta] = useState(document.hidden)
  const [movimentoReduzido, setMovimentoReduzido] = useState(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  )
  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)')
    const atualizarMovimento = () => setMovimentoReduzido(media.matches)
    const atualizarVisibilidade = () => setPaginaOculta(document.hidden)
    media.addEventListener('change', atualizarMovimento)
    document.addEventListener('visibilitychange', atualizarVisibilidade)
    return () => {
      media.removeEventListener('change', atualizarMovimento)
      document.removeEventListener('visibilitychange', atualizarVisibilidade)
    }
  }, [])
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
    if (municipal) return 'satelite'
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
  const chuvaRef = useRef<Map<string, string[]>>(new Map())
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

  const original = useTempoReal()
  const nivelSc = useNivelSc()
  // A classificação estadual × municipal do motor (PR 3, 07/10/2026): o mapa segue a mesma decisão dos
  // cartões, com os mesmos portões (`faixasDoMotor`); sem ela, a regra de sempre.
  const classificacao = useClassificacao()
  const tempoReal = useMemo(() => comReferenciaAscurra(original, nivelSc), [original, nivelSc])
  const mapaBarragens = useBarragens()
  const serie = useSerieRecente()
  const [agora, setAgora] = useState(() => new Date())
  useEffect(() => { const id = setInterval(() => setAgora(new Date()), 60_000); return () => clearInterval(id) }, [])
  const leituraMunicipal = nivelSc.get('ascurra')
  const faixaMunicipal = faixaAscurra(leituraMunicipal, agora)

  // O anel destaca a cidade em FOCO: a selecionada (clique) ou a sob o mouse.
  useEffect(() => {
    selRef.current = (sel ?? hover)?.cidade.id ?? null
    reguaSelRef.current = reguaSel
  }, [sel, hover, reguaSel])

  // Todas as cidades da bacia, para casar a chuva com a coordenada.
  const cidadesBacia = useMemo(
    () => [...new Map(RIOS_TRONCO.flatMap((r) => cidadesDoRio(r)).filter((c) => !municipal || c.id === 'ascurra').map(c => [c.id, c])).values()],
    [municipal],
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
  reguasRef.current = municipal ? [] : filtro === 'sem_leitura' ? reguasDoMapa.filter((r) => reguaSemLeituraDeAgora(r, agora)) : filtro === 'acima_do_normal' ? reguasDoMapa.filter((r) => faixaAcimaDoNormal(r.faixa)) : reguasDoMapa

  /**
   * O seletor de régua da cidade em foco (Itajaí, as onze; pedido do Jefferson, 06/10/2026). Na própria
   * tela: "Todas as N réguas" é o padrão e reenquadra a cidade; uma régua centraliza o mapa nela e abre o
   * painel dela. Tocar numa régua no mapa também muda o seletor, porque o valor vem de `reguaSel`.
   */
  const opcoesRegua = useMemo(
    () => (cidadeFoco && !municipal ? opcoesDoSeletor(reguasDoMapa, cidadeFoco) : []),
    [cidadeFoco, municipal, reguasDoMapa],
  )
  const valorSeletor = reguaSel && opcoesRegua.some((o) => o.valor === reguaSel) ? reguaSel : TODAS
  function escolherRegua(valor: string) {
    if (valor === TODAS) {
      setReguaSel(null)
      setPedidoDeEnquadrar((n) => n + 1)
      return
    }
    const r = reguasDoMapa.find((x) => chaveDaRegua(x) === valor)
    const cena = cenaRef.current
    setReguaSel(valor)
    setSel(null)
    if (!r || !cena) return
    const v = vistaDaRegua(r, cena.limitesBase, cena.largura, cena.altura, MARGEM)
    if (v) setVista(v)
  }

  /**
   * Os textos do painel que dizem a faixa, por que está cinza, de onde vem o pino e a equivalência. Uma
   * função só, usada pelo painel e pelo chat ("por que essa régua está cinza?"): o chat nunca dá um
   * segundo diagnóstico, diferente do que a tela mostra.
   */
  function textosDoFoco(foco: Pino) {
    const cid = foco.cidade
    const brutoSc = cid.id === 'ascurra' ? null : nivelSc.get(cid.id) ?? null
    const daCidade = leiturasDaCidade(tempoReal, foco.rioId, cid.id)
    const variasReguas = foco.nivel == null && (daCidade.length > 1 || reguasRef.current.filter((r) => r.cidade === cid.id).length > 1)
    const situacaoSc = brutoSc ? null : nivelSc.situacoes?.get(cid.id) ?? null
    const faixa = foco.origemFaixa === 'estadual'
      ? `Classificação estadual: ${brutoSc?.faixaEstadual ? NOME_FAIXA_ESTADUAL[brutoSc.faixaEstadual] : ROTULO_FAIXA[foco.faixa]}`
      : foco.faixa === 'sem-dado' && brutoSc && foco.nivel == null ? 'Sem classificação para esta régua' : ROTULO_FAIXA[foco.faixa]
    const motivoCinza = foco.faixa !== 'sem-dado'
      ? null
      : variasReguas
        ? MOTIVO_VARIAS_REGUAS
        : motivoSemCorNoMonitor(cid.cotas_m, foco.medidoEm, agora, foco.nivel != null, !!brutoSc, cid.id, situacaoSc,
            serieDaCidade(serie, foco.rioId, cid.id).at(-1) ?? null)
    return {
      faixa,
      motivoCinza,
      origemDaCor: variasReguas ? null : textoDaOrigemDaCor({ ...foco, codigoEstadual: brutoSc?.codigo ?? null }),
      posicao: textoDaPosicao(cid, foco, reguasRef.current.filter((r) => r.cidade === cid.id).length),
      equivalencia: cid.equivalencia_estadual ? textoEquivalencia(cid.equivalencia_estadual) : null,
    }
  }

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
  barragensRef.current = municipal ? [] : barragensDoMapa
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
      ...OUTROS_TRACADOS.map(async (rioId) => ({ rioId, coords: await baixarTracado(rioId) })),
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

    // Celular (≤ 700 px): rótulos compactos — só o nome; chuva em bolha; nível e hora no painel.
    const compacto = tam.w <= 700
    const cena = construirCena(
      canvas, tracadosVisiveis(rios, tracadosOcultos), tempoReal, instante, tam.w, tam.h, mareItajai, override, nivelSc, vista,
      municipal || emRepro ? undefined : reguasDoMapa.find(r => r.codigo === 'DC-11'),
      emRepro ? null : classificacao,
    )
    // Maré desligada no menu de camadas: o mar fica neutro e o chip some. O dado continua na tábua.
    if (!mostrarMare) cena.mar = null
    if (municipal) {
      cena.pinos = cena.pinos.filter((p) => p.cidade.id === 'ascurra')
      cena.mar = null
      // Conserva a divisão geográfica regional; nunca estende a régua local
      // por todo o rio ao remover as outras cidades.
      cena.trechos = cena.trechos.map((t) => t.cidadeId === 'ascurra' ? t : ({ ...t, faixa: 'sem-dado', cidadeId: null, animacao: 'parada' }))
    }
    pinosTodosRef.current = cena.pinos
    // O destaque é do AGORA: na reprodução, um "em atenção" do passado soaria como de agora.
    setDestaque(emRepro || municipal ? null : destaqueDaBacia(cena.pinos))
    if (filtro === 'sem_leitura') {
      // O filtro só ESCONDE os pinos com leitura de agora. Os trechos do rio continuam pintados como sempre.
      const reguaFresca = new Set(reguasDoMapa.filter((r) => !reguaSemLeituraDeAgora(r, instante)).map((r) => r.cidade))
      cena.pinos = cena.pinos.filter((p) => pinoSemLeituraDeAgora(p, instante, reguaFresca.has(p.cidade.id)))
    } else if (filtro === 'acima_do_normal') {
      // 6ª entrega: só os pinos com a faixa do mapa acima do normal (e Itajaí, se uma régua dela está).
      const reguaAcima = new Set(reguasDoMapa.filter((r) => faixaAcimaDoNormal(r.faixa)).map((r) => r.cidade))
      cena.pinos = cena.pinos.filter((p) => faixaAcimaDoNormal(p.faixa) || reguaAcima.has(p.cidade.id))
    }
    cenaRef.current = cena
    // O painel guarda a seleção, mas os números devem acompanhar a nova coleta.
    setSel(atual => atual ? cena.pinos.find(p => p.cidade.id === atual.cidade.id && p.rioId === atual.rioId) ?? null : null)
    setHover(atual => atual ? cena.pinos.find(p => p.cidade.id === atual.cidade.id && p.rioId === atual.rioId) ?? null : null)
    // A chuva é do agora; na reprodução do passado, some (não fingimos chuva
    // num instante que não medimos). No pino, só o acumulado de 24 h em
    // qualquer zoom; 1 h / 12 h e a idade ficam no painel. Ver `linhasChuva`.
    chuvaRef.current = emRepro || !mostrarChuva
      ? new Map()
      : new Map(cidadesBacia.map(c => [c.id, compacto ? linhasChuvaCompactas(tempoReal.chuva, c.id, agora) : linhasChuva(tempoReal.chuva, c.id, agora)]))

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
        // O chip da maré é HTML desde 07/10/2026 (rodapé, com a próxima maré ao toque).
        etiquetaMare: false,
      })
    }
    redesenharFundo()

    for (const url of pedacos.flatMap(urls)) {
      const existente = cache.get(url)
      if (existente === 'erro') continue
      // O zoom inicial pode mudar enquanto o tile ainda carrega. O callback
      // deve redesenhar a cena atual, não a cena anterior já desmontada.
      if (existente) {
        existente.onload = () => { if (vivo) redesenharFundo() }
        continue
      }
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

    const reduz = animacoesPausadas || movimentoReduzido || paginaOculta

    let camadaPreparada: CamadaDesenhada = null
    let caminhosCamada: Path2D[] = []
    let linhasCamada: Path2D[] = []
    let raf = 0
    const quadro = (t: number) => {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, cena.largura, cena.altura)
      ctx.drawImage(fundoCanvas, 0, 0, cena.largura, cena.altura)
      if (camadaPreparada !== camadaHistorica.current) {
        camadaPreparada = camadaHistorica.current
        caminhosCamada = []
        linhasCamada = []
        for (const f of camadaPreparada?.geo.features ?? []) {
          const g = f.geometry
          const linhas = g.type === 'LineString' ? [g.coordinates] : g.type === 'MultiLineString' ? g.coordinates : []
          for (const linha of linhas) {
            const path = new Path2D()
            linha.forEach((p, i) => {
              const [x, y] = projetar(cena.enq, [p[0]!, p[1]!])
              if (i === 0) path.moveTo(x, y)
              else path.lineTo(x, y)
            })
            linhasCamada.push(path)
          }
          const poligonos = g.type === 'Polygon' ? [g.coordinates] : g.type === 'MultiPolygon' ? g.coordinates : []
          for (const poligono of poligonos) {
            const path = new Path2D()
            for (const anel of poligono) {
              anel.forEach((p, i) => {
                const [x, y] = projetar(cena.enq, [p[0]!, p[1]!])
                if (i === 0) path.moveTo(x, y)
                else path.lineTo(x, y)
              })
              path.closePath()
            }
            caminhosCamada.push(path)
          }
        }
      }
      ctx.save()
      ctx.fillStyle = 'rgba(22,121,186,0.42)'
      for (const path of caminhosCamada) ctx.fill(path, 'evenodd')
      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'
      ctx.strokeStyle = '#062c43'
      ctx.lineWidth = 5
      for (const path of linhasCamada) ctx.stroke(path)
      ctx.strokeStyle = '#43c9ff'
      ctx.lineWidth = 3
      for (const path of linhasCamada) ctx.stroke(path)
      ctx.restore()
      const seg = reduz ? 0 : t / 1000
      desenharOnda(ctx, cena, seg, escala) // a onda descendo até o mar
      desenharCorrenteza(ctx, cena, seg, escala)
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
        chuva: chuvaRef.current,
        escala,
        mostrarIdade: true,
        agora: instante,
        temRegua: temReguaCadastrada,
        compacto,
      }
      const caixas: Caixa[] = []
      // OS CONTROLES DE HTML TAMBÉM OCUPAM O MAPA. Eles são DOM por cima do
      // vidro, e até aqui o canvas não os enxergava: "Timbó" saía atrás do
      // botão +, "Blumenau" atrás do −, sobrando "…mbó" e "…nau" na tela
      // (capturas de 06/09/2026). Reservam ANTES dos nomes das cidades porque
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
      // A marca do chat (confluência): anel claro com contorno escuro, por cima de tudo. É destaque de
      // localização, não cor de faixa — por isso branco, fora da escala de cores das cheias.
      // Os pontos de cota de uma rua (3ª entrega) vêm como `extras`: um anel por ponto, nenhuma linha entre eles.
      const mk = marcaRef.current
      if (mk) {
        const r = 10 * escala
        ctx.save()
        for (const pt of [mk, ...(mk.extras ?? [])]) {
          const [mx, my] = projetar(cena.enq, [pt.lon, pt.lat])
          ctx.lineWidth = 5
          ctx.strokeStyle = '#062c43'
          ctx.beginPath()
          ctx.arc(mx, my, r, 0, 2 * Math.PI)
          ctx.stroke()
          ctx.lineWidth = 2.5
          ctx.strokeStyle = '#ffffff'
          ctx.beginPath()
          ctx.arc(mx, my, r, 0, 2 * Math.PI)
          ctx.stroke()
          ctx.fillStyle = '#ffffff'
          ctx.beginPath()
          ctx.arc(mx, my, 2.5 * escala, 0, 2 * Math.PI)
          ctx.fill()
        }
        ctx.restore()
      }
      if (!reduz) raf = requestAnimationFrame(quadro)
    }
    if (!paginaOculta) raf = requestAnimationFrame(quadro)
    return () => {
      vivo = false // tile que chegar depois não redesenha canvas morto
      cancelAnimationFrame(raf)
    }
  }, [rios, tempoReal, nivelSc, classificacao, reguasDoMapa, agora, tam, cidadesBacia, idxRepro, grade, serie, fundo, vista, rotuloCamada, municipal, animacoesPausadas, movimentoReduzido, paginaOculta, filtro, marca, mostrarMare, mostrarChuva, tracadosOcultos])

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
  }, [cidadeFoco, pedidoDeEnquadrar])

  useEffect(() => {
    if (!cidadeFoco || enquadrou.current) return
    const cena = cenaRef.current
    if (!cena || pinosTodosRef.current.length === 0) return
    const pino = pinosTodosRef.current.find((p) => p.cidade.id === cidadeFoco)
    // Cidade que não está no mapa (id errado no endereço, ou sem coordenada):
    // fica a bacia inteira. Melhor do que zoom num lugar inventado.
    //
    // O enquadramento cabe o pino E AS RÉGUAS DA CIDADE. Itajaí tem onze,
    // espalhadas por 20,8 x 17,6 km: com a janela fixa de 24 km centrada no
    // pino, a DC-10 (Bairro Limoeiro) ficava a 24,2 km do centro, fora da tela.
    // Ver `vistaQueCabeAsReguas`.
    //
    // O centro é o PINO como ele está desenhado (`pino.lat/lon`), não a coordenada do cadastro: em
    // Blumenau, cuja coordenada é de um pluviômetro, o pino fica no rio, e centrar no cadastro abria a
    // tela no morro, sem o pino (auditoria de 06/10/2026).
    const daCidade = reguasRef.current.filter((r) => r.cidade === cidadeFoco)
    const v = vistaQueCabeAsReguas(
      pino ? [pino.lat, pino.lon] : undefined,
      daCidade,
      cena.limitesBase,
      cena.largura > 0 ? cena.altura / cena.largura : 1,
    )
    enquadrou.current = true
    if (!v) return
    // O painel abre junto. No celular ele é uma folha que cobre a parte de baixo, e o pino no meio
    // ficava atrás dela: sobe para a faixa livre (`vistaAcimaDaFolha`).
    const abrePainel = !!pino && !municipal
    setVista(abrePainel ? vistaAcimaDaFolha(v, cena.limitesBase, cena.largura, cena.altura, MARGEM) : v)
    if (pino && !municipal) setSel(pino)
  }, [cidadeFoco, tam, rios, tempoReal, pedidoDeEnquadrar])

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
      const zoom = Math.min(zoomMaximo(cena?.limitesBase, !!cidadeFoco), Math.max(1, v.zoom * fator))
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

  const [ampliado, setAmpliado] = useState(false)
  useEffect(() => {
    if (!ampliado) return
    const anterior = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const sair = (e: KeyboardEvent) => { if (e.key === 'Escape') setAmpliado(false) }
    const mudou = () => { if (!document.fullscreenElement) setAmpliado(false) }
    document.addEventListener('keydown', sair)
    document.addEventListener('fullscreenchange', mudou)
    return () => {
      document.body.style.overflow = anterior
      document.removeEventListener('keydown', sair)
      document.removeEventListener('fullscreenchange', mudou)
    }
  }, [ampliado])
  function telaCheia() {
    if (ampliado) {
      setAmpliado(false)
      if (document.fullscreenElement) void document.exitFullscreen().catch(() => {})
    } else {
      setAmpliado(true) // A ampliação CSS funciona também quando a API nativa é recusada.
      void divRef.current?.requestFullscreen?.().catch(() => {})
    }
  }

  const rotaDoRio = (rioId: string) => (rioId === 'itajai-mirim' ? '/mirim' : '/acu')
  const celular = tam.w > 1 && tam.w <= 700
  const cidadeSelecionada = sel?.cidade.id ?? null
  useEffect(() => {
    setPainelExpandido(false)
  }, [cidadeSelecionada])

  /**
   * A maré no instante mostrado (ao vivo ou da reprodução), pela tábua da Marinha — a MESMA conta que
   * pinta o mar no canvas (`construirCena`). O chip HTML e a linha "Maré" do menu de camadas leem daqui.
   */
  const instanteMostrado = idxRepro !== null && grade.length > 0 ? new Date(grade[Math.min(idxRepro, grade.length - 1)]!) : agora
  const mareAgora = useMemo(() => {
    const paraData = (e: { quando: string; altura_m?: number }) => ({ quando: deBrasilia(e.quando), altura_m: e.altura_m })
    return estadoMareAgora((mareItajai.preamares ?? []).map(paraData), (mareItajai.baixamares ?? []).map(paraData), instanteMostrado)
  }, [instanteMostrado])
  const textoMare = mareAgora.estado === 'subindo' ? 'subindo' : mareAgora.estado === 'baixando' ? 'baixando' : 'sem dado da tábua'
  const setaMare = mareAgora.estado === 'subindo' ? '▲' : mareAgora.estado === 'baixando' ? '▼' : ''
  const opcoesTracado = useMemo(() => opcoesDeTracado(rios ?? []), [rios])


  /**
   * A PONTE COM O CHAT (docs/CHAT-GLOBAL-COMANDOS.md, 06/10/2026). Registrada a cada desenho, com as
   * mesmas funções que os botões usam: o chat nunca clica no DOM nem mexe no estado por fora. Cada função
   * devolve o resultado REAL ("já está no zoom máximo", "esta régua não está no mapa"), e o chat repete.
   * `pronto` só vale com a cena montada e a cidade já enquadrada: é por ele que o chat espera depois de
   * abrir o Monitor de outra cidade.
   */
  const cidadeDaCamada = cidadeFoco ?? sel?.cidade.id ?? 'itajai'
  const nomeDaCidadeEmFoco = cidadeFoco ? cidadesBacia.find((c) => c.id === cidadeFoco)?.nome ?? cidadeFoco : null
  useEffect(() => {
    const opcoes = opcoesRegua.filter((o) => o.valor !== TODAS)
    const rotuloDaRegua = (codigo: string) => opcoes.find((o) => o.valor === codigo)?.rotulo ?? codigo
    const rota = municipal ? '/municipal/ascurra' : cidadeFoco ? `/monitor/${cidadeFoco}` : '/monitor'
    return registrarMonitor({
      cidade: cidadeFoco ?? null,
      get pronto() {
        const cena = cenaRef.current
        return !!cena && pinosTodosRef.current.length > 0 && (!cidadeFoco || enquadrou.current)
      },
      estado: () => ({
        cidade: cidadeFoco ?? null,
        cidadeNome: nomeDaCidadeEmFoco,
        regua: reguaSel ? { codigo: reguaSel, rotulo: rotuloDaRegua(reguaSel) } : null,
        reguas: opcoes.map((o) => ({ codigo: o.valor, rotulo: o.rotulo })),
        fundo,
        camada: rotuloCamada,
        camadasDisponiveis,
        reproducao: idxRepro == null || grade[idxRepro] == null ? null : dataHora(new Date(grade[idxRepro]!)),
        filtro,
        marca: marca?.rotulo ?? null,
      }),
      escolherRegua: (codigo) => {
        if (codigo === 'todas') {
          if (opcoes.length === 0) return { ok: false, texto: `${nomeDaCidadeEmFoco ?? 'Esta tela'} não tem várias réguas para escolher.` }
          escolherRegua(TODAS)
          return { ok: true, texto: `Todas as ${opcoes.length} réguas de ${nomeDaCidadeEmFoco} enquadradas.` }
        }
        if (!opcoes.some((o) => o.valor === codigo) || !reguasDoMapa.some((r) => chaveDaRegua(r) === codigo)) {
          return { ok: false, texto: `A régua ${codigo} não está no mapa agora.` }
        }
        escolherRegua(codigo)
        return { ok: true, texto: `Mapa centralizado na régua ${rotuloDaRegua(codigo)}.` }
      },
      enquadrarCidade: () => {
        if (!cidadeFoco) {
          setVista(VISTA_INTEIRA)
          return { ok: true, texto: 'Bacia inteira enquadrada.' }
        }
        setReguaSel(null)
        setPedidoDeEnquadrar((n) => n + 1)
        return { ok: true, texto: `Mapa enquadrado em ${nomeDaCidadeEmFoco}, no pino da régua.` }
      },
      zoom: (sentido) => {
        const max = zoomMaximo(cenaRef.current?.limitesBase, !!cidadeFoco)
        if (sentido === 'mais' && vista.zoom >= max) return { ok: false, texto: 'O mapa já está no zoom máximo.' }
        if (sentido === 'menos' && vista.zoom <= 1) return { ok: false, texto: 'O mapa já mostra a bacia inteira.' }
        aplicarZoom(sentido === 'mais' ? 1.6 : 1 / 1.6)
        return { ok: true, texto: sentido === 'mais' ? 'Aproximei o mapa.' : 'Afastei o mapa.' }
      },
      verBacia: () => {
        setVista(VISTA_INTEIRA)
        return { ok: true, texto: 'Bacia inteira enquadrada.' }
      },
      fundo: (f) => {
        if (!ehChaveDeFundo(f)) return { ok: false, texto: 'Esse fundo não existe no mapa.' }
        setFundo(f)
        return { ok: true, texto: `Fundo do mapa: ${NOME_DO_FUNDO[f]}.` }
      },
      camada: (arquivo) => {
        if (arquivo !== 'off' && !camadasDisponiveis.some((c) => c.arquivo === arquivo)) {
          return { ok: false, texto: 'Essa camada não está disponível nesta cidade.' }
        }
        setPedidoCamada((p) => ({ cidade: cidadeDaCamada, modo: arquivo, n: (p?.n ?? 0) + 1 }))
        if (arquivo === 'off') return { ok: true, texto: 'Camadas de cheia ocultas.' }
        const rotulo = camadasDisponiveis.find((c) => c.arquivo === arquivo)?.rotulo ?? arquivo
        return { ok: true, texto: `Camada ligada: ${rotulo}. É referência (cheia passada ou simulação), não alagamento atual.` }
      },
      aoVivo: () => {
        if (idxRepro == null) return { ok: true, texto: 'O mapa já mostra as leituras mais recentes.' }
        setTocando(false)
        setIdxRepro(null)
        return { ok: true, texto: 'Voltei às leituras mais recentes. Cada uma mostra a hora dela no painel.' }
      },
      filtrar: (f) => {
        if (municipal) return { ok: false, texto: 'O filtro não existe no Monitor de Ascurra.' }
        if (f === null) {
          if (!filtro) return { ok: true, texto: 'Não há filtro ligado: o mapa já mostra todas as cidades e réguas.' }
          setFiltro(null)
          return { ok: true, texto: 'Filtro limpo: o mapa mostra todas as cidades e réguas de novo.' }
        }
        if (f === 'acima_do_normal') {
          const pinos = pinosTodosRef.current.filter((p) => faixaAcimaDoNormal(p.faixa))
          const reguasAcima = reguasDoMapa.filter((r) => faixaAcimaDoNormal(r.faixa))
          const nomesAcima = [...pinos.map((p) => p.cidade.nome), ...reguasAcima.map((r) => `${r.codigo} · ${r.nome}`)]
          if (nomesAcima.length === 0) {
            return { ok: true, texto: 'Nenhuma cidade ou régua do mapa está com faixa acima de "Abaixo da atenção" agora: o filtro não foi ligado. Cinza não entra na conta, e faixa baixa no rio não quer dizer que não há alagamento. Em emergência, ligue 199.' }
          }
          setFiltro('acima_do_normal')
          setSel(null)
          setReguaSel(null)
          setVista(VISTA_INTEIRA)
          return { ok: true, texto: `Filtro ligado: a bacia inteira, só com a faixa do mapa acima de "Abaixo da atenção" (${nomesAcima.length}): ${nomesAcima.join(', ')}. Cada cor é a faixa da cidade na régua dela; cinza fica de fora. Peça "quais cidades estão em alerta?" para as faixas e "limpar filtros" para voltar.` }
        }
        const reguaFresca = new Set(reguasDoMapa.filter((r) => !reguaSemLeituraDeAgora(r, agora)).map((r) => r.cidade))
        const cidades = pinosTodosRef.current.filter((p) => pinoSemLeituraDeAgora(p, agora, reguaFresca.has(p.cidade.id)))
        const reguas = reguasDoMapa.filter((r) => reguaSemLeituraDeAgora(r, agora))
        const nomes = [...cidades.map((p) => p.cidade.nome), ...reguas.map((r) => `${r.codigo} · ${r.nome}`)]
        if (nomes.length === 0) return { ok: true, texto: 'Todas as cidades e réguas do mapa têm leitura de agora: o filtro não foi ligado.' }
        setFiltro('sem_leitura')
        setSel(null)
        setReguaSel(null)
        // A bacia inteira: o que ficou sem leitura pode estar longe da cidade aberta.
        setVista(VISTA_INTEIRA)
        const lista = nomes.length > 10 ? `${nomes.slice(0, 10).join(', ')} e mais ${nomes.length - 10}` : nomes.join(', ')
        return { ok: true, texto: `Filtro ligado: a bacia inteira, só com o que está sem leitura de agora (${nomes.length}): ${lista}. "Sem leitura" é sem medição, sem horário ou com leitura de mais de 3 h. Peça "limpar filtros" para voltar.` }
      },
      // 12ª entrega: enquadrar um rio inteiro (as cidades dele no mapa) ou as barragens, pelo mesmo
      // `vistaQueCabeAsReguas` do pino da cidade; fechar o painel; o menu de cidades.
      enquadrar: (alvo) => {
        if (municipal) return { ok: false, texto: 'O Monitor de Ascurra mostra só a régua de Ascurra.' }
        const cena = cenaRef.current
        if (!cena) return { ok: false, texto: 'O mapa ainda não está pronto.' }
        const pontos = alvo.tipo === 'rio'
          ? pinosTodosRef.current.filter((p) => p.rioId === alvo.rioId).map((p) => ({ lat: p.lat, lon: p.lon }))
          : barragensRef.current.map((b) => ({ lat: b.lat, lon: b.lon }))
        const nomeRio = alvo.tipo === 'rio' ? (alvo.rioId === 'itajai-mirim' ? 'Itajaí-Mirim' : 'Itajaí-Açu') : ''
        if (pontos.length === 0) {
          return { ok: false, texto: alvo.tipo === 'rio' ? `O ${nomeRio} não tem cidade no mapa agora.` : 'As barragens ainda não têm posição no mapa (a fonte não respondeu). Peça "como estão as barragens?" para o estado das comportas.' }
        }
        const v = vistaQueCabeAsReguas(undefined, pontos, cena.limitesBase, cena.largura > 0 ? cena.altura / cena.largura : 1)
        if (!v) return { ok: false, texto: 'Não consegui enquadrar esses pontos no mapa.' }
        setSel(null)
        setReguaSel(null)
        setVista(v)
        return {
          ok: true,
          texto: alvo.tipo === 'rio'
            ? `Mapa enquadrado no ${nomeRio}: as ${pontos.length} cidades com régua dele, com os afluentes. Cada cor é a faixa da cidade na régua dela.`
            : `Mapa enquadrado nas barragens de contenção (${pontos.length}), comporta a comporta. Peça "como estão as barragens?" para o estado e a hora de cada uma.`,
        }
      },
      fecharPainel: () => {
        if (!sel) return { ok: true, texto: 'Não há painel de cidade aberto.' }
        setSel(null)
        return { ok: true, texto: `Painel de ${sel.cidade.nome} fechado. O mapa continua no mesmo lugar.` }
      },
      menuDeCidades: (acao) => {
        if (municipal) return { ok: false, texto: 'O Monitor de Ascurra não tem menu de cidades.' }
        const abrir = acao === 'abrir'
        if (menuAberto === abrir) return { ok: true, texto: abrir ? 'O menu de cidades já está aberto.' : 'O menu de cidades já está fechado.' }
        setMenuAberto(abrir)
        return { ok: true, texto: abrir ? 'Menu de cidades aberto: toque numa cidade para ir até ela, ou peça "mostrar Gaspar".' : 'Menu de cidades fechado.' }
      },
      // 7ª entrega: os mesmos estados do botão "Pausar/Retomar animações" e do "abrir/recolher" da legenda.
      animacoes: (acao) => {
        if (acao === 'pausar') {
          if (animacoesPausadas) return { ok: true, texto: 'As animações já estão pausadas.' }
          setAnimacoesPausadas(true)
          return { ok: true, texto: 'Animações pausadas: as ondas pararam. As cores e os números não mudam.' }
        }
        if (!animacoesPausadas) {
          return { ok: true, texto: movimentoReduzido ? 'As animações não estão pausadas aqui, mas o aparelho pede movimento reduzido, então elas ficam paradas.' : 'As animações já estão ligadas.' }
        }
        setAnimacoesPausadas(false)
        return { ok: true, texto: movimentoReduzido ? 'Animações retomadas, mas o aparelho pede movimento reduzido, então elas continuam paradas.' : 'Animações retomadas. As ondas mostram só o sentido do curso, não a velocidade da água.' }
      },
      legendaDoMapa: (acao) => {
        const abrir = acao === 'abrir'
        if (legendaAberta === abrir) return { ok: true, texto: abrir ? 'A legenda já está aberta, no canto do mapa.' : 'A legenda já está recolhida.' }
        setLegendaAberta(abrir)
        return { ok: true, texto: abrir ? 'Legenda aberta no canto do mapa. Peça "explicar as cores" para ler aqui.' : 'Legenda recolhida. O botão "abrir" no canto do mapa a traz de volta.' }
      },
      // A reprodução das últimas 24 h, pelos mesmos estados do botão "Reproduzir 24 h" e da barra de tempo.
      reproducao: (p) => {
        if (municipal) return { ok: false, texto: 'A reprodução não existe no Monitor de Ascurra.' }
        if (grade.length === 0) return { ok: false, texto: 'Ainda não há série publicada para reproduzir.' }
        const quando = (i: number) => dataHora(new Date(grade[i]!))
        if (p.acao === 'tocar') {
          setIdxRepro((x) => (x == null ? 0 : x))
          setTocando(true)
          return { ok: true, texto: `Reproduzindo as últimas horas medidas, de ${quando(0)} até agora, de meia em meia hora. É o que já foi medido, não previsão; no fim, o mapa volta ao vivo.` }
        }
        if (p.acao === 'pausar') {
          if (!tocando) {
            return { ok: true, texto: idxRepro == null ? 'A reprodução não está tocando: o mapa mostra as leituras mais recentes.' : `A reprodução já está parada em ${quando(idxRepro)}.` }
          }
          setTocando(false)
          return { ok: true, texto: `Reprodução pausada em ${quando(idxRepro ?? 0)}. Peça "ir para a leitura mais recente" para voltar ao agora.` }
        }
        const t = p.instante.getTime()
        if (t < grade[0]!) return { ok: false, texto: `A reprodução só cobre desde ${quando(0)}.` }
        let i = 0
        for (let k = 0; k < grade.length; k++) if (grade[k]! <= t) i = k
        setTocando(false)
        if (i >= grade.length - 1) {
          setIdxRepro(null)
          return { ok: true, texto: 'Esse horário é o mais recente: o mapa mostra as leituras ao vivo.' }
        }
        setIdxRepro(i)
        return { ok: true, texto: `Mapa em ${quando(i)}, com a última leitura de cada cidade até esse instante — passado, não agora. Peça "ir para a leitura mais recente" para voltar.` }
      },
      marcarPonto: (p) => {
        if (!p) {
          setMarca(null)
          return { ok: true, texto: 'Marca tirada do mapa.' }
        }
        const cena = cenaRef.current
        if (!cena) return { ok: false, texto: 'O mapa ainda não carregou.' }
        const b = cena.limitesBase
        const pts = [p, ...(p.extras ?? [])]
        if (pts.some((q) => q.lon < b.minLon || q.lon > b.maxLon || q.lat < b.minLat || q.lat > b.maxLat)) {
          return { ok: false, texto: 'Esse ponto fica fora do mapa do Monitor.' }
        }
        setMarca(p)
        setSel(null)
        setReguaSel(null)
        // O centro da vista é o meio dos pontos (um só: o próprio ponto).
        const lats = pts.map((q) => q.lat)
        const lons = pts.map((q) => q.lon)
        const v = vistaDaCidade([(Math.min(...lats) + Math.max(...lats)) / 2, (Math.min(...lons) + Math.max(...lons)) / 2], b, p.km ?? 6)
        if (v) setVista(v)
        return { ok: true, texto: pts.length > 1 ? `Mapa centrado, com ${pts.length} anéis brancos.` : 'Mapa centrado e marcado com um anel branco.' }
      },
      explicar: (id) => {
        const pino = pinosTodosRef.current.find((p) => p.cidade.id === id)
        if (!pino) return null
        return { cidadeNome: pino.cidade.nome, ...textosDoFoco(pino) }
      },
      retrato: (): Retrato => ({ rota, cidade: cidadeFoco ?? null, vista, regua: reguaSel, fundo, camada: modoCamada, filtro, marca }),
      restaurar: (r) => {
        enquadrou.current = true
        setFiltro(r.filtro ?? null)
        setMarca(r.marca ?? null)
        if (r.fundo && ehChaveDeFundo(r.fundo)) setFundo(r.fundo)
        if (r.camada != null) setPedidoCamada((p) => ({ cidade: cidadeDaCamada, modo: r.camada!, n: (p?.n ?? 0) + 1 }))
        setReguaSel(r.regua ?? null)
        if (r.regua) setSel(null)
        if (r.vista) setVista(r.vista as Vista)
        return { ok: true, texto: 'ok' }
      },
    })
  })

  /**
   * Endereço com `?regua=DC-05` e `?fundo=satelite` (docs/CHAT-GLOBAL-COMANDOS.md): aplicados uma vez,
   * depois que a cidade é enquadrada. Valor que não existe é ignorado — nunca vira régua inventada.
   */
  const urlAplicada = useRef<string | null>(null)
  useEffect(() => {
    const chave = `${cidadeFoco ?? ''}?${busca.toString()}`
    if (urlAplicada.current === chave || !busca.toString()) return
    const cena = cenaRef.current
    if (!cena || pinosTodosRef.current.length === 0 || (cidadeFoco && !enquadrou.current)) return
    urlAplicada.current = chave
    const f = busca.get('fundo')
    if (f && ehChaveDeFundo(f)) setFundo(f)
    const r = busca.get('regua')
    if (r && opcoesRegua.some((o) => o.valor === r && o.valor !== TODAS)) escolherRegua(r)
  })
  /** A lista de cores e símbolos — a mesma na legenda do canto e no menu "Camadas do mapa". */
  const listaDaLegenda = (
    <ul className={estilos.listaLegenda}>
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
            {/* C7, camada 2: a cor tracejada é a classificação da própria Defesa
                Civil de SC, na régua da estação — só onde não há faixa municipal.
                A amostra é tracejada e neutra porque a cor varia com a faixa. */}
            <li>
              <span className={`${estilos.amostra} ${estilos.amostraTracejada}`} />
              Faixa estadual (tracejado) — classificação da Defesa Civil de SC, não cota deste site
            </li>
            {/* A linha-guia (14/09/2026): onde os pinos se amontoam, o nome vai
                para um lugar livre e a seta aponta a cidade dele. */}
            <li>
              <span className={`${estilos.amostra} ${estilos.amostraSeta}`} aria-hidden="true">→</span>
              Seta — o nome ficou afastado por falta de espaço; a ponta indica a cidade dele
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
  )

  return (
    <div className={`${estilos.pagina} ${municipal ? estilos.paginaMunicipal : ''}`}>
      <div ref={divRef} className={`${estilos.palco} ${ampliado ? estilos.ampliado : ''} ${municipal ? estilos.municipal : ''} ${!municipal && !reguaSel && (sel ?? hover) ? estilos.temPainel : ''}`}>
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
          aria-label={municipal ? "Monitor de Ascurra: mapa, régua e camadas de cheia" : "Monitoramento da bacia do Itajaí: Açu e Mirim, cada trecho na cor da faixa da cidade a montante, com correnteza, chuva e maré na foz"}
        />


        {/* COLUNA DA ESQUERDA — o topo em cima, o rodapé embaixo, os dois na
            MESMA coluna, com `justify-content: space-between`.

            Por que não bastou empilhar o rodapé: título/menu/zoom continuavam
            num bloco `absolute` colado no topo e o rodapé noutro colado
            embaixo. Com a legenda aberta numa tela larga o rodapé subia e
            cobria o botão "−" — AFASTAR, que é justamente como se volta para a
            bacia inteira depois de se perder no zoom (medido em 1280×900 e
            1440×700, 06/09/2026). O comentário antigo do CSS já contava essa
            história com outros números: 13rem cobria, 17rem não. Teto mágico
            é sempre provisório.

            Numa coluna só, os dois disputam a mesma altura pelas regras do
            flex: quando não cabe, a legenda e o menu ROLAM, e nenhum dos dois
            invade o outro em resolução nenhuma. */}
        <div className={`${estilos.colunaEsquerda} ${menuAberto ? estilos.comMenu : ''} ${camadasAbertas ? estilos.comCamadas : ''} ${chatAberto ? estilos.chatAberto : ''}`}>
        {/* Título e aviso no topo-esquerdo (o chip da maré fica no topo-direito,
            desenhado no canvas). O botão de tela cheia vai no canto inferior
            direito para não colidir com o chip. */}
        <div className={estilos.cantoEsquerdo}>
        {/* TOPO. No computador, o cartão de sempre: título, "Cidades", aviso, "Tela cheia" e o chat.
            No celular (redesenho de 07/10/2026, etapa 1), o mesmo DOM vira UMA LINHA transparente: a
            caixa do chat em pílula ("Cidade, régua ou pergunta") e o botão "Cidades"; título e aviso
            saem (o 199 está na faixa do topo da página, e volta aqui em tela cheia); "Tela cheia" e
            "Camadas do mapa" ficam nos botões redondos da coluna da direita. */}
        <div
          className={estilos.topo}
          data-tapa-mapa
          onFocus={(e) => setFocoNoChat((e.target as Element).matches?.('input[aria-label="Pergunte ou peça"]') ?? false)}
          onBlur={() => setFocoNoChat(false)}
        >
          <strong className={estilos.titulo}>{municipal ? "Monitor de Ascurra" : "Monitoramento da bacia"}</strong>
          {!municipal && <button
            type="button"
            className={estilos.botaoMenu}
            aria-expanded={menuAberto}
            aria-controls="menu-cidades"
            onClick={() => setMenuAberto((v) => !v)}
          >
            {menuAberto ? 'Fechar' : 'Cidades ▾'}
          </button>}
          {opcoesRegua.length > 0 && (
            <label className={estilos.seletorRegua}>
              <span>Régua</span>
              <select id="seletor-regua" value={valorSeletor} onChange={(e) => escolherRegua(e.target.value)}>
                {opcoesRegua.map((o) => (
                  <option key={o.valor} value={o.valor}>{o.rotulo}</option>
                ))}
              </select>
            </label>
          )}
          <span className={estilos.aviso}>
            {municipal ? "Dados observados · não é alerta oficial." : <>Não é alerta oficial. Emergência: <strong>199</strong>. Siga a Defesa Civil.</>}
          </span>
          <button type="button" className={estilos.botaoCheia} onClick={telaCheia}>
            {ampliado ? 'Sair da tela cheia' : 'Tela cheia'}
          </button>
          {/* O chat, dentro do bloco do topo (decisão do Jefferson, 06/10/2026): o retângulo do mapa não
              muda, e os pedidos do chat chegam pela ponte abaixo (docs/CHAT-GLOBAL-COMANDOS.md). */}
          <ChatNoTopo variante="monitor" />
        </div>

        {/* DESTAQUE DA BACIA (celular e computador): a cidade com a faixa municipal mais grave agora,
            com o nível e a hora DELA. Só existe com faixa válida — cota do cadastro e leitura fresca
            (`destaqueDaBacia`); sem isso não aparece nada, e nunca na reprodução. Toque abre a cidade. */}
        {destaque && destaque.nivel != null ? (
          <button
            type="button"
            className={estilos.destaque}
            data-faixa={destaque.faixa}
            data-tapa-mapa
            onClick={() => {
              const alvo = destaque
              setReguaSel(null)
              if (alvo.cidade.id !== cidadeFoco) navigate(`/monitor/${alvo.cidade.id}`)
              setSel(alvo)
            }}
          >
            <span className={estilos.destaqueTexto}>
              <strong>{destaque.cidade.nome}</strong> em {ROTULO_FAIXA[destaque.faixa].toLowerCase()} · <strong>{metros(destaque.nivel)}</strong>
              {destaque.medidoEm ? <> · {textoIdade(idadeMin(destaque.medidoEm, agora))}</> : null}
            </span>
            <span className={estilos.destaqueVer}>ver ›</span>
          </button>
        ) : null}

        {/* COLUNA DA DIREITA. No celular: "Camadas do mapa", "Tela cheia" e o zoom, redondos, um abaixo
            do outro, encostados na borda direita — o centro fica para os rios. No computador só o zoom
            aparece aqui (os dois primeiros ficam escondidos pelo CSS), no mesmo lugar de antes. */}
        <div className={estilos.ladoDireito} data-tapa-mapa>
          <button
            type="button"
            className={`${estilos.botaoRedondo} ${estilos.soCelular}`}
            aria-label="Camadas do mapa"
            aria-expanded={camadasAbertas}
            aria-controls="camadas-mapa"
            onClick={() => setCamadasAbertas((v) => !v)}
          >
            <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false">
              <path d="M12 3 2 8.5 12 14l10-5.5L12 3Z" fill="currentColor" opacity=".95" />
              <path d="m4.6 11.8-2.6 1.4L12 18.7l10-5.5-2.6-1.4L12 15.9l-7.4-4.1Z" fill="currentColor" opacity=".6" />
            </svg>
          </button>
          <button
            type="button"
            className={`${estilos.botaoRedondo} ${estilos.soCelular}`}
            aria-label={ampliado ? 'Sair da tela cheia' : 'Tela cheia'}
            onClick={telaCheia}
          >
            <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">
              <path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
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
          {!municipal && vista.zoom > 1 ? (
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

        {!municipal && tempoReal.fonteItajaiOk === false && <p className={estilos.rotuloCamada} role="status" data-tapa-mapa>
          Fonte de Itajaí indisponível: não foi possível obter as medições das réguas municipais.
        </p>}
        {municipal && <div className={estilos.resumoMunicipal} data-tapa-mapa>
          <strong>{leituraMunicipal ? metros(leituraMunicipal.nivelBrutoM) : 'Sem leitura'} · {faixaMunicipal.nome}</strong>
          <span>{leituraMunicipal?.medidoEm ? dataHora(leituraMunicipal.medidoEm) + ' · ' + textoIdade(idadeMin(leituraMunicipal.medidoEm, agora)) : 'Horário indisponível'}</span>
          <span>Chuva: {leituraMunicipal?.chuva24hMm?.toLocaleString('pt-BR', { maximumFractionDigits: 1 }) ?? '—'} mm / 24 h · {leituraMunicipal?.chuva168hMm?.toLocaleString('pt-BR', { maximumFractionDigits: 1 }) ?? '—'} mm / 7 dias</span>
          <a href="https://monitoramento.defesacivil.sc.gov.br/estacao/DCSC-00003" target="_blank" rel="noreferrer">Fonte: DCSC-00003 · Ponte do Beber</a>
          <span>Faixa calculada conforme C18; não representa área alagada.</span>
          <button type="button" onClick={() => navigate('/municipal/ascurra/dados')}>Dados e histórico</button>
        </div>}
        {rotuloCamada && <p className={estilos.rotuloCamada} data-tapa-mapa>
          {rotuloCamada} · referência, não alagamento atual
        </p>}
        {filtro && <p className={estilos.rotuloCamada} role="status" data-tapa-mapa>
          {filtro === 'sem_leitura' ? 'Filtro: só cidades e réguas sem leitura de agora' : 'Filtro: só cidades e réguas com faixa acima do normal'}
          <button type="button" className={estilos.botaoAviso} onClick={() => setFiltro(null)}>Limpar filtro</button>
        </p>}
        {marca && <p className={estilos.rotuloCamada} role="status" data-tapa-mapa>
          Marca: {marca.rotulo}
          <button type="button" className={estilos.botaoAviso} onClick={() => setMarca(null)}>Tirar marca</button>
        </p>}
        {/* CAMADAS DO MAPA (redesenho de 07/10/2026). Um menu só, nesta ordem: camadas de cheia (o
            controle de sempre, `CamadasMonitor`, que continua montado com o menu fechado — o chat pede
            camadas por ele), maré e chuva (visibilidade), legenda, traçados dos rios (um por curso real;
            Benedito e Rio dos Cedros separados) e o fundo do mapa, que saiu da legenda. Fechado, fica
            escondido (`hidden`), não desmontado. */}
        <button
          type="button"
          className={`${estilos.botaoCamadas} ${estilos.soComputador}`}
          aria-expanded={camadasAbertas}
          aria-controls="camadas-mapa"
          onClick={() => setCamadasAbertas((v) => !v)}
        >
          Camadas do mapa {camadasAbertas ? '▴' : '▾'}
        </button>
        <div id="camadas-mapa" className={estilos.painelCamadas} hidden={!camadasAbertas} data-tapa-mapa>
          <div className={estilos.painelCamadasTopo}>
            <strong>Camadas do mapa</strong>
            <button type="button" className={estilos.botaoFecharCamadas} aria-label="Fechar camadas do mapa" onClick={() => setCamadasAbertas(false)}>✕</button>
          </div>
          <div className={estilos.linhaCamada}>
            <span className={estilos.iconeCamada} aria-hidden="true">
              <svg viewBox="0 0 24 24" width="22" height="22"><path d="M3 16c2.5 0 2.5-2 5-2s2.5 2 5 2 2.5-2 5-2 2.5 2 5 2M3 11c2.5 0 2.5-2 5-2s2.5 2 5 2 2.5-2 5-2 2.5 2 5 2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
            </span>
            <label className={estilos.textoCamada} htmlFor="interruptor-cheia">
              <strong>Camadas de cheia</strong>
              <small>{rotuloCamada ?? 'nenhuma camada desenhada agora'}</small>
            </label>
            <input
              id="interruptor-cheia"
              className={estilos.interruptor}
              type="checkbox"
              role="switch"
              checked={modoCamada !== 'off'}
              onChange={(e) => setPedidoCamada((pd) => ({ cidade: cidadeDaCamada, modo: e.target.checked ? 'auto' : 'off', n: (pd?.n ?? 0) + 1 }))}
            />
          </div>
          <div className={estilos.detalheCamada} hidden={modoCamada === 'off'}>
          <CamadasMonitor key={cidadeFoco ?? sel?.cidade.id ?? 'itajai'} cidade={cidadeFoco ?? sel?.cidade.id ?? 'itajai'}
            leituras={tempoReal.leituras} agora={agora} reproduzindo={idxRepro !== null}
            onCamada={receberCamada} somenteDados={municipal}
            pedido={pedidoCamada} onOpcoes={setCamadasDisponiveis} onModo={setModoCamada}
            nomeEscolhida={(cidadeFoco ?? sel?.cidade.id) ? cidadesBacia.find((c) => c.id === (cidadeFoco ?? sel?.cidade.id))?.nome ?? null : null} />
          </div>
          {!municipal ? (
            <div className={estilos.linhaCamada}>
              <span className={estilos.iconeCamada} aria-hidden="true">
                <svg viewBox="0 0 24 24" width="22" height="22"><path d="M2 14c3 0 3-2.5 6-2.5s3 2.5 6 2.5 3-2.5 6-2.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /><path d="M2 19c3 0 3-2.5 6-2.5s3 2.5 6 2.5 3-2.5 6-2.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity=".6" /></svg>
              </span>
              <label className={estilos.textoCamada} htmlFor="interruptor-mare">
                <strong>Maré</strong>
                <small>Maré: {textoMare} {setaMare} · porto de Itajaí</small>
              </label>
              <input id="interruptor-mare" className={estilos.interruptor} type="checkbox" role="switch" checked={mostrarMare} onChange={(e) => { setMostrarMare(e.target.checked); setMareAberta(false) }} />
            </div>
          ) : null}
          {!municipal ? (
            <div className={estilos.linhaCamada}>
              <span className={estilos.iconeCamada} aria-hidden="true">
                <svg viewBox="0 0 24 24" width="22" height="22"><path d="M12 3s-6 7-6 11a6 6 0 0 0 12 0c0-4-6-11-6-11Z" fill="currentColor" opacity=".9" /></svg>
              </span>
              <label className={estilos.textoCamada} htmlFor="interruptor-chuva">
                <strong>Chuva 24 h</strong>
                <small>acumulado nas estações com pluviômetro</small>
              </label>
              <input id="interruptor-chuva" className={estilos.interruptor} type="checkbox" role="switch" checked={mostrarChuva} onChange={(e) => setMostrarChuva(e.target.checked)} />
            </div>
          ) : null}
          {/* "Pausar/Retomar animações" saiu da legenda (que no celular fica escondida) para cá: um só botão,
              o mesmo que o chat aciona pela ponte. */}
          <div className={estilos.linhaCamada}>
            <span className={estilos.iconeCamada} aria-hidden="true">
              <svg viewBox="0 0 24 24" width="22" height="22"><path d="M3 12c3-4 6 4 9 0s6-4 9 0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /><path d="M14 8l5 4-5 4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </span>
            <span className={estilos.textoCamada}>
              <strong>Animações</strong>
              <small>{movimentoReduzido ? 'movimento reduzido ativado no aparelho' : 'correnteza e crista; só ilustram o sentido'}</small>
            </span>
            <button type="button" className={estilos.botaoLegenda}
              aria-pressed={animacoesPausadas}
              onClick={() => setAnimacoesPausadas(v => !v)}>
              {animacoesPausadas ? 'Retomar animações' : 'Pausar animações'}
            </button>
          </div>
          <details className={estilos.legendaCamada}>
            <summary>
              <span className={estilos.iconeCamada} aria-hidden="true">
                <svg viewBox="0 0 24 24" width="22" height="22"><rect x="3" y="4" width="18" height="16" rx="2" fill="none" stroke="currentColor" strokeWidth="2" /><path d="M7 9h4M7 13h4M7 17h4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /><circle cx="16" cy="9" r="1.6" fill="currentColor" /><circle cx="16" cy="13" r="1.6" fill="currentColor" /><circle cx="16" cy="17" r="1.6" fill="currentColor" /></svg>
              </span>
              <span className={estilos.textoCamada}>
                <strong>Legenda</strong>
                <small>cores e símbolos</small>
              </span>
            </summary>
            {listaDaLegenda}
            <p className={estilos.legendaNota}>Cor é a faixa na régua de cada cidade, <strong>nunca o metro</strong> entre cidades. Cinza = sem faixa para afirmar.</p>
          </details>
          {opcoesTracado.length > 0 ? (
            <div className={estilos.secaoCamada}>
              <div className={estilos.linhaCamada}>
                <span className={estilos.iconeCamada} aria-hidden="true">
                  <svg viewBox="0 0 24 24" width="22" height="22"><path d="M3 12c3-6 6 6 9 0s6-6 9 0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>
                </span>
                <span className={estilos.textoCamada}>
                  <strong>Traçados dos rios</strong>
                  <small>cursos desenhados no mapa</small>
                </span>
                <span className={estilos.contagemTracados}>{contagemDeTracados(opcoesTracado, tracadosOcultos)}</span>
              </div>
              <ul className={estilos.listaTracados}>
                {opcoesTracado.map((o) => (
                  <li key={o.id}>
                    <label>
                      <input
                        type="checkbox"
                        checked={o.fixo || !tracadosOcultos.has(o.id)}
                        disabled={o.fixo}
                        onChange={(e) => setTracadosOcultos((atual) => {
                          const prox = new Set(atual)
                          if (e.target.checked) prox.delete(o.id)
                          else prox.add(o.id)
                          return prox
                        })}
                      />
                      <span>{o.nome}{o.fixo ? <small> · tronco, sempre no mapa</small> : null}</span>
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          <div className={estilos.secaoCamada}>
            <div className={estilos.linhaCamada}>
              <span className={estilos.iconeCamada} aria-hidden="true">
                <svg viewBox="0 0 24 24" width="22" height="22"><path d="m3 6 6-2 6 2 6-2v14l-6 2-6-2-6 2V6Z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" /><path d="M9 4v14M15 6v14" stroke="currentColor" strokeWidth="2" /></svg>
              </span>
              <span className={estilos.textoCamada}>
                <strong>Fundo do mapa</strong>
                <small>{FUNDOS[fundo].nome}</small>
              </span>
            </div>
            {/* O ESCURO é o padrão por FUNÇÃO, não por estética: qualquer fundo com textura concorre com
                as faixas de alerta. Ver `docs/CAMADAS-DE-MAPA.md`. */}
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
          </div>
        </div>

        {/* MENU DE CIDADES, na ordem do rio — em GRUPOS, porque o Açu é árvore:
            Taió e Ituporanga correm em paralelo, e uma lista "Taió → Ituporanga
            → Rio do Sul" afirmaria uma sequência que não existe. Toque numa
            cidade abre o monitor DELA (o mesmo mapa, enquadrado nela). */}
        {!municipal && menuAberto ? (
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
                            onClick={() =>
                              item.id === cidadeFoco
                                ? setPedidoDeEnquadrar((n) => n + 1)
                                : navigate(`/monitor/${item.id}`)
                            }
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

        </div>
        {/* RODAPÉ — uma coluna só, e é isso que impede a sobreposição.

            O DEFEITO QUE ISTO CORRIGE (06/09/2026, relatado pelo Jefferson:
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
          {/* CHIP DA MARÉ (HTML desde 07/10/2026; antes era desenhado no canto do canvas). O estado é o
              do instante mostrado — ao vivo ou da reprodução —, pela tábua da Marinha, a mesma conta
              que pinta o mar. Ao toque, a próxima preamar ou baixa-mar. Some com a maré desligada. */}
          {!municipal && mostrarMare ? (
            <div className={estilos.mare} data-tapa-mapa>
              <button
                type="button"
                className={estilos.chipMare}
                aria-expanded={mareAberta}
                aria-controls="mare-detalhe"
                onClick={() => setMareAberta((v) => !v)}
              >
                <span aria-hidden="true">≈</span> Maré: {textoMare} {setaMare} <span aria-hidden="true">{mareAberta ? '▴' : '▾'}</span>
              </button>
              {mareAberta ? (
                <div id="mare-detalhe" className={estilos.mareDetalhe}>
                  {mareAgora.proxima ? (
                    <p>
                      Próxima {mareAgora.proxima.tipo === 'preamar' ? 'preamar' : 'baixa-mar'} às{' '}
                      <strong>{horaDeBrasilia(mareAgora.proxima.quando)}</strong> de {diaDeBrasilia(mareAgora.proxima.quando)}
                      {mareAgora.proxima.altura_m != null ? ` (${numero(mareAgora.proxima.altura_m)} m sobre o nível de redução da carta náutica, não régua de rio)` : ''}.
                    </p>
                  ) : (
                    <p>A tábua não tem preamar ou baixa-mar que cerque este horário.</p>
                  )}
                  <p>
                    {mareItajai._meta?.fonte_curta ?? 'Tábua de maré'}, porto de Itajaí.{' '}
                    <strong>Maré não é cheia</strong>: a maré alta trava o escoamento do rio na foz.
                  </p>
                </div>
              ) : null}
            </div>
          ) : null}
          {/* Reprodução das últimas 24 h: a onda de cor descendo, do MEDIDO. Só
              aparece quando há série publicada. Na reprodução, o "Agora" do fim da barra vira o
              horário histórico e a linha de estado diz que não é a leitura atual (correção 5 da
              maquete, 07/10/2026). */}
          {grade.length > 0 ? (
            <div className={`${estilos.controles} ${idxRepro == null ? '' : estilos.controlesHistoricos}`} data-tapa-mapa>
              <button
                type="button"
                className={estilos.botaoPlay}
                aria-label={tocando ? '⏸ Pausar' : '▶ Reproduzir 24 h'}
                onClick={() => {
                  if (tocando) {
                    setTocando(false)
                  } else {
                    setIdxRepro((x) => (x == null ? 0 : x)) // começa do início da janela
                    setTocando(true)
                  }
                }}
              >
                <span className={estilos.iconePlay} aria-hidden="true">{tocando ? '⏸' : '▶'}</span>
                <span className={estilos.textoPlay} aria-hidden="true">{tocando ? 'Pausar' : 'Reproduzir'}</span>
                <span className={estilos.janelaPlay} aria-hidden="true">24 h</span>
              </button>
              <div className={estilos.linhaDoTempo}>
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
                <div className={estilos.marcas} aria-hidden="true">
                  <span>−24 h</span>
                  <span>−18 h</span>
                  <span>−12 h</span>
                  <span>−6 h</span>
                  <span className={idxRepro == null ? estilos.marcaAgora : estilos.marcaHistorica}>
                    {idxRepro == null ? 'Agora' : horaDeBrasilia(new Date(grade[idxRepro]!))}
                  </span>
                </div>
              </div>
              <span className={estilos.instante} role="status">
                {idxRepro == null ? 'ao vivo' : <>{dataHora(new Date(grade[idxRepro]!))} · reprodução · não é a leitura atual</>}
              </span>
            </div>
          ) : null}
        {/* Legenda, canto inferior esquerdo. No celular nasce recolhida e, recolhida, fica escondida:
            lá ela abre pelo menu "Camadas do mapa" ou pelo chat ("abrir a legenda"). O fundo do mapa
            saiu daqui para o menu de camadas; a atribuição ficou fora, sempre à vista. */}
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
          <p className={estilos.legendaNota}>No Itajaí-Açu, de Santa Regina até a foz, a cor do traçado é referência visual da DC-11. Não indica nível local, ruas alagadas nem classificação das outras réguas. Na reprodução histórica essa referência fica desativada.</p>
          <p className={estilos.legendaNota}>Ondas indicam apenas o sentido ilustrativo do curso, com velocidade visual constante. Cinza em movimento não indica nível atual nem condição de segurança. Não representa velocidade da água ou chegada da cheia. Movimento ilustrativo em direção à foz; não representa a corrente real, que pode variar com a maré. Trechos sem orientação definida ficam parados.</p>
          {movimentoReduzido && <p className={estilos.legendaNota}>Movimento reduzido ativado nas preferências do dispositivo.</p>}
          {listaDaLegenda}
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
            são de estuário, onde a maré pode alterar a corrente. O metro aparece no pino; a cor, não.
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
        </div>
          {/* A ATRIBUIÇÃO É CONDIÇÃO DE LICENÇA, não cortesia: fica visível
              enquanto a camada estiver ativa, e troca junto com ela. */}
          <p className={estilos.atribuicao} data-tapa-mapa>{FUNDOS[fundo].atribuicao}</p>
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
                    {g.medidoEm ? <> · {textoIdade(idadeMin(g.medidoEm, agora))} · medida em {dataHora(g.medidoEm)}</> : null}
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
                        {rotuloCota(k)}: {metros(v)}
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
        {!municipal && !reguaSel && (sel ?? hover) ? (() => {
          const foco = (sel ?? hover)!
          const cid = foco.cidade
          const cotas = cotasOrdenadas(cid.cotas_m ?? {})
          const brutoSc = cid.id === 'ascurra' ? null : nivelSc.get(cid.id) ?? null
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
          // De onde veio a cor (auditoria das cidades sem cor, 06/10/2026): os textos de cota, de
          // cinza e do nível estadual dependem disso, e eram fixos — e se contradiziam.
          const variasReguas = foco.nivel == null && (daCidade.length > 1 || reguasRef.current.filter((r) => r.cidade === cid.id).length > 1)
          const origemDaCor = variasReguas ? 'varias' : foco.origemFaixa === 'estadual' ? 'estadual' : 'municipal'
          const textos = textosDoFoco(foco)
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
              {celular ? (() => {
                // VERSÃO COMPACTA (celular): o que a pessoa quer ao tocar no pino — nível, hora e tendência —
                // e, expandido, chuva e cota antes do painel inteiro. Só textos de dados reais
                // (`logica/painelCompacto`): sem faixa não se escreve faixa; sem tendência, diz-se.
                // A hora que acompanha o número mostrado: a municipal; sem ela, a estadual (dita como tal);
                // em cidade de várias réguas não há uma hora só.
                const estadoLeitura = variasReguas
                  ? LEITURA_VARIAS_REGUAS
                  : foco.nivel != null || !brutoSc
                    ? estadoDaLeitura(foco.medidoEm, agora, cid.id)
                    : estadoDaLeitura(brutoSc.medidoEm, agora, cid.id, 'Leitura estadual')
                const tend = textoTendenciaCompacta(
                  foco.nivel != null ? tendenciaDaLeitura(serieDaCidade(serie, foco.rioId, cid.id), { nivel_m: foco.nivel, medidoEm: foco.medidoEm }, agora) : null,
                )
                const chuva = chuvaMonitor(tempoReal.chuva, cid.id)
                const chuvaIdade = chuva?.medidoEm ? idadeMin(chuva.medidoEm, agora) : null
                const chuvaVale = chuvaIdade != null && frescor(chuvaIdade) !== 'velha' && chuva?.mm.h24 != null
                const cota = cotaDaFaixa(cid, foco.faixa, origemDaCor)
                return (
                  <div className={estilos.compacto}>
                    <div className={estilos.chipFaixa} data-faixa={foco.faixa}>
                      <span className={estilos.amostra} style={{ background: `var(${VAR_LEGENDA[foco.faixa]})` }} />
                      {textos.faixa}
                    </div>
                    <p className={`${estilos.pilulaLeitura} ${estilos[`leitura-${estadoLeitura.tipo}`] ?? ''}`} role="status">{estadoLeitura.texto}</p>
                    <div className={estilos.tiles}>
                      <div className={estilos.tile}>
                        <small>Nível do rio</small>
                        {foco.nivel != null ? (
                          <>
                            <strong>{metros(foco.nivel)}</strong>
                            <small>{foco.medidoEm ? textoIdade(idadeMin(foco.medidoEm, agora)) : 'sem horário'}</small>
                          </>
                        ) : brutoSc ? (
                          <>
                            <strong>{metros(brutoSc.nivelBrutoM)}</strong>
                            <small>rede estadual, zero próprio{brutoSc.medidoEm ? ` · ${textoIdade(idadeMin(brutoSc.medidoEm, agora))}` : ''}</small>
                          </>
                        ) : variasReguas ? (
                          <>
                            <strong>{daCidade.length} réguas</strong>
                            <small>zeros diferentes; cada uma em Mais detalhes</small>
                          </>
                        ) : (
                          <>
                            <strong className={estilos.painelSemDado}>sem leitura</strong>
                            <small>nenhuma medição fresca nesta régua</small>
                          </>
                        )}
                      </div>
                      <div className={estilos.tile}>
                        <small>Tendência</small>
                        <strong><span aria-hidden="true">{tend.seta}</span> {tend.texto}</strong>
                        <small>{tend.nota}</small>
                      </div>
                    </div>
                    {painelExpandido ? (
                      <>
                        <div className={estilos.tiles}>
                          <div className={estilos.tile}>
                            <small>Chuva (24 h)</small>
                            {chuvaVale && chuva ? (
                              <>
                                <strong>{mmChuva(chuva.mm.h24)} mm</strong>
                                <small>{chuva.estacao} · {textoIdade(chuvaIdade!)}</small>
                              </>
                            ) : (
                              <>
                                <strong>—</strong>
                                <small>{chuva?.medidoEm ? 'última medição antiga; não vale como chuva de agora' : 'sem pluviômetro com leitura'}</small>
                              </>
                            )}
                          </div>
                          <div className={estilos.tile}>
                            <small>{cota.titulo}</small>
                            <strong>{cota.valor ?? '—'}</strong>
                            <small>{cota.nota}</small>
                          </div>
                        </div>
                        <div className={estilos.botoesPainel}>
                          <button type="button" onClick={() => navigate(`${rotaDoRio(foco.rioId)}/${cid.id}?aba=historico`)}>Ver histórico</button>
                          <button type="button" onClick={() => navigate(`${rotaDoRio(foco.rioId)}/${cid.id}?aba=fontes`)}>Detalhes da fonte</button>
                        </div>
                      </>
                    ) : null}
                    <button
                      type="button"
                      className={estilos.botaoMais}
                      aria-expanded={painelExpandido}
                      onClick={() => setPainelExpandido((v) => !v)}
                    >
                      {painelExpandido ? 'Menos detalhes ▴' : 'Mais detalhes ▾'}
                    </button>
                  </div>
                )
              })() : null}
              {!celular || painelExpandido ? (<>
              {cid.id === 'ascurra' && <p>Fonte: DCSC-00003 · Ponte do Beber. Enquadramento calculado conforme C18; não é boletim oficial nem área alagada.</p>}
              {cid.id === 'gaspar' && <p>Faixa calculada somente pelo nível, conforme a <a href="https://defesacivil.gaspar.sc.gov.br/estacao/ver/21" target="_blank" rel="noreferrer">legenda da estação 21</a>: normal abaixo de 5 m, atenção acima de 5 m, emergência acima de 7 m. Em 5 m exatos, inclusão não definida. O estado oficial também considera chuva; a cor não indica ruas alagadas.</p>}
              {/* No celular a faixa e o nível já estão no bloco compacto (chip e quadro): estas linhas não
                  entram no DOM — escondê-las por CSS deixaria o número duas vezes na página. */}
              {!celular ? (
              <div className={estilos.painelFaixa}>
                <span
                  className={estilos.amostra}
                  style={{ background: `var(${VAR_LEGENDA[foco.faixa]})` }}
                />
                {textos.faixa}
              </div>
              ) : null}
              {textos.motivoCinza && (
                <p className={estilos.painelRessalva}>
                  <strong>Por que está cinza?</strong>{' '}
                  {textos.motivoCinza}
                </p>
              )}
              {textos.origemDaCor && <p className={estilos.painelRessalva}>{textos.origemDaCor}</p>}
              {!celular ? (
              <p className={estilos.painelNivel}>
                {foco.nivel != null ? (
                  <>
                    <strong>{metros(foco.nivel)}</strong>
                    {/* A hora da medição SEMPRE por extenso (correção 5 da maquete, 07/10/2026) — e a leitura
                        velha é HISTÓRICA, dita como tal, para não passar por atual (Gaspar parado às 16:50,
                        auditoria de 06/10/2026). */}
                    {foco.medidoEm ? <> · {textoIdade(idadeMin(foco.medidoEm, agora))} · medida em {dataHora(foco.medidoEm)}</> : null}
                    {foco.medidoEm && frescor(idadeMin(foco.medidoEm, agora)) === 'velha' ? <> <span className={estilos.painelSemDado}>(leitura antiga, não é a de agora)</span></> : null}
                  </>
                ) : daCidade.length > 1 || brutoSc ? null : (
                  <span className={estilos.painelSemDado}>sem leitura fresca</span>
                )}
              </p>
              ) : null}
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
              {/* De onde vem o ponto do pino: estação, posição aproximada ou cidade de várias réguas
                  (auditoria de 06/10/2026; ver `logica/posicaoDoPino.ts`). */}
              <p className={estilos.painelRessalva}>
                {textos.posicao}
              </p>
              {textos.equivalencia ? (
                <p className={estilos.painelRessalva}>{textos.equivalencia}</p>
              ) : null}
              {cotas.length > 0 ? (
                <div className={estilos.painelBloco}>
                  <span className={estilos.painelRotulo}>{cid.id === 'indaial' ? 'Cotas municipais — régua dos fundos da Celesc' : 'Cotas da régua'}</span>
                  <ul>
                    {cotas.map(([k, v]) => (
                      <li key={k}>
                        {rotuloCota(k, cid.cotas_nomes_na_fonte)}: {metros(v)}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className={estilos.painelSemCota}>
                  {textoSemCota(origemDaCor)}
                </p>
              )}
              {brutoSc ? (
                <div className={estilos.painelBloco}>
                  <span className={estilos.painelRotulo}>Nível bruto — rede estadual (DCSC)</span>
                  {cid.id === 'indaial' && <p>SDC-SC Indaial · DCSC-00006 · terceira ponte. Esta é a régua do monitoramento estadual.</p>}
                  <p className={estilos.painelExtra}>
                    <strong>{metros(brutoSc.nivelBrutoM)}</strong>
                    {brutoSc.medidoEm ? <> · {textoIdade(idadeMin(brutoSc.medidoEm, agora))}</> : null}
                    {' — '}
                    {brutoSc.estacao}
                  </p>
                  {brutoSc.faixaEstadual && brutoSc.medidoEm && frescor(idadeMin(brutoSc.medidoEm, agora)) !== 'velha' ? (
                    <p className={estilos.painelExtra}>
                      <strong>Classificação da Defesa Civil de SC: {NOME_FAIXA_ESTADUAL[brutoSc.faixaEstadual]}</strong>
                      {' — '}faixa declarada pela própria rede estadual, no datum desta estação. {foco.origemFaixa === 'estadual' ? 'É a classificação estadual do pino; não é comparação com as cotas municipais e não aciona aviso.' : 'Não é a faixa de cor deste pino e não aciona aviso.'}
                    </p>
                  ) : null}
                  {brutoSc.codigo && <a href={`https://monitoramento.defesacivil.sc.gov.br/estacao/${brutoSc.codigo}`} target="_blank" rel="noreferrer">Consultar estação na Defesa Civil de SC</a>}
                  {cid.id === 'indaial' && <p>As cotas municipais de 3 / 4 / 5,5 m são da régua dos fundos da Celesc, indicada no <a href="https://docs.google.com/document/d/1EN1iEU3lDUfRnOtPx6IjeSpoO7DMGd-iD4i2AdHiFvk/edit" target="_blank" rel="noreferrer">documento de acompanhamento de Indaial</a>. Não são aplicadas à leitura da terceira ponte.</p>}
                  <p className={estilos.painelRessalva}>
                    {ressalvaDoBruto(cotas.length > 0, foco.origemFaixa === 'estadual', estacaoEhReguaDasCotas(cid.id, brutoSc.codigo))}
                  </p>
                </div>
              ) : null}
              <div className={estilos.painelChuva}>
                <ChuvaMonitor cidades={[cid]} chuva={tempoReal.chuva} agora={agora} situacao={original.situacao} chuvaOk={original.chuvaOk} />
              </div>
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
                  <span className={estilos.painelRotulo}>Resumo da série nesta régua</span>
                  <p className={estilos.painelRessalva}>
                    Até {dataHora(ultimas.resumo.ate)} · {textoIdade(idadeMin(ultimas.resumo.ate, agora))}.
                    {frescorDaCidade(idadeMin(ultimas.resumo.ate, agora), cid.id) === 'velha'
                      ? ' Série parada: a variação abaixo descreve o período até essa leitura, não o rio agora.'
                      : null}
                  </p>
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
              <p className={estilos.painelAcao}>{foco.origemFaixa === 'estadual'
                ? 'Sem leitura municipal compatível para comparar com as cotas locais. A classificação acima é a publicada pela Defesa Civil de SC; não informa quais ruas estão alagadas.'
                : ACAO_FAIXA[foco.faixa]}</p>
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
              {cid.id === 'ituporanga' && (
                <button type="button" className={estilos.dicaDetalhe}
                  onClick={() => navigate('/acu/ituporanga?camadas=inundacao')}>
                  Ver áreas de inundação →
                </button>
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
              </>) : null}
            </div>
          )
        })() : null}
        {celular && !municipal && !ampliado && abaCelular === 'reguas' ? (
          <ReguasDoMonitor aoEscolher={() => setAbaCelular('mapa')} />
        ) : null}
      </div>

      {/* BARRA DE BAIXO (celular, etapa 3): Mapa · Réguas · Perguntar. Fica no fluxo da página, logo abaixo do
          mapa — nunca `position: fixed` —, e o mapa já desconta a altura dela (CSS e baseline da trava).
          É do Monitor e não a barra de navegação do site (`nav[aria-label="Principal"]`), que continua fora. */}
      {celular && !municipal && !ampliado ? (
        <nav className={estilos.barraModos} aria-label="Modos do Monitor">
          <button
            type="button"
            className={estilos.modo}
            aria-pressed={abaCelular === 'mapa' && !chatAberto && !focoNoChat}
            onClick={() => setAbaCelular('mapa')}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2Zm0 2.2 6 2v11.6l-6-2V6.2Z" /></svg>
            Mapa
          </button>
          <button
            type="button"
            className={estilos.modo}
            aria-pressed={abaCelular === 'reguas'}
            onClick={() => setAbaCelular((a) => (a === 'reguas' ? 'mapa' : 'reguas'))}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 16.6 16.6 3 21 7.4 7.4 21 3 16.6Zm2.8 0 1.6 1.6 1.1-1.1-.9-.9.9-.9.9.9 1.2-1.2-1.6-1.6.9-.9 1.6 1.6 1.2-1.2-.9-.9.9-.9.9.9 1.2-1.2-1.6-1.6.9-.9 1.6 1.6 1.1-1.1-1.6-1.6L5.8 16.6Z" /></svg>
            Réguas
          </button>
          <button
            type="button"
            className={estilos.modo}
            aria-pressed={chatAberto || focoNoChat}
            onClick={() => {
              setAbaCelular('mapa')
              const caixa = divRef.current?.querySelector<HTMLInputElement>('input[aria-label="Pergunte ou peça"]')
              caixa?.focus()
            }}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h16a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H9l-5 4v-4H4a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Zm1 2v9h1v2l2.5-2H19V6H5Z" /></svg>
            Perguntar
          </button>
        </nav>
      ) : null}

      {/* A árvore da bacia, embaixo do mapa: quem vê os pinos precisa saber
          QUEM ESTÁ ACIMA DE QUEM, e que a barragem não é o rio da cidade. */}
      {!municipal && <ArvoreDaBacia />}

      {/* Acesso por teclado/leitor: as cidades viram botões fora da vista. */}
      <ul className={estilos.foraDaVista}>
        {cidadesBacia
          .filter((c) => c.coordenadas)
          .map((c) => (
            <li key={c.id}>
              <button type="button" onClick={() => {
                const p = cenaRef.current?.pinos.find(p => p.cidade.id === c.id)
                if (p && !municipal) navigate(`/monitor/${c.id}`)
              }}>
                {c.nome}
              </button>
            </li>
          ))}
      </ul>
    </div>
  )
}
