/**
 * O núcleo do chat com IA, com um cliente FALSO (nenhum teste chama a API nem
 * gasta crédito). Trava: a barreira do presente vem antes da IA; as ferramentas
 * leem os dados do site com a escala de cada pico; o pedido à API tem o modelo,
 * a reserva por recusa e as ferramentas estritas; o laço tem teto.
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import type Anthropic from '@anthropic-ai/sdk'
import { dados } from '../chat-local/testes/carregar'
import { TEXTO_ALERTA } from '../chat-local/motor'
import {
  MAXIMO_RODADAS,
  MODELO_PADRAO,
  TEXTO_RECUSA,
  TEXTO_SEM_RESPOSTA,
  custoEstimado,
  executar,
  opcoesDoModelo,
  ferramentas,
  montarSistema,
  responderComIA,
  validarPedido,
  type Criar,
  type ParametrosCriacao,
} from './nucleo'

type BetaMessage = Anthropic.Beta.Messages.BetaMessage
const obter = async () => dados
const uso = { input_tokens: 100, output_tokens: 20, cache_creation_input_tokens: 0, cache_read_input_tokens: 0 }

function msg(stop_reason: string, content: unknown[]): BetaMessage {
  return { id: 'm', type: 'message', role: 'assistant', model: MODELO_PADRAO, content, stop_reason, usage: uso } as unknown as BetaMessage
}

/** Devolve as respostas em ordem e guarda os pedidos (cópia, porque o array de mensagens cresce). */
function falso(respostas: BetaMessage[]) {
  const pedidos: ParametrosCriacao[] = []
  const criar: Criar = async (p) => {
    pedidos.push(structuredClone(p))
    const r = respostas.shift()
    if (!r) throw new Error('chamada a mais')
    return r
  }
  return { criar, pedidos }
}

const json = async (nome: string, entrada: unknown) => {
  const r = await executar(nome, entrada, obter, dados)
  return { ...r, valor: r.erro ? null : JSON.parse(r.conteudo) }
}

test('validarPedido: esquema fechado e tamanhos', () => {
  assert.deepEqual(validarPedido({ pergunta: ' Maior cheia de Gaspar? ' }), { pergunta: 'Maior cheia de Gaspar?', anteriores: [] })
  assert.ok(validarPedido({ pergunta: 'x', anteriores: [{ pergunta: 'a', resposta: 'b' }] }))
  assert.equal(validarPedido({ pergunta: 'x', email: 'a@b' }), null)
  assert.equal(validarPedido({ pergunta: '' }), null)
  assert.equal(validarPedido({ pergunta: 'x'.repeat(501) }), null)
  assert.equal(validarPedido({ pergunta: 'x', anteriores: [1] }), null)
  assert.equal(validarPedido({ pergunta: 'x', anteriores: [{ pergunta: 'a', resposta: 'b', extra: 1 }] }), null)
  const tres = Array.from({ length: 3 }, () => ({ pergunta: 'a', resposta: 'b' }))
  assert.equal(validarPedido({ pergunta: 'x', anteriores: tres }), null)
  assert.equal(validarPedido([]), null)
  assert.equal(validarPedido(null), null)
})

test('pergunta sobre agora não chega à IA', async () => {
  const { criar, pedidos } = falso([])
  for (const p of ['O rio vai encher hoje em Blumenau?', 'Qual o nível atual em Rio do Sul?', 'Devo sair de casa?']) {
    const r = await responderComIA({ pergunta: p, anteriores: [] }, obter, criar)
    assert.equal(r.tipo, 'agora', p)
    assert.equal(r.texto, TEXTO_ALERTA)
  }
  assert.equal(pedidos.length, 0)
})

test('laço: ferramenta do motor, depois o texto; pedido com reserva e ferramentas estritas', async () => {
  const { criar, pedidos } = falso([
    msg('tool_use', [{ type: 'tool_use', id: 't1', name: 'consultar_motor', input: { pergunta: 'As 5 maiores cheias de Blumenau' } }]),
    msg('end_turn', [{ type: 'text', text: 'A maior cheia de Blumenau…' }]),
  ])
  const r = await responderComIA({ pergunta: 'Quais as piores enchentes que Blumenau já teve?', anteriores: [] }, obter, criar)
  assert.equal(r.tipo, 'ia')
  assert.equal(r.texto, 'A maior cheia de Blumenau…')
  // Dois pedidos de 100 de entrada e 20 de saída (o falso não usa cache).
  assert.deepEqual(r.uso, { modelo: MODELO_PADRAO, rodadas: 2, entrada: 200, cache_criado: 0, cache_lido: 0, saida: 40 })

  const [p1, p2] = pedidos
  assert.ok(p1 && p2)
  assert.equal(p1.model, MODELO_PADRAO)
  assert.deepEqual(p1.betas, ['server-side-fallback-2026-07-01'])
  assert.equal(p1.fallbacks, 'default')
  assert.equal(p1.thinking, undefined, 'Opus 5.5 não aceita desligar o raciocínio; o controle é o esforço')
  assert.equal(p1.output_config?.effort, 'low')
  assert.ok(p1.tools?.every((t) => 'strict' in t && t.strict === true))
  // O sistema é o mesmo nas duas rodadas (cache) e traz o aviso do presente.
  assert.equal(p1.system, p2.system)
  assert.ok(String(p1.system).includes(TEXTO_ALERTA))

  // A segunda rodada leva o resultado do motor, com a régua e a fonte.
  const ultima = p2.messages.at(-1)
  assert.ok(ultima && Array.isArray(ultima.content))
  const bloco = ultima.content[0] as { type: string; tool_use_id: string; content: string; is_error?: boolean }
  assert.equal(bloco.type, 'tool_result')
  assert.equal(bloco.tool_use_id, 't1')
  assert.equal(bloco.is_error, undefined)
  const resultado = JSON.parse(bloco.content)
  assert.equal(resultado.intencao, 'maiores_cheias')
  assert.match(resultado.texto, /Blumenau/)
})

test('trocas anteriores vão como contexto marcado, não como histórico', async () => {
  const { criar, pedidos } = falso([msg('end_turn', [{ type: 'text', text: 'ok' }])])
  await responderComIA({ pergunta: 'E em Gaspar?', anteriores: [{ pergunta: 'Maior cheia de Blumenau?', resposta: '1880, 17,10 m' }] }, obter, criar)
  const m = pedidos[0]?.messages
  assert.equal(m?.length, 1)
  assert.equal(m?.[0]?.role, 'user')
  assert.match(String(m?.[0]?.content), /^<anteriores>\nPergunta: Maior cheia de Blumenau\?\nResposta: 1880, 17,10 m\n<\/anteriores>\n\nE em Gaspar\?$/)
})

test('recusa vira texto fixo', async () => {
  const { criar } = falso([msg('refusal', [])])
  const r = await responderComIA({ pergunta: 'qualquer coisa', anteriores: [] }, obter, criar)
  assert.deepEqual([r.tipo, r.texto], ['recusa', TEXTO_RECUSA])
})

test('laço tem teto de rodadas; sem texto, resposta fixa', async () => {
  const sempre = Array.from({ length: MAXIMO_RODADAS }, (_, i) =>
    msg('tool_use', [{ type: 'tool_use', id: `t${i}`, name: 'tempos_de_descida', input: {} }]),
  )
  const { criar, pedidos } = falso(sempre)
  const r = await responderComIA({ pergunta: 'tempos', anteriores: [] }, obter, criar)
  assert.equal(pedidos.length, MAXIMO_RODADAS)
  assert.deepEqual([r.tipo, r.texto], ['sem_resposta', TEXTO_SEM_RESPOSTA])

  const vazio = falso([msg('end_turn', [])])
  assert.equal((await responderComIA({ pergunta: 'x', anteriores: [] }, obter, vazio.criar)).tipo, 'sem_resposta')
})

test('picos_da_cidade: escala de cada pico, filtro por ano, publicado guardado', async () => {
  const r = await json('picos_da_cidade', { cidade: 'blumenau', ano_inicial: 1983, ano_final: 1984 })
  assert.equal(r.erro, false)
  assert.ok(r.valor.total > 0)
  for (const p of r.valor.picos) {
    assert.ok(p.data >= '1983' && p.data < '1985', p.data)
    assert.ok(['regua', 'ibge', 'ana', 'nao-declarada', 'antes-da-regua'].includes(p.escala))
  }
  // Blumenau tem picos convertidos: o valor publicado vai junto.
  const todos = await json('picos_da_cidade', { cidade: 'blumenau', ano_inicial: null, ano_final: null })
  assert.ok(todos.valor.picos.some((p: { como_publicado?: string }) => p.como_publicado?.includes('convertido')))
  // Brusque antes de 2019 não é régua declarada.
  const br = await json('picos_da_cidade', { cidade: 'brusque', ano_inicial: null, ano_final: 2018 })
  assert.ok(br.valor.picos.length > 0)
  assert.ok(br.valor.picos.every((p: { escala: string }) => p.escala !== 'regua'))
  // Itajaí: aviso das várias réguas.
  assert.match((await json('picos_da_cidade', { cidade: 'itajai', ano_inicial: null, ano_final: null })).valor.atencao, /várias réguas/)
  assert.equal((await json('picos_da_cidade', { cidade: 'atlantida', ano_inicial: null, ano_final: null })).erro, true)
})

test('info_da_cidade e tempos_de_descida', async () => {
  const b = (await json('info_da_cidade', { cidade: 'blumenau' })).valor
  assert.equal(b.cotas_m.alerta, 6)
  assert.equal(b.cotas_nomes_na_fonte.emergencia, 'Alerta Máximo')
  assert.equal(b.cotas_nomes_na_fonte._por_que, undefined)
  const t = (await json('tempos_de_descida', {})).valor
  assert.ok(t.trechos.length > 0 && t.trechos.every((x: { horas_min: number; horas_max: number }) => x.horas_min <= x.horas_max))
  assert.ok(t.experimentais.length > 0)
  // Trecho em estudo sem número de horas nenhum (nem o "indício"): a tela não mostra.
  assert.ok(!/\d\s*(–|-|a)\s*\d+\s*h/.test(JSON.stringify(t.experimentais)), JSON.stringify(t.experimentais))
  assert.equal((await executar('apagar_tudo', {}, obter, dados)).erro, true)
})

test('ferramentas cobrem todas as cidades e o sistema é estável', () => {
  const ids = new Set(Object.values(dados.estacoes.rios).flatMap((r) => r.cidades.map((c) => c.id)))
  const t = ferramentas(dados).find((x) => x.name === 'picos_da_cidade')
  const enumIds = (t?.input_schema.properties as { cidade: { enum: string[] } }).cidade.enum
  assert.deepEqual(new Set(enumIds), ids)
  assert.equal(enumIds.length, ids.size, 'Itajaí aparece uma vez só')
  assert.equal(montarSistema(dados), montarSistema(dados))
})

test('custo estimado pela tabela de preços; modelo desconhecido fica sem custo', () => {
  const u = { modelo: 'claude-opus-5-5', rodadas: 2, entrada: 6_000, cache_criado: 1_000, cache_lido: 2_000, saida: 1_000 }
  // 6000×4 + 1000×5 + 2000×0,20 + 1000×20 = 49.400 por milhão = US$ 0,0494
  assert.equal(custoEstimado(u), 0.0494)
  assert.equal(custoEstimado({ ...u, modelo: 'claude-sonnet-5-5' }), 0.0249)
  assert.equal(custoEstimado({ ...u, modelo: 'modelo-novo' }), null)
})

test('parâmetros por modelo: Haiku sem esforço nem reserva; linha 5 com os dois', () => {
  assert.deepEqual(opcoesDoModelo('claude-haiku-4-5'), {})
  for (const m of ['claude-opus-5-5', 'claude-sonnet-5-5'])
    assert.deepEqual(opcoesDoModelo(m), { output_config: { effort: 'low' }, betas: ['server-side-fallback-2026-07-01'], fallbacks: 'default' }, m)
  assert.deepEqual(opcoesDoModelo('claude-sonnet-4-6'), { output_config: { effort: 'low' } })
})
