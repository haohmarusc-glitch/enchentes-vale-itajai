/**
 * O que o site lembra NESTE aparelho: a cidade da pessoa, as outras que ela
 * segue, se o aviso completo já foi lido e o tamanho da letra.
 *
 * Tudo passa por aqui, e tudo dentro de try/catch: em janela anônima, com
 * armazenamento bloqueado ou cheio, `localStorage` lança — e um site de
 * enchente não pode cair porque não conseguiu lembrar uma preferência. Sem
 * armazenamento, o site se comporta como na primeira visita (inclusive mostra
 * o aviso completo de novo), que é o lado seguro.
 */

/** O mínimo de `Storage` que usamos — permite testar sem navegador. */
export interface Armazem {
  getItem(chave: string): string | null
  setItem(chave: string, valor: string): void
  removeItem(chave: string): void
}

export const CHAVE_CIDADES = 'enchentes:cidades'
export const CHAVE_AVISO = 'enchentes:aviso-lido'
export const CHAVE_LETRA = 'enchentes:letra'
/**
 * Muda quando o texto do aviso mudar de sentido: quem leu a versão anterior
 * precisa ver a nova.
 */
export const VERSAO_AVISO = '2026-10-03'
/** A cidade da pessoa e mais três. Mais que isso vira lista, não atalho. */
export const MAX_CIDADES = 4

/** Uma cidade seguida: o id e o rio da URL (`acu`, `mirim`). */
export interface CidadeSeguida {
  id: string
  rio: 'acu' | 'mirim'
}

function armazemPadrao(): Armazem | null {
  try {
    return typeof window !== 'undefined' ? window.localStorage : null
  } catch {
    return null
  }
}

function ler(chave: string, a: Armazem | null): string | null {
  if (!a) return null
  try {
    return a.getItem(chave)
  } catch {
    return null
  }
}

/** Devolve false quando não deu para gravar — quem chama decide o que fazer. */
function gravar(chave: string, valor: string | null, a: Armazem | null): boolean {
  if (!a) return false
  try {
    if (valor === null) a.removeItem(chave)
    else a.setItem(chave, valor)
    return true
  } catch {
    return false
  }
}

/**
 * As cidades seguidas, a primeira é "a minha". Conteúdo inválido (de uma versão
 * antiga, ou editado à mão) vira lista vazia em vez de quebrar a tela.
 */
export function cidadesSeguidas(a: Armazem | null = armazemPadrao()): CidadeSeguida[] {
  const bruto = ler(CHAVE_CIDADES, a)
  if (!bruto) return []
  try {
    const lista: unknown = JSON.parse(bruto)
    if (!Array.isArray(lista)) return []
    const vistas = new Set<string>()
    const saida: CidadeSeguida[] = []
    for (const item of lista) {
      if (!item || typeof item !== 'object') continue
      const { id, rio } = item as Record<string, unknown>
      if (typeof id !== 'string' || !/^[a-z0-9-]+$/.test(id)) continue
      if (rio !== 'acu' && rio !== 'mirim') continue
      if (vistas.has(id)) continue
      vistas.add(id)
      saida.push({ id, rio })
    }
    return saida.slice(0, MAX_CIDADES)
  } catch {
    return []
  }
}

/** Põe a cidade em primeiro lugar ("a minha"), sem duplicar. */
export function tornarMinha(c: CidadeSeguida, a: Armazem | null = armazemPadrao()): CidadeSeguida[] {
  const lista = [c, ...cidadesSeguidas(a).filter((x) => x.id !== c.id)].slice(0, MAX_CIDADES)
  gravar(CHAVE_CIDADES, JSON.stringify(lista), a)
  return lista
}

/** Deixa de seguir a cidade. */
export function deixarDeSeguir(id: string, a: Armazem | null = armazemPadrao()): CidadeSeguida[] {
  const lista = cidadesSeguidas(a).filter((x) => x.id !== id)
  gravar(CHAVE_CIDADES, lista.length ? JSON.stringify(lista) : null, a)
  return lista
}

/** O aviso completo já foi lido NESTA versão do texto? */
export function avisoLido(a: Armazem | null = armazemPadrao()): boolean {
  return ler(CHAVE_AVISO, a) === VERSAO_AVISO
}

export function marcarAvisoLido(a: Armazem | null = armazemPadrao()): boolean {
  return gravar(CHAVE_AVISO, VERSAO_AVISO, a)
}

export type Letra = 'normal' | 'grande'

export function letra(a: Armazem | null = armazemPadrao()): Letra {
  return ler(CHAVE_LETRA, a) === 'grande' ? 'grande' : 'normal'
}

export function gravarLetra(l: Letra, a: Armazem | null = armazemPadrao()): void {
  gravar(CHAVE_LETRA, l === 'grande' ? 'grande' : null, a)
}
