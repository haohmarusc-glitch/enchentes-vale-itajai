/** O lado do aparelho do chat com IA, com `fetch` de mentira. */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { anterioresParaEnvio, iaLigada, perguntarIA } from './cliente'

const resp = (status: number, corpo: unknown) => new Response(JSON.stringify(corpo), { status })

test('iaLigada: só com "ligado: true"; falha conta como desligada', async () => {
  assert.equal(await iaLigada(async () => resp(200, { ligado: true })), true)
  assert.equal(await iaLigada(async () => resp(200, { ligado: false })), false)
  assert.equal(await iaLigada(async () => resp(404, {})), false)
  assert.equal(await iaLigada(async () => new Response('<html>login</html>', { status: 200 })), false)
  assert.equal(
    await iaLigada(async () => {
      throw new Error('sem rede')
    }),
    false,
  )
  assert.equal(await iaLigada(undefined), false)
})

test('perguntarIA: corpo enviado e respostas do servidor', async () => {
  let enviado: { pergunta: string; anteriores: unknown[] } | null = null
  const r = await perguntarIA(
    async (_url, init) => {
      enviado = JSON.parse(String(init?.body))
      return resp(200, { tipo: 'ia', texto: 'ok' })
    },
    '  Maior cheia de Gaspar?  ',
    [{ pergunta: 'a', resposta: 'b' }],
  )
  assert.deepEqual(r, { tipo: 'ia', texto: 'ok' })
  assert.deepEqual(enviado, { pergunta: 'Maior cheia de Gaspar?', anteriores: [{ pergunta: 'a', resposta: 'b' }] })

  assert.match((await perguntarIA(async () => resp(429, { erro: 'limite_do_dia' }), 'x', [])).texto, /máximo de perguntas de hoje/)
  assert.match((await perguntarIA(async () => resp(503, { erro: 'desligado' }), 'x', [])).texto, /desligada/)
  assert.equal((await perguntarIA(async () => resp(502, { erro: 'ia' }), 'x', [])).tipo, 'erro')
  assert.equal((await perguntarIA(async () => resp(200, { tipo: 'hack', texto: 'x' }), 'x', [])).tipo, 'erro')
  assert.equal((await perguntarIA(async () => new Response('<html>', { status: 200 }), 'x', [])).tipo, 'erro')
  const semRede = await perguntarIA(async () => {
    throw new Error('offline')
  }, 'x', [])
  assert.match(semRede.texto, /chat sem IA continua/)
})

test('anteriores: só as duas últimas, cortadas no tamanho aceito', () => {
  const t = [1, 2, 3].map((i) => ({ pergunta: `p${i}`, resposta: 'r'.repeat(2000) }))
  const a = anterioresParaEnvio(t)
  assert.deepEqual(a.map((x) => x.pergunta), ['p2', 'p3'])
  assert.ok(a.every((x) => x.resposta.length === 1500 && x.resposta.endsWith('…')))
})
