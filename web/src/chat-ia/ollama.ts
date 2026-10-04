/**
 * O chat com IA rodando num modelo LOCAL pelo Ollama (ollama.com) — só para a prova
 * (docs/PROVA-CHAT-IA.md, "Rodar com o Ollama"). O site NÃO usa isto: o /api/chat-ia
 * continua na Anthropic.
 *
 * É o mesmo chat, trocando só quem responde: a mesma barreira do presente, as mesmas
 * instruções (`montarSistema`), as mesmas ferramentas (`ferramentas`, convertidas para
 * o formato do Ollama) e o mesmo executor (`executar`, que lê os dados do site).
 *
 * Fala com a API nativa do Ollama, `POST /api/chat`, com `tools` e `stream: false`.
 * Sem rede no módulo: o `fetch` vem de fora (teste em `ollama.test.ts`).
 */
import { TEXTO_ALERTA, pedeAgora } from '../chat-local/motor'
import {
  MAXIMO_RODADAS,
  TEXTO_SEM_RESPOSTA,
  executar,
  ferramentas,
  mensagemInicial,
  montarSistema,
  type ObterDados,
  type PedidoIA,
  type RespostaIA,
} from './nucleo'

export const URL_OLLAMA_PADRAO = 'http://localhost:11434'
/**
 * Janela de contexto pedida ao Ollama. O padrão dele (2–4 mil tokens) não cabe nem as
 * instruções + ferramentas (~3 mil) + um resultado grande (a lista de picos de Blumenau
 * tem ~11 mil): a conversa seria cortada em silêncio. 16 mil cabe; mais custa memória.
 */
export const CONTEXTO_PADRAO = 16_384

type Buscar = (url: string, init: RequestInit) => Promise<Response>

/** Mensagem no formato do Ollama. `tool_name` é aceito nas versões novas e ignorado nas velhas. */
export interface MensagemOllama {
  role: 'system' | 'user' | 'assistant' | 'tool'
  content: string
  tool_calls?: ChamadaOllama[]
  tool_name?: string
}

export interface ChamadaOllama {
  function: { name: string; arguments: unknown }
}

interface RespostaOllama {
  model?: string
  message?: { role?: string; content?: string; tool_calls?: ChamadaOllama[] }
  done_reason?: string
  prompt_eval_count?: number
  eval_count?: number
  error?: string
}

export interface OpcoesOllama {
  /** Nome do modelo no Ollama, ex.: "qwen2.5:3b". */
  modelo: string
  url?: string
  contexto?: number
  buscar?: Buscar
}

/** Uma rodada, para o executor da prova montar a conversa e somar os tokens. */
export interface RodadaOllama {
  pedido: { model: string; messages: MensagemOllama[] }
  resposta: RespostaOllama
}

/** As ferramentas do chat no formato de função do Ollama (o `strict` da Anthropic não existe lá). */
export function ferramentasOllama(...args: Parameters<typeof ferramentas>) {
  return ferramentas(...args).map((t) => ({
    type: 'function' as const,
    function: { name: t.name, description: t.description ?? '', parameters: t.input_schema },
  }))
}

/** Modelos com raciocínio (Qwen3, DeepSeek-R1) podem mandar o rascunho em <think>…</think>. */
export const semPensamento = (texto: string) => texto.replace(/<think>[\s\S]*?<\/think>/g, '').trim()

/**
 * Modelo pequeno às vezes escreve a chamada de ferramenta como TEXTO, em vez de usar
 * `tool_calls`: `{"name": "consultar_motor", "arguments": {...}}`. Reconhece só esse
 * formato, com nome de ferramenta conhecido; o resto é resposta.
 */
export function chamadaEmTexto(texto: string, nomes: Set<string>): ChamadaOllama | null {
  const t = semPensamento(texto).replace(/^```(json)?\s*|\s*```$/g, '')
  if (!t.startsWith('{') || !t.endsWith('}')) return null
  try {
    const o = JSON.parse(t) as { name?: unknown; arguments?: unknown; parameters?: unknown }
    if (typeof o.name === 'string' && nomes.has(o.name)) return { function: { name: o.name, arguments: o.arguments ?? o.parameters ?? {} } }
  } catch {
    /* não era JSON: é resposta */
  }
  return null
}

/** Argumentos chegam como objeto (Ollama novo) ou como texto JSON (alguns modelos). */
export function argumentos(a: unknown): unknown {
  if (typeof a !== 'string') return a ?? {}
  try {
    return JSON.parse(a)
  } catch {
    return {}
  }
}

/** Responde uma pergunta com um modelo do Ollama. Erro de rede/HTTP sobe como exceção. */
export async function responderComOllama(
  pedido: PedidoIA,
  obter: ObterDados,
  opcoes: OpcoesOllama,
  rodadas: RodadaOllama[] = [],
): Promise<RespostaIA> {
  if (pedeAgora(pedido.pergunta)) return { tipo: 'agora', texto: TEXTO_ALERTA }

  const buscar: Buscar = opcoes.buscar ?? ((url, init) => fetch(url, init))
  const url = `${(opcoes.url ?? URL_OLLAMA_PADRAO).replace(/\/+$/, '')}/api/chat`
  const base = await obter('')
  const tools = ferramentasOllama(base)
  const nomes = new Set(tools.map((t) => t.function.name))
  const messages: MensagemOllama[] = [
    { role: 'system', content: montarSistema(base) },
    { role: 'user', content: mensagemInicial(pedido) },
  ]
  const uso = { modelo: `ollama:${opcoes.modelo}`, rodadas: 0, entrada: 0, cache_criado: 0, cache_lido: 0, saida: 0 }

  while (uso.rodadas < MAXIMO_RODADAS) {
    const corpo = {
      model: opcoes.modelo,
      messages: structuredClone(messages),
      tools,
      stream: false,
      options: { num_ctx: opcoes.contexto ?? CONTEXTO_PADRAO, temperature: 0 },
    }
    const http = await buscar(url, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(corpo) })
    const r = (await http.json().catch(() => ({ error: `resposta não-JSON (HTTP ${http.status})` }))) as RespostaOllama
    if (!http.ok || r.error) throw new Error(`Ollama: ${r.error ?? `HTTP ${http.status}`}`)
    rodadas.push({ pedido: { model: corpo.model, messages: corpo.messages }, resposta: r })
    uso.rodadas++
    uso.entrada += r.prompt_eval_count ?? 0
    uso.saida += r.eval_count ?? 0
    if (r.model) uso.modelo = `ollama:${r.model}`

    const conteudo = r.message?.content ?? ''
    const chamadas = r.message?.tool_calls?.length ? r.message.tool_calls : [chamadaEmTexto(conteudo, nomes)].filter((c): c is ChamadaOllama => c !== null)
    if (chamadas.length) {
      messages.push({ role: 'assistant', content: conteudo, tool_calls: chamadas })
      for (const c of chamadas) {
        const { conteudo: resultado, erro } = await executar(c.function.name, argumentos(c.function.arguments), obter, base)
        messages.push({ role: 'tool', content: erro ? `ERRO: ${resultado}` : resultado, tool_name: c.function.name })
      }
      continue
    }
    const texto = semPensamento(conteudo)
    return texto ? { tipo: 'ia', texto, uso } : { tipo: 'sem_resposta', texto: TEXTO_SEM_RESPOSTA, uso }
  }
  return { tipo: 'sem_resposta', texto: TEXTO_SEM_RESPOSTA, uso }
}
