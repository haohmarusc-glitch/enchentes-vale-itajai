/** Formatação em pt-BR. Metros sempre com 2 casas — a régua é lida em centímetros. */

export function metros(v: number): string {
  return `${v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} m`
}

export function numero(v: number, casas = 2): string {
  return v.toLocaleString('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas })
}

export function dataHora(d: Date): string {
  return d.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * O que a confiança significa depende do que ela qualifica.
 *
 * Num registro histórico ela fala da procedência do número; num trecho de
 * tempo de descida, do tipo de estudo que o produziu. `transito.json` e
 * `enchentes.json` documentam as duas escalas, e elas não são a mesma —
 * chamar de "imprensa" um trecho derivado do hidrograma da JICA seria mentir
 * sobre a origem do dado.
 */
export const ROTULO_CONFIANCA = {
  alta: 'Fonte oficial ou acadêmica',
  media: 'Imprensa ou compilação',
  baixa: 'Compilação informal ou dado disputado',
} as const

export const ROTULO_CONFIANCA_TRECHO = {
  alta: 'Faixa afirmada pelo próprio estudo técnico',
  media: 'Hidrograma de projeto ou modelo acadêmico citado',
  baixa: 'Estimativa informal, ainda não calibrada',
} as const

export type TipoConfianca = 'registro' | 'trecho'

export const ROTULO_COTA: Record<string, string> = {
  atencao: 'Atenção',
  alerta: 'Alerta',
  inundacao: 'Inundação',
  transbordamento: 'Transbordamento',
}

export function rotuloCota(chave: string): string {
  return ROTULO_COTA[chave] ?? chave.charAt(0).toUpperCase() + chave.slice(1)
}

/**
 * As fontes de tempo real vêm anotadas em `estacoes.json` como
 * `"https://… (DC-01, DC-02)"` — a URL e, entre parênteses, qual estação ou
 * leitura ela traz. Sem separar os dois, a tela mostraria o mesmo domínio duas
 * vezes sem dizer que um link é o nível do rio e o outro é a maré.
 */
export function fonteTempoReal(texto: string): { url: string; rotulo: string } {
  const m = /^(\S+)\s*\((.+)\)\s*$/.exec(texto.trim())
  const url = m ? m[1]! : texto.trim()
  let host = url
  try {
    host = new URL(url).hostname
  } catch {
    // Texto que não é URL: mostra como veio, em vez de sumir com a informação.
  }
  return { url, rotulo: m ? `${host} — ${m[2]!}` : host }
}
