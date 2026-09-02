/**
 * Nível BRUTO da rede estadual (Defesa Civil de SC), publicado em
 * `ultimo_nivel_sc.json` no branch `tempo-real`, ao lado do `ultimo.json`.
 *
 * É nível de régua PRÓPRIA da estação — datum diferente das cotas do projeto.
 * Por isso NUNCA vira cota nem pinta faixa: só preenche, rotulado, a lacuna das
 * cidades sem fonte municipal (Ibirama, Indaial, Taió…). Quem decide usá-lo é a
 * tela, e só quando não há leitura municipal (a municipal manda). Espelha a
 * disciplina do coletor `coleta_nivel_sc.py` e do bot.
 *
 * Falhar aqui é inofensivo: sem o arquivo (ou com ele quebrado), o mapa fica
 * vazio e a tela volta a mostrar "sem dado" nas lacunas — nunca um número
 * inventado.
 */
import { useEffect, useState } from 'react'
import { deBrasilia } from '../logica/tempoReal'

const PADRAO =
  'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/ultimo_nivel_sc.json'

/** Dá para apontar para outra fonte sem recompilar, via .env do Vite. */
export const URL_NIVEL_SC = import.meta.env?.VITE_URL_NIVEL_SC || PADRAO

const TEMPO_LIMITE_MS = 8000
const RE_SEM_FUSO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$/

export interface BrutoEstadual {
  cidade: string
  estacao: string
  nivelBrutoM: number
  /** Instante da medição, em hora de Brasília. Null quando a fonte não o publicou. */
  medidoEm: Date | null
}

/** Uma leitura bruta por cidade (a mais fresca). Só para EXIBIR, nunca cota. */
export type NivelSc = Map<string, BrutoEstadual>

function brutoValido(bruta: unknown): BrutoEstadual | null {
  if (typeof bruta !== 'object' || bruta === null) return null
  const l = bruta as Record<string, unknown>
  if (typeof l.cidade !== 'string' || l.cidade.trim() === '') return null
  if (typeof l.estacao !== 'string' || l.estacao.trim() === '') return null
  const nivel = typeof l.nivel_bruto_m === 'number' ? l.nivel_bruto_m : Number.NaN
  // Nenhuma régua de rio da bacia passa de 30 m; fora disso é altitude/defeito.
  if (!Number.isFinite(nivel) || nivel <= 0 || nivel >= 30) return null

  let medidoEm: Date | null = null
  if (typeof l.medido_em === 'string' && RE_SEM_FUSO.test(l.medido_em)) {
    const d = deBrasilia(l.medido_em)
    medidoEm = Number.isNaN(d.getTime()) ? null : d
  }
  return { cidade: l.cidade, estacao: l.estacao, nivelBrutoM: nivel, medidoEm }
}

/** Constrói o mapa cidade → bruto mais fresco a partir do JSON cru. */
export function montarNivelSc(corpo: unknown): NivelSc {
  const mapa: NivelSc = new Map()
  if (typeof corpo !== 'object' || corpo === null) return mapa
  const leituras = (corpo as Record<string, unknown>).leituras
  if (!Array.isArray(leituras)) return mapa
  for (const bruta of leituras) {
    const l = brutoValido(bruta)
    if (!l) continue
    const atual = mapa.get(l.cidade)
    // Mais fresca vence; sem carimbo perde para quem tem.
    const ta = atual?.medidoEm?.getTime() ?? Number.NEGATIVE_INFINITY
    const tn = l.medidoEm?.getTime() ?? Number.NEGATIVE_INFINITY
    if (!atual || tn > ta) mapa.set(l.cidade, l)
  }
  return mapa
}

/** O `fetch`, injetável para o teste rodar sem rede. */
export type Transporte = (url: string, init: RequestInit) => Promise<Response>

export async function buscarNivelSc(
  sinal?: AbortSignal,
  transporte: Transporte = (url, init) => fetch(url, init),
): Promise<NivelSc> {
  try {
    const resposta = await transporte(URL_NIVEL_SC, { cache: 'no-store', signal: sinal })
    if (!resposta.ok) return new Map()
    return montarNivelSc(await resposta.json())
  } catch {
    return new Map()
  }
}

/** Busca ao abrir a página e a cada `intervaloMin`. Falha vira mapa vazio. */
export function useNivelSc(intervaloMin = 5): NivelSc {
  const [mapa, setMapa] = useState<NivelSc>(new Map())

  useEffect(() => {
    let vivo = true
    const emVoo = new Set<AbortController>()

    const buscar = async () => {
      const controle = new AbortController()
      emVoo.add(controle)
      const limite = setTimeout(() => controle.abort(), TEMPO_LIMITE_MS)
      try {
        const novo = await buscarNivelSc(controle.signal)
        if (vivo) setMapa(novo)
      } finally {
        clearTimeout(limite)
        emVoo.delete(controle)
      }
    }

    void buscar()
    const relogio = setInterval(() => void buscar(), intervaloMin * 60_000)
    return () => {
      vivo = false
      clearInterval(relogio)
      for (const c of emVoo) c.abort()
    }
  }, [intervaloMin])

  return mapa
}
