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
    {
      cidades: { id: string; nome: string }[]
      _topologia?: { tronco_sequencia?: string[] }
    }
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

/**
 * A cidade que tem tela própria não pode cair na página genérica.
 *
 * `/itajai` existe para explicar a maré e, sobretudo, POR QUE não se mostra "o
 * nível de Itajaí" ao vivo: são onze réguas com zeros diferentes, que na mesma
 * hora marcam 0,92 m e 4,82 m. A página genérica ao lado dela mostraria uma
 * versão mais pobre da mesma cidade e contradiria essa explicação — duas telas
 * do mesmo lugar dizendo coisas diferentes é como se perde quem lê.
 */
const TELA_CIDADE = readFileSync(new URL('../telas/TelaCidade.tsx', import.meta.url), 'utf8')
const APP = readFileSync(new URL('../App.tsx', import.meta.url), 'utf8')

function telasProprias(): Record<string, string> {
  const i = TELA_CIDADE.indexOf('const TELA_PROPRIA')
  assert.ok(i >= 0, 'TELA_PROPRIA sumiu de TelaCidade.tsx')
  const bloco = TELA_CIDADE.slice(i, TELA_CIDADE.indexOf('}', i))
  const saida: Record<string, string> = {}
  for (const m of bloco.matchAll(/(\w[\w-]*):\s*'([^']+)'/g)) saida[m[1]!] = m[2]!
  return saida
}

test('Itajaí encaminha para a tela da foz, não para a página genérica', () => {
  assert.equal(telasProprias().itajai, '/itajai')
})

test('toda tela própria apontada existe como rota no App', () => {
  for (const [cidadeId, rota] of Object.entries(telasProprias())) {
    assert.ok(
      APP.includes(`path="${rota}"`),
      `TELA_PROPRIA manda ${cidadeId} para ${rota}, que não é rota do App`,
    )
  }
})

test('cidade com tela própria continua no cadastro — o desvio não a apaga', () => {
  const ids = new Set(cidadesDoRio('itajai-acu').map((c) => c.id))
  for (const cidadeId of Object.keys(telasProprias())) {
    assert.ok(ids.has(cidadeId), `${cidadeId} tem tela própria mas sumiu do cadastro do Açu`)
  }
})

/**
 * O índice de cidades da tela inicial.
 *
 * É a porta mais curta do site: quem abre na chuva quer a cidade dele, sem ter
 * de saber em qual rio ela fica. Um link errado aqui manda a pessoa para uma
 * página vazia no pior momento possível.
 */
const INICIO = readFileSync(new URL('../telas/Inicio.tsx', import.meta.url), 'utf8')

test('o índice da tela inicial monta o endereço no mesmo formato das rotas', () => {
  // `/acu/gaspar` e `/mirim/brusque`: apelido do rio + id da cidade.
  assert.match(INICIO, /\$\{apelido\}\/\$\{c\.id\}/, 'o índice deixou de montar /<rio>/<cidade>')
  assert.match(INICIO, /'\/itajai'/, 'Itajaí precisa ir para a tela da foz, não para a genérica')
})

test('Itajaí está nos DOIS rios — por isso o índice tem de desduplicar', () => {
  const noAcu = cidadesDoRio('itajai-acu').some((c) => c.id === 'itajai')
  const noMirim = cidadesDoRio('itajai-mirim').some((c) => c.id === 'itajai')
  assert.ok(noAcu && noMirim, 'se Itajaí sair de um dos rios, a desduplicação vira código morto')
})

test('nenhuma cidade repete id dentro do mesmo rio — o índice usaria a chave errada', () => {
  for (const rioId of ['itajai-acu', 'itajai-mirim']) {
    const ids = cidadesDoRio(rioId).map((c) => c.id)
    assert.equal(new Set(ids).size, ids.length, `${rioId} tem id repetido`)
  }
})

test('toda cidade tem nome não vazio — chip sem rótulo é chip que ninguém acha', () => {
  for (const rioId of ['itajai-acu', 'itajai-mirim']) {
    for (const c of cidadesDoRio(rioId)) {
      assert.ok(String(c.nome ?? '').trim().length > 0, `${rioId}/${c.id} sem nome`)
    }
  }
})
