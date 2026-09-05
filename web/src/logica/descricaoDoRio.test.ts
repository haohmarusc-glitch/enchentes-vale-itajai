/**
 * As linhas "de onde vem a água" da tela de início não podem afirmar uma fila
 * falsa. Afirmaram por dias: "Taió e Rio do Sul → Ibirama → Indaial → …", com
 * Ibirama (Rio Hercílio) como elo do tronco, sem Lontras nem Ascurra, e Taió
 * como começo do Açu. Estes testes travam as linhas ao cadastro e à topologia
 * canônica (docs/TOPOLOGIA-CANONICA.md).
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import {
  descricaoDoRio,
  descreverBarragens,
  listarComE,
  SETA,
  type BarragemParaDescrever,
  type RioParaDescrever,
} from './descricaoDoRio'

const estacoes = JSON.parse(
  readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'),
) as { rios: Record<string, RioParaDescrever> }

function rioDoCadastro(id: string): RioParaDescrever {
  const r = estacoes.rios[id]
  assert.ok(r, `rio ${id} existe no cadastro`)
  return r
}
const hidraulica = JSON.parse(
  readFileSync(new URL('../../../data/hidraulica.json', import.meta.url), 'utf8'),
) as { barragens: Record<string, unknown> }

/** O mesmo filtro de `dados/carregar.barragensDoRio`, sobre o arquivo cru. */
function barragensDoCadastro(rioId: string): BarragemParaDescrever[] {
  return Object.entries(hidraulica.barragens)
    .filter(([k, b]) => !k.startsWith('_') && typeof b === 'object' && b !== null)
    .map(([, b]) => b as BarragemParaDescrever & { rio_id?: string })
    .filter((b) => b.rio_id === rioId)
}
const acuCadastro = rioDoCadastro('itajai-acu')
const acu = descricaoDoRio(acuCadastro, barragensDoCadastro('itajai-acu'))
const mirim = descricaoDoRio(rioDoCadastro('itajai-mirim'), barragensDoCadastro('itajai-mirim'))

test('Açu: o tronco é a sequência canônica, na ordem em que a água desce — e começa em Rio do Sul', () => {
  assert.equal(
    acu.tronco,
    'Rio do Sul → Lontras → Ascurra → Indaial → Blumenau → Gaspar → Ilhota → Itajaí',
  )
})

test('Açu: as cabeceiras são paralelas, cada uma com o seu rio, e se encontram onde o Açu nasce', () => {
  assert.equal(
    acu.cabeceiras,
    'Taió (Itajaí do Oeste) e Ituporanga (Itajaí do Sul) se encontram em Rio do Sul',
  )
  // Taió NÃO encabeça a seta do tronco: a home antiga fazia isso.
  assert.ok(!acu.tronco.includes('Taió'))
})

test('Açu: nenhum afluente lateral aparece como elo da seta', () => {
  const t = acuCadastro._topologia
  assert.ok(t, 'o Açu é ramificado')
  const laterais = t.afluentes_laterais ?? []
  assert.ok(laterais.length >= 3, 'o cadastro tem Ibirama, Timbó e Rio dos Cedros como laterais')
  const nome = new Map(acuCadastro.cidades.map((c) => [c.id, c.nome]))
  const elos = acu.tronco.split(SETA)
  for (const a of laterais) {
    assert.ok(!elos.includes(nome.get(a.id) ?? a.id), `${nome.get(a.id)} não é elo do tronco`)
  }
  // O caso que a captura de tela mostrou, por extenso:
  assert.ok(!acu.tronco.includes('Ibirama'), 'Ibirama fica no Hercílio, não no tronco')
})

test('Açu: os afluentes vão na linha própria, cada um com o rio por onde entra', () => {
  assert.equal(
    acu.laterais,
    'Ibirama, pelo Rio Hercílio (Itajaí do Norte); Timbó, pelo Rio Benedito; Rio dos Cedros (desagua no Benedito)',
  )
})

test('Açu: as TRÊS barragens de contenção, com município e curso, do hidraulica.json', () => {
  assert.equal(
    acu.barragens,
    'Barragem Oeste em Taió, no Itajaí do Oeste; Barragem Sul em Ituporanga, no Itajaí do Sul; ' +
      'Barragem Norte em José Boiteux, no Rio Hercílio (Itajaí do Norte)',
  )
  // Nenhuma barragem vira elo do tronco nem cidade da seta.
  assert.ok(!acu.tronco.includes('Barragem'))
})

test('barragem sem rio_id deste rio não entra; rio sem barragem fica null, não vazio', () => {
  assert.equal(descreverBarragens([]), null)
  assert.equal(barragensDoCadastro('itajai-mirim').length, 0, 'o Mirim não tem barragem de contenção')
})

test('Açu: quem não tem posição na árvore (Trombudo Central) não é afirmado em lugar nenhum', () => {
  for (const linha of [acu.tronco, acu.cabeceiras ?? '', acu.laterais ?? '', acu.barragens ?? '']) {
    assert.ok(!linha.includes('Trombudo'))
  }
})

test('Mirim: fila por `ordem`, igual à topologia canônica (com Guabiruba, que o texto fixo omitia)', () => {
  assert.equal(mirim.tronco, 'Vidal Ramos → Botuverá → Guabiruba → Brusque → Itajaí')
  assert.equal(mirim.cabeceiras, null)
  assert.equal(mirim.laterais, null)
  assert.equal(mirim.barragens, null)
})

test('id sem nome no cadastro aparece pelo id, em vez de sumir calado', () => {
  const rio: RioParaDescrever = {
    cidades: [{ id: 'a', nome: 'A' }],
    _topologia: { tronco_sequencia: ['a', 'fantasma'], cabeceiras_paralelas: [] },
  }
  const d = descricaoDoRio(rio)
  assert.equal(d.tronco, 'A → fantasma')
  assert.equal(d.cabeceiras, null)
})

test('cabeceira sem sub_bacia e sem confluência declarada: cai no primeiro elo do tronco', () => {
  const rio: RioParaDescrever = {
    cidades: [
      { id: 'c1', nome: 'C1' },
      { id: 't1', nome: 'T1' },
    ],
    _topologia: { tronco_sequencia: ['t1'], cabeceiras_paralelas: ['c1'] },
  }
  assert.equal(descricaoDoRio(rio).cabeceiras, 'C1 chega a T1')
})

test('fila ignora cidade sem ordem em vez de embaralhar', () => {
  const rio: RioParaDescrever = {
    cidades: [
      { id: 'c', nome: 'C', ordem: 3 },
      { id: 'x', nome: 'X', ordem: null },
      { id: 'a', nome: 'A', ordem: 1 },
    ],
  }
  assert.equal(descricaoDoRio(rio).tronco, 'A → C')
})

test('listarComE fala como gente', () => {
  assert.equal(listarComE([]), '')
  assert.equal(listarComE(['A']), 'A')
  assert.equal(listarComE(['A', 'B']), 'A e B')
  assert.equal(listarComE(['A', 'B', 'C']), 'A, B e C')
})
