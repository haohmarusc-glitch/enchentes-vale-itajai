/**
 * A régua do CENTRO de Ituporanga (`ultimo_ituporanga_centro.json`), por decisão do Jefferson de 08/10/2026.
 *
 * A cor de Ituporanga no site vem da DCSC-00039, que fica A JUSANTE DA BARRAGEM SUL. A Prefeitura publica, no
 * Boletim Diário (duas leituras por dia, 07:00 e 17:00), OUTRA régua — "Centro" —, que ela não nomeia, não
 * situa e cujo zero não informa. O coletor (`scripts/coleta_ituporanga.py --publicar`) traz essa leitura num
 * arquivo próprio, fora de `leituras`: se entrasse como leitura municipal, desligaria a classificação estadual.
 *
 * Aqui ela aparece **com horário e fonte, e sem cor**: a criticidade que a fonte escreve é repassada como texto
 * da fonte, e nenhuma faixa deste projeto se aplica até a Defesa Civil confirmar as cotas na mesma régua.
 * A idade o site refaz no relógio de agora; leitura antiga nunca aparece como atual.
 */
import { useEffect, useState } from 'react'
import { deBrasilia, idadeMin, textoIdade } from '../logica/tempoReal'
import { metros } from '../logica/formato'
import { ouvirAtualizacao } from './atualizar'
import { quandoBrasilia } from './mareMedida'
import { buscarPublicacao } from './publicacao'

const PADRAO =
  'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/ultimo_ituporanga_centro.json'

export const URL_ITUPORANGA_CENTRO = import.meta.env?.VITE_URL_ITUPORANGA_CENTRO || PADRAO

/** O coletor roda a cada publicação (15 min): arquivo mais velho que isto é de uma publicação parada. */
export const MAX_IDADE_ARQUIVO_MIN = 30
/** Duas leituras por dia (07:00 e 17:00): mais de 18 h sem leitura nova é boletim parado. Igual ao coletor. */
export const FRESCOR_LEITURA_MIN = 18 * 60

const TEMPO_LIMITE_MS = 8000
const RE_SEM_FUSO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$/

export interface CentroItuporanga {
  geradoEm: Date
  fonte: string
  fonteUrl: string | null
  regua: { nome: string; identificada: boolean; nota: string | null }
  ultima: { medidoEm: Date; nivelM: number; criticidadeNaFonte: string | null }
}

const texto = (v: unknown): string | null => (typeof v === 'string' && v.trim() ? v : null)
const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)

/** O arquivo publicado, conferido. Qualquer coisa fora do combinado vira null: "leitura indisponível". */
export function montarCentroItuporanga(bruto: unknown): CentroItuporanga | null {
  if (!bruto || typeof bruto !== 'object') return null
  const d = bruto as Record<string, unknown>
  if (d.versao !== 1 || d.cidade !== 'ituporanga' || d.unidade !== 'm') return null
  const gerado = texto(d.gerado_em)
  // `gerado_em` é UTC com fuso; sem fuso seria Brasília lido como UTC, 3 h de erro.
  if (!gerado || RE_SEM_FUSO.test(gerado)) return null
  const geradoEm = new Date(gerado)
  if (Number.isNaN(geradoEm.getTime())) return null
  const u = d.ultima_leitura as Record<string, unknown> | null | undefined
  if (!u) return null
  const medido = texto(u.medido_em)
  // `medido_em` é Brasília SEM fuso (CLAUDE.md). Com fuso, o contrato foi quebrado: não se adivinha.
  if (!medido || !RE_SEM_FUSO.test(medido)) return null
  const medidoEm = deBrasilia(medido)
  const nivelM = num(u.nivel_m)
  if (Number.isNaN(medidoEm.getTime()) || nivelM === null) return null
  const r = (d.regua ?? {}) as Record<string, unknown>
  return {
    geradoEm,
    fonte: texto(d.fonte) ?? 'Prefeitura de Ituporanga — Defesa Civil',
    fonteUrl: texto(d.fonte_url),
    regua: { nome: texto(r.nome) ?? 'Centro', identificada: r.identificada === true, nota: texto(r.nota) },
    ultima: { medidoEm, nivelM, criticidadeNaFonte: texto(u.criticidade_na_fonte) },
  }
}

export type EstadoCentro =
  | { tipo: 'indisponivel' }
  | { tipo: 'antiga'; medidoEm: Date; idadeMin: number }
  | { tipo: 'leitura'; medidoEm: Date; idadeMin: number; nivelM: number; criticidadeNaFonte: string | null }

/**
 * O que a tela pode dizer agora:
 *  1. sem arquivo, arquivo de publicação parada ou sem leitura → indisponível;
 *  2. leitura mais velha que 18 h (refeito agora) ou do futuro → antiga, com a hora e sem o número;
 *  3. só então o número, com a hora e a criticidade COMO A FONTE ESCREVE — sem cor.
 */
export function estadoDoCentro(c: CentroItuporanga | null, agora: Date): EstadoCentro {
  if (!c) return { tipo: 'indisponivel' }
  const idadeArquivo = (agora.getTime() - c.geradoEm.getTime()) / 60_000
  if (idadeArquivo > MAX_IDADE_ARQUIVO_MIN || idadeArquivo < -15) return { tipo: 'indisponivel' }
  const idade = idadeMin(c.ultima.medidoEm, agora)
  if (idade < 0 || idade > FRESCOR_LEITURA_MIN) return { tipo: 'antiga', medidoEm: c.ultima.medidoEm, idadeMin: idade }
  return {
    tipo: 'leitura',
    medidoEm: c.ultima.medidoEm,
    idadeMin: idade,
    nivelM: c.ultima.nivelM,
    criticidadeNaFonte: c.ultima.criticidadeNaFonte,
  }
}

/** As frases de cada estado, à parte da tela para o teste ler o que o morador lê. */
export function textoDoCentro(e: EstadoCentro): { titulo: string; detalhe: string } {
  switch (e.tipo) {
    case 'indisponivel':
      return { titulo: 'Leitura indisponível.', detalhe: 'Não há leitura recente publicada pela Prefeitura.' }
    case 'antiga':
      return {
        titulo: 'Leitura indisponível.',
        detalhe:
          e.idadeMin < 0
            ? `A última leitura publicada traz um horário que ainda não chegou (${quandoBrasilia(e.medidoEm)}). Não é atual, e o número não aparece.`
            : `A última leitura publicada é de ${quandoBrasilia(e.medidoEm)} (${textoIdade(e.idadeMin)}). Não é atual, e o número não aparece.`,
      }
    case 'leitura':
      return {
        titulo: `Régua do Centro: ${metros(e.nivelM)}`,
        detalhe:
          `Lida em ${quandoBrasilia(e.medidoEm)}, ${textoIdade(e.idadeMin)}.` +
          (e.criticidadeNaFonte ? ` A Prefeitura classifica como “${e.criticidadeNaFonte}” — classificação dela, nas cotas dela.` : ''),
      }
  }
}

type Transporte = (url: string, init: RequestInit) => Promise<Response>

export async function buscarCentroItuporanga(
  sinal?: AbortSignal,
  transporte: Transporte = (url, init) => fetch(url, init),
): Promise<CentroItuporanga | null> {
  try {
    return montarCentroItuporanga(await buscarPublicacao(URL_ITUPORANGA_CENTRO, sinal, transporte))
  } catch {
    return null
  }
}

/** Busca ao abrir a página e a cada `intervaloMin`. Falha não guarda o anterior. */
export function useCentroItuporanga(intervaloMin = 5): { dado: CentroItuporanga | null; carregado: boolean } {
  const [estado, setEstado] = useState<{ dado: CentroItuporanga | null; carregado: boolean }>({
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
        const dado = await buscarCentroItuporanga(controle.signal)
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
