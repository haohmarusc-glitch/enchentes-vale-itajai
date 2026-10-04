/**
 * O lado do aparelho do chat com IA: pergunta ao servidor se está ligado e envia
 * UMA pergunta quando a pessoa aperta "Perguntar à IA". Sem rede no módulo: o
 * `fetch` vem de fora (teste em `cliente.test.ts`).
 */
import { MAXIMO_ANTERIORES, TAMANHO_MAXIMO_ANTERIOR, TAMANHO_MAXIMO_PERGUNTA, type TrocaAnterior } from './nucleo'

export const URL_CHAT_IA = '/api/chat-ia'

type Buscar = (url: string, init?: RequestInit) => Promise<Response>

export interface RespostaDoServidor {
  /** `erro`: a IA não respondeu — o texto explica, e o chat sem IA segue. */
  tipo: 'ia' | 'agora' | 'recusa' | 'sem_resposta' | 'erro'
  texto: string
}

export const AVISO_ENVIO =
  'O botão "Perguntar à IA" envia o texto da pergunta à Anthropic, a empresa da IA Claude, para montar a resposta com os dados deste site. Não escreva nome, endereço ou telefone. A IA pode errar: confira a fonte citada.'

const ERROS: Record<string, string> = {
  limite_do_dia: 'A IA já respondeu o máximo de perguntas de hoje. O chat sem IA continua funcionando.',
  desligado: 'A IA está desligada no momento. O chat sem IA continua funcionando.',
  chave: 'A IA está desligada no momento. O chat sem IA continua funcionando.',
}
const ERRO_GERAL = 'A IA não respondeu agora. Tente de novo em alguns minutos; o chat sem IA continua funcionando.'

/** O servidor tem a IA ligada? Qualquer falha conta como "não". */
export async function iaLigada(buscar: Buscar | undefined): Promise<boolean> {
  if (!buscar) return false
  try {
    const r = await buscar(URL_CHAT_IA, { method: 'GET', cache: 'no-store' })
    if (!r.ok) return false
    const corpo = (await r.json()) as { ligado?: unknown }
    return corpo.ligado === true
  } catch {
    return false
  }
}

/** As últimas trocas com a IA, cortadas no tamanho que o servidor aceita. */
export function anterioresParaEnvio(trocas: TrocaAnterior[]): TrocaAnterior[] {
  return trocas.slice(-MAXIMO_ANTERIORES).map((t) => ({
    pergunta: t.pergunta.slice(0, TAMANHO_MAXIMO_PERGUNTA),
    resposta: t.resposta.length > TAMANHO_MAXIMO_ANTERIOR ? t.resposta.slice(0, TAMANHO_MAXIMO_ANTERIOR - 1) + '…' : t.resposta,
  }))
}

export async function perguntarIA(buscar: Buscar, pergunta: string, anteriores: TrocaAnterior[]): Promise<RespostaDoServidor> {
  const q = pergunta.trim().slice(0, TAMANHO_MAXIMO_PERGUNTA)
  try {
    const r = await buscar(URL_CHAT_IA, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ pergunta: q, anteriores: anterioresParaEnvio(anteriores) }),
    })
    const corpo = (await r.json().catch(() => ({}))) as { tipo?: unknown; texto?: unknown; erro?: unknown }
    if (r.ok && typeof corpo.texto === 'string' && typeof corpo.tipo === 'string' && ['ia', 'agora', 'recusa', 'sem_resposta'].includes(corpo.tipo))
      return { tipo: corpo.tipo as RespostaDoServidor['tipo'], texto: corpo.texto }
    return { tipo: 'erro', texto: (typeof corpo.erro === 'string' && ERROS[corpo.erro]) || ERRO_GERAL }
  } catch {
    return { tipo: 'erro', texto: ERRO_GERAL }
  }
}
