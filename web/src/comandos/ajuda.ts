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
        '• explicar a tela: "o que estou vendo?", "por que essa régua está cinza?", "essa coordenada foi confirmada?".',
        'E perguntas: "como está Blumenau?", "maior cheia de Rio do Sul", "quanto tempo a cheia leva de Rio do Sul até Blumenau?".',
        'Tela cheia é pelo botão "Tela cheia": o navegador só abre com o seu toque.',
      ]
    : [
        'Posso abrir telas e responder perguntas:',
        `• "mostrar ${aqui}" abre o mapa da cidade; "abrir o monitor" abre a bacia;`,
        `• "histórico de ${aqui}", "minha rua em ${aqui}", "abrir o mapa das manchas";`,
        '• "zoom na régua DC-05" abre Itajaí na régua;',
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
