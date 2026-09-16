import type { MedicaoComparavel } from './compararCheias'
import { frescorDaCidade, idadeMin } from './tempoReal'

/** Cota da carta publicada, sem interpolar geometria nem chamar simulação de evento. */
export function camadaBlumenau<T extends { nivel_m: number; arquivo: string }>(camadas: readonly T[], leituras: readonly MedicaoComparavel[], agora: Date): T | null {
  const l = leituras.filter(l => l.cidade === 'blumenau' &&
    (l.estacao === 'Blumenau (AlertaBlu)' || l.estacao === 'Blumenau') &&
    l.medidoEm && Number.isFinite(l.nivel_m) && l.nivel_m > 0 && l.nivel_m < 25 &&
    frescorDaCidade(idadeMin(l.medidoEm, agora), 'blumenau') !== 'velha')
    .sort((a,b) => b.medidoEm!.getTime() - a.medidoEm!.getTime())[0]
  if (!l) return null
  return [...camadas].filter(c => c.nivel_m <= l.nivel_m).sort((a,b) => b.nivel_m-a.nivel_m)[0] ?? null
}
