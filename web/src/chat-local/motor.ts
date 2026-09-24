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

export interface RegistroCheia {
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
  transito: { trechos: TrechoTransito[] }
  estacoes: { rios: Record<string, { nome: string; cidades: { id: string; nome: string }[] }> }
  /** "itajai-acu" | "itajai-mirim" → recorte do Atlas de Desastres. */
  atlas: Record<string, { eventos: EventoAtlas[] }>
  chuvaEventos: { estacoes: Record<string, { nome: string }>; eventos: Record<string, EventoChuva> }
  cotasAna?: { estacoes: Record<string, { nome: string; datas: string[]; cm: number[] }> }
  picosMirim?: { eventos: { botuvera_mont?: { antecedencia_h: number } }[] }
}

export interface Resposta {
  intencao: string
  texto: string
  sugestoes?: string[]
}

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
const AGORA = [
  /\b(agora|hoje|hj|amanha|neste momento|nesse momento|esta noite|essa noite|esta semana|essa semana|proximas horas)\b/,
  /\b(vai|vao|pode|deve)\s+(encher|subir|transbordar|alagar|inundar|chover|baixar|descer)\b/,
  /\b(esta|ta|estao|tao)\s+(enchendo|subindo|alagando|transbordando|chovendo)\b/,
  /\b(devo|preciso|precisamos|tenho que|temos que|e para|e pra)\s+(sair|evacuar|deixar|subir os moveis|tirar o carro)\b/,
  /\b(nivel|cota|situacao)\s+(atual|de agora|de hoje)\b/,
  /\b(previsao|alerta)\b/,
  /\b(estou|to|moro)\b.{0,40}\b(ilhad|alagad|cercad)/,
]
export const TEXTO_ALERTA =
  'Eu só respondo sobre cheias que já aconteceram, com os dados deste site. Não sei o que está acontecendo no rio agora. ' +
  'Para a situação atual, previsão ou para decidir se deve sair de casa, siga a Defesa Civil: ligue 199 (ou 193, Bombeiros, em emergência). ' +
  'O nível ao vivo das réguas está na página de cada rio, com a fonte e a hora da leitura.'

// ---------------------------------------------------------------- extração
interface CidadeConhecida {
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

function cidadesConhecidas(d: Dados): CidadeConhecida[] {
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
  let resto = ` ${t} `
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
  return `Tenho picos históricos para: ${nomes.join(', ')}. Diga a cidade.`
}

// Por que a cidade não tem pico, quando o motivo é conhecido e não é só "falta fonte".
const MOTIVO_SEM_PICO: Record<string, string> = {
  itajai:
    'Itajaí tem onze réguas da Defesa Civil, cada uma com seu zero, e as mais perto da foz sobem e descem com a maré. Um número só não é "o nível de Itajaí": cada pico precisa dizer de qual régua é, e ainda não há fonte que dê isso para as cheias antigas.',
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
      MOTIVO_SEM_PICO[cidade.id] ?? '',
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

function maioresCheias(e: Extraido, d: Dados): Resposta {
  if (!e.cidade) return { intencao: 'maiores_cheias', texto: semCidade(d) }
  const cidade = e.cidade
  const regs = d.enchentes.eventos.filter((r) => r.cidade === cidade.id)
  if (!regs.length) return semPicoNaCidade(cidade, d)
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
      `São ${regs.length} picos registrados para ${cidade.nome}, em metros na régua local.`,
      ressalvas(top),
      fonteDe(top),
    ]
      .filter(Boolean)
      .join('\n'),
  }
}

function cheiasDoPeriodo(e: Extraido, d: Dados): Resposta {
  if (!e.cidade || e.ano == null) return { intencao: 'cheias_periodo', texto: semCidade(d) }
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

function contarAcima(e: Extraido, d: Dados): Resposta {
  if (!e.cidade || e.nivel == null) return { intencao: 'contar_acima', texto: 'Diga a cidade e o nível, por exemplo: "quantas cheias passaram de 10 m em Rio do Sul?"' }
  const cidade = e.cidade
  const nivel = e.nivel
  const regs = d.enchentes.eventos.filter((r) => r.cidade === cidade.id && r.pico_m >= nivel).sort((a, b) => a.data.localeCompare(b.data))
  return {
    intencao: 'contar_acima',
    texto: [`${cidade.nome} tem ${regs.length} pico(s) registrado(s) de ${m(nivel)} ou mais, na régua local.`, regs.map(linhaCheia).join('\n'), ressalvas(regs), regs.length ? fonteDe(regs) : '']
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
  if (!e.ano) return { intencao: 'atlas', texto: 'Diga o ano (e, se souber, o mês). Ex.: "quais cidades tiveram desastre em setembro de 2011?"' }
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
  if (!e.ano) return { intencao: 'chuva', texto: 'Diga o ano (e o mês, se souber) da enchente. Ex.: "quanto choveu antes da enchente de novembro de 2008?"' }
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

function transito(e: Extraido, d: Dados): Resposta {
  if (!e.cidade || !e.cidade2) return { intencao: 'transito', texto: 'Diga as duas cidades. Ex.: "quanto tempo a cheia leva de Rio do Sul até Blumenau?"' }
  const a = e.cidade
  const b = e.cidade2
  const tr = d.transito.trechos.find((x) => x.de === a.id && x.para === b.id) ?? d.transito.trechos.find((x) => x.de === b.id && x.para === a.id)
  if (!tr) {
    const daqui = d.transito.trechos.filter((x) => x.de === a.id).map((x) => x.para)
    return {
      intencao: 'transito',
      texto: `O site não tem tempo de trânsito levantado entre ${a.nome} e ${b.nome}.${daqui.length ? ` De ${a.nome} há tempo para: ${daqui.join(', ')}.` : ''} Não somo trechos, porque alguns rios têm cheia própria e o tempo não se encadeia.`,
    }
  }
  const faixa = tr.horas_min === tr.horas_max ? `cerca de ${tr.horas_min} h (valor único na fonte, é aproximação)` : `de ${tr.horas_min} a ${tr.horas_max} h`
  const conhecidas = cidadesConhecidas(d)
  const nome = (id: string) => conhecidas.find((c) => c.id === id)?.nome ?? id
  return {
    intencao: 'transito',
    texto: `Da passagem do pico em ${nome(tr.de)} até ${nome(tr.para)}: ${faixa}, ${conf(tr.confianca)}.\nFonte: ${String(tr.fonte ?? 'transito.json').replace(/\.+$/, '')}.\nCada cheia é diferente; isso é uma referência de estudo, não uma previsão.`,
  }
}

const ANA_MIRIM: Record<string, string> = { salseiro: '83892990', 'vidal ramos': '83892990', 'botuvera montante': '83892998', botuvera: '83892998', brusque: '83900000' }

function cotaAna(e: Extraido, d: Dados): Resposta {
  const est = Object.entries(ANA_MIRIM).find(([k]) => e.t.includes(k))
  if (!est || !e.ano)
    return { intencao: 'cota_ana', texto: 'Tenho cota diária da ANA no Itajaí-Mirim para Salseiro, Botuverá-Montante e Brusque. Diga a estação e o ano (e o mês). Ex.: "cota da ANA em Brusque em novembro de 2008".' }
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
  if (AGORA.some((r) => r.test(t0))) return { intencao: 'agora', texto: TEXTO_ALERTA }
  if (t0.length < 3 || /^(oi|ola|ajuda|help|o que voce faz|como funciona)\b/.test(t0))
    return { intencao: 'ajuda', texto: 'Respondo perguntas sobre cheias que já aconteceram, com os dados deste site. Veja alguns exemplos:', sugestoes: EXEMPLOS }

  const e = extrair(pergunta, d)
  const t = e.t
  if (/\b(quanto tempo|demora|leva|chega|chegar|transito)\b/.test(t) && e.cidade2) return transito(e, d)
  if (/\bchov|chuva/.test(t)) return chuvaAntes(e, d)
  if (/\b(antecedencia|antes de brusque|chega em brusque)\b/.test(t) || (t.includes('botuvera') && t.includes('brusque') && /\bpico/.test(t))) return antecedenciaMirim(e, d)
  if (/\b(ana|cota|cm)\b/.test(t) && Object.keys(ANA_MIRIM).some((k) => t.includes(k))) return cotaAna(e, d)
  if (/\b(desabrigad|desalojad|mort|atingid|desastre|cidades|municipios|atlas)/.test(t)) return danosAtlas(e, d)
  if (/\b(quantas|quantos|quantas vezes)\b/.test(t) && e.nivel != null) return contarAcima(e, d)
  if (/\b(maior|maiores|recorde|pior|piores|mais alta|maxima)\b/.test(t) && !e.ano) return maioresCheias(e, d)
  if (e.ano && e.cidade) return cheiasDoPeriodo(e, d)
  if (e.cidade) return maioresCheias({ ...e, n: e.n ?? 5 }, d)
  if (e.ano) return danosAtlas(e, d)
  return { intencao: 'nao_entendi', texto: 'Não entendi a pergunta. Eu respondo só sobre o histórico, usando os dados do site. Tente um destes formatos:', sugestoes: EXEMPLOS }
}
