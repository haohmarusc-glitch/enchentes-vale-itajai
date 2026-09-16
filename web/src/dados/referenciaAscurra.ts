import type { EstadoTempoReal, LeituraAoVivo } from './tempoReal'
import type { NivelSc } from './nivelSc'

/** C18 confirma somente esta estação. Não promove nenhuma outra leitura bruta. */
export function comReferenciaAscurra(estado: EstadoTempoReal, nivelSc: NivelSc): EstadoTempoReal {
  // Desde 14/09/2026 o back-end (scripts/coleta_estadual_com_cota.py) já manda a
  // DCSC-00003 dentro de `leituras`, com `codigo`. Quando ela vem, esta exceção
  // não faz nada: duplicá-la seria "duas réguas em Ascurra" e o site apagaria a
  // cor. Só age quando o ultimo.json não trouxe a régua (fallback pelo bruto).
  if (estado.leituras.some((x) => x.codigo === 'DCSC-00003' && x.cidade === 'ascurra')) return estado
  const l = nivelSc.get('ascurra')
  if (!l || l.cidade !== 'ascurra' || l.codigo !== 'DCSC-00003' || !l.medidoEm ||
      !Number.isFinite(l.medidoEm.getTime()) || !Number.isFinite(l.nivelBrutoM) || l.nivelBrutoM <= 0 || l.nivelBrutoM >= 30) return estado
  const leitura: LeituraAoVivo = { codigo: l.codigo, estacao: 'DCSC-00003 · Ponte do Beber (C18)',
    cidade: 'ascurra', rio: 'itajai-acu', nivel_m: l.nivelBrutoM, medidoEm: l.medidoEm, resgateDe: null }
  // Se outra régua vier da fonte, continua separada; não presume identidade.
  return { ...estado, leituras: [...estado.leituras.filter(x => x.codigo !== l.codigo), leitura] }
}
