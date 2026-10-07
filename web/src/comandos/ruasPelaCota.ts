/**
 * 16ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): as ruas pela cota, cidade inteira.
 *
 * A aba "Minha rua" responde "a minha rua alaga com quantos metros?" uma rua por vez e tem o controle "e se o rio
 * estivesse em…". Aqui as mesmas contas (`logica/cotasRuas.ts`: `atingidas`, `proximas`, `nivelUtilizavel`,
 * `podeAfirmarAlcance`) respondem pela cidade inteira, no chat:
 *  - "quais ruas alagam com 8 m em Blumenau?": os pontos com cota até esse nível, por bairro e os mais perto do nível;
 *  - "quais ruas o rio já alcançou em Blumenau?": o mesmo, no nível de agora — só com leitura de agora, em régua;
 *  - "quais são as próximas ruas em Blumenau?", "se subir mais 50 cm?": as de cota logo acima, com quanto falta;
 *  - "quais ruas alagam primeiro em Gaspar?": as cotas mais baixas da cidade.
 *
 * As regras da aba valem aqui: cota de rua é PONTO, não rua inteira; a lista é a que a Defesa Civil publicou e não é
 * completa; ponto marcado `usar_para_aviso: false` não vira "já alagou" (Rio do Sul); cota nula não é zero; números
 * na régua da própria cidade. É tabela — nem observação na rua, nem previsão. Em emergência, 199.
 */
import type { Cidade, CotaRua } from '../dados/tipos'
import { atingidas, comCota, daCidade, nivelUtilizavel, nomeCompleto, pendentesAbaixoDoNivel, podeAfirmarAlcance, proximas } from '../logica/cotasRuas'
import { diaDeBrasilia, distancia, horaDeBrasilia } from '../logica/agora'
import { metros } from '../logica/formato'
import { idadeMin, textoIdade } from '../logica/tempoReal'

export const AVISO_RUAS =
  'Cota de rua é o nível da régua em que a fonte diz que a água chega àquele ponto: não diz que a rua inteira alaga, e a lista é a que a Defesa Civil publicou, não é completa. É tabela, não observação na rua nem previsão: quem diz se o rio vai chegar lá é a Defesa Civil. Em emergência, ligue 199.'

/** Quantos pontos o chat nomeia; o resto vira contagem (a aba mostra 12 por busca). */
export const MAX_RUAS_NO_CHAT = 8

const hd = (d: Date) => `${horaDeBrasilia(d)} de ${diaDeBrasilia(d)}`
const ponto = (c: CotaRua) => `${nomeCompleto(c)}${c.bairro ? `, ${c.bairro}` : ''}`
const plural = (n: number, um: string, varios: string) => (n === 1 ? um : varios)

export interface EntradaRuas {
  cidade: Cidade
  cotas: CotaRua[]
  /** Nomes das cidades com cota levantada, para a resposta de quem não tem. */
  cobertas: string[]
}

export function textoSemCotasDeRua(e: EntradaRuas): string {
  const base = `Ainda não há cota de rua levantada para ${e.cidade.nome}. Isso não quer dizer que as ruas de lá não alagam: a tabela não existe aqui. As cidades com cotas publicadas pelas Defesas Civis são: ${e.cobertas.join(', ')}.`
  if (e.cidade.id === 'itajai') {
    return `${base}\nPara Itajaí existe outra coisa: o mapa das manchas de nove enchentes (1983 a 2015), na tela da foz. Não é cota por rua, mas responde parte da pergunta: peça "manchas na rua X" ou "mostrar a avenida Y em Itajaí".`
  }
  return base
}

function porBairro(pontos: CotaRua[]): string {
  const contagem = new Map<string, number>()
  for (const c of pontos) if (c.bairro) contagem.set(c.bairro, (contagem.get(c.bairro) ?? 0) + 1)
  if (!contagem.size) return ''
  const lista = [...contagem.entries()].sort((a, b) => b[1] - a[1])
  const topo = lista.slice(0, 6).map(([b, n]) => `${b} (${n})`)
  return `Por bairro: ${topo.join(', ')}${lista.length > 6 ? ` e mais ${lista.length - 6} bairro${lista.length - 6 === 1 ? '' : 's'}` : ''}.`
}

/**
 * "Quais ruas alagam com 8 m?" e "quais ruas o rio já alcançou?": os pontos com cota até o nível. Nomeia os MAIS
 * PERTO do nível (os últimos alcançados: são os que mudam de um nível para o outro) e conta os de cota mais baixa.
 */
export function textoRuasNoNivel(e: EntradaRuas, nivelM: number, origem: { tipo: 'dito' } | { tipo: 'agora'; medidoEm: Date; agora: Date }): string {
  const { cidade, cotas } = e
  const dela = daCidade(cotas, cidade.id)
  if (!dela.length) return textoSemCotasDeRua(e)
  const contaveis = comCota(cotas, cidade.id).length
  const ja = atingidas(cotas, cidade.id, nivelM)
  const pendentes = pendentesAbaixoDoNivel(cotas, cidade.id, nivelM)
  const semNumero = dela.filter((c) => c.cota_m === null).length
  const cabecalho =
    origem.tipo === 'agora'
      ? `Régua de ${cidade.nome}: ${metros(nivelM)} às ${hd(origem.medidoEm)} (${textoIdade(idadeMin(origem.medidoEm, origem.agora))}). Pela cota publicada, ${ja.length} de ${contaveis} ${plural(contaveis, 'ponto de rua com cota levantada', 'pontos de rua com cota levantada')} ${plural(ja.length, 'já estaria alagado', 'já estariam alagados')}.`
      : `Se o rio em ${cidade.nome} chegar a ${metros(nivelM)}, pela cota publicada ${ja.length} de ${contaveis} ${plural(contaveis, 'ponto de rua com cota levantada', 'pontos de rua com cota levantada')} ${plural(ja.length, 'já estaria alagado', 'já estariam alagados')}.`
  const linhas = [cabecalho]
  if (!ja.length) {
    const primeiro = proximas(cotas, cidade.id, nivelM, 1)[0]
    if (primeiro?.cota_m != null) linhas.push(`Nenhum ponto levantado alaga com o rio nesse nível. O primeiro é ${ponto(primeiro)}, a partir de ${metros(primeiro.cota_m)}${origem.tipo === 'agora' ? ` (faltam ${distancia(primeiro.cota_m - nivelM)})` : ''}.`)
  } else {
    const bairros = porBairro(ja)
    if (bairros) linhas.push(bairros)
    const maisPerto = ja.slice().sort((a, b) => (b.cota_m ?? 0) - (a.cota_m ?? 0)).slice(0, MAX_RUAS_NO_CHAT)
    linhas.push(ja.length > MAX_RUAS_NO_CHAT ? `Os ${maisPerto.length} pontos mais perto desse nível (os últimos alcançados):` : 'Os pontos:')
    for (const c of maisPerto) linhas.push(`• ${ponto(c)} — a partir de ${metros(c.cota_m!)}${c.abrigo ? ` · abrigo: ${c.abrigo}` : ''}`)
    if (ja.length > maisPerto.length) linhas.push(`E mais ${ja.length - maisPerto.length} ${plural(ja.length - maisPerto.length, 'ponto', 'pontos')} com cota mais baixa, que alagam antes. Para a sua rua, peça "minha rua em ${cidade.nome}" ou procure na aba Minha rua.`)
  }
  if (pendentes.length) linhas.push(`Fora da conta: ${pendentes.length} ${plural(pendentes.length, 'ponto', 'pontos')} com cota abaixo desse nível que a fonte marca como não conferido para aviso (${pendentes.map(ponto).join('; ')}).`)
  if (semNumero) linhas.push(`${semNumero} ${plural(semNumero, 'rua citada pela fonte não tem', 'ruas citadas pela fonte não têm')} número de cota e ${plural(semNumero, 'fica', 'ficam')} fora da conta.`)
  linhas.push(`Números na régua de ${cidade.nome}: não compare com outra cidade. ${AVISO_RUAS}`)
  return linhas.join('\n')
}

/** "Quais são as próximas ruas?" e "se subir mais 50 cm?": as de cota logo acima do nível de agora. */
export function textoProximasRuas(e: EntradaRuas, nivelM: number, medidoEm: Date, agora: Date, subirM?: number): string {
  const { cidade, cotas } = e
  if (!daCidade(cotas, cidade.id).length) return textoSemCotasDeRua(e)
  const leitura = `Régua de ${cidade.nome}: ${metros(nivelM)} às ${hd(medidoEm)} (${textoIdade(idadeMin(medidoEm, agora))}).`
  if (subirM != null) {
    const alvo = Math.round((nivelM + subirM) * 100) / 100
    const novas = atingidas(cotas, cidade.id, alvo).filter((c) => (c.cota_m ?? 0) > nivelM)
    const linhas = [
      leitura,
      `Se subisse mais ${distancia(subirM)}, para ${metros(alvo)}, pela cota publicada ${novas.length} ${plural(novas.length, 'ponto de rua a mais já estaria alagado', 'pontos de rua a mais já estariam alagados')}${novas.length ? ':' : '.'}`,
    ]
    for (const c of novas.slice(0, MAX_RUAS_NO_CHAT)) linhas.push(`• ${ponto(c)} — a partir de ${metros(c.cota_m!)} (faltam ${distancia(c.cota_m! - nivelM)})`)
    if (novas.length > MAX_RUAS_NO_CHAT) linhas.push(`E mais ${novas.length - MAX_RUAS_NO_CHAT} pontos nesse trecho.`)
    linhas.push(`É uma conta sobre a tabela, não previsão de que o rio vai subir. ${AVISO_RUAS}`)
    return linhas.join('\n')
  }
  const seguintes = proximas(cotas, cidade.id, nivelM, MAX_RUAS_NO_CHAT)
  if (!seguintes.length) {
    return [leitura, `Todos os pontos de rua levantados em ${cidade.nome} têm cota igual ou abaixo desse nível: não há "próximas" na tabela.`, AVISO_RUAS].join('\n')
  }
  return [
    leitura,
    `As próximas ruas a alagar, se o rio continuar subindo, com quanto falta na régua de ${cidade.nome}:`,
    ...seguintes.map((c) => `• ${ponto(c)} — a partir de ${metros(c.cota_m!)} (faltam ${distancia(c.cota_m! - nivelM)})${c.abrigo ? ` · abrigo: ${c.abrigo}` : ''}`),
    `"Se continuar subindo" é hipótese, não previsão: o rio pode parar ou descer. ${AVISO_RUAS}`,
  ].join('\n')
}

/** "Quais ruas alagam primeiro?": as cotas mais baixas da cidade. */
export function textoPrimeirasRuas(e: EntradaRuas): string {
  const { cidade, cotas } = e
  if (!daCidade(cotas, cidade.id).length) return textoSemCotasDeRua(e)
  const ordenadas = comCota(cotas, cidade.id).sort((a, b) => (a.cota_m ?? 0) - (b.cota_m ?? 0))
  const primeiras = ordenadas.slice(0, MAX_RUAS_NO_CHAT)
  const bloqueados = daCidade(cotas, cidade.id).filter((c) => c.cota_m !== null && !podeAfirmarAlcance(c))
  return [
    `As ruas que alagam primeiro em ${cidade.nome}, pela cota publicada (da mais baixa para cima, de ${ordenadas.length} pontos com cota):`,
    ...primeiras.map((c) => `• ${ponto(c)} — a partir de ${metros(c.cota_m!)}${c.abrigo ? ` · abrigo: ${c.abrigo}` : ''}`),
    bloqueados.length ? `Fora da lista: ${bloqueados.length} ${plural(bloqueados.length, 'ponto', 'pontos')} que a fonte marca como não conferido para aviso (${bloqueados.map((c) => `${ponto(c)}, ${metros(c.cota_m!)}`).join('; ')}).` : '',
    `Números na régua de ${cidade.nome}: não compare com outra cidade. ${AVISO_RUAS}`,
  ]
    .filter(Boolean)
    .join('\n')
}

/** Sem leitura de agora (ou velha), as perguntas de agora não têm nível para comparar. */
export function textoSemNivelDeAgora(cidade: Cidade, leitura: { nivel_m: number; medidoEm: Date | null } | null, agora: Date, varias: boolean): string {
  if (varias) return `${cidade.nome} tem várias réguas, cada uma com o seu zero: não há "o nível de agora" da cidade para comparar com cotas de rua.`
  const velha = leitura?.medidoEm ? ` A última leitura é de ${hd(leitura.medidoEm)} (${textoIdade(idadeMin(leitura.medidoEm, agora))}), velha demais para servir como nível de agora.` : ''
  return `Sem leitura de agora da régua de ${cidade.nome}, não digo quais ruas o rio já alcançou.${velha} Peça com um nível: "quais ruas alagam com 8 m em ${cidade.nome}?".`
}

export { nivelUtilizavel }
