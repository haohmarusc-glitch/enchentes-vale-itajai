import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  CHAVE_AVISO,
  CHAVE_CIDADES,
  MAX_CIDADES,
  avisoLido,
  cidadesSeguidas,
  deixarDeSeguir,
  gravarLetra,
  letra,
  marcarAvisoLido,
  tornarMinha,
  type Armazem,
} from './preferencias'

function memoria(inicial: Record<string, string> = {}): Armazem & { dados: Record<string, string> } {
  const dados = { ...inicial }
  return {
    dados,
    getItem: (k) => (k in dados ? dados[k]! : null),
    setItem: (k, v) => {
      dados[k] = v
    },
    removeItem: (k) => {
      delete dados[k]
    },
  }
}

/** Armazenamento bloqueado: janela anônima, cota cheia, política do navegador. */
const quebrado: Armazem = {
  getItem: () => {
    throw new Error('SecurityError')
  },
  setItem: () => {
    throw new Error('QuotaExceededError')
  },
  removeItem: () => {
    throw new Error('SecurityError')
  },
}

test('tornarMinha põe a cidade em primeiro, sem duplicar', () => {
  const a = memoria()
  tornarMinha({ id: 'gaspar', rio: 'acu' }, a)
  tornarMinha({ id: 'blumenau', rio: 'acu' }, a)
  const lista = tornarMinha({ id: 'gaspar', rio: 'acu' }, a)
  assert.deepEqual(lista.map((c) => c.id), ['gaspar', 'blumenau'])
  assert.deepEqual(cidadesSeguidas(a).map((c) => c.id), ['gaspar', 'blumenau'])
})

test('a lista para no máximo de cidades', () => {
  const a = memoria()
  for (const id of ['a', 'b', 'c', 'd', 'e', 'f']) tornarMinha({ id, rio: 'acu' }, a)
  assert.equal(cidadesSeguidas(a).length, MAX_CIDADES)
  assert.equal(cidadesSeguidas(a)[0]!.id, 'f')
})

test('deixarDeSeguir apaga a chave quando a lista esvazia', () => {
  const a = memoria()
  tornarMinha({ id: 'brusque', rio: 'mirim' }, a)
  deixarDeSeguir('brusque', a)
  assert.equal(CHAVE_CIDADES in a.dados, false)
})

test('conteúdo inválido vira lista vazia, não erro', () => {
  for (const bruto of ['{', '"x"', '[1,2]', '[{"id":"../x","rio":"acu"}]', '[{"id":"x","rio":"nilo"}]']) {
    assert.deepEqual(cidadesSeguidas(memoria({ [CHAVE_CIDADES]: bruto })), [], bruto)
  }
})

test('armazenamento bloqueado: nada lança, e o aviso conta como não lido', () => {
  assert.deepEqual(cidadesSeguidas(quebrado), [])
  assert.deepEqual(tornarMinha({ id: 'gaspar', rio: 'acu' }, quebrado).map((c) => c.id), ['gaspar'])
  assert.equal(avisoLido(quebrado), false)
  assert.equal(marcarAvisoLido(quebrado), false)
  assert.equal(letra(quebrado), 'normal')
  gravarLetra('grande', quebrado)
  assert.equal(avisoLido(null), false)
})

test('aviso lido vale só para a versão atual do texto', () => {
  const a = memoria({ [CHAVE_AVISO]: '2020-01-01' })
  assert.equal(avisoLido(a), false)
  marcarAvisoLido(a)
  assert.equal(avisoLido(a), true)
})

test('letra grande é lembrada e volta ao normal', () => {
  const a = memoria()
  gravarLetra('grande', a)
  assert.equal(letra(a), 'grande')
  gravarLetra('normal', a)
  assert.equal(letra(a), 'normal')
})
