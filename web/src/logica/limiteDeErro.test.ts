/**
 * O limite de erro existe para uma coisa só: um componente quebrado não pode
 * apagar o telefone da Defesa Civil.
 *
 * Sem limite, o React desmonta a árvore inteira quando qualquer componente
 * lança — e a árvore inteira inclui a `FaixaEmergencia`, cujo próprio
 * comentário diz *"se alguém abrir o site em pânico e ler uma coisa só, que
 * seja esta"*. Um gráfico com dado inesperado apagava o 199.
 *
 * Estes testes leem a estrutura do `App.tsx`, sem montar React: o que precisa
 * ser garantido é ONDE o limite está, e isso está no código.
 */
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const APP = readFileSync(new URL('../App.tsx', import.meta.url), 'utf8')
const LIMITE = readFileSync(new URL('../componentes/LimiteDeErro.tsx', import.meta.url), 'utf8')

test('a FaixaEmergencia fica FORA do limite de erro', () => {
  // Se ela estivesse dentro, um erro no conteúdo a levaria junto — que é
  // exatamente o problema que o limite existe para resolver.
  const faixa = APP.indexOf('<FaixaEmergencia />')
  const abre = APP.indexOf('<LimiteDeErro')
  assert.ok(faixa >= 0 && abre >= 0)
  assert.ok(faixa < abre, 'a FaixaEmergencia tem de vir ANTES do limite, nunca dentro dele')
})

test('as rotas ficam DENTRO do limite', () => {
  const abre = APP.indexOf('<LimiteDeErro')
  const rotas = APP.indexOf('<Routes>')
  const fecha = APP.indexOf('</LimiteDeErro>')
  assert.ok(abre < rotas && rotas < fecha, 'toda tela tem de estar protegida')
})

test('a tela de erro manda para a fonte oficial, não só pede desculpa', () => {
  assert.match(LIMITE, /alertablu/i)
  assert.match(LIMITE, /defesacivil/i)
  assert.match(LIMITE, /199/)
})

test('a tela de erro é anunciada por leitor de tela', () => {
  assert.match(LIMITE, /role="alert"/)
})

test('dá para tentar de novo sem recarregar a página', () => {
  // Erro transitório (um fetch que falhou, um dado que chegou pela metade) não
  // deve exigir que a pessoa saiba recarregar o navegador no meio da chuva.
  assert.match(LIMITE, /setState\(\{ erro: null \}\)/)
})

test('o skip link é o primeiro elemento focável, antes do cabeçalho', () => {
  const pular = APP.indexOf('pularParaConteudo')
  const cabecalho = APP.indexOf('<header')
  assert.ok(pular >= 0 && pular < cabecalho)
})

test('o alvo do skip link existe e recebe foco', () => {
  assert.match(APP, /id="conteudo"/)
  assert.match(APP, /tabIndex=\{-1\}/)
})
