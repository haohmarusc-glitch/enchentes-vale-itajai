/**
 * O aviso que o gráfico de picos históricos não podia deixar de dar.
 *
 * O gráfico ordena enchentes por METRO DE RIO. É a única grandeza que temos, e
 * para quase tudo ela serve. Mas o Vale tem um contraexemplo enorme: **novembro
 * de 2008**. Em Blumenau ele marcou 11,52 m — a 32ª maior cota dos nossos 113
 * registros, com trinta e uma enchentes acima dela, entre elas 1880 (17,10 m) e
 * 1984 (15,46 m). E foi o evento mais letal da história da região.
 *
 * O motivo está no próprio registro, na palavra da Defesa Civil de Blumenau:
 * "as mortes vieram sobretudo dos deslizamentos". Encosta não sobe régua. Quem
 * olhasse só a altura da barra concluiria que 2008 foi um evento médio — e essa
 * é exatamente a conclusão que este projeto existe para não deixar acontecer.
 *
 * Por que o aviso é do GRÁFICO e não de cada ponto: marcar só os eventos cuja
 * nota fala de deslizamento faria a AUSÊNCIA da marca dizer "aqui não houve" —
 * e não sabemos isso de evento nenhum. Não temos série de deslizamento. Então o
 * aviso é sobre o que a régua NÃO mede, sempre; o exemplo concreto entra quando
 * a cidade na tela tem um registro que o comprove.
 */

/** O necessário para posicionar um evento e ler a nota dele. */
export type PontoHistorico = {
  data: string
  pico: number
  nota?: string
}

export type AvisoEncosta = {
  /** O texto fixo: vale para qualquer cidade, porque régua nenhuma mede encosta. */
  geral: string
  /**
   * O exemplo medido nos dados EM TELA, quando existe. `null` quando a cidade
   * não tem registro que sustente o exemplo — aí fica só o aviso geral, em vez
   * de emprestar o número de Blumenau para uma cidade que não o tem.
   */
  exemplo: { data: string; pico: number; posicao: number; acima: number } | null
}

/** Sem acento e em minúsculas, para "deslizamentos" casar com "DESLIZAMENTO". */
function normalizar(texto: string): string {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

/**
 * A nota fala de morte por encosta?
 *
 * Casa em NOSSA nota curada, não em texto de terceiro: quem escreveu aquele
 * campo foi este projeto, lendo a fonte. Ainda assim é busca por palavra, então
 * serve para ILUSTRAR o aviso — nunca para afirmar que os outros eventos não
 * tiveram deslizamento.
 */
function falaDeEncosta(nota: string | undefined): boolean {
  if (!nota) return false
  const t = normalizar(nota)
  return t.includes('deslizamento') || t.includes('encosta')
}

/**
 * O texto NÃO repete o título em negrito que o componente já mostra ("A régua
 * mede o rio, não a encosta"). Aviso que se repete é aviso que se pula.
 */
const GERAL =
  'Esta lista ordena por metro de rio, e deslizamento não sobe régua — mas é ' +
  'ele que mais mata no Vale. Uma enchente mais baixa aqui pode ter sido muito ' +
  'pior para quem morava no morro.'

/**
 * O aviso para o conjunto de pontos em tela.
 *
 * `null` quando não há o que ordenar (menos de dois pontos): sem lista, não há
 * ranking capaz de enganar, e um aviso solto vira ruído.
 */
export function avisoDeEncosta(pontos: PontoHistorico[]): AvisoEncosta | null {
  if (pontos.length < 2) return null

  // Maior para menor: a posição é a que o leitor faria contando as barras.
  const ordenados = [...pontos].sort((a, b) => b.pico - a.pico)
  const achado = ordenados.findIndex((p) => falaDeEncosta(p.nota))
  if (achado === -1) return { geral: GERAL, exemplo: null }

  const p = ordenados[achado]!
  // Só vira exemplo quando há enchente MAIS ALTA na lista: é a inversão que
  // engana. Um evento de encosta que também foi o pico mais alto não contradiz
  // a ordenação, e apontá-lo como exemplo confundiria em vez de esclarecer.
  if (achado === 0) return { geral: GERAL, exemplo: null }

  return {
    geral: GERAL,
    exemplo: { data: p.data, pico: p.pico, posicao: achado + 1, acima: achado },
  }
}
