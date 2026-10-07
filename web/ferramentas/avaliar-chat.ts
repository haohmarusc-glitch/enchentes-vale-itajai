/**
 * Roda a bateria de avaliação do chat e grava os relatórios (17ª entrega — PR 1 do handoff de qualidade):
 *
 *     npm run avaliar               → docs/AVALIACAO-CHAT.md e docs/CHAT-CAPACIDADES.md
 *     npm run avaliar -- --baseline → também regrava src/comandos/avaliacao/baseline.json
 *
 * A linha de base só muda de propósito (a bandeira), para ninguém baixá-la sem querer; o teste
 * `avaliacao.test.ts` compara com ela e reprova queda. Conferir o diff dos três arquivos antes de commitar.
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { avaliar, baselineDe, relatorio, type Baseline } from '../src/comandos/avaliacao/avaliar'
import { textoDoCatalogo } from '../src/comandos/capacidades'

const RAIZ = new URL('../../', import.meta.url).pathname
const BASELINE = `${RAIZ}web/src/comandos/avaliacao/baseline.json`
const hoje = new Date().toISOString().slice(0, 10)

const a = await avaliar()
const anterior: Baseline | null = existsSync(BASELINE) ? JSON.parse(readFileSync(BASELINE, 'utf8')) : null
writeFileSync(`${RAIZ}docs/AVALIACAO-CHAT.md`, relatorio(a, anterior, hoje))
writeFileSync(`${RAIZ}docs/CHAT-CAPACIDADES.md`, textoDoCatalogo())
if (process.argv.includes('--baseline')) writeFileSync(BASELINE, JSON.stringify(baselineDe(a.metricas, hoje), null, 2) + '\n')

const m = a.metricas
console.log(`${m.acertos}/${m.total} acertos · dev ${m.porConjunto.dev.acertos}/${m.porConjunto.dev.total} · reservado ${m.porConjunto.reservado.acertos}/${m.porConjunto.reservado.total} · ações indevidas ${m.acoesIndevidas} · palpites ${m.palpites} · latência ${m.latenciaMs.mediana} ms (p95 ${m.latenciaMs.p95} ms)`)
for (const [g, c] of Object.entries(m.porGrupo)) console.log(`  ${g}: ${c.acertos}/${c.total}`)
if (process.argv.includes('--falhas')) for (const r of a.resultados.filter((r) => !r.ok)) console.log(`✗ [${r.grupo}] "${r.texto}" (${r.contexto}) esperado ${r.esperado} → ${r.obtido}`)
