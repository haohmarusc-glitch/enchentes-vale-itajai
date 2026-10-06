/**
 * De onde vem a posição do pino, escrito no painel da cidade do Monitor (auditoria de 06/10/2026).
 *
 * O mapa desenha o pino num ponto e não dizia de onde ele saiu. Três casos, que não podem se confundir:
 * - a coordenada é a de uma estação da Defesa Civil de SC: diz o código. Não diz que é a mesma régua da
 *   leitura municipal; isso o painel já separa no nível e nas cotas;
 * - o cadastro sabe que a coordenada NÃO é a régua (Blumenau, pluviômetro): "posição aproximada";
 * - cidade de várias réguas (Itajaí): o pino marca a cidade, e cada régua tem o seu ponto.
 */
import type { Cidade } from '../dados/tipos'

const grau = (n: number) => n.toFixed(4).replace('.', ',').replace('-', '−')

export function textoDaPosicao(
  cidade: Pick<Cidade, 'codigo_dcsc' | 'coordenadas'>,
  pino: { lat: number; lon: number; aproximado: boolean },
  reguasDaCidade: number,
): string {
  const onde = `${grau(pino.lat)}, ${grau(pino.lon)}`
  if (pino.aproximado) {
    return `Posição aproximada (${onde}): a fonte não informa onde fica a régua. O pino está no rio, no ponto mais perto da coordenada que temos.`
  }
  if (reguasDaCidade > 1) {
    return `Este pino marca a cidade (${onde}). Cada régua aparece no mapa no seu próprio ponto.`
  }
  if (cidade.codigo_dcsc) {
    return `Pino na coordenada da estação ${cidade.codigo_dcsc} da Defesa Civil de SC (${onde}).`
  }
  return `Pino na coordenada do cadastro (${onde}). A fonte do nível não confirma o ponto exato da régua.`
}
