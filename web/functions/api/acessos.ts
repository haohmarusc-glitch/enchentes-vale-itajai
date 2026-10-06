/**
 * Registro de acessos ao site e a lista para o admin (pedido do Jefferson, 06/10/2026).
 *
 * QUEM ENTRA. O site fica atrás do Cloudflare Access, que põe o e-mail de quem passou pelo login em
 * todo pedido (`emailDoAcesso`). O `_middleware.ts` chama `registrarAcesso` a cada ABERTURA de página
 * (pedido de HTML, não cada arquivo), e o registro guarda por e-mail: primeiro acesso, último acesso,
 * em quantos dias a pessoa entrou e o último dia. Nada além disso: nem IP, nem página, nem aparelho.
 *
 * QUANTO ESCREVE. No máximo uma escrita a cada `INTERVALO_MIN` minutos por pessoa — o KV gratuito
 * aceita mil escritas por dia. Cada registro expira em `RETENCAO_DIAS` sem novo acesso.
 *
 * QUEM VÊ. `GET /api/acessos` responde só para os e-mails de `ADMIN_EMAILS` (variável do Pages,
 * separados por vírgula). Para qualquer outro — inclusive quem está logado no site —, 404, como se a
 * página não existisse. Sem a variável, ninguém vê.
 *
 * Falha aqui NUNCA derruba o site: o registro roda depois da resposta (`waitUntil`) e engole erro.
 */
import { emailDoAcesso } from './chat-ia'

export const PREFIXO = 'acesso|'
export const INTERVALO_MIN = 15
export const RETENCAO_DIAS = 90
export const AGORA_MIN = 15

export interface RegistroAcesso {
  email: string
  primeiro: string // ISO, UTC
  ultimo: string // ISO, UTC
  dias: number // dias distintos (de Brasília) com acesso
  ultimo_dia: string // AAAA-MM-DD, Brasília
}

/** O KV com o que este arquivo usa: o registro vai também no `metadata`, para a lista não ler um a um. */
export interface ArmazemAcessos {
  get(chave: string): Promise<string | null>
  put(chave: string, valor: string, opcoes?: { expirationTtl?: number; metadata?: unknown }): Promise<void>
  list(opcoes: { prefix: string; cursor?: string }): Promise<{
    keys: { name: string; metadata?: unknown }[]
    list_complete: boolean
    cursor?: string
  }>
}

export interface Ambiente {
  CHAT_IA?: ArmazemAcessos
  ADMIN_EMAILS?: string
}

/** Dia no calendário de Brasília (UTC−3, sem horário de verão desde 2019). */
export function diaDeBrasilia(d: Date): string {
  return new Date(d.getTime() - 3 * 3600_000).toISOString().slice(0, 10)
}

/** Abertura de página: GET de HTML fora de /api. Arquivos (JS, JSON, imagens) não contam. */
export function eAberturaDePagina(pedido: Request): boolean {
  if (pedido.method !== 'GET') return false
  const caminho = new URL(pedido.url).pathname
  if (caminho.startsWith('/api/')) return false
  const aceita = pedido.headers.get('accept') ?? ''
  return aceita.includes('text/html')
}

/** O registro novo, ou null quando a última escrita é recente demais para escrever de novo. */
export function proximoRegistro(atual: RegistroAcesso | null, email: string, agora: Date): RegistroAcesso | null {
  const iso = agora.toISOString()
  const dia = diaDeBrasilia(agora)
  if (!atual) return { email, primeiro: iso, ultimo: iso, dias: 1, ultimo_dia: dia }
  if (agora.getTime() - Date.parse(atual.ultimo) < INTERVALO_MIN * 60_000) return null
  return { ...atual, ultimo: iso, dias: atual.dias + (atual.ultimo_dia === dia ? 0 : 1), ultimo_dia: dia }
}

export async function registrarAcesso(pedido: Request, amb: Ambiente, agora = new Date()): Promise<void> {
  const kv = amb.CHAT_IA
  const email = emailDoAcesso(pedido)
  if (!kv || !email || !eAberturaDePagina(pedido)) return
  const chave = PREFIXO + email
  let atual: RegistroAcesso | null = null
  try {
    atual = JSON.parse((await kv.get(chave)) ?? 'null') as RegistroAcesso | null
  } catch {
    atual = null
  }
  const novo = proximoRegistro(atual, email, agora)
  if (!novo) return
  await kv.put(chave, JSON.stringify(novo), { expirationTtl: RETENCAO_DIAS * 86_400, metadata: novo })
}

export function eAdmin(pedido: Request, amb: Ambiente): boolean {
  const email = emailDoAcesso(pedido)
  const admins = (amb.ADMIN_EMAILS ?? '')
    .split(',')
    .map((e) => e.trim().toLowerCase())
    .filter(Boolean)
  return !!email && admins.includes(email)
}

export interface ListaDeAcessos {
  gerado_em: string
  agora: RegistroAcesso[] // visto nos últimos AGORA_MIN minutos
  todos: RegistroAcesso[] // do último acesso mais recente ao mais antigo
  agora_min: number
  retencao_dias: number
}

export function montarLista(registros: RegistroAcesso[], agora: Date): ListaDeAcessos {
  const todos = [...registros].sort((a, b) => b.ultimo.localeCompare(a.ultimo))
  const limite = agora.getTime() - AGORA_MIN * 60_000
  return {
    gerado_em: agora.toISOString(),
    agora: todos.filter((r) => Date.parse(r.ultimo) >= limite),
    todos,
    agora_min: AGORA_MIN,
    retencao_dias: RETENCAO_DIAS,
  }
}

function eRegistro(x: unknown): x is RegistroAcesso {
  const r = x as RegistroAcesso
  return !!r && typeof r.email === 'string' && typeof r.ultimo === 'string' && typeof r.primeiro === 'string'
}

const JSON_SEM_CACHE = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }

export async function tratar(pedido: Request, amb: Ambiente, agora = new Date()): Promise<Response> {
  // Quem não é admin não fica sabendo que a página existe.
  if (pedido.method !== 'GET' || !eAdmin(pedido, amb)) {
    return new Response(JSON.stringify({ erro: 'não encontrado' }), { status: 404, headers: JSON_SEM_CACHE })
  }
  const kv = amb.CHAT_IA
  if (!kv) {
    return new Response(JSON.stringify({ erro: 'sem_kv', ...montarLista([], agora) }), { status: 200, headers: JSON_SEM_CACHE })
  }
  const registros: RegistroAcesso[] = []
  let cursor: string | undefined
  for (let pagina = 0; pagina < 20; pagina++) {
    const r = await kv.list({ prefix: PREFIXO, cursor })
    for (const k of r.keys) if (eRegistro(k.metadata)) registros.push(k.metadata)
    if (r.list_complete || !r.cursor) break
    cursor = r.cursor
  }
  return new Response(JSON.stringify(montarLista(registros, agora)), { status: 200, headers: JSON_SEM_CACHE })
}

export const onRequest = (contexto: { request: Request; env: Ambiente }): Promise<Response> =>
  tratar(contexto.request, contexto.env)
