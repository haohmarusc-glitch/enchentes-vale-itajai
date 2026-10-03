/**
 * CADA RÉGUA DE UMA CIDADE, AGORA — para a cidade que tem várias (Itajaí).
 *
 * Pedido do Jefferson (03/10/2026): "Itajaí tem que mostrar o Itajaí-Mirim
 * também na cidade, e as réguas têm que ser representadas como a imagem" — a
 * imagem é o cartão "Agora" de Blumenau: faixa, número, idade e régua colorida.
 *
 * Antes, a cidade escolhida pelo Açu mostrava só as cotas das três réguas do
 * Açu, sem número; o Mirim e os ribeirões, que alagam bairro, ficavam de fora.
 * Aqui entram TODAS, em qualquer curso, cada uma com a SUA faixa calculada nas
 * SUAS cotas. Continua sem existir "o nível de Itajaí": nada é somado,
 * comparado ou eleito — a cor de uma régua sai só das cotas dela.
 */
import type { LeituraAoVivo } from '../dados/tempoReal'
import { reguaDe } from '../dados/tempoReal'
import { CHAVES_QUE_PINTAM } from './cotasOperacionais'
import type { ReguaComCota } from './reguas'
import { cotaAlcancadaEntre, frescorDaCidade, idadeMin, proximaCotaEntre, type Faixa } from './tempoReal'

export interface ReguaAgora {
  regua: ReguaComCota
  /** A leitura mais recente desta régua (primária ou resgate), ou null. */
  leitura: LeituraAoVivo | null
  faixa: Faixa
  /** Minutos desde a medição; null sem leitura ou sem horário. */
  idade: number | null
  velha: boolean
  /** A próxima cota acima do nível, com quanto falta — só com leitura de agora. */
  proxima: { chave: string; valor: number; faltam: number } | null
}

/**
 * A faixa de UMA régua, nas cotas dela. Sem leitura, sem horário ou com
 * leitura velha: `sem-dado` (nunca verde — verde se lê como seguro).
 */
export function faixaDaRegua(
  regua: ReguaComCota,
  leitura: LeituraAoVivo | null,
  cidadeId: string,
  agora: Date,
): Faixa {
  const quePintam = regua.cotas.filter(([chave]) => CHAVES_QUE_PINTAM.has(chave))
  if (quePintam.length === 0 || !leitura || !leitura.medidoEm) return 'sem-dado'
  if (frescorDaCidade(idadeMin(leitura.medidoEm, agora), cidadeId) === 'velha') return 'sem-dado'
  const cota = cotaAlcancadaEntre(quePintam, leitura.nivel_m)
  if (cota === null) return 'normal'
  if (cota.chave === 'monitoramento' || cota.chave === 'atencao' || cota.chave === 'alerta') return cota.chave
  return cota.chave === 'inundacao' ? 'inundacao' : 'emergencia'
}

/**
 * Cada régua com a leitura DELA, pelo título exato (nunca por prefixo de
 * código). Resgate e primária da mesma régua colam pela identidade
 * (`reguaDe`), e vale a mais recente. A ordem é a das réguas recebidas — quem
 * chama já as entrega agrupadas por curso, da nascente para o mar.
 */
export function reguasAgora(
  reguas: ReguaComCota[],
  leituras: LeituraAoVivo[],
  cidadeId: string,
  agora: Date,
): ReguaAgora[] {
  const maisRecente = new Map<string, LeituraAoVivo>()
  for (const l of leituras) {
    const chave = reguaDe(l)
    const atual = maisRecente.get(chave)
    const t = l.medidoEm?.getTime() ?? -Infinity
    if (!atual || t > (atual.medidoEm?.getTime() ?? -Infinity)) maisRecente.set(chave, l)
  }
  return reguas.map((regua) => {
    const leitura = maisRecente.get(regua.titulo) ?? null
    const idade = leitura?.medidoEm ? idadeMin(leitura.medidoEm, agora) : null
    const velha = idade === null || frescorDaCidade(idade, cidadeId) === 'velha'
    const prox = leitura && !velha ? proximaCotaEntre(regua.cotas, leitura.nivel_m) : null
    return {
      regua,
      leitura,
      faixa: faixaDaRegua(regua, leitura, cidadeId, agora),
      idade,
      velha,
      proxima: prox && leitura ? { ...prox, faltam: prox.valor - leitura.nivel_m } : null,
    }
  })
}
