/**
 * CONTAGEM DAS PERGUNTAS QUE O CHAT NÃO ENTENDE — decisão do Jefferson de 04/10/2026:
 * "Contar somente evento agregado: intenção/categoria, cidade quando necessária,
 * data arredondada, motivo da falha e versão do sistema. Não guardar texto
 * integral, IP, localização precisa, nome, telefone ou identificador persistente."
 *
 * Este módulo é o ESQUEMA FECHADO do evento, usado dos dois lados:
 *  - no navegador, `montarEvento` monta o evento a partir da resposta do motor;
 *  - no servidor (`web/functions/api/chat-nao-entendi.ts`), `validarEvento`
 *    recusa qualquer corpo que não seja exatamente este esquema.
 *
 * A garantia de que o texto digitado não sai do aparelho é ESTRUTURAL: nenhuma
 * função daqui recebe o texto. `montarEvento` recebe a intenção e o motivo que o
 * motor já classificou, a cidade como id do cadastro, a data e a versão do build.
 * Os testes (`telemetriaChat.test.ts`) passam perguntas reais pelo motor e
 * conferem que nenhum pedaço do texto aparece no evento.
 *
 * Sem dependência de navegador nem de Node: as funções que tocam a rede recebem
 * `fetch`/`sendBeacon` por parâmetro. Documentação em `docs/TELEMETRIA-CHAT.md`.
 */

/** Intenções do motor (`chat-local/motor.ts`) + "desconhecida" para o `nao_entendi`. */
export const CATEGORIAS = [
  'maiores_cheias',
  'cheias_periodo',
  'contar_acima',
  'atlas',
  'chuva',
  'transito',
  'cota_ana',
  'antecedencia_mirim',
  'desconhecida',
] as const
export type Categoria = (typeof CATEGORIAS)[number]

/**
 * Por que a pergunta não foi entendida:
 *  - `sem_intencao`: nenhuma intenção casou (a resposta "Não entendi a pergunta");
 *  - `faltou_cidade`: a intenção foi reconhecida, mas a pergunta não disse a cidade;
 *  - `faltou_ano`: a intenção foi reconhecida, mas faltou o ano.
 */
export const MOTIVOS = ['sem_intencao', 'faltou_cidade', 'faltou_ano'] as const
export type MotivoFalha = (typeof MOTIVOS)[number]

/** As únicas chaves do evento, nesta ordem. Qualquer outra é recusada. */
export const CHAVES_EVENTO = ['categoria', 'motivo', 'cidade', 'dia', 'versao'] as const

export interface EventoNaoEntendi {
  categoria: Categoria
  motivo: MotivoFalha
  /** Id do cadastro (`data/estacoes.json`), só quando a pergunta citou a cidade. */
  cidade: string | null
  /** Dia em Brasília, AAAA-MM-DD, sem hora. */
  dia: string
  /** Versão do build (`0.1.0+abc1234`). Igual para todo mundo: não identifica ninguém. */
  versao: string
}

/** O que o motor diz quando a pergunta não foi entendida (campo `falha` da `Resposta`). */
export interface FalhaDoMotor {
  motivo: MotivoFalha
  /** Id da cidade que a pergunta citou, se citou. Pode não ser do cadastro (Atlas). */
  cidade?: string
}

/** Retenção dos contadores no servidor (TTL do KV), em dias. */
export const RETENCAO_DIAS = 90
/** No máximo tantos eventos por página aberta: ninguém enche o contador sozinho. */
export const LIMITE_POR_PAGINA = 10
/** Mesma origem do site (rotas no `#`, a página fica em `/`). */
export const ROTA_CONTAGEM = './api/chat-nao-entendi'
/** Corpo maior que isso não é um evento. */
export const TAMANHO_MAXIMO_CORPO = 512

const RE_CIDADE = /^[a-z0-9-]{2,40}$/
const RE_DIA = /^\d{4}-\d{2}-\d{2}$/
const RE_VERSAO = /^[0-9A-Za-z.+_-]{1,40}$/
const ehCategoria = (x: unknown): x is Categoria => typeof x === 'string' && (CATEGORIAS as readonly string[]).includes(x)
const ehMotivo = (x: unknown): x is MotivoFalha => typeof x === 'string' && (MOTIVOS as readonly string[]).includes(x)

/** Ids das cidades do cadastro, de `data/estacoes.json`. */
export function idsDoCadastro(estacoes: { rios: Record<string, { cidades: { id: string }[] }> }): Set<string> {
  const ids = new Set<string>()
  for (const rio of Object.values(estacoes.rios)) for (const c of rio.cidades) if (RE_CIDADE.test(c.id)) ids.add(c.id)
  return ids
}

/** O dia em Brasília (America/Sao_Paulo), AAAA-MM-DD. A hora é descartada aqui. */
export function diaDeBrasilia(agora: Date): string {
  const partes = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Sao_Paulo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(agora)
  const p = (t: string) => partes.find((x) => x.type === t)?.value ?? ''
  return `${p('year')}-${p('month')}-${p('day')}`
}

/**
 * Monta o evento agregado de uma resposta do motor, ou `null` se a pergunta foi
 * entendida. Não recebe o texto digitado — de propósito.
 */
export function montarEvento(entrada: {
  intencao: string
  falha: FalhaDoMotor | undefined
  agora: Date
  versao: string
  cidadesDoCadastro: ReadonlySet<string>
}): EventoNaoEntendi | null {
  const { falha } = entrada
  if (!falha || !ehMotivo(falha.motivo)) return null
  const categoria: Categoria = ehCategoria(entrada.intencao) ? entrada.intencao : 'desconhecida'
  const cidade =
    falha.cidade && RE_CIDADE.test(falha.cidade) && entrada.cidadesDoCadastro.has(falha.cidade) ? falha.cidade : null
  return {
    categoria,
    motivo: falha.motivo,
    cidade,
    dia: diaDeBrasilia(entrada.agora),
    versao: RE_VERSAO.test(entrada.versao) ? entrada.versao : 'desconhecida',
  }
}

/**
 * Lado do servidor: devolve o evento se o corpo é EXATAMENTE o esquema, senão
 * `null`. Campo a mais, a menos, de tipo errado, cidade fora do cadastro, dia
 * com hora ou longe de hoje — tudo recusado.
 */
export function validarEvento(
  corpo: unknown,
  opcoes: { cidadesDoCadastro: ReadonlySet<string>; agora: Date },
): EventoNaoEntendi | null {
  if (!corpo || typeof corpo !== 'object' || Array.isArray(corpo)) return null
  if (Object.getPrototypeOf(corpo) !== Object.prototype) return null
  const chaves = Object.keys(corpo)
  if (chaves.length !== CHAVES_EVENTO.length || !CHAVES_EVENTO.every((c) => chaves.includes(c))) return null
  const { categoria, motivo, cidade, dia, versao } = corpo as Record<string, unknown>
  if (!ehCategoria(categoria) || !ehMotivo(motivo)) return null
  if (cidade !== null && (typeof cidade !== 'string' || !RE_CIDADE.test(cidade) || !opcoes.cidadesDoCadastro.has(cidade)))
    return null
  if (typeof dia !== 'string' || !RE_DIA.test(dia)) return null
  // Só ontem, hoje ou amanhã (relógio do aparelho torto, virada do dia): data
  // arbitrária não entra, e o TTL de retenção continua valendo para todas.
  const umDia = 86_400_000
  const aceitos = [-umDia, 0, umDia].map((d) => diaDeBrasilia(new Date(opcoes.agora.getTime() + d)))
  if (!aceitos.includes(dia)) return null
  if (typeof versao !== 'string' || !RE_VERSAO.test(versao)) return null
  return { categoria, motivo, cidade, dia, versao }
}

/** Chave do contador no KV: `dia|categoria|motivo|cidade` (cidade "-" quando não há). */
export function chaveContador(e: EventoNaoEntendi): string {
  return `${e.dia}|${e.categoria}|${e.motivo}|${e.cidade ?? '-'}`
}

/** Corpo enviado: só as chaves do esquema, na ordem fixa. */
export function serializarEvento(e: EventoNaoEntendi): string {
  return JSON.stringify({ categoria: e.categoria, motivo: e.motivo, cidade: e.cidade, dia: e.dia, versao: e.versao })
}

type FetchMinimo = (url: string, init?: RequestInit) => Promise<Response>

/**
 * O servidor está contando? Só `true` com resposta 200, sem desvio (sessão do
 * Access vencida), em JSON e com `"contando": true`. Qualquer outra coisa —
 * endpoint inexistente, HTML, sem rede — é `false`: na dúvida, não conta e não
 * mostra o aviso de contagem.
 */
export async function servidorContando(f: FetchMinimo): Promise<boolean> {
  try {
    const r = await f(ROTA_CONTAGEM, { method: 'GET', cache: 'no-store', credentials: 'same-origin' })
    if (!r.ok || r.redirected) return false
    if (!(r.headers.get('content-type') ?? '').toLowerCase().startsWith('application/json')) return false
    const corpo: unknown = await r.json()
    return !!corpo && typeof corpo === 'object' && (corpo as { contando?: unknown }).contando === true
  } catch {
    return false
  }
}

/**
 * Cria a função de envio. Uma tentativa por evento, sem fila, sem repetição:
 * `sendBeacon` primeiro (sobrevive ao fechar da aba); se não houver ou recusar,
 * um `fetch` com `keepalive`. Erro é engolido — o chat nunca quebra por isso.
 * Teto de `LIMITE_POR_PAGINA` eventos por página aberta (contador em memória,
 * que some ao fechar a aba).
 */
export function criarEnviador(deps: {
  beacon?: ((url: string, corpo: string) => boolean) | undefined
  fetch?: FetchMinimo | undefined
  limite?: number
}): (e: EventoNaoEntendi) => void {
  let enviados = 0
  const limite = deps.limite ?? LIMITE_POR_PAGINA
  return (e) => {
    if (enviados >= limite) return
    enviados++
    const corpo = serializarEvento(e)
    try {
      if (deps.beacon?.(ROTA_CONTAGEM, corpo)) return
    } catch {
      /* cai no fetch */
    }
    try {
      deps
        .fetch?.(ROTA_CONTAGEM, {
          method: 'POST',
          body: corpo,
          keepalive: true,
          credentials: 'same-origin',
          headers: { 'content-type': 'text/plain;charset=UTF-8' },
        })
        .catch(() => {})
    } catch {
      /* sem fetch: desiste */
    }
  }
}
