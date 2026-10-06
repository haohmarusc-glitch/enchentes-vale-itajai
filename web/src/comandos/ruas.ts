/**
 * Rua no mapa (3ª entrega, docs/CHAT-GLOBAL-COMANDOS.md). Funções puras; nada é geocodificado na hora.
 *
 * - Itajaí: o traçado REAL da via, da base de vias da Prefeitura (GeoItajaí), destacado no mapa das manchas.
 *   Rua cruzando uma mancha é "interseção com o cenário X", nunca "alagou"; sem interseção não quer dizer que a
 *   rua é segura.
 * - Gaspar e Brusque: os PONTOS de cota que a Defesa Civil publicou com coordenada — localização aproximada, sem
 *   traçado da rua. Nunca uma reta entre pontos, nunca um círculo no lugar do traçado.
 * - Blumenau e Rio do Sul: a cota existe, a coordenada não. O mapa não marca nada.
 */
import type { CotaRua } from '../dados/tipos'
import type { RuasPorMancha } from '../chat-local/motor'
import { metros } from '../logica/formato'
import { acharVias, nomeLegivelDaVia, partesDaVia } from '../logica/viasItajai'

/** Menos que isso é a ponta da rua encostando na borda da mancha (mesmo corte do chat de perguntas). */
export const MINIMO_DENTRO_M = 10

export const AVISO_DESTAQUE = 'O destaque mostra onde a rua fica; não indica risco nem alagamento atual.'
export const AVISO_INTERSECAO =
  'Interseção com a mancha não quer dizer que cada casa alagou, e rua fora da mancha não quer dizer rua segura: a mancha é o mapa da área atingida feito pela Prefeitura, na cidade daquele ano.'

const numeroBR = (n: number) => n.toLocaleString('pt-BR')

/** As cheias em que a rua cruza a mancha (≥ 10 m dentro), e as em que não cruza. */
export function intersecoes(t: RuasPorMancha, nome: string): { dentro: { evento: string; rotulo: string; m: number; pct: number }[]; fora: string[] } {
  const r = t.ruas[nome]
  const dentro: { evento: string; rotulo: string; m: number; pct: number }[] = []
  const fora: string[] = []
  for (const e of t._meta.eventos) {
    const v = r?.ev[e.evento]
    if (v && v.m >= MINIMO_DENTRO_M) dentro.push({ evento: e.evento, rotulo: e.rotulo, m: v.m, pct: v.pct })
    else fora.push(e.rotulo)
  }
  return { dentro, fora }
}

/** O texto da rua de Itajaí destacada, com a interseção do cenário pedido (ou de todos). */
export function textoDaRuaItajai(args: { nome: string; tabela: RuasPorMancha | null; evento: string | null; trechos: number }): string {
  const { nome, tabela, evento } = args
  const legivel = nomeLegivelDaVia(nome)
  const linhas = [`${legivel} destacada no mapa das manchas de Itajaí, com o traçado da base de vias da Prefeitura. ${AVISO_DESTAQUE}`]
  if (args.trechos > 1) linhas.push(`A base tem ${args.trechos} trechos com este nome; todos aparecem destacados (ruas com o mesmo nome entram juntas).`)
  if (!tabela) return [...linhas, 'Não consegui carregar o cruzamento das ruas com as manchas.'].join('\n')
  const { dentro, fora } = intersecoes(tabela, nome)
  if (evento) {
    const ev = tabela._meta.eventos.find((e) => e.evento === evento)
    const d = dentro.find((x) => x.evento === evento)
    linhas.push(
      d
        ? `Interseção com o cenário de ${ev?.rotulo ?? evento}: ${d.pct >= 99 ? 'a rua toda' : `${d.pct}% do trecho`} (${numeroBR(d.m)} m) dentro da mancha.`
        : `A rua não cruza a mancha de ${ev?.rotulo ?? evento}.`,
    )
  } else if (dentro.length) {
    linhas.push(`Interseção com as manchas: ${dentro.map((d) => `${d.rotulo} (${d.pct >= 99 ? 'a rua toda' : `${d.pct}%`})`).join('; ')}.`)
    if (fora.length) linhas.push(`Sem interseção: ${fora.join(', ')}.`)
  } else {
    linhas.push('A rua não cruza nenhuma das nove manchas levantadas.')
  }
  linhas.push(AVISO_INTERSECAO)
  return linhas.join('\n')
}

/** Os pontos de cota COM coordenada de uma rua da cidade, casados como as vias de Itajaí. */
export function pontosDaRua(cotas: readonly CotaRua[], cidadeId: string, texto: string): { rua: string; pontos: CotaRua[] }[] {
  const daCidade = cotas.filter((c) => c.cidade === cidadeId && typeof c.lat === 'number' && typeof c.lon === 'number')
  const nomes = acharVias(texto, [...new Set(daCidade.map((c) => c.rua))])
  return nomes.map((rua) => ({ rua, pontos: daCidade.filter((c) => c.rua === rua) }))
}

/** Ruas de uma cidade com cota levantada, mas sem coordenada (Blumenau, Rio do Sul). */
export function ruasSemCoordenada(cotas: readonly CotaRua[], cidadeId: string, texto: string): string[] {
  const daCidade = cotas.filter((c) => c.cidade === cidadeId)
  return acharVias(texto, [...new Set(daCidade.map((c) => c.rua))])
}

const MAX_PONTOS_NO_TEXTO = 6

/** O texto dos pontos marcados: localização aproximada, a cota de cada ponto na régua da cidade, sem previsão. */
export function textoDosPontos(rua: string, cidadeNome: string, pontos: readonly CotaRua[]): string {
  const linhas = [
    `${nomeLegivelDaVia(rua)}, ${cidadeNome}: ${pontos.length === 1 ? 'o ponto de cota marcado' : `os ${pontos.length} pontos de cota marcados`} no Monitor. Localização aproximada: é o ponto da lista da Defesa Civil, não o traçado da rua, que não está disponível.`,
  ]
  for (const c of pontos.slice(0, MAX_PONTOS_NO_TEXTO)) {
    const onde = [c.bairro, c.ponto].filter(Boolean).join(', ')
    linhas.push(`• ${onde || 'ponto sem descrição'}: ${c.cota_m == null ? 'a fonte cita o ponto, mas não publica a cota' : `cota de ${metros(c.cota_m)} na régua de ${cidadeNome}`}.`)
  }
  if (pontos.length > MAX_PONTOS_NO_TEXTO) linhas.push(`• e mais ${pontos.length - MAX_PONTOS_NO_TEXTO} ponto(s), também marcados.`)
  linhas.push(`A cota é o nível do rio, na régua de ${cidadeNome}, a partir do qual o ponto começa a alagar segundo a fonte. Não é previsão, e ponto marcado não quer dizer que a rua inteira alaga nem que o resto dela é seguro.`)
  return linhas.join('\n')
}

/** O nome da rua que a pessoa escreveu tem o tipo ("rua", "avenida")? Para a pergunta de esclarecimento. */
export function comTipo(texto: string): boolean {
  return partesDaVia(texto).tipo !== null
}
