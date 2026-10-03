import assert from 'node:assert/strict'
import { test } from 'node:test'
import { escalaDoMedidor } from './medidor'

const BLUMENAU = { monitoramento: 3, atencao: 4, alerta: 6, emergencia: 8 }

test('segmentos na ordem da escada, com a faixa que cada cota abre', () => {
  const e = escalaDoMedidor(BLUMENAU, 6.4)!
  assert.deepEqual(e.segmentos.map((s) => s.faixa), ['normal', 'monitoramento', 'atencao', 'alerta', 'emergencia'])
  assert.equal(e.segmentos[0]!.de, 0)
  assert.equal(e.segmentos.at(-1)!.ate, 1)
  // Contíguos: o fim de um é o começo do outro.
  for (let i = 1; i < e.segmentos.length; i++) assert.equal(e.segmentos[i]!.de, e.segmentos[i - 1]!.ate)
})

test('o marcador cai entre as cotas certas', () => {
  const e = escalaDoMedidor(BLUMENAU, 6.4)!
  const alerta = e.marcas.find((m) => m.chave === 'alerta')!.pos
  const emergencia = e.marcas.find((m) => m.chave === 'emergencia')!.pos
  assert.ok(e.nivel! > alerta && e.nivel! < emergencia)
})

test('marca de comportamento não vira degrau', () => {
  assert.equal(escalaDoMedidor({ seguranca_observada: 9.2 }, 9), null)
  const e = escalaDoMedidor({ atencao: 4.8, praca_boca_lobo: 6.02 }, null)!
  assert.deepEqual(e.marcas.map((m) => m.chave), ['atencao'])
  assert.equal(e.nivel, null)
})

test('a barra estica para caber nível fora das cotas', () => {
  const alto = escalaDoMedidor(BLUMENAU, 15.5)!
  assert.ok(alto.max >= 15.5)
  assert.ok(alto.nivel! < 1)
  const baixo = escalaDoMedidor({ atencao: 8.5, alerta: 9.76, emergencia: 10.76 }, 2)!
  assert.ok(baixo.min <= 2)
  assert.ok(baixo.nivel! > 0)
})

test('com cotas altas, a barra não começa no zero da régua', () => {
  const e = escalaDoMedidor({ atencao: 8.5, alerta: 9.76, emergencia: 10.76 }, 9)!
  assert.ok(e.min > 5)
})
