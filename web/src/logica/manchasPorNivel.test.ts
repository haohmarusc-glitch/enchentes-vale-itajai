/**
 * A mancha só se liga ao nível quando existe pico NA MESMA RÉGUA. Estes testes
 * travam as duas metades: que hoje NÃO acende (os dados de Itajaí não têm pico)
 * e que acende sozinho quando o pico entrar.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import {
  fraseFalta,
  frasePassado,
  manchasPorNivel,
  type ManchaComparavel,
} from './manchasPorNivel'

const REGUA = 'DC-11 Santa Regina'
const m2011: ManchaComparavel = { evento: '2011-09', arquivo: 'a.geojson', picoM: 3.05, reguaDoPico: REGUA }
const m2008: ManchaComparavel = { evento: '2008-11', arquivo: 'b.geojson', picoM: 3.9, reguaDoPico: REGUA }
const m1983: ManchaComparavel = { evento: '1983-07', arquivo: 'c.geojson', picoM: 4.8, reguaDoPico: REGUA }
const base: ManchaComparavel[] = [m2011, m2008, m1983]

test('separa o que o rio já passou do que ainda não, pelo nível de agora', () => {
  const r = manchasPorNivel(base, 3.2, REGUA)
  assert.deepEqual(r.jaPassou.map((m) => m.evento), ['2011-09'])
  assert.equal(r.proximo?.evento, '2008-11')
  assert.equal(r.semPico.length, 0)
})

test('o mais alto já alcançado vem primeiro, e o próximo é o mais PERTO acima', () => {
  const r = manchasPorNivel(base, 4.0, REGUA)
  assert.deepEqual(r.jaPassou.map((m) => m.evento), ['2008-11', '2011-09'])
  assert.equal(r.proximo?.evento, '1983-07')
})

test('pico sem régua declarada NÃO é usado — não se sabe de onde veio', () => {
  const r = manchasPorNivel([{ ...m2011, reguaDoPico: null }], 9, REGUA)
  assert.equal(r.jaPassou.length, 0)
  assert.equal(r.semPico.length, 1)
})

test('régua diferente não se compara, mesmo com o número acima do pico', () => {
  // A regra nº 1 do projeto: zeros diferentes, metros que não se comparam.
  const r = manchasPorNivel(base, 9, 'DC-01 CEPSUL')
  assert.equal(r.jaPassou.length, 0)
  assert.equal(r.semPico.length, 3)
})

test('sem leitura não é "abaixo de tudo": nada entra na conta', () => {
  for (const n of [null, undefined, Number.NaN, Number.POSITIVE_INFINITY]) {
    const r = manchasPorNivel(base, n as number | null, REGUA)
    assert.equal(r.jaPassou.length, 0, String(n))
    assert.equal(r.proximo, null, String(n))
    assert.equal(r.semPico.length, 3, String(n))
  }
})

test('pico exatamente igual ao nível conta como alcançado', () => {
  const r = manchasPorNivel([m2011], 3.05, REGUA)
  assert.equal(r.jaPassou.length, 1)
  assert.equal(r.jaPassou[0]?.diferencaM, 0)
})

test('as frases falam no passado e mostram os dois números', () => {
  const r = manchasPorNivel(base, 3.2, REGUA)
  assert.equal(
    frasePassado(r.jaPassou[0]!, '2011-09'),
    'Em 2011-09 o rio marcou 3,05 m nesta régua e a água cobriu esta área.',
  )
  assert.ok(fraseFalta(r.proximo!, '2008-11').startsWith('Faltam 0,70 m'))
})

test('⛔ HOJE não acende: as manchas de Itajaí não têm pico registrado', () => {
  // Não é opinião: é o cadastro. Se um dia entrar pico de Itajaí, este teste
  // cai — e cair é a NOTÍCIA BOA: quer dizer que o recurso pode acender.
  const indice = JSON.parse(
    readFileSync(new URL('../../../data/manchas/index.json', import.meta.url), 'utf8'),
  ) as { manchas: { cidade: string; pico_registrado: unknown }[] }
  const itajai = indice.manchas.filter((m) => m.cidade === 'itajai')
  assert.ok(itajai.length >= 10, 'as manchas de Itajaí existem')
  assert.ok(
    itajai.every((m) => m.pico_registrado === null),
    'nenhuma tem pico — a ligação com o nível está bloqueada por DADO, não por código',
  )

  const enchentes = JSON.parse(
    readFileSync(new URL('../../../data/enchentes.json', import.meta.url), 'utf8'),
  ) as { eventos: { cidade: string }[] }
  assert.equal(
    enchentes.eventos.filter((e) => e.cidade === 'itajai').length,
    0,
    'a causa: Itajaí não tem nenhum pico histórico no cadastro',
  )
})
