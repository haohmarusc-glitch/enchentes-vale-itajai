import assert from 'node:assert/strict'
import { test } from 'node:test'
import type { Cidade, Trecho } from '../dados/tipos'
import {
  MIN_AGORA,
  MIN_VELHA,
  chegadasSePicoAgora,
  deBrasilia,
  frescor,
  foraDeOrdem,
  idadeMin,
  primeiraCota,
  textoIdade,
} from './tempoReal'

test('horário sem fuso é lido como hora de Brasília', () => {
  // 16:01 em Brasília (UTC-3) é 19:01 UTC.
  assert.equal(deBrasilia('2026-08-30T16:01:00').toISOString(), '2026-08-30T19:01:00.000Z')
})

test('a conversão não depende do fuso de quem abre a página', () => {
  // O valor é um instante absoluto: qualquer aparelho chega ao mesmo número.
  const instante = deBrasilia('2026-08-30T16:01:00').getTime()
  assert.equal(instante, Date.UTC(2026, 7, 30, 19, 1, 0))
})

test('horário inválido não vira data silenciosamente errada', () => {
  assert.ok(Number.isNaN(deBrasilia('ontem').getTime()))
})

test('idade em minutos, sem futuro negativo', () => {
  const medido = new Date('2026-08-30T19:00:00Z')
  assert.equal(idadeMin(medido, new Date('2026-08-30T19:12:00Z')), 12)
  assert.equal(idadeMin(medido, new Date('2026-08-30T18:50:00Z')), 0, 'relógio adiantado não é futuro')
})

test('frescor separa o que serve do que não serve', () => {
  assert.equal(frescor(10), 'agora')
  assert.equal(frescor(MIN_AGORA), 'agora')
  assert.equal(frescor(MIN_AGORA + 1), 'atrasada')
  assert.equal(frescor(MIN_VELHA), 'atrasada')
  assert.equal(frescor(MIN_VELHA + 1), 'velha')
})

test('leitura de uma hora ainda serve — é o ritmo real de algumas fontes', () => {
  // A estação MKS de Rio do Sul publica quase uma hora atrás das DC de Itajaí.
  // Com o limite antigo de 45 min ela ficaria permanentemente indisponível.
  assert.equal(frescor(52), 'agora')
  assert.equal(frescor(60), 'agora')
})

test('texto da idade em português', () => {
  assert.equal(textoIdade(0), 'agora mesmo')
  assert.equal(textoIdade(12), 'há 12 min')
  assert.equal(textoIdade(120), 'há 2 h')
  assert.equal(textoIdade(125), 'há 2 h 05')
  assert.equal(textoIdade(60 * 24), 'há 1 dia')
  assert.equal(textoIdade(60 * 72), 'há 3 dias')
})

const cidade = (id: string, nome: string, ordem: number, cotas: Record<string, number> = {}): Cidade => ({
  id,
  nome,
  ordem,
  codigo_ana: null,
  verificado: false,
  cotas_m: cotas,
  fontes_tempo_real: [],
})

const CIDADES = [
  cidade('rio-do-sul', 'Rio do Sul', 1, { atencao: 4.5, alerta: 5.5, inundacao: 6.5 }),
  cidade('blumenau', 'Blumenau', 2, { inundacao: 7.4, atencao: 6.0 }),
  cidade('gaspar', 'Gaspar', 3),
  cidade('itajai', 'Itajaí', 4),
]

const TRECHOS: Trecho[] = [
  { rio: 'itajai-acu', de: 'rio-do-sul', para: 'blumenau', horas_min: 7, horas_max: 10, confianca: 'alta', fonte: 'JICA' },
  { rio: 'itajai-acu', de: 'blumenau', para: 'itajai', horas_min: 14, horas_max: 17, confianca: 'alta', fonte: 'JICA' },
]

test('chegada a jusante a partir de um pico agora', () => {
  const agora = new Date('2026-08-30T19:00:00Z')
  const chegadas = chegadasSePicoAgora(TRECHOS, 'itajai-acu', CIDADES, CIDADES[0]!, agora)
  assert.equal(chegadas.length, 2, 'Blumenau direto e Itajaí pela soma dos trechos')
  assert.equal(chegadas[0]!.cidade.id, 'blumenau')
  assert.equal(chegadas[0]!.inicio.toISOString(), '2026-08-31T02:00:00.000Z')
  assert.equal(chegadas[0]!.fim.toISOString(), '2026-08-31T05:00:00.000Z')
  assert.equal(chegadas[1]!.cidade.id, 'itajai')
  assert.equal(chegadas[1]!.inicio.toISOString(), '2026-08-31T16:00:00.000Z')
})

test('cidade sem trecho conhecido fica de fora, não vira palpite', () => {
  const chegadas = chegadasSePicoAgora(TRECHOS, 'itajai-acu', CIDADES, CIDADES[0]!, new Date())
  assert.ok(!chegadas.some((c) => c.cidade.id === 'gaspar'))
})

test('a última cidade não tem para onde mandar', () => {
  const chegadas = chegadasSePicoAgora(TRECHOS, 'itajai-acu', CIDADES, CIDADES[3]!, new Date())
  assert.deepEqual(chegadas, [])
})

test('primeira cota é a mais baixa que importa', () => {
  assert.deepEqual(primeiraCota(CIDADES[0]!), { chave: 'atencao', valor: 4.5 })
  assert.deepEqual(primeiraCota(CIDADES[1]!), { chave: 'atencao', valor: 6.0 })
  assert.equal(primeiraCota(CIDADES[2]!), null, 'sem cota levantada, sem palpite')
})

test('janela fora da ordem do rio é detectada', () => {
  // A água passa pelas cidades na ordem do curso. Quando os trechos vêm de
  // fontes que não concordam, uma cidade pode aparecer recebendo antes de
  // outra acima dela — e isso tem de ser dito, não arrumado por baixo.
  const chegada = (h: number) =>
    ({ inicio: new Date(2026, 7, 31, h), fim: new Date(2026, 7, 31, h + 3) }) as never

  assert.equal(foraDeOrdem([chegada(1), chegada(2), chegada(5)]), false)
  assert.equal(foraDeOrdem([chegada(2), chegada(1)]), true)
  assert.equal(foraDeOrdem([]), false)
  assert.equal(foraDeOrdem([chegada(4)]), false)
})
