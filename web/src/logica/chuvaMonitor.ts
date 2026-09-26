import type { ChuvaAoVivo } from '../dados/tempoReal'
import { idadeMin, textoIdade } from './tempoReal'

/**
 * Largura máxima da tela (km) em que o pino ainda mostra chuva.
 *
 * Acima disso é vista de bacia: nome + nível bastam. Quatro linhas de chuva
 * por cidade cobriam o rio no print de 26/09/2026.
 */
export const KM_CHUVA_NO_MAPA = 40

/**
 * Em zoom perto (mesmo limiar das cotas de rua), o pino ganha também a idade
 * da medição. Entre este valor e `KM_CHUVA_NO_MAPA`, só a linha de 24 h.
 */
export const KM_CHUVA_DETALHE = 8

/** Um pluviômetro por cidade; nunca combina janelas de estações distintas. */
export function chuvaMonitor(chuvas: ChuvaAoVivo[], cidade: string): ChuvaAoVivo | null {
  return chuvas.filter(c => c.cidade === cidade && c.coerente && c.medidoEm
    && [c.mm.h1, c.mm.h12, c.mm.h24].some(v => v !== null))
    .sort((a, b) => b.medidoEm!.getTime() - a.medidoEm!.getTime()
      || a.estacao.localeCompare(b.estacao))[0] ?? null
}

export function mmChuva(valor: number | null | undefined): string {
  return valor == null ? '—' : valor.toLocaleString('pt-BR', { maximumFractionDigits: 1 })
}

/**
 * Linhas de chuva no pino do Monitor.
 *
 * Nunca inclui 1 h nem 12 h no mapa: poluem o desenho e as três janelas
 * continuam no painel (`ChuvaMonitor`). O detalhe depende da largura da vista:
 * bacia larga → nada; região → só 24 h; perto → 24 h + idade da medição.
 *
 * Sem `kmNaTela` (ou NaN), assume vista de região (só 24 h) — útil nos testes
 * e em qualquer chamada que ainda não passe o zoom.
 */
export function linhasChuva(
  chuvas: ChuvaAoVivo[],
  cidade: string,
  agora: Date,
  kmNaTela?: number,
): string[] {
  const km = kmNaTela === undefined || !Number.isFinite(kmNaTela) ? KM_CHUVA_DETALHE + 1 : kmNaTela
  if (km > KM_CHUVA_NO_MAPA) return []

  const c = chuvaMonitor(chuvas, cidade)
  const linhas = [`24 h: ${mmChuva(c?.mm.h24)} mm`]
  if (km <= KM_CHUVA_DETALHE) {
    // A idade é a da MEDIÇÃO do pluviômetro (medidoEm), não a da coleta — e o
    // texto diz isso, senão "Chuva · há 10 min" lê como "choveu há 10 min".
    linhas.push(
      c?.medidoEm ? `Chuva atualizada ${textoIdade(idadeMin(c.medidoEm, agora))}` : 'Chuva indisponível',
    )
  }
  return linhas
}
