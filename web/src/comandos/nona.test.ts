/**
 * 9ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): nome de cidade com erro de digitação vira
 * "Você quis dizer…?", nos comandos e nas perguntas. O palpite nunca é executado sozinho.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { corrigirCidade, distanciaDeEdicao, textoDaCorrecao } from './corrigir'
import type { Contexto } from './tipos'

const ler = (c: string) => JSON.parse(readFileSync(new URL(`../../../data/${c}`, import.meta.url), 'utf8'))
const cat = catalogoDoCadastro(ler('estacoes.json'))
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const nomes = cat.cidades

test('distância de edição, com corte', () => {
  assert.equal(distanciaDeEdicao('blumenal', 'blumenau'), 1)
  assert.equal(distanciaDeEdicao('brusqe', 'brusque'), 1)
  assert.equal(distanciaDeEdicao('rio do sol', 'rio do sul'), 1)
  assert.equal(distanciaDeEdicao('abc', 'abc'), 0)
  assert.equal(distanciaDeEdicao('blumenau', 'gaspar', 2), 3, 'acima do corte devolve corte + 1')
})

test('corrige o nome parecido, um só, na posição de cidade; troca na frase como foi escrita', () => {
  assert.deepEqual(corrigirCidade('mostrar Blumenal', nomes), { de: 'Blumenal', para: 'Blumenau', cidadeId: 'blumenau', texto: 'mostrar Blumenau' })
  assert.equal(corrigirCidade('como está blumenal?', nomes)?.texto, 'como está Blumenau?')
  assert.equal(corrigirCidade('como esta rio do sol', nomes)?.texto, 'como esta Rio do Sul')
  assert.equal(corrigirCidade('cheias de rio-do-sol', nomes)?.texto, 'cheias de Rio do Sul')
  assert.equal(corrigirCidade('zoom em itajay', nomes)?.para, 'Itajaí')
  assert.equal(corrigirCidade('Brusqe', nomes)?.para, 'Brusque', 'a frase inteira é o nome')
})

test('não palpita: nome exato, nome curto, palavra comum, fora da posição de cidade, longe demais, dois nomes', () => {
  for (const q of ['mostrar Blumenau', 'como está Taió?', 'mostrar Taia', 'levei um tombo', 'sem gastar o limite', 'mostrar Gaspra', 'que dia é hoje', 'o rio vai subir?']) {
    assert.equal(corrigirCidade(q, nomes), null, q)
  }
  // Município que o motor conhece (Atlas) não é erro de digitação de cidade nenhuma.
  assert.equal(corrigirCidade('como está Pomerode?', [...nomes, { id: 'pomerode', nome: 'Pomerode' }]), null)
  // Perto de dois nomes: nenhum palpite.
  assert.equal(corrigirCidade('em aaaaad', [{ id: 'a', nome: 'Aaaaab' }, { id: 'b', nome: 'Aaaaac' }]), null)
})

test('comando com erro de digitação: pergunta "Você quis dizer…?" e não faz nada', () => {
  const r = interpretar('mostrar Blumenal', cat, fora)
  assert.ok(r && r.tipo === 'esclarecer', JSON.stringify(r))
  assert.match(r.texto, /^Não achei a cidade "Blumenal"\. Você quis dizer Blumenau\? Nada foi feito/)
  assert.deepEqual(r.sugestoes, ['mostrar Blumenau'])
  // A sugestão, tocada, é o comando certo.
  assert.deepEqual(interpretar('mostrar Blumenau', cat, fora), { tipo: 'comandos', passos: [{ tipo: 'ir_cidade', cidadeId: 'blumenau' }] })
  const encadeado = interpretar('mostrar Blumenal e satélite', cat, fora)
  assert.ok(encadeado && encadeado.tipo === 'esclarecer')
  assert.deepEqual(encadeado.sugestoes, ['mostrar Blumenau e satélite'])
  const falta = interpretar('quanto falta para a cota em Rio do Sol?', cat, fora)
  assert.ok(falta && falta.tipo === 'esclarecer')
  assert.deepEqual(falta.sugestoes, ['quanto falta para a cota em Rio do Sul?'])
})

test('pergunta com erro de digitação continua indo ao motor; o "Você quis dizer" é do chat da pergunta', () => {
  // "Como está X?" é pergunta (motor), não comando: o interpretador não a engole.
  assert.equal(interpretar('como está blumenal?', cat, fora), null)
  const c = corrigirCidade('como está blumenal?', nomes)!
  assert.match(textoDaCorrecao(c, 'pergunta'), /^Não achei a cidade "blumenal"\. Você quis dizer Blumenau\? Toque na sugestão/)
})
