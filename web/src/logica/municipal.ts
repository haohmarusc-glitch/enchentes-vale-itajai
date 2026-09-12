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
import { faixaC18 } from './tempoReal'

/** C18, 11/09/2026: aplica somente à DCSC-00003, sem converter datum. */
export function faixaAscurra(l: BrutoEstadual | undefined, agora: Date) {
  const faixa = l?.cidade === 'ascurra' ? faixaC18({nivel_m:l.nivelBrutoM, codigo:l.codigo ?? undefined, medidoEm:l.medidoEm}, agora) : 'sem-dado'
  const nomes: Record<string, string> = {monitoramento:'Monitoramento',atencao:'Atenção',alerta:'Alerta',emergencia:'Emergência'}
  if (faixa === 'sem-dado') {
    const limite = l?.nivelBrutoM === 9.76 && faixaC18({...l, nivel_m:9.75, codigo:l.codigo ?? undefined, medidoEm:l.medidoEm},agora) === 'atencao'
    return {nome: limite ? 'Limite entre atenção e alerta — inclusão não definida na fonte' : 'Classificação indisponível', cor:'var(--faixa-sem-dado, #9aa7b2)'}
  }
  return {nome:nomes[faixa]!, cor:`var(--faixa-${faixa})`}
}
