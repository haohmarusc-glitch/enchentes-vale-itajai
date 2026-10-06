/**
 * O filtro "só as réguas sem leitura" do Monitor, pedido pelo chat (docs/CHAT-GLOBAL-COMANDOS.md, 2ª entrega).
 *
 * "Sem leitura de agora" é a mesma regra de idade do resto do site (`frescorDaCidade`): sem leitura, sem
 * horário ou com leitura velha. Uma cidade tem leitura de agora se QUALQUER fonte dela tem — a régua
 * municipal, a estação estadual (zero próprio, só exibida) ou, em Itajaí, uma das réguas dela. O filtro só
 * esconde do mapa o que tem leitura; não muda cor, faixa nem número de ninguém.
 */
import { frescorDaCidade, idadeMin, type Faixa } from './tempoReal'

const fresca = (medidoEm: Date | null | undefined, cidade: string | null, agora: Date) =>
  !!medidoEm && Number.isFinite(medidoEm.getTime()) && frescorDaCidade(idadeMin(medidoEm, agora), cidade) !== 'velha'

export function reguaSemLeituraDeAgora(r: { nivel: number | null; medidoEm: Date | null; cidade: string | null }, agora: Date): boolean {
  return r.nivel == null || !fresca(r.medidoEm, r.cidade, agora)
}

export function pinoSemLeituraDeAgora(
  p: { cidade: { id: string }; nivel: number | null; medidoEm: Date | null; nivelBruto: { medidoEm: Date | null } | null },
  agora: Date,
  /** Alguma régua própria da cidade (as onze de Itajaí) tem leitura de agora. */
  reguaDaCidadeFresca = false,
): boolean {
  if (reguaDaCidadeFresca) return false
  if (p.nivel != null && fresca(p.medidoEm, p.cidade.id, agora)) return false
  if (p.nivelBruto && fresca(p.nivelBruto.medidoEm, p.cidade.id, agora)) return false
  return true
}

/**
 * 6ª entrega: o filtro "só as cidades acima do normal". Usa a faixa que o pino e a régua JÁ mostram (cor do
 * mapa): monitoramento para cima. Cinza (`sem-dado`), várias réguas e régua sem cor (`null`, as de estuário)
 * ficam de fora, porque não afirmam faixa nenhuma. Também só esconde; não muda cor, faixa nem número.
 */
const ACIMA_DO_NORMAL = new Set<Faixa>(['monitoramento', 'atencao', 'alerta', 'inundacao', 'emergencia'])

export function faixaAcimaDoNormal(f: Faixa | null | undefined): boolean {
  return !!f && ACIMA_DO_NORMAL.has(f)
}
