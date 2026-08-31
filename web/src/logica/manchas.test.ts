import { test } from 'node:test'
import assert from 'node:assert/strict'
import { CINZA_SEM_NUMERO, coresPorRotulo, corDaLamina, legenda, ordenar, rotuloEvento } from './manchas'
import indice from '../../../data/manchas/index.json'
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

test('duas faixas do mesmo mapa nunca dividem a mesma cor', () => {
  // O de 2011 é o caso real: "1,01 a 1,50" e "1,51 a 2" caíam na mesma cor,
  // e quem olhava o mapa não tinha como separar um metro e meio de dois metros.
  const mancha = m({
    evento: '2011-09',
    classes_lamina: [
      { rotulo: '0,50', lamina_min_m: null, lamina_max_m: 0.5 },
      { rotulo: '0,51 a 1', lamina_min_m: 0.51, lamina_max_m: 1 },
      { rotulo: '1,01 a 1,50', lamina_min_m: 1.01, lamina_max_m: 1.5 },
      { rotulo: '1,51 a 2', lamina_min_m: 1.51, lamina_max_m: 2 },
      { rotulo: '2,01 a 3', lamina_min_m: 2.01, lamina_max_m: 3 },
    ],
  })
  const cores = coresPorRotulo(mancha.classes_lamina)
  const usadas = [...cores.values()]
  assert.equal(new Set(usadas).size, usadas.length, `cores repetidas: ${usadas.join(' ')}`)
})

test('a cor continua indo do claro ao escuro conforme a água funda', () => {
  const classes = [
    { rotulo: 'a', lamina_min_m: null, lamina_max_m: 0.2 },
    { rotulo: 'b', lamina_min_m: null, lamina_max_m: 1 },
    { rotulo: 'c', lamina_min_m: null, lamina_max_m: 3 },
  ]
  const cores = coresPorRotulo(classes)
  const luz = (cor: string) => parseInt(cor.slice(1, 3), 16) + parseInt(cor.slice(3, 5), 16)
  assert.ok(luz(cores.get('a')!) > luz(cores.get('b')!), 'raso tem de ser mais claro')
  assert.ok(luz(cores.get('b')!) > luz(cores.get('c')!), 'fundo tem de ser mais escuro')
})

test('classe sem número fica cinza mesmo entre outras', () => {
  const cores = coresPorRotulo([
    { rotulo: 'sabe', lamina_min_m: null, lamina_max_m: 0.5 },
    { rotulo: 'nao sabe', lamina_min_m: null, lamina_max_m: null },
  ])
  assert.equal(cores.get('nao sabe'), CINZA_SEM_NUMERO)
  assert.notEqual(cores.get('sabe'), CINZA_SEM_NUMERO)
})

test('nenhuma mancha real do repositório tem cor repetida', () => {
  // Ligado ao arquivo de verdade: dado novo com faixa nova quebra este teste
  // em vez de repetir cor no mapa em silêncio, que foi como o defeito nasceu.
  for (const mancha of (indice as { manchas: Mancha[] }).manchas) {
    const cores = [...coresPorRotulo(mancha.classes_lamina).values()]
    assert.equal(new Set(cores).size, cores.length,
      `${mancha.arquivo}: cores repetidas entre faixas`)
  }
})
