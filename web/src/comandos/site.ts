/**
 * 8ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): o site e os seus dados. Funções puras:
 *
 * - "atualizar as leituras": o que a busca nova trouxe, pela hora da COLETA e da medição mais nova;
 * - "isso é oficial?": o aviso de toda tela (`AvisoLegal`), em texto;
 * - "como instalar o aplicativo?": o caminho de cada aparelho (o navegador só instala com o toque da pessoa);
 * - "o que o site guarda de mim?": as preferências deste aparelho, lidas na hora, e o que NÃO é guardado;
 * - números de emergência: os da faixa de toda tela (199 e 193), nada além.
 */
import { diaDeBrasilia, horaDeBrasilia } from '../logica/agora'
import { idadeMin, textoIdade } from '../logica/tempoReal'

const quando = (d: Date, agora: Date) => `${horaDeBrasilia(d)} de ${diaDeBrasilia(d)} (${textoIdade(idadeMin(d, agora))})`

export function textoAtualizacao(args: {
  pedido: boolean
  coletaAntes: Date | null
  coletaDepois: Date | null
  medicaoMaisNova: Date | null
  agora: Date
}): string {
  const { agora } = args
  if (!args.pedido) {
    return 'Acabei de buscar há menos de 30 segundos. O site também busca sozinho a cada 5 minutos enquanto a página fica aberta.'
  }
  const linhas: string[] = []
  if (!args.coletaDepois) {
    linhas.push('Busquei de novo, mas o arquivo de leituras não respondeu. As telas continuam com o que já tinham, cada número com a hora dele.')
  } else if (args.coletaAntes && args.coletaDepois.getTime() === args.coletaAntes.getTime()) {
    linhas.push(`Busquei de novo: a coleta mais recente ainda é a de ${quando(args.coletaDepois, agora)}. As fontes não publicaram leitura nova desde então; a coleta roda no servidor, no ritmo dela.`)
  } else {
    linhas.push(`Busquei de novo: chegou a coleta de ${quando(args.coletaDepois, agora)}, e as telas abertas já mostram os números dela.`)
  }
  if (args.medicaoMaisNova) linhas.push(`A medição mais nova entre todas as réguas é de ${quando(args.medicaoMaisNova, agora)}. Cada régua tem a hora dela: leitura velha continua marcada como velha.`)
  linhas.push('Em emergência, ligue 199.')
  return linhas.join('\n')
}

export const TEXTO_OFICIAL = [
  'Não. Este site não é sistema oficial de alerta. Ele mostra medições observadas e referências históricas e não substitui o AlertaBlu, a Defesa Civil de SC nem a Defesa Civil do seu município.',
  'Cada cidade tem a sua própria régua, com zero em altura diferente: 8 m em Blumenau e 8 m em Brusque não significam a mesma coisa.',
  'Camadas históricas são referências de cheias passadas; não confirmam alagamento atual.',
  'Em emergência, ligue 199 (Defesa Civil) ou 193 (Bombeiros) e siga os comunicados da Defesa Civil.',
].join('\n')

export const TEXTO_EMERGENCIA =
  'Em emergência: 199 (Defesa Civil) ou 193 (Bombeiros). São os números que este site mostra em toda tela. O site não é sistema oficial de alerta e não tem os telefones das Defesas Civis municipais cadastrados; siga os comunicados delas.'

export function textoInstalar(a: { instalado: boolean; iphone: boolean; pode: boolean }): string {
  if (a.instalado) return 'O site já está aberto como aplicativo neste aparelho.'
  const linhas: string[] = []
  if (a.iphone) {
    linhas.push('No iPhone: no Safari, toque em Compartilhar (o quadrado com a seta) e depois em "Adicionar à Tela de Início".')
  } else if (a.pode) {
    linhas.push('Este navegador pode instalar o site: toque no botão "Instalar" no Início. O navegador só instala com o seu toque, por isso o chat não instala sozinho.')
  } else {
    linhas.push('No Android, pelo menu do navegador (os três pontos): "Instalar app" ou "Adicionar à tela inicial". No computador, o ícone de instalar na barra de endereço, quando o navegador oferece.')
  }
  linhas.push('Como aplicativo, sem internet ele mostra a última cópia guardada, sempre com a hora da medição; um número guardado nunca aparece como se fosse de agora.')
  linhas.push('O acesso continua restrito ao e-mail cadastrado.')
  return linhas.join('\n')
}

export function textoPrivacidade(p: {
  memoria: boolean
  seguidas: string[]
  letraGrande: boolean
  avisoLido: boolean
  contagem: boolean
}): string {
  const linhas: string[] = []
  if (!p.memoria) {
    linhas.push('Este navegador não deixa o site guardar nada (janela anônima ou armazenamento bloqueado): nenhuma preferência fica no aparelho.')
  } else {
    linhas.push('Neste aparelho, e só nele, o site guarda:')
    linhas.push(`• cidades: ${p.seguidas.length ? `${p.seguidas[0]} (a sua)${p.seguidas.length > 1 ? `, e segue ${p.seguidas.slice(1).join(', ')}` : ''}` : 'nenhuma escolhida'};`)
    linhas.push(`• letra: ${p.letraGrande ? 'maior' : 'normal'};`)
    linhas.push(`• aviso legal: ${p.avisoLido ? 'lido' : 'ainda não marcado como lido'};`)
    linhas.push(`• contagem das perguntas que o chat não entende: ${p.contagem ? 'permitida' : 'desligada'} (é só um contador anônimo do dia, e só funciona se o site estiver contando; nunca guarda o que você digitou).`)
  }
  linhas.push('Não guarda: a sua localização (só fica na tela até fechar), esta conversa (some ao fechar a aba) nem o seu nome ou telefone.')
  linhas.push('Para apagar tudo isso, peça "apagar minhas preferências". Para parar a contagem, "não contar minhas perguntas".')
  return linhas.join('\n')
}

export const TEXTO_CONFIRMAR_ESQUECER =
  'Isso apaga deste aparelho a sua cidade, as cidades seguidas, a letra maior, a marca de aviso lido (o aviso volta na próxima visita) e a escolha sobre a contagem do chat. Nada fica guardado em outro lugar. Para confirmar, peça "sim, apagar minhas preferências".'
