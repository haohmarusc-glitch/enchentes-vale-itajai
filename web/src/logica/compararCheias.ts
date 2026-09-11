import { frescor, idadeMin } from './tempoReal'
export interface EventoComparavel {
  cidade: string
  evento: string
  tipo?: string
  arquivo: string
  pico_registrado: { pico_m: number | null; regua?: string | null; fonte?: string } | null
  chuva_7dias?: { mm: number; inicio: string; fim: string; estacao: string; fonte: string } | null
}
export interface MedicaoComparavel {
  cidade: string | null
  estacao: string
  resgateDe?: string | null
  nivel_m: number
  medidoEm: Date | null
}
/** Só aproxima eventos com nível documentado da mesma régua e leitura recente. */
export function cheiaMaisProxima(eventos: readonly EventoComparavel[], leituras: readonly MedicaoComparavel[], agora: Date) {
  const pares = eventos.flatMap((evento) => {
    const pico = evento.pico_registrado
    if (!pico?.regua || !pico.fonte || typeof pico.pico_m !== 'number' || !Number.isFinite(pico.pico_m)) return []
    const leitura = leituras.filter((l) => l.cidade === evento.cidade &&
      (l.resgateDe ?? l.estacao) === pico.regua && Number.isFinite(l.nivel_m) &&
      l.medidoEm && frescor(idadeMin(l.medidoEm, agora)) !== 'velha')
      .sort((a, b) => b.medidoEm!.getTime() - a.medidoEm!.getTime())[0]
    return leitura ? [{ evento, leitura, diferencaM: leitura.nivel_m - pico.pico_m }] : []
  })
  return pares.sort((a, b) => Math.abs(a.diferencaM) - Math.abs(b.diferencaM) || a.evento.arquivo.localeCompare(b.evento.arquivo))[0] ?? null
}
