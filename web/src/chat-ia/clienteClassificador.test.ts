/** O lado do aparelho do piloto do classificador, com `fetch` de mentira. */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { dados } from '../chat-local/testes/carregar'
import { EXEMPLOS, TEXTO_ALERTA, responder, type Classificacao } from '../chat-local/motor'
import { TEXTO_NAO_INTERPRETEI, classificarPergunta, decisaoValida, enviarCorrecao, mensagemDoPiloto, pilotoLigado, type Classificado } from './clienteClassificador'

const resp = (status: number, corpo: unknown) => new Response(JSON.stringify(corpo), { status })
const C: Classificacao = { intencao: 'maiores_cheias', cidade: 'blumenau', cidade2: null, rio: null, ano: null, ano_final: null, mes: null, nivel_m: null, quantidade: 1, rua: null }

test('pilotoLigado: só com "ligado: true"; tela de login ou falha conta como desligado', async () => {
  assert.equal(await pilotoLigado(async () => resp(200, { ligado: true })), true)
  assert.equal(await pilotoLigado(async () => resp(200, { ligado: false })), false)
  assert.equal(await pilotoLigado(async () => new Response('<html>login</html>')), false)
  assert.equal(await pilotoLigado(undefined), false)
})

test('classificarPergunta: corpo enviado; resposta conferida; erro, forma estranha e demora viram erro', async () => {
  let corpo: unknown = null
  const ok = await classificarPergunta(async (_u, init) => {
    corpo = JSON.parse(String(init?.body))
    return resp(200, { id: '2026-10-05_x', decisao: { tipo: 'ok', classificacao: C } })
  }, '  enchente mais feia de blumenal  ', 'nao_entendi')
  assert.deepEqual(corpo, { pergunta: 'enchente mais feia de blumenal', origem: 'nao_entendi' })
  assert.deepEqual(ok, { id: '2026-10-05_x', decisao: { tipo: 'ok', classificacao: C } })
  for (const r of [resp(504, { erro: 'tempo' }), resp(200, { id: 1, decisao: { tipo: 'ok', classificacao: C } }), resp(200, { id: null, decisao: { tipo: 'ok', classificacao: { ...C, extra: 1 } } }), resp(200, { id: null, decisao: { tipo: 'ok', classificacao: { ...C, intencao: 'apagar' } } }), new Response('<html>')])
    assert.deepEqual(await classificarPergunta(async () => r, 'x', 'palpite'), { erro: true })
  const inicio = Date.now()
  const lento = await classificarPergunta(() => new Promise<Response>(() => {}), 'x', 'palpite', 100)
  assert.deepEqual(lento, { erro: true })
  assert.ok(Date.now() - inicio < 1_000)
})

test('decisaoValida: faltou só com parâmetros conhecidos', () => {
  assert.equal(decisaoValida({ tipo: 'faltou', classificacao: C, faltam: ['cidade2'] }), true)
  assert.equal(decisaoValida({ tipo: 'faltou', classificacao: C, faltam: ['senha'] }), false)
  assert.equal(decisaoValida({ tipo: 'agora', origem: 'eu' }), false)
})

test('mensagem: ok mostra "Entendi" + resposta do motor + id para os botões', () => {
  const m = mensagemDoPiloto({ id: 'id1', decisao: { tipo: 'ok', classificacao: C } }, dados)
  assert.equal(m.entendido, 'a maior cheia de Blumenau')
  assert.equal(m.texto, responder('Qual foi a maior cheia de Blumenau?', dados).texto)
  assert.equal(m.idCorrecao, 'id1')
})

test('mensagem: agora → texto da Defesa Civil', () => {
  for (const origem of ['barreira', 'classificador'] as const)
    assert.deepEqual(mensagemDoPiloto({ id: null, decisao: { tipo: 'agora', origem } }, dados), { texto: TEXTO_ALERTA })
})

test('mensagem: faltou pede o parâmetro, sem responder', () => {
  const m = mensagemDoPiloto({ id: 'x', decisao: { tipo: 'faltou', classificacao: { ...C, intencao: 'transito', cidade: null, cidade2: 'blumenau' }, faltam: ['cidade'] } }, dados)
  assert.equal(m.texto, 'Entendi que a pergunta é sobre o tempo que a cheia leva entre duas cidades, mas faltou a cidade. Escreva de novo com isso, por favor.')
  assert.equal(m.idCorrecao, undefined)
})

test('mensagem: não sei, confiança baixa ou falha → "não consegui interpretar", nunca o palpite', () => {
  const palpite = responder('Estou com medo do rio em Blumenau, o que você acha?', dados)
  assert.equal(palpite.palpite, true)
  const falhas: Classificado[] = [{ erro: true }, { id: 'x', decisao: { tipo: 'nao_sei', motivo: 'baixa_confianca' } }, { id: 'x', decisao: { tipo: 'nao_sei', motivo: 'nao_sei' } }]
  for (const c of falhas) {
    const m = mensagemDoPiloto(c, dados)
    assert.ok(m.texto.startsWith(`${TEXTO_NAO_INTERPRETEI} Eu respondo só sobre o histórico`), m.texto)
    assert.deepEqual(m.sugestoes, EXEMPLOS)
    assert.notEqual(m.texto, palpite.texto)
    assert.equal(m.idCorrecao, undefined)
  }
})

test('enviarCorrecao: corpo fechado; falha de rede some', async () => {
  let corpo: unknown = null
  await enviarCorrecao(async (_u, init) => {
    corpo = JSON.parse(String(init?.body))
    return resp(200, { ok: true })
  }, 'id1', 'nao_era_isso')
  assert.deepEqual(corpo, { id: 'id1', correcao: 'nao_era_isso' })
  await enviarCorrecao(async () => {
    throw new Error('sem rede')
  }, 'id1', 'correto')
})
