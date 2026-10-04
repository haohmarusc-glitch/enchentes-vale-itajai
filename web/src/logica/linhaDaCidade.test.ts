import assert from 'node:assert/strict'
import { test } from 'node:test'
import type { BrutoEstadual } from '../dados/nivelSc'
import type { EstadoTempoReal, LeituraAoVivo } from '../dados/tempoReal'
import type { Cidade } from '../dados/tipos'
import { estadoDaCidade, type AoVivo } from '../dados/usarAoVivo'
import { situacaoDaLinha } from './linhaDaCidade'
import { deBrasilia } from './tempoReal'

const AGORA = deBrasilia('2026-10-03T21:30:00')
const cidade = (id: string) => ({ id, nome: id, cotas_m: { atencao: 3, emergencia: 5 } }) as unknown as Cidade
const bruto = (cidadeId: string, faixa: BrutoEstadual['faixaEstadual'], iso = '2026-10-03T21:15:00'): BrutoEstadual => ({
  cidade: cidadeId, estacao: `SDC-SC ${cidadeId}`, codigo: 'DCSC-00030', nivelBrutoM: 9.51, medidoEm: deBrasilia(iso), faixaEstadual: faixa,
})
const leitura = (cidadeId: string, iso: string): LeituraAoVivo => ({
  estacao: cidadeId, rio: 'itajai-acu', cidade: cidadeId, nivel_m: 4, medidoEm: deBrasilia(iso), resgateDe: null,
})
function situacao(id: string, leituras: LeituraAoVivo[], estaduais: BrutoEstadual[]) {
  const v: AoVivo = {
    tempoReal: { situacao: 'ok', leituras } as unknown as EstadoTempoReal,
    nivelSc: new Map(estaduais.map((b) => [b.cidade, b])),
    serie: { series: {} } as unknown as AoVivo['serie'],
    agora: AGORA,
  }
  const estado = estadoDaCidade(cidade(id), 'itajai-acu', v)
  return { estado, linha: situacaoDaLinha(estado, id, AGORA) }
}

test('Ilhota: leitura estadual de 15 min sem faixa publicada não é "sem leitura"', () => {
  const { estado, linha } = situacao('ilhota', [], [bruto('ilhota', null)])
  assert.deepEqual(linha, { tipo: 'estadual', nivel: 9.51, idade: 15, comFaixa: false })
  assert.equal(estado.faixa, 'sem-dado', 'o número estadual não vira faixa')
  assert.equal(estado.faixaEstadual, null)
})

test('com faixa estadual publicada, a linha diz que há faixa', () => {
  assert.equal((situacao('ibirama', [], [bruto('ibirama', 'atencao')]).linha as { comFaixa: boolean }).comFaixa, true)
})

test('estadual velha e sem nada: sem leitura', () => {
  assert.deepEqual(situacao('ilhota', [], [bruto('ilhota', null, '2026-10-03T17:00:00')]).linha, { tipo: 'sem-leitura' })
  assert.deepEqual(situacao('ilhota', [], []).linha, { tipo: 'sem-leitura' })
})

test('municipal de agora manda; municipal velha deixa a estadual aparecer', () => {
  assert.equal(situacao('taio', [leitura('taio', '2026-10-03T21:20:00')], [bruto('taio', null)]).linha.tipo, 'municipal')
  assert.equal(situacao('indaial', [leitura('indaial', '2026-09-12T22:00:00')], [bruto('indaial', null)]).linha.tipo, 'estadual')
})

test('a lista e os cartões usam esta função', async () => {
  const { readFileSync } = await import('node:fs')
  for (const arq of ['ListaRio.tsx', 'CartoesDaCidade.tsx']) {
    const fonte = readFileSync(new URL(`../componentes/${arq}`, import.meta.url), 'utf8')
    assert.match(fonte, /situacaoDaLinha\(/, arq)
    assert.match(fonte, /sem faixa publicada/, arq)
  }
})
