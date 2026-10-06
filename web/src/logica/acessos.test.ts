/**
 * O registro de acessos e a lista do admin (`web/functions/api/acessos.ts`, 06/10/2026), com KV de mentira.
 * Trava: só abertura de página conta, no máximo uma escrita a cada 15 min, dias contados no calendário de
 * Brasília, expiração de 90 dias, e 404 para quem não é admin — inclusive quem está logado.
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  INTERVALO_MIN,
  RETENCAO_DIAS,
  eAberturaDePagina,
  montarLista,
  proximoRegistro,
  registrarAcesso,
  tratar,
  type Ambiente,
  type ArmazemAcessos,
  type RegistroAcesso,
} from '../../functions/api/acessos'

const ADMIN = 'haohmarusc@gmail.com'

function kvFalso() {
  const dados = new Map<string, { valor: string; metadata?: unknown; ttl?: number }>()
  let escritas = 0
  const kv: ArmazemAcessos = {
    get: async (k) => dados.get(k)?.valor ?? null,
    put: async (k, v, o) => {
      escritas++
      dados.set(k, { valor: v, metadata: o?.metadata, ttl: o?.expirationTtl })
    },
    list: async ({ prefix }) => ({
      keys: [...dados].filter(([k]) => k.startsWith(prefix)).map(([name, d]) => ({ name, metadata: d.metadata })),
      list_complete: true,
    }),
  }
  return { kv, dados, escritas: () => escritas }
}

const pagina = (email: string | null, caminho = '/', accept = 'text/html,application/xhtml+xml') =>
  new Request(`https://enchentes.premercadosc.com${caminho}`, {
    headers: { accept, ...(email ? { 'cf-access-authenticated-user-email': email } : {}) },
  })

test('só abertura de página conta: HTML fora de /api', () => {
  assert.equal(eAberturaDePagina(pagina('a@b.com')), true)
  assert.equal(eAberturaDePagina(pagina('a@b.com', '/assets/app.js', '*/*')), false)
  assert.equal(eAberturaDePagina(pagina('a@b.com', '/api/acessos')), false)
  assert.equal(eAberturaDePagina(new Request('https://x.com/', { method: 'POST', headers: { accept: 'text/html' } })), false)
})

test('primeiro acesso, escrita no máximo a cada 15 min e dias pelo calendário de Brasília', () => {
  const t0 = new Date('2026-10-06T02:30:00Z') // 05/10 23:30 em Brasília
  const r0 = proximoRegistro(null, 'a@b.com', t0)!
  assert.deepEqual(r0, { email: 'a@b.com', primeiro: t0.toISOString(), ultimo: t0.toISOString(), dias: 1, ultimo_dia: '2026-10-05' })
  assert.equal(proximoRegistro(r0, 'a@b.com', new Date(t0.getTime() + (INTERVALO_MIN - 1) * 60_000)), null)
  const r1 = proximoRegistro(r0, 'a@b.com', new Date('2026-10-06T02:50:00Z'))! // ainda 05/10 em Brasília
  assert.equal(r1.dias, 1)
  const r2 = proximoRegistro(r1, 'a@b.com', new Date('2026-10-06T03:10:00Z'))! // 06/10 00:10 em Brasília
  assert.deepEqual([r2.dias, r2.ultimo_dia, r2.primeiro], [2, '2026-10-06', t0.toISOString()])
})

test('registrarAcesso grava e-mail e datas, com expiração e metadata; sem e-mail ou sem KV, nada', async () => {
  const { kv, dados, escritas } = kvFalso()
  const amb: Ambiente = { CHAT_IA: kv }
  const t = new Date('2026-10-06T12:00:00Z')
  await registrarAcesso(pagina('Pessoa@Exemplo.com'), amb, t)
  await registrarAcesso(pagina('pessoa@exemplo.com'), amb, new Date(t.getTime() + 60_000)) // 1 min depois: não escreve
  await registrarAcesso(pagina(null), amb, t)
  await registrarAcesso(pagina('x@y.com', '/assets/a.js', '*/*'), amb, t)
  await registrarAcesso(pagina('x@y.com'), {}, t)
  assert.equal(escritas(), 1)
  const d = dados.get('acesso|pessoa@exemplo.com')!
  assert.equal(d.ttl, RETENCAO_DIAS * 86_400)
  assert.deepEqual(d.metadata, JSON.parse(d.valor))
  assert.deepEqual(Object.keys(JSON.parse(d.valor)).sort(), ['dias', 'email', 'primeiro', 'ultimo', 'ultimo_dia'])
})

test('a lista: logados agora (15 min) e todos do mais recente ao mais antigo', () => {
  const agora = new Date('2026-10-06T12:00:00Z')
  const reg = (email: string, min: number): RegistroAcesso => {
    const iso = new Date(agora.getTime() - min * 60_000).toISOString()
    return { email, primeiro: iso, ultimo: iso, dias: 1, ultimo_dia: '2026-10-06' }
  }
  const l = montarLista([reg('velho@x.com', 300), reg('agora@x.com', 5), reg('quase@x.com', 16)], agora)
  assert.deepEqual(l.agora.map((r) => r.email), ['agora@x.com'])
  assert.deepEqual(l.todos.map((r) => r.email), ['agora@x.com', 'quase@x.com', 'velho@x.com'])
})

test('a API: 404 para quem não é admin (mesmo logado) e para todos sem ADMIN_EMAILS; a lista para o admin', async () => {
  const { kv } = kvFalso()
  const t = new Date('2026-10-06T12:00:00Z')
  await registrarAcesso(pagina('outra@x.com'), { CHAT_IA: kv }, t)
  const api = (email: string | null) => pagina(email, '/api/acessos', 'application/json')
  assert.equal((await tratar(api('outra@x.com'), { CHAT_IA: kv, ADMIN_EMAILS: ADMIN }, t)).status, 404)
  assert.equal((await tratar(api(null), { CHAT_IA: kv, ADMIN_EMAILS: ADMIN }, t)).status, 404)
  assert.equal((await tratar(api(ADMIN), { CHAT_IA: kv }, t)).status, 404)
  const r = await tratar(api(ADMIN.toUpperCase()), { CHAT_IA: kv, ADMIN_EMAILS: ` ${ADMIN} ` }, t)
  assert.equal(r.status, 200)
  assert.equal(r.headers.get('cache-control'), 'no-store')
  const corpo = (await r.json()) as { agora: RegistroAcesso[]; todos: RegistroAcesso[] }
  assert.deepEqual(corpo.todos.map((x) => x.email), ['outra@x.com'])
  assert.deepEqual(corpo.agora.map((x) => x.email), ['outra@x.com'])
})
