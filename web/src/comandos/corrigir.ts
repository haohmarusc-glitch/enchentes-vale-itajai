/**
 * 9ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): nome de cidade com erro de digitação.
 *
 * Quem digita no celular, na chuva, escreve "Blumenal" ou "Rio do Sol". O chat casava só o nome exato, e a
 * pergunta caía na resposta genérica. Aqui, o nome mais parecido — UM só, perto o bastante — vira uma
 * PERGUNTA de volta ("Você quis dizer Blumenau?"), com a frase corrigida como sugestão. O palpite nunca é
 * executado nem respondido sozinho: a pessoa toca para confirmar.
 *
 * As regras que seguram o palpite:
 * - se o texto já tem um nome conhecido exato, não há o que corrigir;
 * - nome de até 4 letras (Taió) não é corrigido; 5 a 7 letras aceitam 1 diferença; 8 ou mais, 2;
 * - dois nomes possíveis (ou o mesmo trecho perto de dois nomes) = nenhum palpite;
 * - só onde cabe um nome de cidade (no começo da frase, depois de "em", "de", "está", "mostrar"…, ou com
 *   maiúscula), e nunca em palavra comum que fica a uma letra de um nome ("gastar", "tombo");
 * - a lista de nomes é a de quem chama: o comando usa as cidades do cadastro; a pergunta, também os
 *   municípios do Atlas, para "Pomerode" nunca virar erro de digitação de outra cidade.
 */
import { normalizar } from './normalizar'

export interface NomeConhecido {
  id: string
  nome: string
}

export interface CorrecaoDeCidade {
  /** O trecho como a pessoa escreveu ("Blumenal"). */
  de: string
  /** O nome certo ("Blumenau"). */
  para: string
  cidadeId: string
  /** A frase inteira com o nome trocado, para a sugestão. */
  texto: string
}

/** Distância de edição (Levenshtein), com corte: acima de `max` devolve `max + 1`. */
export function distanciaDeEdicao(a: string, b: string, max = 2): number {
  if (Math.abs(a.length - b.length) > max) return max + 1
  let anterior = Array.from({ length: b.length + 1 }, (_, j) => j)
  for (let i = 1; i <= a.length; i++) {
    const atual = [i]
    let menor = i
    for (let j = 1; j <= b.length; j++) {
      const v = Math.min(anterior[j]! + 1, atual[j - 1]! + 1, anterior[j - 1]! + (a[i - 1] === b[j - 1] ? 0 : 1))
      atual.push(v)
      if (v < menor) menor = v
    }
    if (menor > max) return max + 1
    anterior = atual
  }
  return anterior[b.length]!
}

const limite = (n: string) => (n.length >= 8 ? 2 : n.length >= 5 ? 1 : 0)

/** Palavras do dia a dia a uma letra de um nome de cidade ("gastar" × Gaspar, "tombo" × Timbó). */
const PALAVRAS_COMUNS = new Set(['gastar', 'gastou', 'tombo', 'tomba', 'tombou', 'brisque'])
/** Onde um nome de cidade costuma vir: depois de preposição ou verbo de pedido. */
const ANTES_DE_CIDADE = new Set([
  'em', 'de', 'do', 'da', 'dos', 'das', 'no', 'na', 'nos', 'nas', 'para', 'pra', 'ate', 'a', 'o', 'sobre', 'entre', 'e',
  'esta', 'ta', 'mostrar', 'mostre', 'mostra', 'ver', 'veja', 'abrir', 'abra', 'abre', 'zoom', 'seguir', 'cidade',
])

export function corrigirCidade(texto: string, nomes: readonly NomeConhecido[]): CorrecaoDeCidade | null {
  // Palavra a palavra, guardando a de origem para trocar na frase como foi escrita.
  const tokens = texto.split(/\s+/).filter(Boolean)
  const palavras: { norm: string; token: number }[] = []
  tokens.forEach((tk, i) => {
    for (const w of normalizar(tk).split(' ').filter(Boolean)) palavras.push({ norm: w, token: i })
  })
  const conhecidos = nomes.map((n) => ({ ...n, norm: normalizar(n.nome), idNorm: normalizar(n.id) }))
  const frase = ` ${palavras.map((p) => p.norm).join(' ')} `
  // Já tem um nome conhecido exato: nada a corrigir.
  if (conhecidos.some((c) => frase.includes(` ${c.norm} `) || frase.includes(` ${c.idNorm} `))) return null

  const achados: { inicio: number; fim: number; nome: (typeof conhecidos)[number] }[] = []
  for (const c of conhecidos) {
    const n = c.norm.split(' ').length
    const max = limite(c.norm)
    if (max === 0) continue
    for (let i = 0; i + n <= palavras.length; i++) {
      const trecho = palavras.slice(i, i + n).map((p) => p.norm).join(' ')
      if (trecho.length < 4 || PALAVRAS_COMUNS.has(trecho)) continue
      // Só onde cabe um nome de cidade: no começo, depois de preposição ou verbo de pedido, ou com maiúscula.
      const antes = palavras[i - 1]?.norm
      const maiuscula = /^\p{Lu}/u.test(tokens[palavras[i]!.token]!)
      if (i > 0 && !maiuscula && !(antes && ANTES_DE_CIDADE.has(antes))) continue
      const d = distanciaDeEdicao(trecho, c.norm, max)
      if (d > 0 && d <= max) achados.push({ inicio: i, fim: i + n - 1, nome: c })
    }
  }
  const cidades = new Set(achados.map((a) => a.nome.id))
  if (cidades.size !== 1) return null
  const a = achados[0]!
  // O trecho tem de cobrir palavras inteiras de tokens inteiros (sem cortar "rio-do-sol" ao meio).
  const t0 = palavras[a.inicio]!.token
  const t1 = palavras[a.fim]!.token
  const doToken = (t: number) => palavras.filter((p) => p.token === t).length
  const usadas = palavras.slice(a.inicio, a.fim + 1).length
  const noTrecho = Array.from({ length: t1 - t0 + 1 }, (_, k) => doToken(t0 + k)).reduce((s, x) => s + x, 0)
  if (usadas !== noTrecho) return null
  const pontuacaoFinal = tokens[t1]!.match(/[^\p{L}\p{N}]+$/u)?.[0] ?? ''
  const de = tokens.slice(t0, t1 + 1).join(' ').replace(/[^\p{L}\p{N}]+$/u, '')
  const corrigido = [...tokens.slice(0, t0), `${a.nome.nome}${pontuacaoFinal}`, ...tokens.slice(t1 + 1)].join(' ')
  return { de, para: a.nome.nome, cidadeId: a.nome.id, texto: corrigido }
}

/** A frase de volta: o que não foi achado, o palpite e que nada foi feito. */
export function textoDaCorrecao(c: CorrecaoDeCidade, feito: 'comando' | 'pergunta'): string {
  return feito === 'comando'
    ? `Não achei a cidade "${c.de}". Você quis dizer ${c.para}? Nada foi feito; toque na sugestão para pedir "${c.texto}".`
    : `Não achei a cidade "${c.de}". Você quis dizer ${c.para}? Toque na sugestão para perguntar de novo.`
}
