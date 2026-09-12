import { test } from 'node:test'
import assert from 'node:assert/strict'
import { comReferenciaAscurra } from './referenciaAscurra'
import { faixaDaCidade } from '../logica/tempoReal'
import { faixaAscurra } from '../logica/municipal'
import type { EstadoTempoReal } from './tempoReal'
import type { BrutoEstadual } from './nivelSc'
import type { Cidade } from './tipos'
const agora = new Date('2026-09-12T20:00:00Z')
const estado: EstadoTempoReal = {situacao:'ok',leituras:[],chuva:[],chuvaOk:true,coletadoEm:agora,fonte:null}
const cidade: Cidade = {id:'ascurra',nome:'Ascurra',ordem:null,codigo_ana:null,verificado:false,fontes_tempo_real:[],cotas_m:{atencao:8.5,alerta:9.76,emergencia:10.76}}
const bruto: BrutoEstadual = {cidade:'ascurra',codigo:'DCSC-00003',estacao:'SDC-SC Ascurra',nivelBrutoM:8.94,medidoEm:agora}

test('C18 usa a mesma faixa no regional e no piloto, inclusive nos limites', () => {
  for (const [n,faixa,nome] of [[8.5,'monitoramento','Monitoramento'],[8.51,'atencao','Atenção'],[9.76,'sem-dado','Limite'],[9.77,'alerta','Alerta'],[10.76,'alerta','Alerta'],[10.77,'emergencia','Emergência']] as const) {
    const l = {...bruto,nivelBrutoM:n}
    const leitura = comReferenciaAscurra(estado,new Map([['ascurra',l]])).leituras[0]!
    assert.equal(faixaDaCidade(cidade,leitura,false,agora),faixa)
    assert.ok(faixaAscurra(l,agora).nome.startsWith(nome))
  }
})
test('não vincula outro código, cidade, leitura sem horário ou valor inválido', () => {
  for (const delta of [{codigo:null},{codigo:'DCSC-00032'},{cidade:'lontras'},{medidoEm:null},{nivelBrutoM:NaN}])
    assert.equal(comReferenciaAscurra(estado,new Map([['ascurra',{...bruto,...delta}]])),estado)
})
test('idade antiga e carimbo futuro não pintam Ascurra', () => {
  for (const d of ['2026-09-11T20:00:00Z','2026-09-13T20:00:00Z']) {
    const leitura = comReferenciaAscurra(estado,new Map([['ascurra',{...bruto,medidoEm:new Date(d)}]])).leituras[0]!
    assert.equal(faixaDaCidade(cidade,leitura,false,agora),'sem-dado')
  }
})
test('não substitui nem mistura régua desconhecida com a documentada', () => {
  const outra = {cidade:'ascurra',rio:'itajai-acu',estacao:'Outra régua',nivel_m:2,medidoEm:agora,resgateDe:null}
  const dados = comReferenciaAscurra({...estado,leituras:[outra]},new Map([['ascurra',bruto]]))
  assert.equal(dados.leituras.length,2)
  assert.equal(dados.leituras[0],outra)
  assert.equal(faixaDaCidade(cidade,outra,false,agora),'sem-dado')
})
