import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import type { Cidade, Estacoes } from './tipos'

/*
 * O contrato da árvore, do lado do site. O validador Python (scripts) trava os
 * dados; aqui travamos o que o site PRECISA deles para não voltar a desenhar a
 * fila falsa do Açu (Taió → Ibirama → Indaial). Lê o JSON do disco, como
 * reguas.test.ts, porque o alias `@dados` só existe no Vite.
 */
const estacoes: Estacoes = JSON.parse(
  readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'),
)

/** A mesma ordenação de `cidadesDoRio`: em rio ramificado (ordem null) mantém a
 *  ordem do arquivo; em rio em fila ordena por `ordem`. */
function ordenar(cidades: Cidade[]): Cidade[] {
  return [...cidades].sort((a, b) =>
    a.ordem == null || b.ordem == null ? 0 : a.ordem - b.ordem,
  )
}

test('o Açu é uma árvore: tem _topologia e o tronco é a única sequência', () => {
  const acu = estacoes.rios['itajai-acu']!
  assert.ok(acu._topologia, 'o Açu precisa de _topologia — sem ela a tela volta a ser fila')
  assert.deepEqual(acu._topologia!.tronco_sequencia, [
    'rio-do-sul', 'ascurra', 'indaial', 'blumenau', 'gaspar', 'ilhota', 'itajai',
  ])
  assert.deepEqual(acu._topologia!.cabeceiras_paralelas, ['taio', 'ituporanga'])
  assert.equal(acu._topologia!.afluentes_laterais[0]!.id, 'ibirama')
})

test('nenhuma cidade do Açu tem ordem global; todas têm ramo', () => {
  for (const c of estacoes.rios['itajai-acu']!.cidades) {
    assert.equal(c.ordem, null, `${c.id}: ordem global em rio ramificado afirma uma fila que não existe`)
    assert.ok(c.ramo, `${c.id}: falta ramo`)
  }
})

test('Ibirama não está no tronco (é afluente do Hercílio); Apiúna saiu do eixo', () => {
  const acu = estacoes.rios['itajai-acu']!
  const ids = acu.cidades.map((c) => c.id)
  assert.ok(!acu._topologia!.tronco_sequencia.includes('ibirama'), 'Ibirama é afluente, não tronco')
  assert.equal(acu.cidades.find((c) => c.id === 'ibirama')!.ramo, 'itajai_do_norte')
  assert.ok(!ids.includes('apiuna'), 'Apiúna (estação de altitude) não é mais cidade do eixo')
  assert.ok(ids.includes('ascurra'), 'Ascurra entrou no tronco')
})

test('a ordenação mantém a ordem do arquivo no Açu (cabeceiras → tronco)', () => {
  // Com ordem null, o sort é estável e não embaralha — a tela desenha os blocos
  // a partir de _topologia, mas a lista precisa chegar íntegra.
  const acu = estacoes.rios['itajai-acu']!.cidades
  const antes = acu.map((c) => c.id)
  assert.deepEqual(ordenar(acu).map((c) => c.id), antes)
})

test('o Mirim segue em fila: ordem 1..N contígua e sem ramo', () => {
  const mirim = estacoes.rios['itajai-mirim']!
  assert.equal(mirim._topologia, undefined, 'o Mirim não é ramificado nas cidades')
  const ordens = mirim.cidades.map((c) => c.ordem)
  assert.deepEqual(
    [...ordens].sort((a, b) => (a as number) - (b as number)),
    Array.from({ length: ordens.length }, (_, i) => i + 1),
  )
  for (const c of mirim.cidades) assert.equal(c.ramo, undefined, `${c.id}: Mirim não usa ramo`)
})
