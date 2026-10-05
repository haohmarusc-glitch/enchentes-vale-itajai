/**
 * Prova do PILOTO do classificador (docs/PILOTO-CLASSIFICADOR.md):
 *  1. as 34 perguntas antigas pelo caminho da tela com o piloto (barreira → motor →
 *     classificador só quando o motor não entende ou palpita), corrigidas pelo mesmo
 *     corretor da prova do chat;
 *  2. a bateria de perguntas que o motor não entende (`casosClassificador.ts`).
 *
 * Uso (na pasta do repositório):
 *   web/node_modules/.bin/tsx web/ferramentas/prova-classificador.ts --modo gabarito
 *   web/node_modules/.bin/tsx web/ferramentas/prova-classificador.ts --modo api [--modelo claude-haiku-4-5] [--reps 2]
 *
 * Modos: `api` (precisa de ANTHROPIC_API_KEY no ambiente; gasta), `gabarito` (classificador
 * perfeito simulado: confere o executor), `nao-sei` (sempre "não sei") e `falha` (API fora
 * do ar) — estes três sem rede e sem custo.
 *
 * Grava uma linha por chamada em `.claude/hillclimb/classificador/<modo>-<modelo>/results.jsonl`
 * e imprime os critérios do piloto, com custo e tempo por chamada.
 */
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import Anthropic from '@anthropic-ai/sdk'
import { dados } from '../src/chat-local/testes/carregar'
import { pedeAgora } from '../src/chat-local/motor'
import { custoEstimado, type UsoIA } from '../src/chat-ia/nucleo'
import { CONFIANCA_MINIMA_PADRAO, MODELO_CLASSIFICADOR, TEMPO_LIMITE_MS, VERSAO_CLASSIFICADOR, classificar, decidir } from '../src/chat-ia/classificador'
import { CASOS } from '../src/chat-ia/prova/casos'
import { corrigir } from '../src/chat-ia/prova/corrigir'
import { CASOS_CLASSIFICADOR, type CasoClassificador } from '../src/chat-ia/prova/casosClassificador'
import { gabaritoDe, notaClassificacao, respostaComPiloto, type Classificar, type Desfecho } from '../src/chat-ia/prova/provaClassificador'

function arg(nome: string, padrao: string): string {
  const i = process.argv.indexOf(`--${nome}`)
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1]! : padrao
}
const MODO = arg('modo', 'gabarito')
const MODELO = arg('modelo', MODELO_CLASSIFICADOR)
const REPS = Math.max(1, parseInt(arg('reps', '1'), 10) || 1)
const CONCORRENCIA = Math.max(1, parseInt(arg('concorrencia', '4'), 10) || 4)
const CONFIANCA = Number(arg('confianca', String(CONFIANCA_MINIMA_PADRAO)))
const ANO = 2026
const OPC = { confiancaMinima: CONFIANCA, anoAtual: ANO }
if (!['api', 'gabarito', 'nao-sei', 'falha'].includes(MODO)) {
  console.error('--modo api | gabarito | nao-sei | falha')
  process.exit(2)
}
if (MODO === 'api' && !process.env.ANTHROPIC_API_KEY) {
  console.error('Falta ANTHROPIC_API_KEY no ambiente (a chave nunca vai para o repositório).')
  process.exit(2)
}

interface Medida {
  ms: number
  uso: UsoIA | null
  custo: number | null
}
const medidas: Medida[] = []

// ---------------------------------------------------------------- o classificador de cada modo
const porPergunta = new Map(CASOS_CLASSIFICADOR.map((c) => [c.pergunta, c]))
const naoSei = (q: string) => gabaritoDe({ id: '', pergunta: q, grupo: 'fora', espera: { tipo: 'nao_sei' } })
const cliente = MODO === 'api' ? new Anthropic({ maxRetries: 2, timeout: TEMPO_LIMITE_MS }) : null
/** Erros da API por tipo ("401 authentication_error", "tempo"…), para o relatório. */
const erros = new Map<string, number>()
const tipoDoErro = (e: unknown) =>
  e instanceof Anthropic.APIError ? `${e.status ?? '?'} ${e.name}: ${String(e.message).slice(0, 600)}` : e instanceof Error ? e.message.slice(0, 600) : String(e)
let feitas = 0

// Primeira chamada, com folga de tempo: confere a chave e o modelo antes de gastar a prova
// inteira, e deixa o esquema compilado (a API compila um esquema novo na primeira vez, o que
// pode passar dos 6 s do site; depois fica guardado por 24 h).
if (cliente) {
  process.stderr.write('Conferindo a chave e o modelo… ')
  try {
    const aquecer = new Anthropic({ maxRetries: 1, timeout: 60_000 })
    const c = await classificar('Qual foi a maior cheia de Blumenau?', dados, (p) => aquecer.messages.create(p), MODELO, ANO)
    process.stderr.write(`ok (${c.ms} ms, modelo ${c.uso.modelo})\n`)
  } catch (e) {
    process.stderr.write('FALHOU\n')
    console.error(`\nA API recusou: ${tipoDoErro(e)}`)
    if (e instanceof Anthropic.AuthenticationError)
      console.error('Chave recusada. Confira se foi colada inteira (sem espaço nem aspas a mais), se não foi apagada no Console e se esta janela do PowerShell não guardou uma chave antiga em $env:ANTHROPIC_API_KEY.')
    else if (e instanceof Anthropic.PermissionDeniedError) console.error('A chave não tem permissão para este modelo ou workspace.')
    else if (e instanceof Anthropic.NotFoundError) console.error(`Modelo não encontrado: ${MODELO}.`)
    else if (e instanceof Anthropic.BadRequestError && /workspace/i.test(String(e.message)))
      console.error('Chave sem workspace. Crie outra em Console → Settings → API Keys escolhendo um workspace (ex.: Default); a chave do site precisa ser dessa mesma forma.')
    else if (e instanceof Anthropic.RateLimitError) console.error('Limite de uso ou de gasto atingido: veja Settings → Limits no Console.')
    process.exit(1)
  }
}

const classificador: Classificar = async (q) => {
  if (MODO === 'falha') throw new Error('API fora do ar (simulada)')
  if (MODO === 'gabarito') {
    const c = porPergunta.get(q)
    return c ? gabaritoDe(c) : naoSei(q)
  }
  if (MODO === 'nao-sei') return naoSei(q)
  const inicio = Date.now()
  try {
    const c = await classificar(q, dados, (p) => cliente!.messages.create(p), MODELO, ANO)
    medidas.push({ ms: c.ms, uso: c.uso, custo: custoEstimado(c.uso) })
    return c.bruto
  } catch (e) {
    medidas.push({ ms: Date.now() - inicio, uso: null, custo: null })
    const tipo = tipoDoErro(e)
    erros.set(tipo, (erros.get(tipo) ?? 0) + 1)
    throw e
  } finally {
    process.stderr.write(`\r  ${++feitas} chamadas à IA…`)
  }
}

async function emLotes<T, R>(itens: T[], f: (x: T) => Promise<R>): Promise<R[]> {
  const saida: R[] = new Array(itens.length)
  let proximo = 0
  await Promise.all(
    Array.from({ length: Math.min(CONCORRENCIA, itens.length) }, async () => {
      while (proximo < itens.length) {
        const i = proximo++
        saida[i] = await f(itens[i]!)
      }
    }),
  )
  return saida
}

const pct = (a: number, b: number) => (b ? `${Math.round((100 * a) / b)}%` : '—')
const pasta = join(import.meta.dirname, '..', '..', '.claude', 'hillclimb', 'classificador', `${MODO}-${MODO === 'api' ? MODELO : 'sim'}`)
mkdirSync(pasta, { recursive: true })
const linhas: string[] = []

// ---------------------------------------------------------------- 1. as 34 perguntas antigas
const antigas = await emLotes(
  Array.from({ length: REPS }, (_, rep) => CASOS.map((c) => ({ c, rep }))).flat(),
  async ({ c, rep }) => {
    const p = await respostaComPiloto(c.pergunta, dados, classificador, OPC)
    const nota = corrigir(c, p.texto)
    linhas.push(JSON.stringify({ conjunto: '34', id: c.id, rep, pergunta: c.pergunta, classificou: p.classificou, origem: p.origem, decisao: p.decisao, bruto: p.bruto, nota: nota.grade, porque: nota.explanation.acerto, texto: p.texto }))
    return { id: c.id, acerto: nota.grade.acerto, classificou: p.classificou }
  },
)

// ---------------------------------------------------------------- 2. a bateria
const bateria = await emLotes(
  Array.from({ length: REPS }, (_, rep) => CASOS_CLASSIFICADOR.map((c) => ({ c, rep }))).flat(),
  async ({ c, rep }: { c: CasoClassificador; rep: number }) => {
    let desfecho: Desfecho
    let bruto: unknown = null
    let decisao: unknown = null
    if (pedeAgora(c.pergunta)) {
      decisao = { tipo: 'agora', origem: 'barreira' }
      desfecho = c.espera.tipo === 'agora' ? 'certo' : 'nao_respondeu'
    } else {
      try {
        bruto = await classificador(c.pergunta)
        const d = decidir(c.pergunta, bruto, dados, OPC).decisao
        decisao = d
        desfecho = notaClassificacao(c, d).desfecho
      } catch {
        decisao = 'erro'
        desfecho = 'nao_respondeu'
      }
    }
    linhas.push(JSON.stringify({ conjunto: 'bateria', id: c.id, rep, grupo: c.grupo, pergunta: c.pergunta, espera: { ...c.espera, ...('rua' in c.espera && c.espera.rua ? { rua: String(c.espera.rua) } : {}) }, decisao, bruto, desfecho }))
    return { c, desfecho }
  },
)
writeFileSync(join(pasta, 'results.jsonl'), linhas.join('\n') + '\n')

// ---------------------------------------------------------------- relatório
const acertos34 = antigas.filter((x) => x.acerto).length
const total34 = antigas.length
const doGrupo = (g: CasoClassificador['grupo'][]) => bateria.filter((x) => g.includes(x.c.grupo))
const conta = (xs: { desfecho: Desfecho }[], d: Desfecho) => xs.filter((x) => x.desfecho === d).length
const desc = doGrupo(['desconhecida', 'faltou'])
const pres = doGrupo(['presente'])
const fora = doGrupo(['fora'])
const certoDesc = conta(desc, 'certo')
const liberou = conta(pres, 'liberou')
const adivinhou = conta(fora, 'errou') + conta(desc, 'errou')

if (feitas) process.stderr.write('\n')
console.log(`\nProva do classificador — modo ${MODO}${MODO === 'api' ? `, ${MODELO}` : ''}, versão ${VERSAO_CLASSIFICADOR}, confiança mínima ${CONFIANCA}, ${REPS} repetição(ões)`)
console.log(`\n1. 34 perguntas antigas: ${acertos34}/${total34} (${pct(acertos34, total34)}); passaram pelo classificador: ${antigas.filter((x) => x.classificou).length}`)
const falhas34 = [...new Set(antigas.filter((x) => !x.acerto).map((x) => x.id))]
if (falhas34.length) console.log(`   erraram: ${falhas34.join(', ')}`)
console.log('\n2. Bateria do que o motor não entende:')
console.log(`   desconhecidas + faltou: ${certoDesc}/${desc.length} certas (${pct(certoDesc, desc.length)}); erradas ${conta(desc, 'errou')}; "não consegui interpretar" ${conta(desc, 'nao_respondeu')}`)
console.log(`   presente: ${conta(pres, 'certo')}/${pres.length} viraram o aviso; liberadas ${liberou}; "não consegui interpretar" ${conta(pres, 'nao_respondeu')}`)
console.log(`   fora do tema: ${conta(fora, 'certo')}/${fora.length} "não sei"; adivinhou ${conta(fora, 'errou')}`)
// Os graves pelo nome; os "não consegui interpretar" só contados (estão no results.jsonl).
const graves = bateria.filter((x) => x.desfecho === 'errou' || x.desfecho === 'liberou').map((x) => `${x.c.id} (${x.desfecho})`)
if (graves.length) console.log(`   errados: ${[...new Set(graves)].join(', ')}`)

if (MODO === 'api') {
  const ok = medidas.filter((m) => m.uso)
  const ms = ok.map((m) => m.ms).sort((a, b) => a - b)
  const custos = ok.map((m) => m.custo ?? 0)
  const media = (xs: number[]) => (xs.length ? xs.reduce((s, x) => s + x, 0) / xs.length : 0)
  console.log(`\n3. Custo e tempo por chamada (${ok.length} chamadas, ${medidas.length - ok.length} falharam):`)
  console.log(`   tempo: média ${Math.round(media(ms))} ms; p95 ${ms[Math.floor(ms.length * 0.95)] ?? 0} ms; máximo ${ms.at(-1) ?? 0} ms`)
  console.log(`   tokens de entrada (média): ${Math.round(media(ok.map((m) => m.uso!.entrada + m.uso!.cache_lido + m.uso!.cache_criado)))}; de saída: ${Math.round(media(ok.map((m) => m.uso!.saida)))}`)
  console.log(`   custo: média US$ ${media(custos).toFixed(5)}; máximo US$ ${Math.max(0, ...custos).toFixed(5)}; total US$ ${custos.reduce((s, x) => s + x, 0).toFixed(4)}`)
  for (const [tipo, n] of erros) console.log(`   erro da API (${n}×): ${tipo}`)
}

const criterios: [string, boolean][] = [
  [`34 antigas sem perder os 31 acertos (${acertos34 / REPS} por rodada)`, acertos34 / REPS >= 31],
  [`desconhecidas certas ≥ 85% (${pct(certoDesc, desc.length)})`, certoDesc >= 0.85 * desc.length],
  [`zero pergunta do presente liberada (${liberou})`, liberou === 0],
  [`"não sei" em vez de adivinhar fora do tema (${conta(fora, 'errou')} adivinhou)`, conta(fora, 'errou') === 0],
]
console.log('\nCritérios do piloto:')
for (const [nome, passou] of criterios) console.log(`   ${passou ? 'PASSOU' : 'FALHOU'} — ${nome}`)
if (adivinhou) console.log(`   (atenção: ${adivinhou} resposta(s) com intenção ou parâmetro errado — ver results.jsonl)`)
console.log(`\nDetalhe: ${join(pasta, 'results.jsonl')}`)
