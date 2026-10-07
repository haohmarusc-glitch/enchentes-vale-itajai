import { test } from 'node:test'
import assert from 'node:assert/strict'
import { destaqueDaBacia, type PinoParaDestaque } from './destaqueDaBacia'
import { faixaDaCidade } from './tempoReal'
import type { Cidade } from '../dados/tipos'

const agora = new Date('2026-10-07T12:00:00-03:00')
const pino = (id: string, faixa: PinoParaDestaque['faixa'], extra: Partial<PinoParaDestaque> = {}): PinoParaDestaque => ({
  cidade: { id, nome: id },
  rioId: 'itajai-acu',
  faixa,
  nivel: 4.98,
  medidoEm: agora,
  ...extra,
})

test('destaque: a faixa municipal mais grave, com nível e hora; nunca estadual, várias, cinza ou abaixo da atenção', () => {
  assert.equal(destaqueDaBacia([pino('a', 'normal'), pino('b', 'monitoramento'), pino('c', 'sem-dado'), pino('d', 'varias')]), null)
  assert.equal(destaqueDaBacia([pino('a', 'alerta', { origemFaixa: 'estadual' })]), null, 'faixa estadual não é destaque nosso')
  assert.equal(destaqueDaBacia([pino('a', 'atencao', { nivel: null })]), null, 'sem o número do próprio pino não há o que destacar')
  assert.equal(destaqueDaBacia([pino('rio-do-sul', 'atencao'), pino('blumenau', 'alerta'), pino('gaspar', 'atencao')])?.cidade.id, 'blumenau')
  assert.equal(destaqueDaBacia([pino('rio-do-sul', 'atencao'), pino('gaspar', 'atencao')])?.cidade.id, 'gaspar', 'empate: ordem alfabética, estável')
})

test('a faixa de um pino só existe com cota do cadastro e leitura fresca (correção 1 da maquete)', () => {
  const comCota = { id: 'rio-do-sul', nome: 'Rio do Sul', cotas_m: { atencao: 4.5, alerta: 5.5, emergencia: 6.5 } } as unknown as Cidade
  const semCota = { id: 'x', nome: 'X', cotas_m: {} } as unknown as Cidade
  const fresca = { nivel_m: 4.98, medidoEm: new Date(agora.getTime() - 17 * 60_000) }
  const velha = { nivel_m: 4.98, medidoEm: new Date(agora.getTime() - 4 * 3_600_000) }
  assert.equal(faixaDaCidade(comCota, fresca, false, agora), 'atencao')
  assert.equal(faixaDaCidade(semCota, fresca, false, agora), 'sem-dado', 'sem cota: só o nível, nenhuma faixa')
  assert.equal(faixaDaCidade(comCota, velha, false, agora), 'sem-dado', 'leitura velha: nenhuma faixa')
  assert.equal(faixaDaCidade(comCota, null, false, agora), 'sem-dado')
})
