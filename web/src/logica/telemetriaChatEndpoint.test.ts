/**
 * O endpoint `web/functions/api/chat-nao-entendi.ts` (Cloudflare Pages Function),
 * com um KV de mentira. Trava: desligado sem o binding, esquema fechado,
 * contador agregado com TTL de 90 dias, e nada de IP/cabeçalho no que é gravado.
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { tratar, type ArmazemKV } from '../../functions/api/chat-nao-entendi'
import { RETENCAO_DIAS } from './telemetriaChat'

const AGORA = new Date('2026-10-04T15:00:00Z')
const URL_API = 'https://enchentes.premercadosc.com/api/chat-nao-entendi'
const EVENTO = { categoria: 'atlas', motivo: 'faltou_ano', cidade: 'blumenau', dia: '2026-10-04', versao: '0.1.0+abc1234' }

function kvFalso() {
  const dados = new Map<string, string>()
  const puts: { chave: string; valor: string; opcoes?: { expirationTtl?: number } }[] = []
  const kv: ArmazemKV = {
    get: async (k) => dados.get(k) ?? null,
    put: async (chave, valor, opcoes) => {
      dados.set(chave, valor)
      puts.push({ chave, valor, opcoes })
    },
  }
  return { kv, dados, puts }
}

const post = (corpo: unknown, cabecalhos: Record<string, string> = {}) =>
  new Request(URL_API, {
    method: 'POST',
    body: typeof corpo === 'string' ? corpo : JSON.stringify(corpo),
    headers: {
      'content-type': 'text/plain;charset=UTF-8',
      'sec-fetch-site': 'same-origin',
      'cf-connecting-ip': '200.200.200.200',
      'cf-access-authenticated-user-email': 'fulano@exemplo.com',
      'user-agent': 'Mozilla/5.0 (Linux; Android 14) Telefone-Do-Fulano',
      ...cabecalhos,
    },
  })

test('sem o binding (o estado de hoje): GET diz que não conta e POST responde 204 sem gravar', async () => {
  const g = await tratar(new Request(URL_API), {}, AGORA)
  assert.equal(g.status, 200)
  assert.deepEqual(await g.json(), { contando: false, retencao_dias: RETENCAO_DIAS })
  assert.equal(g.headers.get('cache-control'), 'no-store')
  const p = await tratar(post(EVENTO), {}, AGORA)
  assert.equal(p.status, 204)
})

test('com o binding: soma 1 no contador agregado, com TTL de 90 dias', async () => {
  const { kv, dados, puts } = kvFalso()
  const g = await tratar(new Request(URL_API), { CHAT_NAO_ENTENDI: kv }, AGORA)
  assert.deepEqual(await g.json(), { contando: true, retencao_dias: 90 })
  for (let i = 0; i < 3; i++) assert.equal((await tratar(post(EVENTO), { CHAT_NAO_ENTENDI: kv }, AGORA)).status, 204)
  assert.deepEqual([...dados.entries()], [['2026-10-04|atlas|faltou_ano|blumenau', '3']])
  assert.ok(puts.every((p) => p.opcoes?.expirationTtl === 90 * 86_400))
})

test('o que vai ao KV é só a chave do contador e o número: nada de IP, e-mail, navegador ou hora', async () => {
  const { kv, puts } = kvFalso()
  await tratar(post(EVENTO), { CHAT_NAO_ENTENDI: kv }, AGORA)
  const gravado = JSON.stringify(puts)
  for (const proibido of ['200.200', 'fulano', 'exemplo.com', 'Mozilla', 'Android', 'Telefone', '15:00', 'T15'])
    assert.ok(!gravado.includes(proibido), `gravou "${proibido}": ${gravado}`)
  assert.match(puts[0]!.chave, /^\d{4}-\d{2}-\d{2}\|[a-z_]+\|[a-z_]+\|[a-z0-9-]+$/)
  assert.match(puts[0]!.valor, /^\d+$/)
})

test('corpo fora do esquema: 400 e nada gravado', async () => {
  const { kv, puts } = kvFalso()
  const amb = { CHAT_NAO_ENTENDI: kv }
  const casos: unknown[] = [
    { ...EVENTO, texto: 'me conta uma piada' },
    { ...EVENTO, cidade: 'Rua XV de Novembro, 812' },
    { ...EVENTO, dia: '2026-10-04T15:00:00Z' },
    { ...EVENTO, categoria: 'nao_entendi' },
    'isto não é JSON',
    [EVENTO],
  ]
  for (const c of casos) assert.equal((await tratar(post(c), amb, AGORA)).status, 400, JSON.stringify(c))
  assert.equal(puts.length, 0)
})

test('corpo grande demais, outro site e outro método são recusados sem gravar', async () => {
  const { kv, puts } = kvFalso()
  const amb = { CHAT_NAO_ENTENDI: kv }
  assert.equal((await tratar(post({ ...EVENTO, versao: 'x'.repeat(600) }), amb, AGORA)).status, 413)
  assert.equal((await tratar(post(EVENTO, { 'sec-fetch-site': 'cross-site' }), amb, AGORA)).status, 403)
  const put = await tratar(new Request(URL_API, { method: 'PUT', body: '{}' }), amb, AGORA)
  assert.equal(put.status, 405)
  assert.equal(put.headers.get('allow'), 'GET, POST')
  assert.equal(puts.length, 0)
})

test('KV fora do ar: o aparelho recebe 204 mesmo assim (falha silenciosa)', async () => {
  const kv: ArmazemKV = {
    get: async () => {
      throw new Error('KV fora')
    },
    put: async () => {
      throw new Error('KV fora')
    },
  }
  assert.equal((await tratar(post(EVENTO), { CHAT_NAO_ENTENDI: kv }, AGORA)).status, 204)
})
