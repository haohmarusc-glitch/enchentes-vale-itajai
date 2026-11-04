/**
 * Avisos e alertas meteorológicos da Defesa Civil de SC (`ultimo_avisos_dcsc.json`), decisão do Jefferson de
 * 04/11/2026 ("aprovo todas" as pendências do relatório de ganhos; coletor em `scripts/coleta_avisos_dcsc.py`).
 *
 * O QUE É E O QUE NÃO É. O WordPress da DCSC publica os avisos oficiais do Estado em prosa, por REGIÃO ("Vale do
 * Itajaí", "Foz do Itajaí", "Litoral Norte", "todo o Estado"), nunca por município nem por polígono. Aqui eles
 * aparecem como **aviso da Defesa Civil de SC para a região**, com categoria, hora de Brasília, regiões citadas e
 * o link do original — e nunca como "aviso para a sua cidade". Nada daqui é faixa do rio, não pinta mapa nem
 * cartão, não dispara aviso de cota e não entra em `leituras`.
 *
 * Idade: o coletor roda a cada publicação (15 min); arquivo com mais de 30 min é publicação parada → indisponível.
 * Um aviso só aparece como "recente" nas primeiras 24 h depois de publicado (a DCSC fala em "próximas horas" e não
 * declara validade legível por máquina; 24 h é o teto, não a vigência). Fora disso, a tela diz quando foi o último.
 */
import { useEffect, useState } from 'react'
import { deBrasilia, idadeMin, textoIdade } from '../logica/tempoReal'
import { ouvirAtualizacao } from './atualizar'
import { quandoBrasilia } from './mareMedida'
import { buscarPublicacao } from './publicacao'

const PADRAO =
  'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/ultimo_avisos_dcsc.json'

export const URL_AVISOS_DCSC = import.meta.env?.VITE_URL_AVISOS_DCSC || PADRAO

/** O coletor roda a cada publicação (15 min): arquivo mais velho que isto é de uma publicação parada. */
export const MAX_IDADE_ARQUIVO_MIN = 30
/** Teto para um aviso contar como recente. Não é a vigência (a DCSC não a publica legível por máquina). */
export const RECENTE_MIN = 24 * 60
/** Quantos avisos recentes a tela lista, no máximo. */
export const MAX_NA_TELA = 5

const TEMPO_LIMITE_MS = 8000
const RE_SEM_FUSO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$/
const HOST_DA_FONTE = 'www.defesacivil.sc.gov.br'

export type CategoriaDcsc = 'Alerta' | 'Aviso'

export interface AvisoDcsc {
  id: number
  categoria: CategoriaDcsc
  titulo: string
  publicadoEm: Date
  /** Link do original; só `https://www.defesacivil.sc.gov.br/...` passa. Fora disso, sem link. */
  link: string | null
  regioes: string[]
  estadoInteiro: boolean
  /** Alguma região citada cobre cidades do projeto (ou o aviso é para o Estado inteiro). */
  incluiBacia: boolean
  trecho: string
}

export interface AvisosDcsc {
  geradoEm: Date
  fonte: string
  fonteUrl: string | null
  regioesDaBacia: string[]
  avisos: AvisoDcsc[]
}

const texto = (v: unknown): string | null => (typeof v === 'string' && v.trim() ? v : null)

function linkDaFonte(v: unknown): string | null {
  const t = texto(v)
  if (!t) return null
  try {
    const u = new URL(t)
    return u.protocol === 'https:' && u.hostname === HOST_DA_FONTE ? u.toString() : null
  } catch {
    return null
  }
}

function montarAviso(bruto: unknown): AvisoDcsc | null {
  if (!bruto || typeof bruto !== 'object') return null
  const a = bruto as Record<string, unknown>
  if (a.categoria !== 'Alerta' && a.categoria !== 'Aviso') return null
  const titulo = texto(a.titulo)
  const publicado = texto(a.publicado_em)
  // `publicado_em` é Brasília SEM fuso (contrato do CLAUDE.md). Com fuso, o contrato foi quebrado: não se adivinha.
  if (!titulo || !publicado || !RE_SEM_FUSO.test(publicado)) return null
  const publicadoEm = deBrasilia(publicado)
  if (Number.isNaN(publicadoEm.getTime())) return null
  const regioes = Array.isArray(a.regioes) ? a.regioes.filter((r): r is string => typeof r === 'string' && r.trim() !== '') : []
  return {
    id: typeof a.id === 'number' ? a.id : -1,
    categoria: a.categoria,
    titulo,
    publicadoEm,
    link: linkDaFonte(a.link),
    regioes,
    estadoInteiro: a.estado_inteiro === true,
    incluiBacia: a.inclui_bacia === true,
    trecho: texto(a.trecho) ?? '',
  }
}

/** O arquivo publicado, conferido. Qualquer coisa fora do combinado vira null: "avisos indisponíveis". */
export function montarAvisosDcsc(bruto: unknown): AvisosDcsc | null {
  if (!bruto || typeof bruto !== 'object') return null
  const d = bruto as Record<string, unknown>
  if (d.versao !== 1 || !Array.isArray(d.avisos)) return null
  const gerado = texto(d.gerado_em)
  // `gerado_em` é UTC com fuso; sem fuso seria Brasília lido como UTC, 3 h de erro.
  if (!gerado || RE_SEM_FUSO.test(gerado)) return null
  const geradoEm = new Date(gerado)
  if (Number.isNaN(geradoEm.getTime())) return null
  const avisos = d.avisos.map(montarAviso).filter((a): a is AvisoDcsc => a !== null)
  avisos.sort((x, y) => y.publicadoEm.getTime() - x.publicadoEm.getTime())
  return {
    geradoEm,
    fonte: texto(d.fonte) ?? 'Defesa Civil de Santa Catarina — www.defesacivil.sc.gov.br',
    fonteUrl: linkDaFonte(d.fonte_url) ?? 'https://www.defesacivil.sc.gov.br/',
    regioesDaBacia: Array.isArray(d.regioes_da_bacia) ? d.regioes_da_bacia.filter((r): r is string => typeof r === 'string') : [],
    avisos,
  }
}

export type EstadoAvisos =
  | { tipo: 'indisponivel' }
  /** Nenhum aviso recente que cite a bacia; `ultimo` é o mais novo que a citou, se houver (fora das 24 h). */
  | { tipo: 'nenhum'; ultimo: AvisoDcsc | null; outrasRegioes: number }
  | { tipo: 'avisos'; recentes: (AvisoDcsc & { idadeMin: number })[]; outrasRegioes: number }

/**
 * O que a tela pode dizer agora:
 *  1. sem arquivo ou arquivo de publicação parada → indisponível;
 *  2. nenhum aviso das últimas 24 h citando região da bacia → "nenhum", dizendo quando foi o último;
 *  3. senão, os recentes que citam a bacia (até MAX_NA_TELA), com a idade refeita no relógio de agora.
 * Avisos recentes para outras regiões entram só como contagem: a pessoa vê que o Estado tem aviso, não a bacia.
 */
export function estadoDosAvisos(d: AvisosDcsc | null, agora: Date): EstadoAvisos {
  if (!d) return { tipo: 'indisponivel' }
  const idadeArquivo = (agora.getTime() - d.geradoEm.getTime()) / 60_000
  if (idadeArquivo > MAX_IDADE_ARQUIVO_MIN || idadeArquivo < -15) return { tipo: 'indisponivel' }
  const recentes = d.avisos
    .map((a) => ({ ...a, idadeMin: idadeMin(a.publicadoEm, agora) }))
    .filter((a) => a.idadeMin >= 0 && a.idadeMin <= RECENTE_MIN)
  const daBacia = recentes.filter((a) => a.incluiBacia)
  const outrasRegioes = recentes.length - daBacia.length
  if (daBacia.length === 0) {
    return { tipo: 'nenhum', ultimo: d.avisos.find((a) => a.incluiBacia) ?? null, outrasRegioes }
  }
  return { tipo: 'avisos', recentes: daBacia.slice(0, MAX_NA_TELA), outrasRegioes }
}

/** As frases de cada estado, à parte da tela para o teste ler o que o morador lê. */
export function textoDosAvisos(e: EstadoAvisos): { titulo: string; detalhe: string } {
  const outras = (n: number) =>
    n > 0 ? ` Há ${n === 1 ? 'um aviso recente' : `${n} avisos recentes`} para outras regiões do Estado.` : ''
  switch (e.tipo) {
    case 'indisponivel':
      return {
        titulo: 'Avisos indisponíveis.',
        detalhe: 'Não há publicação recente da Defesa Civil de SC lida pelo site. Confira direto no site dela.',
      }
    case 'nenhum':
      return {
        titulo: 'Nenhum aviso recente para a região.',
        detalhe:
          (e.ultimo
            ? `O último que citou uma região da bacia foi em ${quandoBrasilia(e.ultimo.publicadoEm)}: “${e.ultimo.titulo}”.`
            : 'Nenhum aviso publicado cita uma região da bacia.') + outras(e.outrasRegioes),
      }
    case 'avisos': {
      const n = e.recentes.length
      return {
        titulo: n === 1 ? 'Um aviso recente da Defesa Civil de SC para a região.' : `${n} avisos recentes da Defesa Civil de SC para a região.`,
        detalhe: `Por região, como a Defesa Civil escreve — não é aviso para uma cidade nem faixa do rio.${outras(e.outrasRegioes)}`,
      }
    }
  }
}

/** Uma linha por aviso: categoria, hora de Brasília e idade, regiões citadas. */
export function linhaDoAviso(a: AvisoDcsc & { idadeMin: number }): string {
  const onde = a.estadoInteiro ? 'todo o Estado' : a.regioes.length > 0 ? a.regioes.join(', ') : 'região não identificada no texto'
  return `${a.categoria} · ${quandoBrasilia(a.publicadoEm)}, ${textoIdade(a.idadeMin)} · ${onde}`
}

type Transporte = (url: string, init: RequestInit) => Promise<Response>

export async function buscarAvisosDcsc(
  sinal?: AbortSignal,
  transporte: Transporte = (url, init) => fetch(url, init),
): Promise<AvisosDcsc | null> {
  try {
    return montarAvisosDcsc(await buscarPublicacao(URL_AVISOS_DCSC, sinal, transporte))
  } catch {
    return null
  }
}

/** Busca ao abrir a página e a cada `intervaloMin`. Falha não guarda o anterior. */
export function useAvisosDcsc(intervaloMin = 5): { dado: AvisosDcsc | null; carregado: boolean } {
  const [estado, setEstado] = useState<{ dado: AvisosDcsc | null; carregado: boolean }>({ dado: null, carregado: false })

  useEffect(() => {
    let vivo = true
    const emVoo = new Set<AbortController>()
    const buscar = async () => {
      const controle = new AbortController()
      emVoo.add(controle)
      const limite = setTimeout(() => controle.abort(), TEMPO_LIMITE_MS)
      try {
        const dado = await buscarAvisosDcsc(controle.signal)
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
