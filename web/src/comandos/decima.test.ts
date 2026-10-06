/**
 * 10ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): a conversa que continua — "e Gaspar?",
 * "e em 2011?", "de novo" refazem o último pedido com uma troca só; sem como trocar, o chat pergunta.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { continuar } from './continuar'
import type { Contexto } from './tipos'

const ler = (c: string) => JSON.parse(readFileSync(new URL(`../../../data/${c}`, import.meta.url), 'utf8'))
const cat = catalogoDoCadastro(ler('estacoes.json'))
const nomes = cat.cidades
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }

test('"e Gaspar?": o último pedido com a cidade trocada, na frase como foi escrita', () => {
  assert.deepEqual(continuar('e Gaspar?', 'como está Blumenau?', nomes), { texto: 'como está Gaspar?', troca: 'cidade' })
  assert.deepEqual(continuar('e em Rio do Sul', 'quanto falta para a cota em Blumenau?', nomes), { texto: 'quanto falta para a cota em Rio do Sul?', troca: 'cidade' })
  assert.deepEqual(continuar('e Brusque', 'mostrar Blumenau', nomes), { texto: 'mostrar Brusque', troca: 'cidade' })
  assert.deepEqual(continuar('e lá em Ilhota?', 'maior cheia de Rio do Sul', nomes), { texto: 'maior cheia de Ilhota', troca: 'cidade' })
  // O nome do rio não é a cidade de Itajaí.
  assert.deepEqual(continuar('e Brusque?', 'a cheia do Itajaí-Mirim em Gaspar', nomes), { texto: 'a cheia do Itajaí-Mirim em Brusque', troca: 'cidade' })
  // A mesma cidade: é repetir.
  assert.deepEqual(continuar('e Blumenau?', 'como está Blumenau?', nomes), { texto: 'como está Blumenau?', troca: 'repetir' })
})

test('"e em 2011?" troca o ano; "de novo" repete', () => {
  assert.deepEqual(continuar('e em 2011?', 'cheias de 2008 em Blumenau', nomes), { texto: 'cheias de 2011 em Blumenau', troca: 'ano' })
  assert.deepEqual(continuar('de novo', 'atualizar as leituras', nomes), { texto: 'atualizar as leituras', troca: 'repetir' })
})

test('sem como trocar, pergunta em vez de adivinhar', () => {
  const sem = continuar('e Gaspar?', null, nomes)
  assert.ok(sem && 'erro' in sem)
  assert.match(sem.erro, /Não há pedido anterior[^]*O que você quer saber de Gaspar\?/)
  assert.deepEqual(sem.sugestoes, ['como está Gaspar?', 'mostrar Gaspar'])
  const duas = continuar('e Gaspar?', 'quanto tempo de Rio do Sul até Blumenau?', nomes)
  assert.ok(duas && 'erro' in duas)
  assert.match(duas.erro, /cita Rio do Sul e Blumenau: qual trocar por Gaspar\?/)
  const semCidade = continuar('e Gaspar?', 'onde está chovendo mais?', nomes)
  assert.ok(semCidade && 'erro' in semCidade && /não cita cidade/.test(semCidade.erro))
  const semAno = continuar('e em 2011?', 'como está Blumenau?', nomes)
  assert.ok(semAno && 'erro' in semAno && /não cita ano/.test(semAno.erro))
})

test('não é continuação: frase comum, cidade desconhecida, pergunta inteira', () => {
  for (const q of ['e agora?', 'e se chover?', 'e Pomerode?', 'como está Gaspar?', 'Gaspar', 'e depois mostrar Gaspar']) {
    assert.equal(continuar(q, 'como está Blumenau?', nomes), null, q)
  }
})

test('o pedido refeito é entendido como comando ou pergunta, igual ao digitado', () => {
  const c = continuar('e Gaspar', 'mostrar Blumenau', nomes)
  assert.ok(c && 'texto' in c)
  assert.deepEqual(interpretar(c.texto, cat, fora), { tipo: 'comandos', passos: [{ tipo: 'ir_cidade', cidadeId: 'gaspar' }] })
})
