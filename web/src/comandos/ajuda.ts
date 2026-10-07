/**
 * "O que posso pedir?" — gerado do que funciona NA TELA ABERTA (docs/CHAT-GLOBAL-COMANDOS.md).
 * No Monitor, os comandos do mapa; fora dele, a navegação e as perguntas. Em Itajaí, a régua por código.
 */
import type { Contexto } from './tipos'
import type { Saida } from './executar'

export function textoDeAjuda(ctx: Contexto, nomeCidade: string | null): Saida {
  const aqui = nomeCidade ?? 'Blumenau'
  const linhas = ctx.naMonitor
    ? [
        'No mapa, posso:',
        `• abrir uma cidade: "mostrar ${aqui === 'Blumenau' ? 'Gaspar' : 'Blumenau'}";`,
        ctx.cidadeAtual === 'itajai' ? '• escolher uma régua: "zoom na régua DC-05" ou "todas as réguas";' : '• enquadrar a régua da cidade: "aproximar a régua";',
        '• "aproximar", "afastar", "ver a bacia toda";',
        '• trocar o fundo: "satélite", "mapa de ruas", "fundo escuro";',
        '• camadas de cheia: "ligar as manchas", "mancha de 2008", "desligar as camadas";',
        '• "voltar ao mapa de antes" e "ir para a leitura mais recente";',
        '• explicar a tela: "o que estou vendo?", "por que essa régua está cinza?", "essa coordenada foi confirmada?";',
        '• "mostrar só as réguas sem leitura" e "limpar filtros"; "ver a confluência do Benedito";',
        '• "quais leituras estão atrasadas?", "o que mudou na última hora?", "comparar as réguas de Itajaí";',
        '• "o que fica a montante daqui?", "afluentes deste trecho", "de onde vem esse traçado?";',
        '• "copiar resumo desta cidade", "copiar link desta visualização" (o chat prepara; quem envia é você);',
        '• rua: "mostrar a rua X em Gaspar" (pontos de cota), "mostrar a avenida Y em Itajaí" e "manchas na rua Y" (traçado sobre as manchas), "remover destaque";',
        '• "usar minha localização" (a régua mais perto; nada é guardado), "relatar problema nesta régua", "minha cidade é X", "seguir X";',
        '• "reproduzir as últimas 24 h", "pausar", "como estava às 14h", "voltar 3 horas";',
        '• "onde está chovendo mais?", "como estão as barragens?", "como está a maré?", "de onde vem essa leitura?";',
        '• o rio agora: "quanto falta para a cota?", "está subindo ou descendo?", "máximo das últimas 24 h", "quais cidades estão em alerta?", "o que vem de cima?", "mostrar só as cidades em alerta";',
        '• a foz: "o pico de Blumenau já passou?", "se o pico de Blumenau for às 22h"; o mapa: "o que significa a cor laranja?", "explicar as cores", "pausar as animações", "abrir a legenda";',
        '• o site: "atualizar as leituras", "isso é oficial?", "como instalar o aplicativo?", "o que o site guarda de mim?", "apagar minhas preferências", "limpar a conversa", "telefone de emergência";',
        '• palavras do rio: "o que é cota?", "o que é jusante?", "qual a diferença entre enchente e alagamento?"; "ler em voz alta" e "parar de ler";',
        '• o mapa, peça por peça: "ver o Itajaí-Mirim no mapa", "zoom nas barragens", "fechar o painel", "abrir o menu de cidades";',
        '• várias cidades: "como estão Blumenau e Gaspar?", "como estão as minhas cidades?", "copiar o resumo das minhas cidades";',
        '• a linha do tempo da cheia: "quando Blumenau passou da cota de alerta?", "há quanto tempo Blumenau está em alerta?", "quando o rio começou a subir em Blumenau?", "quanto Blumenau subiu nas últimas 6 horas?".',
        'E perguntas: "como está Blumenau?", "maior cheia de Rio do Sul", "quanto tempo a cheia leva de Rio do Sul até Blumenau?".',
        'Tela cheia é pelo botão "Tela cheia": o navegador só abre com o seu toque.',
      ]
    : [
        'Posso abrir telas e responder perguntas:',
        `• "mostrar ${aqui}" abre o mapa da cidade; "abrir o monitor" abre a bacia;`,
        `• "histórico de ${aqui}", "minha rua em ${aqui}", "abrir o mapa das manchas";`,
        '• "zoom na régua DC-05" abre Itajaí na régua;',
        `• "gráfico de ${aqui}", "o que mudou na última hora em ${aqui}?", "quais leituras estão atrasadas?";`,
        `• "o que fica a montante de ${aqui}?", "afluentes de ${aqui}", "comparar as réguas de Itajaí";`,
        `• "copiar resumo de ${aqui}" e "copiar link desta página" (o chat prepara; quem envia é você);`,
        '• "mostrar a avenida 7 de Setembro em Itajaí", "manchas na rua X", "mostrar a rua Y em Gaspar";',
        `• "usar minha localização", "minha cidade é ${aqui}", "seguir Gaspar", "quais cidades eu sigo?", "letra maior";`,
        '• "relatar problema nesta página" prepara um texto para copiar (o site não tem canal de relato);',
        `• "onde está chovendo mais?", "como estão as barragens?", "como está a maré?", "de onde vem a leitura de ${aqui}?";`,
        `• o rio agora: "quanto falta para a cota em ${aqui}?", "${aqui} está subindo?", "máximo das últimas 24 h em ${aqui}", "quais cidades estão em alerta?", "o que vem de cima para ${aqui}?";`,
        '• a foz: "o pico de Blumenau já passou?", "se o pico de Blumenau for às 22h"; as cores: "o que significa a cor laranja?", "explicar as cores";',
        '• o site: "atualizar as leituras", "isso é oficial?", "como instalar o aplicativo?", "o que o site guarda de mim?", "apagar minhas preferências", "limpar a conversa";',
        '• palavras do rio: "o que é cota?", "o que é jusante?", "qual a diferença entre enchente e alagamento?"; "ler em voz alta";',
        '• várias cidades: "como estão Blumenau e Gaspar?", "como estão as minhas cidades?", "copiar o resumo das minhas cidades";',
        `• a linha do tempo da cheia: "quando ${aqui} passou da cota de alerta?", "há quanto tempo ${aqui} está em alerta?", "quando o rio começou a subir em ${aqui}?", "quanto ${aqui} subiu nas últimas 6 horas?";`,
        '• perguntas: "como está Blumenau?", "as 5 maiores cheias de Brusque", "cheias de 2008".',
      ]
  const sugestoes = ctx.naMonitor
    ? [ctx.cidadeAtual === 'itajai' ? 'zoom na régua DC-01' : 'aproximar a régua', 'satélite', 'o que estou vendo?']
    : [`como está ${aqui}?`, `mostrar ${aqui}`, 'abrir o monitor']
  return {
    texto: `${linhas.join('\n')}\nNão é alerta: em emergência, ligue 199.`,
    sugestoes,
  }
}
