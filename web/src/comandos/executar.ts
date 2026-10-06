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
  'ver_bacia', 'fundo', 'camada', 'ao_vivo', 'filtro', 'abrir_grafico', 'confluencia',
])
const PRECISA_DO_MAPA = new Set<Passo['tipo']>([
  'escolher_regua', 'aproximar_regua', 'zoom', 'ver_bacia', 'fundo', 'camada', 'ao_vivo', 'o_que_vejo', 'filtro',
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
    }
  }
  return { texto: feitos.join(' ') || 'Feito.' }
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
