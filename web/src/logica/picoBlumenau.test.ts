import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import type { PontoSerie } from '../dados/serie'
import { porRegua } from '../dados/serie'
import { publicacaoMaisRecente, situacaoDoPico } from './picoBlumenau'
import { deBrasilia } from './tempoReal'

const ponto = (iso: string, nivel: number, regua: string | null = 'Blumenau'): PontoSerie => ({
  medidoEm: deBrasilia(iso),
  nivel_m: nivel,
  regua,
})

/**
 * A cheia de 11–12/09/2026, como o coletor publicou (registro em data/brutos),
 * pela publicação da Defesa Civil de Itajaí. A do AlertaBlu, nesse registro,
 * tem os horários 3 h adiantados (UTC gravado como hora de Brasília — o defeito
 * do CLAUDE.md, já corrigido na coleta): não serve de gabarito.
 */
function cheia1209(): PontoSerie[] {
  const d = JSON.parse(
    readFileSync(new URL('../../../data/brutos/evento-2026-09-11-12-serie-recente-2200Z.json', import.meta.url), 'utf8'),
  )
  const nomes: string[] = d.reguas['itajai-acu'].blumenau
  return (d.series['itajai-acu'].blumenau as { medido_em: string; nivel_m: number; r: number }[])
    .map((p) => ponto(p.medido_em, p.nivel_m, nomes[p.r] ?? null))
    .filter((p) => p.regua === 'Blumenau')
}

test('12/09/2026, 14h: o pico já passou, num platô de quase três horas', () => {
  const s = situacaoDoPico(cheia1209(), deBrasilia('2026-09-12T14:00:00'))
  assert.equal(s.tipo, 'passou')
  if (s.tipo !== 'passou') return
  assert.equal(s.pico.nivel_m, 7.87)
  assert.equal(s.pico.medidoEm.getTime(), deBrasilia('2026-09-12T02:15:00').getTime())
  // A menos de 5 cm do máximo das 00h45 às 03h35: a janela usa o platô inteiro.
  assert.equal(s.platoInicio.getTime(), deBrasilia('2026-09-12T00:45:00').getTime())
  assert.equal(s.platoFim.getTime(), deBrasilia('2026-09-12T03:35:00').getTime())
})

test('12/09/2026, 01h: o rio ainda sobe — o pico não aconteceu', () => {
  const s = situacaoDoPico(cheia1209(), deBrasilia('2026-09-12T01:00:00'))
  assert.notEqual(s.tipo, 'passou')
})

test('a última leitura não é tratada como pico enquanto o rio sobe', () => {
  const s = situacaoDoPico(
    [ponto('2026-10-03T10:00:00', 5.0), ponto('2026-10-03T11:00:00', 5.2), ponto('2026-10-03T12:00:00', 5.4)],
    deBrasilia('2026-10-03T12:10:00'),
  )
  assert.equal(s.tipo, 'subindo')
})

test('descida de poucos centímetros não basta para dar o pico como passado', () => {
  const s = situacaoDoPico(
    [ponto('2026-10-03T10:00:00', 5.0), ponto('2026-10-03T11:00:00', 6.0), ponto('2026-10-03T12:00:00', 5.96), ponto('2026-10-03T13:00:00', 5.95)],
    deBrasilia('2026-10-03T13:10:00'),
  )
  assert.equal(s.tipo, 'no-alto')
})

test('uma leitura só abaixo do máximo não basta: precisa de duas', () => {
  const s = situacaoDoPico(
    [ponto('2026-10-03T10:00:00', 5.0), ponto('2026-10-03T11:00:00', 6.0), ponto('2026-10-03T12:00:00', 5.8)],
    deBrasilia('2026-10-03T12:10:00'),
  )
  assert.notEqual(s.tipo, 'passou')
})

test('leitura velha não dá situação nenhuma', () => {
  const s = situacaoDoPico(
    [ponto('2026-10-03T01:00:00', 5.0), ponto('2026-10-03T02:00:00', 5.2)],
    deBrasilia('2026-10-03T12:00:00'),
  )
  assert.equal(s.tipo, 'sem-dado')
})

test('máximo no começo da janela: o pico pode ter sido antes, e isso é dito', () => {
  const s = situacaoDoPico(
    [ponto('2026-10-03T00:00:00', 7.0), ponto('2026-10-03T03:00:00', 6.7), ponto('2026-10-03T06:00:00', 6.4)],
    deBrasilia('2026-10-03T06:10:00'),
  )
  assert.equal(s.tipo, 'passou')
  if (s.tipo === 'passou') assert.equal(s.inicioIncerto, true)
})

test('usa a publicação com a leitura mais recente, sem misturar as duas fontes', () => {
  const pontos = [
    ponto('2026-10-03T10:00:00', 5.0, 'Blumenau (AlertaBlu)'),
    ponto('2026-10-03T10:30:00', 5.1, 'Blumenau'),
    ponto('2026-10-03T11:00:00', 5.2, 'Blumenau (AlertaBlu)'),
  ]
  const escolhida = publicacaoMaisRecente(porRegua(pontos))
  assert.ok(escolhida.every((p) => p.regua === 'Blumenau (AlertaBlu)'))
})
