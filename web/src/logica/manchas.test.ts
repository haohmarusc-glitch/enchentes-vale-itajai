import { test } from 'node:test'
import assert from 'node:assert/strict'
import { corDaLamina, legenda, ordenar, rotuloEvento } from './manchas'
import type { Mancha } from './manchas'

function m(over: Partial<Mancha>): Mancha {
  return {
    cidade: 'itajai', evento: '2015-10', tipo: "lâmina d'água",
    arquivo: 'manchas/itajai/inundaoutubro2015.geojson', tem_lamina: true,
    pico_registrado: null, licenca: 'MIT', fonte: 'geoitajai/sie',
    feicoes: 155, crs: 'urn:ogc:def:crs:OGC:1.3:CRS84',
    classes_lamina: [], classes_sobrepostas: false, ...over,
  }
}

test('rótulo do evento em português', () => {
  assert.equal(rotuloEvento('2015-10'), 'out/2015')
  assert.equal(rotuloEvento('2013-07'), 'jul/2013')
  assert.equal(rotuloEvento('2001'), '2001')
})

test('mais recente primeiro, e a lâmina antes da mancha total', () => {
  // Do mesmo evento, o arquivo com lâmina diz quanto de água, não só onde.
  const lista = ordenar([
    m({ evento: '1983-07', tem_lamina: false }),
    m({ evento: '2011-09', tem_lamina: false, arquivo: 'a' }),
    m({ evento: '2011-09', tem_lamina: true, arquivo: 'b' }),
  ])
  assert.deepEqual(
    lista.map((x) => [x.evento, x.tem_lamina]),
    [['2011-09', true], ['2011-09', false], ['1983-07', false]],
  )
})

test('cor mais escura conforme a água fica mais funda', () => {
  const rasa = corDaLamina({ rotulo: '0,20', lamina_min_m: null, lamina_max_m: 0.2 })
  const media = corDaLamina({ rotulo: '0,41 a 0,60', lamina_min_m: 0.41, lamina_max_m: 0.6 })
  const funda = corDaLamina({ rotulo: '2,01 a 3', lamina_min_m: 2.01, lamina_max_m: 3 })
  assert.notEqual(rasa, media)
  assert.notEqual(media, funda)
})

test('classe sem número não vira "raso"', () => {
  // Cinza significa "a fonte não disse". Pintar de azul claro diria que é raso.
  const cinza = corDaLamina({ rotulo: '?', lamina_min_m: null, lamina_max_m: null })
  const rasa = corDaLamina({ rotulo: '0,20', lamina_min_m: null, lamina_max_m: 0.2 })
  assert.notEqual(cinza, rasa)
})

test('legenda vai do raso para o fundo, com o desconhecido no fim', () => {
  const l = legenda(m({ classes_lamina: [
    { rotulo: '0,41 a 0,60', lamina_min_m: 0.41, lamina_max_m: 0.6 },
    { rotulo: '?', lamina_min_m: null, lamina_max_m: null },
    { rotulo: '0,20', lamina_min_m: null, lamina_max_m: 0.2 },
  ] }))
  assert.deepEqual(l.map((c) => c.rotulo), ['0,20', '0,41 a 0,60', '?'])
})
