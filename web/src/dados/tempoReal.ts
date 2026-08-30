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

export interface EstadoTempoReal {
  situacao: 'carregando' | 'ok' | 'indisponivel'
  leituras: LeituraAoVivo[]
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

export async function buscarTempoReal(sinal?: AbortSignal): Promise<EstadoTempoReal> {
  const vazio: EstadoTempoReal = {
    situacao: 'indisponivel',
    leituras: [],
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

    return {
      situacao: 'ok',
      leituras,
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
