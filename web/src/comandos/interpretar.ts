/**
 * Pedido ou pergunta? (docs/CHAT-GLOBAL-COMANDOS.md, 06/10/2026)
 *
 * Devolve `null` quando o texto não é pedido: aí ele segue para o motor do chat, como sempre. Só vira comando
 * o que casa INTEIRO com uma das formas abaixo — "mostrar as cheias de Blumenau" continua pergunta, porque o
 * que sobra depois do verbo não é só uma cidade. Pergunta não mexe no mapa.
 *
 * Pedidos encadeados ("mostre Timbó, aproxime a régua e ative satélite") viram vários passos, resolvidos e
 * validados ANTES de qualquer execução. Se um trecho não for entendido, nada é executado e o chat diz qual.
 */
import type { Aba, Catalogo, Contexto, DiaDito, Fundo, Interpretacao, Passo, ReguaDoCatalogo } from './tipos'
import type { TemaDaLegenda } from './foz'

import { normalizar } from './normalizar'
import { corrigirCidade, distanciaDeEdicao, textoDaCorrecao } from './corrigir'
import { verbeteDe } from './glossario'
import { arquivoPeloNome } from './rios'
import {
  ARTIGOS, COTA_DITA, MESES_SEM_ACENTO, MES_DITO, SUJEITO, cidadeOpcional, cidadePorNome, cidadesDaLista,
  cotaDita, metrosDitos, soSujeito,
} from './entidades'

export { normalizar }

const CORTESIA_INICIO = /^(?:por favor|pfv|favor|voce pode|vc pode|pode|poderia|consegue|me|eu quero|quero|gostaria de|queria)\s+/
const CORTESIA_FIM = /\s+(?:por favor|pfv|pra mim|para mim|no mapa|no monitor|na tela|ai)$/

function semCortesia(t: string): string {
  let antes = ''
  let s = t
  while (s !== antes) {
    antes = s
    s = s.replace(CORTESIA_INICIO, '').replace(CORTESIA_FIM, '').trim()
  }
  return s
}

/**
 * "mostre Timbó, aproxime a régua e ative satélite" → três trechos. A vírgula separa ANTES de normalizar
 * (a normalização tira a pontuação). Nenhum nome do cadastro tem " e ". O "é" sem acento também vira "e":
 * por isso a frase inteira é tentada antes de dividir ("essa informação é atual ou histórica?").
 */
/**
 * 18ª entrega: abreviações do celular, depois de `normalizar` ("ir p/ o monitor" → "ir para o monitor", "qdo blumenau
 * passou da cota" → "quando …"). Só palavras inteiras; "dc" e "m" ficam como estão.
 */
const ABREVIACOES: [RegExp, string][] = [
  [/\bp\b/g, 'para'], [/\bq\b/g, 'que'], [/\bqdo\b/g, 'quando'], [/\b(?:qto|qnt)\b/g, 'quanto'], [/\b(?:qtos|qnts)\b/g, 'quantos'],
  [/\b(?:qtas|qntas)\b/g, 'quantas'], [/\boque\b/g, 'o que'], [/\bhj\b/g, 'hoje'], [/\bvc\b/g, 'voce'], [/\bvcs\b/g, 'voces'],
  [/\bc\b/g, 'com'], [/\b(?:tb|tbm)\b/g, 'tambem'], [/\bpq\b/g, 'por que'], [/\bmsm\b/g, 'mesmo'], [/\bblz\b/g, ''],
]
export function expandirAbreviacoes(t: string): string {
  let s = t
  for (const [re, por] of ABREVIACOES) s = s.replace(re, por)
  return s.replace(/\s+/g, ' ').trim()
}

function trechos(texto: string): string[] {
  return texto
    .split(/[,;]/)
    .flatMap((parte) => expandirAbreviacoes(normalizar(parte)).split(/\s*(?:\be depois\b|\bdepois\b|\be em seguida\b|\bem seguida\b|\be entao\b|\bentao\b|\be\b)\s*/))
    .map((x) => semCortesia(x.trim()))
    .filter(Boolean)
}

const VERBO_IR =
  '(?:mostrar|mostre|mostra|ver|veja|abrir|abra|abre|ir|va|vai|leve me|me leve|leva|leve|levar|me leva|centralizar|centralize|focar|foque|enquadrar|enquadre|selecionar|selecione|zoom|aproximar|aproxime|aproxima)'

function reguaPorCodigo(t: string, cat: Catalogo): ReguaDoCatalogo | null | 'inexistente' {
  const m = t.match(/\bdc\s*0*(\d{1,2})\b/)
  if (!m) return null
  const codigo = `DC-${(m[1] ?? '').padStart(2, '0')}`
  return cat.reguas.find((r) => r.codigo === codigo) ?? 'inexistente'
}

/** Réguas cujo nome aparece INTEIRO no alvo; a de nome mais longo vence ("bairro murta" antes de "murta"). */
function reguasPorNome(alvo: string, cat: Catalogo): ReguaDoCatalogo[] {
  const achadas = cat.reguas.filter((r) => {
    const n = normalizar(r.nome)
    return n && new RegExp(`(?:^|\\s)${n}(?:\\s|$)`).test(alvo)
  })
  if (achadas.length <= 1) return achadas
  const maior = Math.max(...achadas.map((r) => normalizar(r.nome).length))
  return achadas.filter((r) => normalizar(r.nome).length === maior)
}

/** Réguas que só COMPARTILHAM uma palavra com o alvo ("murta"): para perguntar qual, nunca para escolher. */
function reguasParecidas(alvo: string, cat: Catalogo): ReguaDoCatalogo[] {
  const palavras = alvo.split(' ').filter((p) => p.length >= 4)
  return cat.reguas.filter((r) => palavras.some((p) => normalizar(r.nome).split(' ').includes(p)))
}

export function rotuloDaRegua(r: ReguaDoCatalogo): string {
  return `${r.codigo} · ${r.nome}`
}

type Lido = Passo[] | { erro: string; sugestoes: string[] } | null

const TIPO_DE_VIA = '(?:rua|avenida|av|travessa|tv|trav|alameda|al|rodovia|rod|servidao|serv|estrada)'
const VERBO_RUA =
  '(?:mostrar|mostre|mostra|ver|veja|zoom|aproximar|aproxime|destacar|destaque|localizar|localize|achar|ache|encontrar|encontre|marcar|marque|onde fica|onde e|ir para|ir pra|va para)'

/**
 * O que vem depois de "rua …": o nome, a cidade no fim ("…, Gaspar" ou "… em Gaspar") e o ano ("… em 2008").
 * A cidade só sai do fim se for do cadastro; o resto é nome de rua.
 */
function partesDoPedidoDeRua(resto: string, cat: Catalogo): { texto: string; cidadeId?: string; ano?: string } {
  let r = resto.trim()
  let ano: string | undefined
  const a = r.match(/\s(?:em|de|na cheia de|na enchente de)\s(\d{4})$/)
  if (a) {
    ano = a[1]
    r = r.slice(0, a.index).trim()
  }
  let cidadeId: string | undefined
  for (const c of [...cat.cidades].sort((x, y) => normalizar(y.nome).length - normalizar(x.nome).length)) {
    const n = normalizar(c.nome)
    const m = r.match(new RegExp(`^(.+?)\\s(?:(?:em|no|na|de) )?${n}$`))
    // "rua brusque" (em Itajaí) é nome de rua: a cidade só sai do fim se sobrar tipo + nome.
    if (m?.[1] && m[1].trim().split(' ').length >= 2) {
      cidadeId = c.id
      r = m[1].trim()
      break
    }
  }
  return { texto: r, ...(cidadeId ? { cidadeId } : {}), ...(ano ? { ano } : {}) }
}

/** A 5ª entrega: o tempo e a bacia (reprodução, chuva, barragens, maré, fonte da leitura). */
function lerTrechoDaQuinta(t: string, cat: Catalogo): Lido {
  if (/^(?:reproduzir|reproduza)$|^(?:reproduzir|reproduza|tocar|toque|rodar|rode|passar|passe|mostrar|mostre|ver)(?: a| o| as)? (?:reproducao|animacao|(?:das )?ultimas (?:24 ?h|24 horas|horas)|24 ?h|24 horas)$/.test(t)) {
    return [{ tipo: 'reproducao', acao: 'tocar' }]
  }
  // "Parar a reprodução" é voltar ao agora (1ª entrega); pausar congela no instante.
  if (/^(?:pausar|pause|pausa)(?: a| o)?(?: reproducao| animacao)?$/.test(t)) {
    return [{ tipo: 'reproducao', acao: 'pausar' }]
  }
  {
    // "como estava às 14h", "mostrar o mapa das 9h30", "voltar 3 horas", "como estava há 2 horas"
    const h = t.match(/^(?:como (?:estava|tava)|mostrar?(?: o mapa)?|mostre(?: o mapa)?|ir|va|ver|voltar)(?: o rio| o mapa| a bacia)?(?: para| pra)? (?:as|a|das|de) (\d{1,2})(?: ?h(?:oras)?)?(?: ?:? ?(\d{2}))?(?: ?min)?$/)
    if (h) return [{ tipo: 'reproducao', acao: 'ir', hora: Number(h[1]), ...(h[2] ? { minuto: Number(h[2]) } : {}) }]
    const a = t.match(/^(?:como (?:estava|tava)(?: o rio| o mapa| a bacia)? ha|voltar|volte|recuar|recue)(?: o mapa| a reproducao)? (\d{1,2}) (?:horas?|h)(?: atras)?$/)
    if (a) return [{ tipo: 'reproducao', acao: 'ir', horasAtras: Number(a[1]) }]
  }
  if (/^(?:onde|em que cidades?|quais cidades?) (?:esta|ta|estao) chovendo(?: mais)?(?: agora)?$|^onde (?:chove|choveu|chove mais|choveu mais)(?: agora| hoje| na ultima hora)?$|^(?:a )?chuva (?:agora|na bacia|de agora|nas cidades)$|^(?:ranking|lista) (?:da|de) chuva$/.test(t)) {
    return [{ tipo: 'chuva_agora' }]
  }
  if (/^(?:como (?:estao|esta|tao)(?: as| a)?|qual (?:e )?o estado (?:das|da)) barragens?(?: de contencao| do alto vale)?(?: agora)?$|^(?:as )?barragens?(?: agora)?$|^(?:as )?comportas(?: das barragens)?(?: estao)?(?: abertas| fechadas)?$|^(?:as )?barragens? (?:estao|tao|esta|ta) (?:abertas?|fechadas?|vertendo|cheias?|segurando|liberando)$/.test(t)) {
    return [{ tipo: 'barragens' }]
  }
  if (/^(?:(?:como (?:esta|ta)|qual(?: e)?) )?(?:a )?mare(?: agora| em itajai| na foz| no porto)?$|^(?:a )?mare (?:esta|ta) (?:subindo|baixando|alta|baixa)$|^(?:(?:quando e|qual(?: e)?) )?a proxima (?:preamar|mare alta|baixamar|mare baixa)$/.test(t)) {
    return [{ tipo: 'mare' }]
  }
  {
    const m = t.match(/^de onde vem (?:essa|esta|a) (?:leitura|medicao|informacao|numero)(?: (?:de|do|da) (.+))?$/)
      ?? t.match(/^(?:qual (?:e )?a )?fonte (?:da|desta|dessa) (?:leitura|medicao|regua)(?: (?:de|do|da) (.+))?$/)
    if (m) {
      const c = cidadeOpcional(m[1], cat)
      return c ? [{ tipo: 'fonte_leitura', ...c }] : null
    }
  }
  return null
}

/**
 * 16ª entrega: as ruas pela cota, cidade inteira. O número vem como `normalizar` o deixa: "8,50 m" vira "8 50 m", e
 * "50 cm" é centímetro. Só "quais/que ruas…": "qual a cota da rua X" e "manchas na rua X" continuam onde estavam.
 */
const NUM_M = '(\\d{1,2})(?: (\\d{1,2}))? ?(?:m|metros?)'
const NUM_CM = '(\\d{1,3}) ?(?:cm|centimetros?)'
const RUAS = '(?:quais|que|quantas|quantos) (?:sao )?(?:as )?(?:ruas|pontos de rua|pontos)'
const ALAGAM = '(?:alagam|alagariam|alagarao|vao alagar|ficam alagadas|ficariam alagadas|ficam embaixo d agua|ficam debaixo d agua|a agua alcanca|a agua pega|o rio alcanca|o rio pega)'
function lerTrechoDaDecimaSexta(t: string, cat: Catalogo): Lido {
  type P = Extract<Passo, { tipo: 'ruas_pela_cota' }>
  const com = (alvo: string | undefined, resto: Omit<P, 'tipo' | 'cidadeId'>): Lido => {
    const c = cidadeOpcional((alvo ?? '').replace(/^(?:em|de|do|da|no|na) /, '').trim(), cat)
    return c ? [{ tipo: 'ruas_pela_cota', ...resto, ...c }] : null
  }
  // "quais ruas alagam se subir mais 50 cm em Blumenau?", "que ruas alagam com mais 1 m?"
  {
    const m =
      t.match(new RegExp(`^${RUAS} ${ALAGAM} (?:se (?:o rio |o nivel )?(?:subir|subisse|aumentar) |com )?mais ${NUM_CM}(?: (?:em|de|no|na) (.+?))?$`)) ??
      t.match(new RegExp(`^${RUAS} ${ALAGAM} (?:se (?:o rio |o nivel )?(?:subir|subisse|aumentar) |com )?mais ${NUM_M}(?: (?:em|de|no|na) (.+?))?$`))
    if (m) {
      const cm = m.length === 3 ? Number(m[1]) : null
      const subirM = cm != null ? cm / 100 : metrosDitos(m[1], m[2])
      if (!subirM || subirM > 10) return null
      return com(m[m.length - 1], { pergunta: 'proximas', subirM: Math.round(subirM * 100) / 100 })
    }
  }
  // "quais ruas alagam com 8 m em Blumenau?", "se o rio chegar a 8,50 m, quais ruas alagam em Blumenau?"
  {
    const m =
      t.match(new RegExp(`^${RUAS} ${ALAGAM} (?:com |a |em |no nivel de |com o rio (?:a|em) |se o rio (?:chegar|subir|estiver|for|bater) (?:a |em |ate |nos? )?)?${NUM_M}(?: (?:em|de|no|na) (.+?))?$`)) ??
      t.match(new RegExp(`^(?:com |a |em |se o rio (?:chegar|subir|estiver|for|bater) (?:a |em |ate |nos? )?|se chegar (?:a |em )?)${NUM_M}(?: (?:em|de|no|na) (.+?))? ${RUAS} ${ALAGAM}(?: (?:em|de|no|na) (.+?))?$`))
    if (m) {
      const nivelM = metrosDitos(m[1], m[2])
      if (!nivelM) {
        return {
          erro: `${m[1]}${m[2] ? `,${m[2]}` : ''} m não é um nível possível de rio nesta bacia: as réguas das cidades vão de pouco acima de 0 a menos de 25 m. Peça com um nível dentro dessa faixa.`,
          sugestoes: ['quais ruas alagam com 8 m em Blumenau?', 'quais são as ruas mais baixas de Blumenau?'],
        }
      }
      const cidades = m.slice(3).filter(Boolean)
      if (cidades.length > 1) return null
      return com(cidades[0], { pergunta: 'nivel', nivelM })
    }
  }
  // "quais ruas o rio já alcançou em Blumenau?", "que ruas estão alagadas agora em Blumenau?"
  {
    const m =
      t.match(new RegExp(`^${RUAS} (?:o rio |a agua )?(?:ja )?(?:alcancou|atingiu|pegou|alagou|cobriu)(?: agora| ate agora)?(?: (?:em|de|no|na) (.+?))?$`)) ??
      t.match(new RegExp(`^${RUAS} (?:ja )?(?:estao|tao|ficam|estariam) (?:alagadas|alagando|na cota|embaixo d agua|debaixo d agua|com agua)(?: agora| neste momento)?(?: (?:em|de|no|na) (.+?))?$`)) ??
      t.match(new RegExp(`^${RUAS} (?:estao|tao) alagando(?: agora)?(?: (?:em|de|no|na) (.+?))?$`)) ??
      t.match(new RegExp(`^${RUAS} ${ALAGAM} (?:agora|hoje|neste momento|com o (?:rio|nivel) de agora)(?: (?:em|de|no|na) (.+?))?$`))
    if (m) return com(m[1], { pergunta: 'agora' })
  }
  // "quais são as próximas ruas a alagar em Blumenau?"
  {
    const m = t.match(new RegExp(`^${RUAS}(?: sao)? (?:as )?proximas(?: ruas)?(?: a alagar| que alagam| a serem alagadas| na fila)?(?: (?:em|de|no|na) (.+?))?$`)) ??
      t.match(/^(?:quais|que) (?:sao )?(?:as )?proximas ruas(?: a alagar| que alagam| a serem alagadas)?(?: (?:em|de|no|na) (.+?))?$/) ??
      t.match(new RegExp(`^${RUAS} ${ALAGAM} (?:em seguida|depois|a seguir|se (?:o rio )?continuar subindo)(?: (?:em|de|no|na) (.+?))?$`)) ??
      t.match(new RegExp(`^${RUAS} (?:vem|veem|viriam|vao|seriam as proximas|sao as proximas|entram) (?:depois|em seguida|a seguir|na sequencia|agora)(?: (?:em|de|no|na) (.+?))?$`))
    if (m) return com(m[1], { pergunta: 'proximas' })
  }
  // "quais ruas alagam primeiro em Gaspar?", "quais são as ruas mais baixas de Blumenau?"
  {
    const m =
      t.match(new RegExp(`^${RUAS} ${ALAGAM} (?:primeiro|antes|mais cedo|com o rio mais baixo|com menos agua)(?: (?:em|de|no|na) (.+?))?$`)) ??
      t.match(new RegExp(`^${RUAS} (?:sao )?(?:as )?mais baixas(?: da cidade)?(?: (?:em|de|no|na) (.+?))?$`)) ??
      t.match(new RegExp(`^${RUAS} (?:tem|têm) (?:a )?(?:cota|cotas) mais baixas?(?: (?:em|de|no|na) (.+?))?$`))
    if (m) return com(m[1], { pergunta: 'primeiras' })
  }
  return null
}

/**
 * 15ª entrega: as cheias que a coleta do site já captou (`data/eventos-captados.json`). Perguntas sobre o passado
 * RECENTE: "última cheia", "o que o site captou", "nos últimos meses", "este ano", um mês sem ano (ou de 2026 em
 * diante) e um dia do mês. Ano antigo ("cheias de setembro de 2011") continua no motor, que lê enchentes.json.
 */
const RECENTE = '(?:desde que o site (?:acompanha|existe|mede|coleta)|nos ultimos (?:\\d+ )?meses|nas ultimas semanas|este ano|neste ano|em 2026|de 2026|ultimamente|recentemente)'
function lerTrechoDaDecimaQuinta(t: string, cat: Catalogo): Lido {
  type P = Extract<Passo, { tipo: 'captados' }>
  const com = (alvo: string | undefined, resto: Omit<P, 'tipo' | 'cidadeId'>): Lido => {
    const limpo = (alvo ?? '').replace(new RegExp(`^${SUJEITO}(?: (?:de|em|do|da|no|na))? ?`), '').replace(/^(?:em|de|do|da|no|na) /, '').trim()
    const c = cidadeOpcional(limpo, cat)
    return c ? [{ tipo: 'captados', ...resto, ...c }] : null
  }
  const cotaDe = cotaDita
  const anoDe = (s: string | undefined) => (s ? Number(s) : undefined)
  // Lista: "quais cheias o site captou?", "o que aconteceu nos últimos meses?", "cheias recentes em Blumenau".
  {
    const m =
      t.match(/^(?:quais|que) (?:cheias|enchentes|eventos) (?:o site|a coleta|voce|voces) (?:ja )?(?:captou|captaram|registrou|registraram|acompanhou|acompanharam|viu|viram|pegou|pegaram)(?: (?:em|de|no|na) (.+?))?$/) ??
      t.match(/^(?:o que|que) (?:o site|a coleta|voce|voces) (?:ja )?(?:captou|captaram|registrou|registraram|acompanhou|acompanharam|viu|viram)(?: ate agora| nos ultimos meses| este ano)?(?: (?:em|de|no|na) (.+?))?$/) ??
      t.match(/^(?:o que aconteceu|que cheias houve|quais foram as cheias|que cheias teve|quais cheias teve|houve cheia|teve cheia) (?:nos ultimos (?:\d+ )?meses|nas ultimas semanas|este ano|neste ano|ultimamente|recentemente|em 2026)(?: (?:em|de|no|na) (.+?))?$/) ??
      t.match(/^(?:cheias|enchentes) (?:recentes|captadas|dos ultimos meses|deste ano|de 2026)(?: (?:em|de|no|na) (.+?))?$/) ??
      t.match(/^(?:ultimas|as ultimas) (?:cheias|enchentes)(?: (?:em|de|no|na) (.+?))?$/) ??
      t.match(/^(?:quais foram|quais sao|que|quais) (?:as )?(?:cheias|enchentes|eventos) que (?:o site|a coleta|voce|voces) (?:ja )?(?:captou|captaram|registrou|registraram|acompanhou|acompanharam|viu|viram|pegou|pegaram|mediu|mediram)(?: (?:em|de|no|na) (.+?))?$/)
    if (m) {
      const c = m[1] ? cidadeOpcional(m[1], cat) : {}
      return c ? [{ tipo: 'captados', pergunta: 'lista', ...c }] : null
    }
  }
  // Última: "qual foi a última cheia em Blumenau?", "quando foi a última vez que Blumenau passou da cota de alerta?"
  {
    const m =
      t.match(/^(?:qual(?: foi| e)?|quando(?: foi)?) (?:a )?ultima (?:cheia|enchente)(?: (?:em|de|do|da|no|na) (.+?))?$/) ??
      t.match(/^(?:a )?ultima (?:cheia|enchente)(?: (?:em|de|do|da|no|na) (.+?))?$/)
    if (m) return com(m[1], { pergunta: 'ultima' })
    const v = t.match(new RegExp(`^(?:quando foi |qual foi )?(?:a )?ultima vez que (?:(.+?) )?(?:passou|cruzou|chegou|entrou|ficou|esteve) (?:d[aeo] |n[ao] |em |a |acima d[ao] )?(?:cota(?: d[aeo])? |nivel de |faixa de )?${COTA_DITA}?(?: (?:em|de|no|na) (.+?))?$`))
    if (v) {
      const antes = soSujeito(v[1])
      if (antes && v[3]) return null
      return com(antes ?? v[3], { pergunta: 'ultima', ...cotaDe(v[2]) })
    }
  }
  // Maior: "qual foi o maior nível que o site já captou em Blumenau?", "maior leitura captada em Blumenau".
  {
    const m =
      t.match(/^(?:qual (?:foi |e )?)?(?:o |a )?(?:maior|mais alto|mais alta|recorde d[eo]) (?:nivel|leitura|cheia|medicao|marca|valor)?(?: do rio| do nivel)? ?(?:que )?(?:o site|a coleta|voce|voces) (?:ja )?(?:captou|captaram|registrou|registraram|mediu|mediram|viu|viram|acompanhou)(?: (?:em|de|no|na) (.+?))?$/) ??
      t.match(/^(?:qual (?:foi |e )?)?(?:o |a )?(?:maior|mais alto|mais alta) (?:nivel|leitura|cheia|medicao|marca) (?:captad[ao]|medid[ao]|registrad[ao] pelo site)(?: (?:em|de|no|na) (.+?))?$/) ??
      t.match(/^(?:qual (?:foi |e )?)?(?:o |a )?(?:maior|mais alto|mais alta) (?:nivel|leitura|cheia|medicao|marca)(?: (?:em|de|no|na) (.+?))? desde que o site (?:acompanha|existe|mede|coleta)$/) ??
      t.match(/^recorde do site(?: (?:em|de|no|na) (.+?))?$/)
    if (m) return com(m[1], { pergunta: 'maior' })
  }
  // Quantas: "quantas vezes Blumenau passou da cota de alerta desde que o site acompanha?", "quantas cheias o site captou em Blumenau?"
  {
    const m = t.match(new RegExp(`^(?:quantas|quantos) (?:vezes|cheias|enchentes|episodios) (?:(.+?) )?(?:passou|passaram|cruzou|cruzaram|chegou|chegaram|entrou|entraram|ficou|ficaram|esteve|estiveram|teve|houve) (?:d[aeo] |n[ao] |em |a |acima d[ao] )?(?:cota(?: d[aeo])? |nivel de |faixa de )?${COTA_DITA}?(?: (?:em|de|no|na) (.+?))? ${RECENTE}$`))
    if (m) {
      const antes = soSujeito(m[1])
      if (antes && m[3]) return null
      return com(antes ?? m[3], { pergunta: 'quantas', ...cotaDe(m[2]) })
    }
    const n =
      t.match(/^(?:quantas|quantos) (?:cheias|enchentes|episodios|vezes) (?:o site|a coleta|voce|voces) (?:ja )?(?:captou|captaram|registrou|registraram|acompanhou|viu|viram|contou)(?: (?:em|de|no|na) (.+?))?$/) ??
      t.match(/^(?:quantas|quantos) (?:cheias|enchentes) (?:teve|houve|aconteceram)(?: (?:em|de|no|na) (.+?))? (?:desde que o site (?:acompanha|existe|mede|coleta)|nos ultimos (?:\d+ )?meses|este ano|neste ano|em 2026|ultimamente)$/)
    if (n) return com(n[1], { pergunta: 'quantas' })
  }
  // Período: "como foi a cheia de setembro em Blumenau?", "o que aconteceu em 12 de setembro?", "cheias de setembro em Blumenau".
  {
    const d = t.match(new RegExp(`^(?:o que aconteceu|como foi|como estava|qual foi o pico|qual foi o nivel|qual foi a maior leitura|quanto deu|que cheia teve|houve cheia|teve cheia)(?: (?:o rio|a cheia|a enchente|o dia|no dia|em|no|na|de|do|da))*? (\\d{1,2}) de ${MES_DITO}(?: de (20\\d{2}))?(?: (?:em|de|no|na) (.+?))?$`))
    if (d) {
      const ano = anoDe(d[3])
      if (ano && ano < 2026) return null
      const mes = MESES_SEM_ACENTO.indexOf(d[2]!) + 1
      const diaN = Number(d[1])
      if (diaN < 1 || diaN > 31) return null
      const a = ano ?? (mes > new Date().getMonth() + 1 ? new Date().getFullYear() - 1 : new Date().getFullYear())
      return com(d[4], { pergunta: 'periodo', dia: `${a}-${String(mes).padStart(2, '0')}-${String(diaN).padStart(2, '0')}` })
    }
    const m =
      t.match(new RegExp(`^(?:como foi|como foram|o que aconteceu|que cheia teve|houve cheia|teve cheia|qual foi o pico|qual foi a maior leitura|quanto deu) (?:(?:a|as|o|os|na|nas|no|nos|em|de|da|do) )?(?:cheias?|enchentes?|rio|nivel|pico)?(?: (?:de|do|da|em|no|na))? ${MES_DITO}(?: de (20\\d{2}))?(?: (?:em|de|no|na) (.+?))?$`)) ??
      t.match(new RegExp(`^(?:cheias?|enchentes?) de ${MES_DITO}(?: de (20\\d{2}))?(?: (?:em|de|no|na) (.+?))?$`)) ??
      t.match(new RegExp(`^(?:o que aconteceu|como foi) (?:em|no mes de) ${MES_DITO}(?: de (20\\d{2}))?(?: (?:em|de|no|na) (.+?))?$`))
    if (m) {
      const ano = anoDe(m[2])
      if (ano && ano < 2026) return null
      return com(m[3], { pergunta: 'periodo', mes: MESES_SEM_ACENTO.indexOf(m[1]!) + 1, ...(ano ? { ano } : {}) })
    }
  }
  return null
}

/**
 * 14ª entrega: a linha do tempo da cheia de agora. A cidade pode vir antes do verbo ("quando Blumenau passou da
 * cota?") ou no fim ("quando o rio passou da cota em Blumenau?"); sem cidade, vale a da página.
 */
function lerTrechoDaDecimaQuarta(t: string, cat: Catalogo): Lido {
  const comCidade = (alvo: string | undefined, resto: Omit<Extract<Passo, { tipo: 'linha_do_tempo' }>, 'tipo' | 'cidadeId'>): Lido => {
    const limpo = (alvo ?? '').replace(new RegExp(`^${SUJEITO}(?: (?:de|em|do|da|no|na))? ?`), '').trim()
    const c = cidadeOpcional(limpo, cat)
    return c ? [{ tipo: 'linha_do_tempo', ...resto, ...c }] : null
  }
  const cotaDe = cotaDita
  // "quanto Blumenau subiu nas últimas 6 horas?", "quanto o rio subiu em Blumenau nas últimas 12 h?"
  {
    const m =
      t.match(new RegExp(`^(?:quanto|qto) (?:(.+?) )?(?:subiu|baixou|desceu|variou|mudou|encheu)(?: ${SUJEITO})?(?: (?:em|de|no|na) (.+?))? (?:nas |em |desde |durante )?(?:as )?(?:ultimas )?(\\d{1,2}) ?(?:h|horas?)(?: (?:em|de|no|na) (.+?))?$`)) ??
      t.match(new RegExp(`^(?:quanto|qto) (?:${SUJEITO} )?(?:subiu|baixou|desceu|variou|mudou|encheu) (?:(.+?) )?(?:nas |em |desde |durante )?(?:as )?(?:ultimas )?(\\d{1,2}) ?(?:h|horas?)(?: (?:em|de|no|na) (.+?))?$`))
    if (m) {
      const partes = m.slice(1).filter((x): x is string => !!x && !/^\d+$/.test(x)).map(soSujeito).filter(Boolean)
      const horas = Number(m.slice(1).find((x) => x && /^\d+$/.test(x)))
      if (partes.length > 1 || !(horas >= 1 && horas <= 72)) return null
      return comCidade(partes[0], { pergunta: 'variacao', horas })
    }
  }
  // 18ª entrega: "quanto Blumenau subiu?" sem a janela de horas pergunta a janela, em vez de cair no motor por palpite.
  {
    const m = t.match(new RegExp(`^(?:quanto|qto) (?:(.+?) )?(?:subiu|baixou|desceu|variou|mudou|encheu)(?: ${SUJEITO})?(?: (?:em|de|no|na) (.+?))?$`))
    if (m) {
      const partes = m.slice(1).filter((x): x is string => !!x).map(soSujeito).filter(Boolean)
      const alvo = partes.length <= 1 ? cidadeOpcional(partes[0], cat) : null
      if (alvo) {
        const nome = alvo.cidadeId ? nomeDaCidade(alvo.cidadeId, cat) : 'a cidade'
        return {
          erro: `Em quantas horas? Diga a janela, por exemplo "quanto ${nome} subiu nas últimas 6 horas?", ou peça a última hora.`,
          sugestoes: [`quanto ${nome} subiu nas últimas 6 horas?`, `o que mudou na última hora em ${nome}?`],
        }
      }
    }
  }
  // "quando o rio começou a subir em Blumenau?", "quando Blumenau começou a subir?", "há quanto tempo está subindo?"
  {
    const m =
      t.match(new RegExp(`^(?:quando|a que hora|que hora|desde quando|desde que hora) (?:(.+?) )?(?:comecou|comecaram|passou|voltou) a (?:subir|encher)${EM_CIDADE}$`)) ??
      t.match(new RegExp(`^(?:ha|faz) quanto tempo (?:(.+?) )?(?:esta|ta|vem|anda) (?:subindo|enchendo)${EM_CIDADE}$`)) ??
      t.match(new RegExp(`^(?:desde quando) (?:(.+?) )?(?:esta|ta|vem|anda)? ?(?:subindo|sobe|enchendo|enche)${EM_CIDADE}$`))
    if (m) {
      const antes = soSujeito(m[1])
      if (antes && m[2]) return null
      return comCidade(antes ?? m[2], { pergunta: 'comecou_a_subir' })
    }
  }
  // "há quanto tempo Blumenau está em alerta?", "há quanto tempo está acima da cota de atenção em Blumenau?"
  {
    const m = t.match(new RegExp(`^(?:(?:ha|faz|desde) quanto tempo|desde quando|a partir de quando) (?:(.+?) )?(?:esta|ta|fica|ficou|segue|continua) (?:em|no|na|acima d[ao]|acima d[ao] cota de|na cota de|em cota de|na faixa de) ?${COTA_DITA}?${EM_CIDADE}$`))
    if (m) {
      const antes = soSujeito(m[1])
      if (antes && m[3]) return null
      return comCidade(antes ?? m[3], { pergunta: 'ha_quanto_tempo', ...cotaDe(m[2]) })
    }
  }
  // "quando Blumenau passou da cota de alerta?", "a que hora o rio passou da cota em Blumenau?", "quando entrou em alerta?"
  {
    // 19ª: "… ontem?" (ou "hoje", "anteontem") no fim, em qualquer posição relativa à cidade.
    const dia = t.match(/^(.*?)(?: (hoje|ontem|anteontem))(?: (?:em|de|no|na) (.+?))?$/)
    const semDia = dia ? `${dia[1]}${dia[3] ? ` em ${dia[3]}` : ''}` : t
    const diaDito = dia ? (dia[2] as DiaDito) : undefined
    const m = semDia.match(
      new RegExp(`^(?:quando|a que hora|que hora|desde quando|desde que hora) (?:(.+?) )?(?:passou|cruzou|ultrapassou|bateu|chegou|atingiu|entrou|subiu acima|ficou acima)(?: d[aeo]| n[ao]| em| a| para| pra)?(?: cota(?: d[aeo])?| nivel d[aeo]| faixa d[aeo])?(?: ${COTA_DITA})?(?: (?:em|de|no|na) (.+?))?(?: agora)?$`),
    )
    if (m && (m[2] || /cota|nivel de|faixa de|entrou/.test(semDia))) {
      const antes = soSujeito(m[1])
      if (antes && m[3]) return null
      return comCidade(antes ?? m[3], { pergunta: 'cruzou_cota', ...cotaDe(m[2]), ...(diaDito ? { dia: diaDito } : {}) })
    }
  }
  return null
}

const MINHAS = '(?:as )?(?:minhas cidades|cidades que (?:eu )?sigo|cidades seguidas)'
function lerTrechoDaDecimaTerceira(t: string, cat: Catalogo): Lido {
  if (new RegExp(`^(?:como (?:estao|tao) |e )?${MINHAS}(?: agora)?$`).test(t)) return [{ tipo: 'varias_cidades', seguidas: true }]
  if (new RegExp(`^copiar (?:o )?resumo (?:das|de) (?:minhas cidades|cidades que (?:eu )?sigo|cidades seguidas)$`).test(t)) return [{ tipo: 'varias_cidades', seguidas: true, copiar: true }]
  {
    const m = t.match(/^copiar (?:o )?resumo (?:de|das cidades) (.+)$/)
    const ids = m ? cidadesDaLista(m[1]!, cat) : null
    if (ids && ids.length >= 2) return [{ tipo: 'varias_cidades', cidadeIds: ids, copiar: true }]
  }
  {
    const m = t.match(/^como (?:estao|esta|tao|ta) (?:as cidades (?:de )?)?(.+?)(?: agora)?$/)
    const ids = m ? cidadesDaLista(m[1]!, cat) : null
    if (ids && ids.length >= 2) return [{ tipo: 'varias_cidades', cidadeIds: ids }]
    // 18ª entrega: "como estão Blumenau e Pomerode?" — uma fora do cadastro invalida a lista, e o chat diz qual.
    if (m && / e /.test(m[1]!)) {
      const desconhecidas = cidadesForaDoCadastro(m[1]!, cat)
      if (desconhecidas) {
        return {
          erro: `${desconhecidas.map((d) => `"${d}"`).join(' e ')} não ${desconhecidas.length > 1 ? 'estão' : 'está'} entre as cidades do site, então não respondo a lista pela metade. As cidades com régua são: ${cat.cidades.map((c) => c.nome).join(', ')}.`,
          sugestoes: ['quais cidades estão em alerta?'],
        }
      }
    }
  }
  return null
}

/** As palavras de uma lista de cidades que não são cidade do cadastro (e nem "e"), quando ao menos UMA é. */
function cidadesForaDoCadastro(lista: string, cat: Catalogo): string[] | null {
  let resto = ` ${lista} `
  let achouAlguma = false
  for (const c of [...cat.cidades].sort((a, b) => normalizar(b.nome).length - normalizar(a.nome).length)) {
    const n = normalizar(c.nome)
    if (resto.includes(` ${n} `)) {
      achouAlguma = true
      resto = resto.replace(` ${n} `, ' ')
    }
  }
  const sobras = resto.split(' ').filter((w) => w && w !== 'e')
  return achouAlguma && sobras.length ? sobras : null
}

/** A 12ª entrega: o Monitor, peça por peça (rio inteiro, barragens, painel, menu de cidades). */
// "No mapa" é cortesia para o resto do chat (sai antes de ler); aqui ele decide, então é lido no texto inteiro.
const RIO_NO_MAPA = /^(?:ver|veja|mostrar|mostre|enquadrar|enquadre|focar|foque)(?: o| no)?(?: rio)? (itajai acu|acu|itajai mirim|mirim)(?: inteiro| todo)? no mapa$/
const BARRAGENS_NO_MAPA = /^(?:ver|veja|mostrar|mostre|enquadrar|enquadre)(?: as)? barragens no mapa$/
function lerTrechoDaDecimaSegunda(t: string, ctx: Contexto): Lido {
  {
    const m = t.match(/^(?:zoom|enquadrar|enquadre|aproximar|aproxime)(?: no| o| em)?(?: rio)? (itajai acu|acu|itajai mirim|mirim)(?: inteiro| todo)?$/)
      // No Monitor, "ver o Itajaí-Mirim" é o rio no mapa; fora dele, a página do rio (1ª entrega).
      ?? (ctx.naMonitor ? t.match(/^(?:ver|veja|mostrar|mostre|focar|foque)(?: o| no)?(?: rio)? (itajai acu|acu|itajai mirim|mirim)(?: inteiro| todo)?$/) : null)
    if (m) return [{ tipo: 'enquadrar', alvo: 'rio', rioId: /mirim/.test(m[1]!) ? 'itajai-mirim' : 'itajai-acu' }]
  }
  if (/^(?:zoom|enquadrar|enquadre|aproximar|aproxime)(?: nas| as)? barragens$|^onde ficam as barragens$/.test(t)) {
    return [{ tipo: 'enquadrar', alvo: 'barragens' }]
  }
  if (/^(?:fechar|feche|fecha|recolher|recolha|tirar|tire)(?: o| a| esse| essa| este| esta)? (?:painel|folha|ficha)(?: da cidade| da regua)?$/.test(t)) return [{ tipo: 'fechar_painel' }]
  if (/^(?:abrir|abra|abre|mostrar|mostre)(?: o)? menu(?: de| das)? cidades$|^(?:a )?lista de cidades do mapa$|^(?:abrir|abra|abre|mostrar|mostre|ver)(?: a)? lista (?:de|das) cidades(?: do mapa)?$/.test(t)) return [{ tipo: 'menu_cidades', acao: 'abrir' }]
  if (/^(?:fechar|feche|fecha|recolher|recolha)(?: o)? menu(?: de| das)?(?: cidades)?$/.test(t)) return [{ tipo: 'menu_cidades', acao: 'fechar' }]
  return null
}

/** A 11ª entrega: as palavras do rio (glossário) e a resposta em voz alta. */
function lerTrechoDaDecimaPrimeira(t: string): Lido {
  {
    const m = t.match(/^(?:qual (?:e )?)?a diferenca entre (.+?) e (.+)$/)
    if (m && verbeteDe(m[1]!) && verbeteDe(m[2]!)) return [{ tipo: 'glossario', termos: [m[1]!, m[2]!] }]
  }
  {
    const m = t.match(/^o que (?:e|eh|sao|significa|significam|quer dizer|querem dizer) (.+?)(?: no mapa| no site| no rio| na regua)?$/)
    if (m && verbeteDe(m[1]!)) return [{ tipo: 'glossario', termos: [m[1]!] }]
  }
  if (/^(?:que|quais) (?:palavras|termos) (?:voce|vc) (?:explica|conhece|sabe explicar)$|^glossario$/.test(t)) return [{ tipo: 'termos' }]
  if (/^(?:ler|leia|le|falar|fale|fala)(?: a)?(?: ultima)?(?: resposta)? em voz alta$|^(?:ler|leia)(?: a)? (?:ultima )?resposta$/.test(t)) return [{ tipo: 'voz', acao: 'ler' }]
  if (/^(?:parar|pare|para)(?: de)? (?:ler|falar)$|^(?:silencio|chega de ler)$/.test(t)) return [{ tipo: 'voz', acao: 'parar' }]
  return null
}

/** A 8ª entrega: o site e os seus dados (atualizar, aviso, instalar, privacidade, conversa, emergência). */
function lerTrechoDaOitava(t: string): Lido {
  if (/^(?:atualizar|atualize|atualiza|recarregar|recarregue|recarrega|buscar de novo|busque de novo|busca de novo)(?: as| os| a| o)?(?: leituras| dados| niveis| numeros| medicoes| mapa| pagina| tudo)?(?: agora)?$|^(?:hoje |agora )?(?:tem|ha|chegou|teve|saiu|entrou) (?:leitura|medicao|dado) nov[ao](?: hoje| agora)?$|^(?:buscar|busque|busca|pegar|pegue|puxar|puxe|carregar|carregue|checar|cheque|conferir|confira)(?: as| os| se tem| se ha)? ?(?:leituras|dados|medicoes|niveis|numeros)(?: novas?| novos?| mais recentes?| atualizad[ao]s?)?$/.test(t)) {
    return [{ tipo: 'atualizar' }]
  }
  if (/^(?:isso|isto|este site|esse site|o site)(?: aqui)? e oficial$|^(?:o que e|para que serve) (?:este|esse|o) site$|^(?:ler|leia|mostrar|mostre|ver)(?: o)? aviso(?: legal)?$|^(?:este|esse|o) site e (?:um )?(?:alerta|sistema) oficial$|^(?:este|esse|o) site e (?:da|do|oficial da|ligado a|vinculado a) (?:defesa civil|prefeitura|governo|alertablu|ana)$|^(?:voces sao|vcs sao|e) (?:a |da )?defesa civil$/.test(t)) {
    return [{ tipo: 'oficial' }]
  }
  if (/^(?:como )?(?:instalar|instalo|instale|baixar|baixo|baixe)(?: o)? (?:app|aplicativo|site)(?: no celular| no telefone| na tela inicial)?$|^(?:tem|existe) (?:app|aplicativo)$|^(?:adicionar|adiciono|colocar|coloco)(?: o site)? na tela (?:inicial|de inicio)$|^(?:da para|da pra|posso|consigo|tem como|e possivel|como faco para|como faco pra) (?:instalar|baixar|colocar)(?: o site| o app| o aplicativo| isso)?(?: no celular| no telefone| na tela inicial)?$/.test(t)) {
    return [{ tipo: 'instalar' }]
  }
  if (/^o que (?:o site|voce|vc|voces|vcs) (?:guarda|guardam|sabe|sabem|grava|gravam|salva|salvam|coleta|coletam|armazena|armazenam) (?:de mim|sobre mim|no (?:meu )?(?:celular|aparelho|telefone))$|^quais (?:sao )?(?:os )?meus dados(?: guardados)?$|^(?:o site|voce|voces) (?:guarda|guardam|salva|salvam|tem|coleta|coletam) (?:os )?meus dados$|^privacidade$|^o site (?:me rastreia|guarda minha localizacao|grava minhas perguntas|guarda minhas perguntas)$/.test(t)) {
    return [{ tipo: 'privacidade' }]
  }
  {
    const m = t.match(/^(sim )?(?:apagar|apague|esquecer|esqueca|limpar|limpe|zerar|zere)(?: as| os| todas as| todos os)? (?:minhas preferencias|meus dados|preferencias|dados do aparelho|o que o site guarda)$/)
      ?? t.match(/^(sim )?(?:apagar|apague|esquecer|esqueca|limpar|limpe|zerar|zere) (?:tudo|todo) (?:o )?que (?:o site|voce|vc) (?:guarda|guardou|sabe|salvou|tem) (?:de mim|sobre mim|no (?:meu )?(?:celular|aparelho))$/)
    if (m) return [{ tipo: 'esquecer', confirmado: !!m[1] }]
  }
  if (/^(?:nao|parar de|pare de) contar (?:as )?minhas perguntas$|^(?:desligar|desligue) (?:a )?contagem(?: do chat)?$/.test(t)) return [{ tipo: 'contagem', permitir: false }]
  if (/^(?:pode )?contar (?:as )?minhas perguntas$|^(?:ligar|ligue|religar) (?:a )?contagem(?: do chat)?$/.test(t)) return [{ tipo: 'contagem', permitir: true }]
  if (/^(?:limpar|limpe|apagar|apague|zerar|zere)(?: a| esta| essa| o| este| esse| as)? (?:conversa|historico do chat|chat|mensagens|bate papo)$/.test(t)) return [{ tipo: 'limpar_conversa' }]
  if (/^(?:qual (?:e )?)?(?:o )?(?:telefone|numero|contato)(?: de emergencia| da defesa civil| dos bombeiros| de socorro)$|^(?:para )?quem (?:ligar|eu ligo|devo ligar)(?: em emergencia| em caso de enchente)?$|^(?:telefones?|numeros?) de emergencia$/.test(t)) {
    return [{ tipo: 'emergencia' }]
  }
  return null
}

/** A 7ª entrega: a foz (chegada × maré em Itajaí), a legenda do mapa e os botões de animação e legenda. */
const COR_PARA_TEMA: Record<string, TemaDaLegenda> = {
  'verde claro': 'monitoramento', verde: 'normal', amarelo: 'atencao', laranja: 'alerta', vermelho: 'inundacao', cinza: 'sem-dado',
  azul: 'azul', violeta: 'violeta', roxo: 'violeta', lilas: 'violeta',
}
const COR_FEMININA: Record<string, string> = { amarela: 'amarelo', vermelha: 'vermelho', roxa: 'roxo', cinzenta: 'cinza' }
const FAIXA_PARA_TEMA: Record<string, TemaDaLegenda> = {
  'abaixo da atencao': 'normal', monitoramento: 'monitoramento', observacao: 'monitoramento', atencao: 'atencao', alerta: 'alerta',
  prontidao: 'alerta', 'alerta maximo': 'inundacao', inundacao: 'inundacao', emergencia: 'inundacao', 'sem dado': 'sem-dado',
  'varias reguas': 'varias',
}
/**
 * "A água chega na hora da maré alta?", "quanto tempo chega a água de Blumenau até Itajaí, chega na maré alta?":
 * a cheia descendo (água, cheia, pico, enchente, ou Blumenau dita) + chegar + maré alta. É o mesmo quadro de chegada
 * × maré, que já diz a janela em horas. "Como está a maré?" e "quando é a maré alta?" não têm a cheia e seguem
 * para a maré (5ª entrega).
 */
const CHEIA_NA_MARE = (t: string) =>
  /\b(?:mare alta|mare cheia|preamar)\b/.test(t) &&
  /\b(?:chega|chegar|chegara|chegaria|chegam|chegando|pega|pegar|coincide|coincidir|bate|bater|junto)\b/.test(t) &&
  /\b(?:agua|cheia|pico|enchente|blumenau)\b/.test(t)

function lerTrechoDaSetima(t: string): Lido {
  if (CHEIA_NA_MARE(t)) return [{ tipo: 'chegada_itajai' }]
  if (/^(?:o )?pico (?:de |em )?blumenau (?:ja )?passou$|^(?:quando )?(?:o pico|a cheia|a onda de cheia)(?: de blumenau)? chega(?:ria)? (?:em|a|no) itajai$|^(?:o pico|a cheia)(?: de blumenau)?(?: vai)? (?:chega|chegar|pega|pegar|coincide|coincidir)(?: em itajai)?(?: com| na)? (?:a )?mare(?: alta| cheia)?(?: em itajai)?$|^chegada (?:do pico |da cheia )?(?:em|a|no) itajai$|^(?:pico|cheia) (?:x|e|com) mare(?: em itajai)?$/.test(t)) {
    return [{ tipo: 'chegada_itajai' }]
  }
  {
    const m = t.match(/^(?:e )?(?:se|simular|simule)(?: o)? pico (?:de |em )?blumenau (?:for |fosse |foi |tiver sido |ocorrer )?(?:(hoje|amanha|ontem) )?(?:as |a |ao )?(\d{1,2})(?: ?h(?:oras)?)?(?: ?(\d{2}))?(?: ?min)?(?: (hoje|amanha|ontem))?(?: quando chega(?:ria)? (?:em|a) itajai)?$/)
    if (m) {
      const dia = (m[1] ?? m[4]) as 'hoje' | 'amanha' | 'ontem' | undefined
      return [{ tipo: 'simular_chegada', hora: Number(m[2]), ...(m[3] ? { minuto: Number(m[3]) } : {}), ...(dia ? { dia } : {}) }]
    }
  }
  {
    const cor = t.match(/^o que (?:significa|quer dizer|e|indica)(?: a cor| o| a)? (verde claro|verde|amarel[oa]|laranja|vermelh[oa]|cinza|cinzenta|azul|violeta|rox[oa]|lilas)(?: no mapa| no rio| na legenda)?$/)
    if (cor) return [{ tipo: 'legenda', tema: COR_PARA_TEMA[COR_FEMININA[cor[1]!] ?? cor[1]!]! }]
    const fx = t.match(/^o que (?:significa|quer dizer|e)(?: a faixa(?: de)?| o nivel(?: de)?)? (abaixo da atencao|monitoramento|observacao|atencao|alerta maximo|alerta|prontidao|inundacao|emergencia|sem dado|varias reguas)$/)
    if (fx) return [{ tipo: 'legenda', tema: FAIXA_PARA_TEMA[fx[1]!]! }]
  }
  if (/^o que (?:significa|quer dizer|e) (?:o |a )?(?:trecho |linha )?tracejad[oa](?: no mapa)?$|^por que (?:o trecho |a linha )?(?:esta |ta )?tracejad[oa]$/.test(t)) return [{ tipo: 'legenda', tema: 'tracejado' }]
  if (/^o que (?:significam|sao|querem dizer) as ondas(?: no mapa)?$|^por que (?:a agua|o rio|a correnteza|as ondas) (?:se mexe|se mexem|anda|andam|corre|correm|esta andando|se move|se movem)(?: no mapa)?$/.test(t)) return [{ tipo: 'legenda', tema: 'ondas' }]
  if (/^o que (?:significa|e|quer dizer) (?:a |essa |esta )?seta(?: no mapa)?$/.test(t)) return [{ tipo: 'legenda', tema: 'seta' }]
  if (/^o que (?:significa|e|quer dizer) (?:o |a )?(?:anel sem cor|regua sem faixa|bolinha sem cor)$/.test(t)) return [{ tipo: 'legenda', tema: 'regua_mare' }]
  if (/^(?:o que (?:significam|querem dizer) as cores(?: do mapa)?|(?:explicar|explique|me explica|explica)(?: as)? (?:cores|legenda|a legenda)(?: do mapa)?|quais sao as cores(?: do mapa)?)$/.test(t)) return [{ tipo: 'legenda', tema: 'cores' }]
  if (/^(?:pausar|pause|parar|pare|desligar|desligue|congelar)(?: as| a)? (?:animacoes|ondas|animacao do rio|animacao da correnteza|correnteza)(?: do mapa)?$/.test(t)) return [{ tipo: 'animacoes', acao: 'pausar' }]
  if (/^(?:retomar|retome|voltar|volte|ligar|ligue|religar|continuar)(?: as| a)? (?:animacoes|ondas|correnteza)(?: do mapa)?$/.test(t)) return [{ tipo: 'animacoes', acao: 'retomar' }]
  if (/^(?:abrir|abra|mostrar|mostre|ver)(?: a)? legenda(?: do mapa)?$/.test(t)) return [{ tipo: 'legenda_mapa', acao: 'abrir' }]
  if (/^(?:fechar|feche|recolher|recolha|esconder|esconda|tirar|tire)(?: a)? legenda(?: do mapa)?$/.test(t)) return [{ tipo: 'legenda_mapa', acao: 'fechar' }]
  return null
}

/** A 6ª entrega: o rio agora, de cima a baixo (quanto falta, tendência, máximo de 24 h, panorama, de cima, filtro). */
const EM_CIDADE = '(?: (?:em|de|no|na|do|da|para|pra) (.+?))?(?: agora)?'
function lerTrechoDaSexta(t: string, cat: Catalogo): Lido {
  const comCidade = <T extends Passo>(alvo: string | undefined, passo: (c: { cidadeId?: string }) => T): T[] | null => {
    const c = cidadeOpcional(alvo, cat)
    return c ? [passo(c)] : null
  }
  {
    const m = t.match(new RegExp(`^(?:quanto|qto) (?:falta|faltam)(?: (?:para|pra|ate)(?: a| o)? (?:(?:cota|nivel)(?: de)? )?(?:alerta maximo|alerta|atencao|inundacao|emergencia|prontidao|monitoramento|proxima cota|cota|transbordar))?${EM_CIDADE}$`))
      ?? t.match(new RegExp(`^(?:a )?que distancia (?:esta )?(?:o rio |o nivel )?(?:esta )?da (?:proxima )?cota${EM_CIDADE}$`))
    if (m) return comCidade(m[1], (c) => ({ tipo: 'quanto_falta', ...c }))
  }
  {
    const m = t.match(/^(.*?) ?(?:esta|ta) (?:subindo|descendo|baixando)(?: ou (?:subindo|descendo|baixando))?(?: (?:em|de|no|na) (.+?))?(?: agora)?$/)
    if (m) {
      const antes = (m[1] ?? '').replace(/^(?:o rio|a regua|o nivel|a agua)(?: (?:de|em|do|da|no|na))? ?/, '').trim()
      if (m[2] && antes) return null
      return comCidade(m[2] ?? antes, (c) => ({ tipo: 'tendencia', ...c }))
    }
    const n = t.match(new RegExp(`^(?:qual (?:e )?)?a tendencia(?: do rio| do nivel)?${EM_CIDADE}$`))
    if (n) return comCidade(n[1], (c) => ({ tipo: 'tendencia', ...c }))
    // "Blumenau subindo?": a cidade e o particípio, sem verbo.
    const s = t.match(/^(.+?) (?:subindo|descendo|baixando)(?: ou (?:subindo|descendo|baixando))?$/)
    if (s) {
      const c = cidadePorNome(s[1]!, cat)
      if (c) return [{ tipo: 'tendencia', cidadeId: c.id }]
    }
  }
  {
    const m = t.match(new RegExp(`^(?:qual (?:foi |e )?)?(?:o |a )?(?:minimo e (?:o )?)?(?:maximo|pico|maior nivel|nivel maximo|nivel mais alto|maxima)(?: e (?:o )?minimo)?(?: do rio| do nivel)? (?:(?:das|nas|em) ultimas 24 ?(?:h|horas)|de hoje|hoje|em 24 ?(?:h|horas))${EM_CIDADE}$`))
    if (m) return comCidade(m[1], (c) => ({ tipo: 'maximo_24h', ...c }))
  }
  if (/^(?:quais|que|tem|ha|alguma|algumas|existe|existem)(?: as)? (?:cidades?|reguas?)(?: (?:estao|esta|tao|ta))? (?:em|no|na|acima da cota de) (?:alerta|atencao|emergencia|inundacao|cota de alerta)(?: agora)?$|^(?:como (?:esta|ta) a bacia|como (?:estao|tao) (?:os rios|as cidades)|resumo da bacia|panorama(?: da bacia)?|situacao da bacia)(?: agora| toda| inteira)?$/.test(t)) {
    return [{ tipo: 'panorama' }]
  }
  {
    const m = t.match(/^o que (?:vem|esta vindo|ta vindo|desce|esta descendo) (?:de cima|do alto vale|de montante|rio abaixo|rio acima|la de cima)(?: (?:para|pra|ate|em|sobre) (.+?))?(?: agora)?$/)
      ?? t.match(/^como (?:esta|estao|ta|tao) (?:o rio|as cidades|as reguas) (?:acima|de cima|rio acima)(?: (?:de|do|da) (.+?))?(?: agora)?$/)
    if (m) return comCidade(m[1], (c) => ({ tipo: 'de_cima', ...c }))
  }
  if (/^(?:(?:mostrar|mostre|mostra|ver|veja|filtrar|filtre|deixar|deixe)(?: so| somente| apenas)?(?: as| os)? )?(?:so |somente |apenas )?(?:as |os )?(?:reguas|cidades|estacoes|pinos) (?:em alerta|acima do normal|com faixa(?: acima do normal)?|com cor de faixa)$/.test(t)) {
    return [{ tipo: 'filtro', filtro: 'acima_do_normal' }]
  }
  return null
}

/** A 4ª entrega: o que depende do aparelho (localização, preferências, relato, tela cheia). */
function lerTrechoDaQuarta(t: string, cat: Catalogo): Lido {
  if (/^(?:usar|use|usa|pegar|pegue|ver|veja|mostrar|mostre)(?: a)? minha (?:localizacao|posicao)$|^onde (?:eu )?estou$|^(?:qual (?:e )?)?a regua mais (?:perto|proxima)(?: de mim| daqui)?$|^(?:qual )?regua (?:fica |esta )?mais (?:perto|proxima)(?: de mim| daqui)?$/.test(t)) {
    return [{ tipo: 'localizacao' }]
  }
  if (/^(?:relatar|relate|reportar|reporte|informar|informe|comunicar|comunique|avisar|avise)(?: sobre)?(?: um| o)? (?:problema|erro|defeito)(?: (?:nesta|nessa|na|desta|dessa|da|nesse|neste|no) (?:regua|tela|pagina|leitura|cidade|mapa|site))?$|^(?:a |essa |esta )?leitura (?:esta|ta) errada$/.test(t)) {
    return [{ tipo: 'relatar' }]
  }
  {
    const m = t.match(/^(?:a )?minha cidade e (.+)$/)
      ?? t.match(/^(?:definir|defina|mudar|mude|trocar|troque|colocar|coloque|escolher|escolha)(?: a)? minha cidade (?:para|pra|como|em) (.+)$/)
      ?? t.match(/^(?:definir|defina|colocar|coloque|escolher|escolha|tornar|torne) (.+?) como (?:a )?minha cidade$/)
    if (m) {
      const c = cidadePorNome(m[1] ?? '', cat)
      if (c) return [{ tipo: 'preferencia_cidade', acao: 'minha', cidadeId: c.id }]
      return { erro: `"${(m[1] ?? '').trim()}" não está entre as cidades do site, então não dá para guardar como a sua.`, sugestoes: ['quais cidades eu sigo?'] }
    }
  }
  {
    const m = t.match(/^(?:deixar de seguir|deixe de seguir|parar de seguir|pare de seguir|nao seguir mais)(?: a cidade de| a cidade)? (.+)$/)
    if (m) {
      const c = cidadePorNome(m[1] ?? '', cat)
      return c ? [{ tipo: 'preferencia_cidade', acao: 'deixar', cidadeId: c.id }] : null
    }
  }
  {
    const m = t.match(/^(?:seguir|siga|acompanhar|acompanhe)(?: a cidade de| a cidade)? (.+)$/)
    if (m) {
      const c = cidadePorNome(m[1] ?? '', cat)
      return c ? [{ tipo: 'preferencia_cidade', acao: 'seguir', cidadeId: c.id }] : null
    }
  }
  if (/^(?:quais|que) cidades (?:eu )?sigo$|^cidades que (?:eu )?sigo$|^(?:qual (?:e )?)?(?:a )?minha cidade$/.test(t)) {
    return [{ tipo: 'preferencia_cidade', acao: 'listar' }]
  }
  if (/^(?:aumentar|aumente|aumenta)(?: a| o)? (?:letra|fonte|texto)$|^(?:letra|fonte|texto) (?:maior|grande)$|^(?:usar|use|ligar|ligue)(?: a)? letra (?:maior|grande)$/.test(t)) {
    return [{ tipo: 'letra', tamanho: 'grande' }]
  }
  if (/^(?:diminuir|diminua|diminui|reduzir|reduza)(?: a| o)? (?:letra|fonte|texto)$|^(?:letra|fonte|texto) (?:normal|menor|padrao)$|^(?:voltar|volte)(?: a| o)? (?:letra|fonte|texto) (?:normal|ao normal)$/.test(t)) {
    return [{ tipo: 'letra', tamanho: 'normal' }]
  }
  if (/^(?:(?:abrir|abra|abre|ativar|ative|ativa|ligar|ligue|liga|colocar|coloque|coloca|por|poe|ver|mostrar|mostra|entrar|entra)(?: em| no| a| o)? )?(?:modo )?tela cheia$|^(?:maximizar|maximize|maximiza)(?: o)? mapa$/.test(t)) {
    return [{ tipo: 'tela_cheia' }]
  }
  return null
}

/** A 3ª entrega: a rua no mapa (docs/CHAT-GLOBAL-COMANDOS.md, "Rua destacada sobre as manchas"). */
function lerTrechoDaTerceira(t: string, cat: Catalogo): Lido {
  if (/^(?:remover|remova|tirar|tire|apagar|apague|limpar|limpe|desligar|desligue)(?: o| a)? (?:destaque|marca|marcacao)(?: da rua| das ruas| dos pontos)?$/.test(t)) {
    return [{ tipo: 'remover_destaque' }]
  }
  {
    // "manchas na rua X", "mancha de 2008 na rua X", "ver as manchas da avenida Y em Itajaí"
    const m = t.match(new RegExp(`^(?:(?:ver|veja|mostrar|mostre|mostra|quais) )?(?:as |a )?manchas?(?: de (\\d{4}))? (?:na|da|sobre a|no|do) (${TIPO_DE_VIA} .+)$`))
    if (m?.[2]) {
      const p = partesDoPedidoDeRua(m[2], cat)
      return [{ tipo: 'rua', foco: 'manchas', ...p, ...(m[1] ? { ano: m[1] } : {}) }]
    }
  }
  {
    // "mostrar a rua X", "zoom na avenida Y, Itajaí", "onde fica a rua Z em Gaspar" — com verbo: "Rua XV de
    // Novembro, Blumenau" sozinha continua pergunta para o motor.
    const m = t.match(new RegExp(`^${VERBO_RUA}(?: (?:na|no|a|o|para|pra|ate))* (${TIPO_DE_VIA} .+)$`))
    if (m?.[1]) {
      const p = partesDoPedidoDeRua(m[1], cat)
      if (p.texto.split(' ').length < 2) return null
      return [{ tipo: 'rua', foco: 'mostrar', ...p }]
    }
  }
  return null
}

/** A 2ª entrega (docs/CHAT-GLOBAL-COMANDOS.md): leituras, filtro, gráfico, traçado, árvore, confluência, cópia. */
function lerTrechoDaSegunda(t: string, cat: Catalogo): Lido {
  if (/^(?:quais|que|tem|ha|existe|existem)?(?: (?:as|alguma|algumas))? ?(?:leituras?|reguas?|estacoes|estacao|medicoes|medicao)(?: (?:estao|esta|tao|ta))? (?:atrasadas?|velhas?|desatualizadas?|paradas?|sem atualizar)$/.test(t)) {
    return [{ tipo: 'atrasadas' }]
  }
  if (/^(?:(?:mostrar|mostre|mostra|ver|veja|filtrar|filtre|deixar|deixe)(?: so| somente| apenas)?(?: as| os)? )?(?:so |somente |apenas )?(?:as |os )?(?:reguas|cidades|estacoes|pinos) sem leitura(?: de agora| recente| atual)?$/.test(t)) {
    return [{ tipo: 'filtro', filtro: 'sem_leitura' }]
  }
  if (/^(?:limpar|limpe|tirar|tire|remover|remova|desligar|desligue|apagar|apague)(?: os| o)? filtros?$|^(?:mostrar|mostre|ver) (?:todas as reguas e cidades|todos os pinos|todas as cidades)$/.test(t)) {
    return [{ tipo: 'filtro', filtro: null }]
  }
  {
    const m = t.match(/^(?:(?:abrir|abra|abre|ver|veja|mostrar|mostre|mostra) )?(?:o )?grafico(?: (?:desta|dessa|da) (?:regua|cidade))?(?: (?:de|do|da|em) (.+))?$/)
    if (m) {
      const c = cidadeOpcional(m[1], cat)
      return c ? [{ tipo: 'abrir_grafico', ...c }] : null
    }
  }
  {
    const m = t.match(/^o que (?:mudou|aconteceu|variou)(?: com o rio| com a regua)? na ultima hora(?: (?:em|no|na|de|do|da) (.+))?$/)
      ?? t.match(/^(?:quanto|como) (?:o rio |a regua |o nivel )?(?:subiu|desceu|baixou|variou|mudou) na ultima hora(?: (?:em|no|na|de|do|da) (.+))?$/)
      ?? t.match(/^(?:a )?ultima hora(?: (?:em|no|na|de|do|da) (.+))?$/)
    if (m) {
      const c = cidadeOpcional(m[1], cat)
      return c ? [{ tipo: 'ultima_hora', ...c }] : null
    }
  }
  {
    const m = t.match(/^de onde (?:vem|veio|e|saiu) (?:esse|este|o) (?:tracado|desenho)(?: do rio)?(?: (?:de|do|da) (.+))?$/)
      ?? t.match(/^(?:qual (?:e )?a )?(?:fonte|origem) do (?:tracado|desenho)(?: do rio)?(?: (?:de|do|da) (.+))?$/)
    if (m) {
      const alvo = (m[1] ?? '').trim()
      const c = cidadeOpcional(alvo, cat)
      if (c) return [{ tipo: 'origem_tracado', ...c }]
      const rio = arquivoPeloNome(alvo)
      return rio ? [{ tipo: 'origem_tracado', rio }] : { erro: `Não achei o traçado de "${alvo}".`, sugestoes: ['de onde vem o traçado do Benedito?', 'de onde vem o traçado do Itajaí-Mirim?'] }
    }
  }
  {
    const m = t.match(/^o que (?:fica|esta|vem|tem|ha) (?:a montante|acima|rio acima)(?: (?:de|do|da) (.+?)| daqui)?(?: no rio| no mapa)?$/)
      ?? t.match(/^(?:quem|o que|quais cidades) (?:fica|ficam|esta|estao) (?:a montante|acima|rio acima)(?: (?:de|do|da) (.+?)| daqui)?(?: no rio| no mapa)?$/)
      ?? t.match(/^de onde vem a agua(?: (?:de|do|da) (.+?)| daqui)?$/)
      ?? t.match(/^(?:o que fica )?(?:a )?montante(?: (?:de|do|da) (.+?)| daqui)?$/)
    if (m) {
      const c = cidadeOpcional(m[1], cat)
      return c ? [{ tipo: 'montante', foco: 'montante', ...c }] : null
    }
  }
  {
    const m = t.match(/^(?:quais (?:sao )?)?(?:os )?afluentes(?: (?:deste|desse|neste|nesse) trecho| daqui| (?:de|do|da|perto de|em) (.+?))?$/)
      ?? t.match(/^(?:o que|que rios?|quais rios?) (?:entra|entram|desagua|desaguam|chega|chegam) (?:no rio )?(?:aqui|neste trecho|nesse trecho|(?:perto de|em|antes de) (.+?))$/)
    if (m) {
      const c = cidadeOpcional(m[1], cat)
      return c ? [{ tipo: 'montante', foco: 'afluentes', ...c }] : null
    }
  }
  {
    const m = t.match(/^(?:(?:ver|veja|mostrar|mostre|mostra|abrir|abra|ir para|ir pra|va para|onde (?:fica|e|esta)) )?(?:a |o )?(?:confluencia|encontro|juncao|barra)(?: (?:do|da|de|dos|das) (.+?))?(?: com o .+)?$/)
      ?? t.match(/^onde (?:nasce|comeca) o (?:rio )?(itajai acu)$/)
    // "onde o Benedito entra no Açu?": só vira pedido quando o rio é um dos que o cadastro conhece — "onde a
    // água chega em Blumenau?" continua pergunta para o motor.
    const solto = m ? null : t.match(/^onde (?:o |a )?(?:rio |ribeirao )?(.+?) (?:entra|encontra|desagua|chega)(?: (?:no|na|ao|o|a|com o|com a) .+)?$/)
    if (solto) {
      const alvo = (solto[1] ?? '').trim()
      const achada = cat.confluencias?.find((c) => c.chaves.includes(alvo)) ?? cat.semPonto?.find((c) => c.chaves.includes(alvo))
      return achada ? [{ tipo: 'confluencia', id: achada.id }] : null
    }
    if (m) {
      const alvo = (m[1] ?? '').replace(/^(?:rio|ribeirao) /, '').trim()
      if (!alvo) return { erro: 'Confluência de qual rio?', sugestoes: ['ver a confluência do Benedito', 'onde o Trombudo encontra o Oeste', 'onde nasce o Itajaí-Açu'] }
      const nasce = /^itajai acu$|^acu$|cabeceiras|oeste com o sul/.test(alvo) ? 'itajai-acu-nasce' : null
      const achada = nasce ? cat.confluencias?.find((c) => c.id === nasce)
        : cat.confluencias?.find((c) => c.chaves.includes(alvo)) ?? cat.semPonto?.find((c) => c.chaves.includes(alvo))
      if (achada) return [{ tipo: 'confluencia', id: achada.id }]
      return { erro: `O cadastro não tem a confluência de "${alvo}".`, sugestoes: (cat.confluencias ?? []).map((c) => `ver a confluência do ${c.chaves[0]}`) }
    }
  }
  {
    const m = t.match(/^(?:comparar|compare|compara|comparacao das|lado a lado)(?: as)? reguas(?: (?:de|do|da|em) (.+?))?(?: lado a lado)?$/)
    if (m) {
      const c = cidadeOpcional(m[1], cat)
      return c ? [{ tipo: 'comparar_reguas', ...c }] : null
    }
  }
  {
    const m = t.match(/^(?:copiar|copie|copia|gerar|gere|preparar|prepare|montar|monte|compartilhar|compartilhe)(?: o| um)? (?:resumo|texto|situacao)(?: (?:desta|dessa|da) cidade| (?:de|do|da) (.+?))?(?: (?:para|pra|pro) (?:o )?(?:whatsapp|zap))?$/)
    if (m) {
      const c = cidadeOpcional(m[1], cat)
      return c ? [{ tipo: 'copiar_resumo', ...c }] : null
    }
  }
  if (/^(?:copiar|copie|copia|gerar|gere|me de|me da|compartilhar|compartilhe|qual (?:e )?)(?: o| um)? (?:link|endereco)(?: (?:desta|dessa|da) (?:visualizacao|tela|pagina|vista)| do mapa| daqui)?$/.test(t)) {
    return [{ tipo: 'copiar_link' }]
  }
  return null
}

const ABAS: Record<string, Aba> = { historico: 'historico', fontes: 'fontes', agora: 'agora' }

/** 18ª entrega: "… aqui", "… desta cidade" no fim do pedido é a cidade da tela — sai do texto e o executor decide. */
const AQUI_NO_FIM = / (?:aqui|daqui|desta cidade|nesta cidade|dessa cidade|nessa cidade|desta regua|nesta regua|neste trecho|nesse trecho)$/

function lerTrecho(t: string, cat: Catalogo, ctx: Contexto, cidadeDoPedido: string | null): Lido {
  const semAqui = t.replace(AQUI_NO_FIM, '')
  if (semAqui !== t && semAqui) {
    const lido = lerTrecho(semAqui, cat, ctx, cidadeDoPedido)
    if (lido) return lido
  }
  // 19ª: "e a tendência?", "e quanto falta?" — o "e" de continuação de assunto; o resto tem de ser um pedido inteiro.
  if (/^e [a-z]/.test(t) && !/^e (?:em|no|na|de|do|da|o|a|pra|para|sobre|la|ai) /.test(t)) {
    const lido = lerTrecho(t.slice(2), cat, ctx, cidadeDoPedido)
    if (lido) return lido
  }
  const decimaSexta = lerTrechoDaDecimaSexta(t, cat)
  if (decimaSexta) return decimaSexta
  const decimaQuinta = lerTrechoDaDecimaQuinta(t, cat)
  if (decimaQuinta) return decimaQuinta
  const decimaQuarta = lerTrechoDaDecimaQuarta(t, cat)
  if (decimaQuarta) return decimaQuarta
  const decimaTerceira = lerTrechoDaDecimaTerceira(t, cat)
  if (decimaTerceira) return decimaTerceira
  const decimaSegunda = lerTrechoDaDecimaSegunda(t, ctx)
  if (decimaSegunda) return decimaSegunda
  const oitava = lerTrechoDaOitava(t)
  if (oitava) return oitava
  const setima = lerTrechoDaSetima(t)
  if (setima) return setima
  const decimaPrimeira = lerTrechoDaDecimaPrimeira(t)
  if (decimaPrimeira) return decimaPrimeira
  const quinta = lerTrechoDaQuinta(t, cat)
  if (quinta) return quinta
  const sexta = lerTrechoDaSexta(t, cat)
  if (sexta) return sexta
  const quarta = lerTrechoDaQuarta(t, cat)
  if (quarta) return quarta
  const terceira = lerTrechoDaTerceira(t, cat)
  if (terceira) return terceira
  const segunda = lerTrechoDaSegunda(t, cat)
  if (segunda) return segunda
  // --- ajuda
  if (/^(?:o que (?:eu )?posso (?:pedir|fazer|perguntar|mandar)|quais (?:sao )?(?:os )?comandos|comandos|ajuda+|me ajuda|socorro|help|o que voce (?:faz|sabe fazer)|como (?:te )?usar(?: o chat)?)$/.test(t)) {
    return [{ tipo: 'ajuda' }]
  }
  // --- leitura do estado da tela
  if (/^o que (?:eu )?(?:estou|to|esto) vendo$|^o que (?:e|significa) (?:isso|essa tela|esta tela|esse mapa|este mapa)$|^explique? o mapa$|^o que (?:esta|ta|tem|aparece)(?: na tela| no mapa| aparecendo)?$/.test(t)) {
    return [{ tipo: 'o_que_vejo' }]
  }
  if (/\b(?:atual|agora) ou (?:e )?(?:historic[ao]|antig[ao]|passad[ao])\b|^(?:essa|esta) (?:informacao|leitura|camada) e (?:atual|de agora)$/.test(t)) {
    return [{ tipo: 'atual_ou_historico' }]
  }
  {
    const m = t.match(/^por ?que (?:(?:a|essa|esta) )?(?:(?:regua|cidade|estacao|bolinha|pino|bola) )?(?:(?:de|do|da) )?(.*?) ?(?:esta|ta|fica|ficou|aparece|e) (?:(?:em )?cinza|sem cor|sem faixa|apagad[ao]|sem leitura)$/)
    if (m) {
      const alvo = (m[1] ?? '').trim()
      if (!alvo) return [{ tipo: 'por_que_cinza' }]
      const c = cidadePorNome(alvo, cat)
      return c ? [{ tipo: 'por_que_cinza', cidadeId: c.id }] : null
    }
  }
  {
    const m = t.match(/^(?:(?:essa|esta|a) )?(?:coordenada|posicao|localizacao)(?: (?:da regua|do pino))?(?: (?:de|do|da) (.+?))? (?:foi|esta|e) confirmad[ao]$|^o pino(?: (?:de|do|da) (.+?))? esta no lugar certo$/)
    if (m) {
      const alvo = (m[1] ?? m[2] ?? '').trim()
      if (!alvo) return [{ tipo: 'coordenada' }]
      const c = cidadePorNome(alvo, cat)
      return c ? [{ tipo: 'coordenada', cidadeId: c.id }] : null
    }
  }
  // --- voltar no tempo e voltar a vista
  if (/^(?:ir|voltar|volte|volta|va|ver)(?: para| pra| ao| a)?(?: a| o)? (?:leitura )?(?:de |do )?(?:mais recente|ao vivo|agora|presente|tempo real)$|^(?:parar|pare|sair|saia)(?: da| a)? reproducao$|^(?:ao vivo|tempo real|leitura mais recente)$/.test(t)) {
    return [{ tipo: 'ao_vivo' }]
  }
  if (/^(?:ver|mostrar|mostre|mostra|enquadrar|enquadre|voltar para|voltar a|volta pra|volte para)?(?: a| o)? ?(?:bacia(?: toda| inteira)?|toda a bacia|tudo|mapa (?:todo|inteiro)|vale (?:todo|inteiro))$/.test(t)) {
    return [{ tipo: 'ver_bacia' }]
  }
  if (/^(?:voltar|volte|volta|desfazer|desfaca|desfaz)(?: ao| para o| pro| o)?(?: mapa| vista| visualizacao)?(?: de antes| anterior)?$|^(?:o )?mapa de antes$|^(?:desfazer|desfaca|desfaz)(?: a| o)? (?:ultima |ultimo )?(?:acao|mudanca|alteracao|comando|passo)$/.test(t)) {
    return [{ tipo: 'voltar' }]
  }
  // --- zoom
  if (/^(?:aproximar|aproxime|aproxima|aproximar mais|aproxime mais|aproxima mais|mais zoom|zoom|dar zoom|da zoom|ampliar|amplie|mais perto|chegar mais perto)$/.test(t)) {
    return [{ tipo: 'zoom', sentido: 'mais' }]
  }
  if (/^(?:afastar|afaste|afasta|menos zoom|diminuir(?: o)? zoom|diminua(?: o)? zoom|tirar(?: o)? zoom|mais longe|reduzir(?: o)? zoom)$/.test(t)) {
    return [{ tipo: 'zoom', sentido: 'menos' }]
  }
  // --- fundo do mapa
  {
    const m = t.match(/^(?:(?:ativar|ative|ativa|ligar|ligue|liga|mudar|mude|muda|trocar|troque|troca|usar|use|usa|colocar|coloque|coloca|por|poe|mostrar|mostre|mostra|ver)(?: o)?(?: fundo)?(?: para| pra| de| em)?(?: o| a)? )?(?:(?:o )?(?:fundo|modo|vista|mapa) (?:de |em )?)?(satelite|escuro|ruas|mapa de ruas|claro|normal)$/)
    if (m) {
      const f: Fundo = m[1] === 'satelite' ? 'satelite' : m[1] === 'escuro' ? 'escuro' : 'mapa'
      return [{ tipo: 'fundo', fundo: f }]
    }
  }
  // --- camadas de cheia (manchas)
  {
    // "camada: <rótulo>" vem das sugestões do próprio chat, com o rótulo exato que o Monitor oferece.
    const m = t.match(/^camada (.+)$/)
    const ano = m?.[1]?.match(/^(?:de |da cheia de |do ano de |da enchente de )?(\d{4})$/)
    if (ano?.[1]) return [{ tipo: 'camada', acao: 'ligar', ano: ano[1] }]
    if (m?.[1] && !/^(?:de |da |do )?(?:cheia|inundacao|enchente)$/.test(m[1])) return [{ tipo: 'camada', acao: 'ligar', rotulo: m[1] }]
  }
  if (/^(?:desligar|desligue|desliga|ocultar|oculte|oculta|esconder|esconda|esconde|tirar|tire|tira|remover|remova|remove|apagar|apague|apaga)(?: as| a)? (?:manchas?|camadas?)(?: de (?:cheia|inundacao|enchente))?$/.test(t)) {
    return [{ tipo: 'camada', acao: 'desligar' }]
  }
  {
    const m = t.match(/^(?:(?:ligar|ligue|liga|ativar|ative|ativa|mostrar|mostre|mostra|exibir|exiba|exibe|ver)(?: as| a)? )?(?:manchas?|camadas?)(?: de (?:cheia|inundacao|enchente))?(?: (?:de |da cheia de |do ano de |da enchente de )?(\d{4}))?$/)
    if (m && (m[1] || /^(?:ligar|ligue|liga|ativar|ative|ativa|mostrar|mostre|mostra|exibir|exiba|exibe|ver)\b/.test(t))) {
      return [{ tipo: 'camada', acao: 'ligar', ...(m[1] ? { ano: m[1] } : {}) }]
    }
  }
  // --- páginas
  if (/^(?:abrir|abra|abre|ver|mostrar|mostre|ir para|ir pra|va para)?(?: o)? ?(?:mapa|pagina) (?:das|de) manchas(?: de itajai)?$/.test(t)) {
    return [{ tipo: 'abrir_rota', rota: '/itajai?secao=manchas', descricao: 'o mapa das manchas de Itajaí' }]
  }
  if (/^(?:(?:abrir|abra|abre|ver|ir para|ir pra|va para|voltar para|voltar ao|volte ao|volte para) )?(?:o |a )?(?:inicio|pagina inicial|comeco)$/.test(t)) {
    return [{ tipo: 'abrir_rota', rota: '/', descricao: 'o início' }]
  }
  if (/^(?:abrir|abra|abre|ver|mostrar|mostre|ir para|ir pra|va para)(?: o)? (?:rio )?itajai acu$/.test(t)) {
    return [{ tipo: 'abrir_rota', rota: '/acu', descricao: 'a página do Itajaí-Açu' }]
  }
  if (/^(?:abrir|abra|abre|ver|mostrar|mostre|ir para|ir pra|va para)(?: o)? (?:rio )?(?:itajai )?mirim$/.test(t)) {
    return [{ tipo: 'abrir_rota', rota: '/mirim', descricao: 'a página do Itajaí-Mirim' }]
  }
  if (/^(?:(?:abrir|abra|abre|ver|mostrar|mostre|ir para|ir pra|va para) )?(?:a )?(?:pagina da |tela da )?foz$/.test(t) && t !== 'foz') {
    return [{ tipo: 'abrir_rota', rota: '/itajai', descricao: 'a página da foz, em Itajaí' }]
  }
  if (/^(?:abrir|abra|abre|ver|ir para|ir pra|va para)(?: o)? monitor(?: da bacia| inteiro| geral)?$/.test(t)) {
    return [{ tipo: 'monitor_bacia' }]
  }
  {
    // "página do Itajaí-Mirim", "a página do rio Itajaí-Açu"
    const m = t.match(/^(?:abrir|abra|abre|ver|mostrar|mostre|ir para|ir pra|va para)?(?: a)? ?pagina do (?:rio )?(itajai acu|acu|itajai mirim|mirim)$/)
    if (m) {
      return /mirim/.test(m[1]!)
        ? [{ tipo: 'abrir_rota', rota: '/mirim', descricao: 'a página do Itajaí-Mirim' }]
        : [{ tipo: 'abrir_rota', rota: '/acu', descricao: 'a página do Itajaí-Açu' }]
    }
  }
  // 18ª entrega: na página da cidade (ou no Monitor dela), uma palavra basta: "histórico", "minha rua", "fontes".
  if (ctx.cidadeAtual) {
    const m = t.match(/^(?:abrir|abra|abre|ver|mostrar|mostre|ir para|ir pra|va para)?(?: o| a| as)? ?(historico|fontes|minha rua)(?: (?:desta|dessa|da) cidade| daqui)?$/)
    if (m) {
      const aba = m[1] === 'minha rua' ? 'rua' : ABAS[m[1] ?? '']
      return [{ tipo: 'abrir_pagina', cidadeId: ctx.cidadeAtual, ...(aba ? { aba } : {}) }]
    }
  }
  {
    const m = t.match(/^(?:abrir|abra|abre|ver|mostrar|mostre|ir para|ir pra|va para)?(?: a| o| as)? ?(pagina|historico|fontes|agora|minha rua) (?:de|do|da|em) (.+)$/)
    if (m) {
      const c = cidadePorNome(m[2] ?? '', cat)
      if (!c) return null
      const aba = m[1] === 'minha rua' ? 'rua' : ABAS[m[1] ?? '']
      return [{ tipo: 'abrir_pagina', cidadeId: c.id, ...(aba ? { aba } : {}) }]
    }
  }
  // --- réguas
  if (/^(?:(?:mostrar|mostre|ver|veja|selecionar|selecione|voltar para|volte para)(?: a| as)? )?todas(?: as)? reguas(?: de itajai)?$/.test(t)) {
    return [{ tipo: 'escolher_regua', codigo: 'todas' }]
  }
  {
    // "zoom na régua DC-05", "aproxime a régua", "régua do Rio do Meio", "régua de Blumenau", "zoom na DC 5"
    const m = t.match(new RegExp(`^(?:${VERBO_IR}(?: (?:em|no|na|para|pra|ate|a|o))*\\s+)?(?:(?:a|na) )?(?:regua|estacao)(?: (.+))?$`))
      ?? t.match(new RegExp(`^(?:${VERBO_IR}(?: (?:em|no|na|para|pra|a|o))*\\s+)(dc\\s*\\d{1,2})$`))
    if (m) {
      const alvo = (m[1] ?? '').replace(ARTIGOS, '').trim()
      if (!alvo || /^(?:daqui|desta cidade|dessa cidade|selecionada|atual)$/.test(alvo)) return [{ tipo: 'aproximar_regua' }]
      const porCodigo = reguaPorCodigo(alvo, cat)
      if (porCodigo === 'inexistente') {
        return { erro: `Não há régua "${alvo.toUpperCase()}" no cadastro.`, sugestoes: cat.reguas.slice(0, 4).map((r) => `zoom na régua ${rotuloDaRegua(r)}`) }
      }
      if (porCodigo) return [{ tipo: 'escolher_regua', codigo: porCodigo.codigo }]
      const c = cidadePorNome(alvo, cat)
      if (c) return [{ tipo: 'ir_cidade', cidadeId: c.id }, { tipo: 'aproximar_regua' }]
      const porNome = reguasPorNome(alvo, cat)
      if (porNome.length === 1 && porNome[0]) return [{ tipo: 'escolher_regua', codigo: porNome[0].codigo }]
      const parecidas = porNome.length > 1 ? porNome : reguasParecidas(alvo, cat)
      if (parecidas.length > 0) {
        return { erro: `Qual régua? "${alvo}" pode ser mais de uma.`, sugestoes: parecidas.map((r) => `zoom na régua ${rotuloDaRegua(r)}`) }
      }
      return { erro: `Não achei a régua "${alvo}" no cadastro.`, sugestoes: ['o que posso pedir?'] }
    }
  }
  // --- cidade (exige verbo: "Blumenau" sozinho continua pergunta para o motor)
  {
    const m = t.match(new RegExp(`^${VERBO_IR}(?: (?:para|pra|em|no|na|de|ate|a|o))*\\s+(.+)$`))
    if (m) {
      const c = cidadePorNome(m[1] ?? '', cat)
      if (c) return [{ tipo: 'ir_cidade', cidadeId: c.id }]
    }
  }
  void cidadeDoPedido
  return null
}

/**
 * 18ª entrega: pedido de ALTERAR dado do site ("mude o nível de Blumenau para 10 m", "registrar pico de 12 m",
 * "apagar o histórico de Blumenau"). Não é comando e não vai ao motor palpitar: o chat diz que não altera dados.
 * Lido depois de todos os leitores, para "apagar as manchas", "limpar a conversa" e "mudar minha cidade" continuarem
 * sendo os comandos que são.
 */
const VERBO_DE_ALTERACAO = /^(?:mude|mudar|muda|altere|alterar|altera|corrija|corrigir|corrige|registre|registrar|registra|cadastre|cadastrar|cadastra|apague|apagar|apaga|exclua|excluir|exclui|delete|deletar|deleta|edite|editar|edita|insira|inserir|insere|grave|gravar|grava|salve|salvar|salva|zere|zerar|remova|remover|remove|ajuste|ajustar|ajusta|lance|lancar|lanca|adicione|adicionar|adiciona|inclua|incluir|inclui)\b/
const DADO_DO_SITE = /\b(?:nivel|niveis|cotas?|picos?|historico|leituras?|registros?|dados?|medic(?:ao|oes)|coordenadas?|recordes?)\b/
export function pedeAlteracaoDeDado(t: string): boolean {
  return VERBO_DE_ALTERACAO.test(t) && DADO_DO_SITE.test(t)
}
const TEXTO_NAO_ALTERA =
  'O chat não altera dados do site: níveis, cotas, picos e registros vêm das fontes (Defesa Civil, AlertaBlu, ANA) e só mudam no cadastro, por decisão de pessoa, com a fonte aberta. Posso mostrar o que já existe ou preparar um relato de problema.'
const ENDERECO_DIGITADO = /https?:\/\/|(?:^|\s)\/[a-z]/i
const TEXTO_SEM_ENDERECO =
  'Não abro endereços nem rotas digitadas. Peça pela tela: "abrir o monitor", "abrir o início", "mostrar Blumenau", "histórico de Gaspar".'

/**
 * O texto é pedido? `null` = não: vai para o motor de perguntas.
 * Régua de cidade com várias réguas (Itajaí) sem escolha: pergunta qual, com as opções — nunca escolhe uma.
 */
/**
 * O texto vira passos tipados, uma pergunta de esclarecimento ou `null` (pergunta para o motor). Sem nada
 * entendido, tenta o nome de cidade com erro de digitação (9ª entrega): se a frase corrigida vira comando,
 * o chat PERGUNTA "Você quis dizer…?" e não faz nada.
 */
export function interpretar(texto: string, cat: Catalogo, ctx: Contexto): Interpretacao | null {
  // 18ª entrega: endereço ou rota digitada nunca é comando, nem vai ao motor.
  if (ENDERECO_DIGITADO.test(texto)) return { tipo: 'esclarecer', texto: TEXTO_SEM_ENDERECO, sugestoes: ['abrir o monitor', 'abrir o início', 'o que posso pedir?'] }
  const inteiro = expandirAbreviacoes(normalizar(texto))
  const repetida = palavraRepetida(inteiro)
  if (repetida) return { tipo: 'esclarecer', texto: `O pedido repete "${repetida}" muitas vezes e eu não sei o que fazer com ele. Peça uma vez só.`, sugestoes: ['o que posso pedir?'] }
  const rio = inteiro.match(RIO_NO_MAPA)
  if (rio) return { tipo: 'comandos', passos: [{ tipo: 'enquadrar', alvo: 'rio', rioId: /mirim/.test(rio[1]!) ? 'itajai-mirim' : 'itajai-acu' }] }
  if (BARRAGENS_NO_MAPA.test(inteiro)) return { tipo: 'comandos', passos: [{ tipo: 'enquadrar', alvo: 'barragens' }] }
  const r = interpretarAoPeDaLetra(texto, cat, ctx)
  if (r && r.tipo === 'comandos') return r
  if (r && !r.texto.startsWith(NAO_ENTENDI_PARTE)) return r
  const limpo = semCortesia(inteiro)
  // Pedido de alterar dado: recusa dita, nada executado, nada palpitado.
  if (pedeAlteracaoDeDado(limpo)) return { tipo: 'esclarecer', texto: TEXTO_NAO_ALTERA, sugestoes: ['relatar problema nesta régua', 'de onde vem essa leitura?', 'o que posso pedir?'] }
  const c = corrigirCidade(texto, cat.cidades)
  if (c) {
    const corrigido = interpretarAoPeDaLetra(c.texto, cat, ctx)
    if (corrigido && corrigido.tipo === 'comandos') return { tipo: 'esclarecer', texto: textoDaCorrecao(c, 'comando'), sugestoes: [c.texto] }
  }
  // Só o nome de uma cidade: pergunta o que a pessoa quer dela, com exemplos (antes, o motor palpitava "maiores cheias").
  const so = cidadePorNome(limpo, cat)
  if (so && !r) {
    return {
      tipo: 'esclarecer',
      texto: `O que você quer saber de ${so.nome}? Posso dizer como está agora, mostrar no mapa, dizer quanto falta para a cota ou buscar o histórico.`,
      sugestoes: [`como está ${so.nome}?`, `mostrar ${so.nome}`, `quanto falta para a cota em ${so.nome}?`, `maior cheia de ${so.nome}`],
    }
  }
  // Verbo com erro de digitação ("msotrar blumenau"): como no nome da cidade, pergunta e não executa.
  const v = corrigirVerbo(limpo)
  if (v && !r) {
    const corrigido = interpretarAoPeDaLetra(v.texto, cat, ctx)
    if (corrigido && corrigido.tipo === 'comandos') {
      return { tipo: 'esclarecer', texto: `Não conheço "${v.errado}". Você quis dizer "${v.texto}"? Nada foi feito; toque na sugestão para confirmar.`, sugestoes: [v.texto] }
    }
  }
  return r
}

/** Uma palavra repetida 6+ vezes num pedido longo ("mostrar Blumenau" × 30): não é pedido, é ruído. */
function palavraRepetida(t: string): string | null {
  const palavras = t.split(' ').filter(Boolean)
  if (palavras.length < 12) return null
  const contagem = new Map<string, number>()
  for (const w of palavras) contagem.set(w, (contagem.get(w) ?? 0) + 1)
  for (const [w, n] of contagem) if (n >= 6 && w.length >= 3) return w
  return null
}

/**
 * As palavras que abrem ou nomeiam pedidos (verbos e telas/peças): um erro de até 2 letras numa palavra de 6+ (1 letra
 * em 5) vira sugestão "você quis dizer…?", desde que a frase corrigida seja um comando. Uma palavra por vez, a
 * primeira que der certo. Nomes de cidade têm a própria correção (9ª entrega).
 */
const PALAVRAS_DE_PEDIDO = [
  'mostrar', 'mostre', 'mostra', 'abrir', 'abra', 'abre', 'aproximar', 'aproxime', 'afastar', 'afaste', 'ligar', 'ligue', 'desligar',
  'desligue', 'copiar', 'copie', 'comparar', 'compare', 'atualizar', 'atualize', 'voltar', 'volte', 'fechar', 'feche', 'seguir', 'siga',
  'quanto', 'quando', 'quais', 'quantas', 'pausar', 'pause', 'reproduzir', 'limpar', 'limpe', 'apagar', 'apague', 'usar', 'relatar',
  'instalar', 'enquadrar', 'focar', 'centralizar', 'selecionar', 'levar', 'ver',
  'monitor', 'inicio', 'historico', 'fontes', 'legenda', 'satelite', 'escuro', 'manchas', 'camadas', 'reguas', 'regua', 'leituras',
  'barragens', 'grafico', 'resumo', 'tendencia', 'alerta', 'atencao', 'bacia', 'painel', 'conversa', 'localizacao', 'confluencia',
]
function corrigirVerbo(t: string): { texto: string; errado: string } | null {
  const palavras = t.split(' ')
  if (palavras.length < 2) return null
  for (let i = 0; i < palavras.length; i++) {
    const p = palavras[i]!
    if (p.length < 5 || PALAVRAS_DE_PEDIDO.includes(p)) continue
    const limite = p.length >= 6 ? 2 : 1
    const distancias = PALAVRAS_DE_PEDIDO.map((v) => ({ v, d: distanciaDeEdicao(p, v, limite) })).filter((x) => x.d <= limite)
    if (distancias.length === 0) continue
    const menor = Math.min(...distancias.map((x) => x.d))
    const candidatos = distancias.filter((x) => x.d === menor)
    if (candidatos.length !== 1) continue
    return { texto: [...palavras.slice(0, i), candidatos[0]!.v, ...palavras.slice(i + 1)].join(' '), errado: p }
  }
  return null
}

const NAO_ENTENDI_PARTE = 'Não entendi esta parte do pedido'

function interpretarAoPeDaLetra(texto: string, cat: Catalogo, ctx: Contexto): Interpretacao | null {
  const t = semCortesia(expandirAbreviacoes(normalizar(texto)))
  if (!t) return null
  // A frase inteira primeiro: "essa informação é atual" tem um "e" que não é conjunção.
  const partes = lerTrecho(t, cat, ctx, ctx.cidadeAtual) !== null ? [t] : trechos(texto)
  const passos: Passo[] = []
  const naoEntendidos: string[] = []
  let algum = false
  // A cidade "em foco" ao longo do pedido: a do contexto, trocada por um "mostre X" anterior.
  let cidade = ctx.cidadeAtual
  let regua = ctx.reguaAtual
  for (const p of partes) {
    const lido = lerTrecho(p, cat, ctx, cidade)
    if (lido === null) {
      naoEntendidos.push(p)
      continue
    }
    algum = true
    if (!Array.isArray(lido)) return { tipo: 'esclarecer', texto: lido.erro, sugestoes: lido.sugestoes }
    for (const passo of lido) {
      if (passo.tipo === 'ir_cidade') {
        cidade = passo.cidadeId
        regua = null
      }
      if (passo.tipo === 'escolher_regua' && passo.codigo !== 'todas') {
        regua = passo.codigo
        cidade = cat.reguas.find((r) => r.codigo === passo.codigo)?.cidadeId ?? cidade
      }
      if (passo.tipo === 'aproximar_regua' && cidade && !regua) {
        const daCidade = cat.reguas.filter((r) => r.cidadeId === cidade)
        if (daCidade.length > 1) {
          return {
            tipo: 'esclarecer',
            texto: `${nomeDaCidade(cidade, cat)} tem ${daCidade.length} réguas. Qual delas?`,
            sugestoes: daCidade.map((r) => `zoom na régua ${rotuloDaRegua(r)}`),
          }
        }
      }
      passos.push(passo)
    }
  }
  if (!algum) return null
  if (naoEntendidos.length > 0) {
    return {
      tipo: 'esclarecer',
      texto: `${NAO_ENTENDI_PARTE}: "${naoEntendidos.join('", "')}". Nada foi feito. Peça de novo sem ela, ou veja o que posso fazer.`,
      sugestoes: ['o que posso pedir?'],
    }
  }
  return { tipo: 'comandos', passos }
}

export function nomeDaCidade(id: string, cat: Catalogo): string {
  return cat.cidades.find((c) => c.id === id)?.nome ?? id
}
