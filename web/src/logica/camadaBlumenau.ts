import type { MedicaoComparavel } from './compararCheias'
import { frescorDaCidade, idadeMin } from './tempoReal'

/**
 * As publicações da régua de Blumenau: o AlertaBlu horário, a série de 5 min da
 * PADKND (portal da Defesa Civil de Itajaí, conferida contra o AlertaBlu a cada
 * coleta) e o repasse antigo da página de Itajaí — este com o relógio 3 h
 * atrasado, mas o valor bom; aqui só o valor conta.
 */
const PUBLICACOES_DE_BLUMENAU = new Set(['Blumenau (AlertaBlu)', 'Blumenau (PADKND)', 'Blumenau'])

/** Cota da carta publicada, sem interpolar geometria nem chamar simulação de evento. */
export function camadaBlumenau<T extends { nivel_m: number; arquivo: string }>(camadas: readonly T[], leituras: readonly MedicaoComparavel[], agora: Date): T | null {
  const l = leituras.filter(l => l.cidade === 'blumenau' &&
    PUBLICACOES_DE_BLUMENAU.has(l.estacao) &&
    l.medidoEm && Number.isFinite(l.nivel_m) && l.nivel_m > 0 && l.nivel_m < 25 &&
    frescorDaCidade(idadeMin(l.medidoEm, agora), 'blumenau') !== 'velha')
    .sort((a,b) => b.medidoEm!.getTime() - a.medidoEm!.getTime())[0]
  if (!l) return null
  return [...camadas].filter(c => c.nivel_m <= l.nivel_m).sort((a,b) => b.nivel_m-a.nivel_m)[0] ?? null
}
