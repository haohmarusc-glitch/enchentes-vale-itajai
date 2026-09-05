/**
 * A árvore da bacia não pode ensinar o caminho errado da água nem misturar a
 * cota do reservatório com a régua da cidade. Estes testes travam as duas
 * coisas ao cadastro.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { arvoreDaBacia, barragemDaBacia, type RioParaArvore } from './arvoreDaBacia'

const estacoes = JSON.parse(
  readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'),
) as { rios: Record<string, RioParaArvore> }
const hidraulica = JSON.parse(
  readFileSync(new URL('../../../data/hidraulica.json', import.meta.url), 'utf8'),
) as { barragens: Record<string, unknown> }

function rioDoCadastro(id: string): RioParaArvore {
  const r = estacoes.rios[id]
  assert.ok(r, `rio ${id} existe no cadastro`)
  return r
}

const acu = arvoreDaBacia('itajai-acu', rioDoCadastro('itajai-acu'), hidraulica.barragens)
assert.ok(acu, 'o Açu é ramificado e tem árvore')

test('cada cabeceira traz o seu rio e a sua barragem — nenhuma delas é o Açu ainda', () => {
  assert.deepEqual(
    acu.cabeceiras.map((c) => [c.cidade, c.rio, c.barragem?.nome]),
    [
      ['Taió', 'Itajaí do Oeste', 'Barragem Oeste'],
      ['Ituporanga', 'Itajaí do Sul', 'Barragem Sul'],
    ],
  )
})

test('o Açu nasce na confluência, em Rio do Sul, com a coordenada da fonte', () => {
  assert.equal(acu.nasce?.cidade, 'Rio do Sul')
  assert.equal(acu.nasce?.lat, -27.2160314)
  assert.equal(acu.nasce?.lon, -49.6483391)
})

test('a Barragem Norte fica no ramo lateral, com Ibirama abaixo dela — não no tronco', () => {
  const ibirama = acu.laterais.find((l) => l.cidade === 'Ibirama')
  assert.ok(ibirama, 'Ibirama é lateral')
  assert.equal(ibirama.barragem?.nome, 'Barragem Norte')
  assert.equal(ibirama.barragem?.acimaDe, 'Ibirama')
  assert.equal(ibirama.rio, 'Rio Hercílio (Itajaí do Norte)')
  assert.ok(!acu.tronco.includes('Ibirama'))
})

test('as barragens de CONTENÇÃO continuam sendo três, com as locais no arquivo', () => {
  const nomes = [
    ...acu.cabeceiras.map((c) => c.barragem?.nome),
    ...acu.laterais.map((l) => l.barragem?.nome),
  ].filter(Boolean)
  assert.deepEqual(nomes.sort(), ['Barragem Norte', 'Barragem Oeste', 'Barragem Sul'])
  assert.deepEqual(acu.barragensSoltas, [])
})

test('o tronco é a sequência canônica e começa em Rio do Sul', () => {
  assert.deepEqual(acu.tronco, [
    'Rio do Sul', 'Lontras', 'Ascurra', 'Indaial', 'Blumenau', 'Gaspar', 'Ilhota', 'Itajaí',
  ])
})

test('a barragem guarda ano, volume e comportas — e a Norte tem condutos SEM comporta', () => {
  const oeste = acu.cabeceiras[0]?.barragem
  assert.equal(oeste?.ano, 1973)
  assert.equal(oeste?.comportas, 7)
  assert.equal(oeste?.semComporta, null)
  const norte = acu.laterais.find((l) => l.cidade === 'Ibirama')?.barragem
  assert.equal(norte?.comportas, 2)
  assert.equal(norte?.semComporta, 5)
})

test('barragem sem os campos mínimos não vira meia-barragem: vira null', () => {
  assert.equal(barragemDaBacia({ tipo: 'contencao_estadual', nome: 'X' }, (id) => id), null)
  assert.equal(
    barragemDaBacia({ tipo: 'contencao_estadual', nome: 'X', municipio_nome: 'Y', rio: 'Z' }, (id) => id),
    null,
  )
})

test('a barragem LOCAL nunca vira ficha de contenção — nem com todos os campos', () => {
  assert.equal(
    barragemDaBacia(
      { tipo: 'local', nome: 'Pinhal', municipio_nome: 'M', rio: 'R', a_montante_de: 'x' },
      (id) => id,
    ),
    null,
  )
})

test('Pinhal e Rio Bonito entram como LOCAIS, no município delas, e não como as três', () => {
  const cedros = acu.locaisPorCidade.find((g) => g.cidade === 'Rio dos Cedros')
  assert.ok(cedros, 'as locais ficam em Rio dos Cedros')
  assert.deepEqual(cedros.barragens.map((b) => b.nome).sort(), ['Barragem Pinhal', 'Barragem Rio Bonito'])
  assert.deepEqual(
    cedros.barragens.map((b) => b.localidade).sort(),
    ['Alto Cedros', 'Palmeiras'],
  )
  // Nenhuma delas aparece como barragem de cabeceira ou de lateral.
  const contencao = [
    ...acu.cabeceiras.map((c) => c.barragem?.nome),
    ...acu.laterais.map((l) => l.barragem?.nome),
    ...acu.barragensSoltas.map((b) => b.nome),
  ].filter(Boolean)
  assert.ok(!contencao.includes('Barragem Pinhal'))
  assert.ok(!contencao.includes('Barragem Rio Bonito'))
})

test('as locais não têm posição em relação à régua: o tipo não carrega acimaDe', () => {
  const cedros = acu.locaisPorCidade.find((g) => g.cidade === 'Rio dos Cedros')
  for (const b of cedros?.barragens ?? []) {
    assert.ok(!('acimaDe' in b), 'barragem local não afirma o que fica abaixo dela')
  }
})

test('barragem cuja cidade não é cabeceira nem lateral fica SOLTA, não some calada', () => {
  const rio: RioParaArvore = {
    cidades: [{ id: 'a', nome: 'A' }, { id: 'z', nome: 'Z' }],
    _topologia: { tronco_sequencia: ['a'], cabeceiras_paralelas: [], afluentes_laterais: [] },
  }
  const arv = arvoreDaBacia('r', rio, {
    x: { tipo: 'contencao_estadual', nome: 'B1', municipio_nome: 'M', rio: 'R', rio_id: 'r', a_montante_de: 'z' },
  })
  assert.equal(arv?.barragensSoltas.length, 1)
  assert.equal(arv?.barragensSoltas[0]?.acimaDe, 'Z')
})

test('rio em fila (Mirim) não tem árvore, e nenhuma barragem é inventada para ele', () => {
  assert.equal(arvoreDaBacia('itajai-mirim', rioDoCadastro('itajai-mirim'), hidraulica.barragens), null)
})

test('barragem de outro rio não entra nesta árvore', () => {
  const arv = arvoreDaBacia('itajai-acu', rioDoCadastro('itajai-acu'), {
    outra: { tipo: 'contencao_estadual', nome: 'B2', municipio_nome: 'M', rio: 'R', rio_id: 'outro-rio', a_montante_de: 'taio' },
  })
  assert.equal(arv?.cabeceiras[0]?.barragem, null)
  assert.deepEqual(arv?.barragensSoltas, [])
})
