import type { ChuvaAoVivo } from '../dados/tempoReal'
import { frescor, idadeMin } from './tempoReal'

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
 * Linha de chuva no pino do Monitor: só o acumulado de 24 h, em mm, em
 * qualquer zoom (decisão de 02/10/2026 — a chuva voltou à vista da bacia).
 *
 * Uma linha só, sem 1 h, 12 h nem idade: quatro linhas por cidade cobriam o
 * rio no print de 26/09/2026. As três janelas, a estação e a idade da medição
 * continuam no painel da cidade (`ChuvaMonitor`).
 *
 * Como o pino não mostra a idade, leitura `velha` (mais de 3 h, ou do futuro)
 * vira "—": um acumulado de ontem nunca pode passar por chuva de agora.
 */
export function linhasChuva(chuvas: ChuvaAoVivo[], cidade: string, agora: Date): string[] {
  const c = chuvaMonitor(chuvas, cidade)
  const valeAgora = c?.medidoEm != null && frescor(idadeMin(c.medidoEm, agora)) !== 'velha'
  return [`24 h: ${mmChuva(valeAgora ? c.mm.h24 : null)} mm`]
}

/**
 * A chuva como BOLHA do pino, no Monitor compacto do celular (redesenho de 07/10/2026): só o número,
 * "19,6 mm", e só onde há pluviômetro com acumulado de 24 h de agora. Sem estação, sem valor ou com
 * medição velha não há bolha nenhuma — a camada já se chama "Chuva 24 h", e "— mm" numa bolha diria
 * que mediu quando não mediu.
 */
export function linhasChuvaCompactas(chuvas: ChuvaAoVivo[], cidade: string, agora: Date): string[] {
  const c = chuvaMonitor(chuvas, cidade)
  const valeAgora = c?.medidoEm != null && frescor(idadeMin(c.medidoEm, agora)) !== 'velha'
  if (!valeAgora || c.mm.h24 == null) return []
  return [`${mmChuva(c.mm.h24)} mm`]
}
