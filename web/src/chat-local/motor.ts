/**
 * Chat local do histórico: SEM IA e SEM API.
 *
 * Entende a pergunta por palavras-chave e monta a resposta direto dos JSONs de
 * `data/`. Tudo que ele diz sai de um registro, com a fonte e a ressalva do
 * próprio registro. Se não entender, diz que não entendeu — nunca chuta.
 *
 * Funções puras: recebem `Dados` e a pergunta. Testáveis em Node, rodam no
 * navegador. Especificação e regras do produto em `docs/CHAT-LOCAL.md`.
 */
import type { FalhaDoMotor } from '../logica/telemetriaChat'
import type { CotaRua, Trecho, TrechoExperimental } from '../dados/tipos'
import { caminho, type Caminho } from '../logica/transito'
import { buscar, cidadesComCotas, nomeCompleto, podeAfirmarAlcance } from '../logica/cotasRuas'

export interface RegistroCheia {
  rio?: string
  cidade: string
  data: string
  pico_m: number
  confianca: string
  fonte: string
  nota?: string
  referencia?: string | null
  divergencias?: { pico_m: number; fonte: string }[]
}

export interface TrechoTransito {
  rio?: string
  de: string
  para: string
  horas_min: number
  horas_max: number
  confianca: string
  fonte?: string
}

export interface RegistroAtlas {
  municipio: string
  data_evento: string
  tipologia: string
  mortos?: number
  desabrigados?: number
  desalojados?: number
}

export interface EventoAtlas {
  id: string
  mes: string
  tipologias: string[]
  n_municipios: number
  totais: { mortos: number; desabrigados: number; desalojados: number }
  registros: RegistroAtlas[]
}

export interface JanelaChuva {
  mm: number | null
  cobertura: number
}

export interface EventoChuva {
  data_ancora: string
  estacoes: Record<string, Record<string, JanelaChuva>>
}

export interface Dados {
  enchentes: { eventos: RegistroCheia[] }
  transito: { trechos: TrechoTransito[]; trechos_experimentais?: TrechoExperimental[] }
  estacoes: {
    rios: Record<
      string,
      {
        nome: string
        /** Árvore do rio (`docs/TOPOLOGIA-CANONICA.md`): tronco, cabeceiras e afluentes. */
        _topologia?: {
          tronco_sequencia?: string[]
          cabeceiras_paralelas?: string[]
          afluentes_laterais?: { id: string; entra_perto_de: string; rio: string }[]
        }
        cidades: {
          id: string
          nome: string
          /** Brusque: só os picos desde `desde` estão na régua declarada (decisão de 04/10/2026). */
          historico_referencia?: { desde: string }
          /** Cotas da Defesa Civil da cidade, na régua dela (`cotasDaCidade`). */
          cotas_m?: Record<string, number>
          cotas_nomes_na_fonte?: Record<string, string>
          cotas_verificado?: boolean | null
          cotas_aviso_publico?: string
          fonte_cotas?: string
        }[]
      }
    >
  }
  /** "itajai-acu" | "itajai-mirim" → recorte do Atlas de Desastres. */
  atlas: Record<string, { eventos: EventoAtlas[] }>
  chuvaEventos: { estacoes: Record<string, { nome: string }>; eventos: Record<string, EventoChuva> }
  cotasAna?: { estacoes: Record<string, { nome: string; datas: string[]; cm: number[] }> }
  picosMirim?: { eventos: { botuvera_mont?: { antecedencia_h: number } }[] }
  /** Cotas de rua já filtradas (só régua). Baixadas quando a pergunta cita uma rua. */
  cotasRuas?: CotaRua[]
}

export interface Resposta {
  intencao: string
  texto: string
  sugestoes?: string[]
  /**
   * Preenchido só quando a pergunta NÃO foi entendida: o motivo (enum fechado) e,
   * se a pergunta citou, o id da cidade. Nunca o texto. É o que a contagem
   * agregada lê (`logica/telemetriaChat.ts`, decisão de 04/10/2026).
   */
  falha?: FalhaDoMotor
  /**
   * A resposta saiu do PALPITE do roteador (achou só a cidade, ou só o ano, e nenhuma
   * intenção). O piloto do classificador consulta a IA também nesse caso
   * (`docs/PILOTO-CLASSIFICADOR.md`).
   */
  palpite?: boolean
}

/** Falha por falta de dado na pergunta: cidade (se citada) e motivo. */
const faltou = (motivo: FalhaDoMotor['motivo'], e: Extraido): FalhaDoMotor =>
  e.cidade ? { motivo, cidade: e.cidade.id } : { motivo }

// ---------------------------------------------------------------- utilidades
export function norm(s: string): string {
  return s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9,.\s-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}
const MESES = ['janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
const MESES_EXIBIR = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
const num = (n: number, casas = 2) => n.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: casas })
const m = (n: number) => `${num(n)} m`

/** "2023-10-13" → "13/10/2023"; "1983-07" → "julho de 1983"; "1911" → "1911". */
export function dataBR(d: string): string {
  const [a, mes, dia] = d.split('-')
  if (dia) return `${dia}/${mes}/${a}`
  if (mes) return `${MESES_EXIBIR[parseInt(mes, 10) - 1]} de ${a}`
  return a ?? d
}
const CONF: Record<string, string> = { alta: 'confiança alta', media: 'confiança média', baixa: 'confiança BAIXA' }
const conf = (c: string) => CONF[c] ?? c
const corta = (s: string | undefined, n = 240) => (s && s.length > n ? s.slice(0, n) + '…' : (s ?? ''))
const mesIso = (ano: number, mes: number) => `${ano}-${String(mes).padStart(2, '0')}`

// ---------------------------------------------------------------- barreira de "agora"
// Checada antes de qualquer outra coisa. Não é alerta: pergunta sobre o presente
// vai para a Defesa Civil e para as réguas ao vivo do site.
//
// Correções de 04/10/2026 (achadas pela prova do chat com IA, docs/PROVA-CHAT-IA.md):
//  - "alerta" sozinho NÃO é mais barreira: "qual a cota de alerta de Blumenau?" é pergunta
//    sobre a régua, e recebia o texto do 199. Só o alerta de AGORA ("tem alerta?", "está em
//    alerta?", "alerta vigente") continua barrado. "previsão" continua barrada.
//  - "essa madrugada", "daqui a pouco", "como está o rio" passavam pela barreira.
const AGORA = [
  /\b(agora|hoje|hj|amanha|neste momento|nesse momento|esta noite|essa noite|esta semana|essa semana|proximas horas)\b/,
  /\b(madrugada|logo mais|daqui a pouco|mais tarde|esta tarde|essa tarde|esta manha|essa manha|proximos dias|fim de semana)\b/,
  /\bcomo (esta|ta|estao|tao|anda|andam)\b.{0,25}\b(rio|rios|nivel|agua|cheia|enchente|situacao|ribeirao)\b/,
  /\b(vai|vao|pode|deve)\s+(encher|subir|transbordar|alagar|inundar|chover|baixar|descer)\b/,
  /\b(esta|ta|estao|tao)\s+(enchendo|subindo|alagando|transbordando|chovendo)\b/,
  /\b(devo|preciso|precisamos|tenho que|temos que|e para|e pra)\s+(sair|evacuar|deixar|subir os moveis|tirar o carro)\b/,
  /\b(nivel|cota|situacao)\s+(atual|de agora|de hoje)\b/,
  /\bprevisao\b/,
  // Pedido de conselho para agora, disfarçado (04/10/2026): "preciso me preocupar?",
  // "dá para passar na ponte?", "vale a pena tirar o carro?".
  /\b(preciso|precisamos|devo|devemos|tenho que|temos que|vale a pena|e seguro|da para|da pra|posso|podemos)\s+(me\s+|nos\s+)?(preocupar|passar|atravessar|tirar|sair|voltar|subir|levar|deixar|ir (trabalhar|para|pra))\b/,
  /\b(tem|ha|existe|esta|estamos|estao|ta|tao|emitiu|emitiram|saiu|decretou|decretaram|entrou|entramos)\s+(algum\s+|um\s+|o\s+|de\s+|no\s+|em\s+)?(estado\s+de\s+)?alerta\b/,
  /\balerta\s+(vigente|ativo|em vigor|valendo|para (hoje|amanha|esta|essa))\b/,
  /\b(estou|to|moro)\b.{0,40}\b(ilhad|alagad|cercad)/,
]
/** A pergunta é sobre o presente (nível de agora, previsão, sair de casa)? Vale também para o chat com IA. */
export function pedeAgora(pergunta: string): boolean {
  const t = norm(pergunta)
  return AGORA.some((r) => r.test(t))
}
export const TEXTO_ALERTA =
  'Eu só respondo sobre cheias que já aconteceram, com os dados deste site. Não sei o que está acontecendo no rio agora. ' +
  'Para a situação atual, previsão ou para decidir se deve sair de casa, siga a Defesa Civil: ligue 199 (ou 193, Bombeiros, em emergência). ' +
  'O nível ao vivo das réguas está na página de cada rio, com a fonte e a hora da leitura.'

// ---------------------------------------------------------------- extração
export interface CidadeConhecida {
  id: string
  nome: string
  rio: string
  chave: string
}

export interface Extraido {
  t: string
  cidade?: CidadeConhecida
  cidade2?: CidadeConhecida
  rio?: string
  ano?: number
  ano2?: number
  mes?: number
  nivel?: number
  n?: number
}

export function cidadesConhecidas(d: Dados): CidadeConhecida[] {
  const lista: CidadeConhecida[] = []
  for (const [rio, r] of Object.entries(d.estacoes.rios))
    for (const c of r.cidades) if (!lista.some((x) => x.id === c.id)) lista.push({ id: c.id, nome: c.nome, rio, chave: norm(c.nome) })
  for (const [rio, r] of Object.entries(d.atlas))
    for (const ev of r.eventos)
      for (const x of ev.registros ?? []) {
        const chave = norm(x.municipio)
        if (!lista.some((c) => c.chave === chave)) lista.push({ id: chave.replace(/\s+/g, '-'), nome: x.municipio, rio, chave })
      }
  return lista.sort((a, b) => b.chave.length - a.chave.length) // "rio do sul" antes de "sul"
}

export function extrair(pergunta: string, d: Dados): Extraido {
  let t = norm(pergunta)
  const e: Extraido = { t }
  // rio: tirado do texto antes de procurar cidade, para "itajai" do nome do rio não virar a cidade
  if (/\bitajai[\s-]?mirim\b|\bmirim\b/.test(t)) {
    e.rio = 'itajai-mirim'
    t = t.replace(/\bitajai[\s-]?mirim\b/g, ' ')
  } else if (/\bitajai[\s-]?acu\b|\bacu\b/.test(t)) {
    e.rio = 'itajai-acu'
    t = t.replace(/\bitajai[\s-]?acu\b/g, ' ')
  }
  // cidades, na ordem em que aparecem
  const achadas: { pos: number; c: CidadeConhecida }[] = []
  // Pontuação vira espaço SÓ na busca de cidade ("rio do sul,"); mesmo tamanho, mesma posição.
  let resto = ` ${t.replace(/[,.;:!?]/g, ' ')} `
  for (const c of cidadesConhecidas(d)) {
    const i = resto.indexOf(` ${c.chave} `)
    if (i >= 0) {
      achadas.push({ pos: i, c })
      resto = resto.slice(0, i) + ' '.repeat(c.chave.length + 1) + resto.slice(i + c.chave.length + 1)
    }
  }
  achadas.sort((a, b) => a.pos - b.pos)
  if (achadas[0]) e.cidade = achadas[0].c
  if (achadas[1]) e.cidade2 = achadas[1].c
  if (!e.rio && e.cidade) e.rio = e.cidade.rio
  // anos, mês, nível, quantidade
  const anos = [...t.matchAll(/\b(1[89]\d{2}|20\d{2})\b/g)].map((x) => parseInt(x[1] ?? '', 10))
  if (anos[0]) e.ano = anos[0]
  if (anos[1]) e.ano2 = anos[1]
  const mi = MESES.findIndex((mes) => new RegExp(`\\b${mes}\\b`).test(t))
  if (mi >= 0) e.mes = mi + 1
  const mm = t.match(/\b(\d{1,2}(?:[.,]\d{1,2})?)\s?(m|metros?)\b/)
  if (mm?.[1]) e.nivel = parseFloat(mm[1].replace(',', '.'))
  const q = t.match(/\b(\d{1,2})\s+(maiores|piores|mais altas)\b/)
  if (q?.[1]) e.n = parseInt(q[1], 10)
  return e
}

// ---------------------------------------------------------------- intenções
function linhaCheia(r: RegistroCheia): string {
  let s = `• ${dataBR(r.data)}: ${m(r.pico_m)} (${conf(r.confianca)})`
  if (r.referencia) s += ` — referência: ${r.referencia}`
  return s
}
function fonteDe(regs: RegistroCheia[]): string {
  const f = [...new Set(regs.map((r) => r.fonte.split(' — http')[0]))]
  return `Fonte: ${f.slice(0, 3).join('; ')}${f.length > 3 ? ' e outras' : ''}.`
}
function ressalvas(regs: RegistroCheia[]): string {
  const out: string[] = []
  for (const r of regs) {
    if (r.confianca === 'baixa' && r.nota) out.push(`Atenção (${dataBR(r.data)}): ${corta(r.nota, 400)}`)
    if (r.divergencias?.length)
      out.push(`Divergência (${dataBR(r.data)}): também publicado ${r.divergencias.map((x) => `${m(x.pico_m)} (${x.fonte})`).join('; ')}.`)
  }
  return out.join('\n')
}
const semCidade = (d: Dados) => {
  const c = [...new Set(d.enchentes.eventos.map((e) => e.cidade))]
  const conhecidas = cidadesConhecidas(d)
  const nomes = c.map((id) => conhecidas.find((x) => x.id === id)?.nome ?? id)
  return `Não achei a cidade na pergunta, ou ela não tem picos neste site. Tenho picos históricos para: ${nomes.join(', ')}. Diga a cidade.`
}

// Cidade de várias réguas: um número só não é "o nível" dela, e a maior cheia não sai de
// comparar picos de estações diferentes.
const VARIAS_REGUAS: Record<string, string> = {
  itajai:
    'Itajaí tem onze réguas da Defesa Civil, cada uma com seu zero, e as mais perto da foz sobem e descem com a maré. Um número só não é "o nível de Itajaí"',
}

/** Registros do Atlas da cidade, sem repetir protocolo (Itajaí está no recorte dos dois rios). */
function atlasDaCidade(cidade: CidadeConhecida, d: Dados): RegistroAtlas[] {
  const vistos = new Map<string, RegistroAtlas>()
  for (const r of Object.values(d.atlas))
    for (const ev of r.eventos)
      for (const x of ev.registros ?? [])
        if (norm(x.municipio) === cidade.chave) vistos.set(`${x.data_evento}|${x.tipologia}|${x.desabrigados}|${x.desalojados}`, x)
  return [...vistos.values()]
}
const atingidos = (x: RegistroAtlas) => (x.desabrigados ?? 0) + (x.desalojados ?? 0)

function semPicoNaCidade(cidade: CidadeConhecida, d: Dados): Resposta {
  const top = atlasDaCidade(cidade, d)
    .filter((x) => atingidos(x) > 0 || (x.mortos ?? 0) > 0)
    .sort((a, b) => atingidos(b) - atingidos(a) || (b.mortos ?? 0) - (a.mortos ?? 0))
    .slice(0, 5)
  const linhas = top.map((x) => {
    const danos = [x.mortos ? `${x.mortos} morto(s)` : '', x.desabrigados ? `${num(x.desabrigados)} desabrigados` : '', x.desalojados ? `${num(x.desalojados)} desalojados` : ''].filter(Boolean)
    return `• ${dataBR(x.data_evento)}, ${x.tipologia.toLowerCase()}: ${danos.join(', ')}`
  })
  return {
    intencao: 'maiores_cheias',
    texto: [
      `O site ainda não tem o nível do rio (em metros) registrado para as cheias de ${cidade.nome}.`,
      VARIAS_REGUAS[cidade.id] ? `${VARIAS_REGUAS[cidade.id]}: cada pico precisa dizer de qual régua é.` : '',
      top.length
        ? `O que dá para dizer é pelo tamanho do estrago. Pelo Atlas Digital de Desastres (1991–2025), as ocorrências de ${cidade.nome} com mais gente fora de casa foram:`
        : '',
      linhas.join('\n'),
      top.length
        ? 'Isso mede o impacto, não a altura do rio: a tipologia é a que o município declarou (novembro de 2008 aparece como enxurrada), e cheias de antes de 1991, como as de 1983 e 1984, não estão no Atlas.\nFonte: Atlas Digital de Desastres no Brasil (MIDR), v1.1 de 06/08/2026.'
        : '',
      semCidade(d),
    ]
      .filter(Boolean)
      .join('\n'),
  }
}

/** Picos tirados da série da ANA estão no zero da ANA, não na régua da Defesa Civil. */
function reguaDosPicos(regs: RegistroCheia[]): string {
  const ana = regs.filter((r) => r.fonte.startsWith('ANA/HidroWeb')).length
  if (!ana) return ', em metros na régua local.'
  if (ana === regs.length) return ', em metros na régua da ANA, que tem zero próprio: não compare com as cotas da Defesa Civil.'
  return `, em metros; ${ana} deles na régua da ANA, que tem zero próprio.`
}

/** Picos de estações diferentes da mesma cidade: lista cada um com o rio, sem eleger "a maior". */
function picosPorEstacao(cidade: CidadeConhecida, regs: RegistroCheia[], d: Dados): Resposta {
  const ord = [...regs].sort((a, b) => a.data.localeCompare(b.data) || (a.rio ?? '').localeCompare(b.rio ?? ''))
  return {
    intencao: 'maiores_cheias',
    texto: [
      `${VARIAS_REGUAS[cidade.id]}: por isso o site não diz qual foi "a maior cheia" de ${cidade.nome}. Os picos que tem são de estações diferentes, e números de estações diferentes não se comparam — nem entre si, nem com as réguas de hoje:`,
      ord.map((r) => `• ${dataBR(r.data)}, ${r.rio ? nomeRio(d, r.rio) : 'rio não informado'}: ${m(r.pico_m)} (${conf(r.confianca)})`).join('\n'),
      ressalvas(ord),
      fonteDe(ord),
    ]
      .filter(Boolean)
      .join('\n'),
  }
}

function maioresCheias(e: Extraido, d: Dados): Resposta {
  if (!e.cidade) return { intencao: 'maiores_cheias', texto: semCidade(d), falha: faltou('faltou_cidade', e) }
  const cidade = e.cidade
  const regs = d.enchentes.eventos.filter((r) => r.cidade === cidade.id)
  if (!regs.length) return semPicoNaCidade(cidade, d)
  if (VARIAS_REGUAS[cidade.id]) return picosPorEstacao(cidade, regs, d)
  const n = Math.min(e.n ?? (/\bmaiores|piores\b/.test(e.t) ? 5 : 1), 10)
  const top = [...regs].sort((a, b) => b.pico_m - a.pico_m).slice(0, n)
  const primeiro = top[0]
  if (!primeiro) return { intencao: 'maiores_cheias', texto: semCidade(d) }
  const cab =
    n === 1
      ? `A maior cheia registrada de ${cidade.nome} foi de ${m(primeiro.pico_m)}, em ${dataBR(primeiro.data)}.`
      : `As ${n} maiores cheias registradas de ${cidade.nome}:`
  return {
    intencao: 'maiores_cheias',
    texto: [
      cab,
      n > 1 ? top.map(linhaCheia).join('\n') : `(${conf(primeiro.confianca)}${primeiro.referencia ? `; referência: ${primeiro.referencia}` : ''})`,
      (regs.length === 1 ? `É o único pico registrado para ${cidade.nome}` : `São ${regs.length} picos registrados para ${cidade.nome}`) + reguaDosPicos(regs),
      ressalvas(top),
      fonteDe(top),
    ]
      .filter(Boolean)
      .join('\n'),
  }
}

function cheiasDoPeriodo(e: Extraido, d: Dados): Resposta {
  if (!e.cidade || e.ano == null)
    return { intencao: 'cheias_periodo', texto: semCidade(d), falha: faltou(e.cidade ? 'faltou_ano' : 'faltou_cidade', e) }
  const cidade = e.cidade
  const ano = e.ano
  const fim = e.ano2 ?? ano
  let regs = d.enchentes.eventos.filter((r) => {
    const a = parseInt(r.data.slice(0, 4), 10)
    return r.cidade === cidade.id && a >= ano && a <= fim
  })
  if (e.mes) regs = regs.filter((r) => parseInt(r.data.slice(5, 7), 10) === e.mes)
  const quando = e.mes ? `${MESES_EXIBIR[e.mes - 1]} de ${ano}` : e.ano2 ? `${ano}–${e.ano2}` : `${ano}`
  if (!regs.length)
    return {
      intencao: 'cheias_periodo',
      texto: `O site não tem pico de cheia registrado em ${cidade.nome} em ${quando}. Isso não quer dizer que não houve cheia: só que nenhuma fonte usada pelo site registrou pico nesse período.`,
    }
  regs.sort((a, b) => a.data.localeCompare(b.data))
  return { intencao: 'cheias_periodo', texto: [`Picos registrados em ${cidade.nome} em ${quando}:`, regs.map(linhaCheia).join('\n'), ressalvas(regs), fonteDe(regs)].filter(Boolean).join('\n') }
}

// ---------------------------------------------------------------- escala de cada pico
// Um pico só se compara com um nível na MESMA escala. A contagem "quantas cheias
// passaram de 10 m" juntava régua de hoje, zero do IBGE e pico sem referência e
// dizia "na régua local" — em Blumenau, 72 picos quando só 32 estão na régua
// (achado em 04/10/2026). A regra é a do CLAUDE.md (Blumenau, item 4): conta só
// o que está na régua e diz quantos ficaram de fora e por quê.

/** A escala de um pico, para não somar metros de referências diferentes. */
export type Escala = 'regua' | 'ibge' | 'ana' | 'nao-declarada' | 'antes-da-regua'

const NOME_ESCALA: Record<Escala, string> = {
  regua: 'na régua da cidade',
  ibge: 'no zero do IBGE (20 cm abaixo da régua de hoje)',
  ana: 'no zero da estação da ANA, que é próprio',
  'nao-declarada': 'sem referência declarada pela fonte',
  'antes-da-regua': 'antes do trecho que a cidade declara na régua (referência não conferida)',
}

function declaracaoDaCidade(cidadeId: string, d: Dados): { desde: string } | undefined {
  for (const r of Object.values(d.estacoes.rios)) {
    const c = r.cidades.find((x) => x.id === cidadeId)
    if (c?.historico_referencia) return c.historico_referencia
  }
  return undefined
}

export function escalaDoPico(r: RegistroCheia, d: Dados): Escala {
  if (r.referencia === null) return 'nao-declarada'
  if (r.referencia && r.referencia !== 'régua') return /IBGE/i.test(r.referencia) ? 'ibge' : 'nao-declarada'
  const decl = declaracaoDaCidade(r.cidade, d)
  if (decl && r.data < decl.desde) return 'antes-da-regua'
  // Campo ausente = registro antigo, assumido na régua — salvo quando o pico saiu
  // da série da ANA, que tem zero próprio (ver `reguaDosPicos`).
  if (r.referencia === undefined && r.fonte.startsWith('ANA/HidroWeb')) return 'ana'
  return 'regua'
}

interface Contagem {
  /** A escala em que a conta foi feita, ou null quando não dá para contar. */
  escala: Escala | null
  /** Picos da cidade nessa escala (o denominador). */
  base: RegistroCheia[]
  /** Os que passaram do nível, nessa escala. */
  acima: RegistroCheia[]
  /** Os que passaram do nível em OUTRA escala: fora da conta, ditos à parte. */
  fora: Map<Escala, number>
}

/**
 * Quantos picos da cidade chegaram a `nivel`, sem misturar escalas.
 *
 * `exigirRegua`: a cota de rua está na régua de hoje, então só os picos na régua
 * podem ser comparados com ela. Na pergunta sem rua, se a cidade não tem pico na
 * régua mas tem uma escala só (Rio do Sul: todos sem referência declarada), conta
 * nela e diz qual é.
 */
function contarNaEscala(regs: RegistroCheia[], nivel: number, d: Dados, exigirRegua: boolean): Contagem {
  const porEscala = new Map<Escala, RegistroCheia[]>()
  for (const r of regs) {
    const e = escalaDoPico(r, d)
    porEscala.set(e, [...(porEscala.get(e) ?? []), r])
  }
  let escala: Escala | null = null
  if (porEscala.has('regua')) escala = 'regua'
  else if (!exigirRegua && porEscala.size === 1) escala = [...porEscala.keys()][0] ?? null
  const base = escala ? (porEscala.get(escala) ?? []) : []
  const acima = base.filter((r) => r.pico_m >= nivel).sort((a, b) => a.data.localeCompare(b.data))
  const fora = new Map<Escala, number>()
  for (const [e, lista] of porEscala) {
    if (e === escala) continue
    const n = lista.filter((r) => r.pico_m >= nivel).length
    if (n) fora.set(e, n)
  }
  return { escala, base, acima, fora }
}

function textoFora(fora: Map<Escala, number>): string {
  if (!fora.size) return ''
  const total = [...fora.values()].reduce((a, b) => a + b, 0)
  const partes = [...fora].map(([e, n]) => `${n} ${NOME_ESCALA[e]}`)
  return `Fora da conta: ${total} pico(s) que também passaram desse número, mas em outra escala — ${partes.join('; ')}. A mesma altura em escalas diferentes não é a mesma água, então eles não entram na soma.`
}

function contarAcima(e: Extraido, d: Dados): Resposta {
  if (!e.cidade || e.nivel == null)
    return {
      intencao: 'contar_acima',
      texto: 'Diga a cidade e o nível, por exemplo: "quantas cheias passaram de 10 m em Rio do Sul?"',
      ...(e.cidade ? {} : { falha: faltou('faltou_cidade', e) }),
    }
  const cidade = e.cidade
  const nivel = e.nivel
  if (VARIAS_REGUAS[cidade.id])
    return {
      intencao: 'contar_acima',
      texto: `${VARIAS_REGUAS[cidade.id]}: por isso o site não conta quantas cheias de ${cidade.nome} passaram de ${m(nivel)}. Cada estação tem o seu zero.`,
    }
  const daCidade = d.enchentes.eventos.filter((r) => r.cidade === cidade.id)
  if (!daCidade.length) return semPicoNaCidade(cidade, d)
  const c = contarNaEscala(daCidade, nivel, d, false)
  if (!c.escala)
    return {
      intencao: 'contar_acima',
      texto: [
        `Os picos de ${cidade.nome} estão em escalas diferentes e nenhum na régua de hoje. Contar juntos misturaria metros que não se comparam, então o site não soma.`,
        textoFora(c.fora),
      ]
        .filter(Boolean)
        .join('\n'),
    }
  const onde =
    c.escala === 'regua'
      ? `na régua de ${cidade.nome}`
      : `${NOME_ESCALA[c.escala]} — não compare com o nível de hoje`
  return {
    intencao: 'contar_acima',
    texto: [
      `${cidade.nome} tem ${c.acima.length} pico(s) registrado(s) de ${m(nivel)} ou mais, ${onde} (de ${c.base.length} nessa escala).`,
      c.acima.map(linhaCheia).join('\n'),
      textoFora(c.fora),
      ressalvas(c.acima),
      c.acima.length ? fonteDe(c.acima) : '',
    ]
      .filter(Boolean)
      .join('\n'),
  }
}

// ---------------------------------------------------------------- rua
// "Quantas cheias passaram da cota da Rua X?" — decisão do Jefferson de 04/10/2026.
// A frase nunca é "a sua rua alagou N vezes": a cota é de hoje, é de um ponto, e a
// lista de cheias é incompleta. É "o rio passou da cota deste ponto em N das cheias
// registradas na régua".

const PALAVRA_RUA = /\b(rua|avenida|av|travessa|tv|servidao|estrada|rodovia|alameda)\b/

/** A pergunta cita uma rua? Serve também para o componente baixar as cotas antes. */
export function citaRua(pergunta: string): boolean {
  return PALAVRA_RUA.test(norm(pergunta))
}

/** O nome da rua dentro da pergunta: o que vem depois de "rua", até a cidade ou o verbo. */
export function termoDaRua(e: Extraido): string | null {
  const t = ` ${e.t} `
  const mt = t.match(PALAVRA_RUA)
  if (!mt || mt.index == null) return null
  let resto = t.slice(mt.index + mt[0].length)
  if (e.cidade) resto = resto.replace(` ${e.cidade.chave} `, ' | ')
  const corte = resto.search(/\s(\||em|ja|alag|quant|passou|passaram|pegou|teve|foi|enche|inund|na cheia|nas cheias)\b/)
  if (corte >= 0) resto = resto.slice(0, corte)
  resto = resto.replace(/\b(da|de|do|dos|das)\s*$/, '').replace(/[?.,]/g, ' ').trim()
  return resto.length >= 2 ? resto : null
}

const MAX_RUAS_CHAT = 4

const NOTA_LISTA_ESPARSA: Record<string, string> = {
  gaspar: 'A lista de Gaspar só traz as cheias grandes (a menor tem 6,19 m): cheias médias que passaram desta cota podem não estar nela.',
}

// ---------------------------------------------------------------- comparar duas cidades
// "Em 2008 foi maior em Blumenau ou em Gaspar?" — cada cidade tem a sua régua, e metros de
// réguas diferentes não se comparam (CLAUDE.md). O que se compara é a POSIÇÃO de cada cheia
// na história da própria cidade, na mesma escala (04/10/2026).
const PEDE_COMPARACAO = /\b(ou|versus|vs|x|comparad\w*|comparar|compara|diferenca)\b/
const PEDE_MAIOR = /\b(maior|maiores|mais|pior|piores|alta|alto|subiu|compar\w*|diferenca)\b/
const ORDINAL = (n: number) => `${n}ª`

function linhaComparacao(c: CidadeConhecida, e: Extraido, d: Dados): string {
  if (VARIAS_REGUAS[c.id]) return `• ${c.nome}: ${VARIAS_REGUAS[c.id]}, então não há um número só para a cidade.`
  const regs = d.enchentes.eventos.filter((r) => r.cidade === c.id)
  const { escala, base } = contarNaEscala(regs, -Infinity, d, false)
  const pref = e.ano ? (e.mes ? mesIso(e.ano, e.mes) : String(e.ano)) : ''
  const doPeriodo = regs.filter((r) => r.data.startsWith(pref))
  if (!doPeriodo.length) return `• ${c.nome}: o site não tem pico registrado ${e.ano ? `em ${e.mes ? mesBR(pref) : e.ano}` : ''}.`.replace(' .', '.')
  const naEscala = escala ? doPeriodo.filter((r) => escalaDoPico(r, d) === escala) : []
  const lista = naEscala.length ? naEscala : doPeriodo
  const pico = lista.reduce((x, y) => (y.pico_m > x.pico_m ? y : x))
  const esc = escalaDoPico(pico, d)
  let posicao = ''
  if (escala && esc === escala) {
    const rank = [...base].sort((x, y) => y.pico_m - x.pico_m).findIndex((r) => r === pico) + 1
    posicao = ` — ${rank === 1 ? 'a maior' : `a ${ORDINAL(rank)} maior`} das ${base.length} cheias registradas nessa escala`
  }
  return `• ${c.nome}: ${m(pico.pico_m)} em ${dataBR(pico.data)}, ${NOME_ESCALA[esc]}${posicao}.`
}

function compararCidades(e: Extraido, d: Dados): Resposta {
  const titulo = e.ano ? `O maior pico registrado em ${e.mes ? mesBR(mesIso(e.ano, e.mes)) : e.ano} em cada cidade:` : 'A maior cheia registrada em cada cidade:'
  return {
    intencao: 'comparacao',
    texto: [
      titulo,
      linhaComparacao(e.cidade!, e, d),
      linhaComparacao(e.cidade2!, e, d),
      'Não dá para dizer onde foi "maior" pelos metros: cada cidade tem a sua régua, com zero próprio, e metros de réguas diferentes não se comparam. O que dá para comparar é a posição de cada cheia na história da própria cidade.',
    ].join('\n'),
  }
}

// ---------------------------------------------------------------- média dos picos
// "Média dos picos de Blumenau desde 2000" — só numa escala (a régua, quando há), e diz
// quantos ficaram de fora. É a média dos PICOS registrados, não do nível do rio.
function mediaDosPicos(e: Extraido, d: Dados): Resposta {
  if (!e.cidade) return { intencao: 'media', texto: semCidade(d), falha: faltou('faltou_cidade', e) }
  const cidade = e.cidade
  if (VARIAS_REGUAS[cidade.id])
    return { intencao: 'media', texto: `${VARIAS_REGUAS[cidade.id]}: por isso o site não tira média dos picos de ${cidade.nome}. Cada estação tem o seu zero.` }
  const t = e.t
  let de = -Infinity
  let ate = Infinity
  let periodo = ''
  const desde = t.match(/\b(desde|a partir de|depois de|apos)\s+(o ano\s+(de\s+)?)?(1[89]\d{2}|20\d{2})\b/)
  const antes = t.match(/\b(ate|antes de)\s+(o ano\s+(de\s+)?)?(1[89]\d{2}|20\d{2})\b/)
  const decada = t.match(/\b(decada de|anos)\s+(1[89]\d0|20\d0)\b/)
  if (decada?.[2]) {
    de = parseInt(decada[2], 10)
    ate = de + 9
    periodo = ` nos anos ${de}`
  } else if (desde?.[4] || antes?.[4]) {
    if (desde?.[4]) de = parseInt(desde[4], 10) + (desde[1] === 'depois de' || desde[1] === 'apos' ? 1 : 0)
    if (antes?.[4]) ate = parseInt(antes[4], 10) - (antes[1] === 'antes de' ? 1 : 0)
    periodo = `${desde?.[4] ? ` desde ${de}` : ''}${antes?.[4] ? ` até ${ate}` : ''}`
  } else if (e.ano) {
    de = ate = e.ano
    periodo = ` em ${e.ano}`
  }
  const regs = d.enchentes.eventos.filter((r) => {
    if (r.cidade !== cidade.id) return false
    const ano = parseInt(r.data.slice(0, 4), 10)
    return ano >= de && ano <= ate
  })
  if (!regs.length) return { intencao: 'media', texto: `O site não tem pico registrado de ${cidade.nome}${periodo}.` }
  const { escala, base } = contarNaEscala(regs, -Infinity, d, false)
  if (!escala || !base.length)
    return {
      intencao: 'media',
      texto: `Os picos de ${cidade.nome}${periodo} estão em escalas diferentes (régua, IBGE, ANA ou sem referência), e nenhuma delas é a régua de hoje: por isso o site não tira uma média só.`,
    }
  const valores = base.map((r) => r.pico_m)
  const media = valores.reduce((s, x) => s + x, 0) / valores.length
  const fora = regs.length - base.length
  return {
    intencao: 'media',
    texto: [
      `Média dos ${base.length} picos de ${cidade.nome} ${NOME_ESCALA[escala]}${periodo}: ${m(Math.round(media * 100) / 100)} (o menor, ${m(Math.min(...valores))}; o maior, ${m(Math.max(...valores))}).`,
      fora ? `${fora} pico(s) em outra escala ficaram fora da conta.` : '',
      NOTA_LISTA_ESPARSA[cidade.id] ? NOTA_LISTA_ESPARSA[cidade.id]!.replace('que passaram desta cota ', '') : '',
      'É a média dos picos das cheias registradas, não do nível do rio no dia a dia.',
      fonteDe(base),
    ]
      .filter(Boolean)
      .join('\n'),
  }
}

// ---------------------------------------------------------------- cotas da Defesa Civil
// "Qual a cota de alerta de Blumenau?" — a escada de faixas da cidade, na régua dela, com
// o NOME que a Defesa Civil local usa (D6: "Alerta Máximo" em Blumenau, "Prontidão" em
// Ilhota). Marca fora da escada (ex.: Timbó, só gatilho do plano) não vira faixa aqui.
const ESCADA: [string, string][] = [
  ['monitoramento', 'Monitoramento'],
  ['atencao', 'Atenção'],
  ['alerta', 'Alerta'],
  ['inundacao', 'Inundação'],
  ['emergencia', 'Emergência'],
]
/** Gaspar publica a legenda como "maior que": a faixa começa ACIMA do número. */
const LEGENDA_ACIMA_DE = new Set(['gaspar'])
const PALAVRA_COTA_DC =
  /\b(cotas?|niveis?|nivel|faixas?|escala)\b.{0,40}\b(alerta|atencao|emergencia|inundacao|observacao|prontidao|monitoramento|defesa civil)\b|\b(alerta|atencao|emergencia|prontidao)\b.{0,25}\b(comeca|a partir)\b|\ba partir de quantos metros\b/

function cotasDaCidade(e: Extraido, d: Dados): Resposta {
  if (!e.cidade) {
    const comRegua = [...new Set(Object.values(d.estacoes.rios).flatMap((r) => r.cidades.map((c) => c.nome)))]
    return {
      intencao: 'cotas',
      texto: `Não achei a cidade na pergunta. As cidades com régua no site são: ${comRegua.join(', ')}. Ex.: "qual a cota de alerta de Blumenau?"`,
      falha: faltou('faltou_cidade', e),
    }
  }
  const cidade = Object.values(d.estacoes.rios)
    .flatMap((r) => r.cidades)
    .find((c) => c.id === e.cidade!.id)
  if (!cidade) return { intencao: 'cotas', texto: `${e.cidade.nome} não tem régua de rio neste site, então não há cotas de lá.` }
  if (VARIAS_REGUAS[cidade.id])
    return { intencao: 'cotas', texto: `${VARIAS_REGUAS[cidade.id]}: cada régua tem as suas cotas. Elas estão na página de ${cidade.nome}, régua por régua.` }
  const cotas = cidade.cotas_m ?? {}
  const nomes = cidade.cotas_nomes_na_fonte ?? {}
  const degraus = ESCADA.filter(([k]) => typeof cotas[k] === 'number')
  const aviso = cidade.cotas_aviso_publico ? `\n${corta(cidade.cotas_aviso_publico, 400)}` : ''
  if (!degraus.length)
    return {
      intencao: 'cotas',
      texto: `O site não tem cotas de faixa da Defesa Civil para ${cidade.nome}.${aviso}${/199/.test(aviso) ? '' : '\nEm cheia, siga a Defesa Civil: ligue 199.'}`,
    }
  const inicio = LEGENDA_ACIMA_DE.has(cidade.id) ? 'acima de' : 'a partir de'
  const linhas = degraus.map(([k, padrao]) => `• ${nomes[k] ?? padrao}: ${inicio} ${m(cotas[k]!)}`)
  const conferida = cidade.cotas_verificado === true ? '' : '\nAtenção: essas cotas ainda não foram conferidas pelo projeto na fonte oficial.'
  const fonte = cidade.fonte_cotas ? `\nFonte: ${corta(cidade.fonte_cotas, 200)}` : ''
  return {
    intencao: 'cotas',
    texto:
      `Cotas da Defesa Civil para o rio em ${cidade.nome}, na régua da cidade:\n${linhas.join('\n')}${conferida}${aviso}${fonte}\n` +
      'Cada cidade tem a sua régua: esses metros não se comparam com os de outra cidade. Em cheia, siga a Defesa Civil: ligue 199.',
  }
}

function ruaHistorico(e: Extraido, d: Dados, termo: string | null = termoDaRua(e)): Resposta {
  if (!e.cidade)
    return {
      intencao: 'rua_historico',
      texto: 'Diga a rua e a cidade, por exemplo: "quantas cheias passaram da cota da Rua São Rafael em Blumenau?"',
      falha: faltou('faltou_cidade', e),
    }
  if (!d.cotasRuas) return { intencao: 'rua_historico', texto: 'As cotas de rua ainda estão carregando. Tente de novo em instantes.' }
  const cidade = e.cidade
  const comCotas = cidadesComCotas(d.cotasRuas)
  if (!comCotas.includes(cidade.id)) {
    const nomes = comCotas.map((id) => cidadesConhecidas(d).find((c) => c.id === id)?.nome ?? id)
    return {
      intencao: 'rua_historico',
      texto: `Ainda não há cota de rua levantada para ${cidade.nome}. Isso não quer dizer que as ruas de lá não alagam. As cidades com cotas são: ${nomes.join(', ')}.`,
    }
  }
  if (!termo)
    return { intencao: 'rua_historico', texto: `Diga o nome da rua em ${cidade.nome}, por exemplo: "quantas cheias passaram da cota da Rua São Rafael em Blumenau?"` }
  // A busca do site casa por pedaço ("lino" acha "Wandelino"). Se algum ponto casa
  // pela palavra inteira, o chat mostra só esses; senão, os de pedaço.
  const todas = buscar(d.cotasRuas, cidade.id, termo)
  const inteira = new RegExp(`(^|\\s)${termo.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(\\s|$)`)
  const exatas = todas.filter((c) => inteira.test(norm(c.rua)))
  const achadas = exatas.length ? exatas : todas
  if (!achadas.length)
    return {
      intencao: 'rua_historico',
      texto: `Nenhuma rua com "${termo}" entre as levantadas em ${cidade.nome}. Isso não quer dizer que ela não alaga: a lista é das cotas que a Defesa Civil publicou, e não é completa.`,
    }

  const daCidade = d.enchentes.eventos.filter((r) => r.cidade === cidade.id)
  const linhas: string[] = []
  for (const c of achadas.slice(0, MAX_RUAS_CHAT)) {
    const nome = `${nomeCompleto(c)}${c.bairro ? `, ${c.bairro}` : ''}`
    if (c.cota_m === null) {
      linhas.push(`• ${nome}: a fonte cita o ponto, mas não publica a cota.`)
      continue
    }
    if (!podeAfirmarAlcance(c)) {
      linhas.push(`• ${nome}: cota ${m(c.cota_m)}, marcada como não conferida — fica fora da conta.`)
      continue
    }
    const k = contarNaEscala(daCidade, c.cota_m, d, true)
    if (!k.escala) {
      linhas.push(`• ${nome}: cota ${m(c.cota_m)}. Os picos de ${cidade.nome} não estão na régua de hoje, que é a régua da cota, então não dá para contar.`)
      continue
    }
    const ultima = k.acima[k.acima.length - 1]
    linhas.push(
      `• ${nome}: cota ${m(c.cota_m)}. O rio chegou a essa cota em ${k.acima.length} das ${k.base.length} cheias registradas na régua de ${cidade.nome}` +
        (ultima ? `; a mais recente, ${dataBR(ultima.data)} (${m(ultima.pico_m)}).` : '.') +
        (k.fora.size ? ` ${[...k.fora.values()].reduce((a, b) => a + b, 0)} pico(s) em outra escala ficaram fora da conta.` : ''),
    )
  }
  if (achadas.length > MAX_RUAS_CHAT)
    linhas.push(`Mais ${achadas.length - MAX_RUAS_CHAT} ponto(s) casaram com "${termo}". Escreva o nome com mais letras para reduzir.`)

  return {
    intencao: 'rua_historico',
    texto: [
      `Cotas de rua em ${cidade.nome}, comparadas com os picos registrados na régua da cidade:`,
      linhas.join('\n'),
      'Isso NÃO quer dizer que a rua alagou todas essas vezes: a cota é de hoje (obra e aterro mudam o número com o tempo), é de um ponto e não da rua inteira, e a lista de cheias do site não é completa.',
      NOTA_LISTA_ESPARSA[cidade.id] ?? '',
      'Fonte: cotas de rua da Defesa Civil do município (aba "Minha rua" da cidade) e picos de enchentes.json.',
    ]
      .filter(Boolean)
      .join('\n'),
  }
}

function eventoAtlas(e: Extraido, d: Dados): { rio: string; ev: EventoAtlas | undefined; outros: EventoAtlas[] } {
  const rio = e.rio ?? 'itajai-acu'
  const evs = d.atlas[rio]?.eventos ?? []
  if (e.mes) return { rio, ev: evs.find((x) => x.mes === mesIso(e.ano ?? 0, e.mes ?? 0)), outros: [] }
  const doAno = evs.filter((x) => x.mes.startsWith(String(e.ano))).sort((a, b) => b.n_municipios - a.n_municipios)
  return { rio, ev: doAno[0], outros: doAno.slice(1) }
}
const nomeRio = (d: Dados, rio: string) => d.estacoes.rios[rio]?.nome ?? rio
const mesBR = (ym: string) => dataBR(ym)

function danosAtlas(e: Extraido, d: Dados): Resposta {
  if (!e.ano)
    return {
      intencao: 'atlas',
      texto: 'Diga o ano (e, se souber, o mês). Ex.: "quais cidades tiveram desastre em setembro de 2011?"',
      falha: faltou('faltou_ano', e),
    }
  if (e.ano < 1991)
    return {
      intencao: 'atlas',
      texto: `O site não tem número de mortos, desabrigados ou desalojados de ${e.ano}: os danos vêm do Atlas Digital de Desastres, que cobre 1991 a 2025. Para ${e.ano}, o site só tem a altura do rio, quando há registro (pergunte "cheias de ${e.cidade?.nome ?? 'Blumenau'} em ${e.ano}").`,
    }
  const { rio, ev, outros } = eventoAtlas(e, d)
  if (!ev)
    return {
      intencao: 'atlas',
      texto: `O Atlas Digital de Desastres não tem registro de inundação, enxurrada ou alagamento no ${nomeRio(d, rio)} em ${e.mes ? mesBR(mesIso(e.ano, e.mes)) : e.ano}. O Atlas cobre 1991 a 2025.`,
    }
  let regs = ev.registros
  const cidade = e.cidade
  if (cidade && cidade.rio === rio) regs = regs.filter((x) => norm(x.municipio) === norm(cidade.nome))
  const t = ev.totais
  const linhas = regs.map((x) => {
    const danos = [x.mortos ? `${x.mortos} morto(s)` : '', x.desabrigados ? `${num(x.desabrigados)} desabrigados` : '', x.desalojados ? `${num(x.desalojados)} desalojados` : ''].filter(Boolean)
    return `• ${x.municipio} — ${dataBR(x.data_evento)}, ${x.tipologia.toLowerCase()}${danos.length ? ` (${danos.join(', ')})` : ''}`
  })
  return {
    intencao: 'atlas',
    texto: [
      `Em ${mesBR(ev.mes)}, o Atlas registra ${ev.n_municipios} município(s) do ${nomeRio(d, rio)} com ${ev.tipologias.join('/').toLowerCase()}:`,
      linhas.join('\n'),
      `Totais do mês: ${t.mortos} morto(s), ${num(t.desabrigados)} desabrigados, ${num(t.desalojados)} desalojados.`,
      'Ressalva: a tipologia é a que cada município declarou (novembro de 2008 aparece como enxurrada), e os totais somam registros, então a mesma população pode ser contada duas vezes.',
      outros.length ? `O mesmo ano tem outros meses com registro: ${outros.map((o) => mesBR(o.mes)).join(', ')}.` : '',
      'Fonte: Atlas Digital de Desastres no Brasil (MIDR), v1.1 de 06/08/2026.',
    ]
      .filter(Boolean)
      .join('\n'),
  }
}

function chuvaAntes(e: Extraido, d: Dados): Resposta {
  if (!e.ano)
    return {
      intencao: 'chuva',
      texto: 'Diga o ano (e o mês, se souber) da enchente. Ex.: "quanto choveu antes da enchente de novembro de 2008?"',
      falha: faltou('faltou_ano', e),
    }
  if (e.ano < 2006) return { intencao: 'chuva', texto: 'Os dados de chuva do site (estações automáticas do INMET) começam em 2006. Para antes disso não há dado de chuva no site.' }
  const { rio, ev, outros } = eventoAtlas(e, d)
  const c = ev && d.chuvaEventos.eventos[ev.id]
  if (!ev || !c)
    return {
      intencao: 'chuva',
      texto: `Não tenho um evento do Atlas no ${nomeRio(d, rio)} ${e.mes ? `em ${mesBR(mesIso(e.ano, e.mes))}` : `em ${e.ano}`} para ancorar a chuva.`,
    }
  const nomes = d.chuvaEventos.estacoes
  const janela = (v: Record<string, JanelaChuva>, k: string) => {
    const j = v[k]
    if (!j || j.mm == null) return 'sem dado'
    return `${num(j.mm, 1)} mm${j.cobertura < 1 ? ` (cobertura ${Math.round(j.cobertura * 100)}%)` : ''}`
  }
  const linhas = Object.entries(c.estacoes).map(([cod, v]) => `• ${nomes[cod]?.nome ?? cod} (${cod}): 72 h ${janela(v, '72h')}; 7 dias ${janela(v, '7d')}`)
  const sem = Object.keys(nomes)
    .filter((k) => !(k in c.estacoes))
    .map((k) => nomes[k]?.nome ?? k)
  const cidade = e.cidade
  const temEstacao = cidade && Object.values(nomes).some((x) => norm(x.nome) === norm(cidade.nome))
  return {
    intencao: 'chuva',
    texto: [
      cidade && !temEstacao ? `Não há estação do INMET em ${cidade.nome}. Abaixo, as estações do INMET da bacia, que servem só como referência regional.` : '',
      `Chuva medida pelo INMET antes da cheia de ${mesBR(ev.mes)} no ${nomeRio(d, rio)}, até o fim de ${dataBR(c.data_ancora)} (dia com mais municípios atingidos no Atlas):`,
      linhas.join('\n'),
      sem.length ? `Sem dado válido nesse período: ${sem.join(', ')} (estação fora do ar ou pluviômetro travado).` : '',
      'Cobertura abaixo de 100% quer dizer que faltaram horas, então o valor real pode ser maior.',
      outros.length ? `O mesmo ano tem outros meses com cheia: ${outros.map((o) => mesBR(o.mes)).join(', ')}.` : '',
      'Fonte: INMET, estações automáticas (dados brutos, não consistidos).',
    ]
      .filter(Boolean)
      .join('\n'),
  }
}

// Tempo de descida entre QUALQUER par de cidades do site (pedido do Jefferson, 04/10/2026).
// O número vem de `caminho()` (logica/transito.ts) — o MESMO encadeamento da tela e do bot,
// travado pelo gabarito `data/transito-esperado.json`. Sem caminho, o chat diz POR QUÊ
// (outro rio, afluente, cabeceiras paralelas, trecho em estudo, cidade sem tempo medido)
// e nunca inventa número.
const NOME_RIO: Record<string, string> = { 'itajai-acu': 'Itajaí-Açu', 'itajai-mirim': 'Itajaí-Mirim' }
const NOTA_TRANSITO = 'Cada cheia é diferente; isso é uma referência de estudo, não uma previsão.'

function faixaTransito(c: Pick<Caminho, 'horasMin' | 'horasMax'>, direto: boolean): string {
  if (c.horasMin !== c.horasMax) return `de ${num(c.horasMin, 1)} a ${num(c.horasMax, 1)} h`
  return direto ? `cerca de ${num(c.horasMin, 1)} h (valor único na fonte, é aproximação)` : `cerca de ${num(c.horasMin, 1)} h (soma de valores únicos, é aproximação)`
}

function textoCaminho(c: Caminho, nome: (id: string) => string): string {
  const conta = c.direto
    ? ''
    : `\nSoma dos trechos do estudo: ${c.trechos.map((t) => `${nome(t.de)} → ${nome(t.para)} (${faixaTransito({ horasMin: t.horas_min, horasMax: t.horas_max }, true).replace(/ \(.*\)$/, '')})`).join(' + ')}. Somar trechos acumula a incerteza.`
  const fontes = [...new Set(c.trechos.map((t) => String(t.fonte ?? 'transito.json').replace(/\.+$/, '')))]
  return `Da passagem do pico em ${nome(c.trechos[0]!.de)} até ${nome(c.trechos.at(-1)!.para)}: ${faixaTransito(c, c.direto)}, ${conf(c.confianca)}.${conta}\nFonte: ${fontes.join('; ')}.\n${NOTA_TRANSITO}`
}

function transito(e: Extraido, d: Dados): Resposta {
  const rios = Object.entries(d.estacoes.rios)
  const comRegua = rios.flatMap(([, r]) => r.cidades.map((c) => c.nome)).filter((x, i, l) => l.indexOf(x) === i)
  if (!e.cidade || !e.cidade2)
    return {
      intencao: 'transito',
      texto: `Diga as duas cidades. Ex.: "quanto tempo a cheia leva de Rio do Sul até Blumenau?". Cidades com régua no site: ${comRegua.join(', ')}.`,
      falha: faltou('faltou_cidade', e),
    }
  const a = e.cidade
  const b = e.cidade2
  const conhecidas = cidadesConhecidas(d)
  const nome = (id: string) => conhecidas.find((c) => c.id === id)?.nome ?? id
  const riosDe = (id: string) => rios.filter(([, r]) => r.cidades.some((c) => c.id === id)).map(([k]) => k)
  const resp = (texto: string): Resposta => ({ intencao: 'transito', texto })

  for (const x of [a, b])
    if (!riosDe(x.id).length)
      return resp(`${x.nome} não tem régua de rio neste site, então não há tempo de descida para ela. As cidades com régua são: ${comRegua.join(', ')}.`)

  const trechos = d.transito.trechos as unknown as Trecho[]
  const experimentais = d.transito.trechos_experimentais ?? []
  const comuns = riosDe(a.id).filter((r) => riosDe(b.id).includes(r))

  // 1. Há caminho, na ordem pedida ou na contrária (a água só desce).
  for (const rio of comuns) {
    const ida = caminho(trechos, rio, a.id, b.id)
    if (ida) return resp(textoCaminho(ida, nome))
    const volta = caminho(trechos, rio, b.id, a.id)
    if (volta) return resp(`A cheia desce de ${b.nome} para ${a.nome}, não o contrário.\n${textoCaminho(volta, nome)}`)
  }

  // Para as explicações: o que o site TEM de cada cidade até Itajaí, na foz.
  const ateFoz = (id: string, rio: string) => {
    if (id === 'itajai') return ''
    const c = caminho(trechos, rio, id, 'itajai')
    return c ? `\nDe ${nome(id)} até Itajaí: ${faixaTransito(c, c.direto)}, ${conf(c.confianca)}.` : ''
  }

  // 2. Rios diferentes: a cheia de um não passa pelo outro.
  if (!comuns.length) {
    const [ra] = riosDe(a.id)
    const [rb] = riosDe(b.id)
    return resp(
      `${a.nome} fica no rio ${NOME_RIO[ra!] ?? ra} e ${b.nome} no ${NOME_RIO[rb!] ?? rb}: são rios diferentes, e a cheia de um não desce pelo outro. Os dois se encontram só em Itajaí, na foz.${ateFoz(a.id, ra!)}${ateFoz(b.id, rb!)}\n${NOTA_TRANSITO}`,
    )
  }

  const rio = comuns[0]!
  const topo = d.estacoes.rios[rio]?._topologia ?? {}
  const tronco = topo.tronco_sequencia ?? []
  const cabeceiras = topo.cabeceiras_paralelas ?? []
  const afluente = (id: string) => (topo.afluentes_laterais ?? []).find((x) => x.id === id)
  const pos = (id: string) => (cabeceiras.includes(id) ? -1 : tronco.indexOf(id))
  const naArvore = (id: string) => pos(id) >= 0 || cabeceiras.includes(id)

  // 3. Trecho em estudo: há medição, mas cheias pareadas de menos para dar faixa.
  const estudo = experimentais.find((t) => t.rio === rio && (t.de === a.id || t.de === b.id))
  if (estudo) {
    const [cima, baixo] = pos(a.id) <= pos(b.id) ? [a.id, b.id] : [b.id, a.id]
    const resto = baixo !== estudo.para ? caminho(trechos, rio, estudo.para, baixo) : null
    return resp(
      `O trecho ${nome(estudo.de)} → ${nome(estudo.para)} está em estudo: o site tem ${estudo.eventos_pareados_com_hora} cheia medida com hora e precisa de ${estudo.minimo_eventos_pareados} para dar uma faixa. Por isso não dá o tempo de ${nome(cima)} até ${nome(baixo)} (dados insuficientes).` +
        (resto ? `\nO que o site tem: de ${nome(estudo.para)} até ${nome(baixo)}, ${faixaTransito(resto, resto.direto)}, ${conf(resto.confianca)}.` : '') +
        `\n${NOTA_TRANSITO}`,
    )
  }

  // 4. Afluente lateral ou cidade sem posição na árvore: relógio próprio.
  for (const x of [a, b]) {
    const af = afluente(x.id)
    if (af)
      return resp(
        `${x.nome} fica no ${af.rio}, um afluente que entra no ${NOME_RIO[rio] ?? rio} perto de ${nome(af.entra_perto_de)}. A cheia ali vem da chuva da própria sub-bacia: o pico entra no rio principal, não desce por ele. Por isso o site não encadeia tempo de descida entre ${a.nome} e ${b.nome}: ele só tem tempo entre cidades do curso principal do rio.`,
      )
    if (!naArvore(x.id))
      return resp(
        `${x.nome} ainda não tem posição definida no desenho do rio (a fonte diz o rio, não onde ele encontra o ${NOME_RIO[rio] ?? rio}). Sem isso, o site não calcula tempo de descida entre ${a.nome} e ${b.nome}.`,
      )
  }

  // 5. Duas cabeceiras: rios paralelos que só se juntam em Rio do Sul.
  if (cabeceiras.includes(a.id) && cabeceiras.includes(b.id)) {
    const juncao = tronco[0] ?? 'rio-do-sul'
    const ate = (id: string) => {
      const c = caminho(trechos, rio, id, juncao)
      return c ? `\nDe ${nome(id)} até ${nome(juncao)}: ${faixaTransito(c, c.direto)}, ${conf(c.confianca)}.` : ''
    }
    return resp(
      `${a.nome} e ${b.nome} ficam em rios paralelos, que se juntam em ${nome(juncao)}: a cheia de uma não passa pela outra.${ate(a.id)}${ate(b.id)}\n${NOTA_TRANSITO}`,
    )
  }

  // 6. As duas no eixo, mas sem tempo medido: o menor trecho com tempo que contém o percurso.
  const [cima, baixo] = pos(a.id) <= pos(b.id) ? [a.id, b.id] : [b.id, a.id]
  const invertido = cima !== a.id
  const acima = [cima, ...tronco.filter((x) => pos(x) < pos(cima))].reverse()
  const abaixo = [baixo, ...tronco.filter((x) => pos(x) > pos(baixo))]
  let melhor: { u: string; v: string; c: Caminho; folga: number } | null = null
  for (const u of acima)
    for (const v of abaixo) {
      const c = caminho(trechos, rio, u, v)
      const folga = pos(cima) - pos(u) + (pos(v) - pos(baixo))
      if (c && (!melhor || folga < melhor.folga)) melhor = { u, v, c, folga }
    }
  const sentido = invertido ? `A cheia desce de ${nome(cima)} para ${nome(baixo)}, não o contrário.\n` : ''
  const semTempo = [cima, baixo].filter((id) => !trechos.some((t) => t.rio === rio && (t.de === id || t.para === id))).map(nome)
  const porque = semTempo.length ? ` (${semTempo.join(' e ')} não ${semTempo.length > 1 ? 'estão' : 'está'} na tabela de tempos do estudo JICA)` : ''
  if (melhor)
    return resp(
      `${sentido}O site não tem o tempo medido de ${nome(cima)} até ${nome(baixo)}${porque}.\nO menor trecho com tempo que passa pelas duas é de ${nome(melhor.u)} até ${nome(melhor.v)}: ${faixaTransito(melhor.c, melhor.c.direto)}, ${conf(melhor.c.confianca)}. O percurso que você perguntou é um pedaço dele; o tempo só desse pedaço não foi levantado.\n${NOTA_TRANSITO}`,
    )
  return resp(`${sentido}O site não tem tempo de descida levantado entre ${nome(cima)} e ${nome(baixo)}${porque}.`)
}

const ANA_MIRIM: Record<string, string> = { salseiro: '83892990', 'vidal ramos': '83892990', 'botuvera montante': '83892998', botuvera: '83892998', brusque: '83900000' }

function cotaAna(e: Extraido, d: Dados): Resposta {
  const est = Object.entries(ANA_MIRIM).find(([k]) => e.t.includes(k))
  if (!est || !e.ano)
    return {
      intencao: 'cota_ana',
      texto: 'Tenho cota diária da ANA no Itajaí-Mirim para Salseiro, Botuverá-Montante e Brusque. Diga a estação e o ano (e o mês). Ex.: "cota da ANA em Brusque em novembro de 2008".',
      falha: faltou(est ? 'faltou_ano' : 'faltou_cidade', e),
    }
  const codigo = est[1]
  const s = d.cotasAna?.estacoes[codigo]
  if (!s) return { intencao: 'cota_ana', texto: 'As cotas da ANA ainda estão carregando. Tente de novo em instantes.' }
  const pref = e.mes ? mesIso(e.ano, e.mes) : String(e.ano)
  let max = -1
  let dia = ''
  s.datas.forEach((dt, i) => {
    const v = s.cm[i]
    if (dt.startsWith(pref) && v != null && v > max) {
      max = v
      dia = dt
    }
  })
  const primeira = s.datas[0]
  const ultima = s.datas[s.datas.length - 1]
  if (max < 0)
    return {
      intencao: 'cota_ana',
      texto: `A estação ${s.nome} (ANA ${codigo}) não tem leitura em ${e.mes ? mesBR(pref) : e.ano}. Período disponível: ${primeira ? dataBR(primeira) : '?'} a ${ultima ? dataBR(ultima) : '?'}.`,
    }
  // O zero da 83900000 coincide com o da régua municipal de Brusque em 2019–2021 e não se
  // sabe desde quando (docs/HIDROWEB-MIRIM-2026-09-22.md). Salseiro e Botuverá-Montante não
  // são as réguas das cidades. Nada disso vira metro de régua municipal.
  return {
    intencao: 'cota_ana',
    texto: `Maior média diária na estação ${s.nome} (ANA ${codigo}) em ${e.mes ? mesBR(pref) : e.ano}: ${num(max)} cm, em ${dataBR(dia)}.\nAtenção: é a régua da ANA, não a régua da Defesa Civil da cidade — outro ponto do rio e zero próprio. Em Brusque, o zero da ANA coincide com o municipal só onde foi conferido (2019–2021); antes disso não se sabe.\nFonte: ANA/HidroWeb, média das leituras de 07h e 17h.`,
  }
}

function antecedenciaMirim(_e: Extraido, d: Dados): Resposta {
  const ev = d.picosMirim?.eventos ?? []
  const h = ev.map((x) => x.botuvera_mont?.antecedencia_h).filter((x): x is number => x != null)
  const zero = h.filter((x) => x === 0).length
  const um = h.filter((x) => x > 0 && x <= 14).length
  return {
    intencao: 'antecedencia_mirim',
    texto: `Nos ${h.length} picos de Brusque acima de 450 cm desde 1997 com dado em Botuverá-Montante, o pico lá veio na mesma leitura em ${zero} casos (menos de ~10 h antes) e uma leitura antes em ${um} casos (10 a 14 h).\nAs réguas da ANA são lidas só às 07h e às 17h, então não dá para medir em horas exatas.\nFonte: ANA/HidroWeb (83892998 e 83900000).`,
  }
}

export const EXEMPLOS = [
  'Qual foi a maior cheia de Rio do Sul?',
  'As 5 maiores cheias de Blumenau',
  'Cheias de Gaspar em 2011',
  'Quantas cheias passaram de 10 m em Rio do Sul?',
  'Quantas cheias chegaram à cota da Rua São Rafael em Blumenau?',
  'Quais cidades tiveram desastre em setembro de 2011?',
  'Quanto choveu antes da enchente de novembro de 2008?',
  'Quanto tempo a cheia leva de Rio do Sul até Blumenau?',
  'Cota da ANA em Brusque em novembro de 2008',
]

// ---------------------------------------------------------------- roteador
// A ordem importa: a primeira intenção que casar vence. Gatilho amplo demais
// "rouba" pergunta de outra intenção — os testes travam a ordem atual.
export function responder(pergunta: string, d: Dados): Resposta {
  const t0 = norm(pergunta)
  if (pedeAgora(pergunta)) return { intencao: 'agora', texto: TEXTO_ALERTA }
  if (t0.length < 3 || /^(oi|ola|ajuda|help|o que voce faz|como funciona)\b/.test(t0))
    return { intencao: 'ajuda', texto: 'Respondo perguntas sobre cheias que já aconteceram, com os dados deste site. Veja alguns exemplos:', sugestoes: EXEMPLOS }

  const e = extrair(pergunta, d)
  const t = e.t
  if (PALAVRA_RUA.test(t) && (e.cidade || /\b(quantas|quantos|alag|cheia|enchente|cota)/.test(t))) return ruaHistorico(e, d)
  if (PALAVRA_COTA_DC.test(t) && !/\bquant(as|os) (cheias|vezes|enchentes|picos)\b/.test(t)) return cotasDaCidade(e, d)
  if (/\b(quanto tempo|quantas horas|demora|demorar|leva|levar|chega|chegar|desce|descer|transito)\b/.test(t) && (e.cidade2 || (/\b(quanto tempo|quantas horas)\b/.test(t) && /\bate\b/.test(t))))
    return transito(e, d)
  if (/\bchov|chuva/.test(t)) return chuvaAntes(e, d)
  if (/\b(antecedencia|antes de brusque|chega em brusque)\b/.test(t) || (t.includes('botuvera') && t.includes('brusque') && /\bpico/.test(t))) return antecedenciaMirim(e, d)
  if (/\b(ana|cota|cm)\b/.test(t) && Object.keys(ANA_MIRIM).some((k) => t.includes(k))) return cotaAna(e, d)
  if (/\b(desabrigad|desalojad|mort|morre|morreu|morreram|obito|vitima|atingid|desastre|cidades|municipios|atlas)/.test(t)) return danosAtlas(e, d)
  if (e.cidade && e.cidade2 && e.cidade.id !== e.cidade2.id && PEDE_COMPARACAO.test(t) && PEDE_MAIOR.test(t)) return compararCidades(e, d)
  if (/\bmedia\b/.test(t)) return mediaDosPicos(e, d)
  if (/\b(quantas|quantos|quantas vezes)\b/.test(t) && e.nivel != null) return contarAcima(e, d)
  if (/\b(maior|maiores|recorde|pior|piores|mais alta|maxima)\b/.test(t) && !e.ano) return maioresCheias(e, d)
  if (e.ano && e.cidade) return cheiasDoPeriodo(e, d)
  if (e.cidade) return { ...maioresCheias({ ...e, n: e.n ?? 5 }, d), palpite: true }
  if (e.ano) return { ...danosAtlas(e, d), palpite: true }
  return {
    intencao: 'nao_entendi',
    texto: 'Não entendi a pergunta. Eu respondo só sobre o histórico das cheias e enchentes do Vale do Itajaí, usando os dados do site. Tente um destes formatos:',
    sugestoes: EXEMPLOS,
    falha: { motivo: 'sem_intencao' },
  }
}

// ---------------------------------------------------------------- resposta a partir de uma classificação
// Piloto do classificador (decisão do Jefferson de 05/10/2026, `docs/PILOTO-CLASSIFICADOR.md`):
// quando o roteador acima não entende (ou só palpita), uma IA CLASSIFICA a pergunta numa
// destas intenções, com os parâmetros. A IA não escolhe ferramenta e não escreve resposta:
// o servidor confere tudo contra listas fechadas, e o texto sai daqui, das MESMAS funções
// do roteador. Nenhum número vem da IA.

export const INTENCOES = [
  'maiores_cheias',
  'cheias_periodo',
  'contar_acima',
  'atlas',
  'chuva',
  'transito',
  'cota_ana',
  'antecedencia_mirim',
  'rua_historico',
  'cotas',
  'comparacao',
  'media',
] as const
export type Intencao = (typeof INTENCOES)[number]

export type Parametro = 'cidade' | 'cidade2' | 'ano' | 'nivel_m' | 'rua'

/** Sem estes, a pergunta não é respondida: a tela pede o que faltou. */
export const OBRIGATORIOS: Record<Intencao, Parametro[]> = {
  maiores_cheias: ['cidade'],
  cheias_periodo: ['cidade', 'ano'],
  contar_acima: ['cidade', 'nivel_m'],
  atlas: ['ano'],
  chuva: ['ano'],
  transito: ['cidade', 'cidade2'],
  cota_ana: ['cidade', 'ano'],
  antecedencia_mirim: [],
  rua_historico: ['cidade', 'rua'],
  cotas: ['cidade'],
  comparacao: ['cidade', 'cidade2'],
  media: ['cidade'],
}

/** Cidades com cota diária da ANA no Itajaí-Mirim (as chaves de `ANA_MIRIM`). */
export const CIDADES_COTA_ANA = ['vidal-ramos', 'botuvera', 'brusque'] as const

/** Já conferida pelo servidor: intenção da lista, cidade do cadastro, ano no intervalo. */
export interface Classificacao {
  intencao: Intencao
  cidade: string | null
  cidade2: string | null
  rio: 'itajai-acu' | 'itajai-mirim' | null
  ano: number | null
  /** Último ano de um intervalo ("desde 2000" → ano 2000, ano_final o ano corrente). */
  ano_final: number | null
  mes: number | null
  nivel_m: number | null
  quantidade: number | null
  rua: string | null
}

/** Os parâmetros obrigatórios da intenção que vieram vazios. */
export function faltando(c: Classificacao): Parametro[] {
  return OBRIGATORIOS[c.intencao].filter((p) => c[p] == null || c[p] === '')
}

const NOME_PARAMETRO: Record<Parametro, string> = {
  cidade: 'a cidade',
  cidade2: 'a segunda cidade',
  ano: 'o ano',
  nivel_m: 'o nível, em metros',
  rua: 'o nome da rua',
}
export const textoParametros = (ps: Parametro[]) => ps.map((p) => NOME_PARAMETRO[p]).join(' e ')

function extraidoDe(c: Classificacao, d: Dados): Extraido {
  const lista = cidadesConhecidas(d)
  const cidade = lista.find((x) => x.id === c.cidade)
  const cidade2 = lista.find((x) => x.id === c.cidade2)
  const ano2 = c.ano_final != null && c.ano_final !== c.ano ? c.ano_final : undefined
  // Só a média lê período do texto ("desde", "até"): o texto aqui é montado, nunca o da pessoa.
  const t = c.intencao === 'media' && c.ano != null && ano2 != null ? `desde ${c.ano} ate ${ano2}` : c.intencao === 'cota_ana' && cidade ? cidade.chave : ''
  return {
    t,
    ...(cidade ? { cidade } : {}),
    ...(cidade2 ? { cidade2 } : {}),
    ...(c.rio ?? cidade?.rio ? { rio: c.rio ?? cidade?.rio } : {}),
    ...(c.ano != null ? { ano: c.ano } : {}),
    ...(ano2 != null ? { ano2 } : {}),
    ...(c.mes != null ? { mes: c.mes } : {}),
    ...(c.nivel_m != null ? { nivel: c.nivel_m } : {}),
    ...(c.quantidade != null ? { n: c.quantidade } : {}),
  }
}

/** A resposta do motor para uma classificação já conferida. */
export function responderPorIntencao(c: Classificacao, d: Dados): Resposta {
  const e = extraidoDe(c, d)
  switch (c.intencao) {
    case 'maiores_cheias':
      return maioresCheias({ ...e, n: e.n ?? 1 }, d)
    case 'cheias_periodo':
      return cheiasDoPeriodo(e, d)
    case 'contar_acima':
      return contarAcima(e, d)
    case 'atlas':
      return danosAtlas(e, d)
    case 'chuva':
      return chuvaAntes(e, d)
    case 'transito':
      return transito(e, d)
    case 'cota_ana':
      return cotaAna(e, d)
    case 'antecedencia_mirim':
      return antecedenciaMirim(e, d)
    case 'rua_historico':
      return ruaHistorico(e, d, c.rua ? norm(c.rua).replace(PALAVRA_RUA, ' ').replace(/\s+/g, ' ').trim() || null : null)
    case 'cotas':
      return cotasDaCidade(e, d)
    case 'comparacao':
      return compararCidades(e, d)
    case 'media':
      return mediaDosPicos(e, d)
  }
}

/** "Entendi: …" — o que a tela mostra antes da resposta, para a pessoa conferir. */
export function descreverEntendido(c: Classificacao, d: Dados): string {
  const lista = cidadesConhecidas(d)
  const nome = (id: string | null) => lista.find((x) => x.id === id)?.nome ?? ''
  const a = nome(c.cidade)
  const b = nome(c.cidade2)
  const quando =
    c.ano == null
      ? ''
      : c.mes != null
        ? `${MESES_EXIBIR[c.mes - 1]} de ${c.ano}`
        : c.ano_final != null && c.ano_final !== c.ano
          ? `${c.ano} a ${c.ano_final}`
          : String(c.ano)
  const em = quando ? ` em ${quando}` : ''
  const rioNome = c.rio ? (NOME_RIO[c.rio] ?? c.rio) : ''
  switch (c.intencao) {
    case 'maiores_cheias':
      return c.quantidade && c.quantidade > 1 ? `as ${c.quantidade} maiores cheias de ${a}` : `a maior cheia de ${a}`
    case 'cheias_periodo':
      return `as cheias de ${a}${em}`
    case 'contar_acima':
      return `quantas cheias de ${a} chegaram a ${m(c.nivel_m ?? 0)} ou mais`
    case 'atlas':
      return `os danos das cheias${em}${a ? ` em ${a}` : rioNome ? ` no ${rioNome}` : ''}`
    case 'chuva':
      return `quanto choveu antes da cheia${em}${rioNome ? ` no ${rioNome}` : ''}`
    case 'transito':
      return `quanto tempo a cheia leva de ${a} até ${b}`
    case 'cota_ana':
      return `a cota da ANA em ${a}${em}`
    case 'antecedencia_mirim':
      return 'a antecedência do pico em Botuverá antes de Brusque'
    case 'rua_historico':
      return `quantas cheias passaram da cota da rua "${c.rua ?? ''}" em ${a}`
    case 'cotas':
      return `as cotas da Defesa Civil para o rio em ${a}`
    case 'comparacao':
      return `a comparação das cheias de ${a} e ${b}${em}`
    case 'media':
      return `a média dos picos de ${a}${em}`
  }
}
