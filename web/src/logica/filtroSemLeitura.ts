/**
 * O filtro "só as réguas sem leitura" do Monitor, pedido pelo chat (docs/CHAT-GLOBAL-COMANDOS.md, 2ª entrega).
 *
 * "Sem leitura de agora" é a mesma regra de idade do resto do site (`frescorDaCidade`): sem leitura, sem
 * horário ou com leitura velha. Uma cidade tem leitura de agora se QUALQUER fonte dela tem — a régua
 * municipal, a estação estadual (zero próprio, só exibida) ou, em Itajaí, uma das réguas dela. O filtro só
 * esconde do mapa o que tem leitura; não muda cor, faixa nem número de ninguém.
 */
import { frescorDaCidade, idadeMin } from './tempoReal'

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
