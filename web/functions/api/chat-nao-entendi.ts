/**
 * Cloudflare Pages Function: `/api/chat-nao-entendi` — contador AGREGADO das
 * perguntas que o chat local não entende (decisão do Jefferson, 04/10/2026).
 * Documentação: `docs/TELEMETRIA-CHAT.md`; como ligar: `docs/PUBLICACAO-E-ACESSO.md`.
 *
 * O que faz, e só isso:
 *  - GET  → `{"contando": true|false, "retencao_dias": 90}`. O site só mostra o
 *           aviso de contagem e só envia quando aqui diz `true`.
 *  - POST → valida o corpo contra o esquema FECHADO (`validarEvento`: cinco
 *           chaves, nenhuma a mais) e soma 1 no contador
 *           `dia|categoria|motivo|cidade` do KV, com TTL de 90 dias.
 *
 * INTERRUPTOR: o binding de KV `CHAT_NAO_ENTENDI`. Sem ele (o estado de hoje),
 * o GET diz `contando: false` e o POST responde 204 sem ler nem gravar nada.
 *
 * NÃO grava IP, cabeçalho, User-Agent, e-mail do Access nem hora: nenhum desses
 * é lido. O único dado que vai ao KV é a chave do contador e o número.
 *
 * Mora em `web/functions/` porque o Pages procura `functions/` no diretório raiz
 * do build — ver a seção de ligar em `docs/PUBLICACAO-E-ACESSO.md`.
 */
import estacoes from '../../../data/estacoes.json'
import {
  RETENCAO_DIAS,
  TAMANHO_MAXIMO_CORPO,
  chaveContador,
  idsDoCadastro,
  validarEvento,
} from '../../src/logica/telemetriaChat'

/** O mínimo do KV da Cloudflare que usamos — permite testar sem a Cloudflare. */
export interface ArmazemKV {
  get(chave: string): Promise<string | null>
  put(chave: string, valor: string, opcoes?: { expirationTtl?: number }): Promise<void>
}

export interface Ambiente {
  CHAT_NAO_ENTENDI?: ArmazemKV
}

const CIDADES = idsDoCadastro(estacoes as unknown as Parameters<typeof idsDoCadastro>[0])
const SEM_CACHE = { 'cache-control': 'no-store' }

const vazio = (status: number, extra: Record<string, string> = {}) =>
  new Response(null, { status, headers: { ...SEM_CACHE, ...extra } })

export async function tratar(pedido: Request, amb: Ambiente, agora: Date = new Date()): Promise<Response> {
  const kv = amb.CHAT_NAO_ENTENDI

  if (pedido.method === 'GET') {
    return new Response(JSON.stringify({ contando: Boolean(kv), retencao_dias: RETENCAO_DIAS }), {
      status: 200,
      headers: { ...SEM_CACHE, 'content-type': 'application/json; charset=utf-8' },
    })
  }

  if (pedido.method !== 'POST') return vazio(405, { allow: 'GET, POST' })

  // Desligado: não lê o corpo, não grava nada.
  if (!kv) return vazio(204)

  // Só do próprio site. O cabeçalho é lido para decidir, nunca guardado.
  const site = pedido.headers.get('sec-fetch-site')
  if (site !== null && site !== 'same-origin') return vazio(403)

  const tamanho = Number(pedido.headers.get('content-length') ?? '0')
  if (tamanho > TAMANHO_MAXIMO_CORPO) return vazio(413)
  let corpo: unknown
  try {
    const texto = await pedido.text()
    if (texto.length > TAMANHO_MAXIMO_CORPO) return vazio(413)
    corpo = JSON.parse(texto)
  } catch {
    return vazio(400)
  }

  const evento = validarEvento(corpo, { cidadesDoCadastro: CIDADES, agora })
  if (!evento) return vazio(400)

  // Ler-somar-gravar não é atômico no KV: duas somas no mesmo segundo podem
  // virar uma. Para "quantas perguntas o chat não entendeu", serve.
  try {
    const chave = chaveContador(evento)
    const atual = parseInt((await kv.get(chave)) ?? '0', 10)
    await kv.put(chave, String((Number.isFinite(atual) ? atual : 0) + 1), {
      expirationTtl: RETENCAO_DIAS * 86_400,
    })
  } catch {
    // KV fora do ar: perde a contagem, não devolve erro ao aparelho.
  }
  return vazio(204)
}

/** Entrada do Pages Functions. */
export const onRequest = (contexto: { request: Request; env: Ambiente }): Promise<Response> =>
  tratar(contexto.request, contexto.env)
