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
  | { texto: string; troca: 'cidade' | 'ano' | 'repetir' }
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
