import type { EstadoDaCidade } from '../dados/usarAoVivo'
import { frescorDaCidade, idadeMin } from './tempoReal'

/**
 * O que a linha de uma cidade (lista do rio, cartões do início) diz embaixo do nome.
 *
 * Auditoria de 03/10/2026, item 5: Ilhota aparecia como "sem leitura recente"
 * com 9,51 m da rede estadual (DCSC-00030) medidos 15 minutos antes, porque a
 * linha só mostrava o número estadual quando a Defesa Civil de SC publica faixa
 * para a estação — e para a de Ilhota ela não publica (`ativo=false`).
 * "Não há leitura" e "há leitura estadual sem faixa" são coisas diferentes.
 *
 * O número estadual continua fora de `faixa` (regra da faixa estadual do
 * CLAUDE.md): aqui ele só é texto, e frase, WhatsApp e aviso não leem isto.
 */
export type SituacaoDaLinha =
  | { tipo: 'municipal'; idade: number }
  | { tipo: 'varias'; quantas: number }
  | { tipo: 'estadual'; nivel: number; idade: number; comFaixa: boolean }
  | { tipo: 'sem-leitura' }

export function situacaoDaLinha(estado: EstadoDaCidade, cidadeId: string, agora: Date): SituacaoDaLinha {
  const { leitura } = estado
  if (leitura?.medidoEm) {
    const idade = idadeMin(leitura.medidoEm, agora)
    if (frescorDaCidade(idade, cidadeId) !== 'velha') return { tipo: 'municipal', idade }
  }
  if (estado.varias) return { tipo: 'varias', quantas: estado.todas.length }
  const e = estado.estadual
  if (e?.medidoEm && Number.isFinite(e.medidoEm.getTime())) {
    const idade = idadeMin(e.medidoEm, agora)
    if (frescorDaCidade(idade, cidadeId) !== 'velha') {
      return { tipo: 'estadual', nivel: e.nivelBrutoM, idade, comFaixa: estado.faixaEstadual !== null }
    }
  }
  return { tipo: 'sem-leitura' }
}
