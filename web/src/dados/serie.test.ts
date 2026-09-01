import { test } from 'node:test'
import assert from 'node:assert/strict'
import { buscarSerie, leituraEm, serieDaCidade } from './serie'
import type { PontoSerie, Transporte } from './serie'

/*
 * O que estes casos protegem: a série é a matéria-prima do slider de 24 h. Se
 * entrar ponto quebrado, se o `medido_em` (hora de Brasília sem fuso) sair
 * convertido errado, ou se a ordenação falhar, o gráfico mente sobre como o rio
 * está subindo — e é justamente disso que alguém decide sair de casa.
 */

const CORPO = {
  gerado_em: '2026-09-01T13:00:00+00:00',
  janela_horas: 48,
  series: {
    'itajai-acu': {
      'rio-do-sul': [
        { medido_em: '2026-09-01T09:00:00', nivel_m: 6.1 },
        { medido_em: '2026-09-01T08:00:00', nivel_m: 5.8 }, // fora de ordem de propósito
        { medido_em: '2026-09-01T10:00:00', nivel_m: 6.6 },
        { medido_em: 'lixo', nivel_m: 9 }, // carimbo inválido: sai
        { medido_em: '2026-09-01T11:00:00', nivel_m: null }, // sem nível: sai
      ],
    },
  },
}

function responde(corpo: unknown): Transporte {
  return async () => ({ ok: true, json: async () => corpo }) as Response
}

test('parseia, descarta ponto inválido e ordena no tempo', async () => {
  const estado = await buscarSerie(undefined, responde(CORPO))
  assert.equal(estado.situacao, 'ok')
  assert.equal(estado.janelaHoras, 48)
  const serie = serieDaCidade(estado, 'itajai-acu', 'rio-do-sul')
  assert.equal(serie.length, 3) // dois inválidos fora
  assert.deepEqual(serie.map((p) => p.nivel_m), [5.8, 6.1, 6.6]) // do mais antigo
})

test('medido_em é lido como hora de Brasília (UTC-3)', async () => {
  const estado = await buscarSerie(undefined, responde(CORPO))
  const serie = serieDaCidade(estado, 'itajai-acu', 'rio-do-sul')
  // 09:00 em Brasília = 12:00 UTC.
  assert.equal(serie[1]!.medidoEm.toISOString(), '2026-09-01T12:00:00.000Z')
})

test('resposta não-ok vira estado indisponível, sem inventar série', async () => {
  const estado = await buscarSerie(undefined, async () => ({ ok: false }) as Response)
  assert.equal(estado.situacao, 'indisponivel')
  assert.deepEqual(serieDaCidade(estado, 'itajai-acu', 'rio-do-sul'), [])
})

test('JSON sem series não quebra', async () => {
  const estado = await buscarSerie(undefined, responde({ gerado_em: 'x' }))
  assert.equal(estado.situacao, 'indisponivel')
})

test('cidade sem pontos não aparece', async () => {
  const estado = await buscarSerie(
    undefined,
    responde({ series: { 'itajai-acu': { itajai: [] } } }),
  )
  assert.deepEqual(serieDaCidade(estado, 'itajai-acu', 'itajai'), [])
})

test('leituraEm pega a última medição até o instante, nunca a futura', () => {
  const pts: PontoSerie[] = [
    { medidoEm: new Date('2026-09-01T12:00:00Z'), nivel_m: 3.0 },
    { medidoEm: new Date('2026-09-01T13:00:00Z'), nivel_m: 4.0 },
    { medidoEm: new Date('2026-09-01T14:00:00Z'), nivel_m: 5.0 },
  ]
  // Antes de tudo: nada.
  assert.equal(leituraEm(pts, new Date('2026-09-01T11:00:00Z').getTime()), null)
  // Entre a 2ª e a 3ª: devolve a 2ª (nunca a de 14h, que ainda não aconteceu).
  assert.equal(leituraEm(pts, new Date('2026-09-01T13:30:00Z').getTime())?.nivel_m, 4.0)
  // Exatamente no carimbo: conta.
  assert.equal(leituraEm(pts, new Date('2026-09-01T14:00:00Z').getTime())?.nivel_m, 5.0)
})
