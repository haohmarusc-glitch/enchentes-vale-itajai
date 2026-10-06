/**
 * Executa os passos de um pedido, em ordem, e diz o resultado REAL de cada um
 * (docs/CHAT-GLOBAL-COMANDOS.md, 06/10/2026).
 *
 * - Passo que precisa do mapa, fora do Monitor: abre o Monitor (na cidade da página, se houver) e espera ele
 *   ficar pronto. Não ficou: diz isso e para.
 * - Um passo falhou: os seguintes não rodam, e a resposta diz o que já foi feito.
 * - Antes da primeira mudança de um pedido, guarda um retrato da tela; "voltar ao mapa de antes" restaura o
 *   último (pilha curta, só nesta aba, nada gravado no aparelho).
 */
import { serieDaCidade } from '../dados/serie'
import type { Cidade } from '../dados/tipos'
import type { AoVivo } from '../dados/usarAoVivo'
import type { ReguaNoMapa } from '../logica/reguasNoMapa'
import { compartilharDaCidade } from '../chat-local/situacaoAgora'
import { nomeDaCidade, normalizar, rotuloDaRegua } from './interpretar'
import type { ControleMonitor, Retrato } from './ponte'
import {
  baseDoSite, linkDoMonitor, serieDeUmaRegua, textoAtrasadas, textoComparar, textoDaCoordenada, textoDoLink,
  textoMontante, textoOrigemTracado, textoUltimaHora, type PropriedadesDoTracado,
} from './respostas'
import { NOME_DO_ARQUIVO, arquivoDoRioDaCidade } from './rios'
import { intersecoes, pontosDaRua, ruasSemCoordenada, textoDaRuaItajai, textoDosPontos, comTipo } from './ruas'
import { acharVias, nomeLegivelDaVia } from '../logica/viasItajai'
import type { CotaRua } from '../dados/tipos'
import type { CidadeSeguida } from '../logica/preferencias'
import { estadoDaCidade } from '../dados/usarAoVivo'
import { horaDeBrasilia } from '../logica/agora'
import { metros } from '../logica/formato'
import { idadeMin, textoIdade } from '../logica/tempoReal'
import { AVISO_RELATO, textoDaLocalizacao, textoDoRelato, type Posicao } from './aparelho'
import { instantePedido, textoBarragens, textoChuvaAgora, textoFonteDaLeitura, textoMare } from './bacia'
import type { Barragem } from '../dados/barragens'
import type { TabuaMare } from '../dados/tipos'
import { leiturasDaCidadeEmTodosOsRios } from '../dados/tempoReal'
import type { RuasPorMancha } from '../chat-local/motor'
import type { Catalogo, Contexto, Passo, Resultado } from './tipos'

/**
 * O que os pedidos da 2ª entrega leem do site. Fica de fora nos testes da 1ª entrega (opcional): sem ele, o
 * pedido diz que não conseguiu carregar, em vez de inventar.
 */
export interface DadosDoChat {
  /** As leituras ao vivo, esperando a primeira busca terminar (ou null se não vier a tempo). */
  aoVivo(): Promise<AoVivo | null>
  cidade(id: string): { cidade: Cidade; rioId: string } | null
  reguasNoMapa(v: AoVivo): ReguaNoMapa[]
  tracado(arquivo: string): Promise<PropriedadesDoTracado | null>
  /** O endereço do site, sem o `#` (para montar o link da tela). */
  base(): string
  /** 3ª entrega: as vias de Itajaí (nome → quantos trechos na base), o cruzamento rua × mancha e as cotas de rua. */
  viasItajai?(): Promise<Record<string, number> | null>
  ruasMancha?(): Promise<RuasPorMancha | null>
  cotasRuas?(): Promise<CotaRua[] | null>
  /** 4ª entrega: a posição do aparelho (o navegador pede permissão) e as preferências guardadas nele. */
  localizacao?(): Promise<Posicao | { erro: 'negada' | 'indisponivel' | 'tempo' | 'sem_suporte' }>
  preferencias?: {
    seguidas(): CidadeSeguida[]
    tornarMinha(c: CidadeSeguida): CidadeSeguida[]
    seguir(c: CidadeSeguida): 'seguindo' | 'ja_seguia' | 'cheia' | 'sem_memoria'
    deixarDeSeguir(id: string): CidadeSeguida[]
    letra(l: 'normal' | 'grande'): void
  }
  /** 5ª entrega: as barragens (buscadas na hora), a tábua de maré e as fontes de tempo real do cadastro. */
  barragens?(): Promise<ReadonlyMap<string, Barragem>>
  mare?(): TabuaMare
  fontesDaCidade?(id: string): string[]
}

export interface Ambiente {
  navegar(rota: string): void
  rotaAtual(): string
  monitor(): ControleMonitor | null
  esperarMonitor(cidade: string | null): Promise<ControleMonitor | null>
  dados?: DadosDoChat
}

const MAX_RETRATOS = 10
const retratos: Retrato[] = []

/** Só para os testes: começa cada caso sem histórico. */
export function limparRetratos(): void {
  retratos.length = 0
}

export const MUDA_A_TELA = new Set<Passo['tipo']>([
  'ir_cidade', 'monitor_bacia', 'abrir_pagina', 'abrir_rota', 'escolher_regua', 'aproximar_regua', 'zoom',
  'ver_bacia', 'fundo', 'camada', 'ao_vivo', 'filtro', 'abrir_grafico', 'confluencia', 'rua', 'remover_destaque',
  'localizacao', 'reproducao',
])
const PRECISA_DO_MAPA = new Set<Passo['tipo']>([
  'escolher_regua', 'aproximar_regua', 'zoom', 'ver_bacia', 'fundo', 'camada', 'ao_vivo', 'o_que_vejo', 'filtro',
  'reproducao',
])

const NOME_FUNDO = { escuro: 'escuro', satelite: 'satélite', mapa: 'mapa de ruas' } as const

export interface Saida {
  texto: string
  sugestoes?: string[]
  link?: { texto: string; para: string }
  /** Texto preparado para a pessoa copiar (resumo, link). O chat mostra o botão; nunca envia sozinho. */
  copiar?: string
}

const SEM_DADOS = 'Não consegui carregar as leituras agora. Tente de novo em instantes; em emergência, ligue 199.'

export async function executar(passos: Passo[], amb: Ambiente, cat: Catalogo, ctx: Contexto, ajuda: () => Saida): Promise<Saida> {
  const feitos: string[] = []
  let guardou = false
  let cidade = ctx.cidadeAtual
  const falha = (r: Resultado | string): Saida => {
    const motivo = typeof r === 'string' ? r : r.texto
    const antes = feitos.length ? `Feito: ${feitos.join(' ')} ` : ''
    const resto = feitos.length || passos.length > 1 ? ' Os passos seguintes não foram feitos.' : ''
    return { texto: `${antes}${motivo}${resto}`.trim(), sugestoes: ['o que posso pedir?'] }
  }

  for (const passo of passos) {
    if (MUDA_A_TELA.has(passo.tipo) && !guardou) {
      const m = amb.monitor()
      retratos.push(m ? m.retrato() : { rota: amb.rotaAtual() })
      if (retratos.length > MAX_RETRATOS) retratos.shift()
      guardou = true
    }

    // Garante o Monitor para quem precisa do mapa: o da cidade em foco, ou a bacia. A confluência só precisa
    // do mapa quando o cadastro tem o ponto — sem ponto, a resposta é texto e a tela não muda.
    let m = amb.monitor()
    const precisa = PRECISA_DO_MAPA.has(passo.tipo) || (passo.tipo === 'confluencia' && !!cat.confluencias?.some((c) => c.id === passo.id))
    if (precisa && !m) {
      amb.navegar(cidade ? `/monitor/${cidade}` : '/monitor')
      m = await amb.esperarMonitor(cidade)
      if (!m) return falha('Não consegui abrir o Monitor agora. Tente de novo.')
    }

    switch (passo.tipo) {
      case 'ajuda':
        return ajuda()
      case 'ir_cidade': {
        const nome = nomeDaCidade(passo.cidadeId, cat)
        if (m && m.cidade === passo.cidadeId) {
          const r = m.enquadrarCidade()
          if (!r.ok) return falha(r)
        } else {
          amb.navegar(`/monitor/${passo.cidadeId}`)
          const novo = await amb.esperarMonitor(passo.cidadeId)
          if (!novo) return falha(`Não consegui abrir o Monitor de ${nome}.`)
        }
        cidade = passo.cidadeId
        feitos.push(`Monitor de ${nome} aberto e enquadrado.`)
        break
      }
      case 'monitor_bacia': {
        amb.navegar('/monitor')
        const novo = await amb.esperarMonitor(null)
        if (!novo) return falha('Não consegui abrir o Monitor.')
        cidade = null
        feitos.push('Monitor da bacia aberto.')
        break
      }
      case 'abrir_pagina': {
        const c = cat.cidades.find((x) => x.id === passo.cidadeId)
        if (!c) return falha('Cidade fora do cadastro.')
        const base = c.id === 'itajai' ? '/itajai' : `/${c.rio}/${c.id}`
        const aba = passo.aba && c.id !== 'itajai' && passo.aba !== 'agora' ? `?aba=${passo.aba}` : ''
        amb.navegar(base + aba)
        const qual = passo.aba === 'historico' ? 'o histórico' : passo.aba === 'rua' ? 'a busca de rua' : passo.aba === 'fontes' ? 'as fontes' : 'a página'
        feitos.push(`Abri ${qual} de ${c.nome}.`)
        break
      }
      case 'abrir_rota':
        amb.navegar(passo.rota)
        feitos.push(`Abri ${passo.descricao}.`)
        break
      case 'escolher_regua': {
        if (passo.codigo !== 'todas') {
          const regua = cat.reguas.find((r) => r.codigo === passo.codigo)
          if (!regua) return falha(`A régua ${passo.codigo} não está no cadastro.`)
          if (!m || m.cidade !== regua.cidadeId) {
            amb.navegar(`/monitor/${regua.cidadeId}`)
            m = await amb.esperarMonitor(regua.cidadeId)
            if (!m) return falha(`Não consegui abrir o Monitor de ${nomeDaCidade(regua.cidadeId, cat)}.`)
            cidade = regua.cidadeId
          }
        }
        const r = m!.escolherRegua(passo.codigo)
        if (!r.ok) return falha(r)
        feitos.push(r.texto)
        break
      }
      case 'aproximar_regua': {
        const est = m!.estado()
        const r = est.regua ? m!.escolherRegua(est.regua.codigo) : m!.enquadrarCidade()
        if (!r.ok) return falha(r)
        feitos.push(r.texto)
        break
      }
      case 'zoom':
      case 'ver_bacia':
      case 'fundo':
      case 'ao_vivo': {
        const r = passo.tipo === 'zoom' ? m!.zoom(passo.sentido)
          : passo.tipo === 'ver_bacia' ? m!.verBacia()
          : passo.tipo === 'fundo' ? m!.fundo(passo.fundo)
          : m!.aoVivo()
        if (!r.ok) return falha(r)
        feitos.push(r.texto)
        break
      }
      case 'camada': {
        const est = m!.estado()
        const onde = est.cidadeNome ?? 'esta tela'
        if (passo.acao === 'desligar') {
          const r = m!.camada('off')
          if (!r.ok) return falha(r)
          feitos.push(r.texto)
          break
        }
        const opcoes = est.camadasDisponiveis
        if (opcoes.length === 0) return falha(`Não há camadas de cheia cadastradas para ${onde}.`)
        const escolhidas = passo.rotulo ? opcoes.filter((o) => normalizar(o.rotulo) === passo.rotulo)
          : passo.ano ? opcoes.filter((o) => o.rotulo.includes(passo.ano!)) : opcoes
        if (escolhidas.length === 0) {
          return { texto: `${onde} não tem camada de ${passo.ano}. As camadas disponíveis são estas; escolha uma.`, sugestoes: opcoes.slice(0, 8).map((o) => `camada: ${o.rotulo}`) }
        }
        if (escolhidas.length > 1) {
          // Vários cenários e nenhum escolhido: pergunta. Não liga todos.
          return { texto: `${onde} tem ${escolhidas.length} camadas${passo.ano ? ` de ${passo.ano}` : ''}. Qual delas? (Camada é referência de cheia passada ou simulação, não alagamento atual.)`, sugestoes: escolhidas.slice(0, 8).map((o) => `camada: ${o.rotulo}`) }
        }
        const r = m!.camada(escolhidas[0]!.arquivo)
        if (!r.ok) return falha(r)
        feitos.push(r.texto)
        break
      }
      case 'voltar': {
        const r = retratos.pop()
        if (!r) return { texto: 'Não há ação do chat para desfazer.' }
        if (r.cidade === undefined) {
          amb.navegar(r.rota)
          return { texto: 'Voltei à página de antes.' }
        }
        let alvo = amb.monitor()
        if (!alvo || alvo.cidade !== r.cidade) {
          amb.navegar(r.rota)
          alvo = await amb.esperarMonitor(r.cidade)
          if (!alvo) return { texto: 'Não consegui voltar ao mapa de antes.' }
        }
        const feito = alvo.restaurar(r)
        return { texto: feito.ok ? 'Voltei ao mapa de antes: vista, régua, fundo e camada.' : feito.texto }
      }
      case 'o_que_vejo': {
        const e = m!.estado()
        const partes = [
          e.cidadeNome ? `Monitor de ${e.cidadeNome}.` : 'Monitor da bacia inteira.',
          e.regua ? `Régua selecionada: ${e.regua.rotulo}.` : e.reguas.length > 1 ? `Todas as ${e.reguas.length} réguas da cidade.` : '',
          `Fundo: ${NOME_FUNDO[e.fundo]}.`,
          e.camada ? `Camada: ${e.camada} — referência, não alagamento atual.` : 'Sem camada de cheia desenhada.',
          e.reproducao ? `Reprodução ligada: mostrando ${e.reproducao}, leituras do passado.` : 'Leituras ao vivo, cada uma com a hora dela no painel.',
          'A cor de cada pino é a faixa da Defesa Civil da cidade; cinza é sem faixa. Toque no pino para ver o motivo.',
        ]
        return { texto: partes.filter(Boolean).join(' ') }
      }
      case 'atual_ou_historico': {
        if (!m) return { texto: 'Fora do Monitor, cada cartão diz a hora da medição. Leitura velha aparece com a data por extenso, não como atual.' }
        const e = m.estado()
        const partes = [
          e.reproducao ? `Histórico: a reprodução mostra ${e.reproducao}. Peça "ir para a leitura mais recente" para voltar ao agora.` : 'As leituras são as mais recentes, cada uma com a hora dela.',
          e.camada ? `A camada "${e.camada}" é referência (cheia passada ou simulação), não alagamento atual.` : '',
        ]
        return { texto: partes.filter(Boolean).join(' ') }
      }
      case 'por_que_cinza':
      case 'coordenada': {
        const alvo = passo.cidadeId ?? cidade
        if (!alvo) return { texto: 'De qual cidade? Por exemplo: "por que Lontras está cinza?"' }
        const nome = nomeDaCidade(alvo, cat)
        if (!m) {
          return { texto: `Isso aparece no painel de ${nome} no Monitor.`, link: { texto: `Abrir ${nome} no Monitor →`, para: `/monitor/${alvo}` } }
        }
        const ex = m.explicar(alvo)
        if (!ex) return { texto: `${nome} não está no mapa do Monitor.` }
        if (passo.tipo === 'por_que_cinza') {
          return { texto: ex.motivoCinza ? `${nome} está cinza: ${ex.motivoCinza}` : `${nome} não está cinza agora: ${ex.faixa}.` }
        }
        return { texto: [ex.posicao, ex.equivalencia].filter(Boolean).join(' ') }
      }
      // ------------------------------------------------ 2ª entrega
      case 'filtro': {
        if (!m!.filtrar) return falha('O filtro não está disponível nesta tela.')
        const r = m!.filtrar(passo.filtro)
        if (!r.ok) return falha(r)
        feitos.push(r.texto)
        break
      }
      case 'confluencia': {
        const c = cat.confluencias?.find((x) => x.id === passo.id)
        if (!c) {
          const sem = cat.semPonto?.find((x) => x.id === passo.id)
          return { texto: `${sem?.nome ?? 'Esse rio'} não tem ponto de confluência gravado no cadastro. ${sem?.motivo ?? ''} O mapa não marca um ponto estimado.`.trim() }
        }
        if (!m!.marcarPonto) return falha('Não consigo marcar pontos nesta tela.')
        const r = m!.marcarPonto({ lat: c.lat, lon: c.lon, rotulo: c.nome })
        if (!r.ok) return falha(r)
        feitos.push(`${r.texto} ${c.nome}: ${textoDaCoordenada(c.lat, c.lon)}. Fonte: ${resumoDaFonte(c.fonte)}`)
        break
      }
      case 'atrasadas': {
        const v = await amb.dados?.aoVivo()
        if (!v) return { texto: SEM_DADOS }
        return { texto: textoAtrasadas(v, cat) }
      }
      case 'abrir_grafico': {
        const alvo = passo.cidadeId ?? cidade
        if (!alvo) return { texto: 'O gráfico de qual cidade? Por exemplo: "gráfico de Blumenau".', sugestoes: ['gráfico de Blumenau', 'gráfico de Rio do Sul'] }
        const c = cat.cidades.find((x) => x.id === alvo)
        if (!c) return falha('Cidade fora do cadastro.')
        if (c.id === 'itajai') {
          amb.navegar('/itajai')
          return { texto: 'Itajaí tem onze réguas, cada uma com o seu zero, e não tem um gráfico só: abri a página da foz, com a leitura de cada régua. Para ver todas lado a lado aqui, peça "comparar as réguas de Itajaí".', sugestoes: ['comparar as réguas de Itajaí'] }
        }
        amb.navegar(`/${c.rio}/${c.id}?secao=grafico`)
        feitos.push(`Abri a página de ${c.nome} no gráfico "Últimas horas". Ele aparece quando há série publicada e cota da cidade.`)
        break
      }
      case 'ultima_hora': {
        const alvo = passo.cidadeId ?? cidade
        if (!alvo) return { texto: 'Em qual cidade? Por exemplo: "o que mudou na última hora em Blumenau?"', sugestoes: ['o que mudou na última hora em Blumenau?'] }
        const d = amb.dados
        const v = await d?.aoVivo()
        if (!d || !v) return { texto: SEM_DADOS }
        const nome = nomeDaCidade(alvo, cat)
        const reguaDoMonitor = ctx.reguaAtual && cat.reguas.find((r) => r.codigo === ctx.reguaAtual && r.cidadeId === alvo)
        const rios = Object.keys(v.serie.series)
        const pontos = rios.flatMap((r) => serieDaCidade(v.serie, r, alvo)).sort((a, b) => a.medidoEm.getTime() - b.medidoEm.getTime())
        const s = serieDeUmaRegua(pontos, v.serie.resgates ?? {}, reguaDoMonitor ? reguaDoMonitor.titulo : null)
        if ('escolher' in s) {
          const daCidade = cat.reguas.filter((r) => r.cidadeId === alvo)
          return {
            texto: `${nome} tem ${s.escolher.length} réguas, cada uma com o seu zero: a variação é de uma régua só. Escolha uma no Monitor e peça de novo, ou veja todas lado a lado.`,
            sugestoes: [`comparar as réguas de ${nome}`, ...daCidade.slice(0, 3).map((r) => `zoom na régua ${rotuloDaRegua(r)}`)],
          }
        }
        const rotulo = reguaDoMonitor ? `${nome} (${rotuloDaRegua(reguaDoMonitor)})` : nome
        return { texto: textoUltimaHora({ nome: rotulo, cidadeId: alvo, pontos: s.pontos, publicacao: s.publicacao, agora: v.agora }) }
      }
      case 'origem_tracado': {
        const alvo = passo.cidadeId ?? cidade
        const c = alvo ? cat.cidades.find((x) => x.id === alvo) : null
        const arquivo = passo.rio ?? (c ? arquivoDoRioDaCidade(c.id, c.rio) : null)
        if (!arquivo) return { texto: 'O traçado de qual rio?', sugestoes: ['de onde vem o traçado do Itajaí-Açu?', 'de onde vem o traçado do Benedito?'] }
        const props = await amb.dados?.tracado(arquivo)
        if (!props) return { texto: `Não consegui abrir o arquivo do traçado (${arquivo}).` }
        return { texto: textoOrigemTracado(NOME_DO_ARQUIVO[arquivo] ?? arquivo, props) }
      }
      case 'montante': {
        const alvo = passo.cidadeId ?? cidade
        if (!alvo) return { texto: 'De qual cidade? Por exemplo: "o que fica a montante de Blumenau?"', sugestoes: ['o que fica a montante de Blumenau?', 'afluentes de Indaial'] }
        return { texto: textoMontante(cat, alvo, passo.foco) }
      }
      case 'comparar_reguas': {
        const alvo = passo.cidadeId ?? cidade ?? 'itajai'
        const d = amb.dados
        const v = await d?.aoVivo()
        if (!d || !v) return { texto: SEM_DADOS }
        const reguas = d.reguasNoMapa(v).filter((r) => r.cidade === alvo)
        const nome = nomeDaCidade(alvo, cat)
        if (reguas.length < 2) return { texto: `${nome} tem uma régua só no mapa: não há réguas para comparar. Peça "como está ${nome}?".`, sugestoes: [`como está ${nome}?`] }
        return { texto: textoComparar(nome, reguas, v.agora) }
      }
      case 'copiar_resumo': {
        const alvo = passo.cidadeId ?? cidade
        if (!alvo) return { texto: 'O resumo de qual cidade? Por exemplo: "copiar resumo de Blumenau".', sugestoes: ['copiar resumo de Blumenau'] }
        const d = amb.dados
        const v = await d?.aoVivo()
        const c = d?.cidade(alvo)
        if (!d || !v || !c) return { texto: SEM_DADOS }
        // Cidade de várias réguas (Itajaí) não tem um número só, haja ou não leitura nesta coleta.
        const texto = cat.reguas.filter((r) => r.cidadeId === alvo).length > 1 ? 'varias' : compartilharDaCidade(c.cidade, c.rioId, v)
        if (texto === 'varias') return { texto: `${c.cidade.nome} tem várias réguas, cada uma com o seu zero: não há um número só para resumir. Peça "comparar as réguas de ${c.cidade.nome}".`, sugestoes: [`comparar as réguas de ${c.cidade.nome}`] }
        if (!texto) return { texto: `Não há leitura de agora da régua de ${c.cidade.nome}: o resumo só sai com leitura que não é velha, para não circular número antigo como se fosse de agora.` }
        return { texto: `Resumo pronto para copiar (sem o endereço do site, com a hora da medição). Quem envia é você:\n\n${texto}`, copiar: texto }
      }
      case 'copiar_link': {
        const base = amb.dados?.base()
        if (!base) return { texto: 'Não consegui montar o link desta tela.' }
        const mon = amb.monitor()
        if (mon) {
          const e = mon.estado()
          const link = linkDoMonitor(base, e)
          const desc = [e.cidadeNome ? `Monitor de ${e.cidadeNome}` : 'Monitor da bacia', e.regua ? `régua ${e.regua.rotulo}` : '', `fundo ${NOME_FUNDO[e.fundo]}`].filter(Boolean).join(', ')
          return { texto: textoDoLink(link, desc), copiar: link }
        }
        const link = `${base}#${amb.rotaAtual()}`
        return { texto: textoDoLink(link, 'a página aberta'), copiar: link }
      }
      // ------------------------------------------------ 3ª entrega: rua no mapa
      case 'rua': {
        const r = await executarRua(passo, amb, cat, cidade)
        if ('fim' in r) return r.fim
        cidade = r.cidade
        feitos.push(r.texto)
        if (r.sugestoes) return { texto: feitos.join(' '), sugestoes: r.sugestoes }
        break
      }
      case 'remover_destaque': {
        const rota = amb.rotaAtual()
        const [caminho, busca = ''] = rota.split('?')
        const params = new URLSearchParams(busca)
        if (caminho === '/itajai' && params.has('rua')) {
          params.delete('rua')
          const resto = params.toString()
          amb.navegar(`${caminho}${resto ? `?${resto}` : ''}`)
          feitos.push('Destaque da rua tirado do mapa das manchas.')
          break
        }
        const mon = amb.monitor()
        if (mon?.marcarPonto && mon.estado().marca) {
          const r = mon.marcarPonto(null)
          if (!r.ok) return falha(r)
          feitos.push(r.texto)
          break
        }
        return { texto: 'Não há rua destacada nem ponto marcado nesta tela.' }
      }
      // ------------------------------------------------ 4ª entrega: o aparelho
      case 'localizacao': {
        if (!amb.dados?.localizacao) return { texto: 'Este navegador não oferece a localização ao site.' }
        const p = await amb.dados.localizacao()
        if ('erro' in p) return { texto: ERRO_LOCALIZACAO[p.erro] }
        const r = textoDaLocalizacao(p, cat)
        if (r.fora || !r.perto) return { texto: r.texto }
        const nomePerto = nomeDaCidade(r.perto.cidadeId, cat)
        const sugestoes = [`como está ${nomePerto}?`, `definir ${nomePerto} como minha cidade`]
        // A posição vai para o mapa como marca (memória da tela). Fora do Monitor, abre o da cidade mais perto.
        let mon = amb.monitor()
        if (!mon) {
          amb.navegar(`/monitor/${r.perto.cidadeId}`)
          mon = await amb.esperarMonitor(r.perto.cidadeId)
        }
        const marcou = mon?.marcarPonto?.({ lat: p.lat, lon: p.lon, rotulo: 'Você está aqui (aproximado; não fica guardado)', km: 6 })
        const nota = marcou?.ok ? 'Sua posição está marcada no mapa com um anel branco.' : 'Não deu para marcar a sua posição no mapa.'
        return { texto: `${r.texto}\n${nota}`, sugestoes }
      }
      case 'relatar': {
        const mon = amb.monitor()
        const e = mon?.estado()
        const caminho = `#${amb.rotaAtual()}`
        const alvo = cidade
        const tela = e
          ? [e.cidadeNome ? `Monitor de ${e.cidadeNome}` : 'Monitor da bacia', e.regua ? `régua ${e.regua.rotulo}` : ''].filter(Boolean).join(', ')
          : alvo ? `página de ${nomeDaCidade(alvo, cat)}` : 'página do site'
        let mostra: string | null = null
        const v = await amb.dados?.aoVivo()
        if (v && e?.regua) {
          const r = cat.reguas.find((x) => x.codigo === e.regua!.codigo)
          const l = r && v.tempoReal.leituras.find((x) => x.estacao === r.titulo)
          mostra = l ? `${metros(l.nivel_m)}${l.medidoEm ? `, medido às ${horaDeBrasilia(l.medidoEm)} (${textoIdade(idadeMin(l.medidoEm, v.agora))})` : ', sem horário'} na ${e.regua.rotulo}` : `sem leitura da ${e.regua.rotulo}`
        } else if (v && alvo) {
          const c = amb.dados?.cidade(alvo)
          const est = c ? estadoDaCidade(c.cidade, c.rioId, v) : null
          if (est?.varias) mostra = `várias réguas em ${nomeDaCidade(alvo, cat)} (sem régua escolhida)`
          else if (est?.leitura) mostra = `${metros(est.leitura.nivel_m)} na régua de ${nomeDaCidade(alvo, cat)}${est.leitura.medidoEm ? `, medido às ${horaDeBrasilia(est.leitura.medidoEm)} (${textoIdade(idadeMin(est.leitura.medidoEm, v.agora))})` : ', sem horário'}`
          else mostra = `sem leitura municipal de ${nomeDaCidade(alvo, cat)} nesta coleta`
        }
        const texto = textoDoRelato({ tela, caminho, mostra, agora: v?.agora ?? new Date() })
        return { texto: `${AVISO_RELATO}\n\n${texto}`, copiar: texto }
      }
      case 'preferencia_cidade': {
        const pref = amb.dados?.preferencias
        if (!pref) return { texto: 'Não consigo mexer nas preferências deste aparelho agora.' }
        const c = passo.cidadeId ? cat.cidades.find((x) => x.id === passo.cidadeId) : null
        const nome = c?.nome ?? ''
        const comoSeguida = (x: typeof c): CidadeSeguida => ({ id: x!.id, rio: x!.rio })
        if (passo.acao === 'listar') {
          const lista = pref.seguidas()
          if (!lista.length) return { texto: 'Nenhuma cidade guardada neste aparelho. Peça, por exemplo, "minha cidade é Gaspar".', sugestoes: ['minha cidade é Gaspar'] }
          const [minha, ...outras] = lista.map((x) => nomeDaCidade(x.id, cat))
          return { texto: `Sua cidade neste aparelho: ${minha}.${outras.length ? ` Também segue: ${outras.join(', ')}.` : ''} Fica só neste aparelho.` }
        }
        if (!c) return { texto: 'Qual cidade?', sugestoes: ['minha cidade é Gaspar', 'seguir Blumenau'] }
        if (passo.acao === 'minha') {
          const lista = pref.tornarMinha(comoSeguida(c))
          return lista[0]?.id === c.id && pref.seguidas()[0]?.id === c.id
            ? { texto: `${nome} agora é a sua cidade neste aparelho: o Início abre com ela. A escolha fica só neste aparelho.`, sugestoes: [`como está ${nome}?`] }
            : { texto: `Não deu para guardar neste aparelho (navegação anônima ou armazenamento bloqueado). ${nome} vale só enquanto a página estiver aberta.` }
        }
        if (passo.acao === 'seguir') {
          const r = pref.seguir(comoSeguida(c))
          return {
            texto: {
              seguindo: `Agora você segue ${nome} neste aparelho: ela aparece no Início.`,
              ja_seguia: `Você já segue ${nome}.`,
              cheia: 'Você já segue quatro cidades, o máximo. Deixe de seguir uma antes (por exemplo, "deixar de seguir Ilhota").',
              sem_memoria: 'Não deu para guardar neste aparelho (navegação anônima ou armazenamento bloqueado).',
            }[r],
          }
        }
        const antes = pref.seguidas().some((x) => x.id === c.id)
        pref.deixarDeSeguir(c.id)
        return { texto: antes ? `Você deixou de seguir ${nome} neste aparelho.` : `Você não segue ${nome}.` }
      }
      case 'letra': {
        if (!amb.dados?.preferencias) return { texto: 'Não consigo mudar a letra agora.' }
        amb.dados.preferencias.letra(passo.tamanho)
        const qual = passo.tamanho === 'grande' ? 'Letra maior ligada' : 'Letra normal'
        return {
          texto: ctx.naMonitor
            ? `${qual} neste aparelho, nas páginas do site. O Monitor mantém o desenho dele e não muda o tamanho da letra.`
            : `${qual} neste aparelho. É o mesmo botão de letra do topo da página.`,
        }
      }
      // ------------------------------------------------ 5ª entrega: o tempo e a bacia
      case 'reproducao': {
        if (!m!.reproducao) return falha('A reprodução não está disponível nesta tela.')
        let r: Resultado
        if (passo.acao === 'ir') {
          const agora = (await amb.dados?.aoVivo())?.agora ?? new Date()
          const instante = instantePedido(passo, agora)
          if (!instante) return { texto: 'Não entendi o horário. Peça, por exemplo, "como estava às 14h" ou "voltar 3 horas".' }
          r = m!.reproducao({ acao: 'ir', instante })
        } else {
          r = m!.reproducao({ acao: passo.acao })
        }
        if (!r.ok) return falha(r)
        feitos.push(r.texto)
        break
      }
      case 'chuva_agora': {
        const v = await amb.dados?.aoVivo()
        if (!v) return { texto: SEM_DADOS }
        return { texto: textoChuvaAgora(v.tempoReal.chuva, v.tempoReal.chuvaOk, cat, v.agora) }
      }
      case 'barragens': {
        const b = await amb.dados?.barragens?.()
        if (!b) return { texto: 'Não consegui buscar o estado das barragens agora.' }
        return { texto: textoBarragens(b, new Date()) }
      }
      case 'mare': {
        const t = amb.dados?.mare?.()
        if (!t) return { texto: 'A tábua de maré não está disponível agora.' }
        return { texto: textoMare(t, new Date()), link: { texto: 'Ver a foz e a maré →', para: '/itajai' } }
      }
      case 'fonte_leitura': {
        const alvo = passo.cidadeId ?? cidade
        if (!alvo) return { texto: 'De qual cidade? Por exemplo: "de onde vem a leitura de Blumenau?"', sugestoes: ['de onde vem a leitura de Blumenau?'] }
        const v = await amb.dados?.aoVivo()
        if (!v) return { texto: SEM_DADOS }
        const c = cat.cidades.find((x) => x.id === alvo)
        if (!c) return falha('Cidade fora do cadastro.')
        return {
          texto: textoFonteDaLeitura({
            nome: c.nome,
            leituras: leiturasDaCidadeEmTodosOsRios(v.tempoReal, alvo),
            estadual: v.nivelSc.get(alvo) ?? null,
            fontesCadastradas: amb.dados?.fontesDaCidade?.(alvo) ?? [],
            agora: v.agora,
          }),
          link: { texto: `Abrir as fontes de ${c.nome} →`, para: c.id === 'itajai' ? '/itajai' : `/${c.rio}/${c.id}?aba=fontes` },
        }
      }
      case 'tela_cheia': {
        if (ctx.naMonitor) return { texto: 'O navegador só abre a tela cheia com o seu toque: use o botão "Tela cheia" no bloco do topo do mapa. Para sair, o mesmo botão ou a tecla Esc.' }
        const alvo = cidade
        return {
          texto: 'A tela cheia é do mapa, e o navegador só a abre com o seu toque: abra o Monitor e toque em "Tela cheia".',
          link: { texto: 'Abrir o Monitor →', para: alvo ? `/monitor/${alvo}` : '/monitor' },
        }
      }
    }
  }
  return { texto: feitos.join(' ') || 'Feito.' }
}

const ERRO_LOCALIZACAO = {
  negada: 'Você não permitiu a localização (ou o navegador bloqueou). Nada foi lido nem guardado. Para usar, permita a localização para este site nas configurações do navegador e peça de novo.',
  indisponivel: 'O aparelho não conseguiu dizer a sua posição agora. Nada foi guardado.',
  tempo: 'A posição não chegou a tempo: o navegador pode estar esperando a sua permissão, ou o aparelho está sem sinal de localização. Nada foi guardado; responda à pergunta do navegador ou tente de novo.',
  sem_suporte: 'Este navegador não oferece a localização ao site.',
} as const

/** As cidades com rua no mapa: Itajaí (traçado) e as que publicam o ponto da cota (Gaspar, Brusque). */
const CIDADES_COM_RUA_NO_MAPA = ['itajai', 'gaspar', 'brusque']

type ResultadoRua = { fim: Saida } | { texto: string; cidade: string | null; sugestoes?: string[] }

async function executarRua(
  passo: Extract<Passo, { tipo: 'rua' }>,
  amb: Ambiente,
  cat: Catalogo,
  cidadeEmFoco: string | null,
): Promise<ResultadoRua> {
  const d = amb.dados
  const [vias, cotas] = await Promise.all([d?.viasItajai?.() ?? null, d?.cotasRuas?.() ?? null])
  if (!vias && !cotas) return { fim: { texto: 'Não consegui carregar as ruas agora. Tente de novo em instantes.' } }
  const nomeDe = (id: string) => nomeDaCidade(id, cat)
  const comTipoEscrito = (rua: string) => (comTipo(rua) ? rua : `rua ${rua}`)
  const achadosEm = (id: string) =>
    id === 'itajai' ? acharVias(passo.texto, Object.keys(vias ?? {})).length : pontosDaRua(cotas ?? [], id, passo.texto).length

  // A cidade citada manda. Sem ela, a da tela — se a rua estiver lá. Senão, procura nas cidades que têm rua no
  // mapa e pergunta se achar em mais de uma.
  const naTela = cidadeEmFoco && cat.cidades.some((c) => c.id === cidadeEmFoco) ? cidadeEmFoco : null
  const ruaNaTela = naTela && (CIDADES_COM_RUA_NO_MAPA.includes(naTela) ? achadosEm(naTela) > 0 : ruasSemCoordenada(cotas ?? [], naTela, passo.texto).length > 0)
  let alvo = passo.cidadeId ?? (ruaNaTela ? naTela : null)
  if (!alvo) {
    const onde = CIDADES_COM_RUA_NO_MAPA.filter((id) => achadosEm(id) > 0)
    if (onde.length === 0) {
      return { fim: { texto: `Não achei "${passo.texto}" em Itajaí, Gaspar nem Brusque, as cidades com rua no mapa. Diga a cidade, por exemplo: "${passo.texto} em Blumenau".` } }
    }
    if (onde.length > 1) {
      return { fim: { texto: `Achei "${passo.texto}" em ${onde.map(nomeDe).join(' e ')}. Em qual cidade?`, sugestoes: onde.map((id) => `mostrar a ${passo.texto} em ${nomeDe(id)}`) } }
    }
    alvo = onde[0]!
  }
  const nomeCidade = nomeDe(alvo)

  if (alvo === 'itajai') {
    const nomes = acharVias(passo.texto, Object.keys(vias ?? {}))
    if (nomes.length === 0) {
      return { fim: { texto: `Nenhuma via com "${passo.texto}" na base de vias da Prefeitura de Itajaí. Confira o nome, sem número de casa; a base pode não ter todas as ruas. Nada foi marcado.` } }
    }
    if (nomes.length > 1) {
      // Homônimos (R. e Av. com o mesmo nome) ou nomes parecidos: pergunta antes de marcar.
      return { fim: { texto: `Mais de uma via casa com "${passo.texto}" em Itajaí. Qual delas?`, sugestoes: nomes.slice(0, 8).map((n) => `mostrar a ${nomeLegivelDaVia(n)} em Itajaí`) } }
    }
    const nome = nomes[0]!
    const tabela = (await d?.ruasMancha?.()) ?? null
    let evento: string | null = null
    if (passo.ano) {
      const doAno = tabela?._meta.eventos.filter((e) => e.evento.startsWith(passo.ano!)) ?? []
      if (!doAno.length) {
        const de = tabela ? ` As manchas da Prefeitura são de: ${tabela._meta.eventos.map((e) => e.rotulo).join(', ')}.` : ''
        return { fim: { texto: `O site não tem mancha de cheia de Itajaí de ${passo.ano}.${de} Nada foi marcado.` } }
      }
      // Dois cenários no mesmo ano (2013): o que cruza a rua, se houver.
      const cruzam = tabela ? intersecoes(tabela, nome).dentro.map((x) => x.evento) : []
      evento = (doAno.find((e) => cruzam.includes(e.evento)) ?? doAno[0]!).evento
    }
    const busca = new URLSearchParams({ secao: 'manchas', rua: nome })
    if (evento) busca.set('cenario', evento)
    amb.navegar(`/itajai?${busca.toString()}`)
    const texto = textoDaRuaItajai({ nome, tabela, evento, trechos: vias?.[nome] ?? 1 })
    // "manchas na rua X" sem ano, com várias cheias cruzando: o mapa mantém o cenário escolhido e o chat
    // pergunta qual mostrar, em vez de ligar um por conta própria.
    if (passo.foco === 'manchas' && !evento && tabela) {
      const anos = [...new Set(intersecoes(tabela, nome).dentro.map((x) => x.evento.slice(0, 4)))]
      if (anos.length > 1) {
        return { texto: `${texto}\nQual cenário mostrar no mapa?`, cidade: 'itajai', sugestoes: anos.map((a) => `mancha de ${a} na ${nomeLegivelDaVia(nome)} em Itajaí`) }
      }
    }
    return { texto, cidade: 'itajai' }
  }

  // Gaspar e Brusque: os pontos de cota com coordenada.
  const grupos = pontosDaRua(cotas ?? [], alvo, passo.texto)
  if (grupos.length === 0) {
    const semPonto = ruasSemCoordenada(cotas ?? [], alvo, passo.texto)
    if (semPonto.length) {
      return {
        fim: {
          texto: `${nomeCidade} tem cota levantada para ${semPonto.slice(0, 3).map(nomeLegivelDaVia).join(', ')}, mas a fonte não publica a coordenada do ponto: o mapa não marca a rua (nada é localizado por conta própria).`,
          sugestoes: semPonto.slice(0, 2).map((r) => `quantas cheias passaram da cota da ${comTipoEscrito(r)} em ${nomeCidade}?`),
        },
      }
    }
    const temCotas = (cotas ?? []).some((c) => c.cidade === alvo)
    return {
      fim: {
        texto: temCotas
          ? `Nenhuma rua com "${passo.texto}" entre as cotas levantadas em ${nomeCidade}. Isso não quer dizer que ela não alaga: a lista é a que a Defesa Civil publicou. Nada foi marcado.`
          : `O site não tem as ruas de ${nomeCidade} no mapa: só Itajaí (traçado das vias) e Gaspar e Brusque (pontos de cota). Nada foi marcado.`,
      },
    }
  }
  if (grupos.length > 1) {
    return { fim: { texto: `Mais de uma rua casa com "${passo.texto}" em ${nomeCidade}. Qual delas?`, sugestoes: grupos.slice(0, 8).map((g) => `mostrar a ${comTipoEscrito(g.rua)} em ${nomeCidade}`) } }
  }
  const { rua, pontos } = grupos[0]!
  let m = amb.monitor()
  if (!m || m.cidade !== alvo) {
    amb.navegar(`/monitor/${alvo}`)
    m = await amb.esperarMonitor(alvo)
    if (!m) return { fim: { texto: `Não consegui abrir o Monitor de ${nomeCidade}.` } }
  }
  if (!m.marcarPonto) return { fim: { texto: 'Não consigo marcar pontos nesta tela.' } }
  const [primeiro, ...resto] = pontos
  const r = m.marcarPonto({
    lat: primeiro!.lat!,
    lon: primeiro!.lon!,
    rotulo: `${nomeLegivelDaVia(rua)}, ${nomeCidade} — localização aproximada`,
    km: kmParaOsPontos(pontos),
    extras: resto.map((c) => ({ lat: c.lat!, lon: c.lon! })),
  })
  if (!r.ok) return { fim: { texto: r.texto } }
  return { texto: textoDosPontos(rua, nomeCidade, pontos), cidade: alvo }
}

/** Largura da vista que cabe os pontos de uma rua, com folga; ao menos 1,2 km. */
function kmParaOsPontos(pontos: readonly CotaRua[]): number {
  const lats = pontos.map((c) => c.lat!)
  const lons = pontos.map((c) => c.lon!)
  const dLat = (Math.max(...lats) - Math.min(...lats)) * 111.32
  const dLon = (Math.max(...lons) - Math.min(...lons)) * 111.32 * Math.cos(((lats[0] ?? -27) * Math.PI) / 180)
  return Math.max(1.2, 1.5 * Math.max(dLat, dLon))
}

/** A fonte da coordenada, inteira até ~320 caracteres; mais longa, corta na última frase que cabe. */
function resumoDaFonte(fonte: string): string {
  const f = fonte.trim()
  if (!f) return 'cadastro (data/estacoes.json).'
  if (f.length <= 320) return f
  const frases = f.split(/(?<=\.)\s+/)
  let saida = ''
  for (const fr of frases) {
    if ((saida + ' ' + fr).trim().length > 320) break
    saida = (saida + ' ' + fr).trim()
  }
  return saida || `${f.slice(0, 317).replace(/\s+\S*$/, '')}…`
}

/** Para quem monta o ambiente no navegador. */
export { baseDoSite }

/** Texto da régua para o chat ("DC-05 · Sítio Sr. Hilário"). */
export { rotuloDaRegua }
