import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { montarClassificacao } from '../dados/classificacao'
import { montarNivelSc } from '../dados/nivelSc'
import { buscarTempoReal } from '../dados/tempoReal'
import type { Cidade } from '../dados/tipos'
import { estadoDaCidade, type AoVivo } from '../dados/usarAoVivo'
import { deBrasilia } from './tempoReal'

// --- Contrato com o motor de classificação (Python) ------------------------------------------------
//
// `data/classificacao-esperada.json` é o gabarito da classificação estadual × municipal (PR 1, 07/10/2026).
// `scripts/teste_classificar_reguas.py` exige que o motor Python dê o `esperado` de cada caso; este teste
// exige que o site de HOJE dê o `site` — pelos mesmos caminhos que a tela usa (o parser do `ultimo.json`,
// o do `ultimo_nivel_sc.json` e o `estadoDaCidade`). Sem `diverge_do_site`, o Python cobra que as duas
// respostas pintem igual.
//
// Vermelho aqui = o site mudou a regra da cor. Se foi de propósito, o gabarito e o motor mudam junto.
//
// PR 2 (07/10/2026): o site passou a seguir o motor quando recebe o `ultimo_classificacao.json` desta
// coleta. O segundo teste dá a cada caso a saída do motor guardada em `motor` (regerada por
// `classificar_reguas.py --gabarito`, e o teste Python cobra que esteja em dia) e exige o `esperado`.

interface Caso {
  id: string
  agora_brasilia: string
  cidade: string
  leituras: unknown[]
  nivel_sc: unknown
  site: { faixa: string; faixaEstadual: string | null }
  esperado: { aplicada: { tipo: 'municipal' | 'estadual' | 'nenhuma'; faixa: string | null } }
  motor: { cidades: Record<string, { classificacoes: { municipal: { varias_reguas: boolean } } }> }
}

const gabarito = JSON.parse(
  readFileSync(new URL('../../../data/classificacao-esperada.json', import.meta.url), 'utf8'),
) as { casos: Caso[] }
const estacoes = JSON.parse(
  readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'),
) as { rios: Record<string, { cidades: Cidade[] }> }

function cidadeDoPiloto(id: string): { cidade: Cidade; rio: string } {
  const achadas = Object.entries(estacoes.rios).flatMap(([rio, r]) =>
    r.cidades.filter((c) => c.id === id).map((cidade) => ({ cidade, rio })),
  )
  assert.equal(achadas.length, 1, `${id} precisa estar uma vez só no estacoes.json`)
  return achadas[0]!
}

async function aoVivoDoCaso(caso: Caso, comMotor: boolean): Promise<AoVivo> {
  const corpo = { coletado_em: '2026-10-07T16:05:00+00:00', leituras: caso.leituras }
  const tempoReal = await buscarTempoReal(undefined, async () => new Response(JSON.stringify(corpo), { status: 200 }))
  return {
    tempoReal,
    nivelSc: montarNivelSc(caso.nivel_sc),
    serie: { series: {} } as unknown as AoVivo['serie'],
    agora: deBrasilia(caso.agora_brasilia),
    classificacao: comMotor ? montarClassificacao(caso.motor) : null,
  }
}

test('sem o arquivo do motor, o site dá o lado `site` do gabarito (a regra de sempre)', async () => {
  assert.ok(gabarito.casos.length >= 15, 'gabarito pequeno demais para provar algo')
  const divergentes: string[] = []
  for (const caso of gabarito.casos) {
    const { cidade, rio } = cidadeDoPiloto(caso.cidade)
    const e = estadoDaCidade(cidade, rio, await aoVivoDoCaso(caso, false))
    assert.equal(e.classificadaPor, 'site', caso.id)
    const obtido = { faixa: e.faixa, faixaEstadual: e.faixaEstadual }
    if (JSON.stringify(obtido) !== JSON.stringify(caso.site)) {
      divergentes.push(`${caso.id}: esperado ${JSON.stringify(caso.site)}, o site deu ${JSON.stringify(obtido)}`)
    }
  }
  assert.deepEqual(divergentes, [])
})

test('com o arquivo do motor desta coleta, o site pinta o `esperado` — inclusive na divergência declarada', async () => {
  const divergentes: string[] = []
  for (const caso of gabarito.casos) {
    const { cidade, rio } = cidadeDoPiloto(caso.cidade)
    const e = estadoDaCidade(cidade, rio, await aoVivoDoCaso(caso, true))
    if (e.classificadaPor !== 'motor') {
      divergentes.push(`${caso.id}: o site não usou o motor`)
      continue
    }
    const ap = caso.esperado.aplicada
    const varias = caso.motor.cidades[caso.cidade]!.classificacoes.municipal.varias_reguas
    const esperado =
      ap.tipo === 'municipal' ? { faixa: ap.faixa, faixaEstadual: null, origem: 'municipal' }
      : ap.tipo === 'estadual' ? { faixa: 'sem-dado', faixaEstadual: ap.faixa, origem: 'estadual' }
      : { faixa: varias ? 'varias' : 'sem-dado', faixaEstadual: null, origem: null }
    const obtido = { faixa: e.faixa, faixaEstadual: e.faixaEstadual, origem: e.origemDaCor?.tipo ?? null }
    if (JSON.stringify(obtido) !== JSON.stringify(esperado)) {
      divergentes.push(`${caso.id}: esperado ${JSON.stringify(esperado)}, o site deu ${JSON.stringify(obtido)}`)
    }
  }
  assert.deepEqual(divergentes, [])
})
