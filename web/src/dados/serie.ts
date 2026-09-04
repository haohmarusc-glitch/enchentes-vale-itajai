/**
 * Busca a série das últimas horas de nível, publicada em tempo de execução.
 *
 * Irmã de `tempoReal.ts`: o `ultimo.json` é um instante; este é a linha do
 * tempo. Vem do mesmo branch `tempo-real`, no arquivo `serie-recente.json` que
 * `scripts/coleta_niveis.py` monta e `publicar_tempo_real.sh` publica —
 * `raw.githubusercontent.com` serve com CORS aberto.
 *
 * `medido_em` é hora de Brasília SEM fuso, igual ao resto do projeto, e é lido
 * com `deBrasilia()` — nada de converter em outro lugar. Falhar aqui é normal:
 * sem o arquivo (coleta antiga, série ainda vazia), a tela não mostra a linha
 * do tempo, e nunca inventa uma.
 */
import { useEffect, useState } from 'react'
import { deBrasilia } from '../logica/tempoReal'

const PADRAO =
  'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/serie-recente.json'

export const URL_SERIE = import.meta.env?.VITE_URL_SERIE || PADRAO

const TEMPO_LIMITE_MS = 8000

export interface PontoSerie {
  /** Instante da medição (Brasília, já resolvido para o momento real). */
  medidoEm: Date
  nivel_m: number
  /**
   * A RÉGUA de onde este ponto veio, ou `null` quando a fonte não disse.
   *
   * Existe porque uma cidade pode ter várias réguas com ZEROS DIFERENTES —
   * Itajaí tem onze —, e sem isto a série da cidade sai com todas
   * intercaladas. Ver o comentário de `tendencia`. Primária e resgate contam
   * como UMA régua: o publicador já resolve isso por `resgate_de`.
   */
  regua: string | null
}

export type SituacaoSerie = 'carregando' | 'ok' | 'indisponivel'

export interface EstadoSerie {
  situacao: SituacaoSerie
  /** rio -> cidade -> pontos ordenados no tempo. */
  series: Record<string, Record<string, PontoSerie[]>>
  janelaHoras: number | null
  geradoEm: Date | null
}

const VAZIO: EstadoSerie = {
  situacao: 'indisponivel',
  series: {},
  janelaHoras: null,
  geradoEm: null,
}

function pontoValido(bruto: unknown, legenda: string[]): PontoSerie | null {
  if (typeof bruto !== 'object' || bruto === null) return null
  const d = bruto as Record<string, unknown>
  if (typeof d.medido_em !== 'string') return null
  if (typeof d.nivel_m !== 'number' || Number.isNaN(d.nivel_m)) return null
  const medidoEm = deBrasilia(d.medido_em)
  if (Number.isNaN(medidoEm.getTime())) return null
  // `r` é índice na legenda `reguas[rio][cidade]`. Fora da legenda ou ausente
  // vira `null` — "não sei de que régua veio" —, nunca a primeira da lista:
  // chutar seria afirmar um zero de medição.
  const r = typeof d.r === 'number' ? legenda[d.r] : undefined
  return { medidoEm, nivel_m: d.nivel_m, regua: r ?? null }
}

export type Transporte = (url: string, init: RequestInit) => Promise<Response>

export async function buscarSerie(
  sinal?: AbortSignal,
  transporte: Transporte = (url, init) => fetch(url, init),
): Promise<EstadoSerie> {
  try {
    const resposta = await transporte(URL_SERIE, { cache: 'no-store', signal: sinal })
    if (!resposta.ok) return VAZIO
    const corpo: unknown = await resposta.json()
    if (typeof corpo !== 'object' || corpo === null) return VAZIO
    const dados = corpo as Record<string, unknown>
    const brutoSeries = dados.series
    if (typeof brutoSeries !== 'object' || brutoSeries === null) return VAZIO

    const brutoReguas = (dados.reguas ?? {}) as Record<string, unknown>
    const legendaDe = (rio: string, cidade: string): string[] => {
      const porCidade = brutoReguas[rio]
      if (typeof porCidade !== 'object' || porCidade === null) return []
      const lista = (porCidade as Record<string, unknown>)[cidade]
      return Array.isArray(lista) ? lista.filter((x): x is string => typeof x === 'string') : []
    }

    const series: Record<string, Record<string, PontoSerie[]>> = {}
    for (const [rio, porCidade] of Object.entries(brutoSeries as Record<string, unknown>)) {
      if (typeof porCidade !== 'object' || porCidade === null) continue
      for (const [cidade, pontos] of Object.entries(porCidade as Record<string, unknown>)) {
        if (!Array.isArray(pontos)) continue
        const legenda = legendaDe(rio, cidade)
        const validos = pontos
          .map((p) => pontoValido(p, legenda))
          .filter((p): p is PontoSerie => p !== null)
          .sort((a, b) => a.medidoEm.getTime() - b.medidoEm.getTime())
        if (validos.length > 0) {
          ;(series[rio] ??= {})[cidade] = validos
        }
      }
    }

    const gerado =
      typeof dados.gerado_em === 'string' ? new Date(dados.gerado_em) : null
    return {
      situacao: 'ok',
      series,
      janelaHoras: typeof dados.janela_horas === 'number' ? dados.janela_horas : null,
      geradoEm: gerado && !Number.isNaN(gerado.getTime()) ? gerado : null,
    }
  } catch {
    return VAZIO
  }
}

export async function buscarSerieComLimite(
  limiteMs: number = TEMPO_LIMITE_MS,
  transporte?: Transporte,
  registrar?: (c: AbortController) => void,
): Promise<EstadoSerie> {
  const controle = new AbortController()
  registrar?.(controle)
  const limite = setTimeout(() => controle.abort(), limiteMs)
  try {
    return await buscarSerie(controle.signal, transporte)
  } finally {
    clearTimeout(limite)
  }
}

/** Busca ao abrir e a cada `intervaloMin` — a série cresce enquanto a chuva cai. */
export function useSerieRecente(intervaloMin = 5): EstadoSerie {
  const [estado, setEstado] = useState<EstadoSerie>({
    situacao: 'carregando',
    series: {},
    janelaHoras: null,
    geradoEm: null,
  })

  useEffect(() => {
    let vivo = true
    const emVoo = new Set<AbortController>()
    const buscar = async () => {
      let meu: AbortController | null = null
      const novo = await buscarSerieComLimite(TEMPO_LIMITE_MS, undefined, (c) => {
        meu = c
        emVoo.add(c)
      })
      if (meu) emVoo.delete(meu)
      if (vivo) setEstado(novo)
    }
    void buscar()
    const relogio = setInterval(() => void buscar(), intervaloMin * 60_000)
    return () => {
      vivo = false
      clearInterval(relogio)
      for (const c of emVoo) c.abort()
    }
  }, [intervaloMin])

  return estado
}

/**
 * Os pontos de uma cidade naquele rio, ou lista vazia.
 *
 * ATENÇÃO: numa cidade de VÁRIAS RÉGUAS esta lista vem com todas intercaladas,
 * e réguas diferentes têm zeros diferentes. Para qualquer conta que compare um
 * ponto com outro, use `porRegua` antes. Ver `tendencia`.
 */
export function serieDaCidade(estado: EstadoSerie, rioId: string, cidadeId: string): PontoSerie[] {
  return estado.series[rioId]?.[cidadeId] ?? []
}

/**
 * Separa a série por RÉGUA, preservando a ordem no tempo dentro de cada uma.
 *
 * A chave é o título da régua; pontos sem régua conhecida caem em `''`, e ficam
 * separados de propósito — juntá-los com qualquer régua nomeada seria afirmar
 * um zero de medição que a fonte não disse.
 */
export function porRegua(pontos: PontoSerie[]): Map<string, PontoSerie[]> {
  const saida = new Map<string, PontoSerie[]>()
  for (const p of pontos) {
    const chave = p.regua ?? ''
    const lista = saida.get(chave)
    if (lista) lista.push(p)
    else saida.set(chave, [p])
  }
  return saida
}

/** Quantas réguas distintas há nesta série. 1 = dá para comparar ponto com ponto. */
export function quantasReguas(pontos: PontoSerie[]): number {
  return porRegua(pontos).size
}

/**
 * A última leitura medida ATÉ o instante `t` (ms), ou null. É o que a animação
 * usa para saber a faixa de cada cidade num momento do passado — nunca um valor
 * futuro, que seria adivinhar. Assume `pontos` já ordenado no tempo.
 */
export function leituraEm(pontos: PontoSerie[], t: number): PontoSerie | null {
  let atual: PontoSerie | null = null
  for (const p of pontos) {
    if (p.medidoEm.getTime() <= t) atual = p
    else break
  }
  return atual
}

/** Para onde o rio ia na última hora medida. `cmh` é a taxa em cm/h. */
export type Tendencia = { rotulo: 'subindo' | 'descendo' | 'estável'; cmh: number }

/**
 * A tendência do nível na última hora da série, ou null quando não dá para
 * dizer (menos de dois pontos, ou dois pontos no mesmo instante).
 *
 * Vive aqui, e não dentro do gráfico, porque não serve só para rotular a linha:
 * é o que diz se uma leitura VELHA ainda pode ser lida como aproximação do
 * agora. "5,11 m há 3 h" com o rio subindo 20 cm/h não é o mesmo dado que
 * "5,11 m há 3 h" com o rio parado — o primeiro quer dizer que o rio está mais
 * alto agora, e a tela mostrava os dois igual.
 *
 * O limiar de 2 cm/h separa movimento de ruído de sensor: abaixo disso, dizer
 * "subindo" seria transformar oscilação de leitura em tendência.
 */
export function tendencia(serie: PontoSerie[]): Tendencia | null {
  if (serie.length < 2) return null
  // SÉRIE MISTURADA NÃO TEM TENDÊNCIA. Uma cidade pode ter várias réguas com
  // ZEROS DIFERENTES, e esta função pega o último ponto e o de ~1 h antes: se
  // forem de réguas distintas, a diferença é entre dois ZEROS, não entre dois
  // instantes do rio.
  //
  // Medido na série publicada de 04/09/2026, simulando o site em cada instante
  // da janela de 48 h: em `itajai-mirim/itajai` (cinco réguas), 736 dos 949
  // instantes dariam |cm/h| > 30 e 707 dariam > 100, com pico de +2448 — o site
  // dizendo a quem mora na foz que o rio sobe 24 metros por hora. Em
  // `itajai-acu/itajai` (DC-01, DC-02, DC-11), pico de −13.140.
  //
  // Devolver `null` some com a frase "subindo/descendo" nessas cidades. É o
  // certo: "não sei" é o que sabemos, e o número que estava ali não era o rio.
  // Quem quiser a tendência de UMA régua chama `porRegua` e passa a lista dela.
  if (quantasReguas(serie) > 1) return null
  const ult = serie[serie.length - 1]!
  const alvo = ult.medidoEm.getTime() - 3_600_000 // ~1 h antes
  let ref = serie[0]!
  for (const p of serie) {
    if (p.medidoEm.getTime() <= alvo) ref = p
    else break
  }
  const horas = (ult.medidoEm.getTime() - ref.medidoEm.getTime()) / 3_600_000
  if (horas <= 0) return null
  const cmh = Math.round(((ult.nivel_m - ref.nivel_m) * 100) / horas)
  if (cmh >= 2) return { rotulo: 'subindo', cmh }
  if (cmh <= -2) return { rotulo: 'descendo', cmh }
  return { rotulo: 'estável', cmh }
}
