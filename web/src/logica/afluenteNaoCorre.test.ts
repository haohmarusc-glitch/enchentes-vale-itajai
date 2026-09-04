/**
 * Ribeirão fica cinza e PARADO — e o dia em que isso mudar tem de ser uma
 * decisão, não um efeito colateral.
 *
 * HISTÓRICO (04/09/2026). Este arquivo já afirmou que o canal retificado do
 * Mirim também devia ficar cinza. Estava errado, e o morador é que viu: o canal
 * NÃO é afluente, é o próprio Itajaí-Mirim em outro leito (as réguas DC-03…DC-06
 * dizem `rio: "itajai-mirim"`; pelo JICA ele leva 2/3 da vazão). Pior: o curso
 * antigo, ao lado, já saía pintado e animado, porque a geometria dele está
 * dentro de `itajai-mirim.geojson`. O canal foi para `canaisDoTronco.ts` e hoje
 * é pintado pela âncora de montante, Brusque — ver `canalDoTronco.test.ts`.
 *
 * O que continua valendo, e é o motivo de este arquivo existir: os RIBEIRÕES de
 * Itajaí (Murta, Canhanduba, e o Conceição que fecha o vão) ficam cinza. A razão
 * é a régua, não o desenho: são de estuário — a maré cruza a cota sem enchente
 * nenhuma —, e por isso estão marcadas `alerta_automatico: false`. Correnteza
 * animada SIGNIFICA faixa (`VEL_FAIXA` é indexado por faixa); fazer a água
 * correr ali afirmaria um nível que a maré não deixa ler.
 *
 * Isso vale hoje por DOIS caminhos independentes, e é bom que valha:
 *
 *  1. o afluente entra na cena sem cidade (`cidades: []`), então todo trecho cai
 *     em `sem-dado`, e `VEL_FAIXA['sem-dado'] = 0`;
 *  2. as réguas que ficam nesses cursos estão marcadas `alerta_automatico:
 *     false`, então nem por elas o trecho ganharia faixa.
 *
 * Se o `medir_mare.py` um dia destravar uma delas, o caminho (2) cai. Este
 * arquivo existe para que isso apareça como um teste vermelho — uma pergunta a
 * responder — em vez de o mapa começar a correr sozinho.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { VEL_FAIXA } from './mapaCanvas'

const MONITOR = readFileSync(new URL('../telas/MonitorBacia.tsx', import.meta.url), 'utf8')
const estacoes = JSON.parse(
  readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'),
) as {
  rios: Record<string, { cidades: { id: string }[] }>
  estacoes_tempo_real: {
    codigo?: string
    rio?: string
    alerta_automatico?: boolean
    cotas_m?: Record<string, number>
  }[]
}

/** Os afluentes que o Monitor desenha, lidos do próprio componente. */
function afluentes(): string[] {
  const i = MONITOR.indexOf('const AFLUENTES')
  assert.ok(i >= 0, 'AFLUENTES sumiu do MonitorBacia')
  const bloco = MONITOR.slice(i, MONITOR.indexOf(']', i))
  return [...bloco.matchAll(/'([a-z-]+)'/g)].map((m) => m[1]!)
}

test('cinza não corre: a velocidade de sem-dado é exatamente zero', () => {
  assert.equal(VEL_FAIXA['sem-dado'], 0)
})

test('os ribeirões de Itajaí estão entre os afluentes desenhados', () => {
  const lista = afluentes()
  for (const id of ['ribeirao-murta', 'ribeirao-canhanduba', 'rio-conceicao']) {
    assert.ok(lista.includes(id), `${id} saiu da lista de afluentes do Monitor`)
  }
})

test('o canal retificado NÃO é afluente — é o próprio Mirim', () => {
  assert.ok(
    !afluentes().includes('mirim-canal-retificado'),
    'o canal voltou para os afluentes: ficaria cinza e parado ao lado do curso ' +
      'antigo, pintado e animado, no mesmo trecho do mesmo rio',
  )
})

test('nenhum afluente tem cidade no cadastro — é o que o mantém sem faixa', () => {
  for (const id of afluentes()) {
    const cidades = estacoes.rios[id]?.cidades ?? []
    assert.equal(
      cidades.length,
      0,
      `${id} ganhou cidade no cadastro: o trecho passaria a ser pintado e ANIMADO. ` +
        'Decida se ele deve correr antes de deixar este teste passar.',
    )
  }
})

test('as réguas dos afluentes continuam travadas pela maré', () => {
  const nosAfluentes = estacoes.estacoes_tempo_real.filter(
    (e) => e.rio && afluentes().includes(e.rio),
  )
  assert.ok(nosAfluentes.length > 0, 'nenhuma régua nos afluentes — o teste virou vazio')
  for (const e of nosAfluentes) {
    assert.equal(
      e.alerta_automatico,
      false,
      `${e.codigo} deixou de ser travada pela maré. Se a medição (scripts/medir_mare.py) ` +
        'destravou mesmo, decida também se o curso dela passa a correr no mapa — ' +
        'correnteza significa faixa.',
    )
  }
})
