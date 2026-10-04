/**
 * O endpoint `web/functions/api/chat-ia.ts`, com cliente e KV de mentira.
 * Trava: desligado sem a chave (e sem ler o corpo), só do próprio site, esquema
 * fechado, teto do dia no KV guardando só o contador, e erro sem detalhe.
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import type Anthropic from '@anthropic-ai/sdk'
import { tratar, type ArmazemKV } from '../../functions/api/chat-ia'
import type { Criar } from './nucleo'

const URL_API = 'https://enchentes.premercadosc.com/api/chat-ia'
const AGORA = new Date('2026-10-04T15:00:00Z')
const CHAVE = { ANTHROPIC_API_KEY: 'sk-ant-teste' }

const texto = (t: string) =>
  ({ content: [{ type: 'text', text: t }], stop_reason: 'end_turn', usage: { input_tokens: 1, output_tokens: 1 } }) as unknown as Anthropic.Beta.Messages.BetaMessage

function criarFalso(t = 'resposta') {
  let chamadas = 0
  const criar: Criar = async () => {
    chamadas++
    return texto(t)
  }
  return { criar, chamadas: () => chamadas }
}

function kvFalso() {
  const dados = new Map<string, string>()
  const kv: ArmazemKV = { get: async (k) => dados.get(k) ?? null, put: async (k, v) => void dados.set(k, v) }
  return { kv, dados }
}

const post = (corpo: unknown, cab: Record<string, string> = {}) =>
  new Request(URL_API, {
    method: 'POST',
    body: typeof corpo === 'string' ? corpo : JSON.stringify(corpo),
    headers: { 'content-type': 'application/json', 'sec-fetch-site': 'same-origin', ...cab },
  })

test('sem a chave: GET diz desligado e o POST não chama a IA', async () => {
  const g = await tratar(new Request(URL_API), {})
  assert.deepEqual(await g.json(), { ligado: false })
  assert.equal(g.headers.get('cache-control'), 'no-store')
  const { criar, chamadas } = criarFalso()
  const p = await tratar(post({ pergunta: 'Maior cheia de Gaspar?' }), { ANTHROPIC_API_KEY: '  ' }, criar)
  assert.equal(p.status, 503)
  assert.equal(chamadas(), 0)
  assert.deepEqual(await (await tratar(new Request(URL_API), CHAVE)).json(), { ligado: true })
})

test('com a chave: responde o texto da IA', async () => {
  const { criar, chamadas } = criarFalso('Em Gaspar, a maior cheia…')
  const r = await tratar(post({ pergunta: 'Maior cheia de Gaspar?' }), CHAVE, criar, AGORA)
  assert.equal(r.status, 200)
  assert.deepEqual(await r.json(), { tipo: 'ia', texto: 'Em Gaspar, a maior cheia…' })
  assert.equal(chamadas(), 1)
})

test('barreira do presente responde sem chamar a IA', async () => {
  const { criar, chamadas } = criarFalso()
  const r = await tratar(post({ pergunta: 'O rio vai subir hoje?' }), CHAVE, criar, AGORA)
  assert.equal((await r.json()).tipo, 'agora')
  assert.equal(chamadas(), 0)
})

test('recusa outra origem, corpo inválido, corpo grande e outro método', async () => {
  const { criar, chamadas } = criarFalso()
  assert.equal((await tratar(post({ pergunta: 'x' }, { 'sec-fetch-site': 'cross-site' }), CHAVE, criar)).status, 403)
  assert.equal((await tratar(post('não é json'), CHAVE, criar)).status, 400)
  assert.equal((await tratar(post({ pergunta: 'x', ip: '1.2.3.4' }), CHAVE, criar)).status, 400)
  assert.equal((await tratar(post({ pergunta: 'x'.repeat(7000) }), CHAVE, criar)).status, 413)
  assert.equal((await tratar(new Request(URL_API, { method: 'DELETE' }), CHAVE, criar)).status, 405)
  assert.equal(chamadas(), 0)
})

test('teto do dia no KV: só o contador, e 429 quando passa', async () => {
  const { kv, dados } = kvFalso()
  const { criar, chamadas } = criarFalso()
  const amb = { ...CHAVE, CHAT_IA: kv, CHAT_IA_LIMITE_DIA: '2' }
  assert.equal((await tratar(post({ pergunta: 'Maior cheia de Gaspar?' }), amb, criar, AGORA)).status, 200)
  assert.equal((await tratar(post({ pergunta: 'Maior cheia de Ilhota?' }), amb, criar, AGORA)).status, 200)
  const r = await tratar(post({ pergunta: 'Maior cheia de Brusque?' }), amb, criar, AGORA)
  assert.equal(r.status, 429)
  assert.deepEqual(await r.json(), { erro: 'limite_do_dia' })
  assert.equal(chamadas(), 2)
  assert.deepEqual([...dados.entries()], [['ia|2026-10-04', '2']])
})

test('erro da IA não vaza detalhe nem a pergunta', async () => {
  const criar: Criar = async () => {
    throw new Error('falha com a pergunta Maior cheia de Gaspar?')
  }
  const r = await tratar(post({ pergunta: 'Maior cheia de Gaspar?' }), CHAVE, criar, AGORA)
  assert.equal(r.status, 500)
  assert.deepEqual(await r.json(), { erro: 'interno' })
})
