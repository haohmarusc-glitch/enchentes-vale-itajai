import { test } from 'node:test'
import assert from 'node:assert/strict'
import { chuvaDaCidade, resumir, textoFaixa } from './chuva'
import type { ChuvaAoVivo, MilimetrosPorJanela } from '../dados/tempoReal'

/** Base com os números reais da DC-09 em 30/08/2026; `mm` entra por janela. */
type Ajuste = Partial<Omit<ChuvaAoVivo, 'mm'>> & { mm?: Partial<MilimetrosPorJanela> }

function leitura(over: Ajuste = {}): ChuvaAoVivo {
  const { mm, ...resto } = over
  return {
    estacao: 'DC-09',
    rio: 'ribeirao-murta',
    cidade: 'itajai',
    medidoEm: new Date('2026-08-30T21:10:00Z'),
    coerente: true,
    incoerencias: [],
    ...resto,
    mm: { min10: 0, h1: 0.4, h12: 39.6, h24: 39.6, h48: 41.4, ...mm },
  }
}

test('sem pluviômetro na cidade não há resumo', () => {
  assert.equal(resumir([]), null)
  assert.equal(chuvaDaCidade([leitura({ cidade: 'itajai' })], 'blumenau'), null)
})

test('um pluviômetro: o valor dele', () => {
  const r = resumir([leitura({})])!
  assert.equal(r.pluviometros, 1)
  assert.deepEqual(r.porJanela.h24, { maior: 39.6, menor: 39.6 })
})

test('vários pluviômetros mostram o maior e guardam a faixa', () => {
  // Os cinco de Itajaí, com os números reais de 30/08/2026: a chuva caiu
  // desigual pela cidade, e a média inventaria um meio-termo inexistente.
  const r = resumir([
    leitura({ estacao: 'DC-06', mm: { h24: 14.0 } }),
    leitura({ estacao: 'DC-08', mm: { h24: 19.0 } }),
    leitura({ estacao: 'DC-07', mm: { h24: 30.0 } }),
    leitura({ estacao: 'DC-09', mm: { h24: 39.6 } }),
  ])!
  assert.equal(r.pluviometros, 4)
  assert.deepEqual(r.porJanela.h24, { maior: 39.6, menor: 14 })
  assert.equal(textoFaixa(r.porJanela.h24!), '14,0–39,6 mm')
})

test('leitura incoerente é descartada e contada', () => {
  // O caso real da estação Guarani, em Brusque: 0,20 mm em 10 min e 0,00 mm em
  // 1 h. Zero ali é "sem dado", e entraria como se não tivesse chovido.
  const r = resumir([
    leitura({ estacao: 'DC-09', mm: { h24: 39.6 } }),
    leitura({ estacao: 'Guarani', coerente: false, incoerencias: ['min10 > h1'], mm: { h24: 0 } }),
  ])!
  assert.equal(r.pluviometros, 1)
  assert.equal(r.descartados, 1)
  assert.equal(r.porJanela.h24!.maior, 39.6)
  assert.equal(r.porJanela.h24!.menor, 39.6, 'o zero suspeito não pode virar o piso da faixa')
})

test('só leituras incoerentes: o problema aparece, não vira "sem chuva"', () => {
  const r = resumir([leitura({ coerente: false, incoerencias: ['min10 > h1'] })])!
  assert.equal(r.pluviometros, 0)
  assert.equal(r.descartados, 1)
  assert.deepEqual(r.porJanela, {})
})

test('janela ausente na fonte não vira zero', () => {
  const r = resumir([leitura({ mm: { h48: null } })])!
  assert.equal(r.porJanela.h48, undefined)
  assert.equal(r.porJanela.h24?.maior, 39.6)
})

test('não existe janela de 6 h', () => {
  const r = resumir([leitura({})])!
  assert.ok(!('h6' in r.porJanela), 'a fonte não publica 6 h e não se estima')
})

test('diferença de aparelho não vira faixa na tela', () => {
  assert.equal(textoFaixa({ maior: 39.6, menor: 39.4 }), '39,6 mm')
  assert.equal(textoFaixa({ maior: 39.6, menor: 39.0 }), '39,0–39,6 mm')
})

test('o horário do resumo é o da medição mais recente', () => {
  const r = resumir([
    leitura({ medidoEm: new Date('2026-08-30T21:10:00Z') }),
    leitura({ estacao: 'Brusque', medidoEm: new Date('2026-08-30T21:15:00Z') }),
  ])!
  assert.equal(r.medidoEm?.toISOString(), '2026-08-30T21:15:00.000Z')
})
