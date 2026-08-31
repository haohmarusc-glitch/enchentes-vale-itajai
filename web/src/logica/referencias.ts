/**
 * O que a legenda do gráfico pode afirmar sobre a régua.
 *
 * Existe porque o cabeçalho do gráfico de picos dizia, sempre,
 * "Alturas na régua de Blumenau (Ponte Adolfo Konder)". Quando a série mistura
 * referências — parte na régua, parte em IBGE, 20 cm acima —, isso é uma
 * afirmação falsa no lugar mais lido da tela. O aviso existia, mas embaixo do
 * gráfico e da legenda: quem olhasse só as barras não o via.
 *
 * A REGRA BLOQUEANTE do CLAUDE.md manda a tela exibir a referência de cada
 * ponto e avisar quando o gráfico mistura. Avisar em rodapé não cumpre isso
 * enquanto o topo afirma o contrário.
 */

/** A referência declarada de um ponto, como o JSON a guarda. */
export type Referencia = string | null | undefined

/**
 * Quantas referências distintas a tela está mostrando.
 *
 * `undefined` (campo ausente) e `null` (campo presente, sem valor) NÃO são a
 * mesma coisa: ausente é registro antigo, que se assume na régua; nulo é
 * "ninguém conferiu". Contar os dois juntos esconderia a mistura.
 */
export function referenciasDistintas(referencias: Referencia[]): Set<string> {
  return new Set(
    referencias.map((r) => (r === undefined ? 'regua' : r === null ? 'nao-declarada' : r)),
  )
}

export function misturaReferencias(referencias: Referencia[]): boolean {
  return referenciasDistintas(referencias).size > 1
}

export interface LegendaDaEscala {
  /** O texto do cabeçalho, já decidido. */
  texto: string
  /** Verdadeiro quando o cabeçalho é um aviso, não uma afirmação. */
  ehAviso: boolean
}

/**
 * O cabeçalho do gráfico: afirma a régua só quando pode afirmar.
 *
 * Com uma referência só, diz de qual régua são as alturas. Com mais de uma,
 * não diz — porque não é verdade — e avisa que a escala está misturada.
 */
export function legendaDaEscala(
  nomeCidade: string,
  regua: string | null | undefined,
  referencias: Referencia[],
): LegendaDaEscala {
  const nomeDaRegua = regua ? ` (${regua})` : ''
  if (misturaReferencias(referencias)) {
    return {
      texto: `Alturas de ${nomeCidade} em mais de uma referência — não estão todas na mesma escala. `
        + 'Veja a ressalva abaixo do gráfico. Não compare com outra cidade.',
      ehAviso: true,
    }
  }
  return {
    texto: `Alturas na régua de ${nomeCidade}${nomeDaRegua}. Não compare com outra cidade.`,
    ehAviso: false,
  }
}
