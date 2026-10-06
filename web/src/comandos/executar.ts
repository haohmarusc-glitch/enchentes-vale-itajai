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
import { nomeDaCidade, normalizar, rotuloDaRegua } from './interpretar'
import type { ControleMonitor, Retrato } from './ponte'
import type { Catalogo, Contexto, Passo, Resultado } from './tipos'

export interface Ambiente {
  navegar(rota: string): void
  rotaAtual(): string
  monitor(): ControleMonitor | null
  esperarMonitor(cidade: string | null): Promise<ControleMonitor | null>
}

const MAX_RETRATOS = 10
const retratos: Retrato[] = []

/** Só para os testes: começa cada caso sem histórico. */
export function limparRetratos(): void {
  retratos.length = 0
}

const MUDA_A_TELA = new Set<Passo['tipo']>([
  'ir_cidade', 'monitor_bacia', 'abrir_pagina', 'abrir_rota', 'escolher_regua', 'aproximar_regua', 'zoom',
  'ver_bacia', 'fundo', 'camada', 'ao_vivo',
])
const PRECISA_DO_MAPA = new Set<Passo['tipo']>([
  'escolher_regua', 'aproximar_regua', 'zoom', 'ver_bacia', 'fundo', 'camada', 'ao_vivo', 'o_que_vejo',
])

const NOME_FUNDO = { escuro: 'escuro', satelite: 'satélite', mapa: 'mapa de ruas' } as const

export interface Saida {
  texto: string
  sugestoes?: string[]
  link?: { texto: string; para: string }
}

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

    // Garante o Monitor para quem precisa do mapa: o da cidade em foco, ou a bacia.
    let m = amb.monitor()
    if (PRECISA_DO_MAPA.has(passo.tipo) && !m) {
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
    }
  }
  return { texto: feitos.join(' ') || 'Feito.' }
}

/** Texto da régua para o chat ("DC-05 · Sítio Sr. Hilário"). */
export { rotuloDaRegua }
