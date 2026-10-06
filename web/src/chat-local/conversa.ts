/**
 * A conversa do chat, uma só para o site inteiro (docs/CHAT-GLOBAL-COMANDOS.md, 06/10/2026).
 *
 * Fica na MEMÓRIA da aba: sobrevive à navegação interna (do Início para o Monitor, de uma cidade para outra),
 * mas não é gravada no aparelho — fechou a aba, acabou. Por isso vive num módulo, e não no estado de um
 * componente: quem pede "mostrar Blumenau" na barra do Início continua a conversa no bloco do Monitor.
 *
 * Também guarda se o painel está aberto e quantos chats de PÁGINA estão montados (/perguntas e a aba
 * Histórico): com um deles na tela, a barra do topo some, e a caixa aparece uma vez só.
 */
import { useSyncExternalStore } from 'react'

export type Correcao = 'correto' | 'nao_era_isso'

export type Msg = {
  papel: 'usuario' | 'assistente'
  texto: string
  sugestoes?: string[]
  /** Resposta do motor local que pode ir à IA: a pergunta que a gerou. */
  paraIA?: string
  /** Veio da IA (rótulo próprio na tela). */
  ia?: boolean
  /** Piloto do classificador: o que foi entendido, e o id para os botões. */
  entendido?: string
  idCorrecao?: string
  corrigido?: Correcao
  /** Atalho para uma página do site ("Ver Blumenau agora →"). */
  link?: { texto: string; para: string }
  /** Resposta de um comando (mapa ou navegação), não do motor de perguntas. */
  comando?: boolean
}

interface Estado {
  msgs: Msg[]
  aberto: boolean
  chatsDePagina: number
  ocupado: boolean
}

let estado: Estado = { msgs: [], aberto: false, chatsDePagina: 0, ocupado: false }
const ouvintes = new Set<() => void>()

function mudar(parcial: Partial<Estado>): void {
  estado = { ...estado, ...parcial }
  ouvintes.forEach((f) => f())
}

function assinar(f: () => void): () => void {
  ouvintes.add(f)
  return () => ouvintes.delete(f)
}

export function useConversa(): Estado {
  return useSyncExternalStore(assinar, () => estado, () => estado)
}

export function lerConversa(): Estado {
  return estado
}

export function mudarMsgs(f: Msg[] | ((atual: Msg[]) => Msg[])): void {
  mudar({ msgs: typeof f === 'function' ? f(estado.msgs) : f })
}

export function acrescentar(...novas: Msg[]): void {
  mudar({ msgs: [...estado.msgs, ...novas] })
}

export function limparConversa(): void {
  mudar({ msgs: [] })
}

export function abrirPainel(aberto: boolean): void {
  if (estado.aberto !== aberto) mudar({ aberto })
}

export function marcarOcupado(ocupado: boolean): void {
  if (estado.ocupado !== ocupado) mudar({ ocupado })
}

/** Um chat de página montou: a barra do topo some enquanto ele estiver na tela. Devolve a desmontagem. */
export function registrarChatDePagina(): () => void {
  mudar({ chatsDePagina: estado.chatsDePagina + 1 })
  return () => mudar({ chatsDePagina: Math.max(0, estado.chatsDePagina - 1) })
}
