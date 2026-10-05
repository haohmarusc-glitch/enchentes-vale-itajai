/**
 * O endpoint do piloto `web/functions/api/chat-classificar.ts`, com IA e KV de mentira.
 * Trava: os três interruptores, a barreira sem gastar IA, o tempo limite, o registro
 * anônimo (sem e-mail, pergunta mascarada) e a correção.
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import type { Message } from '@anthropic-ai/sdk/resources/messages/messages'
import { tratar, type Ambiente, type RegistroPiloto } from '../../functions/api/chat-classificar'
import type { ArmazemKV } from '../../functions/api/chat-ia'
import type { Chamar } from './classificador'

const URL_API = 'https://enchentes.premercadosc.com/api/chat-classificar'
const AGORA = new Date('2026-10-05T15:00:00Z')
const EMAIL = 'piloto@exemplo.com'
const ID = '00000000-0000-4000-8000-000000000001'

function kvFalso() {
  const dados = new Map<string, string>()
  const kv: ArmazemKV = { get: async (k) => dados.get(k) ?? null, put: async (k, v) => void dados.set(k, v) }
  return { kv, dados }
}

const LIGADO = (kv?: ArmazemKV): Ambiente => ({ ANTHROPIC_API_KEY: 'sk-ant-teste', CLASSIFICADOR_PILOTO: 'ligado', CLASSIFICADOR_EMAILS: `outra@x.com, ${EMAIL.toUpperCase()}`, ...(kv ? { CHAT_IA: kv } : {}) })

const req = (corpo?: unknown, email = EMAIL) =>
  new Request(URL_API, {
    method: corpo === undefined ? 'GET' : 'POST',
    ...(corpo === undefined ? {} : { body: JSON.stringify(corpo) }),
    headers: { 'content-type': 'application/json', 'sec-fetch-site': 'same-origin', 'cf-access-authenticated-user-email': email },
  })

function iaFalsa(saida: unknown, esperaMs = 0) {
  let chamadas = 0
  const chamar: Chamar = async () => {
    chamadas++
    if (esperaMs) await new Promise((r) => setTimeout(r, esperaMs))
    return {
      model: 'claude-haiku-4-5-20251001',
      stop_reason: 'end_turn',
      content: [{ type: 'text', text: JSON.stringify(saida) }],
      usage: { input_tokens: 1800, output_tokens: 90, cache_read_input_tokens: 0, cache_creation_input_tokens: 0 },
    } as unknown as Message
  }
  return { chamar, chamadas: () => chamadas }
}

const BOA = {
  intencao: 'maiores_cheias',
  cidade: 'blumenau',
  cidade2: null,
  rio: null,
  ano: null,
  ano_final: null,
  mes: null,
  nivel_m: null,
  quantidade: 1,
  rua: null,
  situacao_atual: false,
  confianca: 0.94,
  motivo_curto: 'recorde de Blumenau',
  nao_sei: false,
}

test('interruptores: chave, CLASSIFICADOR_PILOTO=ligado e e-mail na lista', async () => {
  const { chamar, chamadas } = iaFalsa(BOA)
  const ligado = async (amb: Ambiente, email = EMAIL) => ((await (await tratar(req(undefined, email), amb)).json()) as { ligado: boolean }).ligado
  assert.equal(await ligado(LIGADO()), true)
  assert.equal(await ligado({ ...LIGADO(), ANTHROPIC_API_KEY: '' }), false)
  assert.equal(await ligado({ ...LIGADO(), CLASSIFICADOR_PILOTO: 'sim' }), false)
  assert.equal(await ligado(LIGADO(), 'estranho@x.com'), false)
  assert.equal(await ligado({ ...LIGADO(), CLASSIFICADOR_EMAILS: '' }), false)
  assert.equal(await ligado({ ...LIGADO(), CLASSIFICADOR_EMAILS: '*' }, 'estranho@x.com'), true)
  const fora = await tratar(req({ pergunta: 'enchente mais feia de blumenal', origem: 'nao_entendi' }, 'estranho@x.com'), LIGADO(), chamar)
  assert.equal(fora.status, 503)
  assert.equal(chamadas(), 0)
})

test('classifica, registra anônimo (pergunta mascarada, sem e-mail) e aceita a correção uma vez', async () => {
  const { kv, dados } = kvFalso()
  const { chamar } = iaFalsa(BOA)
  const r = await tratar(req({ pergunta: 'a rua XV de Novembro, 120 encheu muito em blumenal? meu tel 47 99999-1234', origem: 'nao_entendi' }), LIGADO(kv), chamar, AGORA, () => ID)
  assert.equal(r.status, 200)
  const corpo = (await r.json()) as { id: string; decisao: { tipo: string } }
  assert.equal(corpo.id, `2026-10-05_${ID}`)
  assert.equal(corpo.decisao.tipo, 'ok')
  const bruto = dados.get(`piloto|2026-10-05_${ID}`)!
  assert.ok(!bruto.includes(EMAIL) && !bruto.toLowerCase().includes('piloto@'), 'sem e-mail no registro')
  const reg = JSON.parse(bruto) as RegistroPiloto
  assert.equal(reg.pergunta, 'a rua XV de Novembro, [nº] encheu muito em blumenal? meu tel [número]')
  assert.equal(reg.resultado, 'ok')
  assert.equal(reg.confianca, 0.94)
  assert.equal(reg.origem, 'nao_entendi')
  assert.equal(reg.entrada, 1800)
  assert.equal(reg.custo_usd, 0.00225) // Haiku: 1800 × US$ 1/M + 90 × US$ 5/M
  assert.equal(reg.correcao, null)
  assert.equal(dados.get('classif|2026-10-05'), '1')

  const c1 = await tratar(req({ id: corpo.id, correcao: 'nao_era_isso' }), LIGADO(kv), chamar, AGORA)
  assert.deepEqual(await c1.json(), { ok: true })
  await tratar(req({ id: corpo.id, correcao: 'correto' }), LIGADO(kv), chamar, AGORA)
  assert.equal((JSON.parse(dados.get(`piloto|${corpo.id}`)!) as RegistroPiloto).correcao, 'nao_era_isso')
  for (const ruim of [{ id: 'piloto|x', correcao: 'correto' }, { id: corpo.id, correcao: 'talvez' }, { id: corpo.id, correcao: 'correto', extra: 1 }])
    assert.equal((await tratar(req(ruim), LIGADO(kv), chamar, AGORA)).status, 400)
  assert.equal((await tratar(req({ id: `2026-10-05_${ID.replace('1', '2')}`, correcao: 'correto' }), LIGADO(kv), chamar, AGORA)).status, 404)
})

test('barreira do presente: responde "agora" sem chamar a IA nem gastar o limite', async () => {
  const { kv, dados } = kvFalso()
  const { chamar, chamadas } = iaFalsa(BOA)
  const r = await tratar(req({ pergunta: 'Blumenau vai encher hoje?', origem: 'palpite' }), LIGADO(kv), chamar, AGORA)
  assert.deepEqual(await r.json(), { id: null, decisao: { tipo: 'agora', origem: 'barreira' } })
  assert.equal(chamadas(), 0)
  assert.equal(dados.size, 0)
})

test('situacao_atual true da IA vira barreira e fica registrado', async () => {
  const { kv, dados } = kvFalso()
  const { chamar } = iaFalsa({ ...BOA, situacao_atual: true })
  const r = await tratar(req({ pergunta: 'Estou com medo do rio em Blumenau, o que você acha?', origem: 'palpite' }), LIGADO(kv), chamar, AGORA, () => ID)
  assert.deepEqual(((await r.json()) as { decisao: unknown }).decisao, { tipo: 'agora', origem: 'classificador' })
  assert.equal((JSON.parse(dados.get(`piloto|2026-10-05_${ID}`)!) as RegistroPiloto).resultado, 'agora:classificador')
})

test('IA lenta: desiste no tempo limite, registra o erro e devolve 504', async () => {
  const { kv, dados } = kvFalso()
  const { chamar } = iaFalsa(BOA, 7_000)
  const inicio = Date.now()
  const r = await tratar(req({ pergunta: 'enchente mais feia de blumenal', origem: 'nao_entendi' }), LIGADO(kv), chamar, AGORA, () => ID)
  assert.ok(Date.now() - inicio < 6_800)
  assert.equal(r.status, 504)
  assert.deepEqual(await r.json(), { erro: 'tempo' })
  assert.equal((JSON.parse(dados.get(`piloto|2026-10-05_${ID}`)!) as RegistroPiloto).resultado, 'erro:tempo')
})

test('IA com erro: 502 sem detalhe; corpo fora do esquema: 400; limite do dia: 429', async () => {
  const quebrada: Chamar = async () => {
    throw new Error('rede')
  }
  const r = await tratar(req({ pergunta: 'enchente mais feia de blumenal', origem: 'nao_entendi' }), LIGADO(), quebrada, AGORA)
  assert.equal(r.status, 502)
  assert.deepEqual(await r.json(), { erro: 'ia' })
  const { chamar, chamadas } = iaFalsa(BOA)
  for (const ruim of [{ pergunta: 'x', origem: 'outro' }, { pergunta: '', origem: 'palpite' }, { pergunta: 'x'.repeat(301), origem: 'palpite' }, { pergunta: 'x', origem: 'palpite', email: EMAIL }, ['x']])
    assert.equal((await tratar(req(ruim), LIGADO(), chamar, AGORA)).status, 400, JSON.stringify(ruim))
  assert.equal(chamadas(), 0)
  const { kv } = kvFalso()
  await kv.put('classif|2026-10-05', '1')
  const cheio = await tratar(req({ pergunta: 'enchente mais feia de blumenal', origem: 'nao_entendi' }), { ...LIGADO(kv), CLASSIFICADOR_LIMITE_DIA: '1' }, chamar, AGORA)
  assert.equal(cheio.status, 429)
  assert.equal(chamadas(), 0)
})

test('confiança mínima configurável', async () => {
  const { chamar } = iaFalsa({ ...BOA, confianca: 0.8 })
  const r = await tratar(req({ pergunta: 'enchente mais feia de blumenal', origem: 'nao_entendi' }), { ...LIGADO(), CLASSIFICADOR_CONFIANCA_MINIMA: '0.85' }, chamar, AGORA)
  assert.deepEqual(((await r.json()) as { decisao: unknown }).decisao, { tipo: 'nao_sei', motivo: 'baixa_confianca' })
})

test('GET diz o motivo do desligado, sem revelar valores', async () => {
  const estado = async (amb: Ambiente, cab: Record<string, string> = { 'cf-access-authenticated-user-email': EMAIL }) =>
    (await tratar(new Request(URL_API, { headers: cab }), amb)).json()
  assert.deepEqual(await estado({ ...LIGADO(), ANTHROPIC_API_KEY: '' }), { ligado: false, motivo: 'sem_chave' })
  assert.deepEqual(await estado({ ...LIGADO(), CLASSIFICADOR_PILOTO: undefined }), { ligado: false, motivo: 'piloto_desligado' })
  assert.deepEqual(await estado({ ...LIGADO(), CLASSIFICADOR_EMAILS: ' , ' }), { ligado: false, motivo: 'lista_vazia' })
  assert.deepEqual(await estado(LIGADO(), {}), { ligado: false, motivo: 'sem_email' })
  assert.deepEqual(await estado(LIGADO(), { 'cf-access-authenticated-user-email': 'outro@x.org' }), { ligado: false, motivo: 'email_fora_da_lista' })
  assert.deepEqual(await estado(LIGADO()), { ligado: true })
})

test('sem o cabeçalho de e-mail, lê o e-mail do token do Access (Cf-Access-Jwt-Assertion)', async () => {
  const b64url = (o: unknown) => Buffer.from(JSON.stringify(o)).toString('base64url')
  const token = `${b64url({ alg: 'RS256' })}.${b64url({ email: 'Piloto@Exemplo.com', sub: 'x' })}.assinatura`
  const estado = async (cab: Record<string, string>) => (await tratar(new Request(URL_API, { headers: cab }), LIGADO())).json()
  assert.deepEqual(await estado({ 'cf-access-jwt-assertion': token }), { ligado: true })
  assert.deepEqual(await estado({ 'cf-access-jwt-assertion': 'lixo' }), { ligado: false, motivo: 'sem_email' })
  assert.deepEqual(await estado({ 'cf-access-jwt-assertion': `a.${b64url({ email: 'x@y.com' })}.b` }), { ligado: false, motivo: 'email_fora_da_lista' })
})
