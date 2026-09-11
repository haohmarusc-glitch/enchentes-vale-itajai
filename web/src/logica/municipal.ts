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
