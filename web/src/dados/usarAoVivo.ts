import { useMemo } from 'react'
import { comReferenciaAscurra } from './referenciaAscurra'
import { leituraDaCidade, leiturasDaCidade, useTempoReal, type EstadoTempoReal, type LeituraAoVivo } from './tempoReal'
import { useNivelSc, type BrutoEstadual, type NivelSc } from './nivelSc'
import { serieDaCidade, useSerieRecente, type EstadoSerie, type PontoSerie } from './serie'
import type { Cidade } from './tipos'
import { faixaDaCidade, frescorDaCidade, idadeMin, type Faixa } from '../logica/tempoReal'

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
  /**
   * A leitura da rede estadual da cidade, haja ou não régua municipal — para
   * dizer o nível de agora quando a municipal está velha (Indaial).
   */
  estadual: BrutoEstadual | null
  /**
   * A faixa que a PRÓPRIA Defesa Civil de SC publica para a estação da cidade,
   * só quando não há leitura municipal de agora e a estadual é fresca. Nunca
   * vem de cota nossa, nunca dispara aviso, e a tela diz de quem é.
   */
  faixaEstadual: Faixa | null
  serie: PontoSerie[]
}

/**
 * A faixa estadual que pode aparecer: publicada pela fonte, com carimbo e
 * fresca. Mesmo critério do mapa do Monitor (`faixaEstadualDe`).
 */
export function faixaDaRedeEstadual(bruto: BrutoEstadual | null, cidadeId: string, agora: Date): Faixa | null {
  if (!bruto?.faixaEstadual || !bruto.medidoEm || !Number.isFinite(bruto.medidoEm.getTime())) return null
  if (frescorDaCidade(idadeMin(bruto.medidoEm, agora), cidadeId) === 'velha') return null
  return bruto.faixaEstadual
}

export function estadoDaCidade(cidade: Cidade, rioId: string, v: AoVivo): EstadoDaCidade {
  const leitura = leituraDaCidade(v.tempoReal, rioId, cidade.id)
  const todas = leiturasDaCidade(v.tempoReal, rioId, cidade.id)
  const varias = leitura === null && todas.length > 1
  const estadual = v.nivelSc.get(cidade.id) ?? null
  const bruto = leitura === null && todas.length <= 1 ? estadual : null
  const faixa = faixaDaCidade(cidade, leitura, varias, v.agora)
  // A municipal manda: a estadual só aparece quando a municipal não diz nada de agora.
  const municipalDeAgora =
    leitura?.medidoEm != null && frescorDaCidade(idadeMin(leitura.medidoEm, v.agora), cidade.id) !== 'velha'
  return {
    leitura,
    todas,
    varias,
    faixa,
    bruto,
    estadual,
    faixaEstadual: varias || municipalDeAgora ? null : faixaDaRedeEstadual(estadual, cidade.id, v.agora),
    serie: serieDaCidade(v.serie, rioId, cidade.id),
  }
}
