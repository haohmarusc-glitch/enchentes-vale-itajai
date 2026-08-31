/**
 * Cidade com mais de uma régua: cada leitura ao lado das cotas DELA.
 *
 * Itajaí tem onze réguas com zeros diferentes. Eleger uma como "o nível de
 * Itajaí" produziria um número que não existe, e a tela sempre se recusou a
 * isso — mas o efeito era a cidade da foz, que recebe os dois rios, ficar sem
 * número nenhum enquanto o dado existia.
 *
 * O perigo de mostrar todas é comparar cada uma com a cota errada. A DC-10, no
 * Limoeiro, usa 8/9/10 m; as do estuário usam pouco mais de um metro. O mesmo
 * 6,75 m é "abaixo de tudo" numa régua e alarme em outra. Por isso o pareamento
 * aqui é pelo TÍTULO exato que a fonte publica, e nunca por prefixo de código.
 */
import type { LeituraAoVivo } from '../dados/tempoReal'
import type { ReguaComCota } from './reguas'
import { cotaAlcancadaEntre } from './tempoReal'

export interface LeituraComRegua {
  leitura: LeituraAoVivo
  /** A régua cadastrada desta leitura, ou null quando não há cota para ela. */
  regua: ReguaComCota | null
  /** A cota mais alta que ESTA régua já passou, ou null. */
  cota: { chave: string; valor: number } | null
}

/**
 * Cada leitura com a régua dela. Leitura sem régua cadastrada entra com
 * `regua: null` — some da tela seria pior: é nível medido de verdade, só sem
 * cota com que comparar.
 */
export function parear(
  leituras: LeituraAoVivo[],
  reguas: ReguaComCota[],
): LeituraComRegua[] {
  const porTitulo = new Map(reguas.map((r) => [r.titulo, r]))
  return leituras.map((leitura) => {
    const regua = porTitulo.get(leitura.estacao) ?? null
    return {
      leitura,
      regua,
      cota: regua ? cotaAlcancadaEntre(regua.cotas, leitura.nivel_m) : null,
    }
  })
}

/**
 * A leitura que a tela deve destacar quando há várias: a que está mais alta
 * EM RELAÇÃO À PRÓPRIA COTA, não a de maior número.
 *
 * Comparar metros entre réguas de zeros diferentes é o erro central deste
 * projeto. O que se compara é a distância de cada uma até a sua cota mais
 * baixa: uma régua 20 cm acima da própria cota de atenção importa mais que
 * outra marcando o dobro de metros e ainda longe da dela.
 *
 * Devolve null quando nenhuma régua tem cota — sem cota não há o que ordenar,
 * e inventar um destaque seria eleger pelo número, que é o que se recusa.
 */
export function maisCritica(pareadas: LeituraComRegua[]): LeituraComRegua | null {
  let melhor: LeituraComRegua | null = null
  let melhorFolga = Infinity
  for (const p of pareadas) {
    if (!p.regua || p.regua.cotas.length === 0) continue
    const piso = Math.min(...p.regua.cotas.map(([, v]) => v))
    const folga = piso - p.leitura.nivel_m
    if (folga < melhorFolga) {
      melhorFolga = folga
      melhor = p
    }
  }
  return melhor
}
