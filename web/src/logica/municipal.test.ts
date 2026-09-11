import { test } from 'node:test'
import assert from 'node:assert/strict'
import { fontesGovernamentais, historicoMunicipal } from './municipal'
test('aceita domínio governamental e rejeita nome enganoso ou menção sem endereço', () => {
  assert.equal(fontesGovernamentais('https://ascurra.sc.gov.br/documento').length, 1)
  assert.equal(fontesGovernamentais('https://ascurra.sc.gov.br.example.com/x').length, 0)
  assert.equal(fontesGovernamentais('Segundo a Defesa Civil').length, 0)
})
test('histórico municipal não mistura cidades nem fontes sem endereço governamental', () => {
  const base = {rio:'itajai-acu',cidade:'ascurra',data:'2023',pico_m:10,confianca:'alta' as const,fonte:'https://ascurra.sc.gov.br/a'}
  assert.equal(historicoMunicipal([base,{...base,cidade:'lontras'},{...base,fonte:'https://jornal.example/a'}], 'ascurra').length, 1)
})
