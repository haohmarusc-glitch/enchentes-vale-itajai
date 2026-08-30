import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  atingidas,
  buscar,
  cidadesComCotas,
  faixaDaCidade,
  faltaPara,
  nomeCompleto,
  normalizar,
  proximas,
} from './cotasRuas'
import type { CotaRua } from '../dados/tipos'

function c(over: Partial<CotaRua>): CotaRua {
  return {
    cidade: 'blumenau',
    rio: 'itajai-acu',
    rua: 'Rua São Rafael',
    bairro: 'Itoupava Norte',
    ponto: null,
    cota_m: 7.4,
    fonte: 'F',
    data_fonte: '2022-05',
    confianca: 'media',
    ...over,
  }
}

// Os números reais de Blumenau e de Brusque.
const DADOS: CotaRua[] = [
  c({ rua: 'Rua São Rafael', ponto: 'final da rua', cota_m: 7.4 }),
  c({ rua: 'Rua São Rafael', ponto: 'próximo ao nº 169', cota_m: 7.75 }),
  c({ rua: 'Rua Martha Cordeiro', bairro: 'Fortaleza', ponto: 'ponto mais baixo', cota_m: 7.6 }),
  c({ rua: 'Rua Max Aldemann', bairro: 'Fortaleza', cota_m: 7.95 }),
  c({ cidade: 'brusque', rio: 'itajai-mirim', rua: 'Av. Beira-Rio', bairro: null, cota_m: 4.8 }),
  c({ cidade: 'gaspar', rio: 'itajai-acu', rua: 'Rua Alfazema', bairro: null, cota_m: null,
      nota: 'entre as primeiras a alagar; cota exata não publicada' }),
]

test('cada cidade só vê as próprias ruas', () => {
  // 7 m em Gaspar não é 7 m em Blumenau: misturar é o erro mais grave possível.
  assert.deepEqual(cidadesComCotas(DADOS), ['blumenau', 'brusque', 'gaspar'])
  assert.equal(atingidas(DADOS, 'blumenau', 10).length, 4)
  assert.equal(atingidas(DADOS, 'brusque', 10).length, 1)
})

test('a mesma rua com dois pontos conta como duas', () => {
  // Agrupar por nome perderia o ponto que alaga primeiro.
  const achadas = buscar(DADOS, 'blumenau', 'sao rafael')
  assert.equal(achadas.length, 2)
  assert.deepEqual(achadas.map((x) => x.cota_m), [7.4, 7.75], 'a mais baixa vem primeiro')
})

test('busca ignora acento e caixa', () => {
  assert.equal(buscar(DADOS, 'blumenau', 'SAO RAFAEL').length, 2)
  assert.equal(buscar(DADOS, 'blumenau', 'são rafael').length, 2)
  assert.equal(normalizar('Rua Vitório Demarchi'), 'rua vitorio demarchi')
})

test('busca por bairro também acha', () => {
  assert.equal(buscar(DADOS, 'blumenau', 'fortaleza').length, 2)
})

test('busca curta demais não devolve a lista inteira', () => {
  assert.deepEqual(buscar(DADOS, 'blumenau', 'r'), [])
})

test('rua sem cota aparece na busca, mas por último', () => {
  const achadas = buscar(DADOS, 'gaspar', 'alfazema')
  assert.equal(achadas.length, 1)
  assert.equal(achadas[0]!.cota_m, null)
})

test('rua sem cota fica fora de qualquer conta', () => {
  // Nulo não é zero: entrar como zero a faria aparecer como "já alagada".
  assert.equal(atingidas(DADOS, 'gaspar', 99).length, 0)
  assert.equal(proximas(DADOS, 'gaspar', 0).length, 0)
  assert.equal(faixaDaCidade(DADOS, 'gaspar'), null)
})

test('atingidas com o rio num nível', () => {
  const em77 = atingidas(DADOS, 'blumenau', 7.7)
  assert.deepEqual(em77.map((x) => x.cota_m), [7.4, 7.6])
})

test('a cota exata conta como atingida', () => {
  // A rua alaga A PARTIR daquele nível: excluir a igualdade tiraria a rua da
  // lista exatamente no metro em que ela começa a alagar.
  assert.equal(atingidas(DADOS, 'blumenau', 7.4).length, 1)
})

test('próximas a alagar, em ordem', () => {
  const p = proximas(DADOS, 'blumenau', 7.5, 2)
  assert.deepEqual(p.map((x) => x.cota_m), [7.6, 7.75])
})

test('faixa da cidade', () => {
  assert.deepEqual(faixaDaCidade(DADOS, 'blumenau'), { min: 7.4, max: 7.95 })
  assert.deepEqual(faixaDaCidade(DADOS, 'brusque'), { min: 4.8, max: 4.8 })
})

test('quanto falta subir, arredondado ao centímetro', () => {
  assert.equal(faltaPara(7.4, 5.1), 2.3)
  assert.equal(faltaPara(7.4, 7.8), -0.4, 'negativo quando a rua já alagou')
  assert.equal(faltaPara(7.75, 7.7), 0.05, 'sem sujeira de ponto flutuante')
})

test('o ponto faz parte do nome mostrado', () => {
  assert.equal(nomeCompleto(c({ ponto: 'final da rua' })), 'Rua São Rafael (final da rua)')
  assert.equal(nomeCompleto(c({ ponto: null })), 'Rua São Rafael')
})
