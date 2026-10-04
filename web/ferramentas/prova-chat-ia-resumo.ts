/**
 * Resumo da prova do chat com IA: uma linha por modelo (variante), com acerto, margem
 * de erro, custo e tempo, e o acerto por categoria. Lê o que o executor gravou.
 *
 *   web/node_modules/.bin/tsx web/ferramentas/prova-chat-ia-resumo.ts .claude/hillclimb/chat-ia
 *
 * O custo sai dos tokens de cada linha × a tabela de preços de `nucleo.ts` (custoEstimado),
 * pelo modelo que DE FATO respondeu. O valor oficial é o do Console da Anthropic.
 */
import { existsSync, readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { custoEstimado } from '../src/chat-ia/nucleo'

interface Linha {
  prompt_id: string
  rep: number
  tags?: string[]
  model?: string
  status?: string
  latency_s?: number
  tool_calls?: number
  usage?: { input_tokens?: number; output_tokens?: number; cache_read_input_tokens?: number; cache_creation_input_tokens?: number }
  grade: { acerto: number; fatos: number; regras: number }
  meta?: { simulado?: string }
}

const lerJsonl = <T>(p: string): T[] =>
  existsSync(p)
    ? readFileSync(p, 'utf-8')
        .split('\n')
        .filter((l) => l.trim())
        .map((l) => JSON.parse(l) as T)
    : []

const pct = (x: number) => `${Math.round(x * 100)}%`
const media = (xs: number[]) => (xs.length ? xs.reduce((s, x) => s + x, 0) / xs.length : NaN)

const flow = process.argv[2]
if (!flow) {
  console.error('uso: tsx web/ferramentas/prova-chat-ia-resumo.ts .claude/hillclimb/chat-ia')
  process.exit(2)
}

const variantes = readdirSync(flow)
  .filter((d) => /^(baseline|v\d+)$/.test(d) && existsSync(join(flow, d, 'results.jsonl')))
  .sort((a, b) => (a === 'baseline' ? -1 : b === 'baseline' ? 1 : parseInt(a.slice(1)) - parseInt(b.slice(1))))

if (!variantes.length) {
  console.error(`nenhum resultado em ${flow} (rode o executor primeiro)`)
  process.exit(1)
}

console.log('Variante  | Modelo             | Casos | Acerto (±95%) | Fato certo | Regras | Erros | Custo/pergunta | Custo total | Tempo médio')
for (const v of variantes) {
  const linhas = lerJsonl<Linha>(join(flow, v, 'results.jsonl'))
  const erros = lerJsonl<unknown>(join(flow, v, 'errors.jsonl')).length
  const ok = linhas.filter((l) => l.status !== 'truncated')
  const acerto = media(ok.map((l) => l.grade.acerto))
  const margem = ok.length ? 1.96 * Math.sqrt((acerto * (1 - acerto)) / ok.length) : NaN
  const custos = linhas.map((l) =>
    custoEstimado({
      modelo: l.model ?? '',
      rodadas: 0,
      entrada: l.usage?.input_tokens ?? 0,
      cache_criado: l.usage?.cache_creation_input_tokens ?? 0,
      cache_lido: l.usage?.cache_read_input_tokens ?? 0,
      saida: l.usage?.output_tokens ?? 0,
    }),
  )
  const semPreco = custos.filter((c) => c === null).length
  const total = custos.reduce<number>((s, c) => s + (c ?? 0), 0)
  const modelos = [...new Set(linhas.map((l) => l.model ?? '?'))].join(',')
  const simulado = linhas.some((l) => l.meta?.simulado) ? ' (SIMULADO, sem API)' : ''
  console.log(
    [
      v.padEnd(9),
      modelos.padEnd(18),
      String(linhas.length).padStart(5),
      `${pct(acerto)} ± ${Math.round(margem * 100)}`.padStart(13),
      pct(media(ok.map((l) => l.grade.fatos))).padStart(10),
      pct(media(ok.map((l) => l.grade.regras))).padStart(6),
      String(erros).padStart(5),
      `US$ ${(total / Math.max(1, linhas.length)).toFixed(4)}`.padStart(14),
      `US$ ${total.toFixed(2)}`.padStart(11),
      `${media(linhas.map((l) => l.latency_s ?? NaN)).toFixed(1)} s`.padStart(11),
    ].join(' | ') + simulado + (semPreco ? `  [${semPreco} linha(s) de modelo sem preço na tabela]` : ''),
  )
  const truncadas = linhas.length - ok.length
  if (truncadas) console.log(`          ${truncadas} resposta(s) cortada(s) no limite de tokens, fora da média`)
}

console.log('\nAcerto por categoria:')
const categorias = new Map<string, Map<string, number[]>>()
for (const v of variantes)
  for (const l of lerJsonl<Linha>(join(flow, v, 'results.jsonl'))) {
    const cat = l.tags?.[0] ?? '?'
    const porVar = categorias.get(cat) ?? new Map<string, number[]>()
    porVar.set(v, [...(porVar.get(v) ?? []), l.grade.acerto])
    categorias.set(cat, porVar)
  }
console.log('Categoria     | ' + variantes.map((v) => v.padStart(8)).join(' | '))
for (const [cat, porVar] of categorias)
  console.log(cat.padEnd(13) + ' | ' + variantes.map((v) => (porVar.has(v) ? pct(media(porVar.get(v)!)) : '—').padStart(8)).join(' | '))

console.log('\nCasos que falharam (todas as repetições):')
for (const v of variantes) {
  const porCaso = new Map<string, number[]>()
  for (const l of lerJsonl<Linha>(join(flow, v, 'results.jsonl'))) porCaso.set(l.prompt_id, [...(porCaso.get(l.prompt_id) ?? []), l.grade.acerto])
  const falhas = [...porCaso].filter(([, xs]) => xs.every((x) => x === 0)).map(([id]) => id)
  console.log(`  ${v}: ${falhas.length ? falhas.join(', ') : 'nenhum'}`)
}
