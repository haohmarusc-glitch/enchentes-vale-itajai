/**
 * O avaliador da bateria (17ª entrega — PR 1 do handoff de qualidade do chat).
 *
 * Roda cada caso de `casos.ts` pelo MESMO caminho da tela (`ChatLocal.tsx`): primeiro a continuação da conversa
 * (`continuar`), depois o leitor de pedidos (`interpretar`), e o que não é pedido vai ao motor de perguntas
 * (`responder`). Os casos de execução rodam o executor de verdade num cenário congelado. Nada de rede, nada de
 * relógio de parede: os números são reproduzíveis, e é isso que permite a linha de base (`baseline.json`) e o
 * teste que impede a queda.
 *
 * Métricas, como o handoff pede: intenção correta, argumentos corretos, esclarecimentos adequados e
 * desnecessários, ações indevidas (a tela mudou quando não devia), respostas por palpite, latência (mediana e p95
 * do leitor + motor, em ms). Uma ação indevida é defeito, não estatística: o teste trava em zero.
 */
import { performance } from 'node:perf_hooks'
import { catalogoDoCadastro } from '../catalogo'
import { interpretar } from '../interpretar'
import { continuar } from '../continuar'
import { executar, limparRetratos, MUDA_A_TELA } from '../executar'
import { textoDeAjuda } from '../ajuda'
import { responder, type Dados } from '../../chat-local/motor'
import type { Contexto, Interpretacao, Passo } from '../tipos'
import { CASOS, GRUPOS, type Caso, type Conjunto, type Esperado, type Grupo } from './casos'
import { CENARIOS, aoVivoComNivelImpossivel, cenario, estacoes, type Cenario, type NomeDoCenario } from './cenarios'

export interface Resultado {
  id: string
  grupo: Grupo
  conjunto: Conjunto
  texto: string
  contexto: string
  esperado: string
  obtido: string
  ok: boolean
  /** A tela mudaria (passo de `MUDA_A_TELA`) sem o caso esperar isso. */
  acaoIndevida: boolean
  /** O motor respondeu por palpite (achou só cidade ou só ano). */
  palpite: boolean
  /** Esperava-se agir e o leitor pediu esclarecimento. */
  esclarecimentoDesnecessario: boolean
  /** Esperava-se esclarecer/perguntar e o sistema agiu ou respondeu. */
  esclarecimentoFaltou: boolean
  ms: number
  nota?: string
}

export interface Contagem { total: number; acertos: number }

export interface Metricas {
  total: number
  acertos: number
  porGrupo: Record<Grupo, Contagem>
  porConjunto: Record<Conjunto, Contagem>
  /** O tipo de desfecho certo (comando/esclarecer/motor), sem olhar argumentos. */
  intencaoCorreta: Contagem
  /** Só os casos de comando com argumentos declarados. */
  argumentosCorretos: Contagem
  esclarecimentos: { adequados: number; desnecessarios: number; faltaram: number }
  acoesIndevidas: number
  palpites: number
  latenciaMs: { mediana: number; p95: number }
}

const CONTEXTO_PADRAO: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const contextoDe = (c: Caso): Contexto => ({ ...CONTEXTO_PADRAO, ...(c.contexto ?? {}) })
const rotuloDoContexto = (c: Caso) => (c.contexto?.naMonitor ? `Monitor${c.contexto.cidadeAtual ? ` de ${c.contexto.cidadeAtual}` : ''}` : c.contexto?.cidadeAtual ? `página de ${c.contexto.cidadeAtual}` : 'fora')

function descreverEsperado(e: Esperado): string {
  switch (e.tipo) {
    case 'comando': return `comando ${e.passo}${e.args ? ' ' + JSON.stringify(e.args) : ''}`
    case 'comandos': return `comandos ${e.passos.join(' → ')}`
    case 'esclarecer': return 'esclarecer'
    case 'pergunta': return 'perguntar (esclarecer ou "não entendi")'
    case 'motor': return `motor ${e.intencao}`
    case 'continuacao': return `continuação ${e.troca}: "${e.texto}"`
    case 'continuacao_pergunta': return 'continuação: perguntar'
    case 'execucao': return `execução [${e.cenario}] ${e.contem.map(String).join(' ')}${e.naoContem?.length ? ' sem ' + e.naoContem.map(String).join(' ') : ''}${e.navega ? ' (navega)' : ''}`
  }
}

/** `args` esperados são subconjunto do passo; `null` esperado aceita `null` ou ausente. */
function argumentosBatem(passo: Passo, args: Record<string, unknown>): boolean {
  const p = passo as unknown as Record<string, unknown>
  return Object.entries(args).every(([k, v]) => (v === null ? p[k] == null : JSON.stringify(p[k]) === JSON.stringify(v)))
}

const mudaATela = (passos: Passo[]) => passos.some((p) => MUDA_A_TELA.has(p.tipo))

type Desfecho =
  | { via: 'continuacao'; texto: string; troca: string }
  | { via: 'continuacao_pergunta'; erro: string }
  | { via: 'comandos'; passos: Passo[] }
  | { via: 'esclarecer'; texto: string }
  | { via: 'motor'; intencao: string; palpite: boolean; falha?: string }

function descreverDesfecho(d: Desfecho): string {
  switch (d.via) {
    case 'continuacao': return `continuação ${d.troca}: "${d.texto}"`
    case 'continuacao_pergunta': return `continuação: perguntou ("${d.erro.slice(0, 60)}…")`
    case 'comandos': return d.passos.length === 1 ? `comando ${JSON.stringify(d.passos[0])}` : `comandos ${d.passos.map((p) => p.tipo).join(' → ')}`
    case 'esclarecer': return `esclarecer ("${d.texto.slice(0, 70)}")`
    case 'motor': return `motor ${d.intencao}${d.falha ? ` (${d.falha})` : ''}${d.palpite ? ' (palpite)' : ''}`
  }
}

/** O caminho da tela: continuação → leitor → motor. */
function decidir(c: Caso, ctx: Contexto, cat: ReturnType<typeof catalogoDoCadastro>, dados: Dados): Desfecho {
  if (c.anterior !== undefined) {
    const k = continuar(c.texto, c.anterior, cat.cidades)
    if (k && 'erro' in k) return { via: 'continuacao_pergunta', erro: k.erro }
    if (k) return { via: 'continuacao', texto: k.texto, troca: k.troca }
  }
  const r: Interpretacao | null = interpretar(c.texto, cat, ctx)
  if (r?.tipo === 'comandos') return { via: 'comandos', passos: r.passos }
  if (r?.tipo === 'esclarecer') return { via: 'esclarecer', texto: r.texto }
  const m = responder(c.texto, dados)
  return { via: 'motor', intencao: m.intencao, palpite: m.palpite === true, falha: m.falha?.motivo }
}

const PERGUNTOU_NO_MOTOR = new Set(['nao_entendi', 'ajuda'])

function julgar(e: Esperado, d: Desfecho): { ok: boolean; intencao: boolean; args: boolean | null } {
  switch (e.tipo) {
    case 'comando': {
      const intencao = d.via === 'comandos' && d.passos.length === 1 && d.passos[0]!.tipo === e.passo
      const args = intencao && e.args ? argumentosBatem((d as { passos: Passo[] }).passos[0]!, e.args) : null
      return { ok: intencao && args !== false, intencao, args }
    }
    case 'comandos': {
      const intencao = d.via === 'comandos' && d.passos.map((p) => p.tipo).join(',') === e.passos.join(',')
      return { ok: intencao, intencao, args: null }
    }
    case 'esclarecer': return { ok: d.via === 'esclarecer', intencao: d.via === 'esclarecer', args: null }
    case 'pergunta': {
      const ok = d.via === 'esclarecer' || d.via === 'continuacao_pergunta' || (d.via === 'motor' && PERGUNTOU_NO_MOTOR.has(d.intencao) && !d.palpite)
      return { ok, intencao: ok, args: null }
    }
    case 'motor': {
      const ok = d.via === 'motor' && d.intencao === e.intencao
      return { ok, intencao: ok, args: null }
    }
    case 'continuacao': {
      const ok = d.via === 'continuacao' && d.texto === e.texto && d.troca === e.troca
      return { ok, intencao: d.via === 'continuacao', args: ok ? true : d.via === 'continuacao' ? false : null }
    }
    case 'continuacao_pergunta': return { ok: d.via === 'continuacao_pergunta', intencao: d.via === 'continuacao_pergunta', args: null }
    case 'execucao': return { ok: false, intencao: false, args: null } // julgado à parte
  }
}

async function cenarioDe(nome: NomeDoCenario | 'impossivel'): Promise<Cenario> {
  if (nome === 'impossivel') return cenario({ aoVivo: await aoVivoComNivelImpossivel() })
  return CENARIOS[nome]()
}

const esperaAgir = (e: Esperado) => e.tipo === 'comando' || e.tipo === 'comandos' || (e.tipo === 'execucao' && e.navega === true)
const esperaPerguntar = (e: Esperado) => e.tipo === 'esclarecer' || e.tipo === 'pergunta' || e.tipo === 'continuacao_pergunta'

export interface Avaliacao { resultados: Resultado[]; metricas: Metricas }

export async function avaliar(casos: Caso[] = CASOS, dados?: Dados): Promise<Avaliacao> {
  const cat = catalogoDoCadastro(estacoes)
  const motorDados = dados ?? (await import('../../chat-local/testes/carregar')).dados
  const resultados: Resultado[] = []
  for (const c of casos) {
    const ctx = contextoDe(c)
    const base = { id: c.id, grupo: c.grupo, conjunto: c.conjunto, texto: c.texto, contexto: rotuloDoContexto(c), esperado: descreverEsperado(c.esperado), nota: c.nota }
    const t0 = performance.now()
    if (c.esperado.tipo === 'execucao') {
      limparRetratos()
      const e = c.esperado
      const cen = await cenarioDe(e.cenario)
      const r = interpretar(c.texto, cat, ctx)
      if (!r || r.tipo !== 'comandos') {
        resultados.push({ ...base, obtido: `não virou comando: ${r ? descreverDesfecho({ via: 'esclarecer', texto: r.texto }) : 'motor'}`, ok: false, acaoIndevida: false, palpite: false, esclarecimentoDesnecessario: r?.tipo === 'esclarecer', esclarecimentoFaltou: false, ms: performance.now() - t0 })
        continue
      }
      const saida = await executar(r.passos, cen.amb, cat, ctx, () => textoDeAjuda(ctx, null))
      const ms = performance.now() - t0
      const faltou = e.contem.filter((re) => !re.test(saida.texto))
      const sobrou = (e.naoContem ?? []).filter((re) => re.test(saida.texto))
      const navegou = cen.navegacoes.length > 0
      const ok = faltou.length === 0 && sobrou.length === 0 && navegou === (e.navega === true)
      const problemas = [...faltou.map((re) => `faltou ${re}`), ...sobrou.map((re) => `sobrou ${re}`), ...(navegou !== (e.navega === true) ? [navegou ? `navegou ${cen.navegacoes.join(', ')}` : 'não navegou'] : [])]
      resultados.push({ ...base, obtido: `${problemas.length ? problemas.join('; ') + ' — ' : ''}"${saida.texto.replace(/\s+/g, ' ').slice(0, 160)}"`, ok, acaoIndevida: navegou && e.navega !== true, palpite: false, esclarecimentoDesnecessario: false, esclarecimentoFaltou: false, ms })
      continue
    }
    const d = decidir(c, ctx, cat, motorDados)
    const ms = performance.now() - t0
    const j = julgar(c.esperado, d)
    const agiu = d.via === 'comandos' && mudaATela(d.passos)
    resultados.push({
      ...base,
      obtido: descreverDesfecho(d),
      ok: j.ok,
      acaoIndevida: agiu && (!esperaAgir(c.esperado) || !j.intencao),
      palpite: d.via === 'motor' && d.palpite,
      esclarecimentoDesnecessario: esperaAgir(c.esperado) && (d.via === 'esclarecer' || d.via === 'continuacao_pergunta'),
      esclarecimentoFaltou: esperaPerguntar(c.esperado) && !j.ok,
      ms,
    })
  }
  return { resultados, metricas: medir(resultados, casos) }
}

function medir(rs: Resultado[], casos: Caso[]): Metricas {
  const contagem = (lista: Resultado[]): Contagem => ({ total: lista.length, acertos: lista.filter((r) => r.ok).length })
  const porGrupo = Object.fromEntries((Object.keys(GRUPOS) as Grupo[]).map((g) => [g, contagem(rs.filter((r) => r.grupo === g))])) as Record<Grupo, Contagem>
  const porConjunto = { dev: contagem(rs.filter((r) => r.conjunto === 'dev')), reservado: contagem(rs.filter((r) => r.conjunto === 'reservado')) }
  const esperadoDe = new Map(casos.map((c) => [c.id, c.esperado]))
  const deLeitura = rs.filter((r) => esperadoDe.get(r.id)!.tipo !== 'execucao')
  const comArgs = rs.filter((r) => { const e = esperadoDe.get(r.id)!; return (e.tipo === 'comando' && e.args) || e.tipo === 'continuacao' })
  // Intenção certa = o desfecho certo, mesmo com argumento errado: aproxima pelo texto do obtido.
  const intencaoCorreta = { total: deLeitura.length, acertos: deLeitura.filter((r) => r.ok || (r.obtido.startsWith('comando') && r.esperado.startsWith('comando') && r.obtido.includes(`"tipo":"${r.esperado.split(' ')[1]}"`))).length }
  const esperavaPerguntar = rs.filter((r) => esperaPerguntar(esperadoDe.get(r.id)!))
  const tempos = rs.map((r) => r.ms).sort((a, b) => a - b)
  const q = (p: number) => (tempos.length ? Math.round(tempos[Math.min(tempos.length - 1, Math.floor(p * tempos.length))]! * 100) / 100 : 0)
  return {
    total: rs.length,
    acertos: rs.filter((r) => r.ok).length,
    porGrupo,
    porConjunto,
    intencaoCorreta,
    argumentosCorretos: contagem(comArgs),
    esclarecimentos: { adequados: esperavaPerguntar.filter((r) => r.ok).length, desnecessarios: rs.filter((r) => r.esclarecimentoDesnecessario).length, faltaram: rs.filter((r) => r.esclarecimentoFaltou).length },
    acoesIndevidas: rs.filter((r) => r.acaoIndevida).length,
    palpites: rs.filter((r) => r.palpite).length,
    latenciaMs: { mediana: q(0.5), p95: q(0.95) },
  }
}

/** A linha de base guardada em `baseline.json`: só o que o teste compara (nada de latência, que varia por máquina). */
export interface Baseline {
  geradoEm: string
  total: number
  acertos: number
  porGrupo: Record<Grupo, Contagem>
  porConjunto: Record<Conjunto, Contagem>
  acoesIndevidas: number
  palpites: number
}

export const baselineDe = (m: Metricas, geradoEm = '2026-10-07'): Baseline => ({ geradoEm, total: m.total, acertos: m.acertos, porGrupo: m.porGrupo, porConjunto: m.porConjunto, acoesIndevidas: m.acoesIndevidas, palpites: m.palpites })

const pct = (c: Contagem) => (c.total ? `${Math.round((100 * c.acertos) / c.total)} %` : '—')
const linha = (c: Contagem) => `${c.acertos}/${c.total} (${pct(c)})`

/** O relatório em Markdown (`docs/AVALIACAO-CHAT.md`). */
export function relatorio(a: Avaliacao, anterior: Baseline | null, geradoEm = new Date().toISOString().slice(0, 10)): string {
  const m = a.metricas
  const L: string[] = [
    '# Avaliação do chat — bateria e linha de base',
    '',
    `Gerado por \`npm run avaliar\` em ${geradoEm}, de \`web/src/comandos/avaliacao/\` (não editar à mão). O que cada caso espera é o`,
    'comportamento certo pelas regras do projeto, não o que o sistema faz hoje: caso reprovado é achado, e a lista deles',
    'é o diagnóstico. O teste `avaliacao.test.ts` trava: zero ações indevidas, conjunto `dev` em 100 % e nenhum grupo',
    'abaixo da linha de base (`baseline.json`).',
    '',
    '## Números',
    '',
    '| Métrica | Valor |',
    '|---|---|',
    `| Casos | ${m.total} (${m.porConjunto.dev.total} dev · ${m.porConjunto.reservado.total} reservados) |`,
    `| Acertos | ${linha({ total: m.total, acertos: m.acertos })} |`,
    `| Conjunto dev (exemplos do catálogo) | ${linha(m.porConjunto.dev)} |`,
    `| Conjunto reservado (frases novas) | ${linha(m.porConjunto.reservado)} |`,
    `| Intenção correta (casos de leitura) | ${linha(m.intencaoCorreta)} |`,
    `| Argumentos corretos (casos com argumentos) | ${linha(m.argumentosCorretos)} |`,
    `| Esclarecimentos adequados | ${m.esclarecimentos.adequados} |`,
    `| Esclarecimentos desnecessários | ${m.esclarecimentos.desnecessarios} |`,
    `| Esclarecimentos que faltaram (agiu ou respondeu quando devia perguntar) | ${m.esclarecimentos.faltaram} |`,
    `| **Ações indevidas** (a tela mudaria sem o caso esperar) | **${m.acoesIndevidas}** |`,
    `| Respostas por palpite do motor | ${m.palpites} |`,
    `| Latência do leitor + motor (mediana · p95) | ${m.latenciaMs.mediana} ms · ${m.latenciaMs.p95} ms |`,
    '',
    '## Por grupo',
    '',
    '| Grupo | Acertos | Linha de base anterior |',
    '|---|---|---|',
  ]
  for (const g of Object.keys(GRUPOS) as Grupo[]) L.push(`| ${GRUPOS[g]} | ${linha(m.porGrupo[g])} | ${anterior ? linha(anterior.porGrupo[g]) : '—'} |`)
  L.push('', '## Casos reprovados (o diagnóstico)', '')
  for (const g of Object.keys(GRUPOS) as Grupo[]) {
    const falhas = a.resultados.filter((r) => r.grupo === g && !r.ok)
    if (!falhas.length) continue
    L.push(`### ${GRUPOS[g]} — ${falhas.length}`, '', '| Pedido | Contexto | Esperado | Obtido | Nota |', '|---|---|---|---|---|')
    for (const r of falhas) L.push(`| ${cel(r.texto)} | ${r.contexto} | ${cel(r.esperado)} | ${cel(r.obtido)} | ${cel(r.nota ?? '')} |`)
    L.push('')
  }
  const indevidas = a.resultados.filter((r) => r.acaoIndevida)
  L.push('## Ações indevidas', '', indevidas.length ? indevidas.map((r) => `- "${r.texto}" → ${r.obtido}`).join('\n') : 'Nenhuma.', '')
  return L.join('\n')
}

const cel = (s: string) => s.replace(/\|/g, '\\|').replace(/\n/g, ' ').replace(/`/g, "'").slice(0, 220)
