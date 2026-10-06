/**
 * "ATUALIZAR AS LEITURAS" (8ª entrega dos comandos do chat, docs/CHAT-GLOBAL-COMANDOS.md).
 *
 * As telas já buscam o tempo real a cada 5 minutos. Este evento só antecipa a próxima busca dos três arquivos
 * (leituras, rede estadual e série recente) em todas as telas abertas; não muda o intervalo nem o que se faz
 * com a resposta. Não força a COLETA: ela roda no servidor, no ritmo dela, e pode ainda não ter leitura nova.
 * Um pedido por 30 s, para um dedo nervoso durante a chuva não virar uma rajada de buscas.
 */
export const EVENTO_ATUALIZAR = 'enchentes:atualizar'
export const MIN_ENTRE_PEDIDOS_MS = 30_000

let ultimoPedido = -Infinity

/** Pede a busca; devolve false quando houve outro pedido há menos de 30 s (nada é disparado). */
export function pedirAtualizacao(agora: number = Date.now()): boolean {
  if (agora - ultimoPedido < MIN_ENTRE_PEDIDOS_MS) return false
  ultimoPedido = agora
  if (typeof window !== 'undefined') window.dispatchEvent(new Event(EVENTO_ATUALIZAR))
  return true
}

/** Para os ganchos de tempo real: chama `f` a cada pedido. Devolve a função que para de ouvir. */
export function ouvirAtualizacao(f: () => void): () => void {
  if (typeof window === 'undefined') return () => {}
  window.addEventListener(EVENTO_ATUALIZAR, f)
  return () => window.removeEventListener(EVENTO_ATUALIZAR, f)
}

/** Só para os testes. */
export function zerarPedidos(): void {
  ultimoPedido = -Infinity
}
