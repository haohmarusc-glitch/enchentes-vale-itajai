/** Somente fases de acionamento; marcas históricas e administrativas não são gatilhos. */
export const ORDEM_COTAS = ['monitoramento', 'atencao', 'alerta', 'emergencia', 'inundacao'] as const
export const CHAVES_QUE_PINTAM: ReadonlySet<string> = new Set(ORDEM_COTAS)

export function cotasOperacionais(cotas: Record<string, unknown>): [string, number][] {
  return ORDEM_COTAS.flatMap((chave) => {
    const valor = cotas[chave]
    return typeof valor === 'number' && Number.isFinite(valor) ? [[chave, valor] as [string, number]] : []
  })
}
