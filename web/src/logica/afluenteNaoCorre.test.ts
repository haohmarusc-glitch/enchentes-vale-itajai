/**
 * Ribeirão e canal ficam cinza e PARADOS — e o dia em que isso mudar tem de ser
 * uma decisão, não um efeito colateral.
 *
 * O relato foi: "o canal retificado do Mirim não tem animação". Está certo, e a
 * razão importa. Não é falta de número: a SEMASA (DC-03) publica 0,41 m e o pino
 * mostra. É que a correnteza animada SIGNIFICA a faixa — `VEL_FAIXA` é indexado
 * por faixa —, e a régua daquele trecho é de ESTUÁRIO: a maré cruza a cota sem
 * enchente nenhuma. Fazer a água correr ali afirmaria um nível que a maré não
 * deixa ler.
 *
 * Hoje isso vale por DOIS caminhos independentes, e é bom que valha:
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

test('os três cursos de Itajaí estão entre os afluentes desenhados', () => {
  const lista = afluentes()
  for (const id of ['ribeirao-murta', 'ribeirao-canhanduba', 'mirim-canal-retificado']) {
    assert.ok(lista.includes(id), `${id} saiu da lista de afluentes do Monitor`)
  }
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
