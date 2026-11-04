/**
 * 20ª entrega: o texto do chat para os avisos meteorológicos da Defesa Civil de SC. A mesma leitura da tela
 * (`dados/avisosDcsc.ts`): por região, como a Defesa Civil escreve; nunca "para a sua cidade"; nunca faixa do rio.
 */
import { estadoDosAvisos, linhaDoAviso, textoDosAvisos, type AvisosDcsc } from '../dados/avisosDcsc'

export const FONTE_PADRAO_DCSC = 'Defesa Civil de Santa Catarina (www.defesacivil.sc.gov.br)'

export function textoAvisosDcsc(d: AvisosDcsc | null, agora: Date): string {
  const e = estadoDosAvisos(d, agora)
  const { titulo, detalhe } = textoDosAvisos(e)
  const linhas = [`${titulo} ${detalhe}`]
  if (e.tipo === 'avisos') {
    for (const a of e.recentes) linhas.push(`• ${a.titulo}\n  ${linhaDoAviso(a)}${a.link ? `\n  ${a.link}` : ''}`)
  }
  linhas.push(`Fonte: ${d && e.tipo !== 'indisponivel' ? d.fonte : FONTE_PADRAO_DCSC}.`)
  linhas.push('É aviso para a região que a Defesa Civil nomeia, não para uma cidade, e não é a faixa do rio (a cor do mapa continua vindo só da régua). Não é alerta deste site: em emergência, ligue 199.')
  return linhas.join('\n')
}
