/**
 * Busca a última leitura de nível publicada, em tempo de execução.
 *
 * Por que não vem do build: o site é estático, e um número embutido no pacote
 * tem a idade do último deploy. Numa cheia isso é inútil — e pior que inútil,
 * porque parece atual. A leitura é buscada quando a página abre.
 *
 * De onde vem: `scripts/coleta_niveis.py` grava `data/tempo-real/ultimo.json`
 * na máquina que coleta, e `scripts/publicar_tempo_real.sh` publica esse
 * arquivo no branch `tempo-real` do repositório. O `raw.githubusercontent.com`
 * serve com CORS aberto, então a página busca direto de lá, sem servidor
 * próprio no meio.
 *
 * Falhar aqui é normal e previsto: sem rede, sem coleta rodando ou com o
 * branch ainda inexistente, a tela simplesmente não mostra nível ao vivo. Ela
 * nunca inventa um.
 */
import { useEffect, useState } from 'react'
import { deBrasilia } from '../logica/tempoReal'

const PADRAO =
  'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/ultimo.json'

/** Dá para apontar para outra fonte sem recompilar o código, via .env do Vite. */
export const URL_TEMPO_REAL = import.meta.env.VITE_URL_TEMPO_REAL || PADRAO

/** Depois disso a página desiste: melhor sem número que travada esperando. */
const TEMPO_LIMITE_MS = 8000

export interface LeituraAoVivo {
  estacao: string
  rio: string | null
  cidade: string | null
  nivel_m: number
  /** Instante da medição. Null quando a fonte não publicou o horário. */
  medidoEm: Date | null
}

/** Janelas de acumulado publicadas pela fonte. Ela NÃO publica 6 h. */
export interface MilimetrosPorJanela {
  min10: number | null
  h1: number | null
  h12: number | null
  h24: number | null
  h48: number | null
}

export interface ChuvaAoVivo {
  estacao: string
  rio: string | null
  cidade: string | null
  mm: MilimetrosPorJanela
  medidoEm: Date | null
  /**
   * As janelas são encaixadas, então o acumulado tem de ser não-decrescente.
   * Quando a fonte publica série que não fecha — e ela publica —, isto vem
   * `false` e a tela mostra o problema em vez do número.
   */
  coerente: boolean
  incoerencias: string[]
}

export interface EstadoTempoReal {
  situacao: 'carregando' | 'ok' | 'indisponivel'
  leituras: LeituraAoVivo[]
  chuva: ChuvaAoVivo[]
  /** Quando a coleta rodou (não é quando o rio foi medido). */
  coletadoEm: Date | null
  fonte: string | null
}

const RE_SEM_FUSO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$/

function leituraValida(bruta: unknown): LeituraAoVivo | null {
  if (typeof bruta !== 'object' || bruta === null) return null
  const l = bruta as Record<string, unknown>

  const nivel = typeof l.nivel_m === 'number' ? l.nivel_m : Number.NaN
  // Nenhuma régua da bacia chega perto de 25 m; fora disso não é nível de rio.
  if (!Number.isFinite(nivel) || nivel <= 0 || nivel >= 25) return null
  if (typeof l.estacao !== 'string' || l.estacao.trim() === '') return null

  let medidoEm: Date | null = null
  if (typeof l.medido_em === 'string' && RE_SEM_FUSO.test(l.medido_em)) {
    const d = deBrasilia(l.medido_em)
    medidoEm = Number.isNaN(d.getTime()) ? null : d
  }

  return {
    estacao: l.estacao,
    rio: typeof l.rio === 'string' ? l.rio : null,
    cidade: typeof l.cidade === 'string' ? l.cidade : null,
    nivel_m: nivel,
    medidoEm,
  }
}

const JANELAS = ['min10', 'h1', 'h12', 'h24', 'h48'] as const

function mm(bruto: unknown): number | null {
  if (typeof bruto !== 'number' || !Number.isFinite(bruto)) return null
  // Chuva negativa não existe. O recorde brasileiro em 24 h fica bem abaixo de
  // 1000 mm; acima disso é defeito de sensor, não temporal.
  if (bruto < 0 || bruto > 1000) return null
  return bruto
}

function chuvaValida(bruta: unknown): ChuvaAoVivo | null {
  if (typeof bruta !== 'object' || bruta === null) return null
  const c = bruta as Record<string, unknown>
  if (typeof c.estacao !== 'string' || c.estacao.trim() === '') return null

  const cru = (typeof c.mm === 'object' && c.mm !== null ? c.mm : {}) as Record<string, unknown>
  const valores = Object.fromEntries(
    JANELAS.map((j) => [j, mm(cru[j])]),
  ) as unknown as MilimetrosPorJanela
  if (JANELAS.every((j) => valores[j] === null)) return null

  let medidoEm: Date | null = null
  if (typeof c.medido_em === 'string' && RE_SEM_FUSO.test(c.medido_em)) {
    const d = deBrasilia(c.medido_em)
    medidoEm = Number.isNaN(d.getTime()) ? null : d
  }

  const incoerencias = Array.isArray(c.incoerencias)
    ? c.incoerencias.filter((i): i is string => typeof i === 'string')
    : []

  return {
    estacao: c.estacao,
    rio: typeof c.rio === 'string' ? c.rio : null,
    cidade: typeof c.cidade === 'string' ? c.cidade : null,
    mm: valores,
    medidoEm,
    // Ausência do campo NÃO vale como "coerente": só o `true` explícito vale.
    coerente: c.coerente === true && incoerencias.length === 0,
    incoerencias,
  }
}

export async function buscarTempoReal(sinal?: AbortSignal): Promise<EstadoTempoReal> {
  const vazio: EstadoTempoReal = {
    situacao: 'indisponivel',
    leituras: [],
    chuva: [],
    coletadoEm: null,
    fonte: null,
  }

  try {
    const resposta = await fetch(URL_TEMPO_REAL, { cache: 'no-store', signal: sinal })
    if (!resposta.ok) return vazio
    const corpo: unknown = await resposta.json()
    if (typeof corpo !== 'object' || corpo === null) return vazio

    const dados = corpo as Record<string, unknown>
    const leituras = Array.isArray(dados.leituras)
      ? dados.leituras.map(leituraValida).filter((l): l is LeituraAoVivo => l !== null)
      : []
    if (leituras.length === 0) return vazio

    const coletado =
      typeof dados.coletado_em === 'string' ? new Date(dados.coletado_em) : null

    const chuva = Array.isArray(dados.chuva)
      ? dados.chuva.map(chuvaValida).filter((c): c is ChuvaAoVivo => c !== null)
      : []

    return {
      situacao: 'ok',
      leituras,
      chuva,
      coletadoEm: coletado && !Number.isNaN(coletado.getTime()) ? coletado : null,
      fonte: typeof dados.fonte === 'string' ? dados.fonte : null,
    }
  } catch {
    // Rede fora, CORS, JSON quebrado: a tela segue sem nível ao vivo.
    return vazio
  }
}

/** Busca uma vez ao abrir a página, e a cada `intervaloMin` enquanto ela ficar aberta. */
export function useTempoReal(intervaloMin = 5): EstadoTempoReal {
  const [estado, setEstado] = useState<EstadoTempoReal>({
    situacao: 'carregando',
    leituras: [],
    chuva: [],
    coletadoEm: null,
    fonte: null,
  })

  useEffect(() => {
    let vivo = true
    const controle = new AbortController()
    const limite = setTimeout(() => controle.abort(), TEMPO_LIMITE_MS)

    const buscar = async () => {
      const novo = await buscarTempoReal(controle.signal)
      if (vivo) setEstado(novo)
    }

    void buscar()
    const relogio = setInterval(() => void buscar(), intervaloMin * 60_000)

    return () => {
      vivo = false
      clearTimeout(limite)
      clearInterval(relogio)
      controle.abort()
    }
  }, [intervaloMin])

  return estado
}

/** A leitura mais recente de uma cidade, na régua de um rio. */
export function leituraDaCidade(
  estado: EstadoTempoReal,
  rioId: string,
  cidadeId: string,
): LeituraAoVivo | null {
  const candidatas = estado.leituras.filter((l) => l.rio === rioId && l.cidade === cidadeId)
  if (candidatas.length === 0) return null
  // Cidade com mais de uma régua: não dá para escolher uma como "o nível da
  // cidade" — os zeros são diferentes. Melhor não mostrar nenhuma.
  if (candidatas.length > 1) return null
  return candidatas[0]!
}
