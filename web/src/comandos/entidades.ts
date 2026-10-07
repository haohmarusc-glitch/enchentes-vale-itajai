/**
 * As entidades que os pedidos citam — cidade, lista de cidades, cota, metros, mês, sujeito — num lugar só
 * (17ª entrega, PR 1 do handoff de qualidade do chat, docs/HANDOFF-QUALIDADE-CHAT-2026-10-07.md).
 *
 * Antes cada leitor de `interpretar.ts` tinha a sua cópia destas regras, e duas cópias divergem em silêncio. Aqui
 * vive a resolução contra o cadastro: nenhum identificador sai do texto sem casar com uma cidade do `Catalogo`, e
 * um nome fora dele devolve `null` (o trecho não vira comando). O comportamento é o mesmo de antes: os testes das
 * dezesseis entregas e a bateria de avaliação (`avaliacao/`) travam a equivalência.
 */
import type { Catalogo, CidadeDoCatalogo } from './tipos'
import { normalizar } from './normalizar'
import { NOMES_DE_COTA } from './linhaDoTempo'

export { NOMES_DE_COTA }

/** O que pode vir antes do nome da cidade num pedido ("a cidade de Gaspar", "o mapa de Blumenau"). */
export const ARTIGOS = /^(?:(?:o|a|os|as|de|do|da|dos|das|em|no|na|para|pra|pro|ao|a cidade de|o mapa de|o monitor de|o pino de)\s+)+/

/** A cidade do cadastro com este nome (ou id), já normalizado e sem artigos; `null` fora do cadastro. */
export function cidadePorNome(alvo: string, cat: Catalogo): CidadeDoCatalogo | null {
  const a = alvo.replace(ARTIGOS, '').trim()
  if (!a) return null
  return cat.cidades.find((c) => normalizar(c.nome) === a || normalizar(c.id) === a) ?? null
}

/** "Aqui", "daqui", "desta cidade": a cidade é a da tela, decidida na execução. */
export const AQUI = /^(?:aqui|daqui|desta cidade|dessa cidade|deste lugar|desse lugar|desta regua|dessa regua|deste trecho|desse trecho|neste trecho|nesse trecho|da cidade|da regua)$/

/**
 * A cidade opcional de um pedido ("… de Gaspar"). Sem alvo, ou "daqui": `{}` e o contexto decide na execução.
 * Alvo que não é cidade do cadastro: `null` — o trecho não vira comando (e o motor de perguntas tenta).
 */
export function cidadeOpcional(alvo: string | undefined, cat: Catalogo): { cidadeId?: string } | null {
  const a = (alvo ?? '').trim()
  if (!a || AQUI.test(a)) return {}
  const c = cidadePorNome(a, cat)
  return c ? { cidadeId: c.id } : null
}

/**
 * Uma lista de cidades dita ("Blumenau, Gaspar e Itajaí"). A vírgula já sumiu na normalização, então lê palavra a
 * palavra, o nome mais longo primeiro ("rio do sul"), e NÃO divide pelo "e": o "e" é pulado como separador, mas um
 * nome composto fica inteiro. Só vale com DUAS ou mais cidades conhecidas; uma palavra fora do cadastro invalida
 * a lista inteira (não se responde com uma cidade a menos).
 */
export function cidadesDaLista(texto: string, cat: Catalogo): string[] | null {
  const palavras = texto.split(' ').filter((w) => w && w !== 'e')
  const ids: string[] = []
  let i = 0
  while (i < palavras.length) {
    let achou: string | null = null
    for (let n = Math.min(4, palavras.length - i); n >= 1 && !achou; n--) {
      const c = cidadePorNome(palavras.slice(i, i + n).join(' '), cat)
      if (c) {
        achou = c.id
        i += n
      }
    }
    if (!achou) return null
    ids.push(achou)
  }
  const unicos = [...new Set(ids)]
  return unicos.length >= 2 ? unicos : null
}

/** Os nomes de cota que a pessoa diz, como `normalizar` os deixa (a chave do cadastro sai de `NOMES_DE_COTA`). */
export const COTA_DITA = '(alerta maximo|alerta|atencao|observacao|monitoramento|inundacao|emergencia|prontidao|transbordamento)'

/** A chave de cota do cadastro para o nome dito, ou o próprio nome quando não é um dos conhecidos. */
export const cotaDita = (s: string | undefined): { cota?: string } => (s ? { cota: NOMES_DE_COTA[s] ?? s } : {})

/** "O rio", "o nível", "a água" antes do verbo não são cidade. */
export const SUJEITO = '(?:o rio|o nivel|a agua|a regua|o itajai(?: acu| mirim)?)'
export const soSujeito = (s: string | undefined): string | undefined => (s && new RegExp(`^${SUJEITO}$`).test(s) ? undefined : s)

/**
 * Metros ditos, como `normalizar` os deixa: "8,50 m" vira "8 50 m" (inteiro e decimal em grupos separados).
 * Só vale um nível possível de rio nesta bacia: acima de 0 e abaixo de 25 m, como `leituraValida`.
 */
export function metrosDitos(inteiro: string | undefined, decimal: string | undefined): number | null {
  if (!inteiro) return null
  const n = Number(`${inteiro}.${decimal ?? '0'}`)
  return n > 0 && n < 25 ? n : null
}

export const MESES_SEM_ACENTO = ['janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
export const MES_DITO = `(${MESES_SEM_ACENTO.join('|')})`

/** 1–12 para o mês dito (sem acento), ou `null`. */
export function mesDito(s: string | undefined): number | null {
  const i = s ? MESES_SEM_ACENTO.indexOf(s) : -1
  return i >= 0 ? i + 1 : null
}
