import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { distanciaKm, maisProximos } from './abrigos'
import type { Abrigo, AbrigosItajai } from '../dados/tipos'

const dados: AbrigosItajai = JSON.parse(
  readFileSync(new URL('../../../data/abrigos-itajai.json', import.meta.url), 'utf8'),
)

function abrigo(over: Partial<Abrigo>): Abrigo {
  return { nome: 'X', endereco: 'Rua Y', zona_defesa_civil: 'Z1', capacidade: 10, lat: 0, lon: 0, ...over }
}

test('distância em km bate com um valor conhecido', () => {
  // Centro de Itajaí ~ foz: ~1,5 km. Aqui um caso simples: 1 grau de latitude ≈ 111 km.
  assert.ok(Math.abs(distanciaKm([-26, -48], [-27, -48]) - 111.2) < 0.5)
  assert.equal(distanciaKm([-26.9, -48.6], [-26.9, -48.6]), 0)
})

test('ordena do mais perto ao mais longe', () => {
  const base: Abrigo[] = [
    abrigo({ nome: 'longe', lat: -26.95, lon: -48.7 }),
    abrigo({ nome: 'perto', lat: -26.9005, lon: -48.6005 }),
    abrigo({ nome: 'médio', lat: -26.92, lon: -48.62 }),
  ]
  const r = maisProximos(base, -26.9, -48.6, 3)
  assert.deepEqual(r.map((x) => x.abrigo.nome), ['perto', 'médio', 'longe'])
  assert.ok(r[0]!.distanciaKm < r[1]!.distanciaKm)
})

test('abrigo sem nome não entra na sugestão (não dá para indicar um ponto sem nome)', () => {
  const base: Abrigo[] = [
    abrigo({ nome: null, lat: -26.9, lon: -48.6 }), // colado no ponto, mas sem nome
    abrigo({ nome: 'com nome', lat: -26.95, lon: -48.7 }),
  ]
  const r = maisProximos(base, -26.9, -48.6, 3)
  assert.deepEqual(r.map((x) => x.abrigo.nome), ['com nome'])
})

test('limita à quantidade pedida', () => {
  const base = Array.from({ length: 10 }, (_, i) => abrigo({ nome: `a${i}`, lat: -26.9 - i * 0.01, lon: -48.6 }))
  assert.equal(maisProximos(base, -26.9, -48.6, 3).length, 3)
})

test('os dados reais têm 45 abrigos e o aviso de exibição', () => {
  assert.equal(dados.abrigos.length, 45)
  assert.match(dados._meta.AVISO_EXIBICAO, /Defesa Civil/)
  // O par situacao/lotacao NÃO pode ter entrado no arquivo.
  for (const a of dados.abrigos) {
    assert.ok(!('situacao' in a), 'situacao não pode existir no arquivo')
    assert.ok(!('lotacao' in a), 'lotacao não pode existir no arquivo')
  }
})

test('todo abrigo tem coordenada finita', () => {
  for (const a of dados.abrigos) {
    assert.ok(Number.isFinite(a.lat) && Number.isFinite(a.lon), `${a.nome}: coordenada inválida`)
  }
})
