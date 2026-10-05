/**
 * Cloudflare Pages Function: `/api/chat-classificar` — PILOTO do classificador de
 * intenção (decisão do Jefferson de 05/10/2026). Documentação e como ligar:
 * `docs/PILOTO-CLASSIFICADOR.md`.
 *
 * A IA só CLASSIFICA a pergunta que o chat sem IA não entendeu (ou em que palpitou).
 * A resposta é montada no aparelho, pelo motor do chat, a partir da classificação
 * conferida aqui (`decidir` em `src/chat-ia/classificador.ts`).
 *
 *  - GET  → `{"ligado": true}` ou `{"ligado": false, "motivo": …}` para QUEM pede (o motivo diz
 *           qual interruptor falta). O chat só consulta quando é `true`.
 *  - POST `{"pergunta", "origem": "nao_entendi"|"palpite"}` → `{"id", "decisao"}`.
 *  - POST `{"id", "correcao": "correto"|"nao_era_isso"}` → guarda o botão que a pessoa apertou.
 *
 * INTERRUPTOR (os três juntos): segredo `ANTHROPIC_API_KEY`, `CLASSIFICADOR_PILOTO=ligado`
 * e o e-mail de acesso na lista `CLASSIFICADOR_EMAILS` (separados por vírgula; `*` = todos
 * que passam pelo Cloudflare Access). Faltando um, o GET diz `false` e o POST dá 503.
 *
 * TEMPO: a IA tem `TEMPO_LIMITE_MS` para responder, sem nova tentativa. Passou disso, ou
 * falhou, a resposta é um erro curto e o aparelho diz "não consegui interpretar"; o chat
 * sem IA segue igual.
 *
 * REGISTRO ANÔNIMO (pedido do Jefferson, 05/10/2026), com o KV `CHAT_IA`: uma entrada por
 * chamada em `piloto|AAAA-MM-DD_<uuid>`, por 90 dias, com a pergunta MASCARADA (sem e-mail,
 * telefone nem número de casa), a classificação, a confiança, a decisão, o tempo, os tokens,
 * o custo e, depois, a correção. NÃO guarda e-mail de acesso, IP nem User-Agent — o e-mail
 * só é lido para conferir a lista e é descartado. A tela avisa antes de enviar.
 */
import Anthropic from '@anthropic-ai/sdk'
import enchentes from '../../../data/enchentes.json'
import transito from '../../../data/transito.json'
import estacoes from '../../../data/estacoes.json'
import atlasAcu from '../../../data/brutos/atlas-desastres-recorte-itajai-acu-2026-09-21.json'
import atlasMirim from '../../../data/brutos/atlas-desastres-recorte-itajai-mirim-2026-09-21.json'
import type { Dados } from '../../src/chat-local/motor'
import { custoEstimado } from '../../src/chat-ia/nucleo'
import {
  CONFIANCA_MINIMA_PADRAO,
  MODELO_CLASSIFICADOR,
  TAMANHO_MAXIMO_PERGUNTA,
  TEMPO_LIMITE_MS,
  VERSAO_CLASSIFICADOR,
  classificar,
  decidir,
  mascarar,
  type Chamada,
  type Chamar,
  type Decisao,
} from '../../src/chat-ia/classificador'
import { emailDoAcesso, type ArmazemKV } from './chat-ia'

export interface Ambiente {
  ANTHROPIC_API_KEY?: string
  CLASSIFICADOR_PILOTO?: string
  CLASSIFICADOR_EMAILS?: string
  CLASSIFICADOR_MODELO?: string
  CLASSIFICADOR_CONFIANCA_MINIMA?: string
  CLASSIFICADOR_LIMITE_DIA?: string
  CHAT_IA?: ArmazemKV
}

const TAMANHO_MAXIMO_CORPO = 2_000
const LIMITE_PADRAO_DIA = 200
const RETENCAO_DIAS = 90
const SEM_CACHE = { 'cache-control': 'no-store' }
const ORIGENS = ['nao_entendi', 'palpite'] as const
const CORRECOES = ['correto', 'nao_era_isso'] as const
const ID_VALIDO = /^\d{4}-\d{2}-\d{2}_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/

const resposta = (status: number, corpo: unknown) =>
  new Response(JSON.stringify(corpo), { status, headers: { ...SEM_CACHE, 'content-type': 'application/json; charset=utf-8' } })

// O classificador só precisa da lista de cidades (estações + municípios do Atlas).
const BASE: Dados = {
  enchentes: enchentes as unknown as Dados['enchentes'],
  transito: transito as unknown as Dados['transito'],
  estacoes: estacoes as unknown as Dados['estacoes'],
  atlas: {
    'itajai-acu': atlasAcu as unknown as Dados['atlas'][string],
    'itajai-mirim': atlasMirim as unknown as Dados['atlas'][string],
  },
  chuvaEventos: { estacoes: {}, eventos: {} },
}

/**
 * Por que o piloto está (des)ligado para quem pede. O GET devolve o motivo para quem
 * configura saber qual interruptor falta; não revela valor de nada (nem a lista, nem o
 * e-mail lido).
 */
export type MotivoDesligado = 'sem_chave' | 'piloto_desligado' | 'lista_vazia' | 'sem_email' | 'email_fora_da_lista'

export function estadoDoPiloto(pedido: Request, amb: Ambiente): { ligado: true } | { ligado: false; motivo: MotivoDesligado } {
  if (!amb.ANTHROPIC_API_KEY?.trim()) return { ligado: false, motivo: 'sem_chave' }
  if (amb.CLASSIFICADOR_PILOTO?.trim().toLowerCase() !== 'ligado') return { ligado: false, motivo: 'piloto_desligado' }
  const lista = (amb.CLASSIFICADOR_EMAILS ?? '')
    .split(',')
    .map((x) => x.trim().toLowerCase())
    .filter(Boolean)
  if (!lista.length) return { ligado: false, motivo: 'lista_vazia' }
  if (lista.includes('*')) return { ligado: true }
  const email = emailDoAcesso(pedido)
  if (email === null) return { ligado: false, motivo: 'sem_email' }
  return lista.includes(email) ? { ligado: true } : { ligado: false, motivo: 'email_fora_da_lista' }
}

/** O piloto está ligado para quem pede? */
export const ligadoPara = (pedido: Request, amb: Ambiente): boolean => estadoDoPiloto(pedido, amb).ligado

function numeroDoAmbiente(valor: string | undefined, padrao: number, min: number, max: number): number {
  const n = Number(valor)
  return valor?.trim() && Number.isFinite(n) && n >= min && n <= max ? n : padrao
}

async function dentroDoLimite(amb: Ambiente, dia: string): Promise<boolean> {
  const kv = amb.CHAT_IA
  if (!kv) return true
  const teto = numeroDoAmbiente(amb.CLASSIFICADOR_LIMITE_DIA, LIMITE_PADRAO_DIA, 1, 100_000)
  const chave = `classif|${dia}`
  try {
    const atual = parseInt((await kv.get(chave)) ?? '0', 10) || 0
    if (atual >= teto) return false
    await kv.put(chave, String(atual + 1), { expirationTtl: 3 * 86_400 })
  } catch {
    // KV fora do ar: não trava; o limite mensal da chave na Anthropic continua valendo.
  }
  return true
}

/** Corre contra o relógio: passou do tempo, rejeita (a chamada à IA é abandonada). */
function comTempoLimite<T>(p: Promise<T>, ms: number): Promise<T> {
  return new Promise((ok, falha) => {
    const t = setTimeout(() => falha(new Error('tempo')), ms)
    p.then(
      (v) => {
        clearTimeout(t)
        ok(v)
      },
      (e) => {
        clearTimeout(t)
        falha(e)
      },
    )
  })
}

export interface RegistroPiloto {
  id: string
  versao: string
  origem: (typeof ORIGENS)[number]
  pergunta: string
  /** A saída do modelo depois da conferência (null se veio inválida ou não veio). */
  classificacao: unknown
  confianca: number | null
  motivo_curto: string | null
  /** "ok", "faltou", "agora:barreira", "agora:classificador", "nao_sei:<motivo>", "erro:<tipo>". */
  resultado: string
  modelo: string | null
  ms: number
  entrada: number
  cache_criado: number
  cache_lido: number
  saida: number
  custo_usd: number | null
  correcao: (typeof CORRECOES)[number] | null
}

const rotulo = (d: Decisao) => (d.tipo === 'agora' ? `agora:${d.origem}` : d.tipo === 'nao_sei' ? `nao_sei:${d.motivo}` : d.tipo)

async function registrar(r: RegistroPiloto, amb: Ambiente): Promise<void> {
  // A linha do log da Cloudflare leva só números e rótulos — nunca a pergunta.
  console.log(
    JSON.stringify({
      evento: 'chat-classificar',
      versao: r.versao,
      origem: r.origem,
      resultado: r.resultado,
      confianca: r.confianca,
      modelo: r.modelo,
      ms: r.ms,
      entrada: r.entrada,
      cache_lido: r.cache_lido,
      saida: r.saida,
      custo_usd: r.custo_usd,
    }),
  )
  try {
    await amb.CHAT_IA?.put(`piloto|${r.id}`, JSON.stringify(r), { expirationTtl: RETENCAO_DIAS * 86_400 })
  } catch {
    // KV fora do ar: perde o registro; a linha de log já saiu.
  }
}

async function corrigir(corpo: Record<string, unknown>, amb: Ambiente): Promise<Response> {
  const { id, correcao } = corpo
  if (typeof id !== 'string' || !ID_VALIDO.test(id) || !CORRECOES.includes(correcao as (typeof CORRECOES)[number]) || Object.keys(corpo).length !== 2)
    return resposta(400, { erro: 'corpo' })
  const kv = amb.CHAT_IA
  if (!kv) return resposta(200, { ok: true })
  try {
    const bruto = await kv.get(`piloto|${id}`)
    if (!bruto) return resposta(404, { erro: 'id' })
    const r = JSON.parse(bruto) as RegistroPiloto
    if (r.correcao === null) {
      r.correcao = correcao as RegistroPiloto['correcao']
      await kv.put(`piloto|${id}`, JSON.stringify(r), { expirationTtl: RETENCAO_DIAS * 86_400 })
    }
  } catch {
    return resposta(200, { ok: false })
  }
  return resposta(200, { ok: true })
}

export async function tratar(pedido: Request, amb: Ambiente, chamar?: Chamar, agora: Date = new Date(), novoId: () => string = () => crypto.randomUUID()): Promise<Response> {
  if (pedido.method === 'GET') return resposta(200, estadoDoPiloto(pedido, amb))
  if (pedido.method !== 'POST') return new Response(null, { status: 405, headers: { ...SEM_CACHE, allow: 'GET, POST' } })
  if (!ligadoPara(pedido, amb)) return resposta(503, { erro: 'desligado' })

  const site = pedido.headers.get('sec-fetch-site')
  if (site !== null && site !== 'same-origin') return resposta(403, { erro: 'origem' })
  if (Number(pedido.headers.get('content-length') ?? '0') > TAMANHO_MAXIMO_CORPO) return resposta(413, { erro: 'grande' })
  let corpo: Record<string, unknown>
  try {
    const bruto = await pedido.text()
    if (bruto.length > TAMANHO_MAXIMO_CORPO) return resposta(413, { erro: 'grande' })
    const c = JSON.parse(bruto) as unknown
    if (!c || typeof c !== 'object' || Array.isArray(c)) return resposta(400, { erro: 'corpo' })
    corpo = c as Record<string, unknown>
  } catch {
    return resposta(400, { erro: 'corpo' })
  }
  if ('correcao' in corpo) return corrigir(corpo, amb)

  const { pergunta, origem } = corpo
  if (typeof pergunta !== 'string' || !pergunta.trim() || pergunta.length > TAMANHO_MAXIMO_PERGUNTA || !ORIGENS.includes(origem as (typeof ORIGENS)[number]) || Object.keys(corpo).length !== 2)
    return resposta(400, { erro: 'corpo' })
  const q = pergunta.trim()
  const dia = agora.toISOString().slice(0, 10)
  const anoAtual = agora.getUTCFullYear()
  const opcoes = { confiancaMinima: numeroDoAmbiente(amb.CLASSIFICADOR_CONFIANCA_MINIMA, CONFIANCA_MINIMA_PADRAO, 0, 1), anoAtual }

  // A barreira do presente, sem gastar IA.
  const antes = decidir(q, null, BASE, opcoes)
  if (antes.decisao.tipo === 'agora') return resposta(200, { id: null, decisao: antes.decisao })

  if (!(await dentroDoLimite(amb, dia))) return resposta(429, { erro: 'limite_do_dia' })

  const id = `${dia}_${novoId()}`
  const modelo = amb.CLASSIFICADOR_MODELO?.trim() || MODELO_CLASSIFICADOR
  const base: Omit<RegistroPiloto, 'classificacao' | 'confianca' | 'motivo_curto' | 'resultado' | 'modelo' | 'ms' | 'entrada' | 'cache_criado' | 'cache_lido' | 'saida' | 'custo_usd'> = {
    id,
    versao: VERSAO_CLASSIFICADOR,
    origem: origem as RegistroPiloto['origem'],
    pergunta: mascarar(q),
    correcao: null,
  }
  const cliente = chamar ? null : new Anthropic({ apiKey: amb.ANTHROPIC_API_KEY!.trim(), maxRetries: 0, timeout: TEMPO_LIMITE_MS })
  const chamarIA: Chamar = chamar ?? ((p) => cliente!.messages.create(p))
  const inicio = Date.now()
  let c: Chamada
  try {
    c = await comTempoLimite(classificar(q, BASE, chamarIA, modelo, anoAtual), TEMPO_LIMITE_MS)
  } catch (erro) {
    const tipo = erro instanceof Error && erro.message === 'tempo' ? 'tempo' : erro instanceof Anthropic.APIError ? `api_${erro.status ?? '?'}` : 'interno'
    console.error('chat-classificar', tipo)
    await registrar(
      { ...base, classificacao: null, confianca: null, motivo_curto: null, resultado: `erro:${tipo}`, modelo, ms: Date.now() - inicio, entrada: 0, cache_criado: 0, cache_lido: 0, saida: 0, custo_usd: 0 },
      amb,
    )
    return resposta(tipo === 'tempo' ? 504 : 502, { erro: tipo === 'tempo' ? 'tempo' : 'ia' })
  }
  const { decisao, saida } = decidir(q, c.bruto, BASE, opcoes)
  await registrar(
    {
      ...base,
      classificacao: saida,
      confianca: saida?.confianca ?? null,
      motivo_curto: saida?.motivo_curto ?? null,
      resultado: rotulo(decisao),
      modelo: c.uso.modelo,
      ms: c.ms,
      entrada: c.uso.entrada,
      cache_criado: c.uso.cache_criado,
      cache_lido: c.uso.cache_lido,
      saida: c.uso.saida,
      custo_usd: custoEstimado(c.uso),
    },
    amb,
  )
  return resposta(200, { id, decisao })
}

/** Entrada do Pages Functions. */
export const onRequest = (contexto: { request: Request; env: Ambiente }): Promise<Response> => tratar(contexto.request, contexto.env)
