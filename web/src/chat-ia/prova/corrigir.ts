/**
 * Corretor da prova do chat com IA: verificação por padrões, sem outra IA julgando.
 * Três notas por resposta, cada uma 0 ou 1:
 *  - `fatos`:  casou ao menos um padrão de cada grupo de `deve`;
 *  - `regras`: não casou nenhum padrão de `nao_deve`;
 *  - `acerto`: as duas (a nota principal).
 */
import type { CasoProva } from './casos'

/** Sem acento, minúsculo, vírgula decimal → ponto, espaços simples. */
export function normalizar(texto: string): string {
  return texto
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/(\d),(\d)/g, '$1.$2')
    .replace(/\s+/g, ' ')
    .trim()
}

export interface Nota {
  acerto: number
  fatos: number
  regras: number
}

export interface Correcao {
  grade: Nota
  explanation: { acerto: string }
}

export function corrigir(caso: CasoProva, resposta: string): Correcao {
  const t = normalizar(resposta)
  const faltou = caso.deve.filter((grupo) => !grupo.some((r) => r.test(t)))
  const quebrou = caso.nao_deve.filter((r) => r.test(t))
  const fatos = faltou.length === 0 ? 1 : 0
  const regras = quebrou.length === 0 ? 1 : 0
  const motivos = [
    ...faltou.map((g) => `faltou: ${g.map(String).join(' ou ')}`),
    ...quebrou.map((r) => `regra quebrada: ${String(r)}`),
  ]
  return { grade: { acerto: fatos && regras ? 1 : 0, fatos, regras }, explanation: { acerto: motivos.join('; ') || 'ok' } }
}
