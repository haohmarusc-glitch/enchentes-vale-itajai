/**
 * O que as últimas horas dizem, em três números — e quando NÃO dizem nada.
 *
 * Para o painel da cidade no Monitor: mínimo, máximo e quanto variou do
 * primeiro ao último ponto. É leitura de série, sem modelo.
 *
 * Recusa quando a série mistura RÉGUAS: em Itajaí a mesma cidade tem onze,
 * com zeros diferentes, e "mín 0,92 · máx 4,82" seria a DC-03 contra a DC-10 —
 * um número que parece uma amplitude e é duas réguas. `regua: null` conta como
 * uma régua desconhecida; duas desconhecidas não são a mesma.
 */
export interface PontoParaResumo {
  medidoEm: Date
  nivel_m: number
  regua: string | null
}

export interface Resumo24h {
  min: number
  max: number
  /** último − primeiro, em metros; positivo é subindo. */
  variacao: number
  pontos: number
  de: Date
  ate: Date
}

export type MotivoSemResumo = 'sem-pontos' | 'varias-reguas' | 'um-ponto-so'

export function resumo24h(
  pontos: readonly PontoParaResumo[],
): { resumo: Resumo24h; motivo: null } | { resumo: null; motivo: MotivoSemResumo } {
  const validos = pontos
    .filter((p) => Number.isFinite(p.nivel_m) && p.medidoEm instanceof Date && !Number.isNaN(+p.medidoEm))
    .sort((a, b) => +a.medidoEm - +b.medidoEm)
  if (validos.length === 0) return { resumo: null, motivo: 'sem-pontos' }
  const reguas = new Set(validos.map((p) => p.regua ?? '?'))
  if (reguas.size > 1 || (reguas.has('?') && validos.some((p) => p.regua === null) && validos.length > 1 && new Set(validos.map((p) => p.regua)).size > 1)) {
    return { resumo: null, motivo: 'varias-reguas' }
  }
  if (validos.length < 2) return { resumo: null, motivo: 'um-ponto-so' }
  const niveis = validos.map((p) => p.nivel_m)
  const primeiro = validos[0]!
  const ultimo = validos[validos.length - 1]!
  return {
    resumo: {
      min: Math.min(...niveis),
      max: Math.max(...niveis),
      variacao: Math.round((ultimo.nivel_m - primeiro.nivel_m) * 100) / 100,
      pontos: validos.length,
      de: primeiro.medidoEm,
      ate: ultimo.medidoEm,
    },
    motivo: null,
  }
}
