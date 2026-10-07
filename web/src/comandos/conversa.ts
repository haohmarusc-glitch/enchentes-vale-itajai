/**
 * 19ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): o contexto da CONVERSA, separado do da TELA.
 *
 * O handoff de qualidade (docs/HANDOFF-QUALIDADE-CHAT-2026-10-07.md, "Contexto de conversa") pede três coisas:
 *  1. separar o que a tela tem aberto do que a conversa já disse, e dizer de onde veio a cidade;
 *  2. uma entidade dita no pedido vence qualquer referência implícita;
 *  3. contexto não transforma pergunta em ação: "mostre Blumenau" → "e Gaspar?" não navega por suposição — pergunta.
 *
 * Aqui mora a memória mínima da conversa (a última cidade citada e o último pedido) e a decisão sobre uma continuação
 * ("e Gaspar?", "e ontem?", "e com 9 m?"): refazer e responder, refazer mas CONFIRMAR antes (quando mudaria a tela), ou
 * perguntar. Nada disso vai ao aparelho nem ao servidor: é só a lista de mensagens desta aba.
 */
import { MUDA_A_TELA } from './executar'
import { interpretar } from './interpretar'
import { continuar, type Continuacao } from './continuar'
import { normalizar } from './normalizar'
import type { NomeConhecido } from './corrigir'
import type { Catalogo, Contexto } from './tipos'

/** O que a conversa lembra: só o necessário para resolver "aqui", "quanto falta?" e "e Gaspar?". */
export interface MemoriaDaConversa {
  /** A última cidade citada pela pessoa (ou entendida numa continuação), ou null. */
  cidade: string | null
  /** O último pedido da pessoa, como foi entendido ("Entendi como: …" vale mais do que o texto digitado). */
  ultimoPedido: string | null
}

/** Os textos da pessoa, do mais antigo ao mais novo, já com o "entendido como" quando houver. */
export function memoriaDaConversa(pedidos: readonly string[], nomes: readonly NomeConhecido[]): MemoriaDaConversa {
  let cidade: string | null = null
  for (const p of pedidos) {
    const c = cidadeCitada(p, nomes)
    if (c) cidade = c
  }
  return { cidade, ultimoPedido: pedidos.length ? pedidos[pedidos.length - 1]! : null }
}

/** A ÚNICA cidade do cadastro citada no texto (nome inteiro, palavra a palavra); duas ou nenhuma → null. */
export function cidadeCitada(texto: string, nomes: readonly NomeConhecido[]): string | null {
  const t = ` ${normalizar(texto)} `
  const achadas = new Set<string>()
  for (const n of [...nomes].sort((a, b) => normalizar(b.nome).length - normalizar(a.nome).length)) {
    const nome = normalizar(n.nome)
    if (t.includes(` ${nome} `) || t.includes(` ${normalizar(n.id)} `)) {
      achadas.add(n.id)
    }
  }
  // "Itajaí-Açu" e "Itajaí-Mirim" são rios: "itajai" dentro deles não é a cidade.
  if (achadas.has('itajai') && /\bitajai (?:acu|mirim)\b/.test(t) && !/\bitajai\b(?! (?:acu|mirim))/.test(t)) achadas.delete('itajai')
  return achadas.size === 1 ? [...achadas][0]! : null
}

/**
 * O contexto que vai ao leitor e ao executor: a tela como está, mais a cidade da conversa. A da tela vence a da conversa
 * (a pessoa está olhando para ela); a dita no pedido vence as duas (o executor lê `passo.cidadeId` primeiro).
 */
export function contextoComConversa(tela: Contexto, memoria: MemoriaDaConversa): Contexto {
  return { ...tela, cidadeDaConversa: tela.cidadeAtual ? null : memoria.cidade }
}

export type Decisao =
  /** Refaz o pedido anterior com a troca e responde ("Entendi como: …"). */
  | { tipo: 'refazer'; texto: string; troca: Exclude<Continuacao, null | { erro: string }>['troca'] }
  /** Refaria um pedido que MUDA A TELA: pergunta antes, com a frase pronta para tocar. */
  | { tipo: 'confirmar'; texto: string; pergunta: string; sugestoes: string[] }
  /** Era continuação, mas não há como trocar: pergunta. */
  | { tipo: 'perguntar'; texto: string; sugestoes: string[] }
  /** Não é continuação: segue o caminho normal (leitor, depois motor). */
  | null

/**
 * A decisão sobre uma possível continuação. `ctx` é o contexto da tela (com a cidade da conversa), para saber se o
 * pedido refeito mudaria a tela.
 */
export function decidirContinuacao(texto: string, memoria: MemoriaDaConversa, nomes: readonly NomeConhecido[], cat: Catalogo, ctx: Contexto): Decisao {
  const c = continuar(texto, memoria.ultimoPedido, nomes)
  if (!c) return null
  if ('erro' in c) return { tipo: 'perguntar', texto: c.erro, sugestoes: c.sugestoes }
  if (c.troca === 'repetir') return { tipo: 'refazer', texto: c.texto, troca: c.troca }
  const r = interpretar(c.texto, cat, ctx)
  if (r && r.tipo === 'comandos' && r.passos.some((p) => MUDA_A_TELA.has(p.tipo))) {
    return {
      tipo: 'confirmar',
      texto: c.texto,
      pergunta: `Entendi como "${c.texto}", que muda a tela. É isso? Toque na sugestão para confirmar; nada foi feito.`,
      sugestoes: [c.texto],
    }
  }
  return { tipo: 'refazer', texto: c.texto, troca: c.troca }
}
