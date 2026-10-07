/**
 * O chat tenta o texto como PEDIDO antes de levá-lo ao motor de perguntas (docs/CHAT-GLOBAL-COMANDOS.md).
 * Não é pedido: devolve false e a pergunta segue o caminho de sempre.
 */
import { useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { estacoes, estacoesTempoReal, mareItajai, trechos, trechosExperimentais } from '../dados/carregar'
import { buscarBarragens } from '../dados/barragens'
import historicoChegada from '@dados/historico-chegada-itajai.json'
import { eventosCaptados } from '../dados/eventosCaptados'
import type { AoVivo } from '../dados/usarAoVivo'
import { reguasNoMapa } from '../logica/reguasNoMapa'
import { abrirPainel, acrescentar, lerConversa, limparConversa, marcarOcupado } from '../chat-local/conversa'
import { textoParaFala } from './fala'
import { catalogoDoCadastro } from './catalogo'
import { MUDA_A_TELA, baseDoSite, executar, type DadosDoChat, type Saida } from './executar'
import type { PropriedadesDoTracado } from './respostas'
import { carregarCotasRuas, carregarRuasManchaItajai } from '../chat-local/carregar'
import { carregarViasItajai } from '../dados/viasItajai'
import { avisoLido, cidadesSeguidas, contagemChatPermitida, deixarDeSeguir, esquecerPreferencias, gravarContagemChat, gravarLetra, letra, seguir, temMemoria, tornarMinha } from '../logica/preferencias'
import { pedirAtualizacao } from '../dados/atualizar'
import { ehIphone, jaInstalado, podeInstalar } from '../dados/modoAplicativo'
import { avisarPreferencias } from '../dados/usarPreferencias'
import type { Posicao } from './aparelho'

const LIMITE_LOCALIZACAO_MS = 25_000

/**
 * A posição do aparelho, UMA vez, quando a pessoa pede ("usar minha localização"). O navegador pergunta se
 * pode; a resposta não é guardada pelo site, nem a posição (docs/CHAT-GLOBAL-COMANDOS.md, 4ª entrega).
 */
function localizacao(): ReturnType<NonNullable<DadosDoChat['localizacao']>> {
  if (typeof navigator === 'undefined' || !navigator.geolocation) return Promise.resolve({ erro: 'sem_suporte' as const })
  return new Promise((resolver) => {
    // O `timeout` da API só conta DEPOIS da permissão: com a pergunta do navegador sem resposta, o pedido
    // ficaria em "Executando…" para sempre, com o Enviar travado. O limite daqui cobre a espera inteira.
    let feito = false
    const responder = (r: Awaited<ReturnType<NonNullable<DadosDoChat['localizacao']>>>) => {
      if (feito) return
      feito = true
      clearTimeout(limite)
      resolver(r)
    }
    const limite = setTimeout(() => responder({ erro: 'tempo' }), LIMITE_LOCALIZACAO_MS)
    navigator.geolocation.getCurrentPosition(
      (pos) => responder({ lat: pos.coords.latitude, lon: pos.coords.longitude, precisaoM: Number.isFinite(pos.coords.accuracy) ? pos.coords.accuracy : null } satisfies Posicao),
      (erro) => responder({ erro: erro.code === erro.PERMISSION_DENIED ? 'negada' : erro.code === erro.TIMEOUT ? 'tempo' : 'indisponivel' }),
      { enableHighAccuracy: false, timeout: 20_000, maximumAge: 5 * 60_000 },
    )
  })
}

/** As preferências do aparelho, com o aviso para as telas abertas (Início, estrela da cidade, letra). */
const preferencias: NonNullable<DadosDoChat['preferencias']> = {
  seguidas: () => cidadesSeguidas(),
  tornarMinha: (c) => {
    const l = tornarMinha(c)
    avisarPreferencias()
    return l
  },
  seguir: (c) => {
    const r = seguir(c)
    avisarPreferencias()
    return r
  },
  deixarDeSeguir: (id) => {
    const l = deixarDeSeguir(id)
    avisarPreferencias()
    return l
  },
  letra: (l) => {
    gravarLetra(l)
    // Sem armazenamento a troca ainda vale nesta visita (como no botão de letra).
    document.documentElement.dataset.letra = l
    avisarPreferencias()
  },
}

/**
 * "Ler em voz alta": a voz do próprio navegador lê a última resposta do chat (a anterior a este pedido).
 * Nada sai para servidor do site. "Parar de ler" cancela.
 */
function lerEmVoz(acao: 'ler' | 'parar'): 'lendo' | 'parado' | 'nada' | 'sem_suporte' {
  if (typeof window === 'undefined' || !('speechSynthesis' in window) || typeof SpeechSynthesisUtterance === 'undefined') return 'sem_suporte'
  const voz = window.speechSynthesis
  if (acao === 'parar') {
    const falava = voz.speaking || voz.pending
    voz.cancel()
    return falava ? 'parado' : 'nada'
  }
  const ultima = [...lerConversa().msgs].reverse().find((m) => m.papel === 'assistente')
  if (!ultima) return 'nada'
  const fala = new SpeechSynthesisUtterance(textoParaFala(ultima.texto))
  fala.lang = 'pt-BR'
  voz.cancel()
  voz.speak(fala)
  return 'lendo'
}

/**
 * "Atualizar as leituras": pede a busca (todas as telas abertas buscam de novo) e espera a resposta chegar
 * ao chat — o estado ao vivo troca de objeto a cada busca —, por no máximo 10 s.
 */
async function atualizarLeituras(aoVivo: () => Promise<AoVivo | null>) {
  const antes = await aoVivo()
  const coletaAntes = antes?.tempoReal.coletadoEm ?? null
  const pedido = pedirAtualizacao()
  let v = antes
  if (pedido) {
    const fim = Date.now() + 10_000
    while (Date.now() < fim) {
      await new Promise((r) => setTimeout(r, 400))
      v = await aoVivo()
      if (v && antes && v.tempoReal !== antes.tempoReal) break
    }
  }
  const medicoes = (v?.tempoReal.leituras ?? []).map((l) => l.medidoEm?.getTime() ?? NaN).filter(Number.isFinite)
  return {
    pedido,
    coletaAntes,
    coletaDepois: v?.tempoReal.coletadoEm ?? null,
    medicaoMaisNova: medicoes.length ? new Date(Math.max(...medicoes)) : null,
    agora: new Date(),
  }
}

/** Nome da via → quantos trechos ela tem na base (ruas com o mesmo nome entram juntas). */
async function viasDeItajai(): Promise<Record<string, number> | null> {
  try {
    const g = await carregarViasItajai()
    const conta: Record<string, number> = {}
    for (const f of g.features) {
      const n = f.properties?.nome
      if (typeof n === 'string') conta[n] = (conta[n] ?? 0) + 1
    }
    return conta
  } catch {
    return null
  }
}
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

// Os traçados como URL, os mesmos arquivos que o Monitor baixa (o navegador reaproveita).
const TRACADOS = import.meta.glob('@dados/rios/*.geojson', { query: '?url', import: 'default', eager: true }) as Record<string, string>

async function propriedadesDoTracado(arquivo: string): Promise<PropriedadesDoTracado | null> {
  const chave = Object.keys(TRACADOS).find((k) => k.endsWith(`/${arquivo}.geojson`))
  if (!chave) return null
  try {
    const r = await fetch(TRACADOS[chave]!)
    if (!r.ok) return null
    const geo = (await r.json()) as { properties?: PropriedadesDoTracado }
    return geo.properties ?? null
  } catch {
    return null
  }
}

function cidadeDoCadastro(id: string): ReturnType<DadosDoChat['cidade']> {
  for (const [rioId, r] of Object.entries(estacoes.rios)) {
    const c = r.cidades.find((x) => x.id === id)
    if (c) return { cidade: c, rioId }
  }
  return null
}

let catalogo: Catalogo | null = null
export function catalogoDoSite(): Catalogo {
  catalogo ??= catalogoDoCadastro(estacoes as Parameters<typeof catalogoDoCadastro>[0])
  return catalogo
}

/**
 * @param aoVivo devolve as leituras ao vivo do chat, esperando a primeira busca (ver `ChatLocal`).
 */
export function useComandos(aoVivo: () => Promise<AoVivo | null> = async () => null): {
  contexto: () => Contexto
  nomeDaCidadeAtual: () => string | null
  /** `eco: false`: o pedido já está na conversa (continuação "e Gaspar?"); não repete a mensagem da pessoa. */
  tentar: (texto: string, eco?: boolean) => boolean
} {
  const navigate = useNavigate()
  const cat = useMemo(catalogoDoSite, [])
  const contexto = useCallback(() => contextoDaRota(rotaAgora(), monitorAtual()), [])
  const nomeDaCidadeAtual = useCallback(() => {
    const id = contexto().cidadeAtual
    return id ? nomeDaCidade(id, cat) : null
  }, [cat, contexto])

  const tentar = useCallback(
    (texto: string, eco = true) => {
      const ctx = contexto()
      const r = interpretar(texto, cat, ctx)
      if (!r) return false
      // Sem eco quando o chat já mostrou o pedido ("e Gaspar?" refeito como "mostrar Gaspar").
      if (eco) acrescentar({ papel: 'usuario', texto })
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
        dados: {
          aoVivo,
          cidade: cidadeDoCadastro,
          reguasNoMapa: (v: AoVivo) =>
            reguasNoMapa(estacoesTempoReal, v.tempoReal.leituras.map((l) => ({ titulo: l.estacao, nivel_m: l.nivel_m, medidoEm: l.medidoEm })), v.agora),
          tracado: propriedadesDoTracado,
          base: () => (typeof window === 'undefined' ? '' : baseDoSite(window.location.href)),
          viasItajai: viasDeItajai,
          ruasMancha: () => carregarRuasManchaItajai().catch(() => null),
          cotasRuas: () => carregarCotasRuas().catch(() => null),
          localizacao,
          preferencias,
          barragens: () => buscarBarragens(),
          mare: () => mareItajai,
          transito: () => ({ trechos, experimentais: trechosExperimentais }),
          referenciaChegada: () => historicoChegada.referencia_estudo,
          captados: () => eventosCaptados,
          atualizar: () => atualizarLeituras(aoVivo),
          aplicativo: () => ({ instalado: jaInstalado(), iphone: ehIphone(), pode: podeInstalar() }),
          privacidade: () => ({
            memoria: temMemoria(),
            seguidas: cidadesSeguidas().map((c) => c.id),
            letraGrande: letra() === 'grande',
            avisoLido: avisoLido(),
            contagem: contagemChatPermitida(),
          }),
          esquecer: () => {
            const ok = esquecerPreferencias()
            document.documentElement.dataset.letra = 'normal'
            avisarPreferencias()
            return ok
          },
          contagem: (permitir: boolean) => {
            const ok = gravarContagemChat(permitir)
            avisarPreferencias()
            return ok
          },
          limparConversa,
          voz: lerEmVoz,
          fontesDaCidade: (id: string) => {
            const c = cidadeDoCadastro(id)?.cidade as { fontes_tempo_real?: unknown } | undefined
            return Array.isArray(c?.fontes_tempo_real) ? c.fontes_tempo_real.filter((f): f is string => typeof f === 'string') : []
          },
        },
      }
      let saida: Saida | null = null
      executar(r.passos, ambiente, cat, ctx, () => textoDeAjuda(ctx, ctx.cidadeAtual ? nomeDaCidade(ctx.cidadeAtual, cat) : null))
        .then((s) => (saida = s))
        .then((s) => acrescentar({ papel: 'assistente', texto: s.texto, comando: true, ...(s.sugestoes ? { sugestoes: s.sugestoes } : {}), ...(s.link ? { link: s.link } : {}), ...(s.copiar ? { copiar: s.copiar } : {}) }))
        .catch(() => acrescentar({ papel: 'assistente', texto: 'Não consegui executar o pedido. Nada foi alterado depois do erro.', comando: true }))
        .finally(() => {
          marcarOcupado(false)
          // No celular, no Monitor, a conversa recolhe depois do pedido: o resultado está no MAPA (a folha
          // da régua, a cidade enquadrada), e a última resposta fica numa linha logo abaixo da caixa. Pedido que
          // só RESPONDE (leituras atrasadas, montante) ou prepara texto para copiar fica aberto: o resultado é a
          // conversa, e o botão "Copiar" sumiria com ela.
          const mexeuNoMapa = r.passos.some((p) => MUDA_A_TELA.has(p.tipo)) && !(saida as Saida | null)?.copiar
          if (mexeuNoMapa && contextoDaRota(rotaAgora(), null).naMonitor && typeof matchMedia === 'function' && matchMedia('(max-width: 700px)').matches) {
            abrirPainel(false)
          }
        })
      return true
    },
    [cat, contexto, navigate, aoVivo],
  )
  return { contexto, nomeDaCidadeAtual, tentar }
}
