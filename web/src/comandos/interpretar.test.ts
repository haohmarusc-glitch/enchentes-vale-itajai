import { test } from 'node:test'
import assert from 'node:assert/strict'
import { interpretar, normalizar } from './interpretar'
import { catalogoDoCadastro } from './catalogo'
import { readFileSync } from 'node:fs'
import type { Contexto } from './tipos'

const estacoes = JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'))
const cat = catalogoDoCadastro(estacoes)
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const emItajai: Contexto = { cidadeAtual: 'itajai', naMonitor: true, reguaAtual: null }
const emTimbo: Contexto = { cidadeAtual: 'timbo', naMonitor: true, reguaAtual: null }

const passos = (texto: string, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', `"${texto}" devia virar comando, veio ${JSON.stringify(r)}`)
  return r.passos
}

test('o catálogo sai do cadastro: 19 cidades e as onze réguas DC de Itajaí', () => {
  assert.equal(new Set(cat.cidades.map((c) => c.id)).size, cat.cidades.length)
  assert.ok(cat.cidades.some((c) => c.id === 'guabiruba' && c.rio === 'mirim'))
  assert.deepEqual(cat.reguas.map((r) => r.codigo), Array.from({ length: 11 }, (_, i) => `DC-${String(i + 1).padStart(2, '0')}`))
  assert.equal(cat.reguas.find((r) => r.codigo === 'DC-05')?.nome, 'Sítio Sr. Hilário')
})

test('normalizar tira acento, pontuação e hífen', () => {
  assert.equal(normalizar('Zoom na régua DC-05!'), 'zoom na regua dc 05')
})

test('pergunta continua pergunta: nada de mapa sem pedido', () => {
  for (const q of [
    'Como está Blumenau?',
    'mostrar as 5 maiores cheias de Brusque',
    'qual a maior cheia de Blumenau e Gaspar?',
    'quanto tempo a cheia leva de Rio do Sul até Blumenau?',
    'Rua XV de Novembro, Blumenau',
  ]) {
    assert.equal(interpretar(q, cat, fora), null, q)
  }
  // 18ª entrega: só o nome da cidade pergunta o que a pessoa quer dela (antes ia ao motor, que palpitava "maiores cheias").
  const so = interpretar('Blumenau', cat, fora)
  assert.ok(so && so.tipo === 'esclarecer' && /O que você quer saber de Blumenau/.test(so.texto) && so.sugestoes.includes('mostrar Blumenau'), JSON.stringify(so))
})

test('cidade: exige verbo, aceita cortesia, resolve pelo cadastro', () => {
  assert.deepEqual(passos('mostrar Blumenau'), [{ tipo: 'ir_cidade', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('por favor, vá para Rio do Sul'), [{ tipo: 'ir_cidade', cidadeId: 'rio-do-sul' }])
  assert.deepEqual(passos('abrir Trombudo Central no mapa'), [{ tipo: 'ir_cidade', cidadeId: 'trombudo-central' }])
  assert.equal(interpretar('mostrar Pomerode', cat, fora), null) // fora do cadastro: não vira comando
})

test('régua por código, por nome e por cidade', () => {
  assert.deepEqual(passos('zoom na régua DC-05'), [{ tipo: 'escolher_regua', codigo: 'DC-05' }])
  assert.deepEqual(passos('zoom na dc 5'), [{ tipo: 'escolher_regua', codigo: 'DC-05' }])
  assert.deepEqual(passos('mostrar a régua do Rio do Meio'), [{ tipo: 'escolher_regua', codigo: 'DC-08' }])
  assert.deepEqual(passos('régua de Blumenau'), [{ tipo: 'ir_cidade', cidadeId: 'blumenau' }, { tipo: 'aproximar_regua' }])
  assert.deepEqual(passos('todas as réguas'), [{ tipo: 'escolher_regua', codigo: 'todas' }])
})

test('régua inexistente ou ambígua: pergunta, nunca escolhe', () => {
  const inexistente = interpretar('zoom na régua DC-40', cat, fora)
  assert.equal(inexistente?.tipo, 'esclarecer')
  const murta = interpretar('zoom na régua da Murta', cat, fora)
  assert.equal(murta?.tipo, 'esclarecer')
  assert.ok(murta && murta.tipo === 'esclarecer' && murta.sugestoes.length >= 2)
})

test('"aproximar a régua" usa o contexto; em Itajaí, sem régua escolhida, pergunta qual das onze', () => {
  assert.deepEqual(passos('aproxime a régua', emTimbo), [{ tipo: 'aproximar_regua' }])
  const r = interpretar('aproxime a régua', cat, emItajai)
  assert.equal(r?.tipo, 'esclarecer')
  assert.ok(r && r.tipo === 'esclarecer' && r.sugestoes.length === 11)
  assert.deepEqual(passos('aproxime a régua', { ...emItajai, reguaAtual: 'DC-03' }), [{ tipo: 'aproximar_regua' }])
})

test('cidade citada vence o contexto, e a régua antiga não fica no contexto', () => {
  const r = interpretar('mostre Itajaí e aproxime a régua', cat, { cidadeAtual: 'itajai', naMonitor: true, reguaAtual: 'DC-03' })
  assert.equal(r?.tipo, 'esclarecer') // ao trocar (ou reabrir) a cidade, a régua anterior não vale
})

test('pedido encadeado: resolve tudo antes, na ordem', () => {
  assert.deepEqual(passos('Mostre Timbó, aproxime a régua e ative satélite'), [
    { tipo: 'ir_cidade', cidadeId: 'timbo' },
    { tipo: 'aproximar_regua' },
    { tipo: 'fundo', fundo: 'satelite' },
  ])
})

test('trecho não entendido num pedido: nada é executado', () => {
  const r = interpretar('mostre Timbó e faça um café', cat, fora)
  assert.equal(r?.tipo, 'esclarecer')
  assert.match(r && r.tipo === 'esclarecer' ? r.texto : '', /Nada foi feito/)
})

test('zoom, bacia, fundo, camadas, tempo e voltar', () => {
  assert.deepEqual(passos('aproximar'), [{ tipo: 'zoom', sentido: 'mais' }])
  assert.deepEqual(passos('afastar'), [{ tipo: 'zoom', sentido: 'menos' }])
  assert.deepEqual(passos('ver a bacia toda'), [{ tipo: 'ver_bacia' }])
  assert.deepEqual(passos('ver tudo'), [{ tipo: 'ver_bacia' }])
  assert.deepEqual(passos('satélite'), [{ tipo: 'fundo', fundo: 'satelite' }])
  assert.deepEqual(passos('mudar para o mapa de ruas'), [{ tipo: 'fundo', fundo: 'mapa' }])
  assert.deepEqual(passos('fundo escuro'), [{ tipo: 'fundo', fundo: 'escuro' }])
  assert.deepEqual(passos('ligar as manchas'), [{ tipo: 'camada', acao: 'ligar' }])
  assert.deepEqual(passos('mancha de 2008'), [{ tipo: 'camada', acao: 'ligar', ano: '2008' }])
  assert.deepEqual(passos('desligar as camadas'), [{ tipo: 'camada', acao: 'desligar' }])
  assert.deepEqual(passos('ir para a leitura mais recente'), [{ tipo: 'ao_vivo' }])
  assert.deepEqual(passos('voltar ao mapa de antes'), [{ tipo: 'voltar' }])
})

test('páginas e leituras do estado', () => {
  assert.deepEqual(passos('abrir o histórico de Gaspar'), [{ tipo: 'abrir_pagina', cidadeId: 'gaspar', aba: 'historico' }])
  assert.deepEqual(passos('minha rua em Brusque'), [{ tipo: 'abrir_pagina', cidadeId: 'brusque', aba: 'rua' }])
  assert.deepEqual(passos('abrir o mapa das manchas'), [{ tipo: 'abrir_rota', rota: '/itajai?secao=manchas', descricao: 'o mapa das manchas de Itajaí' }])
  assert.deepEqual(passos('abrir o monitor'), [{ tipo: 'monitor_bacia' }])
  assert.deepEqual(passos('o que estou vendo?'), [{ tipo: 'o_que_vejo' }])
  assert.deepEqual(passos('Essa informação é atual ou histórica?'), [{ tipo: 'atual_ou_historico' }])
  assert.deepEqual(passos('por que essa régua está cinza?'), [{ tipo: 'por_que_cinza' }])
  assert.deepEqual(passos('por que Lontras está cinza?'), [{ tipo: 'por_que_cinza', cidadeId: 'lontras' }])
  assert.deepEqual(passos('essa coordenada foi confirmada?'), [{ tipo: 'coordenada' }])
  assert.deepEqual(passos('a coordenada de Timbó foi confirmada?'), [{ tipo: 'coordenada', cidadeId: 'timbo' }])
  assert.deepEqual(passos('o que posso pedir?'), [{ tipo: 'ajuda' }])
})
