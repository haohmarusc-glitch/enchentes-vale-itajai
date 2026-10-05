/**
 * Correção da prova do PILOTO do classificador (docs/PILOTO-CLASSIFICADOR.md) e o caminho
 * completo que a tela faz: barreira → motor → (não entendeu ou palpitou) → classificador →
 * decisão → texto do motor. O executor (`web/ferramentas/prova-classificador.ts`) e os
 * testes usam as mesmas funções da tela, sem copiar regra.
 */
import { norm, pedeAgora, responder, TEXTO_ALERTA, type Dados } from '../../chat-local/motor'
import { CONFIANCA_MINIMA_PADRAO, decidir, type Decisao, type SaidaClassificador } from '../classificador'
import { mensagemDoPiloto, type Origem } from '../clienteClassificador'
import type { CasoClassificador } from './casosClassificador'

/** Uma classificação: o JSON do modelo (ou null), ou exceção para falha da API. */
export type Classificar = (pergunta: string) => Promise<unknown>

/** O que o classificador perfeito devolveria para o caso (o simulador usa). */
export function gabaritoDe(caso: CasoClassificador): SaidaClassificador {
  const vazio: SaidaClassificador = {
    intencao: 'nao_sei',
    cidade: null,
    cidade2: null,
    rio: null,
    ano: null,
    ano_final: null,
    mes: null,
    nivel_m: null,
    quantidade: null,
    rua: null,
    situacao_atual: false,
    confianca: 0.95,
    motivo_curto: 'gabarito',
    nao_sei: false,
  }
  const e = caso.espera
  if (e.tipo === 'agora') return { ...vazio, situacao_atual: true }
  if (e.tipo === 'nao_sei') return { ...vazio, nao_sei: true }
  if (e.tipo === 'faltou') return { ...vazio, intencao: e.intencao, ...(e.intencao === 'transito' ? { cidade2: 'blumenau' } : {}) }
  const { tipo: _t, rua, ...campos } = e
  return { ...vazio, ...campos, rua: rua ? rua.source.replace(/\\/g, '') : null }
}

export type Desfecho = 'certo' | 'errou' | 'nao_respondeu' | 'liberou'

/**
 * Nota de um caso da bateria:
 *  - certo: a decisão esperada (no "não sei", aceita também o aviso do presente);
 *  - errou: respondeu (ou pediu parâmetro) com outra intenção ou outro parâmetro — adivinhou;
 *  - nao_respondeu: ficou no "não consegui interpretar" quando havia o que responder (seguro);
 *  - liberou: pergunta sobre o presente que NÃO virou o aviso e foi respondida (grave).
 */
export function notaClassificacao(caso: CasoClassificador, d: Decisao): { acerto: 0 | 1; desfecho: Desfecho } {
  const e = caso.espera
  const certo = { acerto: 1 as const, desfecho: 'certo' as const }
  const seguro = { acerto: 0 as const, desfecho: 'nao_respondeu' as const }
  const errou = { acerto: 0 as const, desfecho: 'errou' as const }
  if (e.tipo === 'agora') return d.tipo === 'agora' ? certo : d.tipo === 'nao_sei' ? seguro : { acerto: 0, desfecho: 'liberou' }
  if (e.tipo === 'nao_sei') return d.tipo === 'nao_sei' || d.tipo === 'agora' ? certo : errou
  if (e.tipo === 'faltou') {
    if (d.tipo === 'faltou') return d.classificacao.intencao === e.intencao && e.faltam.every((p) => d.faltam.includes(p)) ? certo : errou
    return d.tipo === 'ok' ? errou : seguro
  }
  if (d.tipo !== 'ok') return seguro
  const c = d.classificacao
  if (c.intencao !== e.intencao) return errou
  for (const k of ['cidade', 'cidade2', 'ano', 'ano_final', 'mes', 'nivel_m', 'quantidade'] as const) if (e[k] !== undefined && e[k] !== c[k]) return errou
  if (e.rua && !(c.rua && e.rua.test(norm(c.rua)))) return errou
  return certo
}

export interface PassoPipeline {
  texto: string
  /** A pergunta foi ao classificador (o motor não entendeu ou palpitou). */
  classificou: boolean
  origem: Origem | null
  /** "erro" quando a chamada falhou (rede, tempo, API). */
  decisao: Decisao | 'erro' | null
  bruto: unknown
}

/** O caminho da tela com o piloto ligado, para uma pergunta. */
export async function respostaComPiloto(pergunta: string, d: Dados, classificar: Classificar, opcoes = { confiancaMinima: CONFIANCA_MINIMA_PADRAO, anoAtual: 2026 }): Promise<PassoPipeline> {
  const r = responder(pergunta, d)
  if (pedeAgora(pergunta)) return { texto: TEXTO_ALERTA, classificou: false, origem: null, decisao: null, bruto: null }
  const origem: Origem | null = r.intencao === 'nao_entendi' ? 'nao_entendi' : r.palpite ? 'palpite' : null
  if (!origem) return { texto: r.texto, classificou: false, origem: null, decisao: null, bruto: null }
  let bruto: unknown = null
  try {
    bruto = await classificar(pergunta)
  } catch {
    return { texto: mensagemDoPiloto({ erro: true }, d).texto, classificou: true, origem, decisao: 'erro', bruto: null }
  }
  const { decisao } = decidir(pergunta, bruto, d, opcoes)
  return { texto: mensagemDoPiloto({ id: null, decisao }, d).texto, classificou: true, origem, decisao, bruto }
}
