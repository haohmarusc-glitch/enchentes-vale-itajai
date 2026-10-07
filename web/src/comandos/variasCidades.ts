/**
 * 13ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): várias cidades de uma vez.
 *
 * Quem tem família em Blumenau, Gaspar e Itajaí perguntava cidade por cidade. Aqui, uma resposta só, com as
 * mesmas regras de cada cidade sozinha:
 *  - a linha de cada cidade é a de "o que vem de cima" (`leituraCurta`): número NA RÉGUA DELA, faixa com o nome
 *    da Defesa Civil, seta só quando a série casa com a leitura (D7), hora e idade; leitura velha não aparece
 *    como de agora; a estadual só com "zero próprio"; Itajaí não tem um número só;
 *  - o texto para copiar junta os resumos de cada cidade (D4: sem endereço do site, com a hora, sem ordem de
 *    ação, só leitura que não é velha), com um rodapé só.
 * Metros de cidades diferentes nunca se comparam, e a resposta diz isso.
 */
import type { CidadeAgora } from './rioAgora'
import { leituraCurta } from './rioAgora'

export const MAX_CIDADES_JUNTAS = 6

export function textoVariasCidades(itens: CidadeAgora[], agora: Date): string {
  return [
    'Agora, cada cidade na régua dela (não compare os metros de uma cidade com os de outra):',
    ...itens.map(({ cidade, estado }) => `• ${cidade.nome}: ${leituraCurta(cidade, estado, agora)}`),
    'É a última medição, não previsão. Siga a Defesa Civil de cada cidade; em emergência, ligue 199.',
  ].join('\n')
}

/** O texto para copiar: o resumo de cada cidade (já sem o rodapé dele) e um rodapé só. */
export function textoParaCopiarVarias(resumos: { nome: string; texto: string | null | 'varias' }[]): string | null {
  if (!resumos.some((r) => typeof r.texto === 'string')) return null
  const blocos = resumos.map((r) =>
    r.texto === 'varias'
      ? `${r.nome}: várias réguas, cada uma com o seu zero; não há um número só para a cidade.`
      : r.texto
        ? r.texto.split('\n\n')[0]!
        : `${r.nome}: sem leitura de agora.`,
  )
  return [...blocos, 'Não é alerta oficial. Em emergência, ligue 199. Siga a Defesa Civil.'].join('\n\n')
}
