/**
 * 10ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): a conversa que continua.
 *
 * "Como está Blumenau?" e depois "e Gaspar?". O chat lia cada mensagem sozinha, e "e Gaspar?" virava "Gaspar"
 * solto. Aqui, três continuações curtas refazem o ÚLTIMO pedido da conversa com uma troca só, e a tela diz
 * "Entendi como: …" antes de responder, para a troca nunca ser escondida:
 *  - "e Gaspar?", "e em Brusque?": a cidade trocada (o pedido anterior precisa citar UMA cidade);
 *  - "e em 2011?": o ano trocado (o pedido anterior precisa citar UM ano);
 *  - "de novo", "repetir": o mesmo pedido (útil para ver a leitura mais nova).
 * Sem pedido anterior, ou com duas cidades nele, o chat pergunta em vez de adivinhar.
 */
import { normalizar } from './normalizar'
import type { NomeConhecido } from './corrigir'

export type Continuacao =
  | { texto: string; troca: 'cidade' | 'ano' | 'repetir' | 'dia' | 'numero' | 'cota' }
  | { erro: string; sugestoes: string[] }
  | null

interface Palavra {
  norm: string
  token: number
}

function palavrasDe(texto: string): { tokens: string[]; palavras: Palavra[] } {
  const tokens = texto.split(/\s+/).filter(Boolean)
  const palavras: Palavra[] = []
  tokens.forEach((tk, i) => {
    for (const w of normalizar(tk).split(' ').filter(Boolean)) palavras.push({ norm: w, token: i })
  })
  return { tokens, palavras }
}

/** Onde cada nome conhecido aparece no texto (nome inteiro, palavra a palavra). "Itajaí-Açu/Mirim" é rio, não cidade. */
function ocorrencias(palavras: Palavra[], nomes: readonly NomeConhecido[]) {
  const achadas: { inicio: number; fim: number; nome: NomeConhecido }[] = []
  const ordenados = [...nomes].sort((a, b) => normalizar(b.nome).length - normalizar(a.nome).length)
  const usadas = new Set<number>()
  for (const n of ordenados) {
    const alvo = normalizar(n.nome).split(' ')
    for (let i = 0; i + alvo.length <= palavras.length; i++) {
      if (alvo.some((w, k) => palavras[i + k]!.norm !== w || usadas.has(i + k))) continue
      const depois = palavras[i + alvo.length]?.norm
      if (n.id === 'itajai' && (depois === 'acu' || depois === 'mirim')) continue
      achadas.push({ inicio: i, fim: i + alvo.length - 1, nome: n })
      for (let k = 0; k < alvo.length; k++) usadas.add(i + k)
    }
  }
  return achadas.sort((a, b) => a.inicio - b.inicio)
}

/** Troca, na frase como foi escrita, o trecho de palavras [inicio, fim] por `novo` (mantém a pontuação do fim). */
function trocar(tokens: string[], palavras: Palavra[], inicio: number, fim: number, novo: string): string | null {
  const t0 = palavras[inicio]!.token
  const t1 = palavras[fim]!.token
  // Só troca tokens inteiros: "rio-do-sul," é um token com três palavras.
  const noTrecho = palavras.filter((p) => p.token >= t0 && p.token <= t1).length
  if (noTrecho !== fim - inicio + 1) return null
  const pontuacao = tokens[t1]!.match(/[^\p{L}\p{N}]+$/u)?.[0] ?? ''
  return [...tokens.slice(0, t0), `${novo}${pontuacao}`, ...tokens.slice(t1 + 1)].join(' ')
}

const SEM_ANTERIOR = 'Não há pedido anterior nesta conversa para continuar.'

// 19ª entrega: as trocas de dia, cota e número.
const COTAS_LISTA = ['alerta maximo', 'alerta', 'atencao', 'observacao', 'monitoramento', 'inundacao', 'emergencia', 'prontidao', 'transbordamento']
const COTAS = `(${COTAS_LISTA.join('|')})`

/** Onde uma das frases (normalizadas) aparece no texto como foi escrito: [inicio, fim] em palavras. A mais longa vence. */
function ocorrenciasDeFrase(texto: string, frases: readonly string[]): { inicio: number; fim: number }[] {
  const { palavras } = palavrasDe(texto)
  const achadas: { inicio: number; fim: number }[] = []
  const usadas = new Set<number>()
  for (const f of [...frases].sort((a, b) => b.length - a.length)) {
    const alvo = f.split(' ')
    for (let i = 0; i + alvo.length <= palavras.length; i++) {
      if (alvo.some((w, k) => palavras[i + k]!.norm !== w || usadas.has(i + k))) continue
      achadas.push({ inicio: i, fim: i + alvo.length - 1 })
      for (let k = 0; k < alvo.length; k++) usadas.add(i + k)
    }
  }
  return achadas.sort((a, b) => a.inicio - b.inicio)
}

/** Troca o trecho de palavras achado por `novo`, na frase como foi escrita. */
function trocarTrecho(texto: string, trecho: { inicio: number; fim: number }, novo: string): string | null {
  const { tokens, palavras } = palavrasDe(texto)
  return trocar(tokens, palavras, trecho.inicio, trecho.fim, novo)
}

/** Troca a ÚNICA palavra que casa com `re` (normalizada) por `nova`; null se não há exatamente uma. */
function trocarPalavras(texto: string, re: RegExp, nova: string): string | null {
  const { tokens, palavras } = palavrasDe(texto)
  const achadas = palavras.map((p, i) => (re.test(p.norm) ? i : -1)).filter((i) => i >= 0)
  if (achadas.length !== 1) return null
  return trocar(tokens, palavras, achadas[0]!, achadas[0]!, nova)
}

/** Os números do pedido (sem anos), com a unidade que os segue e a posição no texto original. */
function numerosDoPedido(texto: string): { inicio: number; fim: number; unidade: 'm' | 'h' | 'cm' | null }[] {
  const saida: { inicio: number; fim: number; unidade: 'm' | 'h' | 'cm' | null }[] = []
  const re = /(?<![\d,.])(\d{1,2}(?:[,.]\d{1,2})?)(?![\d,.])(?:\s?(m|metros?|h|horas?|cm)\b)?/gi
  for (const m of texto.matchAll(re)) {
    const u = m[2] ? (/^h/i.test(m[2]) ? 'h' : /^cm/i.test(m[2]) ? 'cm' : 'm') : null
    saida.push({ inicio: m.index!, fim: m.index! + m[1]!.length, unidade: u })
  }
  return saida
}

export function continuar(texto: string, anterior: string | null, nomes: readonly NomeConhecido[]): Continuacao {
  const t = normalizar(texto)
  if (/^(?:de novo|outra vez|mais uma vez|repetir|repita|repete)$/.test(t)) {
    if (!anterior) return { erro: `${SEM_ANTERIOR} Diga o pedido inteiro, por exemplo: "como está Blumenau?".`, sugestoes: ['como está Blumenau?'] }
    return { texto: anterior, troca: 'repetir' }
  }
  const ano = t.match(/^e (?:em |no ano de |de |no )?((?:18|19|20)\d{2})(?: agora)?$/)
  if (ano) {
    const novo = ano[1]!
    if (!anterior) return { erro: `${SEM_ANTERIOR} Diga o pedido inteiro, por exemplo: "cheias de ${novo}".`, sugestoes: [`cheias de ${novo}`] }
    const anos = [...new Set(anterior.match(/\b(?:18|19|20)\d{2}\b/g) ?? [])]
    if (anos.length !== 1) {
      return {
        erro: anos.length ? `O pedido anterior cita mais de um ano (${anos.join(', ')}): qual trocar? Diga o pedido inteiro.` : `O pedido anterior não cita ano. Diga o pedido inteiro, por exemplo: "cheias de ${novo}".`,
        sugestoes: [`cheias de ${novo}`],
      }
    }
    return { texto: anterior.replace(new RegExp(`\\b${anos[0]}\\b`, 'g'), novo), troca: 'ano' }
  }
  // 19ª entrega: "e ontem?", "e com 9 m?", "e nas últimas 12 horas?", "e de atenção?" — a mesma pergunta com UMA troca.
  const dia = t.match(/^e (hoje|ontem|anteontem)$/)
  if (dia) {
    const novo = dia[1]!
    if (!anterior) return { erro: `${SEM_ANTERIOR} Diga o pedido inteiro, por exemplo: "quando Blumenau passou da cota de alerta ${novo}?".`, sugestoes: [`quando Blumenau passou da cota de alerta ${novo}?`] }
    const trocado = trocarPalavras(anterior, /^(?:hoje|ontem|anteontem)$/, novo)
    if (trocado) return { texto: trocado, troca: 'dia' }
    if (/\b(?:quando|a que hora|que hora|desde quando|passou|cruzou|entrou|ultrapassou)\b/.test(normalizar(anterior))) {
      return { texto: `${anterior.replace(/\?\s*$/, '')} ${novo}?`, troca: 'dia' }
    }
    return { erro: `O pedido anterior não é uma pergunta de "quando" para trocar o dia. Diga o pedido inteiro, por exemplo: "quando Blumenau passou da cota de alerta ${novo}?".`, sugestoes: [`quando Blumenau passou da cota de alerta ${novo}?`] }
  }
  const cota = t.match(new RegExp(`^e (?:(?:a|de|da|na|em|no|para|pra) )*(?:cota de |cota da |faixa de |nivel de )?${COTAS}$`))
  if (cota) {
    const nova = cota[1]!
    if (!anterior) return { erro: `${SEM_ANTERIOR} Diga o pedido inteiro, por exemplo: "quando Blumenau passou da cota de ${nova}?".`, sugestoes: [`quando Blumenau passou da cota de ${nova}?`] }
    const achadas = ocorrenciasDeFrase(anterior, COTAS_LISTA)
    if (achadas.length !== 1) {
      return { erro: achadas.length ? 'O pedido anterior cita mais de uma cota: qual trocar? Diga o pedido inteiro.' : `O pedido anterior não cita cota. Diga o pedido inteiro, por exemplo: "quando Blumenau passou da cota de ${nova}?".`, sugestoes: [`quando Blumenau passou da cota de ${nova}?`] }
    }
    const trocado = trocarTrecho(anterior, achadas[0]!, nova)
    return trocado ? { texto: trocado, troca: 'cota' } : { erro: 'Não consegui trocar a cota no pedido anterior. Diga o pedido inteiro.', sugestoes: [`quando Blumenau passou da cota de ${nova}?`] }
  }
  const num = t.match(/^e (?:com |a |em |de |para |pra |nas |nas ultimas |ultimas |ate )?(\d{1,2})(?:[ ,.](\d{1,2}))? ?(m|metros?|h|horas?|cm)?$/)
  if (num) {
    const inteiro = num[1]!
    const decimal = num[2]
    const unidade = num[3] ? (/^h/.test(num[3]) ? 'h' : /^cm/.test(num[3]) ? 'cm' : 'm') : null
    const novo = decimal ? `${inteiro},${decimal}` : inteiro
    if (!anterior) return { erro: `${SEM_ANTERIOR} Diga o pedido inteiro, por exemplo: "quais ruas alagam com ${novo} m em Blumenau?".`, sugestoes: [`quais ruas alagam com ${novo} m em Blumenau?`] }
    const numeros = numerosDoPedido(anterior).filter((n) => !unidade || n.unidade === unidade)
    if (numeros.length !== 1) {
      return { erro: numeros.length ? 'O pedido anterior tem mais de um número: qual trocar? Diga o pedido inteiro.' : 'O pedido anterior não tem número para trocar. Diga o pedido inteiro.', sugestoes: ['o que posso pedir?'] }
    }
    const n = numeros[0]!
    const texto = `${anterior.slice(0, n.inicio)}${novo}${anterior.slice(n.fim)}`
    return { texto, troca: 'numero' }
  }
  const cid = t.match(/^e (?:em |no |na |de |do |da |o |a |pra |para |sobre |quanto a |la em |ai em )?(.+?)(?: agora)?$/)
  if (!cid) return null
  const nova = nomes.find((n) => normalizar(n.nome) === cid[1] || normalizar(n.id) === cid[1])
  if (!nova) return null
  if (!anterior) {
    return { erro: `${SEM_ANTERIOR} O que você quer saber de ${nova.nome}?`, sugestoes: [`como está ${nova.nome}?`, `mostrar ${nova.nome}`] }
  }
  const { tokens, palavras } = palavrasDe(anterior)
  const achadas = ocorrencias(palavras, nomes)
  const distintas = [...new Set(achadas.map((a) => a.nome.id))]
  if (distintas.length === 0) {
    return { erro: `O pedido anterior não cita cidade. O que você quer saber de ${nova.nome}?`, sugestoes: [`como está ${nova.nome}?`, `mostrar ${nova.nome}`] }
  }
  if (distintas.length > 1) {
    const ns = distintas.map((id) => achadas.find((a) => a.nome.id === id)!.nome.nome)
    return { erro: `O pedido anterior cita ${ns.join(' e ')}: qual trocar por ${nova.nome}? Diga o pedido inteiro.`, sugestoes: [`como está ${nova.nome}?`] }
  }
  if (distintas[0] === nova.id) return { texto: anterior, troca: 'repetir' }
  // Troca da última para a primeira, para os índices das anteriores continuarem valendo.
  let frase = anterior
  let atual = { tokens, palavras }
  for (const a of [...achadas].reverse()) {
    const r = trocar(atual.tokens, atual.palavras, a.inicio, a.fim, nova.nome)
    if (r === null) return { erro: `Não consegui trocar a cidade no pedido anterior. Diga o pedido inteiro.`, sugestoes: [`como está ${nova.nome}?`] }
    frase = r
    atual = palavrasDe(frase)
  }
  return { texto: frase, troca: 'cidade' }
}
