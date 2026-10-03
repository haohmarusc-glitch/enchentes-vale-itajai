import assert from 'node:assert/strict'
import { test } from 'node:test'
import { deBrasilia } from '../logica/tempoReal'
import type { BrutoEstadual } from './nivelSc'
import type { EstadoTempoReal, LeituraAoVivo } from './tempoReal'
import type { Cidade } from './tipos'
import { estadoDaCidade, faixaDaRedeEstadual, type AoVivo } from './usarAoVivo'

const AGORA = deBrasilia('2026-10-03T16:10:00')

const cidade = (id: string, cotas: Record<string, number> = { atencao: 3, emergencia: 5 }): Cidade =>
  ({ id, nome: id, cotas_m: cotas }) as unknown as Cidade

const bruto = (cidadeId: string, faixa: BrutoEstadual['faixaEstadual'], iso = '2026-10-03T16:01:00'): BrutoEstadual => ({
  cidade: cidadeId, estacao: `SDC-SC ${cidadeId}`, codigo: 'DCSC-00000', nivelBrutoM: 2.3, medidoEm: deBrasilia(iso), faixaEstadual: faixa,
})

function aoVivo(leituras: LeituraAoVivo[], estaduais: BrutoEstadual[]): AoVivo {
  return {
    tempoReal: { situacao: 'ok', leituras } as unknown as EstadoTempoReal,
    nivelSc: new Map(estaduais.map((b) => [b.cidade, b])),
    serie: { series: {} } as unknown as AoVivo['serie'],
    agora: AGORA,
  }
}

const leitura = (cidadeId: string, iso: string): LeituraAoVivo => ({
  estacao: cidadeId, rio: 'itajai-acu', cidade: cidadeId, nivel_m: 4, medidoEm: deBrasilia(iso), resgateDe: null,
})

test('sem régua municipal, a cidade ganha a faixa que a Defesa Civil de SC publica', () => {
  const e = estadoDaCidade(cidade('ibirama'), 'itajai-acu', aoVivo([], [bruto('ibirama', 'atencao')]))
  assert.equal(e.faixa, 'sem-dado', 'a faixa da cidade continua sem cor: não sai de cota nossa')
  assert.equal(e.faixaEstadual, 'atencao')
})

test('com leitura municipal de agora, a municipal manda e a estadual não aparece', () => {
  const e = estadoDaCidade(cidade('taio'), 'itajai-acu', aoVivo([leitura('taio', '2026-10-03T16:00:00')], [bruto('taio', 'atencao')]))
  assert.equal(e.faixaEstadual, null)
})

test('municipal velha: a estadual fresca aparece, para dizer o nível de agora', () => {
  const e = estadoDaCidade(cidade('indaial'), 'itajai-acu', aoVivo([leitura('indaial', '2026-09-12T22:00:00')], [bruto('indaial', 'normal')]))
  assert.equal(e.faixa, 'sem-dado')
  assert.equal(e.faixaEstadual, 'normal')
  assert.equal(e.estadual?.nivelBrutoM, 2.3)
})

test('estadual velha, sem carimbo ou sem faixa publicada: sem cor', () => {
  assert.equal(faixaDaRedeEstadual(bruto('x', 'alerta', '2026-10-03T09:00:00'), 'x', AGORA), null)
  assert.equal(faixaDaRedeEstadual({ ...bruto('x', 'alerta'), medidoEm: null }, 'x', AGORA), null)
  assert.equal(faixaDaRedeEstadual(bruto('x', null), 'x', AGORA), null)
})
