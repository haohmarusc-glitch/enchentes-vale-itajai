import { test } from 'node:test'
import assert from 'node:assert/strict'
import { desenharCorrenteza, desenharOnda, construirCena, type Cena } from './mapaMotor'

function ondas(faixa: string, tempo: number) {
  const pontos: number[][] = []
  globalThis.Path2D = class { moveTo() {} lineTo() {} } as unknown as typeof Path2D
  const ctx = { lineDashOffset: 0, lineWidth: 0, save() {}, restore() {}, setLineDash() {}, stroke(this: { lineDashOffset: number; lineWidth: number; strokeStyle: string }) { assert.equal(this.strokeStyle, '#abcdef'); pontos.push([this.lineDashOffset, this.lineWidth]) } } as unknown as CanvasRenderingContext2D
  const cena = { cores: { [faixa]: '#abcdef' }, trechos: [{ pts: [[0, 0], [200, 0]], cum: [0, 200], total: 200, faixa, animacao: 'direcional' }] } as unknown as Cena
  desenharCorrenteza(ctx, cena, tempo)
  return pontos
}
test('ondas têm mesma posição e tamanho em todas as faixas animadas', () => {
  for (const faixa of ['monitoramento', 'atencao', 'alerta', 'inundacao']) {
    assert.deepEqual(ondas(faixa, 1.5), ondas('normal', 1.5))
  }
})
test('ondas dependem do instante, não de chamadas anteriores ou outro rio', () => {
  const antes = ondas('normal', 2)
  ondas('alerta', 9)
  assert.deepEqual(ondas('normal', 2), antes)
  assert.notDeepEqual(ondas('normal', 2.1), antes)
  assert.deepEqual(ondas('sem-dado', 2), antes)
})


test('ambos os efeitos obedecem à mesma autorização, inclusive no cinza', () => {
  for (const faixa of ['sem-dado','normal','alerta','varias']) {
    for (const animacao of [undefined,'parada','direcional']) {
      for (const desenhar of [desenharCorrenteza,desenharOnda]) {
        let chamadas=0
        const ctx={save(){},restore(){},beginPath(){},moveTo(){},lineTo(){},setLineDash(){},stroke(){chamadas++}} as unknown as CanvasRenderingContext2D
        const cena={cores:{[faixa]:'#abcdef'},trechos:[{pts:[[0,0],[200,0]],faixa,animacao,progMid:0.5}]} as unknown as Cena
        desenhar(ctx,cena,2.75)
        assert.equal(chamadas>0,animacao==='direcional',`${faixa}/${animacao}/${desenhar.name}`)
      }
    }
  }
})

test('cena neutra autoriza montante orientada, bloqueia foz e afluente sem âncoras', () => {
  globalThis.getComputedStyle=(()=>({getPropertyValue:()=>''})) as unknown as typeof getComputedStyle
  const cidades=['taio','ilhota','itajai'].map((id,i)=>({id,nome:id,coordenadas:[-27,-49+i*0.01],cotas_m:{}}))
  const rios=[{rioId:'itajai-acu',cidades,coords:[
    [[-49,-27],[-48.995,-27],[-48.99,-27]],
    [[-48.99,-27],[-48.98,-27]],
  ]},{rioId:'ribeirao-murta',cidades:[],coords:[[[-49,-27],[-48.98,-27]]]}]
  const cena=construirCena({} as Element,rios as never,{leituras:[]} as never,new Date(),800,600,null)
  assert.ok(cena.trechos.some(t=>t.faixa==='sem-dado'&&t.animacao==='direcional'))
  assert.ok(cena.trechos.some(t=>t.rioId==='itajai-acu'&&t.animacao==='parada'))
  assert.ok(cena.trechos.filter(t=>t.rioId==='ribeirao-murta').every(t=>t.animacao==='parada'))
})
