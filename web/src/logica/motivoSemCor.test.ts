import { test } from 'node:test'
import assert from 'node:assert/strict'
import { motivoSemCor, motivoSemCorNoMonitor } from './motivoSemCor'
const agora = new Date('2026-09-11T03:00:00Z')

test('municipal antiga tem prioridade sobre bruto estadual presente', () => {
  assert.match(motivoSemCorNoMonitor({ atencao: 3 }, new Date('2026-09-10T20:00:00Z'), agora, true, true, 'indaial'), /mais de 3 horas/)
  assert.match(motivoSemCorNoMonitor({ atencao: 3 }, null, agora, true, true, 'indaial'), /horário válido/)
  assert.match(motivoSemCorNoMonitor({ atencao: 3 }, null, agora, false, true, 'indaial'), /vínculo confirmado/)
  assert.match(motivoSemCorNoMonitor({ atencao: 4 }, new Date('2026-09-11T00:30:00Z'), agora, true, true, 'blumenau'), /duas horas/)
})
test('distingue falta de faixa de marca histórica sem acionamento', () => {
  assert.match(motivoSemCor({ inundacao_historica: 5 }, agora, agora), /Faltam faixas/)
})
test('distingue leitura antiga, ausente e futura', () => {
  const cotas = { atencao: 5 }
  assert.match(motivoSemCor(cotas, new Date('2026-09-10T23:00:00Z'), agora), /mais de 3 horas/)
  assert.match(motivoSemCor(cotas, null, agora), /horário válido/)
  assert.match(motivoSemCor(cotas, new Date('2026-09-11T06:00:00Z'), agora), /futuro/)
})
