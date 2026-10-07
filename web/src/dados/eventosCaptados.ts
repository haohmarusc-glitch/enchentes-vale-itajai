/**
 * As cheias que a PRÓPRIA COLETA do site já captou (`data/eventos-captados.json`, gerado por
 * `scripts/eventos_captados.py` a partir da série de 15 em 15 min).
 *
 * É um resumo da captura — "a maior leitura que o site captou foi X às HH:MM" —, não pico conferido nem
 * registro oficial: a série tem lacunas, e cada episódio diz a maior delas. O arquivo nunca escreve em
 * `enchentes.json`; `registro_em_enchentes` só aponta o que JÁ foi conferido e gravado lá. Horários em
 * horário de Brasília sem fuso, como a série (`deBrasilia`).
 */
import eventosJson from '../../../data/eventos-captados.json'
import { deBrasilia } from '../logica/tempoReal'
import type { Faixa } from '../logica/tempoReal'

export type FaixaCaptada = Exclude<Faixa, 'sem-dado' | 'varias' | 'normal'>

export interface EpisodioCaptado {
  id: string
  rio: string
  cidade: string
  /** O título da publicação (régua); Itajaí tem uma por estação. */
  regua: string
  /** A publicação ainda está no cadastro de tempo real (`false`: fonte antiga, como "Rio do Sul Estação MKS"). */
  no_cadastro: boolean
  inicio: Date
  fim: Date
  maior_leitura_m: number
  quando: Date
  horario_de: string
  relogio_defasado: boolean
  cota_referencia: { chave: string; valor_m: number }
  faixa_alcancada: FaixaCaptada | null
  leituras: number
  maior_lacuna_min: number
  leituras_suspeitas: number
  registro_em_enchentes: { data: string; hora: string | null; pico_m: number | null; referencia: string | null; confianca: string | null } | null
}

export interface CoberturaCaptada {
  cidade: string
  rio: string
  regua: string
  no_cadastro: boolean
  varias_ao_mesmo_tempo: boolean
  publicacoes: string[]
  de: Date
  ate: Date
  leituras: number
  cota_referencia: { chave: string; valor_m: number } | null
  /** Por que esta régua não ganha faixa (estuário, C18); `null` quando ganha. */
  sem_faixa: string | null
  maior_leitura: { nivel_m: number; quando: Date; horario_de: string; relogio_defasado: boolean; faixa: FaixaCaptada | null }
}

export interface EventosCaptados {
  geradoEm: Date | null
  cobertura: CoberturaCaptada[]
  episodios: EpisodioCaptado[]
}

interface Bruto {
  gerado_em?: string
  cobertura?: Array<Omit<CoberturaCaptada, 'de' | 'ate' | 'maior_leitura'> & { de: string; ate: string; maior_leitura: Omit<CoberturaCaptada['maior_leitura'], 'quando'> & { quando: string } }>
  episodios?: Array<Omit<EpisodioCaptado, 'inicio' | 'fim' | 'quando'> & { inicio: string; fim: string; quando: string }>
}

const dataValida = (d: Date) => Number.isFinite(d.getTime())

export function lerEventosCaptados(bruto: unknown): EventosCaptados {
  const b = (bruto ?? {}) as Bruto
  const geradoEm = b.gerado_em ? new Date(b.gerado_em) : null
  const cobertura: CoberturaCaptada[] = []
  for (const c of b.cobertura ?? []) {
    const de = deBrasilia(c.de)
    const ate = deBrasilia(c.ate)
    const quando = deBrasilia(c.maior_leitura?.quando ?? '')
    if (!c.cidade || !c.regua || !dataValida(de) || !dataValida(ate) || !dataValida(quando) || !Number.isFinite(c.maior_leitura?.nivel_m)) continue
    cobertura.push({ ...c, de, ate, maior_leitura: { ...c.maior_leitura, quando } })
  }
  const episodios: EpisodioCaptado[] = []
  for (const e of b.episodios ?? []) {
    const inicio = deBrasilia(e.inicio)
    const fim = deBrasilia(e.fim)
    const quando = deBrasilia(e.quando)
    if (!e.cidade || !e.regua || !dataValida(inicio) || !dataValida(fim) || !dataValida(quando) || !Number.isFinite(e.maior_leitura_m)) continue
    episodios.push({ ...e, inicio, fim, quando })
  }
  episodios.sort((a, b2) => a.inicio.getTime() - b2.inicio.getTime())
  return { geradoEm: geradoEm && dataValida(geradoEm) ? geradoEm : null, cobertura, episodios }
}

export const eventosCaptados: EventosCaptados = lerEventosCaptados(eventosJson)
