import { test } from 'node:test'
import assert from 'node:assert/strict'
import { desenharCorrenteza, type Cena } from './mapaMotor'

function ondas(faixa: string, tempo: number) {
  const pontos: number[][] = []
  globalThis.Path2D = class { moveTo() {} lineTo() {} } as unknown as typeof Path2D
  const ctx = { lineDashOffset: 0, lineWidth: 0, save() {}, restore() {}, setLineDash() {}, stroke(this: { lineDashOffset: number; lineWidth: number; strokeStyle: string }) { assert.equal(this.strokeStyle, '#abcdef'); pontos.push([this.lineDashOffset, this.lineWidth]) } } as unknown as CanvasRenderingContext2D
  const cena = { cores: { [faixa]: '#abcdef' }, trechos: [{ pts: [[0, 0], [200, 0]], cum: [0, 200], total: 200, faixa }] } as unknown as Cena
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
  assert.deepEqual(ondas('sem-dado', 2), [])
})
