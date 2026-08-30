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

export const ROTULO_CONFIANCA = {
  alta: 'Fonte oficial ou acadêmica',
  media: 'Imprensa ou compilação',
  baixa: 'Compilação informal ou dado disputado',
} as const

export const ROTULO_COTA: Record<string, string> = {
  atencao: 'Atenção',
  alerta: 'Alerta',
  inundacao: 'Inundação',
  transbordamento: 'Transbordamento',
}

export function rotuloCota(chave: string): string {
  return ROTULO_COTA[chave] ?? chave.charAt(0).toUpperCase() + chave.slice(1)
}
