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
import type { Aba, Catalogo, CidadeDoCatalogo, Contexto, Fundo, Interpretacao, Passo, ReguaDoCatalogo } from './tipos'

/** Minúsculo, sem acento, sem pontuação; hífen vira espaço ("DC-05" → "dc 05", "rio-do-sul" → "rio do sul"). */
export function normalizar(s: string): string {
  return s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

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
function trechos(texto: string): string[] {
  return texto
    .split(/[,;]/)
    .flatMap((parte) => normalizar(parte).split(/\s*(?:\be depois\b|\bdepois\b|\be em seguida\b|\bem seguida\b|\be entao\b|\bentao\b|\be\b)\s*/))
    .map((x) => semCortesia(x.trim()))
    .filter(Boolean)
}

const ARTIGOS = /^(?:(?:o|a|os|as|de|do|da|dos|das|em|no|na|para|pra|pro|ao|a cidade de|o mapa de|o monitor de|o pino de)\s+)+/

function cidadePorNome(alvo: string, cat: Catalogo): CidadeDoCatalogo | null {
  const a = alvo.replace(ARTIGOS, '').trim()
  if (!a) return null
  return cat.cidades.find((c) => normalizar(c.nome) === a || normalizar(c.id) === a) ?? null
}

const VERBO_IR =
  '(?:mostrar|mostre|mostra|ver|veja|abrir|abra|abre|ir|va|vai|leve me|centralizar|centralize|focar|foque|enquadrar|enquadre|selecionar|selecione|zoom|aproximar|aproxime|aproxima)'

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

const ABAS: Record<string, Aba> = { historico: 'historico', fontes: 'fontes', agora: 'agora' }

function lerTrecho(t: string, cat: Catalogo, ctx: Contexto, cidadeDoPedido: string | null): Lido {
  // --- ajuda
  if (/^(?:o que (?:eu )?posso (?:pedir|fazer|perguntar|mandar)|quais (?:sao )?(?:os )?comandos|comandos|ajuda|o que voce (?:faz|sabe fazer)|como (?:te )?usar(?: o chat)?)$/.test(t)) {
    return [{ tipo: 'ajuda' }]
  }
  // --- leitura do estado da tela
  if (/^o que (?:eu )?(?:estou|to|esto) vendo$|^o que (?:e|significa) (?:isso|essa tela|esta tela|esse mapa|este mapa)$|^explique? o mapa$/.test(t)) {
    return [{ tipo: 'o_que_vejo' }]
  }
  if (/\b(?:atual|agora) ou (?:historic[ao]|antig[ao]|passad[ao])\b|^(?:essa|esta) (?:informacao|leitura|camada) e (?:atual|de agora)$/.test(t)) {
    return [{ tipo: 'atual_ou_historico' }]
  }
  {
    const m = t.match(/^por ?que (?:(?:a|essa|esta) )?(?:(?:regua|cidade|estacao|bolinha|pino|bola) )?(?:(?:de|do|da) )?(.*?) ?(?:esta|ta|fica|ficou|aparece|e) (?:em )?cinza$/)
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
  if (/^(?:ir|voltar|volte|volta|va|ver)(?: para| pra| ao| a)?(?: a| o)? (?:leitura )?(?:mais recente|ao vivo|agora|presente|tempo real)$|^(?:parar|pare|sair|saia)(?: da)? reproducao$/.test(t)) {
    return [{ tipo: 'ao_vivo' }]
  }
  if (/^(?:ver|mostrar|mostre|mostra|enquadrar|enquadre|voltar para|voltar a|volta pra|volte para)?(?: a| o)? ?(?:bacia(?: toda| inteira)?|toda a bacia|tudo|mapa (?:todo|inteiro)|vale (?:todo|inteiro))$/.test(t)) {
    return [{ tipo: 'ver_bacia' }]
  }
  if (/^(?:voltar|volte|volta|desfazer|desfaca|desfaz)(?: ao| para o| pro| o)?(?: mapa| vista| visualizacao)?(?: de antes| anterior)?$|^(?:o )?mapa de antes$/.test(t)) {
    return [{ tipo: 'voltar' }]
  }
  // --- zoom
  if (/^(?:aproximar|aproxime|aproxima|mais zoom|zoom|ampliar|amplie|mais perto|chegar mais perto)$/.test(t)) {
    return [{ tipo: 'zoom', sentido: 'mais' }]
  }
  if (/^(?:afastar|afaste|afasta|menos zoom|diminuir(?: o)? zoom|diminua(?: o)? zoom|tirar(?: o)? zoom|mais longe|reduzir(?: o)? zoom)$/.test(t)) {
    return [{ tipo: 'zoom', sentido: 'menos' }]
  }
  // --- fundo do mapa
  {
    const m = t.match(/^(?:(?:ativar|ative|ligar|ligue|mudar|mude|trocar|troque|usar|use|colocar|coloque|por|mostrar|mostre|ver)(?: o)?(?: fundo)?(?: para| pra| de| em)? )?(?:(?:o )?(?:fundo|modo|vista|mapa) (?:de |em )?)?(satelite|escuro|ruas|mapa de ruas|claro|normal)$/)
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
  if (/^(?:desligar|desligue|ocultar|oculte|esconder|esconda|tirar|tire|remover|remova|apagar|apague)(?: as| a)? (?:manchas?|camadas?)(?: de (?:cheia|inundacao|enchente))?$/.test(t)) {
    return [{ tipo: 'camada', acao: 'desligar' }]
  }
  {
    const m = t.match(/^(?:(?:ligar|ligue|ativar|ative|mostrar|mostre|exibir|exiba|ver)(?: as| a)? )?(?:manchas?|camadas?)(?: de (?:cheia|inundacao|enchente))?(?: (?:de|da cheia de|do ano de|da enchente de) (\d{4}))?$/)
    if (m && (m[1] || /^(?:ligar|ligue|ativar|ative|mostrar|mostre|exibir|exiba|ver)\b/.test(t))) {
      return [{ tipo: 'camada', acao: 'ligar', ...(m[1] ? { ano: m[1] } : {}) }]
    }
  }
  // --- páginas
  if (/^(?:abrir|abra|abre|ver|mostrar|mostre|ir para|ir pra|va para)?(?: o)? ?(?:mapa|pagina) (?:das|de) manchas(?: de itajai)?$/.test(t)) {
    return [{ tipo: 'abrir_rota', rota: '/itajai?secao=manchas', descricao: 'o mapa das manchas de Itajaí' }]
  }
  if (/^(?:abrir|abra|abre|ver|ir para|ir pra|va para|voltar para|voltar ao|volte ao|volte para)?(?: o| a)? ?(?:inicio|pagina inicial|comeco)$/.test(t)) {
    return [{ tipo: 'abrir_rota', rota: '/', descricao: 'o início' }]
  }
  if (/^(?:abrir|abra|abre|ver|mostrar|mostre|ir para|ir pra|va para)(?: o)? (?:rio )?itajai acu$/.test(t)) {
    return [{ tipo: 'abrir_rota', rota: '/acu', descricao: 'a página do Itajaí-Açu' }]
  }
  if (/^(?:abrir|abra|abre|ver|mostrar|mostre|ir para|ir pra|va para)(?: o)? (?:rio )?(?:itajai )?mirim$/.test(t)) {
    return [{ tipo: 'abrir_rota', rota: '/mirim', descricao: 'a página do Itajaí-Mirim' }]
  }
  if (/^(?:abrir|abra|abre|ver|mostrar|mostre|ir para|ir pra|va para)(?: a)? foz$/.test(t)) {
    return [{ tipo: 'abrir_rota', rota: '/itajai', descricao: 'a página da foz, em Itajaí' }]
  }
  if (/^(?:abrir|abra|abre|ver|ir para|ir pra|va para)(?: o)? monitor$/.test(t)) {
    return [{ tipo: 'monitor_bacia' }]
  }
  {
    const m = t.match(/^(?:abrir|abra|abre|ver|mostrar|mostre|ir para|ir pra|va para)?(?: a| o)? ?(pagina|historico|fontes|agora|minha rua) (?:de|do|da|em) (.+)$/)
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
  void ctx
  void cidadeDoPedido
  return null
}

/**
 * O texto é pedido? `null` = não: vai para o motor de perguntas.
 * Régua de cidade com várias réguas (Itajaí) sem escolha: pergunta qual, com as opções — nunca escolhe uma.
 */
export function interpretar(texto: string, cat: Catalogo, ctx: Contexto): Interpretacao | null {
  const t = semCortesia(normalizar(texto))
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
      texto: `Não entendi esta parte do pedido: "${naoEntendidos.join('", "')}". Nada foi feito. Peça de novo sem ela, ou veja o que posso fazer.`,
      sugestoes: ['o que posso pedir?'],
    }
  }
  return { tipo: 'comandos', passos }
}

export function nomeDaCidade(id: string, cat: Catalogo): string {
  return cat.cidades.find((c) => c.id === id)?.nome ?? id
}
