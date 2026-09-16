import { test } from 'node:test'
import assert from 'node:assert/strict'
import { camadaBlumenau } from './camadaBlumenau'
import { frescorDaCidade } from './tempoReal'
const agora = new Date('2026-09-12T21:00:00Z')
const camadas = [8,8.5,9,18].map(nivel_m => ({nivel_m,arquivo:String(nivel_m)}))
const leitura = {cidade:'blumenau',estacao:'Blumenau (AlertaBlu)',nivel_m:8.7,medidoEm:agora}
test('carta inferior disponível, sem interpolar nem desenhar abaixo de 8 m', () => {
  assert.equal(camadaBlumenau(camadas,[leitura],agora)?.nivel_m,8.5)
  assert.equal(camadaBlumenau(camadas,[{...leitura,nivel_m:6.1}],agora),null)
  assert.equal(camadaBlumenau(camadas,[{...leitura,nivel_m:8}],agora)?.nivel_m,8)
})
test('recusa outra régua, leitura antiga e futura', () => {
  for (const l of [{...leitura,estacao:'Outra'}, {...leitura,medidoEm:new Date('2026-09-12T18:59:00Z')}, {...leitura,medidoEm:new Date('2026-09-12T22:00:00Z')}])
    assert.equal(camadaBlumenau(camadas,[l],agora),null)
  assert.equal(frescorDaCidade(120,'blumenau'),'atrasada')
  assert.equal(frescorDaCidade(121,'blumenau'),'velha')
  assert.equal(frescorDaCidade(121,'gaspar'),'atrasada')
})
