/**
 * 17ª entrega dos comandos do chat (PR 1 do handoff de qualidade): a bateria de avaliação como trava.
 *
 *  - zero ações indevidas (a tela nunca muda quando o caso não espera isso);
 *  - o conjunto `dev` (exemplos do catálogo) em 100 %;
 *  - nenhum grupo abaixo da linha de base (`baseline.json`), e o total também não — o número só anda para cima.
 *    Subiu? Regrave a linha de base com `npm run avaliar -- --baseline` e commite o diff junto.
 *  - as regras de dado que os casos de execução travam continuam valendo (leitura velha, nível impossível, Itajaí).
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { avaliar, type Baseline } from './avaliar'
import { CASOS, GRUPOS, type Grupo } from './casos'

const baseline: Baseline = JSON.parse(readFileSync(new URL('./baseline.json', import.meta.url), 'utf8'))
const avaliacao = await avaliar()
const { metricas: m, resultados } = avaliacao

test('a bateria tem os sete grupos, ids únicos e pelo menos 300 casos', () => {
  const ids = new Set(CASOS.map((c) => c.id))
  assert.equal(ids.size, CASOS.length, 'id repetido')
  assert.ok(CASOS.length >= 300, `${CASOS.length} casos`)
  for (const g of Object.keys(GRUPOS) as Grupo[]) assert.ok(m.porGrupo[g].total >= 30, `${g}: ${m.porGrupo[g].total} casos`)
})

test('zero ações indevidas: nenhum caso muda a tela sem esperar isso', () => {
  const indevidas = resultados.filter((r) => r.acaoIndevida)
  assert.deepEqual(indevidas.map((r) => `${r.texto} → ${r.obtido}`), [])
  assert.equal(m.acoesIndevidas, 0)
})

test('conjunto dev (exemplos do catálogo) em 100 %', () => {
  const falhas = resultados.filter((r) => r.conjunto === 'dev' && !r.ok)
  assert.deepEqual(falhas.map((r) => `${r.texto} (${r.contexto}) → ${r.obtido}`), [])
})

test('nenhum grupo abaixo da linha de base; o total também não', () => {
  for (const g of Object.keys(GRUPOS) as Grupo[]) {
    assert.ok(m.porGrupo[g].acertos >= baseline.porGrupo[g].acertos, `${g}: ${m.porGrupo[g].acertos} < linha de base ${baseline.porGrupo[g].acertos}`)
  }
  assert.ok(m.acertos >= baseline.acertos, `${m.acertos} < ${baseline.acertos}`)
  assert.ok(m.palpites <= baseline.palpites, `palpites ${m.palpites} > ${baseline.palpites}`)
  // Caso novo sem atualizar a linha de base é esquecimento: o total registrado tem de ser o de hoje.
  assert.equal(m.total, baseline.total, 'a bateria mudou de tamanho: regrave a linha de base (npm run avaliar -- --baseline)')
})

test('as regras de dado dos cenários congelados valem todas (atualidade 100 % no que já passa; nunca número de leitura velha ou impossível)', () => {
  const atual = resultados.filter((r) => r.grupo === 'atualidade')
  // Achados conhecidos ficariam listados aqui de propósito (sair da lista exige corrigir o executor, não o caso). Hoje: nenhum.
  const achados = new Set<string>()
  for (const r of atual) if (!achados.has(r.texto)) assert.ok(r.ok, `${r.texto} [${r.esperado}] → ${r.obtido}`)
  // Em nenhum caso de execução o nível impossível (30 m / −0,5 m) ou a leitura velha aparece como número de agora.
  for (const r of resultados.filter((r) => r.esperado.startsWith('execução [impossivel]') || r.esperado.startsWith('execução [velha]'))) {
    assert.doesNotMatch(r.obtido, /30,00 m|-0,50 m/, r.texto)
  }
})
