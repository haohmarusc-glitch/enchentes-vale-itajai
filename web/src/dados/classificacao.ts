/**
 * A classificação estadual × municipal que o motor Python publica (`ultimo_classificacao.json`).
 *
 * PR 2 de 07/10/2026 (`docs/CLASSIFICACAO-ESTADUAL-MUNICIPAL.md`). O motor (`scripts/classificar_reguas.py`)
 * calcula, para cada cidade do piloto, a classificação MUNICIPAL (cotas na régua da própria leitura, por
 * código) e a ESTADUAL (a faixa que a Defesa Civil de SC publica), e diz qual pinta. O site passa a seguir
 * essa decisão em `estadoDaCidade` — mas só quando ela é desta coleta e viu as MESMAS medições que a tela
 * mostra. Em qualquer outro caso (arquivo ausente, velho, quebrado, de outra publicação ou cidade fora do
 * piloto), vale a regra de sempre do site. O Monitor ainda não lê isto (PR 3).
 *
 * O motor decide identidade de régua e quais faixas valem. A IDADE da leitura o site refaz no relógio do
 * aparelho: o motor rodou na hora da coleta, e "velha" é sobre agora.
 */
import { useEffect, useState } from 'react'
import { deBrasilia, frescorDaCidade, idadeMin, type Faixa } from '../logica/tempoReal'
import { ouvirAtualizacao } from './atualizar'
import { buscarPublicacao } from './publicacao'

const PADRAO =
  'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/ultimo_classificacao.json'

/** Dá para apontar para outra fonte sem recompilar, via .env do Vite. */
export const URL_CLASSIFICACAO = import.meta.env?.VITE_URL_CLASSIFICACAO || PADRAO

/** O motor roda a cada publicação (15 min): mais velho que isto não é desta coleta. Igual ao publicador. */
export const MAX_IDADE_CLASSIFICACAO_MIN = 30

const TEMPO_LIMITE_MS = 8000
const RE_SEM_FUSO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$/
const FAIXAS_MUNICIPAIS = ['normal', 'monitoramento', 'atencao', 'alerta', 'emergencia', 'inundacao'] as const
const FAIXAS_ESTADUAIS = ['normal', 'atencao', 'alerta', 'emergencia'] as const

export interface ClassificacaoMunicipal {
  reguaId: string | null
  /** A faixa pelas cotas da cidade, null quando não classificou (o motivo vem junto). */
  faixa: Faixa | null
  medidoEm: Date | null
  /** Havia leitura municipal com carimbo e não velha NA HORA DA COLETA. */
  deAgora: boolean
  /**
   * A leitura municipal de agora segura a estadual — só com as cotas da cidade confirmadas. Com cotas não
   * confirmadas (Rio dos Cedros, decisão de 07/10/2026), a municipal não diz faixa e a estadual válida aparece.
   * Arquivo de antes do campo: vale `deAgora`, a regra de então.
   */
  seguraEstadual: boolean
  /** `status_faixas` do motor: as cotas da cidade estão confirmadas. */
  cotasConfirmadas: boolean
  variasReguas: boolean
  rotulo: string
  motivo: string | null
}

export interface ClassificacaoEstadual {
  reguaId: string | null
  faixa: Faixa | null
  medidoEm: Date | null
  rotulo: string
  aviso: string
  motivo: string | null
}

export interface ClassificacaoDaCidade {
  rio: string
  municipal: ClassificacaoMunicipal
  estadual: ClassificacaoEstadual
}

export interface EstadoClassificacao {
  geradoEm: Date
  /** Chave: id da cidade (o piloto só tem cidades de um rio só). */
  cidades: Map<string, ClassificacaoDaCidade>
}

function texto(v: unknown): string | null {
  return typeof v === 'string' && v.trim() !== '' ? v : null
}

function hora(v: unknown): Date | null {
  if (typeof v !== 'string' || !RE_SEM_FUSO.test(v)) return null
  const d = deBrasilia(v)
  return Number.isNaN(d.getTime()) ? null : d
}

function faixaEntre<T extends string>(v: unknown, vocabulario: readonly T[]): T | null | undefined {
  if (v === null) return null
  return vocabulario.find((f) => f === v)
}

function cidadeValida(bruta: unknown): ClassificacaoDaCidade | null {
  if (typeof bruta !== 'object' || bruta === null) return null
  const c = bruta as Record<string, unknown>
  const cls = (typeof c.classificacoes === 'object' && c.classificacoes !== null ? c.classificacoes : {}) as Record<string, unknown>
  const m = (cls.municipal ?? {}) as Record<string, unknown>
  const e = (cls.estadual ?? {}) as Record<string, unknown>
  const rio = texto(c.rio)
  if (!rio || m.tipo !== 'municipal' || e.tipo !== 'estadual') return null

  const faixaM = faixaEntre(m.faixa, FAIXAS_MUNICIPAIS)
  const faixaE = faixaEntre(e.faixa, FAIXAS_ESTADUAIS)
  // Faixa fora do vocabulário é arquivo que este site não entende: a cidade volta para a regra de sempre.
  if (faixaM === undefined || faixaE === undefined) return null
  const medidoM = hora(m.medido_em)
  const medidoE = hora(e.medido_em)
  // Defesa em profundidade: o motor já recusa isto, mas cor sem carimbo ou de outra régua não passa aqui.
  if (faixaM && (!medidoM || !texto(m.regua_id) || m.regua_da_leitura !== m.regua_id)) return null
  if (faixaE && (!medidoE || !texto(e.regua_id))) return null

  const reguaE = texto(e.regua_id)
  return {
    rio,
    municipal: {
      reguaId: texto(m.regua_id),
      faixa: faixaM,
      medidoEm: medidoM,
      deAgora: m.de_agora === true,
      seguraEstadual: typeof m.segura_estadual === 'boolean' ? m.segura_estadual : m.de_agora === true,
      cotasConfirmadas: m.status_faixas === 'confirmada',
      variasReguas: m.varias_reguas === true,
      rotulo: `Classificação municipal — ${texto(m.regua_nome) ?? texto(m.regua_id) ?? 'régua da cidade'}`,
      motivo: texto(m.motivo),
    },
    estadual: {
      reguaId: reguaE,
      faixa: faixaE,
      medidoEm: medidoE,
      rotulo: `Faixa estadual (Defesa Civil de SC) — ${reguaE ?? 'estação estadual'}`,
      aviso: `Cor pela classificação que a Defesa Civil de SC publica para a estação ${reguaE ?? ''}, no zero dela. Não são as cotas do município.`,
      motivo: texto(e.motivo),
    },
  }
}

/** O JSON cru → estado, ou null quando não é um arquivo que este site entende (aí vale a regra de sempre). */
export function montarClassificacao(corpo: unknown): EstadoClassificacao | null {
  if (typeof corpo !== 'object' || corpo === null) return null
  const d = corpo as Record<string, unknown>
  if (d.versao !== 1 || typeof d.gerado_em !== 'string') return null
  const geradoEm = new Date(d.gerado_em)
  if (Number.isNaN(geradoEm.getTime()) || !/(Z|[+-]\d{2}:\d{2})$/.test(d.gerado_em)) return null
  const cidades = new Map<string, ClassificacaoDaCidade>()
  const brutas = typeof d.cidades === 'object' && d.cidades !== null ? (d.cidades as Record<string, unknown>) : {}
  for (const [id, bruta] of Object.entries(brutas)) {
    const c = cidadeValida(bruta)
    if (c) cidades.set(id, c)
  }
  return { geradoEm, cidades }
}

/** De onde veio a cor que a tela mostra. */
export interface OrigemDaCor {
  tipo: 'municipal' | 'estadual'
  reguaId: string | null
  rotulo: string
  /** Só na estadual: a cor não é das cotas do município. */
  aviso: string | null
}

export interface FaixasDoMotor {
  faixa: Faixa
  faixaEstadual: Faixa | null
  origem: OrigemDaCor | null
  /**
   * As cotas da cidade não estão confirmadas: não há classificação municipal (decisão de 07/10/2026, Rio dos
   * Cedros). A tela não compara o nível com elas e diz que a falta de cor municipal não é nível normal.
   */
  cotasMunicipaisNaoConfirmadas: boolean
}

function mesmoInstante(a: Date | null | undefined, b: Date | null | undefined): boolean {
  return (a?.getTime() ?? null) === (b?.getTime() ?? null)
}

/**
 * A faixa da cidade pelo motor, ou null quando o site deve usar a regra de sempre.
 *
 * `leitura` e `estadual` são o que a TELA vai mostrar (do `ultimo.json` e do `ultimo_nivel_sc.json`). Os dois
 * arquivos e o da classificação são buscados em separado e podem estar em publicações vizinhas: se o motor
 * não viu as mesmas medições, a cor dele seria de outro número — e cor que não é do número na tela não sai.
 */
export function faixasDoMotor(
  estado: EstadoClassificacao | null | undefined,
  cidadeId: string,
  rioId: string,
  tela: { leituraMedidaEm: Date | null | undefined; estadualMedidaEm: Date | null | undefined; varias: boolean },
  agora: Date,
): FaixasDoMotor | null {
  if (!estado) return null
  const c = estado.cidades.get(cidadeId)
  if (!c || c.rio !== rioId) return null
  const idade = (agora.getTime() - estado.geradoEm.getTime()) / 60_000
  if (idade > MAX_IDADE_CLASSIFICACAO_MIN || idade < -15) return null
  if (c.municipal.variasReguas !== tela.varias) return null
  if (!tela.varias && !mesmoInstante(c.municipal.medidoEm, tela.leituraMedidaEm)) return null
  if (!mesmoInstante(c.estadual.medidoEm, tela.estadualMedidaEm)) return null

  // A idade, no relógio de agora: o que era "de agora" na coleta pode ter envelhecido desde então.
  const viva = (d: Date | null) => d !== null && frescorDaCidade(idadeMin(d, agora), cidadeId) !== 'velha'
  const municipal = c.municipal.faixa && viva(c.municipal.medidoEm) ? c.municipal.faixa : null
  const municipalDeAgora = c.municipal.seguraEstadual && viva(c.municipal.medidoEm)
  const cotasMunicipaisNaoConfirmadas = !c.municipal.cotasConfirmadas
  const estadual = c.estadual.faixa && viva(c.estadual.medidoEm) ? c.estadual.faixa : null

  if (municipal) {
    return {
      faixa: municipal,
      faixaEstadual: null,
      origem: { tipo: 'municipal', reguaId: c.municipal.reguaId, rotulo: c.municipal.rotulo, aviso: null },
      cotasMunicipaisNaoConfirmadas,
    }
  }
  const semMunicipal: Faixa = c.municipal.variasReguas ? 'varias' : 'sem-dado'
  if (!c.municipal.variasReguas && !municipalDeAgora && estadual) {
    return {
      faixa: semMunicipal,
      faixaEstadual: estadual,
      origem: { tipo: 'estadual', reguaId: c.estadual.reguaId, rotulo: c.estadual.rotulo, aviso: c.estadual.aviso },
      cotasMunicipaisNaoConfirmadas,
    }
  }
  return { faixa: semMunicipal, faixaEstadual: null, origem: null, cotasMunicipaisNaoConfirmadas }
}

/** O `fetch`, injetável para o teste rodar sem rede. */
export type Transporte = (url: string, init: RequestInit) => Promise<Response>

export async function buscarClassificacao(
  sinal?: AbortSignal,
  transporte: Transporte = (url, init) => fetch(url, init),
): Promise<EstadoClassificacao | null> {
  try {
    return montarClassificacao(await buscarPublicacao(URL_CLASSIFICACAO, sinal, transporte))
  } catch {
    // Sem o arquivo (VPS sem o motor, rede fora), o site segue pela regra de sempre.
    return null
  }
}

/** Busca ao abrir a página e a cada `intervaloMin`, como o nível ao vivo. */
export function useClassificacao(intervaloMin = 5): EstadoClassificacao | null {
  const [estado, setEstado] = useState<EstadoClassificacao | null>(null)

  useEffect(() => {
    let vivo = true
    const emVoo = new Set<AbortController>()

    const buscar = async () => {
      const controle = new AbortController()
      emVoo.add(controle)
      const limite = setTimeout(() => controle.abort(), TEMPO_LIMITE_MS)
      try {
        const novo = await buscarClassificacao(controle.signal)
        // Falha não guarda o anterior: um arquivo de outra coleta passaria por atual. O portão de idade
        // de `faixasDoMotor` já descartaria, mas sem ele a regra de sempre volta na hora.
        if (vivo) setEstado(novo)
      } finally {
        clearTimeout(limite)
        emVoo.delete(controle)
      }
    }

    void buscar()
    const relogio = setInterval(() => void buscar(), intervaloMin * 60_000)
    const pararDeOuvir = ouvirAtualizacao(() => void buscar())
    return () => {
      vivo = false
      clearInterval(relogio)
      pararDeOuvir()
      for (const c of emVoo) c.abort()
    }
  }, [intervaloMin])

  return estado
}
