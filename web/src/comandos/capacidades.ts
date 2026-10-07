/**
 * O catálogo único de capacidades do chat (17ª entrega — PR 1 do handoff de qualidade,
 * docs/HANDOFF-QUALIDADE-CHAT-2026-10-07.md).
 *
 * Uma entrada por tipo de `Passo`, e o TypeScript cobra que nenhuma falte (`Record<Passo['tipo'], …>`): um passo
 * novo sem ficha aqui não compila. A ficha diz o que o passo faz, dá exemplos que o leitor de hoje entende (o
 * teste do catálogo roda cada um), declara os argumentos e se o passo muda a tela (`executar.ts` continua sendo
 * quem decide; o teste confere que os dois concordam).
 *
 * Daqui saem a documentação (`docs/CHAT-CAPACIDADES.md`), o conjunto "dev" da bateria de avaliação (`avaliacao/`)
 * e, no PR 2 do handoff, o esquema do classificador. O catálogo de comandos NÃO é o catálogo de cidades e réguas
 * (`catalogo.ts`): um diz o que o chat sabe fazer; o outro, sobre o que.
 */
import type { Contexto, Passo } from './tipos'

export type Grupo =
  | 'navegacao' // abrir telas e enquadrar o mapa
  | 'mapa' // fundo, camadas, legenda, animações, reprodução
  | 'leituras' // o rio agora: níveis, faixas, tendência, fontes
  | 'rio' // a bacia: montante, confluência, traçado, barragens, maré, chuva
  | 'historico' // o que o site já captou e a foz
  | 'ruas' // cotas de rua e manchas
  | 'aparelho' // localização, preferências, letra, tela cheia, voz
  | 'site' // atualizar, oficial, instalar, privacidade, conversa, emergência, ajuda, glossário

export type TipoDeArgumento = 'cidadeId' | 'cidadeIds' | 'codigoRegua' | 'rioId' | 'enum' | 'numero' | 'texto' | 'ano' | 'mes' | 'dia' | 'booleano' | 'termos'

export interface Argumento {
  nome: string
  tipo: TipoDeArgumento
  obrigatorio: boolean
  /** Valores possíveis, quando `tipo` é `enum`. */
  valores?: readonly string[]
  /** Como o argumento é preenchido quando a pessoa não o diz. */
  semDizer?: 'cidade da tela' | 'pergunta qual' | 'padrão'
  nota?: string
}

export interface Exemplo {
  texto: string
  /** O exemplo só vira este passo com este contexto (o padrão é fora do Monitor, sem cidade). */
  contexto?: Partial<Contexto>
}

export interface Capacidade {
  grupo: Grupo
  entrega: number
  titulo: string
  descricao: string
  exemplos: Exemplo[]
  argumentos: Argumento[]
  /** O passo altera a tela (navega, mexe no mapa) — `executar.ts` (`MUDA_A_TELA`) é quem manda; aqui é declaração. */
  mudaTela: boolean
  /** O passo só faz sentido com o Monitor aberto (o executor o abre antes). */
  precisaDoMapa: boolean
  /** O que o passo lê para responder. */
  dados: readonly ('aoVivo' | 'serie' | 'cadastro' | 'cotasRuas' | 'captados' | 'preferencias' | 'mare' | 'barragens' | 'tracado' | 'transito' | 'aparelho' | 'monitor' | 'nenhum')[]
  /** Quando o passo pede esclarecimento em vez de executar. */
  esclarece?: string
  /** O que o passo nunca faz (as recusas que os testes travam). */
  nunca?: string
}

const cidade = (semDizer: Argumento['semDizer'] = 'cidade da tela'): Argumento => ({ nome: 'cidadeId', tipo: 'cidadeId', obrigatorio: false, semDizer })
const cidadeObrigatoria: Argumento = { nome: 'cidadeId', tipo: 'cidadeId', obrigatorio: true }
const noMonitor: Partial<Contexto> = { naMonitor: true }
const emItajai: Partial<Contexto> = { cidadeAtual: 'itajai', naMonitor: true }

export const CAPACIDADES: Record<Passo['tipo'], Capacidade> = {
  // --- 1ª entrega: navegação e o Monitor
  ir_cidade: {
    grupo: 'navegacao', entrega: 1, titulo: 'Abrir o Monitor numa cidade',
    descricao: 'Abre o Monitor enquadrado na cidade (ou reenquadra, se já está nela). Exige verbo: "Blumenau" sozinho pergunta o que a pessoa quer da cidade, com exemplos (18ª).',
    exemplos: [{ texto: 'mostrar Blumenau' }, { texto: 'ir para Taió' }, { texto: 'abrir Rio do Sul' }],
    argumentos: [cidadeObrigatoria], mudaTela: true, precisaDoMapa: false, dados: ['cadastro'],
    esclarece: 'Nome parecido com uma cidade do cadastro ("Blumenal") ou verbo com erro ("msotrar") pergunta "você quis dizer…?" e não faz nada.',
  },
  monitor_bacia: {
    grupo: 'navegacao', entrega: 1, titulo: 'Abrir o Monitor da bacia',
    descricao: 'Abre o Monitor na bacia inteira.',
    exemplos: [{ texto: 'abrir o monitor' }, { texto: 'ir para o monitor' }],
    argumentos: [], mudaTela: true, precisaDoMapa: false, dados: ['nenhum'],
  },
  abrir_pagina: {
    grupo: 'navegacao', entrega: 1, titulo: 'Abrir a página da cidade',
    descricao: 'Abre a página da cidade numa aba: Agora, Minha rua, Histórico ou Fontes. Na página da cidade (ou no Monitor dela), "histórico", "minha rua" ou "fontes" sozinhos bastam (18ª).',
    exemplos: [{ texto: 'histórico de Blumenau' }, { texto: 'abrir a página de Gaspar' }, { texto: 'minha rua em Blumenau' }, { texto: 'fontes de Brusque' }],
    argumentos: [cidadeObrigatoria, { nome: 'aba', tipo: 'enum', obrigatorio: false, valores: ['agora', 'rua', 'historico', 'fontes'], semDizer: 'padrão' }],
    mudaTela: true, precisaDoMapa: false, dados: ['cadastro'],
  },
  abrir_rota: {
    grupo: 'navegacao', entrega: 1, titulo: 'Abrir uma tela fixa do site',
    descricao: 'O início, a página de um rio, a foz ou o mapa das manchas. Só rotas do próprio site: nunca uma URL dita.',
    exemplos: [{ texto: 'abrir o início' }, { texto: 'mostrar o Itajaí-Açu' }, { texto: 'ver a foz' }, { texto: 'abrir o mapa das manchas' }],
    argumentos: [{ nome: 'rota', tipo: 'enum', obrigatorio: true, valores: ['/', '/acu', '/mirim', '/itajai', '/itajai?secao=manchas'] }],
    mudaTela: true, precisaDoMapa: false, dados: ['nenhum'],
  },
  escolher_regua: {
    grupo: 'navegacao', entrega: 1, titulo: 'Escolher uma régua',
    descricao: 'Uma régua pelo código do cadastro (DC-05) ou pelo nome do lugar, ou todas as da cidade.',
    exemplos: [{ texto: 'zoom na régua DC-05' }, { texto: 'todas as réguas de Itajaí' }, { texto: 'régua do Limoeiro' }],
    argumentos: [{ nome: 'codigo', tipo: 'codigoRegua', obrigatorio: true }], mudaTela: true, precisaDoMapa: true, dados: ['cadastro', 'monitor'],
    esclarece: 'Nome que casa com mais de uma régua ("murta") pergunta qual, com as opções; código inexistente diz que não há.',
  },
  aproximar_regua: {
    grupo: 'navegacao', entrega: 1, titulo: 'Aproximar a régua da cidade aberta',
    descricao: 'Reenquadra o pino da cidade aberta no Monitor.',
    exemplos: [{ texto: 'aproximar a régua' }, { texto: 'zoom na régua' }],
    argumentos: [], mudaTela: true, precisaDoMapa: true, dados: ['monitor'],
    esclarece: 'Em Itajaí (onze réguas) sem régua escolhida, pergunta qual delas; nunca escolhe uma.',
  },
  zoom: {
    grupo: 'navegacao', entrega: 1, titulo: 'Aproximar ou afastar o mapa',
    descricao: 'Um passo de zoom para dentro ou para fora.',
    exemplos: [{ texto: 'aproximar' }, { texto: 'afastar' }, { texto: 'mais zoom' }],
    argumentos: [{ nome: 'sentido', tipo: 'enum', obrigatorio: true, valores: ['mais', 'menos'] }], mudaTela: true, precisaDoMapa: true, dados: ['monitor'],
  },
  ver_bacia: {
    grupo: 'navegacao', entrega: 1, titulo: 'Ver a bacia toda',
    descricao: 'Reenquadra o mapa na bacia inteira.',
    exemplos: [{ texto: 'ver a bacia toda' }, { texto: 'mostrar tudo' }],
    argumentos: [], mudaTela: true, precisaDoMapa: true, dados: ['monitor'],
  },
  fundo: {
    grupo: 'mapa', entrega: 1, titulo: 'Trocar o fundo do mapa',
    descricao: 'Escuro, satélite ou mapa de ruas — os três fundos que o Monitor já tem.',
    exemplos: [{ texto: 'satélite' }, { texto: 'fundo escuro' }, { texto: 'mapa de ruas' }],
    argumentos: [{ nome: 'fundo', tipo: 'enum', obrigatorio: true, valores: ['escuro', 'satelite', 'mapa'] }], mudaTela: true, precisaDoMapa: true, dados: ['monitor'],
  },
  camada: {
    grupo: 'mapa', entrega: 1, titulo: 'Ligar ou desligar uma camada de cheia',
    descricao: 'Liga a mancha de um ano (ou o rótulo exato que o Monitor oferece) ou desliga as camadas. Só onde a camada existe; ano ou rótulo fora da lista para a cadeia e lista as camadas (o leitor não as conhece; quem pergunta é o executor).',
    exemplos: [{ texto: 'ligar as manchas de 2008' }, { texto: 'desligar as manchas' }, { texto: 'camada 2011' }],
    argumentos: [{ nome: 'acao', tipo: 'enum', obrigatorio: true, valores: ['ligar', 'desligar'] }, { nome: 'ano', tipo: 'ano', obrigatorio: false, semDizer: 'pergunta qual' }, { nome: 'rotulo', tipo: 'texto', obrigatorio: false }],
    mudaTela: true, precisaDoMapa: true, dados: ['monitor'],
  },
  ao_vivo: {
    grupo: 'mapa', entrega: 1, titulo: 'Voltar à leitura mais recente',
    descricao: 'Sai da reprodução e volta ao agora.',
    exemplos: [{ texto: 'voltar ao agora' }, { texto: 'ir para a leitura mais recente' }, { texto: 'parar a reprodução' }],
    argumentos: [], mudaTela: true, precisaDoMapa: true, dados: ['monitor'],
  },
  voltar: {
    grupo: 'navegacao', entrega: 1, titulo: 'Desfazer a última ação do chat',
    descricao: 'Volta à vista, régua, fundo, camada ou página de antes (pilha de retratos do próprio chat). Restaura um retrato em vez de guardar outro, por isso fica fora de `MUDA_A_TELA`.',
    exemplos: [{ texto: 'voltar ao mapa de antes' }, { texto: 'desfazer' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['monitor'],
  },
  o_que_vejo: {
    grupo: 'mapa', entrega: 1, titulo: 'O que estou vendo',
    descricao: 'Cidade, régua, fundo, camada ativa e reprodução, lidos do estado do Monitor.',
    exemplos: [{ texto: 'o que estou vendo?' }, { texto: 'explique o mapa' }],
    argumentos: [], mudaTela: false, precisaDoMapa: true, dados: ['monitor'],
  },
  atual_ou_historico: {
    grupo: 'mapa', entrega: 1, titulo: 'Atual ou histórico',
    descricao: 'Diz se a tela mostra o agora, uma reprodução ou uma camada histórica.',
    exemplos: [{ texto: 'essa informação é atual ou histórica?' }, { texto: 'essa leitura é de agora?' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['monitor'],
  },
  por_que_cinza: {
    grupo: 'leituras', entrega: 1, titulo: 'Por que a régua está cinza',
    descricao: 'O mesmo motivo que o painel já mostra (sem leitura, leitura velha, sem cota, estuário); nunca um segundo diagnóstico.',
    exemplos: [{ texto: 'por que essa régua está cinza?' }, { texto: 'por que Lontras está cinza?' }],
    argumentos: [cidade()], mudaTela: false, precisaDoMapa: false, dados: ['aoVivo', 'cadastro'],
  },
  coordenada: {
    grupo: 'leituras', entrega: 1, titulo: 'A coordenada do pino foi confirmada',
    descricao: 'A origem da posição do pino e a equivalência estadual, como o cadastro declara.',
    exemplos: [{ texto: 'essa coordenada foi confirmada?' }, { texto: 'o pino de Timbó está no lugar certo?' }],
    argumentos: [cidade()], mudaTela: false, precisaDoMapa: false, dados: ['cadastro'],
  },
  ajuda: {
    grupo: 'site', entrega: 1, titulo: 'O que posso pedir',
    descricao: 'A lista do que o chat faz, adaptada à tela aberta.',
    exemplos: [{ texto: 'o que posso pedir?' }, { texto: 'ajuda' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['nenhum'],
  },
  // --- 2ª entrega
  atrasadas: {
    grupo: 'leituras', entrega: 2, titulo: 'Quais leituras estão atrasadas',
    descricao: 'A idade de cada leitura pela regra de leitura velha do site.',
    exemplos: [{ texto: 'quais leituras estão atrasadas?' }, { texto: 'tem régua parada?' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['aoVivo'],
  },
  filtro: {
    grupo: 'mapa', entrega: 2, titulo: 'Filtrar as réguas do Monitor',
    descricao: 'Só as sem leitura de agora, só as acima do normal, ou limpar o filtro.',
    exemplos: [{ texto: 'mostrar só as réguas sem leitura' }, { texto: 'só as cidades em alerta' }, { texto: 'limpar os filtros' }],
    argumentos: [{ nome: 'filtro', tipo: 'enum', obrigatorio: true, valores: ['sem_leitura', 'acima_do_normal', 'null'] }], mudaTela: true, precisaDoMapa: true, dados: ['monitor'],
  },
  abrir_grafico: {
    grupo: 'navegacao', entrega: 2, titulo: 'Abrir o gráfico da cidade',
    descricao: 'A página da cidade, na aba com a série das últimas horas.',
    exemplos: [{ texto: 'abrir o gráfico de Blumenau' }, { texto: 'gráfico desta régua' }],
    argumentos: [cidade()], mudaTela: true, precisaDoMapa: false, dados: ['cadastro'],
  },
  ultima_hora: {
    grupo: 'leituras', entrega: 2, titulo: 'O que mudou na última hora',
    descricao: 'A variação medida na última hora, numa régua só, com lacunas e o passo das medições.',
    exemplos: [{ texto: 'o que mudou na última hora em Blumenau?' }, { texto: 'quanto subiu na última hora?' }],
    argumentos: [cidade()], mudaTela: false, precisaDoMapa: false, dados: ['serie'],
    esclarece: 'Cidade de várias réguas sem régua escolhida: pede para escolher.',
  },
  origem_tracado: {
    grupo: 'rio', entrega: 2, titulo: 'De onde vem o traçado',
    descricao: 'Fonte e cobertura do GeoJSON do rio.',
    exemplos: [{ texto: 'de onde vem esse traçado?' }, { texto: 'de onde vem o traçado do Benedito?' }],
    argumentos: [cidade(), { nome: 'rio', tipo: 'texto', obrigatorio: false }], mudaTela: false, precisaDoMapa: false, dados: ['tracado'],
  },
  montante: {
    grupo: 'rio', entrega: 2, titulo: 'O que fica a montante; os afluentes',
    descricao: 'Pela árvore da bacia do cadastro. Ligação não é previsão de impacto.',
    exemplos: [{ texto: 'o que fica a montante de Blumenau?' }, { texto: 'afluentes de Indaial' }],
    argumentos: [cidade(), { nome: 'foco', tipo: 'enum', obrigatorio: true, valores: ['montante', 'afluentes'] }], mudaTela: false, precisaDoMapa: false, dados: ['cadastro'],
  },
  confluencia: {
    grupo: 'rio', entrega: 2, titulo: 'Ver uma confluência',
    descricao: 'Centra o mapa num ponto de confluência gravado no cadastro, ou diz que não há ponto.',
    exemplos: [{ texto: 'ver a confluência do Benedito' }, { texto: 'onde nasce o Itajaí-Açu?' }],
    argumentos: [{ nome: 'id', tipo: 'texto', obrigatorio: true }], mudaTela: true, precisaDoMapa: false, dados: ['cadastro'],
    esclarece: 'Sem o rio ("ver a confluência") pergunta de qual; rio fora do cadastro diz que não tem.',
  },
  comparar_reguas: {
    grupo: 'leituras', entrega: 2, titulo: 'Comparar as réguas de uma cidade',
    descricao: 'Lado a lado, com hora e referência; nunca subtrai zeros diferentes.',
    exemplos: [{ texto: 'comparar as réguas de Itajaí' }],
    argumentos: [cidade()], mudaTela: false, precisaDoMapa: false, dados: ['aoVivo'],
  },
  copiar_resumo: {
    grupo: 'leituras', entrega: 2, titulo: 'Copiar o resumo da cidade',
    descricao: 'O texto do WhatsApp (D4: sem endereço do site, com a hora, sem ordem de ação), preparado para copiar; nunca enviado.',
    exemplos: [{ texto: 'copiar resumo de Blumenau' }, { texto: 'copiar o resumo desta cidade' }],
    argumentos: [cidade()], mudaTela: false, precisaDoMapa: false, dados: ['aoVivo'],
  },
  copiar_link: {
    grupo: 'site', entrega: 2, titulo: 'Copiar o link da tela',
    descricao: 'O endereço da tela aberta, com régua e fundo, e o aviso de que o site só abre para e-mail cadastrado.',
    exemplos: [{ texto: 'copiar link desta visualização' }, { texto: 'copiar o link' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['monitor'],
  },
  // --- 3ª entrega
  rua: {
    grupo: 'ruas', entrega: 3, titulo: 'Mostrar uma rua no mapa',
    descricao: 'Em Itajaí, o traçado da via sobre as manchas; em Gaspar e Brusque, os pontos de cota no Monitor; nas outras, só a cota em texto. O nome é casado com a base na execução.',
    exemplos: [{ texto: 'mostrar a rua Lauro Müller em Itajaí' }, { texto: 'manchas na rua Hamilton Pimentel' }],
    argumentos: [{ nome: 'texto', tipo: 'texto', obrigatorio: true }, cidade(), { nome: 'ano', tipo: 'ano', obrigatorio: false }, { nome: 'foco', tipo: 'enum', obrigatorio: true, valores: ['mostrar', 'manchas'] }],
    mudaTela: true, precisaDoMapa: false, dados: ['cotasRuas', 'cadastro'],
    esclarece: 'Rua homônima pede para escolher o trecho.',
  },
  remover_destaque: {
    grupo: 'ruas', entrega: 3, titulo: 'Tirar o destaque da rua',
    descricao: 'Tira o destaque do mapa das manchas ou a marca dos pontos no Monitor.',
    exemplos: [{ texto: 'remover o destaque da rua' }, { texto: 'tirar a marca' }],
    argumentos: [], mudaTela: true, precisaDoMapa: false, dados: ['monitor'],
  },
  // --- 4ª entrega
  localizacao: {
    grupo: 'aparelho', entrega: 4, titulo: 'Usar minha localização',
    descricao: 'A régua mais perto. O navegador pede permissão na hora; nada é guardado nem enviado.',
    exemplos: [{ texto: 'usar minha localização' }, { texto: 'qual a régua mais perto de mim?' }],
    argumentos: [], mudaTela: true, precisaDoMapa: false, dados: ['aparelho', 'cadastro'],
  },
  relatar: {
    grupo: 'site', entrega: 4, titulo: 'Relatar um problema',
    descricao: 'Prepara um texto com a tela e a leitura para a pessoa copiar; não há canal de envio.',
    exemplos: [{ texto: 'relatar problema nesta régua' }, { texto: 'a leitura está errada' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['monitor'],
  },
  preferencia_cidade: {
    grupo: 'aparelho', entrega: 4, titulo: 'Minha cidade e as que eu sigo',
    descricao: 'Guarda no aparelho a minha cidade e as seguidas; lista e deixa de seguir. Só no aparelho.',
    exemplos: [{ texto: 'minha cidade é Gaspar' }, { texto: 'seguir Blumenau' }, { texto: 'quais cidades eu sigo?' }, { texto: 'deixar de seguir Gaspar' }],
    argumentos: [{ nome: 'acao', tipo: 'enum', obrigatorio: true, valores: ['minha', 'seguir', 'deixar', 'listar'] }, cidade('pergunta qual')],
    mudaTela: false, precisaDoMapa: false, dados: ['preferencias'],
    esclarece: '"Minha cidade é X" com X fora do cadastro diz que não dá para guardar.',
  },
  letra: {
    grupo: 'aparelho', entrega: 4, titulo: 'Letra maior ou normal',
    descricao: 'Guardado no aparelho.',
    exemplos: [{ texto: 'letra maior' }, { texto: 'letra normal' }],
    argumentos: [{ nome: 'tamanho', tipo: 'enum', obrigatorio: true, valores: ['normal', 'grande'] }], mudaTela: false, precisaDoMapa: false, dados: ['preferencias'],
  },
  tela_cheia: {
    grupo: 'aparelho', entrega: 4, titulo: 'Tela cheia',
    descricao: 'O navegador exige o toque no botão; o chat aponta o botão.',
    exemplos: [{ texto: 'tela cheia' }, { texto: 'maximizar o mapa' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['nenhum'],
  },
  // --- 5ª entrega
  reproducao: {
    grupo: 'mapa', entrega: 5, titulo: 'Reproduzir as últimas horas',
    descricao: 'Tocar, pausar ou ir a um instante ("às 14h", "há 3 horas") na reprodução do Monitor.',
    exemplos: [{ texto: 'reproduzir as últimas 24 h' }, { texto: 'pausar' }, { texto: 'como estava às 14h' }, { texto: 'voltar 3 horas' }],
    argumentos: [{ nome: 'acao', tipo: 'enum', obrigatorio: true, valores: ['tocar', 'pausar', 'ir'] }, { nome: 'hora', tipo: 'numero', obrigatorio: false }, { nome: 'minuto', tipo: 'numero', obrigatorio: false }, { nome: 'horasAtras', tipo: 'numero', obrigatorio: false }],
    mudaTela: true, precisaDoMapa: true, dados: ['monitor', 'serie'],
  },
  chuva_agora: {
    grupo: 'rio', entrega: 5, titulo: 'Onde está chovendo mais',
    descricao: 'Os pluviômetros com leitura recente, 1 h / 12 h / 24 h como a fonte publica.',
    exemplos: [{ texto: 'onde está chovendo mais?' }, { texto: 'chuva agora' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['aoVivo'],
  },
  barragens: {
    grupo: 'rio', entrega: 5, titulo: 'Como estão as barragens',
    descricao: 'O estado das comportas, como a fonte publica.',
    exemplos: [{ texto: 'como estão as barragens?' }, { texto: 'as comportas estão abertas?' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['barragens'],
  },
  mare: {
    grupo: 'rio', entrega: 5, titulo: 'Como está a maré',
    descricao: 'A tábua da Marinha para o porto de Itajaí: previsão astronômica, não medição.',
    exemplos: [{ texto: 'como está a maré?' }, { texto: 'qual a próxima maré alta?' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['mare'],
  },
  fonte_leitura: {
    grupo: 'leituras', entrega: 5, titulo: 'De onde vem essa leitura',
    descricao: 'Estação, hora e fontes cadastradas da leitura de uma cidade.',
    exemplos: [{ texto: 'de onde vem essa leitura?' }, { texto: 'fonte da leitura de Blumenau' }],
    argumentos: [cidade()], mudaTela: false, precisaDoMapa: false, dados: ['aoVivo', 'cadastro'],
  },
  // --- 6ª entrega
  quanto_falta: {
    grupo: 'leituras', entrega: 6, titulo: 'Quanto falta para a cota',
    descricao: 'A frase do cartão Agora: só com leitura de agora; nunca em Gaspar ("maior que"), Ascurra (C18) nem Itajaí (várias réguas).',
    exemplos: [{ texto: 'quanto falta para a cota em Blumenau?' }, { texto: 'quanto falta para o alerta?' }],
    argumentos: [cidade()], mudaTela: false, precisaDoMapa: false, dados: ['aoVivo', 'cadastro'],
    nunca: 'Fazer a conta com leitura velha ou em cidade sem frase de cota.',
  },
  tendencia: {
    grupo: 'leituras', entrega: 6, titulo: 'Está subindo ou baixando',
    descricao: 'A seta do cartão (D7): só quando o último ponto da série é a leitura mostrada e é de agora.',
    exemplos: [{ texto: 'Blumenau está subindo?' }, { texto: 'qual a tendência do rio em Gaspar?' }],
    argumentos: [cidade()], mudaTela: false, precisaDoMapa: false, dados: ['aoVivo', 'serie'],
  },
  maximo_24h: {
    grupo: 'leituras', entrega: 6, titulo: 'Máximo das últimas 24 h',
    descricao: 'Máximo e mínimo da série publicada de uma régua, com a hora de cada ponto.',
    exemplos: [{ texto: 'máximo das últimas 24 h em Blumenau' }, { texto: 'qual foi o pico de hoje em Rio do Sul?' }],
    argumentos: [cidade()], mudaTela: false, precisaDoMapa: false, dados: ['serie'],
  },
  panorama: {
    grupo: 'leituras', entrega: 6, titulo: 'Panorama da bacia',
    descricao: 'A faixa de cada cidade na régua dela (mesma faixa não é mesmo metro); a estadual à parte.',
    exemplos: [{ texto: 'quais cidades estão em alerta?' }, { texto: 'como está a bacia?' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['aoVivo'],
  },
  de_cima: {
    grupo: 'rio', entrega: 6, titulo: 'O que vem de cima',
    descricao: 'As cidades acima pela árvore, com a leitura de cada uma e o tempo de descida em intervalo. Ligação não é previsão.',
    exemplos: [{ texto: 'o que vem de cima para Blumenau?' }, { texto: 'como estão as cidades acima de Gaspar?' }],
    argumentos: [cidade()], mudaTela: false, precisaDoMapa: false, dados: ['aoVivo', 'transito', 'cadastro'],
  },
  // --- 7ª entrega
  chegada_itajai: {
    grupo: 'historico', entrega: 7, titulo: 'A chegada do pico em Itajaí e a maré',
    descricao: 'O "Hoje" do painel de Itajaí: se o pico de Blumenau passou, a janela de chegada (referência de estudo) e as marés dentro dela.',
    exemplos: [{ texto: 'o pico de Blumenau já passou?' }, { texto: 'a água chega na hora da maré alta?' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['serie', 'mare', 'transito'],
  },
  simular_chegada: {
    grupo: 'historico', entrega: 7, titulo: 'Simular a chegada com um horário de pico',
    descricao: 'A janela de chegada em Itajaí se o pico de Blumenau for na hora dita; o horário é da pessoa, nunca da última leitura.',
    exemplos: [{ texto: 'se o pico de Blumenau for às 22h' }, { texto: 'simular pico em Blumenau amanhã às 3h' }],
    argumentos: [{ nome: 'hora', tipo: 'numero', obrigatorio: true }, { nome: 'minuto', tipo: 'numero', obrigatorio: false }, { nome: 'dia', tipo: 'enum', obrigatorio: false, valores: ['hoje', 'amanha', 'ontem'] }],
    mudaTela: false, precisaDoMapa: false, dados: ['mare', 'transito'],
  },
  legenda: {
    grupo: 'mapa', entrega: 7, titulo: 'O que significa a cor',
    descricao: 'A legenda do mapa, de `data/faixas.json`: cor é faixa na régua da cidade, nunca metro.',
    exemplos: [{ texto: 'o que significa a cor laranja?' }, { texto: 'explicar as cores' }, { texto: 'o que são as ondas no mapa?' }],
    argumentos: [{ nome: 'tema', tipo: 'enum', obrigatorio: true, valores: ['cores', 'normal', 'monitoramento', 'atencao', 'alerta', 'inundacao', 'sem-dado', 'varias', 'azul', 'violeta', 'tracejado', 'ondas', 'seta', 'regua_mare'] }],
    mudaTela: false, precisaDoMapa: false, dados: ['nenhum'],
  },
  animacoes: {
    grupo: 'mapa', entrega: 7, titulo: 'Pausar ou retomar as animações',
    descricao: 'O botão de animações do Monitor.',
    exemplos: [{ texto: 'pausar as animações' }, { texto: 'retomar as animações' }],
    argumentos: [{ nome: 'acao', tipo: 'enum', obrigatorio: true, valores: ['pausar', 'retomar'] }], mudaTela: true, precisaDoMapa: true, dados: ['monitor'],
  },
  legenda_mapa: {
    grupo: 'mapa', entrega: 7, titulo: 'Abrir ou fechar a legenda',
    descricao: 'O botão de legenda do Monitor.',
    exemplos: [{ texto: 'abrir a legenda' }, { texto: 'fechar a legenda' }],
    argumentos: [{ nome: 'acao', tipo: 'enum', obrigatorio: true, valores: ['abrir', 'fechar'] }], mudaTela: true, precisaDoMapa: true, dados: ['monitor'],
  },
  // --- 8ª entrega
  atualizar: {
    grupo: 'site', entrega: 8, titulo: 'Atualizar as leituras',
    descricao: 'Busca de novo e diz se veio medição mais nova.',
    exemplos: [{ texto: 'atualizar as leituras' }, { texto: 'tem leitura nova?' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['aoVivo'],
  },
  oficial: {
    grupo: 'site', entrega: 8, titulo: 'Isso é oficial?',
    descricao: 'O aviso legal: não é alerta oficial; Defesa Civil, 199.',
    exemplos: [{ texto: 'isso é oficial?' }, { texto: 'ler o aviso legal' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['nenhum'],
  },
  instalar: {
    grupo: 'site', entrega: 8, titulo: 'Como instalar o aplicativo',
    descricao: 'O modo aplicativo (PWA), com o passo para o aparelho da pessoa.',
    exemplos: [{ texto: 'como instalar o aplicativo?' }, { texto: 'tem app?' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['aparelho'],
  },
  privacidade: {
    grupo: 'site', entrega: 8, titulo: 'O que o site guarda de mim',
    descricao: 'As preferências do aparelho e a contagem anônima, como estão.',
    exemplos: [{ texto: 'o que o site guarda de mim?' }, { texto: 'privacidade' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['preferencias'],
  },
  esquecer: {
    grupo: 'site', entrega: 8, titulo: 'Apagar minhas preferências',
    descricao: 'Pede confirmação ("sim, apagar") antes de apagar o que o aparelho guarda.',
    exemplos: [{ texto: 'apagar minhas preferências' }, { texto: 'sim apagar minhas preferências' }],
    argumentos: [{ nome: 'confirmado', tipo: 'booleano', obrigatorio: true }], mudaTela: false, precisaDoMapa: false, dados: ['preferencias'],
    esclarece: 'Sem o "sim", só pergunta.',
  },
  contagem: {
    grupo: 'site', entrega: 8, titulo: 'Contar ou não minhas perguntas',
    descricao: 'Liga ou desliga a contagem anônima do chat.',
    exemplos: [{ texto: 'não contar minhas perguntas' }, { texto: 'pode contar minhas perguntas' }],
    argumentos: [{ nome: 'permitir', tipo: 'booleano', obrigatorio: true }], mudaTela: false, precisaDoMapa: false, dados: ['preferencias'],
  },
  limpar_conversa: {
    grupo: 'site', entrega: 8, titulo: 'Limpar a conversa',
    descricao: 'Apaga as mensagens da conversa nesta tela.',
    exemplos: [{ texto: 'limpar a conversa' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['nenhum'],
  },
  emergencia: {
    grupo: 'site', entrega: 8, titulo: 'Telefone de emergência',
    descricao: '199 (Defesa Civil) e 193 (Bombeiros).',
    exemplos: [{ texto: 'telefone de emergência' }, { texto: 'quem ligar em emergência?' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['nenhum'],
  },
  // --- 11ª entrega
  glossario: {
    grupo: 'site', entrega: 11, titulo: 'O que é uma palavra do rio',
    descricao: 'Os verbetes do glossário (régua, cota, faixa, montante…); palavra fora dele segue para o motor.',
    exemplos: [{ texto: 'o que é cota?' }, { texto: 'qual a diferença entre enchente e alagamento?' }],
    argumentos: [{ nome: 'termos', tipo: 'termos', obrigatorio: true }], mudaTela: false, precisaDoMapa: false, dados: ['nenhum'],
  },
  termos: {
    grupo: 'site', entrega: 11, titulo: 'Que palavras você explica',
    descricao: 'A lista dos verbetes.',
    exemplos: [{ texto: 'que palavras você explica?' }, { texto: 'glossário' }],
    argumentos: [], mudaTela: false, precisaDoMapa: false, dados: ['nenhum'],
  },
  voz: {
    grupo: 'aparelho', entrega: 11, titulo: 'Ler em voz alta',
    descricao: 'Lê a última resposta pela voz do navegador, ou para.',
    exemplos: [{ texto: 'ler em voz alta' }, { texto: 'parar de ler' }],
    argumentos: [{ nome: 'acao', tipo: 'enum', obrigatorio: true, valores: ['ler', 'parar'] }], mudaTela: false, precisaDoMapa: false, dados: ['aparelho'],
  },
  // --- 12ª entrega
  enquadrar: {
    grupo: 'navegacao', entrega: 12, titulo: 'Enquadrar um rio inteiro ou as barragens',
    descricao: 'As cidades com régua do rio, ou os marcadores das barragens, no Monitor. Fora do Monitor, "mostrar o Itajaí-Açu" continua abrindo a página do rio.',
    exemplos: [{ texto: 'ver o Itajaí-Mirim no mapa' }, { texto: 'zoom nas barragens' }, { texto: 'onde ficam as barragens?' }, { texto: 'mostrar o Itajaí-Mirim', contexto: noMonitor }],
    argumentos: [{ nome: 'alvo', tipo: 'enum', obrigatorio: true, valores: ['rio', 'barragens'] }, { nome: 'rioId', tipo: 'rioId', obrigatorio: false }],
    mudaTela: true, precisaDoMapa: true, dados: ['monitor', 'cadastro'],
  },
  fechar_painel: {
    grupo: 'mapa', entrega: 12, titulo: 'Fechar o painel da cidade',
    descricao: 'Fecha o painel; o mapa fica onde está.',
    exemplos: [{ texto: 'fechar o painel' }],
    argumentos: [], mudaTela: true, precisaDoMapa: true, dados: ['monitor'],
  },
  menu_cidades: {
    grupo: 'mapa', entrega: 12, titulo: 'Abrir ou fechar o menu de cidades',
    descricao: 'O botão "Cidades ▾" do Monitor.',
    exemplos: [{ texto: 'abrir o menu de cidades' }, { texto: 'fechar o menu' }],
    argumentos: [{ nome: 'acao', tipo: 'enum', obrigatorio: true, valores: ['abrir', 'fechar'] }], mudaTela: true, precisaDoMapa: true, dados: ['monitor'],
  },
  // --- 13ª entrega
  varias_cidades: {
    grupo: 'leituras', entrega: 13, titulo: 'Várias cidades de uma vez',
    descricao: 'Uma linha por cidade, cada uma na régua dela; as seguidas no aparelho; o resumo de todas para copiar.',
    exemplos: [{ texto: 'como estão Blumenau e Gaspar?' }, { texto: 'como estão as minhas cidades?' }, { texto: 'copiar o resumo das minhas cidades' }],
    argumentos: [{ nome: 'cidadeIds', tipo: 'cidadeIds', obrigatorio: false }, { nome: 'seguidas', tipo: 'booleano', obrigatorio: false }, { nome: 'copiar', tipo: 'booleano', obrigatorio: false }],
    mudaTela: false, precisaDoMapa: false, dados: ['aoVivo', 'preferencias'],
    nunca: 'Comparar metros entre cidades; responder com uma cidade a menos quando uma da lista está fora do cadastro (18ª: diz qual não está).',
  },
  // --- 14ª entrega
  linha_do_tempo: {
    grupo: 'leituras', entrega: 14, titulo: 'A linha do tempo da cheia de agora',
    descricao: 'Quando passou da cota, há quanto tempo está na faixa, quando começou a subir, quanto subiu em N horas — pela série de 48 h de uma régua, com a hora da medição e o passo da série.',
    exemplos: [{ texto: 'quando Blumenau passou da cota de alerta?' }, { texto: 'há quanto tempo Blumenau está em alerta?' }, { texto: 'quando o rio começou a subir em Blumenau?' }, { texto: 'quanto Blumenau subiu nas últimas 6 horas?' }],
    argumentos: [{ nome: 'pergunta', tipo: 'enum', obrigatorio: true, valores: ['cruzou_cota', 'ha_quanto_tempo', 'comecou_a_subir', 'variacao'] }, cidade(), { nome: 'cota', tipo: 'enum', obrigatorio: false, valores: ['monitoramento', 'atencao', 'alerta', 'inundacao', 'emergencia'] }, { nome: 'horas', tipo: 'numero', obrigatorio: false }],
    mudaTela: false, precisaDoMapa: false, dados: ['serie', 'cadastro'],
    nunca: 'Inventar hora entre duas medições; perguntas de cota em Gaspar, Ascurra e Itajaí.',
  },
  // --- 15ª entrega
  captados: {
    grupo: 'historico', entrega: 15, titulo: 'As cheias que o site já captou',
    descricao: 'Lista, última, maior, quantas e por período, de `data/eventos-captados.json`: maior leitura captada, nunca "pico"; "registrado" só com registro em enchentes.json.',
    exemplos: [{ texto: 'quais cheias o site captou?' }, { texto: 'qual foi a última cheia em Blumenau?' }, { texto: 'como foi a cheia de setembro?' }, { texto: 'quantas vezes Blumenau passou da cota de alerta desde que o site acompanha?' }],
    argumentos: [{ nome: 'pergunta', tipo: 'enum', obrigatorio: true, valores: ['lista', 'ultima', 'maior', 'quantas', 'periodo'] }, cidade(), { nome: 'cota', tipo: 'enum', obrigatorio: false, valores: ['monitoramento', 'atencao', 'alerta', 'inundacao', 'emergencia'] }, { nome: 'mes', tipo: 'mes', obrigatorio: false }, { nome: 'ano', tipo: 'ano', obrigatorio: false }, { nome: 'dia', tipo: 'dia', obrigatorio: false }],
    mudaTela: false, precisaDoMapa: false, dados: ['captados', 'cadastro'],
  },
  // --- 16ª entrega
  ruas_pela_cota: {
    grupo: 'ruas', entrega: 16, titulo: 'As ruas pela cota, cidade inteira',
    descricao: 'Quais pontos de rua alagam com um nível, quais o rio já alcançou (só com leitura fresca), as próximas e as mais baixas. Tabela, não observação nem previsão.',
    exemplos: [{ texto: 'quais ruas alagam com 8 m em Blumenau?' }, { texto: 'quais ruas o rio já alcançou em Blumenau?' }, { texto: 'quais são as próximas ruas em Blumenau?' }, { texto: 'quais ruas alagam primeiro em Gaspar?' }],
    argumentos: [{ nome: 'pergunta', tipo: 'enum', obrigatorio: true, valores: ['nivel', 'agora', 'proximas', 'primeiras'] }, cidade(), { nome: 'nivelM', tipo: 'numero', obrigatorio: false }, { nome: 'subirM', tipo: 'numero', obrigatorio: false }],
    mudaTela: false, precisaDoMapa: false, dados: ['cotasRuas', 'aoVivo', 'cadastro'],
    nunca: 'Afirmar "já alagou" com leitura velha, cidade de várias réguas ou nível dito.',
    esclarece: 'Nível impossível ("30 m", "0 m") pergunta um nível possível (18ª).',
  },
}

/** Os exemplos que precisam do Monitor de Itajaí para pedir esclarecimento (não são capacidade: são o contrato). */
export const EXEMPLOS_DE_ESCLARECIMENTO: Exemplo[] = [
  { texto: 'aproximar a régua', contexto: emItajai },
  { texto: 'mostrar Blumenal' },
  { texto: 'zoom na régua murta' },
  { texto: 'mostre Blumenau e apague o banco de dados' },
]

export const TIPOS: Passo['tipo'][] = Object.keys(CAPACIDADES) as Passo['tipo'][]

export function capacidadeDe(tipo: Passo['tipo']): Capacidade {
  return CAPACIDADES[tipo]
}

export const GRUPOS: Record<Grupo, string> = {
  navegacao: 'Navegação: abrir telas e enquadrar o mapa',
  mapa: 'O mapa: fundo, camadas, legenda, animações, reprodução',
  leituras: 'O rio agora: níveis, faixas, tendência, fontes',
  rio: 'A bacia: montante, confluência, traçado, barragens, maré, chuva',
  historico: 'O que o site já captou e a foz',
  ruas: 'Cotas de rua e manchas',
  aparelho: 'O aparelho: localização, preferências, letra, voz, tela cheia',
  site: 'O site: atualizar, oficial, instalar, privacidade, conversa, emergência, ajuda, glossário',
}

/**
 * O esquema de intenções para o classificador (PR 2 do handoff): só os identificadores e os argumentos declarados
 * aqui; nenhum texto livre vira passo sem passar pela validação contra o cadastro.
 */
export function esquemaDoClassificador(): { intencoes: string[]; argumentos: Record<string, Argumento[]> } {
  return {
    intencoes: [...TIPOS, 'nao_sei'],
    argumentos: Object.fromEntries(TIPOS.map((t) => [t, CAPACIDADES[t].argumentos])),
  }
}

/** A documentação do catálogo, em Markdown (`docs/CHAT-CAPACIDADES.md`, gerada por `npm run avaliar`). */
export function textoDoCatalogo(): string {
  const linhas = [
    '# Capacidades do chat — catálogo único',
    '',
    'Gerado de `web/src/comandos/capacidades.ts` por `npm run avaliar` (não editar à mão). Uma ficha por tipo de passo',
    'do chat: o que faz, exemplos que o leitor entende hoje, argumentos e se muda a tela. Regra do handoff de',
    'qualidade (PR 1): o catálogo de comandos não substitui o catálogo de cidades e réguas; são conceitos diferentes.',
    '',
    `${TIPOS.length} capacidades, em ${Object.keys(GRUPOS).length} grupos.`,
    '',
  ]
  for (const [grupo, nome] of Object.entries(GRUPOS) as [Grupo, string][]) {
    const doGrupo = TIPOS.filter((t) => CAPACIDADES[t].grupo === grupo).sort((a, b) => CAPACIDADES[a].entrega - CAPACIDADES[b].entrega || a.localeCompare(b))
    linhas.push(`## ${nome}`, '')
    linhas.push('| Passo | Entrega | O que faz | Exemplos | Argumentos | Muda a tela |', '|---|---|---|---|---|---|')
    for (const t of doGrupo) {
      const c = CAPACIDADES[t]
      const args = c.argumentos.map((a) => `\`${a.nome}\`${a.obrigatorio ? '' : '?'}${a.valores ? ` (${a.valores.join(' · ')})` : ''}`).join(', ') || '—'
      const ex = c.exemplos.map((e) => `"${e.texto}"${e.contexto?.naMonitor ? ' (no Monitor)' : ''}`).join('; ')
      const extras = [c.esclarece ? `Esclarece: ${c.esclarece}` : '', c.nunca ? `Nunca: ${c.nunca}` : ''].filter(Boolean).join(' ')
      linhas.push(`| \`${t}\` — ${c.titulo} | ${c.entrega}ª | ${c.descricao}${extras ? ` ${extras}` : ''} | ${ex} | ${args} | ${c.mudaTela ? 'sim' : 'não'}${c.precisaDoMapa ? ' (abre o Monitor)' : ''} |`)
    }
    linhas.push('')
  }
  linhas.push('## O contrato de esclarecimento', '', 'Pedidos que o chat NÃO executa e pergunta antes:', '')
  for (const e of EXEMPLOS_DE_ESCLARECIMENTO) linhas.push(`- "${e.texto}"${e.contexto?.cidadeAtual ? ` (no Monitor de ${e.contexto.cidadeAtual})` : ''}`)
  linhas.push('')
  return linhas.join('\n')
}
