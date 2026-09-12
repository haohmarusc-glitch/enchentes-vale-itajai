import type { ChuvaAoVivo } from '../dados/tempoReal'

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
