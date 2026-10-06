/**
 * O chat tenta o texto como PEDIDO antes de levá-lo ao motor de perguntas (docs/CHAT-GLOBAL-COMANDOS.md).
 * Não é pedido: devolve false e a pergunta segue o caminho de sempre.
 */
import { useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { estacoes } from '../dados/carregar'
import { abrirPainel, acrescentar, marcarOcupado } from '../chat-local/conversa'
import { catalogoDoCadastro } from './catalogo'
import { executar } from './executar'
import { interpretar, nomeDaCidade } from './interpretar'
import { esperarMonitor, monitorAtual, type ControleMonitor } from './ponte'
import { textoDeAjuda } from './ajuda'
import type { Catalogo, Contexto } from './tipos'

/** A cidade e o tipo da tela, pelo endereço (HashRouter: `#/monitor/blumenau`). */
export function contextoDaRota(caminho: string, monitor: ControleMonitor | null): Contexto {
  const p = caminho.split('?')[0] ?? ''
  let cidadeAtual: string | null = null
  let naMonitor = false
  let m: RegExpMatchArray | null
  if ((m = p.match(/^\/monitor(?:\/([a-z0-9-]+))?\/?$/))) {
    naMonitor = true
    cidadeAtual = m[1] ?? null
  } else if (p.startsWith('/municipal/ascurra') && !p.startsWith('/municipal/ascurra/dados')) {
    naMonitor = true
    cidadeAtual = 'ascurra'
  } else if (p === '/itajai') {
    cidadeAtual = 'itajai'
  } else if ((m = p.match(/^\/(?:acu|mirim)\/([a-z0-9-]+)\/?$/))) {
    cidadeAtual = m[1] ?? null
  }
  const reguaAtual = naMonitor && monitor && monitor.cidade === cidadeAtual ? monitor.estado().regua?.codigo ?? null : null
  return { cidadeAtual, naMonitor, reguaAtual }
}

/** O endereço de agora, lido na hora (a ação pode terminar depois que este componente saiu da tela). */
function rotaAgora(): string {
  if (typeof window === 'undefined') return '/'
  return window.location.hash.replace(/^#/, '') || '/'
}

let catalogo: Catalogo | null = null
export function catalogoDoSite(): Catalogo {
  catalogo ??= catalogoDoCadastro(estacoes as Parameters<typeof catalogoDoCadastro>[0])
  return catalogo
}

export function useComandos(): {
  contexto: () => Contexto
  nomeDaCidadeAtual: () => string | null
  tentar: (texto: string) => boolean
} {
  const navigate = useNavigate()
  const cat = useMemo(catalogoDoSite, [])
  const contexto = useCallback(() => contextoDaRota(rotaAgora(), monitorAtual()), [])
  const nomeDaCidadeAtual = useCallback(() => {
    const id = contexto().cidadeAtual
    return id ? nomeDaCidade(id, cat) : null
  }, [cat, contexto])

  const tentar = useCallback(
    (texto: string) => {
      const ctx = contexto()
      const r = interpretar(texto, cat, ctx)
      if (!r) return false
      acrescentar({ papel: 'usuario', texto })
      if (r.tipo === 'esclarecer') {
        acrescentar({ papel: 'assistente', texto: r.texto, sugestoes: r.sugestoes, comando: true })
        return true
      }
      marcarOcupado(true)
      const ambiente = {
        navegar: (rota: string) => navigate(rota),
        rotaAtual: rotaAgora,
        monitor: monitorAtual,
        esperarMonitor: (cidade: string | null) => esperarMonitor(cidade),
      }
      executar(r.passos, ambiente, cat, ctx, () => textoDeAjuda(ctx, ctx.cidadeAtual ? nomeDaCidade(ctx.cidadeAtual, cat) : null))
        .then((s) => acrescentar({ papel: 'assistente', texto: s.texto, comando: true, ...(s.sugestoes ? { sugestoes: s.sugestoes } : {}), ...(s.link ? { link: s.link } : {}) }))
        .catch(() => acrescentar({ papel: 'assistente', texto: 'Não consegui executar o pedido. Nada foi alterado depois do erro.', comando: true }))
        .finally(() => {
          marcarOcupado(false)
          // No celular, no Monitor, a conversa recolhe depois do pedido: o resultado está no MAPA (a folha
          // da régua, a cidade enquadrada), e a última resposta fica numa linha logo abaixo da caixa.
          if (contextoDaRota(rotaAgora(), null).naMonitor && typeof matchMedia === 'function' && matchMedia('(max-width: 700px)').matches) {
            abrirPainel(false)
          }
        })
      return true
    },
    [cat, contexto, navigate],
  )
  return { contexto, nomeDaCidadeAtual, tentar }
}
