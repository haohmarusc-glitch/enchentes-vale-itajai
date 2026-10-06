/**
 * A ponte entre o chat e o Monitor (docs/CHAT-GLOBAL-COMANDOS.md, 06/10/2026).
 *
 * O Monitor registra aqui os próprios executores: as MESMAS funções que os botões usam (escolher régua,
 * zoom, ver tudo, fundo, camada). O chat nunca clica no DOM nem mexe no estado do Monitor por fora.
 * Fora do Monitor não há controle registrado, e quem precisa do mapa abre o Monitor e espera ele ficar pronto.
 */
import type { Fundo, Resultado } from './tipos'

/** O que o Monitor guarda antes de uma ação do chat, para "voltar ao mapa de antes". */
export interface Retrato {
  rota: string
  /** Cidade do Monitor; null na bacia inteira. Ausente quando o retrato é de outra página. */
  cidade?: string | null
  vista?: unknown
  regua?: string | null
  fundo?: Fundo
  camada?: string | null
  filtro?: FiltroMonitor
  marca?: MarcaNoMapa | null
}

/** Filtro do Monitor pedido pelo chat (2ª entrega): só cidades e réguas sem leitura de agora. */
export type FiltroMonitor = 'sem_leitura' | null

/** Um ponto marcado no mapa pelo chat (confluência), com o nome e a fonte que o painel mostra. */
export interface MarcaNoMapa {
  lat: number
  lon: number
  rotulo: string
  /** Largura da vista, em km (padrão 6; rua, mais perto). */
  km?: number
  /** Outros pontos da mesma marca (os pontos de cota de uma rua): cada um ganha o seu anel. */
  extras?: { lat: number; lon: number }[]
}

export interface EstadoMonitor {
  cidade: string | null
  cidadeNome: string | null
  regua: { codigo: string; rotulo: string } | null
  /** As réguas que o seletor oferece na cidade aberta (vazio fora de Itajaí). */
  reguas: { codigo: string; rotulo: string }[]
  fundo: Fundo
  /** A camada de cheia desenhada agora, com o rótulo da fonte; null sem camada. */
  camada: string | null
  /** As camadas que a cidade aberta tem, para o chat escolher pelo ano ou perguntar qual. */
  camadasDisponiveis: { arquivo: string; rotulo: string }[]
  /** Reprodução ligada: a hora mostrada (passado). Null = leituras ao vivo. */
  reproducao: string | null
  filtro?: FiltroMonitor
  /** O ponto marcado pelo chat, pelo nome; null sem marca. */
  marca?: string | null
}

export interface Explicacao {
  cidadeNome: string
  /** Rótulo da faixa como o painel mostra. */
  faixa: string
  /** O "Por que está cinza?" do painel, ou null quando a cidade tem cor. */
  motivoCinza: string | null
  /** De onde vem o pino (`textoDaPosicao`) e a equivalência com a estação estadual, se houver. */
  posicao: string
  equivalencia: string | null
}

export interface ControleMonitor {
  cidade: string | null
  /** Enquadrado e com a cena montada: pode receber comando. */
  pronto: boolean
  estado(): EstadoMonitor
  escolherRegua(codigo: string | 'todas'): Resultado
  enquadrarCidade(): Resultado
  zoom(sentido: 'mais' | 'menos'): Resultado
  verBacia(): Resultado
  fundo(f: Fundo): Resultado
  /** `arquivo` = uma camada de `camadasDisponiveis`; 'off' desliga. */
  camada(arquivo: string | 'off'): Resultado
  aoVivo(): Resultado
  /** Liga ou limpa o filtro "só sem leitura de agora"; o filtro aparece escrito na tela, com "limpar". */
  filtrar?(f: FiltroMonitor): Resultado
  /** A reprodução das últimas 24 h: tocar, pausar ou ir a um instante do passado. */
  reproducao?(p: { acao: 'tocar' } | { acao: 'pausar' } | { acao: 'ir'; instante: Date }): Resultado
  /** Marca um ponto (confluência) e centra nele; null tira a marca. */
  marcarPonto?(p: MarcaNoMapa | null): Resultado
  explicar(cidadeId: string): Explicacao | null
  retrato(): Retrato
  restaurar(r: Retrato): Resultado
}

let atual: ControleMonitor | null = null
const ouvintes = new Set<() => void>()

/** O Monitor chama a cada mudança relevante (cidade, pronto). Devolve a função que desregistra. */
export function registrarMonitor(c: ControleMonitor): () => void {
  atual = c
  ouvintes.forEach((f) => f())
  return () => {
    if (atual === c) {
      atual = null
      ouvintes.forEach((f) => f())
    }
  }
}

export function monitorAtual(): ControleMonitor | null {
  return atual
}

/**
 * Espera o Monitor da cidade pedida (null = bacia) ficar pronto. Devolve null se não ficar em `ms`:
 * o chat diz que não conseguiu, em vez de fingir que fez.
 */
export function esperarMonitor(cidade: string | null, ms = 10_000): Promise<ControleMonitor | null> {
  const serve = () => (atual && atual.pronto && atual.cidade === cidade ? atual : null)
  const ja = serve()
  if (ja) return Promise.resolve(ja)
  return new Promise((resolver) => {
    const ouvir = () => {
      const c = serve()
      if (c) {
        ouvintes.delete(ouvir)
        clearTimeout(limite)
        resolver(c)
      }
    }
    const limite = setTimeout(() => {
      ouvintes.delete(ouvir)
      resolver(null)
    }, ms)
    ouvintes.add(ouvir)
  })
}
