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

import { faixaAscurra } from './municipal'
const agora = new Date('2026-09-11T16:00:00Z')
const leitura = {cidade:'ascurra',codigo:'DCSC-00003',estacao:'SDC-SC Ascurra',nivelBrutoM:8,medidoEm:agora}
test('C18 respeita até 8,50 e emergência estritamente acima de 10,76', () => {
  for (const [n,nome] of [[8.5,'Monitoramento'],[8.51,'Atenção'],[9.75,'Atenção'],[9.77,'Alerta'],[10.76,'Alerta'],[10.77,'Emergência']] as const)
    assert.equal(faixaAscurra({...leitura,nivelBrutoM:n},agora).nome,nome)
  assert.match(faixaAscurra({...leitura,nivelBrutoM:9.76},agora).nome,/inclusão não definida/)
})
test('C18 recusa código ausente, outra régua, dado antigo, futuro e nível inválido', () => {
  for (const alteracao of [{codigo:null},{codigo:'DCSC-00032'},{cidade:'lontras'},{medidoEm:null},{medidoEm:new Date('2026-09-10T16:00:00Z')},{medidoEm:new Date('2026-09-12T16:00:00Z')},{nivelBrutoM:NaN}])
    assert.equal(faixaAscurra({...leitura,...alteracao},agora).nome,'Classificação indisponível')
})
