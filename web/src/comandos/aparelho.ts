/**
 * 4ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): o que depende do aparelho da pessoa.
 * Funções puras.
 *
 * - "usar minha localização": a régua mais perto EM LINHA RETA. A posição não é gravada, não vai para o
 *   endereço nem para servidor nenhum: fica na memória da tela até ela fechar. Distância não é previsão — não
 *   diz se a água chega à pessoa, nem quando.
 * - "relatar problema": o site não tem canal de relato. O chat prepara o texto; a pessoa copia e envia.
 */
import { diaDeBrasilia, horaDeBrasilia } from '../logica/agora'
import type { Catalogo } from './tipos'

export interface Posicao {
  lat: number
  lon: number
  /** Raio de incerteza informado pelo aparelho, em metros. */
  precisaoM: number | null
}

/** Mais longe que isso da régua mais perto, a pessoa está fora da área das réguas do site. */
export const KM_FORA_DA_AREA = 25
/** Posição com incerteza acima disso pode trocar qual régua é a mais perto. */
export const PRECISAO_RUIM_M = 2000

export function distanciaKm(a: { lat: number; lon: number }, b: { lat: number; lon: number }): number {
  const rad = (g: number) => (g * Math.PI) / 180
  const dLat = rad(b.lat - a.lat)
  const dLon = rad(b.lon - a.lon)
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLon / 2) ** 2
  return 2 * 6371 * Math.asin(Math.sqrt(h))
}

export interface ReguaPerto {
  /** "Gaspar" ou "DC-05 · Sítio Sr. Hilário, em Itajaí". */
  rotulo: string
  cidadeId: string
  km: number
  naoConfirmada: boolean
}

/** As réguas do cadastro (a de cada cidade e as DC de Itajaí), da mais perto para a mais longe. */
export function reguasPerto(p: Posicao, cat: Catalogo): ReguaPerto[] {
  const nome = (id: string) => cat.cidades.find((c) => c.id === id)?.nome ?? id
  const comReguasProprias = new Set(cat.reguas.map((r) => r.cidadeId))
  const daCidade: ReguaPerto[] = cat.cidades
    // Itajaí não tem "a régua da cidade": entram as onze dela, cada uma pelo nome.
    .filter((c) => typeof c.lat === 'number' && typeof c.lon === 'number' && !comReguasProprias.has(c.id))
    .map((c) => ({ rotulo: c.nome, cidadeId: c.id, km: distanciaKm(p, { lat: c.lat!, lon: c.lon! }), naoConfirmada: !!c.coordenadaNaoConfirmada }))
  const dc: ReguaPerto[] = cat.reguas
    .filter((r) => typeof r.lat === 'number' && typeof r.lon === 'number')
    .map((r) => ({ rotulo: `${r.codigo} · ${r.nome}, em ${nome(r.cidadeId)}`, cidadeId: r.cidadeId, km: distanciaKm(p, { lat: r.lat!, lon: r.lon! }), naoConfirmada: false }))
  return [...daCidade, ...dc].sort((a, b) => a.km - b.km)
}

const km = (n: number) => `${n.toLocaleString('pt-BR', { maximumFractionDigits: n < 10 ? 1 : 0 })} km`

export const AVISO_DISTANCIA =
  'Distância em linha reta não diz se a água chega até você, nem quando: o nível de cada régua vale para o rio naquele ponto, não para a sua rua. Em emergência, ligue 199.'
export const AVISO_PRIVACIDADE =
  'Sua localização ficou só nesta tela: o site não grava, não põe no endereço e não envia para lugar nenhum. Ela some ao fechar a página.'

export function textoDaLocalizacao(p: Posicao, cat: Catalogo): { texto: string; perto: ReguaPerto | null; fora: boolean } {
  const lista = reguasPerto(p, cat)
  const perto = lista[0] ?? null
  if (!perto) return { texto: 'O cadastro não tem coordenada de régua para comparar.', perto: null, fora: true }
  if (perto.km > KM_FORA_DA_AREA) {
    return {
      texto: [`Você parece estar fora da área das réguas do site: a mais perto, ${perto.rotulo}, fica a ${km(perto.km)} em linha reta.`, AVISO_PRIVACIDADE].join('\n'),
      perto,
      fora: true,
    }
  }
  const linhas = [`A régua mais perto de você, em linha reta, é ${perto.rotulo === cat.cidades.find((c) => c.id === perto.cidadeId)?.nome ? `a de ${perto.rotulo}` : `a ${perto.rotulo}`} (${km(perto.km)}).`]
  const depois = lista.slice(1, 3)
  if (depois.length) linhas.push(`Depois: ${depois.map((r) => `${r.rotulo} (${km(r.km)})`).join('; ')}.`)
  if (perto.naoConfirmada) linhas.push(`A posição da régua de ${perto.rotulo} no mapa não está confirmada: a distância pode estar errada.`)
  if (p.precisaoM != null && p.precisaoM > PRECISAO_RUIM_M) {
    linhas.push(`O aparelho informou a posição com incerteza de cerca de ${km(p.precisaoM / 1000)}: a régua mais perto pode ser outra.`)
  }
  linhas.push(AVISO_DISTANCIA, AVISO_PRIVACIDADE)
  return { texto: linhas.join('\n'), perto, fora: false }
}

/** O texto do relato, para a pessoa copiar e completar. Sem endereço do site (só o caminho da tela). */
export function textoDoRelato(args: { tela: string; caminho: string; mostra: string | null; agora: Date }): string {
  return [
    'Relato de problema — site Enchentes do Vale do Itajaí',
    `Quando: ${diaDeBrasilia(args.agora)}, ${horaDeBrasilia(args.agora)} (horário de Brasília)`,
    `Tela: ${args.tela} (${args.caminho})`,
    `O site mostra: ${args.mostra ?? 'nenhuma leitura nesta tela'}`,
    'O problema: [descreva aqui o que está errado]',
  ].join('\n')
}

export const AVISO_RELATO =
  'O site ainda não tem um canal de relato. O texto abaixo está pronto: copie, complete o problema e mande para quem administra o site (o mesmo contato que liberou o seu acesso). Relato ao site não é alerta: se a água está subindo, ligue 199.'
