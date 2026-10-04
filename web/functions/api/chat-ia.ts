/**
 * Cloudflare Pages Function: `/api/chat-ia` — o chat do histórico com IA (Claude).
 * Documentação: `docs/CHAT-IA.md`; como ligar: `docs/PUBLICACAO-E-ACESSO.md`, "Chat com IA".
 *
 *  - GET  → `{"ligado": true|false}`. O site só mostra o botão "Perguntar à IA"
 *           quando aqui diz `true`.
 *  - POST → `{"pergunta": "...", "anteriores": [{pergunta, resposta}]}` (esquema
 *           fechado, `validarPedido`) → `{"tipo", "texto"}`.
 *
 * INTERRUPTOR: o segredo `ANTHROPIC_API_KEY`. Sem ele (o estado de hoje), o GET
 * diz `ligado: false` e o POST responde 503 sem ler o corpo.
 *
 * LIMITE DO DIA (opcional): com o KV `CHAT_IA` ligado, no máximo
 * `CHAT_IA_LIMITE_DIA` perguntas por dia (padrão 50) no site todo. O teto de
 * gasto de verdade fica no Console da Anthropic (limite mensal da chave).
 *
 * CUSTO (pedido do Jefferson, 04/10/2026): cada pergunta escreve UMA linha no log
 * da Cloudflare — `{"evento":"chat-ia","tipo",…,"entrada","saida","custo_usd"}` —
 * só com números. Com o KV `CHAT_IA`, soma também o dia em `uso|AAAA-MM-DD`
 * (90 dias), porque o log do Pages é só ao vivo.
 *
 * NÃO grava a pergunta, a resposta, IP, User-Agent nem o e-mail do Access. O KV
 * só guarda contadores do dia. A pergunta vai à Anthropic para ser respondida —
 * o site avisa isso antes de cada envio.
 */
import Anthropic from '@anthropic-ai/sdk'
import enchentes from '../../../data/enchentes.json'
import transito from '../../../data/transito.json'
import estacoes from '../../../data/estacoes.json'
import atlasAcu from '../../../data/brutos/atlas-desastres-recorte-itajai-acu-2026-09-21.json'
import atlasMirim from '../../../data/brutos/atlas-desastres-recorte-itajai-mirim-2026-09-21.json'
import chuva from '../../../data/brutos/inmet-chuva-eventos-atlas-2026-09-22.json'
import picosMirim from '../../../data/brutos/hidroweb-mirim-2026-09-22/picos_itajai_mirim_1997_2021.json'
import { citaRua, type Dados } from '../../src/chat-local/motor'
import { cotaRuaValida } from '../../src/logica/cotasRuas'
import type { CotaRua } from '../../src/dados/tipos'
import { MODELO_PADRAO, custoEstimado, responderComIA, validarPedido, type Criar, type ObterDados, type RespostaIA } from '../../src/chat-ia/nucleo'

/** O mínimo do KV da Cloudflare que usamos. */
export interface ArmazemKV {
  get(chave: string): Promise<string | null>
  put(chave: string, valor: string, opcoes?: { expirationTtl?: number }): Promise<void>
}

export interface Ambiente {
  ANTHROPIC_API_KEY?: string
  /** Troca o modelo sem mexer no código (ex.: "claude-sonnet-5-5"). */
  CHAT_IA_MODELO?: string
  CHAT_IA?: ArmazemKV
  CHAT_IA_LIMITE_DIA?: string
}

const TAMANHO_MAXIMO_CORPO = 6_000
const LIMITE_PADRAO_DIA = 50
const SEM_CACHE = { 'cache-control': 'no-store' }

const resposta = (status: number, corpo: unknown) =>
  new Response(JSON.stringify(corpo), { status, headers: { ...SEM_CACHE, 'content-type': 'application/json; charset=utf-8' } })

const BASE: Dados = {
  enchentes: enchentes as unknown as Dados['enchentes'],
  transito: transito as unknown as Dados['transito'],
  estacoes: estacoes as unknown as Dados['estacoes'],
  atlas: {
    'itajai-acu': atlasAcu as unknown as Dados['atlas'][string],
    'itajai-mirim': atlasMirim as unknown as Dados['atlas'][string],
  },
  chuvaEventos: chuva as unknown as Dados['chuvaEventos'],
  picosMirim: picosMirim as unknown as Dados['picosMirim'],
}

// As cotas de rua (~3 MB) e as diárias da ANA (~1,2 MB) só entram quando a
// pergunta pede: import dinâmico, avaliado na primeira vez e guardado.
let cotasRuas: CotaRua[] | undefined
let cotasAna: Dados['cotasAna']

const obterDados: ObterDados = async (pergunta) => {
  if (citaRua(pergunta) && !cotasRuas) {
    const mod = await import('../../../data/cotas-ruas.json')
    cotasRuas = ((mod.default as unknown as { cotas?: CotaRua[] }).cotas ?? []).filter(cotaRuaValida)
  }
  if (/\b(ana|cota|cm)\b/i.test(pergunta) && !cotasAna) {
    const mod = await import('../../../data/brutos/hidroweb-mirim-2026-09-22/cotas_itajai_mirim_diaria.json')
    cotasAna = mod.default as unknown as Dados['cotasAna']
  }
  return { ...BASE, ...(cotasRuas ? { cotasRuas } : {}), ...(cotasAna ? { cotasAna } : {}) }
}

/** Soma 1 no contador do dia; devolve false se o teto já foi atingido. */
async function dentroDoLimite(amb: Ambiente, agora: Date): Promise<boolean> {
  const kv = amb.CHAT_IA
  if (!kv) return true
  const limite = parseInt(amb.CHAT_IA_LIMITE_DIA ?? '', 10)
  const teto = Number.isFinite(limite) && limite > 0 ? limite : LIMITE_PADRAO_DIA
  const chave = `ia|${agora.toISOString().slice(0, 10)}`
  try {
    const atual = parseInt((await kv.get(chave)) ?? '0', 10) || 0
    if (atual >= teto) return false
    await kv.put(chave, String(atual + 1), { expirationTtl: 3 * 86_400 })
  } catch {
    // KV fora do ar: não trava o chat; o limite mensal da Anthropic continua valendo.
  }
  return true
}

/** Totais do dia no KV: perguntas, tokens e custo. Só números. */
export interface UsoDoDia {
  perguntas: number
  entrada: number
  cache_criado: number
  cache_lido: number
  saida: number
  custo_usd: number
}

const RETENCAO_USO_DIAS = 90

/** Uma linha de log por pergunta, só com números; e a soma do dia no KV, se houver. */
async function registrarUso(r: RespostaIA, amb: Ambiente, agora: Date): Promise<void> {
  const u = r.uso
  const custo = u ? custoEstimado(u) : 0
  console.log(
    JSON.stringify({
      evento: 'chat-ia',
      tipo: r.tipo,
      modelo: u?.modelo ?? null,
      rodadas: u?.rodadas ?? 0,
      entrada: u?.entrada ?? 0,
      cache_criado: u?.cache_criado ?? 0,
      cache_lido: u?.cache_lido ?? 0,
      saida: u?.saida ?? 0,
      custo_usd: custo,
    }),
  )
  const kv = amb.CHAT_IA
  if (!kv || !u) return
  const chave = `uso|${agora.toISOString().slice(0, 10)}`
  try {
    const bruto = await kv.get(chave)
    const dia: UsoDoDia = bruto ? JSON.parse(bruto) : { perguntas: 0, entrada: 0, cache_criado: 0, cache_lido: 0, saida: 0, custo_usd: 0 }
    dia.perguntas += 1
    dia.entrada += u.entrada
    dia.cache_criado += u.cache_criado
    dia.cache_lido += u.cache_lido
    dia.saida += u.saida
    dia.custo_usd = Math.round((dia.custo_usd + (custo ?? 0)) * 1e6) / 1e6
    await kv.put(chave, JSON.stringify(dia), { expirationTtl: RETENCAO_USO_DIAS * 86_400 })
  } catch {
    // KV fora do ar: perde a soma do dia; a linha de log já saiu.
  }
}

export async function tratar(pedido: Request, amb: Ambiente, criar?: Criar, agora: Date = new Date()): Promise<Response> {
  const chave = amb.ANTHROPIC_API_KEY?.trim()

  if (pedido.method === 'GET') return resposta(200, { ligado: Boolean(chave) })
  if (pedido.method !== 'POST') return new Response(null, { status: 405, headers: { ...SEM_CACHE, allow: 'GET, POST' } })
  if (!chave) return resposta(503, { erro: 'desligado' })

  // Só do próprio site. O cabeçalho é lido para decidir, nunca guardado.
  const site = pedido.headers.get('sec-fetch-site')
  if (site !== null && site !== 'same-origin') return resposta(403, { erro: 'origem' })

  if (Number(pedido.headers.get('content-length') ?? '0') > TAMANHO_MAXIMO_CORPO) return resposta(413, { erro: 'grande' })
  let corpo: unknown
  try {
    const bruto = await pedido.text()
    if (bruto.length > TAMANHO_MAXIMO_CORPO) return resposta(413, { erro: 'grande' })
    corpo = JSON.parse(bruto)
  } catch {
    return resposta(400, { erro: 'corpo' })
  }
  const p = validarPedido(corpo)
  if (!p) return resposta(400, { erro: 'corpo' })

  if (!(await dentroDoLimite(amb, agora))) return resposta(429, { erro: 'limite_do_dia' })

  const cliente = criar ? null : new Anthropic({ apiKey: chave, maxRetries: 1, timeout: 60_000 })
  const chamar: Criar = criar ?? ((params) => cliente!.beta.messages.create(params))
  try {
    const r = await responderComIA(p, obterDados, chamar, { modelo: amb.CHAT_IA_MODELO?.trim() || MODELO_PADRAO })
    await registrarUso(r, amb, agora)
    return resposta(200, { tipo: r.tipo, texto: r.texto })
  } catch (erro) {
    // Para o log da Cloudflare, só o tipo e o status — nunca a pergunta.
    console.error('chat-ia', erro instanceof Anthropic.APIError ? `${erro.name} ${erro.status}` : 'erro interno')
    // Mais específico primeiro. Nada do erro (nem a pergunta) vai para o aparelho.
    if (erro instanceof Anthropic.RateLimitError) return resposta(429, { erro: 'ocupado' })
    if (erro instanceof Anthropic.AuthenticationError || erro instanceof Anthropic.PermissionDeniedError) return resposta(503, { erro: 'chave' })
    if (erro instanceof Anthropic.APIError) return resposta(502, { erro: 'ia' })
    return resposta(500, { erro: 'interno' })
  }
}

/** Entrada do Pages Functions. */
export const onRequest = (contexto: { request: Request; env: Ambiente }): Promise<Response> => tratar(contexto.request, contexto.env)
