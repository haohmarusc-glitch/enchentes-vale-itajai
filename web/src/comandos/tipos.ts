/**
 * Os comandos que o chat pode executar (docs/CHAT-GLOBAL-COMANDOS.md, 06/10/2026).
 *
 * O texto da pessoa só PROPÕE um destes passos; nenhum identificador sai do texto sem ser resolvido contra
 * o cadastro (`Catalogo`). Nada de URL, JavaScript ou nome inventado.
 */
import type { TemaDaLegenda } from './foz'

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
  // --- 2ª entrega (docs/CHAT-GLOBAL-COMANDOS.md)
  /** Quais leituras estão atrasadas ou velhas, pela regra de idade do site (`frescorDaCidade`). */
  | { tipo: 'atrasadas' }
  /** Filtro do Monitor: só as cidades e réguas sem leitura de agora; null limpa. */
  | { tipo: 'filtro'; filtro: 'sem_leitura' | 'acima_do_normal' | null }
  /** O gráfico das últimas horas, na página da cidade. */
  | { tipo: 'abrir_grafico'; cidadeId?: string }
  /** A variação medida na última hora, numa régua só. */
  | { tipo: 'ultima_hora'; cidadeId?: string }
  /** Fonte, cobertura e data da base do traçado do rio. `rio` = arquivo de `data/rios/`. */
  | { tipo: 'origem_tracado'; cidadeId?: string; rio?: string }
  /** O que fica a montante, ou os afluentes do trecho, pela árvore da bacia. */
  | { tipo: 'montante'; cidadeId?: string; foco: 'montante' | 'afluentes' }
  /** Centra o mapa num ponto de confluência gravado no cadastro (ou diz que não há ponto). */
  | { tipo: 'confluencia'; id: string }
  /** As réguas de uma cidade de várias réguas, lado a lado, sem subtrair. */
  | { tipo: 'comparar_reguas'; cidadeId?: string }
  /** O texto de compartilhar da cidade (regra D4): preparado para copiar, nunca enviado. */
  | { tipo: 'copiar_resumo'; cidadeId?: string }
  /** O endereço da tela aberta, com régua e fundo, para copiar. */
  | { tipo: 'copiar_link' }
  // --- 3ª entrega: rua no mapa
  /**
   * Uma rua: em Itajaí, o traçado destacado no mapa das manchas; em Gaspar e Brusque, os pontos de cota no
   * Monitor. `texto` é o que a pessoa escreveu ("rua hamilton pimentel"); casar com a base é da execução.
   */
  | { tipo: 'rua'; texto: string; cidadeId?: string; ano?: string; foco: 'mostrar' | 'manchas' }
  /** Tira o destaque da rua (mapa das manchas) ou a marca dos pontos (Monitor). */
  | { tipo: 'remover_destaque' }
  // --- 4ª entrega: o aparelho
  /** A régua mais perto da pessoa. O navegador pede permissão; nada é guardado nem enviado. */
  | { tipo: 'localizacao' }
  /** Texto pronto para relatar um problema na tela (não há canal: a pessoa copia e envia). */
  | { tipo: 'relatar' }
  /** As cidades guardadas no aparelho: a minha, seguir, deixar de seguir, listar. */
  | { tipo: 'preferencia_cidade'; acao: 'minha' | 'seguir' | 'deixar' | 'listar'; cidadeId?: string }
  | { tipo: 'letra'; tamanho: 'normal' | 'grande' }
  | { tipo: 'tela_cheia' }
  // --- 5ª entrega: o tempo e a bacia
  /** A reprodução das últimas 24 h do Monitor: tocar, pausar ou ir a um instante ("às 14h", "há 3 horas"). */
  | { tipo: 'reproducao'; acao: 'tocar' | 'pausar' | 'ir'; hora?: number; minuto?: number; horasAtras?: number }
  /** Onde chove mais agora, pelos pluviômetros com leitura recente. */
  | { tipo: 'chuva_agora' }
  /** O estado das comportas das barragens de contenção, como a fonte publica. */
  | { tipo: 'barragens' }
  /** A maré no porto de Itajaí, pela tábua da Marinha. */
  | { tipo: 'mare' }
  /** De onde vem a leitura de uma cidade: estação, hora e fontes cadastradas. */
  | { tipo: 'fonte_leitura'; cidadeId?: string }
  // 6ª entrega: o rio agora, de cima a baixo.
  | { tipo: 'quanto_falta'; cidadeId?: string }
  | { tipo: 'tendencia'; cidadeId?: string }
  | { tipo: 'maximo_24h'; cidadeId?: string }
  | { tipo: 'panorama' }
  | { tipo: 'de_cima'; cidadeId?: string }
  // 7ª entrega: a foz (chegada × maré em Itajaí) e o que o mapa quer dizer.
  | { tipo: 'chegada_itajai' }
  | { tipo: 'simular_chegada'; hora: number; minuto?: number; dia?: 'hoje' | 'amanha' | 'ontem' }
  | { tipo: 'legenda'; tema: TemaDaLegenda }
  | { tipo: 'animacoes'; acao: 'pausar' | 'retomar' }
  | { tipo: 'legenda_mapa'; acao: 'abrir' | 'fechar' }
  // 8ª entrega: o site e os seus dados.
  | { tipo: 'atualizar' }
  | { tipo: 'oficial' }
  | { tipo: 'instalar' }
  | { tipo: 'privacidade' }
  | { tipo: 'esquecer'; confirmado: boolean }
  | { tipo: 'contagem'; permitir: boolean }
  | { tipo: 'limpar_conversa' }
  | { tipo: 'emergencia' }
  // 11ª entrega: as palavras do rio e a resposta em voz alta.
  | { tipo: 'glossario'; termos: string[] }
  | { tipo: 'termos' }
  | { tipo: 'voz'; acao: 'ler' | 'parar' }
  // 12ª entrega: o Monitor, peça por peça.
  | { tipo: 'enquadrar'; alvo: 'rio'; rioId: 'itajai-acu' | 'itajai-mirim' }
  | { tipo: 'enquadrar'; alvo: 'barragens' }
  | { tipo: 'fechar_painel' }
  | { tipo: 'menu_cidades'; acao: 'abrir' | 'fechar' }
  // 13ª entrega: várias cidades de uma vez (uma lista dita, ou as cidades que a pessoa segue).
  | { tipo: 'varias_cidades'; cidadeIds?: string[]; seguidas?: boolean; copiar?: boolean }
  /** 14ª: a linha do tempo da cheia de agora, na série de uma régua. `cota` já é a chave do cadastro. */
  | { tipo: 'linha_do_tempo'; pergunta: 'cruzou_cota' | 'ha_quanto_tempo' | 'comecou_a_subir' | 'variacao'; cidadeId?: string; cota?: string; horas?: number }
  /**
   * 15ª: as cheias que a coleta do site já captou (`data/eventos-captados.json`). `mes` é 1–12 e `dia` é
   * `AAAA-MM-DD`; `cota` é a chave do cadastro, para "quantas vezes passou da cota de alerta".
   */
  | { tipo: 'captados'; pergunta: 'lista' | 'ultima' | 'maior' | 'quantas' | 'periodo'; cidadeId?: string; cota?: string; mes?: number; ano?: number; dia?: string }

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
  /** Coordenada da régua da cidade no cadastro, quando há. */
  lat?: number
  lon?: number
  /** `coordenadas_status: "não confirmada"` no cadastro (Timbó). */
  coordenadaNaoConfirmada?: boolean
}

export interface ReguaDoCatalogo {
  /** Código do cadastro (`estacoes_tempo_real[].codigo`), a chave do seletor do Monitor. */
  codigo: string
  /** Título da régua na fonte (`estacoes_tempo_real[].titulo`): a chave da leitura e da série. */
  titulo: string
  /** Nome do lugar, como o mapa mostra ("Sítio Sr. Hilário"). */
  nome: string
  cidadeId: string
  lat?: number
  lon?: number
}

/** Um ponto de confluência com coordenada gravada no cadastro, e a fonte dela. */
export interface Confluencia {
  id: string
  nome: string
  /** Palavras (normalizadas) que nomeiam este encontro num pedido: "benedito", "trombudo". */
  chaves: string[]
  lat: number
  lon: number
  fonte: string
}

/** Um rio que entra na bacia sem ponto de confluência gravado: o chat diz isso, não inventa. */
export interface ConfluenciaSemPonto {
  id: string
  nome: string
  chaves: string[]
  motivo: string
}

/** A árvore de um rio, como o cadastro a declara (`_topologia`). */
export interface TopologiaDoRio {
  rioId: string
  tronco: string[]
  cabeceiras: string[]
  laterais: { id: string; rio: string; entraPertoDe: string }[]
  afluentesSemRegua: { nome: string; entraPertoDe: string; pontoExato: string | null }[]
}

export interface Catalogo {
  cidades: CidadeDoCatalogo[]
  reguas: ReguaDoCatalogo[]
  confluencias?: Confluencia[]
  semPonto?: ConfluenciaSemPonto[]
  topologia?: TopologiaDoRio[]
  /** Cidade fora da árvore, com a ligação que a fonte dá (Trombudo Central → Itajaí do Oeste). */
  foraDaArvore?: { id: string; rio: string; chegaA: string; lat: number; lon: number; fonte: string }[]
}

/** O resultado REAL de um passo, dito ao chat. */
export interface Resultado {
  ok: boolean
  texto: string
}
