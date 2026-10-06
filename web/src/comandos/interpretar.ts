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
import type { TemaDaLegenda } from './foz'

import { normalizar } from './normalizar'
import { arquivoPeloNome } from './rios'

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

const AQUI = /^(?:aqui|daqui|desta cidade|dessa cidade|deste lugar|desse lugar|desta regua|dessa regua|deste trecho|desse trecho|neste trecho|nesse trecho|da cidade|da regua)$/

/**
 * A cidade opcional de um pedido ("… de Gaspar"). Sem alvo, ou "daqui": o contexto decide na execução.
 * Alvo que não é cidade do cadastro: `null` — o trecho não vira comando (e o motor de perguntas tenta).
 */
function cidadeOpcional(alvo: string | undefined, cat: Catalogo): { cidadeId?: string } | null {
  const a = (alvo ?? '').trim()
  if (!a || AQUI.test(a)) return {}
  const c = cidadePorNome(a, cat)
  return c ? { cidadeId: c.id } : null
}

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
  if (/^(?:como (?:estao|esta|tao)(?: as| a)?|qual (?:e )?o estado (?:das|da)) barragens?(?: de contencao| do alto vale)?(?: agora)?$|^(?:as )?barragens?(?: agora)?$|^(?:as )?comportas(?: das barragens)?(?: estao)?(?: abertas| fechadas)?$/.test(t)) {
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

/** A 8ª entrega: o site e os seus dados (atualizar, aviso, instalar, privacidade, conversa, emergência). */
function lerTrechoDaOitava(t: string): Lido {
  if (/^(?:atualizar|atualize|atualiza|recarregar|recarregue|recarrega|buscar de novo|busque de novo|busca de novo)(?: as| os| a| o)?(?: leituras| dados| niveis| numeros| medicoes| mapa| pagina| tudo)?(?: agora)?$|^(?:tem|ha|chegou) (?:leitura|medicao|dado) nov[ao]$/.test(t)) {
    return [{ tipo: 'atualizar' }]
  }
  if (/^(?:isso|isto|este site|esse site|o site)(?: aqui)? e oficial$|^(?:o que e|para que serve) (?:este|esse|o) site$|^(?:ler|leia|mostrar|mostre|ver)(?: o)? aviso(?: legal)?$|^(?:este|esse|o) site e (?:um )?(?:alerta|sistema) oficial$/.test(t)) {
    return [{ tipo: 'oficial' }]
  }
  if (/^(?:como )?(?:instalar|instalo|instale|baixar|baixo|baixe)(?: o)? (?:app|aplicativo|site)(?: no celular| no telefone| na tela inicial)?$|^(?:tem|existe) (?:app|aplicativo)$|^(?:adicionar|adiciono|colocar|coloco)(?: o site)? na tela (?:inicial|de inicio)$/.test(t)) {
    return [{ tipo: 'instalar' }]
  }
  if (/^o que (?:o site|voce|vc) (?:guarda|sabe|grava|salva) (?:de mim|sobre mim|no (?:meu )?(?:celular|aparelho|telefone))$|^quais (?:sao )?(?:os )?meus dados(?: guardados)?$|^privacidade$|^o site (?:me rastreia|guarda minha localizacao|grava minhas perguntas|guarda minhas perguntas)$/.test(t)) {
    return [{ tipo: 'privacidade' }]
  }
  {
    const m = t.match(/^(sim )?(?:apagar|apague|esquecer|esqueca|limpar|limpe|zerar|zere)(?: as| os| todas as| todos os)? (?:minhas preferencias|meus dados|preferencias|dados do aparelho|o que o site guarda)$/)
    if (m) return [{ tipo: 'esquecer', confirmado: !!m[1] }]
  }
  if (/^(?:nao|parar de|pare de) contar (?:as )?minhas perguntas$|^(?:desligar|desligue) (?:a )?contagem(?: do chat)?$/.test(t)) return [{ tipo: 'contagem', permitir: false }]
  if (/^(?:pode )?contar (?:as )?minhas perguntas$|^(?:ligar|ligue|religar) (?:a )?contagem(?: do chat)?$/.test(t)) return [{ tipo: 'contagem', permitir: true }]
  if (/^(?:limpar|limpe|apagar|apague|zerar|zere)(?: a| esta| essa)? (?:conversa|historico do chat)$/.test(t)) return [{ tipo: 'limpar_conversa' }]
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
const FAIXA_PARA_TEMA: Record<string, TemaDaLegenda> = {
  'abaixo da atencao': 'normal', monitoramento: 'monitoramento', observacao: 'monitoramento', atencao: 'atencao', alerta: 'alerta',
  prontidao: 'alerta', 'alerta maximo': 'inundacao', inundacao: 'inundacao', emergencia: 'inundacao', 'sem dado': 'sem-dado',
  'varias reguas': 'varias',
}
function lerTrechoDaSetima(t: string): Lido {
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
    const cor = t.match(/^o que (?:significa|quer dizer|e|indica)(?: a cor| o| a)? (verde claro|verde|amarelo|laranja|vermelho|cinza|azul|violeta|roxo|lilas)(?: no mapa| no rio| na legenda)?$/)
    if (cor) return [{ tipo: 'legenda', tema: COR_PARA_TEMA[cor[1]!]! }]
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
  }
  {
    const m = t.match(new RegExp(`^(?:qual (?:foi |e )?)?(?:o |a )?(?:minimo e (?:o )?)?(?:maximo|pico|maior nivel|nivel maximo|nivel mais alto|maxima)(?: e (?:o )?minimo)?(?: do rio| do nivel)? (?:(?:das|nas|em) ultimas 24 ?(?:h|horas)|de hoje|hoje|em 24 ?(?:h|horas))${EM_CIDADE}$`))
    if (m) return comCidade(m[1], (c) => ({ tipo: 'maximo_24h', ...c }))
  }
  if (/^(?:quais|que|tem|ha|alguma|algumas|existe|existem)(?: as)? (?:cidades?|reguas?)(?: (?:estao|esta|tao|ta))? (?:em|no|na|acima da cota de) (?:alerta|atencao|emergencia|inundacao|cota de alerta)(?: agora)?$|^(?:como (?:esta|ta) a bacia|como (?:estao|tao) (?:os rios|as cidades)|resumo da bacia|panorama(?: da bacia)?|situacao da bacia)(?: agora| toda| inteira)?$/.test(t)) {
    return [{ tipo: 'panorama' }]
  }
  {
    const m = t.match(/^o que (?:vem|esta vindo|ta vindo|desce|esta descendo) (?:de cima|do alto vale|de montante|rio abaixo)(?: (?:para|pra|ate|em|sobre) (.+?))?(?: agora)?$/)
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
  if (/^(?:(?:abrir|abra|ativar|ative|ligar|ligue|colocar|coloque|por|ver|mostrar|entrar)(?: em| no| a| o)? )?(?:modo )?tela cheia$|^(?:maximizar|maximize)(?: o)? mapa$/.test(t)) {
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
    const m = t.match(/^o que (?:fica|esta|vem|tem|ha) (?:a montante|acima|rio acima)(?: (?:de|do|da) (.+?)| daqui)?$/)
      ?? t.match(/^(?:quem|o que|quais cidades) (?:fica|ficam|esta|estao) (?:a montante|acima|rio acima)(?: (?:de|do|da) (.+?)| daqui)?$/)
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
    const m = t.match(/^(?:comparar|compare|compara|comparacao das|lado a lado)(?: as)? reguas(?: (?:de|do|da|em) (.+))?$/)
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

function lerTrecho(t: string, cat: Catalogo, ctx: Contexto, cidadeDoPedido: string | null): Lido {
  const oitava = lerTrechoDaOitava(t)
  if (oitava) return oitava
  const setima = lerTrechoDaSetima(t)
  if (setima) return setima
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
  if (/^(?:ir|voltar|volte|volta|va|ver)(?: para| pra| ao| a)?(?: a| o)? (?:leitura )?(?:mais recente|ao vivo|agora|presente|tempo real)$|^(?:parar|pare|sair|saia)(?: da| a)? reproducao$/.test(t)) {
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
