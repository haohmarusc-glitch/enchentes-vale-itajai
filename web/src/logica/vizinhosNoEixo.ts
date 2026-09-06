/**
 * Quem está acima e abaixo desta cidade NO EIXO, e quanto a água leva.
 *
 * É a pergunta que o painel da cidade no Monitor não respondia: "a água que
 * está em Rio do Sul chega aqui quando?". A tela da cidade já sabia; o mesmo
 * cálculo agora mora aqui, puro, para as duas telas concordarem.
 *
 * Só se afirma vizinho DENTRO do eixo (o tronco no Açu, a fila no Mirim).
 * Cabeceira e afluente ficam com `noEixo: false` — a cheia deles não é a mesma
 * que desce o rio principal, e encadear tempo por eles daria resultado errado.
 */
import { caminho, faixaHoras } from './transito'
import type { Trecho } from '../dados/tipos'

export interface VizinhoNoEixo {
  id: string
  nome: string
  /** "14–17 h" — ou null quando o trecho não foi levantado. */
  janela: string | null
  confianca: 'alta' | 'media' | 'baixa' | null
}

export interface Vizinhos {
  noEixo: boolean
  montante: VizinhoNoEixo | null
  jusante: VizinhoNoEixo | null
}

export function vizinhosNoEixo(
  rioId: string,
  cidadeId: string,
  eixo: readonly string[],
  cidades: readonly { id: string; nome: string }[],
  trechos: readonly Trecho[],
): Vizinhos {
  const i = eixo.indexOf(cidadeId)
  if (i < 0) return { noEixo: false, montante: null, jusante: null }
  const nome = (id: string) => cidades.find((c) => c.id === id)?.nome ?? id
  const vizinho = (de: string, para: string, id: string): VizinhoNoEixo => {
    const c = caminho(trechos as Trecho[], rioId, de, para)
    return { id, nome: nome(id), janela: c ? faixaHoras(c) : null, confianca: c?.confianca ?? null }
  }
  const acima = i > 0 ? eixo[i - 1]! : null
  const abaixo = i < eixo.length - 1 ? eixo[i + 1]! : null
  return {
    noEixo: true,
    montante: acima ? vizinho(acima, cidadeId, acima) : null,
    jusante: abaixo ? vizinho(cidadeId, abaixo, abaixo) : null,
  }
}
