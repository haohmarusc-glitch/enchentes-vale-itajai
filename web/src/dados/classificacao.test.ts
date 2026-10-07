import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { deBrasilia } from '../logica/tempoReal'
import { buscarClassificacao, faixasDoMotor, MAX_IDADE_CLASSIFICACAO_MIN, montarClassificacao } from './classificacao'

// Os portões do PR 2: o site só segue o motor com a decisão desta coleta, sobre as mesmas medições
// que a tela mostra, e com a idade refeita no relógio de agora. Fora disso, a regra de sempre (null).

const gabarito = JSON.parse(
  readFileSync(new URL('../../../data/classificacao-esperada.json', import.meta.url), 'utf8'),
) as { casos: { id: string; motor: Record<string, unknown> }[] }

/** A saída real do motor para um caso do gabarito, copiada para poder ser alterada no teste. */
function motorDe(id: string): Record<string, any> {
  const caso = gabarito.casos.find((c) => c.id === id)
  assert.ok(caso, id)
  return JSON.parse(JSON.stringify(caso.motor))
}

const AGORA = deBrasilia('2026-10-07T13:05:00') // o `gerado_em` do gabarito
const minDepois = (n: number) => new Date(AGORA.getTime() + n * 60_000)
// O caso "abaixo-da-atencao": municipal 2,29 m às 12:59:55, estadual normal às 13:00:00.
const TELA = {
  leituraMedidaEm: deBrasilia('2026-10-07T12:59:55'),
  estadualMedidaEm: deBrasilia('2026-10-07T13:00:00'),
  varias: false,
}

test('desta coleta e com as mesmas medições: a cor é a do motor, com a origem', () => {
  const r = faixasDoMotor(montarClassificacao(motorDe('abaixo-da-atencao')), 'brusque', 'itajai-mirim', TELA, AGORA)
  assert.deepEqual(r?.faixa, 'normal')
  assert.equal(r?.faixaEstadual, null)
  assert.equal(r?.origem?.tipo, 'municipal')
  assert.equal(r?.origem?.reguaId, 'DCSC-00019')
  assert.match(r!.origem!.rotulo, /^Classificação municipal/)
})

test('arquivo de outra coleta não vale: regra de sempre', () => {
  const estado = montarClassificacao(motorDe('abaixo-da-atencao'))
  assert.ok(faixasDoMotor(estado, 'brusque', 'itajai-mirim', TELA, minDepois(MAX_IDADE_CLASSIFICACAO_MIN)))
  assert.equal(faixasDoMotor(estado, 'brusque', 'itajai-mirim', TELA, minDepois(MAX_IDADE_CLASSIFICACAO_MIN + 1)), null)
  assert.equal(faixasDoMotor(estado, 'brusque', 'itajai-mirim', TELA, minDepois(-16)), null, 'gerado no futuro')
})

test('o motor viu outra medição que a tela: a cor dele seria de outro número', () => {
  const estado = montarClassificacao(motorDe('abaixo-da-atencao'))
  const outra = deBrasilia('2026-10-07T13:10:00')
  assert.equal(faixasDoMotor(estado, 'brusque', 'itajai-mirim', { ...TELA, leituraMedidaEm: outra }, AGORA), null)
  assert.equal(faixasDoMotor(estado, 'brusque', 'itajai-mirim', { ...TELA, estadualMedidaEm: outra }, AGORA), null)
  assert.equal(faixasDoMotor(estado, 'brusque', 'itajai-mirim', { ...TELA, leituraMedidaEm: null }, AGORA), null)
  assert.equal(faixasDoMotor(estado, 'brusque', 'itajai-mirim', { ...TELA, varias: true }, AGORA), null)
})

test('cidade fora do piloto ou no outro rio: regra de sempre', () => {
  const estado = montarClassificacao(motorDe('abaixo-da-atencao'))
  assert.equal(faixasDoMotor(estado, 'blumenau', 'itajai-acu', TELA, AGORA), null)
  assert.equal(faixasDoMotor(estado, 'brusque', 'itajai-acu', TELA, AGORA), null)
  assert.equal(faixasDoMotor(null, 'brusque', 'itajai-mirim', TELA, AGORA), null)
})

test('a idade é refeita agora: a municipal que envelheceu depois da coleta deixa a estadual entrar', () => {
  // Coleta às 13:05: municipal 3,50 m das 10:10 (175 min, atrasada mas pinta) e estadual de 12:55.
  const m = motorDe('atrasada-ainda-pinta')
  const c = m.cidades.brusque.classificacoes
  c.municipal.medido_em = '2026-10-07T10:10:00'
  c.estadual.medido_em = '2026-10-07T12:55:00'
  const estado = montarClassificacao(m)
  const tela = {
    leituraMedidaEm: deBrasilia('2026-10-07T10:10:00'),
    estadualMedidaEm: deBrasilia('2026-10-07T12:55:00'),
    varias: false,
  }
  assert.equal(faixasDoMotor(estado, 'brusque', 'itajai-mirim', tela, AGORA)?.faixa, 'atencao')
  // 15 min depois, a municipal tem 190 min: velha. Não pinta e não segura a estadual, como no site.
  const depois = faixasDoMotor(estado, 'brusque', 'itajai-mirim', tela, minDepois(15))
  assert.equal(depois?.faixa, 'sem-dado')
  assert.equal(depois?.faixaEstadual, 'atencao')
  assert.equal(depois?.origem?.tipo, 'estadual')
  assert.match(depois!.origem!.aviso!, /Não são as cotas do município/)
})

test('a estadual que envelheceu depois da coleta também para de pintar', () => {
  const m = motorDe('so-estadual')
  m.cidades.brusque.classificacoes.estadual.medido_em = '2026-10-07T10:10:00'
  const estado = montarClassificacao(m)
  const tela = { leituraMedidaEm: null, estadualMedidaEm: deBrasilia('2026-10-07T10:10:00'), varias: false }
  assert.equal(faixasDoMotor(estado, 'brusque', 'itajai-mirim', tela, AGORA)?.faixaEstadual, 'alerta')
  const depois = faixasDoMotor(estado, 'brusque', 'itajai-mirim', tela, minDepois(15))
  assert.deepEqual(depois, { faixa: 'sem-dado', faixaEstadual: null, origem: null })
})

test('arquivo que o site não entende é ignorado inteiro, ou a cidade estranha', () => {
  const bom = motorDe('abaixo-da-atencao')
  assert.equal(montarClassificacao(null), null)
  assert.equal(montarClassificacao('<html>'), null)
  assert.equal(montarClassificacao({ ...bom, versao: 2 }), null)
  assert.equal(montarClassificacao({ ...bom, gerado_em: '2026-10-07T16:05:00' }), null, 'sem fuso')

  const fora = motorDe('abaixo-da-atencao')
  fora.cidades.brusque.classificacoes.municipal.faixa = 'vermelho'
  assert.equal(montarClassificacao(fora)?.cidades.size, 0)

  const outraRegua = motorDe('abaixo-da-atencao')
  outraRegua.cidades.brusque.classificacoes.municipal.regua_da_leitura = 'Brusque'
  assert.equal(montarClassificacao(outraRegua)?.cidades.size, 0, 'cor de outra régua não passa nem aqui')

  const semCarimbo = motorDe('abaixo-da-atencao')
  semCarimbo.cidades.brusque.classificacoes.municipal.medido_em = null
  assert.equal(montarClassificacao(semCarimbo)?.cidades.size, 0)

  const trocada = motorDe('abaixo-da-atencao')
  trocada.cidades.brusque.classificacoes.estadual.tipo = 'municipal'
  assert.equal(montarClassificacao(trocada)?.cidades.size, 0)
})

test('sem o arquivo (VPS sem o motor, rede fora): null, e o site segue pela regra de sempre', async () => {
  assert.equal(await buscarClassificacao(undefined, async () => new Response('não', { status: 404 })), null)
  assert.equal(await buscarClassificacao(undefined, async () => { throw new Error('rede') }), null)
  const ok = await buscarClassificacao(undefined, async () => new Response(JSON.stringify(motorDe('so-estadual')), { status: 200 }))
  assert.equal(ok?.cidades.get('brusque')?.estadual.faixa, 'alerta')
})
