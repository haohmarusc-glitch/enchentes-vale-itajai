import { useMemo } from 'react'
import { comReferenciaAscurra } from './referenciaAscurra'
import { leituraDaCidade, leiturasDaCidade, useTempoReal, type EstadoTempoReal, type LeituraAoVivo } from './tempoReal'
import { useNivelSc, type BrutoEstadual, type NivelSc } from './nivelSc'
import { serieDaCidade, useSerieRecente, type EstadoSerie, type PontoSerie } from './serie'
import type { Cidade } from './tipos'
import { faixaDaCidade, type Faixa } from '../logica/tempoReal'

/**
 * Tudo o que é ao vivo, numa chamada só, para as telas da versão 2. Um único
 * "agora" por atualização: todos os cartões contam a idade a partir do mesmo
 * instante — dois relógios na mesma tela dariam duas idades para a mesma
 * leitura.
 */
export interface AoVivo {
  tempoReal: EstadoTempoReal
  nivelSc: NivelSc
  serie: EstadoSerie
  agora: Date
}

export function useAoVivo(): AoVivo {
  const original = useTempoReal()
  const nivelSc = useNivelSc()
  const tempoReal = useMemo(() => comReferenciaAscurra(original, nivelSc), [original, nivelSc])
  const serie = useSerieRecente()
  const agora = useMemo(() => new Date(), [tempoReal])
  return { tempoReal, nivelSc, serie, agora }
}

/** O estado de UMA cidade, como os cartões precisam. */
export interface EstadoDaCidade {
  /** A leitura municipal, com cota (null quando não há, ou quando há várias réguas). */
  leitura: LeituraAoVivo | null
  /** Todas as leituras da cidade (Itajaí tem várias réguas). */
  todas: LeituraAoVivo[]
  varias: boolean
  faixa: Faixa
  /** Nível bruto da rede estadual, quando não há régua municipal (sem cor). */
  bruto: BrutoEstadual | null
  serie: PontoSerie[]
}

export function estadoDaCidade(cidade: Cidade, rioId: string, v: AoVivo): EstadoDaCidade {
  const leitura = leituraDaCidade(v.tempoReal, rioId, cidade.id)
  const todas = leiturasDaCidade(v.tempoReal, rioId, cidade.id)
  const varias = leitura === null && todas.length > 1
  const bruto = leitura === null && todas.length <= 1 ? v.nivelSc.get(cidade.id) ?? null : null
  return {
    leitura,
    todas,
    varias,
    faixa: faixaDaCidade(cidade, leitura, varias, v.agora),
    bruto,
    serie: serieDaCidade(v.serie, rioId, cidade.id),
  }
}
