/**
 * O lado do aparelho do PILOTO do classificador (docs/PILOTO-CLASSIFICADOR.md).
 *
 * Só entra quando o chat sem IA não entendeu a pergunta, ou só palpitou. O servidor
 * devolve uma classificação conferida; a resposta sai do motor, aqui no aparelho. Se o
 * servidor demorar ou falhar, a tela diz "não consegui interpretar" e o chat sem IA
 * segue igual. Sem rede no módulo: o `fetch` vem de fora (teste em
 * `clienteClassificador.test.ts`).
 */
import {
  EXEMPLOS,
  INTENCOES,
  TEXTO_ALERTA,
  descreverEntendido,
  responderPorIntencao,
  textoParametros,
  type Classificacao,
  type Dados,
  type Intencao,
  type Parametro,
} from '../chat-local/motor'
import type { Decisao } from './classificador'

export const URL_CLASSIFICAR = '/api/chat-classificar'
/** O servidor desiste da IA em 6 s; o aparelho, em 8 s (rede de celular na chuva). */
export const TEMPO_LIMITE_APARELHO_MS = 8_000

type Buscar = (url: string, init?: RequestInit) => Promise<Response>

export type Origem = 'nao_entendi' | 'palpite'
export type Correcao = 'correto' | 'nao_era_isso'
export type Classificado = { id: string | null; decisao: Decisao } | { erro: true }

export const AVISO_PILOTO =
  'Piloto: quando o chat não entende uma pergunta, o texto dela vai à Anthropic (empresa da IA Claude) só para ser classificado — a resposta continua saindo dos dados do site. O site guarda por 90 dias o texto da pergunta (sem e-mail, telefone ou número de casa), como ela foi classificada e o botão que você apertar, sem o seu e-mail. Não escreva nome, endereço ou telefone.'

export const TEXTO_NAO_INTERPRETEI = 'Não consegui interpretar a pergunta.'
const TEXTO_ESCOPO = 'Eu respondo só sobre o histórico das cheias e enchentes do Vale do Itajaí, usando os dados do site. Tente um destes formatos:'
export const TEXTO_NAO_ERA_ISSO = 'Obrigado por avisar. Tente escrever de outro jeito, dizendo a cidade e o ano, ou use um destes exemplos:'

/** O piloto está ligado para esta pessoa? Qualquer falha conta como "não". */
export async function pilotoLigado(buscar: Buscar | undefined): Promise<boolean> {
  if (!buscar) return false
  try {
    const r = await buscar(URL_CLASSIFICAR, { method: 'GET', cache: 'no-store' })
    if (!r.ok) return false
    return ((await r.json()) as { ligado?: unknown }).ligado === true
  } catch {
    return false
  }
}

const PARAMETROS: Parametro[] = ['cidade', 'cidade2', 'ano', 'nivel_m', 'rua']
const CAMPOS: (keyof Classificacao)[] = ['intencao', 'cidade', 'cidade2', 'rio', 'ano', 'ano_final', 'mes', 'nivel_m', 'quantidade', 'rua']

function classificacaoValida(x: unknown): x is Classificacao {
  if (!x || typeof x !== 'object') return false
  const o = x as Record<string, unknown>
  return INTENCOES.includes(o.intencao as Intencao) && CAMPOS.every((k) => k in o) && Object.keys(o).length === CAMPOS.length
}

/** Confere a forma da resposta do servidor (o site inteiro está atrás do Access, mas a tela não confia de olhos fechados). */
export function decisaoValida(x: unknown): x is Decisao {
  if (!x || typeof x !== 'object') return false
  const d = x as Record<string, unknown>
  switch (d.tipo) {
    case 'agora':
      return d.origem === 'barreira' || d.origem === 'classificador'
    case 'ok':
      return classificacaoValida(d.classificacao)
    case 'faltou':
      return classificacaoValida(d.classificacao) && Array.isArray(d.faltam) && d.faltam.length > 0 && d.faltam.every((p) => PARAMETROS.includes(p as Parametro))
    case 'nao_sei':
      return typeof d.motivo === 'string'
    default:
      return false
  }
}

/** Uma pergunta ao classificador, com tempo limite. Falha, demora ou resposta estranha → `{erro: true}`. */
export async function classificarPergunta(buscar: Buscar, pergunta: string, origem: Origem, tempoMs = TEMPO_LIMITE_APARELHO_MS): Promise<Classificado> {
  const controle = typeof AbortController === 'function' ? new AbortController() : null
  const relogio = setTimeout(() => controle?.abort(), tempoMs)
  try {
    const r = await Promise.race([
      buscar(URL_CLASSIFICAR, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ pergunta: pergunta.trim().slice(0, 300), origem }),
        ...(controle ? { signal: controle.signal } : {}),
      }),
      new Promise<never>((_, falha) => setTimeout(() => falha(new Error('tempo')), tempoMs + 50)),
    ])
    if (!r.ok) return { erro: true }
    const corpo = (await r.json()) as { id?: unknown; decisao?: unknown }
    if (!decisaoValida(corpo.decisao) || !(corpo.id === null || typeof corpo.id === 'string')) return { erro: true }
    return { id: corpo.id, decisao: corpo.decisao }
  } catch {
    return { erro: true }
  } finally {
    clearTimeout(relogio)
  }
}

/** Guarda o botão "Correto"/"Não era isso". Sem resposta esperada; falha some em silêncio. */
export async function enviarCorrecao(buscar: Buscar, id: string, correcao: Correcao): Promise<void> {
  try {
    await buscar(URL_CLASSIFICAR, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ id, correcao }) })
  } catch {
    /* sem rede: a correção se perde, o chat segue */
  }
}

const NOME_INTENCAO: Record<Intencao, string> = {
  maiores_cheias: 'as maiores cheias de uma cidade',
  cheias_periodo: 'as cheias de uma cidade num período',
  contar_acima: 'quantas cheias passaram de um nível',
  atlas: 'os danos das cheias',
  chuva: 'a chuva antes de uma cheia',
  transito: 'o tempo que a cheia leva entre duas cidades',
  cota_ana: 'a cota da ANA',
  antecedencia_mirim: 'a antecedência do pico no Itajaí-Mirim',
  rua_historico: 'as cheias que passaram da cota de uma rua',
  cotas: 'as cotas da Defesa Civil de uma cidade',
  comparacao: 'a comparação entre duas cidades',
  media: 'a média dos picos de uma cidade',
}

/** O que a tela mostra no lugar da resposta do motor. */
export interface MensagemPiloto {
  texto: string
  sugestoes?: string[]
  /** "Entendi: …" — só quando a resposta veio da classificação. */
  entendido?: string
  /** Para os botões "Correto"/"Não era isso". */
  idCorrecao?: string
}

/**
 * O que a tela mostra quando a pergunta passou pelo classificador. Regras:
 *  - "agora" → o texto da Defesa Civil, sempre;
 *  - "ok" → "Entendi: …" + a resposta do motor para a classificação + os botões;
 *  - "faltou" → pede o que faltou, sem responder;
 *  - "não sei", confiança baixa, demora ou falha → "não consegui interpretar" e os
 *    exemplos — também quando o motor ia palpitar (decisão de 05/10/2026: com o piloto,
 *    a maior cheia da cidade citada nunca sai como resposta automática).
 */
export function mensagemDoPiloto(c: Classificado, d: Dados): MensagemPiloto {
  // Dúvida, demora ou falha: nunca o palpite do motor (a maior cheia da cidade citada).
  if ('erro' in c || c.decisao.tipo === 'nao_sei') return { texto: `${TEXTO_NAO_INTERPRETEI} ${TEXTO_ESCOPO}`, sugestoes: EXEMPLOS }
  const dec = c.decisao
  if (dec.tipo === 'agora') return { texto: TEXTO_ALERTA }
  if (dec.tipo === 'faltou')
    return { texto: `Entendi que a pergunta é sobre ${NOME_INTENCAO[dec.classificacao.intencao]}, mas faltou ${textoParametros(dec.faltam)}. Escreva de novo com isso, por favor.` }
  const r = responderPorIntencao(dec.classificacao, d)
  return {
    texto: r.texto,
    ...(r.sugestoes ? { sugestoes: r.sugestoes } : {}),
    entendido: descreverEntendido(dec.classificacao, d),
    ...(c.id ? { idCorrecao: c.id } : {}),
  }
}
