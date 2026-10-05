/**
 * Piloto do classificador (docs/PILOTO-CLASSIFICADOR.md). Trava as regras de segurança:
 * barreira antes da IA, `situacao_atual: false` nunca a desfaz, listas fechadas, confiança
 * mínima, obrigatórios, e o texto da resposta saindo do motor.
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import type { Message } from '@anthropic-ai/sdk/resources/messages/messages'
import { dados } from '../chat-local/testes/carregar'
import { INTENCOES, OBRIGATORIOS, TEXTO_ALERTA, descreverEntendido, responder, responderPorIntencao, type Classificacao } from '../chat-local/motor'
import { CONFIANCA_MINIMA_PADRAO, classificar, decidir, esquema, instrucoes, mascarar, pedido, validar, type SaidaClassificador } from './classificador'

const OPC = { confiancaMinima: CONFIANCA_MINIMA_PADRAO, anoAtual: 2026 }

const saida = (x: Partial<SaidaClassificador> = {}): SaidaClassificador => ({
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
  motivo_curto: 'pede o recorde de Blumenau',
  nao_sei: false,
  ...x,
})

test('classificação boa: a resposta sai do motor, igual à do roteador', () => {
  const { decisao } = decidir('qual foi a enchente mais feia que blumenal já viu', saida(), dados, OPC)
  assert.equal(decisao.tipo, 'ok')
  if (decisao.tipo !== 'ok') return
  const r = responderPorIntencao(decisao.classificacao, dados)
  assert.equal(r.texto, responder('Qual foi a maior cheia de Blumenau?', dados).texto)
  assert.equal(descreverEntendido(decisao.classificacao, dados), 'a maior cheia de Blumenau')
})

test('barreira determinística vem antes: situacao_atual false NUNCA a desfaz', () => {
  for (const q of ['O rio vai subir hoje em Blumenau?', 'Qual a previsão para Gaspar?', 'Devo sair de casa?']) {
    const { decisao } = decidir(q, saida({ situacao_atual: false, confianca: 1 }), dados, OPC)
    assert.deepEqual(decisao, { tipo: 'agora', origem: 'barreira' }, q)
  }
})

test('situacao_atual true liga a barreira, mesmo com o resto inválido ou com confiança baixa', () => {
  for (const bruto of [saida({ situacao_atual: true }), saida({ situacao_atual: true, cidade: 'paris' }), saida({ situacao_atual: true, confianca: 0.1, nao_sei: true }), { situacao_atual: true }])
    assert.deepEqual(decidir('A Beira-Rio está transitável?', bruto, dados, OPC).decisao, { tipo: 'agora', origem: 'classificador' })
})

test('nao_sei, intenção "nao_sei" e confiança abaixo do limite: não responde', () => {
  assert.deepEqual(decidir('x', saida({ nao_sei: true }), dados, OPC).decisao, { tipo: 'nao_sei', motivo: 'nao_sei' })
  assert.deepEqual(decidir('x', saida({ intencao: 'nao_sei', confianca: 0.99 }), dados, OPC).decisao, { tipo: 'nao_sei', motivo: 'nao_sei' })
  assert.deepEqual(decidir('x', saida({ confianca: 0.69 }), dados, OPC).decisao, { tipo: 'nao_sei', motivo: 'baixa_confianca' })
  assert.equal(decidir('x', saida({ confianca: 0.7 }), dados, OPC).decisao.tipo, 'ok')
  assert.deepEqual(decidir('x', null, dados, OPC).decisao, { tipo: 'nao_sei', motivo: 'sem_saida' })
})

test('listas fechadas: valor fora vira "não sei", nunca conserto', () => {
  const ruins: Partial<SaidaClassificador>[] = [
    { intencao: 'apagar_tudo' as never },
    { cidade: 'florianopolis' },
    { cidade2: 'BLUMENAU' },
    { rio: 'itajai' as never },
    { ano: 1700 },
    { ano: 2027 },
    { ano: 2008.5 },
    { ano: 2011, ano_final: 2008 },
    { ano: null, ano_final: 2008 },
    { mes: 13 },
    { nivel_m: -1 },
    { nivel_m: 99 },
    { quantidade: 50 },
    { rua: '<script>' },
    { rua: 'x'.repeat(61) },
    { confianca: 1.5 },
    { situacao_atual: 'nao' as never },
    { intencao: 'cota_ana', cidade: 'gaspar', ano: 2008 },
  ]
  for (const r of ruins) assert.deepEqual(decidir('x', saida(r), dados, OPC).decisao, { tipo: 'nao_sei', motivo: 'invalida' }, JSON.stringify(r))
  assert.ok('invalida' in validar('texto', dados, 2026))
  assert.ok('invalida' in validar([saida()], dados, 2026))
})

test('faltou parâmetro obrigatório: pede, não responde', () => {
  const { decisao } = decidir('quanto tempo a água demora pra chegar em blumenau', saida({ intencao: 'transito', cidade: null, cidade2: 'blumenau', quantidade: null }), dados, OPC)
  assert.equal(decisao.tipo, 'faltou')
  if (decisao.tipo === 'faltou') assert.deepEqual(decisao.faltam, ['cidade'])
  // Toda intenção tem a lista de obrigatórios.
  assert.deepEqual(Object.keys(OBRIGATORIOS).sort(), [...INTENCOES].sort())
})

test('cada intenção, com os obrigatórios, gera resposta do motor (nunca "não entendi")', () => {
  const base: Classificacao = { intencao: 'maiores_cheias', cidade: null, cidade2: null, rio: null, ano: null, ano_final: null, mes: null, nivel_m: null, quantidade: null, rua: null }
  const casos: Classificacao[] = [
    { ...base, intencao: 'maiores_cheias', cidade: 'rio-do-sul', quantidade: 3 },
    { ...base, intencao: 'cheias_periodo', cidade: 'gaspar', ano: 2011 },
    { ...base, intencao: 'contar_acima', cidade: 'rio-do-sul', nivel_m: 10 },
    { ...base, intencao: 'atlas', ano: 2011, mes: 9 },
    { ...base, intencao: 'chuva', ano: 2008, mes: 11 },
    { ...base, intencao: 'transito', cidade: 'rio-do-sul', cidade2: 'blumenau' },
    { ...base, intencao: 'cota_ana', cidade: 'brusque', ano: 2008, mes: 11 },
    { ...base, intencao: 'antecedencia_mirim' },
    { ...base, intencao: 'rua_historico', cidade: 'blumenau', rua: 'São Rafael' },
    { ...base, intencao: 'cotas', cidade: 'blumenau' },
    { ...base, intencao: 'comparacao', cidade: 'blumenau', cidade2: 'gaspar', ano: 2008 },
    { ...base, intencao: 'media', cidade: 'blumenau', ano: 2000, ano_final: 2026 },
  ]
  for (const c of casos) {
    const r = responderPorIntencao(c, dados)
    assert.equal(r.intencao, c.intencao, c.intencao)
    assert.equal(r.falha, undefined, c.intencao)
    assert.ok(descreverEntendido(c, dados).length > 5)
  }
  // A média lê o intervalo; o ano único continua ano único.
  assert.match(responderPorIntencao(casos[11]!, dados).texto, /desde 2000 até 2026/)
  assert.match(responderPorIntencao({ ...casos[11]!, ano_final: null, ano: 2011 }, dados).texto, /em 2011/)
  // A rua vem sem "rua" e acha a mesma cota do roteador.
  assert.equal(
    responderPorIntencao(casos[8]!, dados).texto,
    responder('Quantas cheias chegaram à cota da Rua São Rafael em Blumenau?', dados).texto,
  )
})

test('o pedido à API: esquema fechado, sem ferramenta, Haiku sem effort, instruções com as cidades', () => {
  const p = pedido('pergunta', dados, 'claude-haiku-4-5', 2026)
  assert.equal(p.tools, undefined)
  assert.equal(p.tool_choice, undefined)
  assert.deepEqual(Object.keys(p.output_config ?? {}), ['format'])
  assert.equal(p.temperature, 0)
  const s = esquema(dados) as { properties: Record<string, { enum?: string[] }>; required: string[]; additionalProperties: boolean }
  assert.equal(s.additionalProperties, false)
  assert.deepEqual([...s.required].sort(), Object.keys(s.properties).sort())
  assert.ok(s.properties.intencao!.enum!.includes('nao_sei'))
  const p5 = pedido('pergunta', dados, 'claude-sonnet-5-5', 2026)
  assert.equal(p5.output_config?.effort, 'low')
  assert.equal(p5.temperature, undefined)
  const sys = instrucoes(dados, 2026)
  assert.match(sys, /blumenau \(Blumenau\)/)
  assert.match(sys, /situacao_atual = true/)
  assert.match(sys, /"desde 2000" → 2000 e 2026/)
  assert.match(String((p.messages[0]!.content as string)), /"""\npergunta\n"""/)
})

test('classificar: lê o JSON, soma tokens; recusa ou corte viram "sem saída"', async () => {
  const msg = (stop: string, texto: string) =>
    ({ model: 'claude-haiku-4-5-20251001', stop_reason: stop, content: [{ type: 'text', text: texto }], usage: { input_tokens: 1500, output_tokens: 80, cache_read_input_tokens: 0, cache_creation_input_tokens: 0 } }) as unknown as Message
  const ok = await classificar('q', dados, async () => msg('end_turn', JSON.stringify(saida())), 'claude-haiku-4-5', 2026)
  assert.deepEqual(ok.bruto, saida())
  assert.equal(ok.uso.entrada, 1500)
  for (const [stop, t] of [['refusal', '{}'], ['max_tokens', '{"intencao":'], ['end_turn', 'não é json']] as const) {
    const c = await classificar('q', dados, async () => msg(stop, t), 'claude-haiku-4-5', 2026)
    assert.equal(c.bruto, null)
    assert.deepEqual(decidir('q', c.bruto, dados, OPC).decisao, { tipo: 'nao_sei', motivo: 'sem_saida' })
  }
})

test('máscara do registro: tira e-mail, telefone e número da casa; mantém anos e metros', () => {
  assert.equal(mascarar('meu email é ana@x.com.br'), 'meu email é [e-mail]')
  assert.equal(mascarar('ligue 47 99999-1234'), 'ligue [número]')
  assert.equal(mascarar('moro na rua XV de Novembro, 1234 em Blumenau'), 'moro na rua XV de Novembro, [nº] em Blumenau')
  assert.equal(mascarar('Rua São Rafael nº 55 alaga?'), 'Rua São Rafael, [nº] alaga?')
  assert.equal(mascarar('cheias de 2008, 2011 e 2015 acima de 10 m'), 'cheias de 2008, 2011 e 2015 acima de 10 m')
  assert.equal(mascarar('de 1983 1984'), 'de 1983 1984')
  assert.equal(mascarar('x'.repeat(400)).length, 300)
})

test('o texto do motor para "agora" é o mesmo do chat', () => {
  assert.equal(responder('o rio vai subir hoje?', dados).texto, TEXTO_ALERTA)
})

test('"maior cheia" com ano vira "cheias do período" (achado da prova com a API: "enchente de 84 em blumenau")', () => {
  const { decisao } = decidir('qual a altura da enchente de 84 em blumenau', saida({ ano: 1984, quantidade: null }), dados, OPC)
  assert.equal(decisao.tipo, 'ok')
  if (decisao.tipo !== 'ok') return
  assert.equal(decisao.classificacao.intencao, 'cheias_periodo')
  const r = responderPorIntencao(decisao.classificacao, dados)
  assert.equal(r.texto, responder('cheias de Blumenau em 1984', dados).texto)
  assert.doesNotMatch(r.texto, /1880/)
  // Sem ano, continua o recorde.
  assert.equal((decidir('x', saida(), dados, OPC).decisao as { classificacao: Classificacao }).classificacao.intencao, 'maiores_cheias')
})

test('instruções (c2): parâmetro faltando não baixa a confiança; "teve enchente em ANO" é Atlas; "84" é 1984', () => {
  const sys = instrucoes(dados, 2026)
  assert.match(sys, /NÃO baixa a confiança/)
  assert.match(sys, /teve enchente em 2023/)
  assert.match(sys, /"84" → 1984/)
})

test('faltando parâmetro, o limite é 0,5: a tela só pede (c3, achado da prova: o modelo dá 0,6 quando falta a cidade)', () => {
  const transito = saida({ intencao: 'transito', cidade: null, cidade2: 'blumenau', quantidade: null })
  assert.equal(decidir('quanto tempo a água leva pra chegar em blumenau?', { ...transito, confianca: 0.6 }, dados, OPC).decisao.tipo, 'faltou')
  assert.deepEqual(decidir('x', { ...transito, confianca: 0.45 }, dados, OPC).decisao, { tipo: 'nao_sei', motivo: 'baixa_confianca' })
  // Com tudo preenchido, continua 0,7.
  assert.deepEqual(decidir('x', saida({ confianca: 0.6 }), dados, OPC).decisao, { tipo: 'nao_sei', motivo: 'baixa_confianca' })
  // Instrução c3: com cidade, "X encheu em ANO?" é cheias_periodo.
  assert.match(instrucoes(dados, 2026), /Com cidade e sem falar de danos, é cheias_periodo/)
})
