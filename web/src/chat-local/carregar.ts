/**
 * Dados do chat local.
 *
 * O que o site já carrega no pacote principal (`dados/carregar.ts`: enchentes,
 * trânsito, estações — já validados) é REAPROVEITADO, não baixado de novo. Os
 * quatro JSONs que só o chat usa vêm por import dinâmico: o Vite os separa em
 * arquivos próprios, baixados quando a caixa do chat entra na tela. As cotas
 * diárias da ANA (~1,2 MB) vêm por último, em segundo plano; até chegarem o
 * motor responde "carregando".
 *
 * Os quatro moram em `data/brutos/`, onde já estavam quando o pacote do chat
 * chegou (22/09/2026): mesma versão, um arquivo só — ver docs/CHAT-LOCAL.md.
 */
import { estacoes, eventos, trechos } from '../dados/carregar'
import type { Dados } from './motor'

export async function carregarBase(): Promise<Dados> {
  const [acu, mirim, chuva, picos] = await Promise.all([
    import('@dados/brutos/atlas-desastres-recorte-itajai-acu-2026-09-21.json'),
    import('@dados/brutos/atlas-desastres-recorte-itajai-mirim-2026-09-21.json'),
    import('@dados/brutos/inmet-chuva-eventos-atlas-2026-09-22.json'),
    import('@dados/brutos/hidroweb-mirim-2026-09-22/picos_itajai_mirim_1997_2021.json'),
  ])
  return {
    enchentes: { eventos: eventos as unknown as Dados['enchentes']['eventos'] },
    transito: { trechos: trechos as unknown as Dados['transito']['trechos'] },
    estacoes: estacoes as unknown as Dados['estacoes'],
    atlas: {
      'itajai-acu': acu.default as unknown as Dados['atlas'][string],
      'itajai-mirim': mirim.default as unknown as Dados['atlas'][string],
    },
    chuvaEventos: chuva.default as unknown as Dados['chuvaEventos'],
    picosMirim: picos.default as unknown as Dados['picosMirim'],
  }
}

export async function carregarCotasAna(): Promise<NonNullable<Dados['cotasAna']>> {
  const mod = await import('@dados/brutos/hidroweb-mirim-2026-09-22/cotas_itajai_mirim_diaria.json')
  return mod.default as unknown as NonNullable<Dados['cotasAna']>
}
