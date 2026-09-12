import { test } from 'node:test'
import assert from 'node:assert/strict'
import { desenharCorrenteza, type Cena } from './mapaMotor'

function ondas(faixa: string, tempo: number) {
  const pontos: number[][] = []
  const ctx = { beginPath() {}, moveTo() {}, stroke() {}, bezierCurveTo(...p: number[]) { pontos.push(p) } } as unknown as CanvasRenderingContext2D
  const cena = { trechos: [{ pts: [[0, 0], [200, 0]], cum: [0, 200], total: 200, faixa }] } as unknown as Cena
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
