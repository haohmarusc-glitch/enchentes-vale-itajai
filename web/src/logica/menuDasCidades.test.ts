import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { menuDasCidades, type RioParaMenu } from './menuDasCidades'

const real = JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf-8'))
const rios: RioParaMenu[] = Object.entries(real.rios).map(([id, r]) => {
  const rio = r as { nome: string; cidades: RioParaMenu['cidades']; _topologia?: RioParaMenu['_topologia'] }
  return { id, nome: rio.nome, cidades: rio.cidades, _topologia: rio._topologia }
})
const acu = () => menuDasCidades(rios).find((r) => r.id === 'itajai-acu')!
const mirim = () => menuDasCidades(rios).find((r) => r.id === 'itajai-mirim')!
const ids = (g: { itens: { id: string }[] } | undefined) => (g ? g.itens.map((i) => i.id) : [])

test('o Açu NÃO vira fila: as cabeceiras ficam fora do tronco, sem ordem entre si', () => {
  const cab = acu().grupos.find((g) => g.titulo === 'Cabeceiras')!
  const tronco = acu().grupos.find((g) => g.titulo === 'Tronco')!
  assert.deepEqual(new Set(ids(cab)), new Set(['taio', 'ituporanga']))
  assert.equal(cab.ordenado, false, 'Taió e Ituporanga correm em paralelo')
  assert.ok(!ids(tronco).includes('taio') && !ids(tronco).includes('ituporanga'))
})

test('o tronco sai exatamente na sequência do cadastro, montante → jusante', () => {
  const tronco = acu().grupos.find((g) => g.titulo === 'Tronco')!
  assert.deepEqual(ids(tronco), real.rios['itajai-acu']._topologia.tronco_sequencia)
  assert.equal(tronco.ordenado, true)
  assert.equal(ids(tronco)[0], 'rio-do-sul')
  assert.equal(ids(tronco).at(-1), 'itajai')
})

test('afluentes entram de lado e dizem onde entram', () => {
  const afl = acu().grupos.find((g) => g.titulo === 'Afluentes')!
  assert.deepEqual(new Set(ids(afl)), new Set(['ibirama', 'timbo', 'rio-dos-cedros']))
  assert.equal(afl.ordenado, false)
  const ibirama = afl.itens.find((i) => i.id === 'ibirama')!
  assert.match(ibirama.detalhe ?? '', /Rio do Sul/)
})

test('Trombudo Central, sem posição na árvore, vai para "Outros pontos" — não para o tronco', () => {
  const outros = acu().grupos.find((g) => g.titulo === 'Outros pontos')!
  assert.ok(ids(outros).includes('trombudo-central'))
})

test('toda cidade do Açu aparece uma vez, e só uma', () => {
  const todos = acu().grupos.flatMap(ids)
  assert.equal(new Set(todos).size, todos.length)
  assert.deepEqual(new Set(todos), new Set(real.rios['itajai-acu'].cidades.map((c: { id: string }) => c.id)))
})

test('o Mirim, que é fila, sai na ordem do cadastro', () => {
  const [fila] = mirim().grupos
  assert.equal(fila?.titulo, 'Montante → jusante')
  assert.deepEqual(ids(fila), ['vidal-ramos', 'botuvera', 'guabiruba', 'brusque', 'itajai'])
})

test('numa fila, cidade sem `ordem` não ganha posição inventada', () => {
  const menu = menuDasCidades([
    { id: 'x', nome: 'X', cidades: [
      { id: 'b', nome: 'B', ordem: 2 }, { id: 'a', nome: 'A', ordem: 1 }, { id: 'z', nome: 'Z', ordem: null },
    ] },
  ])
  const [fila, outros] = menu[0]!.grupos
  assert.deepEqual(ids(fila), ['a', 'b'])
  assert.deepEqual(ids(outros), ['z'])
})

test('sobrevive a topologia que cita cidade fora do cadastro', () => {
  const menu = menuDasCidades([
    { id: 'x', nome: 'X', cidades: [{ id: 'a', nome: 'A' }],
      _topologia: { tronco_sequencia: ['a', 'fantasma'], cabeceiras_paralelas: ['outro-fantasma'] } },
  ])
  assert.deepEqual(menu[0]!.grupos.map((g) => [g.titulo, ids(g)]), [['Tronco', ['a']]])
})
