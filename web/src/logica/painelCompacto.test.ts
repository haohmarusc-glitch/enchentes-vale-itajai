import { test } from 'node:test'
import assert from 'node:assert/strict'
import { cotaDaFaixa, estadoDaLeitura, textoTendenciaCompacta } from './painelCompacto'
import type { Cidade } from '../dados/tipos'

const agora = new Date('2026-10-07T12:00:00-03:00')
const min = (n: number) => new Date(agora.getTime() - n * 60_000)

test('estado da leitura: a hora sempre por extenso; velha vira "antiga"; sem hora, sem leitura', () => {
  const fresca = estadoDaLeitura(min(17), agora, 'rio-do-sul')
  assert.equal(fresca.tipo, 'agora')
  assert.match(fresca.texto, /^Leitura: há 17 min · \d\d\/\d\d, \d\d:\d\d$/)
  assert.equal(estadoDaLeitura(min(100), agora, 'rio-do-sul').tipo, 'atrasada')
  const velha = estadoDaLeitura(min(4 * 60), agora, 'rio-do-sul')
  assert.equal(velha.tipo, 'velha')
  assert.match(velha.texto, /^Leitura antiga: há 4 h .* — não é a de agora$/)
  // Blumenau envelhece em 120 min (MIN_VELHA_BLUMENAU).
  assert.equal(estadoDaLeitura(min(130), agora, 'blumenau').tipo, 'velha')
  assert.deepEqual(estadoDaLeitura(null, agora, 'x'), { tipo: 'sem', texto: 'Sem leitura fresca nesta régua' })
  assert.equal(estadoDaLeitura(min(5), agora, 'ilhota', 'Leitura estadual').texto.startsWith('Leitura estadual: há 5 min'), true)
})

test('tendência compacta: seta só com tendência; sem ela, dito', () => {
  assert.deepEqual(textoTendenciaCompacta({ rotulo: 'subindo', cmh: 12 } as never), { seta: '▲', texto: 'subindo 12 cm/h', nota: 'última hora, nesta régua' })
  assert.equal(textoTendenciaCompacta({ rotulo: 'descendo', cmh: -4 } as never).seta, '▼')
  assert.equal(textoTendenciaCompacta({ rotulo: 'estável', cmh: 0 } as never).texto, 'estável')
  assert.equal(textoTendenciaCompacta(null).seta, '—')
  assert.match(textoTendenciaCompacta(null).texto, /sem tendência/)
})

test('cota da faixa: a da faixa de agora; sem faixa, a primeira cota dita como primeira; sem cota, dito', () => {
  const rioDoSul = { id: 'rio-do-sul', nome: 'Rio do Sul', cotas_m: { atencao: 4.5, alerta: 5.5, emergencia: 6.5 } } as unknown as Cidade
  assert.deepEqual(cotaDaFaixa(rioDoSul, 'atencao', 'municipal'), { titulo: 'Cota de Atenção', valor: '4,50 m', nota: 'faixa de agora, na régua desta cidade' })
  assert.deepEqual(cotaDaFaixa(rioDoSul, 'normal', 'municipal'), { titulo: 'Primeira cota (Atenção)', valor: '4,50 m', nota: 'nível abaixo desta cota' })
  assert.equal(cotaDaFaixa(rioDoSul, 'sem-dado', 'municipal').nota, 'sem faixa para esta leitura')
  // O nome da Defesa Civil da cidade vence (D6).
  const ilhota = { id: 'ilhota', nome: 'Ilhota', cotas_m: { alerta: 8 }, cotas_nomes_na_fonte: { alerta: 'Prontidão' } } as unknown as Cidade
  assert.equal(cotaDaFaixa(ilhota, 'alerta', 'municipal').titulo, 'Cota de Prontidão')
  const semCota = { id: 'x', nome: 'X', cotas_m: {} } as unknown as Cidade
  assert.deepEqual(cotaDaFaixa(semCota, 'sem-dado', 'municipal'), { titulo: 'Cota', valor: null, nota: 'sem cota cadastrada para esta régua' })
  assert.equal(cotaDaFaixa(semCota, 'varias', 'varias').valor, null)
  assert.match(cotaDaFaixa(semCota, 'atencao', 'estadual').nota, /Defesa Civil de SC/)
})
