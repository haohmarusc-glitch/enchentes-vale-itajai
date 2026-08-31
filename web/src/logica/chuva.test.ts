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

test('o horário do resumo é o da medição mais ANTIGA', () => {
  // Este teste afirmava o contrário e, com isso, travava o defeito no lugar:
  // ele exigia a medição mais recente. Como o valor exibido é o MAIOR entre os
  // pluviômetros, e o maior pode vir do aparelho mais parado, a idade só é
  // verdadeira sobre o conjunto se for a do mais velho.
  const r = resumir([
    leitura({ medidoEm: new Date('2026-08-30T21:10:00Z') }),
    leitura({ estacao: 'Brusque', medidoEm: new Date('2026-08-30T21:15:00Z') }),
  ])!
  assert.equal(r.medidoEm?.toISOString(), '2026-08-30T21:10:00.000Z')
  assert.equal(r.maisNovoEm?.toISOString(), '2026-08-30T21:15:00.000Z')
})

test('a idade do resumo é a do pluviômetro mais VELHO', () => {
  // Os valores mostrados são o maior de cada janela, e o maior pode vir do
  // aparelho parado. Com a idade do mais novo, a tela dizia "80 mm em 24 h,
  // há 5 min" sobre uma leitura de três horas atrás.
  const resumo = resumir([
    leitura({ estacao: 'VELHO', medidoEm: new Date('2026-08-30T15:30:00Z'), mm: { h24: 80 } }),
    leitura({ estacao: 'NOVO', medidoEm: new Date('2026-08-30T18:25:00Z'), mm: { h24: 2 } }),
  ])
  assert.equal(resumo?.medidoEm?.toISOString(), '2026-08-30T15:30:00.000Z')
  assert.equal(resumo?.maisNovoEm?.toISOString(), '2026-08-30T18:25:00.000Z')
})

test('o maior valor exibido nunca é mais novo do que a idade declarada', () => {
  // A invariante que importa: a idade é um limite superior para o conjunto.
  const resumo = resumir([
    leitura({ estacao: 'A', medidoEm: new Date('2026-08-30T10:00:00Z'), mm: { h24: 90 } }),
    leitura({ estacao: 'B', medidoEm: new Date('2026-08-30T18:00:00Z'), mm: { h24: 1 } }),
    leitura({ estacao: 'C', medidoEm: new Date('2026-08-30T17:00:00Z'), mm: { h24: 5 } }),
  ])
  assert.equal(resumo?.porJanela.h24?.maior, 90)
  assert.equal(resumo?.medidoEm?.toISOString(), '2026-08-30T10:00:00.000Z')
})

test('um pluviômetro só tem as duas idades iguais', () => {
  const resumo = resumir([
    leitura({ estacao: 'UNICO', medidoEm: new Date('2026-08-30T18:00:00Z'), mm: { h24: 7 } }),
  ])
  assert.equal(resumo?.medidoEm?.getTime(), resumo?.maisNovoEm?.getTime())
})
