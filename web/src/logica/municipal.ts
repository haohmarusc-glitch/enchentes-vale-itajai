import type { Evento } from '../dados/tipos'

/** Aceita endereço governamental real, não menção a governo em texto livre. */
export function fontesGovernamentais(texto: string): string[] {
  return [...new Set((texto.match(/https?:\/\/[^\s<>"']+/g) ?? []).flatMap((s) => {
    try {
      const url = new URL(s.replace(/[),.;]+$/, ''))
      return url.hostname.endsWith('.gov.br') ? [url.href] : []
    } catch { return [] }
  }))]
}
export function historicoMunicipal(eventos: readonly Evento[], cidade: string) {
  return eventos.filter((e) => e.cidade === cidade && fontesGovernamentais(e.fonte).length > 0)
    .sort((a, b) => b.data.localeCompare(a.data))
}

import type { BrutoEstadual } from '../dados/nivelSc'
import { frescor, idadeMin } from './tempoReal'

/** C18, 11/09/2026: aplica somente à DCSC-00003, sem converter datum. */
export function faixaAscurra(l: BrutoEstadual | undefined, agora: Date) {
  const sem = { nome: 'Classificação indisponível', cor: '#596773' }
  if (!l || l.cidade !== 'ascurra' || l.codigo !== 'DCSC-00003' || !l.medidoEm ||
      !Number.isFinite(l.nivelBrutoM) || l.nivelBrutoM <= 0 || l.nivelBrutoM >= 30 ||
      frescor(idadeMin(l.medidoEm, agora)) === 'velha') return sem
  const n = l.nivelBrutoM
  if (n <= 8.50) return { nome: 'Monitoramento', cor: '#22648a' }
  if (n < 9.76) return { nome: 'Atenção', cor: '#806100' }
  // A fonte compartilha este extremo entre dois intervalos; não escolhe um.
  if (n === 9.76) return { nome: 'Limite entre atenção e alerta — inclusão não definida na fonte', cor: '#596773' }
  if (n <= 10.76) return { nome: 'Alerta', cor: '#a74400' }
  return { nome: 'Emergência', cor: '#ae2028' }
}
