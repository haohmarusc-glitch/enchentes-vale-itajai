/**
 * As páginas por cidade existem? E o endereço aponta para uma cidade real?
 *
 * O que estes testes protegem é um link quebrado numa noite de chuva. `/acu/…`
 * é um endereço que se dita por telefone; se ele levar a "cidade não
 * encontrada", a pessoa conclui que o site caiu.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

/**
 * Lê o cadastro do disco em vez de `dados/carregar`, que passa pelo alias
 * `@dados` do Vite — alias que o executor de testes não resolve. O que importa
 * aqui é o DADO, e ele é o mesmo arquivo.
 */
const estacoes = JSON.parse(
  readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'),
) as {
  rios: Record<
    string,
    { cidades: { id: string }[]; _topologia?: { tronco_sequencia?: string[] } }
  >
}

const cidadesDoRio = (rioId: string) => estacoes.rios[rioId]?.cidades ?? []
const troncoDoRio = (rioId: string) => estacoes.rios[rioId]?._topologia?.tronco_sequencia ?? null

const RIO_DA_URL: Record<string, string> = {
  acu: 'itajai-acu',
  mirim: 'itajai-mirim',
}

test('toda cidade do Açu e do Mirim tem um id usável em URL', () => {
  for (const rioId of Object.values(RIO_DA_URL)) {
    const cidades = cidadesDoRio(rioId)
    assert.ok(cidades.length > 0, `${rioId} sem cidades`)
    for (const c of cidades) {
      assert.match(c.id, /^[a-z0-9-]+$/, `id "${c.id}" não cabe numa URL limpa`)
    }
  }
})

test('os apelidos da URL batem com os ids do cadastro', () => {
  for (const [apelido, rioId] of Object.entries(RIO_DA_URL)) {
    assert.ok(cidadesDoRio(rioId).length > 0, `/${apelido} não resolve para rio nenhum`)
  }
})

test('o tronco do Açu só nomeia cidades que existem no cadastro', () => {
  const tronco = troncoDoRio('itajai-acu')
  assert.ok(tronco, 'o Açu tem de ter tronco — é uma árvore, não uma fila')
  const ids = new Set(cidadesDoRio('itajai-acu').map((c) => c.id))
  for (const id of tronco!) {
    assert.ok(ids.has(id), `tronco cita "${id}", que não está no cadastro`)
  }
})

test('cidade fora do tronco é reconhecível — a página não pode inventar vizinha', () => {
  const noTronco = new Set(troncoDoRio('itajai-acu')!)
  const fora = cidadesDoRio('itajai-acu').filter((c) => !noTronco.has(c.id))
  // O Açu é uma ÁRVORE: existem cidades fora do tronco, e é justamente para
  // elas que a página tem de dizer "não há montante/jusante afirmável".
  assert.ok(fora.length > 0, 'se ninguém ficou fora do tronco, a árvore virou fila')
})
