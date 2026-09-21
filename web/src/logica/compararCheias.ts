import { frescorDaCidade, idadeMin } from './tempoReal'
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
/**
 * Só aproxima eventos com nível documentado da mesma régua e leitura recente.
 * "Recente" é por cidade: Blumenau fica velha aos 120 min (AlertaBlu é
 * horário), as demais aos 180 — o mesmo limite que o bot usa, alinhado em
 * 21/09/2026 por decisão do Jefferson. Antes este filtro usava 180 para todas
 * e a comparação de cheias podia pintar Blumenau com leitura que o mapa já
 * recusava.
 */
export function cheiaMaisProxima(eventos: readonly EventoComparavel[], leituras: readonly MedicaoComparavel[], agora: Date) {
  const pares = eventos.flatMap((evento) => {
    const pico = evento.pico_registrado
    if (!pico?.regua || !pico.fonte || typeof pico.pico_m !== 'number' || !Number.isFinite(pico.pico_m)) return []
    const leitura = leituras.filter((l) => l.cidade === evento.cidade &&
      (l.resgateDe ?? l.estacao) === pico.regua && Number.isFinite(l.nivel_m) &&
      l.medidoEm && frescorDaCidade(idadeMin(l.medidoEm, agora), l.cidade) !== 'velha')
      .sort((a, b) => b.medidoEm!.getTime() - a.medidoEm!.getTime())[0]
    return leitura ? [{ evento, leitura, diferencaM: leitura.nivel_m - pico.pico_m }] : []
  })
  return pares.sort((a, b) => Math.abs(a.diferencaM) - Math.abs(b.diferencaM) || a.evento.arquivo.localeCompare(b.evento.arquivo))[0] ?? null
}
