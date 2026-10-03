import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import type { LeituraAoVivo } from '../dados/tempoReal'
import type { EstacaoTempoReal } from '../dados/tipos'
import { agruparPorCurso, todasAsReguas } from './reguas'
import { faixaDaRegua, reguasAgora } from './reguasAgora'
import { deBrasilia } from './tempoReal'

const AGORA = deBrasilia('2026-10-03T15:00:00')
const DC01 = 'DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL'
const DC10 = 'DC-10 Rio Itajaí-Mirim – Bairro Limoeiro'

function leitura(estacao: string, nivel: number, iso = '2026-10-03T14:45:00', resgateDe: string | null = null): LeituraAoVivo {
  return { estacao, rio: null, cidade: 'itajai', nivel_m: nivel, medidoEm: deBrasilia(iso), resgateDe }
}

// O cadastro direto do disco: o alias `@dados` só existe no Vite.
const estacoesTempoReal: EstacaoTempoReal[] =
  JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8')).estacoes_tempo_real ?? []
const reguas = todasAsReguas(estacoesTempoReal, 'itajai')
const regua = (titulo: string) => reguas.find((r) => r.titulo === titulo)!

test('Itajaí mostra as réguas dos dois rios e dos ribeirões, não só as do Açu', () => {
  const cursos = agruparPorCurso(reguas).map((g) => g.rio)
  assert.deepEqual(cursos, ['itajai-acu', 'itajai-mirim', 'ribeirao-murta', 'ribeirao-canhanduba'])
  assert.equal(reguas.length, 11)
})

test('a faixa de cada régua sai das cotas DELA: o mesmo número é normal numa e emergência noutra', () => {
  // 1,60 m: acima da emergência da DC-01 (1,56) e muito abaixo da atenção da DC-10 (8,00).
  assert.equal(faixaDaRegua(regua(DC01), leitura(DC01, 1.6), 'itajai', AGORA), 'emergencia')
  assert.equal(faixaDaRegua(regua(DC10), leitura(DC10, 1.6), 'itajai', AGORA), 'normal')
})

test('leitura velha ou ausente fica cinza, nunca verde', () => {
  assert.equal(faixaDaRegua(regua(DC10), leitura(DC10, 3, '2026-10-03T09:00:00'), 'itajai', AGORA), 'sem-dado')
  assert.equal(faixaDaRegua(regua(DC10), null, 'itajai', AGORA), 'sem-dado')
})

test('cada régua pega a SUA leitura mais recente, e a próxima cota com quanto falta', () => {
  const r = reguasAgora(
    [regua(DC01), regua(DC10)],
    [leitura(DC10, 6.0, '2026-10-03T14:00:00'), leitura(DC10, 6.5, '2026-10-03T14:45:00'), leitura(DC01, 1.0)],
    'itajai',
    AGORA,
  )
  assert.equal(r[1]!.leitura!.nivel_m, 6.5)
  assert.equal(r[1]!.proxima!.chave, 'atencao')
  assert.ok(Math.abs(r[1]!.proxima!.faltam - 1.5) < 1e-9)
  assert.equal(r[0]!.leitura!.nivel_m, 1.0)
})

test('régua sem leitura continua na lista, sem número e sem cor', () => {
  const [r] = reguasAgora([regua(DC10)], [], 'itajai', AGORA)
  assert.equal(r!.leitura, null)
  assert.equal(r!.faixa, 'sem-dado')
  assert.equal(r!.proxima, null)
})
