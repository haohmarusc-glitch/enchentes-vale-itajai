/**
 * Os comandos que o chat pode executar (docs/CHAT-GLOBAL-COMANDOS.md, 06/10/2026).
 *
 * O texto da pessoa só PROPÕE um destes passos; nenhum identificador sai do texto sem ser resolvido contra
 * o cadastro (`Catalogo`). Nada de URL, JavaScript ou nome inventado.
 */

export type Fundo = 'escuro' | 'satelite' | 'mapa'

export type Aba = 'agora' | 'rua' | 'historico' | 'fontes'

export type Passo =
  /** Abre o Monitor enquadrado na cidade (ou reenquadra, se já está nela). */
  | { tipo: 'ir_cidade'; cidadeId: string }
  /** Abre o Monitor na bacia inteira. */
  | { tipo: 'monitor_bacia' }
  /** Abre a página da cidade, numa aba. */
  | { tipo: 'abrir_pagina'; cidadeId: string; aba?: Aba }
  /** Abre uma rota fixa do site (início, rios, foz, mapa de manchas). */
  | { tipo: 'abrir_rota'; rota: string; descricao: string }
  /** Uma régua pelo código do cadastro (DC-05), ou todas as da cidade. */
  | { tipo: 'escolher_regua'; codigo: string | 'todas' }
  /** A régua da cidade aberta: reenquadra o pino dela. */
  | { tipo: 'aproximar_regua' }
  | { tipo: 'zoom'; sentido: 'mais' | 'menos' }
  | { tipo: 'ver_bacia' }
  | { tipo: 'fundo'; fundo: Fundo }
  /** Liga uma camada: pelo ano, pelo rótulo exato (sugestão do próprio chat) ou, sem nada, pergunta qual. */
  | { tipo: 'camada'; acao: 'ligar' | 'desligar'; ano?: string; rotulo?: string }
  /** Sai da reprodução e volta à leitura mais recente. */
  | { tipo: 'ao_vivo' }
  /** Desfaz a última ação do chat (vista, régua, fundo, camada e página). */
  | { tipo: 'voltar' }
  | { tipo: 'o_que_vejo' }
  | { tipo: 'atual_ou_historico' }
  | { tipo: 'por_que_cinza'; cidadeId?: string }
  | { tipo: 'coordenada'; cidadeId?: string }
  | { tipo: 'ajuda' }

export type Interpretacao =
  | { tipo: 'comandos'; passos: Passo[] }
  /** Era pedido, mas falta escolher (régua ambígua) ou um trecho não foi entendido: nada é executado. */
  | { tipo: 'esclarecer'; texto: string; sugestoes: string[] }

/** O que a tela tem aberto agora. "Aqui", "essa cidade", "essa régua" usam isto. */
export interface Contexto {
  /** Cidade da página ou do Monitor; null na bacia inteira ou fora de uma cidade. */
  cidadeAtual: string | null
  naMonitor: boolean
  /** Código da régua selecionada no Monitor, se houver. */
  reguaAtual: string | null
}

export interface CidadeDoCatalogo {
  id: string
  nome: string
  /** Rio da página da cidade: `/acu/<id>` ou `/mirim/<id>`. Itajaí (foz) tem página própria. */
  rio: 'acu' | 'mirim'
}

export interface ReguaDoCatalogo {
  /** Código do cadastro (`estacoes_tempo_real[].codigo`), a chave do seletor do Monitor. */
  codigo: string
  /** Nome do lugar, como o mapa mostra ("Sítio Sr. Hilário"). */
  nome: string
  cidadeId: string
}

export interface Catalogo {
  cidades: CidadeDoCatalogo[]
  reguas: ReguaDoCatalogo[]
}

/** O resultado REAL de um passo, dito ao chat. */
export interface Resultado {
  ok: boolean
  texto: string
}
