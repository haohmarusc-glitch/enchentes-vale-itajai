import test from 'node:test'
import assert from 'node:assert/strict'
import { instanteLocal, simularChegada } from './simulacaoChegada'
import tabuaReal from '../../../data/mare-itajai.json'
import historico from '../../../data/historico-chegada-itajai.json'

const tabua = {
  preamares: [{ quando: '2026-09-20T01:30', altura_m: 1.2 }, { quando: '2026-09-20T13:30', altura_m: 1.1 }],
  baixamares: [{ quando: '2026-09-19T19:30', altura_m: .2 }, { quando: '2026-09-20T07:30', altura_m: .1 }],
}
test('pico às 10h + 14–17h muda o dia e encontra a preamar', () => {
  const r = simularChegada('2026-09-19T10:00', 14, 17, tabua)
  assert.ok(!('erro' in r))
  assert.equal(r.inicio.toISOString(), '2026-09-20T03:00:00.000Z')
  assert.equal(r.fim.toISOString(), '2026-09-20T06:00:00.000Z')
  assert.equal(r.cobertura, true)
  assert.equal(r.preamaresDentro, 1)
  assert.deepEqual(r.extremos.map((e) => e.altura), [.2, 1.2, .1])
})
test('não aplica margem de duas horas para chamar um pico externo de coincidente', () => {
  const r = simularChegada('2026-09-19T10:00', 12, 15, tabua)
  assert.ok(!('erro' in r))
  assert.equal(r.cobertura, true)
  assert.equal(r.preamaresDentro, 0)
})
test('preamar exatamente no limite faz parte da janela', () => {
  for (const [min, max] of [[15.5, 17], [14, 15.5]]) {
    const r = simularChegada('2026-09-19T10:00', min!, max!, tabua)
    assert.ok(!('erro' in r))
    assert.equal(r.preamaresDentro, 1)
  }
})
test('fora do ano da tábua ou com lacuna, não conclui ausência de coincidência', () => {
  for (const t of [tabuaReal, { preamares: [], baixamares: [] }]) {
    const r = simularChegada('2027-01-02T10:00', 14, 17, t)
    assert.ok(!('erro' in r))
    assert.equal(r.cobertura, false)
  }
  const r = simularChegada('2026-09-19T10:00', 14, 17, {
    preamares: [{ quando: '2026-09-21T01:00', altura_m: 1 }],
    baixamares: tabua.baixamares.slice(0, 1),
  })
  assert.ok(!('erro' in r))
  assert.equal(r.cobertura, false)
})
test('extremos repetidos, faltantes ou da mesma fase não comprovam cobertura', () => {
  const r = simularChegada('2026-09-19T10:00', 14, 17, {
    preamares: [{ quando: '2026-09-19T23:00' }, { quando: '2026-09-20T04:00' }], baixamares: [],
  })
  assert.ok(!('erro' in r))
  assert.equal(r.cobertura, false)
})
test('datas impossíveis e intervalos inválidos são recusados', () => {
  for (const s of ['', '2026-02-30T10:00', '2026-09-19T25:00', '2026-09-19']) assert.equal(instanteLocal(s), null)
  for (const [min, max] of [[0, 17], [17, 14], [19, 19], [14, 73], [NaN, 17], [14, Infinity]]) {
    assert.ok('erro' in simularChegada('2026-09-19T10:00', min!, max!, tabua))
  }
})
test('Brasília histórica respeita horário de verão e não depende do fuso do navegador', () => {
  assert.equal(instanteLocal('2011-09-09T07:00')?.toISOString(), '2011-09-09T10:00:00.000Z')
  assert.equal(instanteLocal('2011-12-01T07:00')?.toISOString(), '2011-12-01T09:00:00.000Z')
  assert.equal(instanteLocal('2018-11-04T00:30'), null)
})
test('altura ausente não vira zero e preamar negativa permanece valor da fonte', () => {
  const r = simularChegada('2026-09-19T10:00', 14, 17, {
    ...tabua, preamares: [{ quando: '2026-09-20T01:30', altura_m: -.1 }],
    baixamares: [{ quando: '2026-09-19T19:30' }, { quando: '2026-09-20T07:30', altura_m: NaN }],
  })
  assert.ok(!('erro' in r))
  assert.deepEqual(r.extremos.map((e) => e.altura), [null, -.1, null])
})
test('caso de 2011 não se transforma em média nem altera a referência JICA', () => {
  assert.equal(historico.estado, 'calibracao_pendente')
  assert.equal(historico.eventos[0]!.status, 'pendente')
  assert.equal(historico.eventos[0]!.pico_jusante, null)
  assert.deepEqual([historico.referencia_estudo.horas_min, historico.referencia_estudo.horas_max], [14, 17])
})
