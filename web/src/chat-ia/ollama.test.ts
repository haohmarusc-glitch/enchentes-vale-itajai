/**
 * O adaptador do Ollama com um servidor FALSO (o formato é o de `POST /api/chat`
 * documentado pelo Ollama). Trava: barreira antes do modelo, ferramentas no formato
 * de função, contexto de 16 mil, laço de ferramentas, chamada escrita como texto,
 * <think> removido e erro HTTP como exceção.
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { dados } from '../chat-local/testes/carregar'
import { TEXTO_ALERTA } from '../chat-local/motor'
import { MAXIMO_RODADAS, TEXTO_SEM_RESPOSTA } from './nucleo'
import { CONTEXTO_PADRAO, argumentos, chamadaEmTexto, ferramentasOllama, responderComOllama, semPensamento, type RodadaOllama } from './ollama'

const obter = async () => dados

function servidor(respostas: unknown[], status = 200) {
  const pedidos: { url: string; corpo: Record<string, unknown> }[] = []
  const buscar = async (url: string, init: RequestInit) => {
    pedidos.push({ url, corpo: JSON.parse(String(init.body)) })
    const r = respostas.shift()
    if (r === undefined) throw new Error('chamada a mais')
    return new Response(JSON.stringify(r), { status })
  }
  return { buscar, pedidos }
}

const msg = (content: string, tool_calls?: unknown[]) => ({
  model: 'qwen2.5:3b',
  message: { role: 'assistant', content, ...(tool_calls ? { tool_calls } : {}) },
  done: true,
  prompt_eval_count: 1000,
  eval_count: 50,
})

test('barreira do presente: nem chama o Ollama', async () => {
  const { buscar, pedidos } = servidor([])
  const r = await responderComOllama({ pergunta: 'O rio vai subir hoje?', anteriores: [] }, obter, { modelo: 'qwen2.5:3b', buscar })
  assert.deepEqual([r.tipo, r.texto], ['agora', TEXTO_ALERTA])
  assert.equal(pedidos.length, 0)
})

test('ferramenta do motor e resposta; pedido no formato do Ollama', async () => {
  const { buscar, pedidos } = servidor([
    msg('', [{ function: { name: 'consultar_motor', arguments: { pergunta: 'Qual foi a maior cheia de Blumenau?' } } }]),
    msg('<think>rascunho</think>A maior cheia de Blumenau foi de 17,3 m, em 1880.'),
  ])
  const rodadas: RodadaOllama[] = []
  const r = await responderComOllama({ pergunta: 'Qual a maior enchente de Blumenau?', anteriores: [] }, obter, { modelo: 'qwen2.5:3b', buscar, url: 'http://pc:11434/' }, rodadas)
  assert.equal(r.tipo, 'ia')
  assert.equal(r.texto, 'A maior cheia de Blumenau foi de 17,3 m, em 1880.')
  assert.deepEqual(r.uso, { modelo: 'ollama:qwen2.5:3b', rodadas: 2, entrada: 2000, cache_criado: 0, cache_lido: 0, saida: 100 })
  assert.equal(rodadas.length, 2)

  const [p1, p2] = pedidos
  assert.equal(p1?.url, 'http://pc:11434/api/chat')
  assert.equal(p1?.corpo.stream, false)
  assert.deepEqual(p1?.corpo.options, { num_ctx: CONTEXTO_PADRAO, temperature: 0 })
  const m1 = p1?.corpo.messages as { role: string; content: string }[]
  assert.deepEqual(m1.map((m) => m.role), ['system', 'user'])
  assert.ok(m1[0]!.content.includes(TEXTO_ALERTA), 'as mesmas instruções do chat com IA')
  // A segunda rodada leva o resultado do motor como mensagem de ferramenta.
  const m2 = p2?.corpo.messages as { role: string; content: string; tool_name?: string }[]
  assert.deepEqual(m2.map((m) => m.role), ['system', 'user', 'assistant', 'tool'])
  assert.equal(m2[3]!.tool_name, 'consultar_motor')
  assert.match(m2[3]!.content, /17,3 m/)
})

test('chamada de ferramenta escrita como texto (modelo pequeno) também roda', async () => {
  const { buscar, pedidos } = servidor([
    msg('```json\n{"name": "picos_da_cidade", "arguments": {"cidade": "gaspar", "ano_inicial": 2008, "ano_final": 2008}}\n```'),
    msg('Em 2008, Gaspar chegou a 9,8 m.'),
  ])
  const r = await responderComOllama({ pergunta: 'Cheia de Gaspar em 2008?', anteriores: [] }, obter, { modelo: 'x', buscar })
  assert.equal(r.texto, 'Em 2008, Gaspar chegou a 9,8 m.')
  const ferramenta = (pedidos[1]?.corpo.messages as { role: string; content: string }[]).at(-1)!
  assert.equal(ferramenta.role, 'tool')
  assert.match(ferramenta.content, /9\.8/)
})

test('ferramenta desconhecida volta como erro para o modelo; laço tem teto', async () => {
  const sempre = Array.from({ length: MAXIMO_RODADAS }, () => msg('', [{ function: { name: 'apagar_tudo', arguments: '{}' } }]))
  const { buscar, pedidos } = servidor(sempre)
  const r = await responderComOllama({ pergunta: 'x', anteriores: [] }, obter, { modelo: 'x', buscar })
  assert.equal(pedidos.length, MAXIMO_RODADAS)
  assert.deepEqual([r.tipo, r.texto], ['sem_resposta', TEXTO_SEM_RESPOSTA])
  const ultima = (pedidos.at(-1)?.corpo.messages as { content: string }[]).at(-1)!
  assert.match(ultima.content, /^ERRO: ferramenta desconhecida/)
})

test('erro do Ollama (modelo não baixado) sobe como exceção', async () => {
  const { buscar } = servidor([{ error: 'model "qwen9:1b" not found, try pulling it first' }], 404)
  await assert.rejects(responderComOllama({ pergunta: 'Maior cheia de Gaspar?', anteriores: [] }, obter, { modelo: 'qwen9:1b', buscar }), /not found/)
})

test('auxiliares: formato de função, argumentos, <think>, texto que não é chamada', () => {
  const t = ferramentasOllama(dados)
  assert.ok(t.length >= 4 && t.every((x) => x.type === 'function' && x.function.parameters && !('strict' in x.function)))
  assert.deepEqual(argumentos('{"a":1}'), { a: 1 })
  assert.deepEqual(argumentos({ a: 1 }), { a: 1 })
  assert.deepEqual(argumentos('não é json'), {})
  assert.equal(semPensamento('<think>x</think> ok'), 'ok')
  const nomes = new Set(t.map((x) => x.function.name))
  assert.equal(chamadaEmTexto('A maior cheia foi em 1880.', nomes), null)
  assert.equal(chamadaEmTexto('{"name": "rm", "arguments": {}}', nomes), null)
})
