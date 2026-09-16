import {test} from 'node:test'
import assert from 'node:assert/strict'
import {construirCena} from './mapaMotor'
import type {ReguaNoMapa} from './reguasNoMapa'

test('DC-11 pinta só Açu a jusante, sem alterar pinos, mar ou outros rios',()=>{
  globalThis.getComputedStyle=(()=>({getPropertyValue:()=>''})) as unknown as typeof getComputedStyle
  const cidades=['gaspar','ilhota','itajai'].map((id,i)=>({id,nome:id,coordenadas:[-27,-49+i*0.02],cotas_m:{}}))
  const coords=[[[-49,-27],[-48.985,-27]],[[-48.975,-27],[-48.96,-27]],[[-48.96,-27],[-48.95,-27]]]
  const rios=['itajai-acu','itajai-mirim','ribeirao-murta'].map(rioId=>({rioId,cidades,coords}))
  const r={codigo:'DC-11',cidade:'itajai',lon:-48.98,lat:-27,faixa:'alerta'} as ReguaNoMapa
  const criar=(ref?:ReguaNoMapa,repro=false)=>construirCena({} as Element,rios as never,{leituras:[]} as never,new Date(),800,600,null,repro?()=>null:undefined,undefined,undefined,ref)
  const base=criar(),cena=criar(r)
  assert.deepEqual(cena.pinos,base.pinos)
  assert.deepEqual(cena.mar,base.mar)
  for(const rio of ['itajai-mirim','ribeirao-murta']) assert.deepEqual(cena.trechos.filter(t=>t.rioId===rio),base.trechos.filter(t=>t.rioId===rio))
  const acu=cena.trechos.filter(t=>t.rioId==='itajai-acu')
  assert.equal(acu[0]!.faixa,'sem-dado')
  assert.ok(acu.slice(1).every(t=>t.faixa==='alerta'))
  assert.ok(criar({...r,faixa:null}).trechos.filter(t=>t.rioId==='itajai-acu').every(t=>t.faixa==='sem-dado'))
  assert.deepEqual(criar(r,true).trechos,base.trechos)
  assert.deepEqual(criar({...r,codigo:'DC-10'}).trechos,base.trechos)
})

