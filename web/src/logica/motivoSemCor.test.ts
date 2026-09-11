import { test } from 'node:test'
import assert from 'node:assert/strict'
import { motivoSemCor } from './motivoSemCor'
const agora = new Date('2026-09-11T03:00:00Z')
test('distingue falta de faixa de marca histórica sem acionamento', () => {
  assert.match(motivoSemCor({ inundacao_historica: 5 }, agora, agora), /Faltam faixas/)
})
test('distingue leitura antiga, ausente e futura', () => {
  const cotas = { atencao: 5 }
  assert.match(motivoSemCor(cotas, new Date('2026-09-10T23:00:00Z'), agora), /mais de 3 horas/)
  assert.match(motivoSemCor(cotas, null, agora), /horário válido/)
  assert.match(motivoSemCor(cotas, new Date('2026-09-11T06:00:00Z'), agora), /futuro/)
})
