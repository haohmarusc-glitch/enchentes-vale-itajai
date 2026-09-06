/**
 * O que a REPRODUÇÃO pode mostrar na linha de cada cidade — e quando não pode
 * mostrar número nenhum.
 *
 * O DEFEITO QUE ISTO CORRIGE (07/09/2026, achado rodando o site com dado ao
 * vivo). O painel "Reprodução das últimas horas" pegava o ponto mais próximo
 * do instante na série da cidade e escrevia o metro dele. Para Itajaí, essa
 * série NÃO é de uma régua: é a costura das réguas daquele rio na cidade — no
 * Açu, DC-01 (CEPSUL), DC-02 (Praça) e DC-11 (Santa Regina), cada uma com o
 * seu zero.
 *
 * Na série publicada em 06/09/2026, as 564 transições entre pontos vizinhos
 * trocavam de régua, e 381 delas saltavam mais de 1,00 m. Arrastando a
 * reprodução, Itajaí ia de 3,10 m para 1,47 m em um minuto — um salto de
 * 1,63 m que não é o rio subindo nem descendo, é a régua trocando. É o mesmo
 * defeito que a tendência em cm/h de Itajaí já tinha tido, e que rendeu o
 * absurdo de "+2448 cm/h", sobrevivendo num componente que ninguém olhou.
 *
 * A linha ainda mostrava "Sem cota / sem leitura" ao lado do número: o rótulo
 * é da FAIXA (cinza porque não há cota da cidade para afirmar faixa), e ele
 * negava a leitura que estava escrita do lado.
 *
 * A regra é a mesma que o resto do site já segue: cidade com mais de uma
 * régua não tem "o nível da cidade". A reprodução diz VÁRIAS RÉGUAS e manda
 * ler a lista de cada uma, em vez de eleger uma delas em silêncio.
 *
 * PRIMÁRIA E RESGATE SÃO UMA RÉGUA SÓ. Blumenau publica "Blumenau" e
 * "Blumenau (AlertaBlu)": a mesma régua ANA 83800002, o mesmo zero, uma delas
 * é só a fonte de socorro quando a outra cala. Contá-las como duas faria
 * Blumenau PERDER o número — o defeito contra o qual o teste 11 de
 * `docs/testes-navegador.md` foi escrito. O vínculo vem em `resgate_de` no
 * `ultimo.json`; a série publicada NÃO o traz (lista os dois títulos lado a
 * lado), então quem chama passa o mapa por `mesmaRegua`.
 */

export interface PontoDaReproducao {
  medidoEm: Date
  nivel_m: number
  /** Título da régua. `null` quando a fonte não disse de qual régua é. */
  regua: string | null
}

export type LinhaDaReproducao =
  | { tipo: 'leitura'; nivel_m: number; medidoEm: Date }
  | { tipo: 'varias-reguas'; quantas: number }
  | { tipo: 'sem-leitura' }

/**
 * Quantas RÉGUAS DISTINTAS a série desta cidade tem.
 *
 * Ponto sem régua conhecida (`null`) conta como uma régua desconhecida, e duas
 * desconhecidas não são a mesma — a mesma escolha do `resumo24h`, pelo mesmo
 * motivo: juntá-las afirmaria um zero que a fonte não disse.
 */
export function quantasReguas(
  pontos: readonly PontoDaReproducao[],
  /** Título da régua de resgate -> título da PRIMÁRIA que ela socorre. */
  mesmaRegua: ReadonlyMap<string, string> = new Map(),
): number {
  const raiz = (titulo: string): string => {
    // Segue a cadeia até a primária. CICLO NÃO JUNTA: se A diz socorrer B e B
    // diz socorrer A, não há primária, e juntar duas réguas de zeros talvez
    // diferentes num número só é o erro caro. Devolver o próprio título as
    // mantém separadas, e a cidade fica sem metro — o lado seguro.
    const vistos = new Set<string>([titulo])
    let atual = titulo
    for (;;) {
      const acima = mesmaRegua.get(atual)
      if (!acima || vistos.has(acima)) return acima && vistos.has(acima) && acima !== atual ? titulo : atual
      vistos.add(acima)
      atual = acima
    }
  }
  let desconhecidas = 0
  const nomeadas = new Set<string>()
  for (const p of pontos) {
    if (p.regua == null) desconhecidas++
    else nomeadas.add(raiz(p.regua))
  }
  return nomeadas.size + (desconhecidas > 0 ? 1 : 0)
}

/**
 * A linha da cidade num instante da reprodução.
 *
 * `escolher` é quem sabe pegar o ponto do instante (o `leituraEm` do site);
 * entra por parâmetro para esta decisão continuar pura e testável.
 */
export function linhaDaReproducao(
  pontos: readonly PontoDaReproducao[],
  escolhido: PontoDaReproducao | null,
  mesmaRegua: ReadonlyMap<string, string> = new Map(),
): LinhaDaReproducao {
  const quantas = quantasReguas(pontos, mesmaRegua)
  if (quantas > 1) return { tipo: 'varias-reguas', quantas }
  if (!escolhido || !Number.isFinite(escolhido.nivel_m)) return { tipo: 'sem-leitura' }
  return { tipo: 'leitura', nivel_m: escolhido.nivel_m, medidoEm: escolhido.medidoEm }
}

/**
 * O mapa resgate -> primária, a partir das leituras ao vivo.
 *
 * O `ultimo.json` é quem traz `resgate_de`; a série publicada não. Sem este
 * mapa, "Blumenau" e "Blumenau (AlertaBlu)" passariam por duas réguas e a
 * cidade perderia o número na reprodução.
 */
export function vinculoDeResgate(
  leituras: readonly { estacao: string; resgateDe: string | null }[],
): Map<string, string> {
  const mapa = new Map<string, string>()
  for (const l of leituras) {
    if (l.resgateDe && l.resgateDe !== l.estacao) mapa.set(l.estacao, l.resgateDe)
  }
  return mapa
}
