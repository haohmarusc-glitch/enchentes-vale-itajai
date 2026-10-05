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
const CHAVE = { ANTHROPIC_API_KEY: 'sk-ant-teste', CHAT_IA_REDATOR: 'ligado' }

const texto = (t: string) =>
  ({
    model: 'claude-opus-5-5',
    content: [{ type: 'text', text: t }],
    stop_reason: 'end_turn',
    usage: { input_tokens: 1, output_tokens: 1 },
  }) as unknown as Anthropic.Beta.Messages.BetaMessage

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

test('a chave sozinha não liga o chat que redige (ela serve ao piloto do classificador)', async () => {
  const { criar, chamadas } = criarFalso()
  for (const amb of [{ ANTHROPIC_API_KEY: 'sk-ant-teste' }, { ANTHROPIC_API_KEY: 'sk-ant-teste', CHAT_IA_REDATOR: 'sim' }]) {
    assert.deepEqual(await (await tratar(new Request(URL_API), amb)).json(), { ligado: false })
    assert.equal((await tratar(post({ pergunta: 'Maior cheia de Gaspar?' }), amb, criar)).status, 503)
  }
  assert.equal(chamadas(), 0)
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
  assert.equal(dados.get('ia|2026-10-04'), '2')
  // Soma do dia: só números (o falso gasta 1 de entrada e 1 de saída por pergunta).
  const dia = JSON.parse(dados.get('uso|2026-10-04') ?? '{}')
  assert.deepEqual(Object.keys(dia).sort(), ['cache_criado', 'cache_lido', 'custo_usd', 'entrada', 'perguntas', 'por_email', 'saida'])
  assert.equal(dia.perguntas, 2)
  assert.equal(dia.entrada, 2)
  assert.equal(dia.saida, 2)
  assert.deepEqual([...dados.keys()].sort(), ['ia|2026-10-04', 'uso|2026-10-04'])
})

test('erro da IA não vaza detalhe nem a pergunta', async () => {
  const criar: Criar = async () => {
    throw new Error('falha com a pergunta Maior cheia de Gaspar?')
  }
  const r = await tratar(post({ pergunta: 'Maior cheia de Gaspar?' }), CHAVE, criar, AGORA)
  assert.equal(r.status, 500)
  assert.deepEqual(await r.json(), { erro: 'interno' })
})

test('log de custo: uma linha por pergunta com o e-mail de acesso e números, sem a pergunta nem a resposta', async () => {
  const linhas: string[] = []
  const pedidosAPI: string[] = []
  const original = console.log
  console.log = (...x: unknown[]) => void linhas.push(x.map(String).join(' '))
  try {
    const { criar } = criarFalso('Resposta secreta sobre Gaspar')
    const espiao: Criar = async (p) => {
      pedidosAPI.push(JSON.stringify(p))
      return criar(p)
    }
    await tratar(post({ pergunta: 'Pergunta secreta de Gaspar?' }, { 'cf-access-authenticated-user-email': ' Fulano@Exemplo.com ' }), CHAVE, espiao, AGORA)
    await tratar(post({ pergunta: 'Outra pergunta secreta?' }), CHAVE, criar, AGORA)
    await tratar(post({ pergunta: 'Mais uma secreta?' }, { 'cf-access-authenticated-user-email': 'não é e-mail' }), CHAVE, criar, AGORA)
  } finally {
    console.log = original
  }
  assert.equal(linhas.length, 3)
  for (const l of linhas) assert.ok(!l.includes('secreta'), l)
  assert.deepEqual(JSON.parse(linhas[0]!), {
    evento: 'chat-ia',
    email: 'fulano@exemplo.com',
    tipo: 'ia',
    modelo: 'claude-opus-5-5',
    rodadas: 1,
    entrada: 1,
    cache_criado: 0,
    cache_lido: 0,
    saida: 1,
    custo_usd: 0.000024,
  })
  assert.equal(JSON.parse(linhas[1]!).email, null, 'sem o cabeçalho do Access')
  assert.equal(JSON.parse(linhas[2]!).email, null, 'cabeçalho que não é e-mail')
  // O e-mail não vai à Anthropic.
  assert.equal(pedidosAPI.length, 1)
  assert.ok(!pedidosAPI[0]!.toLowerCase().includes('fulano'))
})

test('soma do dia no KV traz o total por e-mail', async () => {
  const { kv, dados } = kvFalso()
  const { criar } = criarFalso()
  const amb = { ...CHAVE, CHAT_IA: kv }
  const como = (email?: string): Record<string, string> => (email ? { 'cf-access-authenticated-user-email': email } : {})
  await tratar(post({ pergunta: 'Maior cheia de Gaspar?' }, como('a@x.com')), amb, criar, AGORA)
  await tratar(post({ pergunta: 'Maior cheia de Ilhota?' }, como('a@x.com')), amb, criar, AGORA)
  await tratar(post({ pergunta: 'Maior cheia de Brusque?' }, como('b@x.com')), amb, criar, AGORA)
  await tratar(post({ pergunta: 'Maior cheia de Blumenau?' }), amb, criar, AGORA)
  const dia = JSON.parse(dados.get('uso|2026-10-04') ?? '{}')
  assert.equal(dia.perguntas, 4)
  assert.deepEqual(dia.por_email, {
    'a@x.com': { perguntas: 2, custo_usd: 0.000048 },
    'b@x.com': { perguntas: 1, custo_usd: 0.000024 },
    '(sem e-mail)': { perguntas: 1, custo_usd: 0.000024 },
  })
  assert.ok(!JSON.stringify([...dados.entries()]).includes('Maior cheia'))
})
