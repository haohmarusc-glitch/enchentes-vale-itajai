/**
 * Resumo da chuva de uma cidade a partir dos pluviômetros que ela tem.
 *
 * Por que a chuva pode ser agregada e o nível não: milímetro é milímetro em
 * qualquer ponto. Duas réguas de rio na mesma cidade têm zeros diferentes e
 * não se comparam — por isso `leituraDaCidade` desiste quando há mais de uma.
 * Com pluviômetro é o contrário: cinco aparelhos em Itajaí medem a mesma
 * grandeza, e o que eles mostram junto (19 mm num ponto, 40 mm em outro) é
 * informação de verdade sobre onde a chuva caiu.
 *
 * O que se mostra é o MAIOR valor, não a média. Numa bacia, o que enche o rio
 * é a chuva onde ela caiu, e a média entre um ponto encharcado e um seco
 * inventa um meio-termo que não aconteceu em lugar nenhum. Quando os
 * pluviômetros discordam, a faixa inteira aparece.
 *
 * Leitura marcada como incoerente pela coleta é DESCARTADA aqui e contada à
 * parte: a fonte publica zeros que significam "sem dado", e mostrar 0 mm ao
 * lado de uma estação vizinha com 40 mm mandaria a pessoa para o lado errado.
 */
import type { ChuvaAoVivo, MilimetrosPorJanela } from '../dados/tempoReal'

/** As janelas que a fonte publica, da mais curta para a mais longa. */
export const JANELAS = ['min10', 'h1', 'h12', 'h24', 'h48'] as const
export type Janela = (typeof JANELAS)[number]

export const ROTULO_JANELA: Record<Janela, string> = {
  min10: '10 min',
  h1: '1 h',
  h12: '12 h',
  h24: '24 h',
  h48: '48 h',
}

export interface FaixaChuva {
  /** O maior valor entre os pluviômetros da cidade. */
  maior: number
  /** O menor, para mostrar a discordância quando ela existe. */
  menor: number
}

export interface ResumoChuva {
  porJanela: Partial<Record<Janela, FaixaChuva>>
  /** Quantos pluviômetros entraram na conta. */
  pluviometros: number
  /** Quantos ficaram de fora por publicarem série que não fecha. */
  descartados: number
  /** A medição mais recente entre os que entraram. */
  medidoEm: Date | null
}

export function resumir(leituras: ChuvaAoVivo[]): ResumoChuva | null {
  const boas = leituras.filter((c) => c.coerente)
  const descartados = leituras.length - boas.length
  if (boas.length === 0) {
    // Havia leitura, mas nenhuma confiável: isso precisa aparecer na tela como
    // problema da fonte, não como ausência de chuva.
    return descartados > 0
      ? { porJanela: {}, pluviometros: 0, descartados, medidoEm: null }
      : null
  }

  const porJanela: Partial<Record<Janela, FaixaChuva>> = {}
  for (const janela of JANELAS) {
    const valores = boas
      .map((c) => c.mm[janela as keyof MilimetrosPorJanela])
      .filter((v): v is number => v !== null)
    if (valores.length === 0) continue
    porJanela[janela] = { maior: Math.max(...valores), menor: Math.min(...valores) }
  }

  const instantes = boas
    .map((c) => c.medidoEm)
    .filter((d): d is Date => d !== null)
    .map((d) => d.getTime())

  return {
    porJanela,
    pluviometros: boas.length,
    descartados,
    medidoEm: instantes.length > 0 ? new Date(Math.max(...instantes)) : null,
  }
}

/** O resumo da chuva de uma cidade, ou null quando não há pluviômetro nela. */
export function chuvaDaCidade(chuva: ChuvaAoVivo[], cidadeId: string): ResumoChuva | null {
  return resumir(chuva.filter((c) => c.cidade === cidadeId))
}

/** Milímetros em português, com uma casa: `39,6`. */
export function milimetros(valor: number): string {
  return valor.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
}

/** Texto de uma janela: `39,6 mm` ou `19,0–39,6 mm` quando os pontos discordam. */
export function textoFaixa(faixa: FaixaChuva): string {
  // Meio milímetro de diferença entre pluviômetros é ruído do aparelho, não
  // discordância que valha ocupar espaço na tela.
  if (faixa.maior - faixa.menor < 0.5) return `${milimetros(faixa.maior)} mm`
  return `${milimetros(faixa.menor)}–${milimetros(faixa.maior)} mm`
}
