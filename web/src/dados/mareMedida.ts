/**
 * Maré MEDIDA da EPAGRI/CIRAM (`ultimo_mare_medida.json`), por decisão do Jefferson de 07/10/2026.
 *
 * O coletor (`scripts/coleta_mare_ciram.py --publicar`) consulta a estação de Balneário Camboriú, a 13 km
 * da foz, a cada publicação. Ele só põe número no arquivo com a referência vertical (o zero) confirmada;
 * sem ela, a tela diz "referência pendente". A idade da medição o site refaz no relógio de agora: leitura
 * antiga nunca aparece como atual.
 *
 * A diferença para a maré astronômica sai da MESMA linha da MESMA estação (o coletor faz a conta). Ela se
 * chama "diferença entre nível observado e maré astronômica prevista": não se atribui só a vento e pressão,
 * porque também pode trazer influência do rio e outros efeitos. A tábua do porto de Itajaí usada no site (a da
 * UNIVALI desde 08/10/2026) é outro lugar e outro zero, e continua sendo a previsão da tela, à parte.
 */
import { useEffect, useState } from 'react'
import { metros } from '../logica/formato'
import { deBrasilia, idadeMin, textoIdade } from '../logica/tempoReal'
import { ouvirAtualizacao } from './atualizar'
import { buscarPublicacao } from './publicacao'

const PADRAO =
  'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/ultimo_mare_medida.json'

/** Dá para apontar para outra fonte sem recompilar, via .env do Vite. */
export const URL_MARE_MEDIDA = import.meta.env?.VITE_URL_MARE_MEDIDA || PADRAO

/** O coletor roda a cada publicação (15 min): arquivo mais velho que isto é de uma publicação parada. */
export const MAX_IDADE_ARQUIVO_MIN = 30
/** Cadência da estação é 15 min; uma hora sem medição nova já é estação parada. Igual ao coletor. */
export const FRESCOR_MEDICAO_MIN = 60

const TEMPO_LIMITE_MS = 8000
const RE_SEM_FUSO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$/

export interface MareMedida {
  geradoEm: Date
  fonte: string
  fonteUrl: string | null
  estacao: { nome: string; kmDaFoz: number | null }
  referencia: { confirmada: boolean; descricao: string | null; fonte: string | null }
  ultima: {
    medidoEm: Date
    observadaM: number | null
    astronomicaM: number | null
    diferencaM: number | null
  } | null
}

const texto = (v: unknown): string | null => (typeof v === 'string' && v.trim() ? v : null)
const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)

/** O arquivo publicado, conferido. Qualquer coisa fora do combinado vira null: "medição indisponível". */
export function montarMareMedida(bruto: unknown): MareMedida | null {
  if (!bruto || typeof bruto !== 'object') return null
  const d = bruto as Record<string, unknown>
  if (d.versao !== 1) return null
  const gerado = texto(d.gerado_em)
  // `gerado_em` é UTC com fuso; sem fuso seria Brasília lido como UTC, 3 h de erro.
  if (!gerado || RE_SEM_FUSO.test(gerado)) return null
  const geradoEm = new Date(gerado)
  if (Number.isNaN(geradoEm.getTime())) return null
  const est = d.estacao as Record<string, unknown> | undefined
  const nome = texto(est?.nome)
  if (!nome) return null
  // A unidade publicada é metro; outra coisa não se mostra.
  if (d.unidade !== 'm') return null
  const ref = (d.referencia_vertical ?? {}) as Record<string, unknown>
  const confirmada =
    ref.status === 'confirmada' && texto(ref.descricao) !== null && texto(ref.fonte) !== null

  let ultima: MareMedida['ultima'] = null
  const u = d.ultima_medicao as Record<string, unknown> | null | undefined
  if (u) {
    const medido = texto(u.medido_em)
    // `medido_em` é Brasília SEM fuso (CLAUDE.md). Com fuso, o contrato foi quebrado: não se adivinha.
    if (!medido || !RE_SEM_FUSO.test(medido)) return null
    const medidoEm = deBrasilia(medido)
    if (Number.isNaN(medidoEm.getTime())) return null
    ultima = {
      medidoEm,
      observadaM: num(u.observada_m),
      astronomicaM: num(u.astronomica_m),
      diferencaM: num(u.diferenca_observado_astronomica_m),
    }
  }

  return {
    geradoEm,
    fonte: texto(d.fonte) ?? 'EPAGRI/CIRAM',
    fonteUrl: texto(d.fonte_url),
    estacao: { nome, kmDaFoz: num(est?.km_da_foz) },
    referencia: {
      confirmada,
      descricao: confirmada ? texto(ref.descricao) : null,
      fonte: confirmada ? texto(ref.fonte) : null,
    },
    ultima,
  }
}

export type EstadoMareMedida =
  | { tipo: 'indisponivel' }
  | { tipo: 'antiga'; medidoEm: Date; idadeMin: number }
  | { tipo: 'referencia-pendente'; medidoEm: Date; idadeMin: number }
  | {
      tipo: 'medida'
      medidoEm: Date
      idadeMin: number
      observadaM: number
      referencia: string
      fonteDaReferencia: string
      diferencaM: number | null
    }

/**
 * O que a tela pode dizer agora. Ordem dos portões:
 *  1. sem arquivo, arquivo de publicação parada ou sem medição → indisponível;
 *  2. medição mais velha que o frescor (refeito agora) ou do futuro → antiga, nunca como atual;
 *  3. referência vertical não confirmada → pendente, sem número;
 *  4. só então o nível, e a diferença quando a mesma linha a trouxe.
 */
export function estadoDaMareMedida(m: MareMedida | null, agora: Date): EstadoMareMedida {
  if (!m || !m.ultima) return { tipo: 'indisponivel' }
  const idadeArquivo = (agora.getTime() - m.geradoEm.getTime()) / 60_000
  if (idadeArquivo > MAX_IDADE_ARQUIVO_MIN || idadeArquivo < -15) return { tipo: 'indisponivel' }
  const idade = idadeMin(m.ultima.medidoEm, agora)
  if (idade < 0 || idade > FRESCOR_MEDICAO_MIN) {
    return { tipo: 'antiga', medidoEm: m.ultima.medidoEm, idadeMin: idade }
  }
  if (!m.referencia.confirmada || m.ultima.observadaM === null) {
    return { tipo: 'referencia-pendente', medidoEm: m.ultima.medidoEm, idadeMin: idade }
  }
  return {
    tipo: 'medida',
    medidoEm: m.ultima.medidoEm,
    idadeMin: idade,
    observadaM: m.ultima.observadaM,
    referencia: m.referencia.descricao!,
    fonteDaReferencia: m.referencia.fonte!,
    diferencaM: m.ultima.astronomicaM === null ? null : m.ultima.diferencaM,
  }
}

/** `+0,17 m` / `−0,02 m`: o sinal é a informação, então aparece sempre. */
const DIA = new Intl.DateTimeFormat('pt-BR', { timeZone: 'America/Sao_Paulo', day: '2-digit', month: '2-digit' })
const HORA = new Intl.DateTimeFormat('pt-BR', { timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit' })

/** `07/10 às 18:30 (Brasília)`: o horário da medição, sempre no fuso da fonte, dito na tela. */
export function quandoBrasilia(d: Date): string {
  return `${DIA.format(d)} às ${HORA.format(d)} (Brasília)`
}

export function comSinal(v: number): string {
  if (v === 0) return metros(0)
  return `${v > 0 ? '+' : '−'}${metros(Math.abs(v))}`
}

/** As frases de cada estado, à parte da tela para o teste ler o que o morador lê. */
export function textoDaMareMedida(e: EstadoMareMedida): { titulo: string; detalhe: string } {
  switch (e.tipo) {
    case 'indisponivel':
      return {
        titulo: 'Medição indisponível.',
        detalhe: 'Não há medição recente publicada desta estação.',
      }
    case 'antiga':
      return {
        titulo: 'Medição indisponível.',
        detalhe:
          e.idadeMin < 0
            ? `A última medição publicada traz um horário que ainda não chegou (${quandoBrasilia(e.medidoEm)}). Não é atual, e o número não aparece.`
            : `A última medição publicada é de ${quandoBrasilia(e.medidoEm)} (${textoIdade(e.idadeMin)}). Não é atual, e o número não aparece.`,
      }
    case 'referencia-pendente':
      return {
        titulo: 'Referência pendente.',
        detalhe:
          `O marégrafo está medindo (última medição em ${quandoBrasilia(e.medidoEm)}, ${textoIdade(e.idadeMin)}), ` +
          'mas a fonte não informa a referência vertical (o zero) a que o nível se refere. Sem ela, o número não aparece aqui.',
      }
    case 'medida':
      return {
        titulo: `Nível observado: ${metros(e.observadaM)}`,
        detalhe: `Medido em ${quandoBrasilia(e.medidoEm)}, ${textoIdade(e.idadeMin)}. Referência vertical: ${e.referencia} (fonte: ${e.fonteDaReferencia}).`,
      }
  }
}

type Transporte = (url: string, init: RequestInit) => Promise<Response>

export async function buscarMareMedida(
  sinal?: AbortSignal,
  transporte: Transporte = (url, init) => fetch(url, init),
): Promise<MareMedida | null> {
  try {
    return montarMareMedida(await buscarPublicacao(URL_MARE_MEDIDA, sinal, transporte))
  } catch {
    return null
  }
}

/** Busca ao abrir a página e a cada `intervaloMin`. Falha não guarda o anterior. */
export function useMareMedida(intervaloMin = 5): { dado: MareMedida | null; carregado: boolean } {
  const [estado, setEstado] = useState<{ dado: MareMedida | null; carregado: boolean }>({
    dado: null,
    carregado: false,
  })

  useEffect(() => {
    let vivo = true
    const emVoo = new Set<AbortController>()
    const buscar = async () => {
      const controle = new AbortController()
      emVoo.add(controle)
      const limite = setTimeout(() => controle.abort(), TEMPO_LIMITE_MS)
      try {
        const dado = await buscarMareMedida(controle.signal)
        if (vivo) setEstado({ dado, carregado: true })
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
