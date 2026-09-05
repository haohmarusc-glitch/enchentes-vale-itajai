/**
 * Estado das duas barragens do Alto Vale, publicado em `ultimo_barragens.json`
 * no branch `tempo-real`, ao lado do `ultimo.json`.
 *
 * POR QUE ISTO VAI PARA A TELA
 * O mesmo nível a jusante significa coisas opostas conforme a barragem esteja
 * segurando ou soltando água. Sem isto, o site mostra Rio do Sul em 5,4 m e o
 * morador não tem como saber se a cheia está sendo amortecida ou se a água já
 * está passando direto. Foi por não ter este dado que uma análise nossa
 * concluiu que a cota de Rio do Sul estava errada, quando o rio estava sendo
 * mantido alto de propósito enquanto o sistema esvaziava.
 *
 * ⚠️ O QUE ESTE MÓDULO NÃO ENTREGA, DE PROPÓSITO
 *
 * 1. **O nível da barragem em metros.** A régua da barragem tem zero PRÓPRIO
 *    (339 m de altitude na Oeste, 370 na Sul). Mostrar "14,66 m" ao lado dos
 *    "5,24 m" de Rio do Sul convidaria a comparação que é o erro central deste
 *    projeto. O que atravessa sem datum é o ESTADO DAS COMPORTAS e o PERCENTUAL
 *    de capacidade — e é só isso que sai daqui.
 *
 * 2. **Um veredito sobre a cheia.** "O pico já passou" depende da tendência do
 *    rio, não do estado da comporta. Aqui saem os fatos; quem lê a tendência é
 *    a linha do tempo, na mesma tela. Juntar as duas coisas numa frase só é
 *    exatamente onde um erro viraria "pode voltar para casa".
 *
 * Falhar aqui é inofensivo: sem o arquivo, o bloco não aparece e o resto da
 * tela segue igual.
 */
import { useEffect, useState } from 'react'
import { deBrasilia } from '../logica/tempoReal'

const PADRAO =
  'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/ultimo_barragens.json'

/** Dá para apontar para outra fonte sem recompilar, via .env do Vite. */
export const URL_BARRAGENS = import.meta.env?.VITE_URL_BARRAGENS || PADRAO

const TEMPO_LIMITE_MS = 8000
const RE_SEM_FUSO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$/

export interface Barragem {
  nome: string
  /** Curso que a barragem controla, como a fonte publica. */
  rio: string | null
  abertas: number
  total: number
  /** Nomes das comportas fechadas, para a tela poder dizer quais. */
  fechadas: string[]
  /** Percentual de uso do reservatório, como a FONTE publica — não recalculado. */
  percentUso: number | null
  medidoEm: Date | null
  /**
   * Coordenada da barragem, como a fonte publica — é o que põe o marcador no
   * lugar exato do mapa. `null` quando a fonte não a trouxe: sem coordenada não
   * há marcador, e o bloco de texto segue funcionando. Note o que NÃO está aqui:
   * o nível da barragem em metros (ver o cabeçalho).
   */
  lat: number | null
  lon: number | null
}

/**
 * Quais barragens aparecem na tela de cada cidade.
 *
 * Sai da topologia do próprio cadastro (ver `docs/TOPOLOGIA-CANONICA.md`): Taió
 * está na cabeceira Oeste e Ituporanga na Sul; **Rio do Sul é onde as duas se
 * encontram**, então é a única cidade que precisa das duas ao mesmo tempo. Há
 * teste conferindo este mapa contra os `ramo` do `estacoes.json`, para ele não
 * envelhecer sozinho se a topologia mudar.
 */
export const BARRAGENS_DA_CIDADE: Record<string, readonly string[]> = {
  taio: ['Barragem Oeste Taió'],
  ituporanga: ['Barragem Sul Ituporanga'],
  'rio-do-sul': ['Barragem Oeste Taió', 'Barragem Sul Ituporanga'],
}

function barragemValida(bruta: unknown): Barragem | null {
  if (typeof bruta !== 'object' || bruta === null) return null
  const b = bruta as Record<string, unknown>
  if (typeof b.nome !== 'string' || b.nome.trim() === '') return null

  const total = typeof b.comportas_total === 'number' ? b.comportas_total : Number.NaN
  const abertas = typeof b.comportas_abertas === 'number' ? b.comportas_abertas : Number.NaN
  // Sem saber quantas são, "N de M" não significa nada. E abertas > total é
  // corpo incoerente, não dado.
  if (!Number.isInteger(total) || total <= 0) return null
  if (!Number.isInteger(abertas) || abertas < 0 || abertas > total) return null

  const fechadas: string[] = []
  if (Array.isArray(b.comportas)) {
    for (const c of b.comportas) {
      if (typeof c !== 'object' || c === null) continue
      const comporta = c as Record<string, unknown>
      // `aberta` ausente conta como FECHADA — "não sei" não pode virar
      // "soltando água", que é a direção que engana. Mesma regra do coletor.
      if (comporta.aberta !== true) fechadas.push(String(comporta.nome ?? '?'))
    }
  }

  const pu = typeof b.percent_use === 'number' ? b.percent_use : Number.NaN
  const percentUso = Number.isFinite(pu) && pu >= 0 && pu <= 100 ? pu : null

  let medidoEm: Date | null = null
  if (typeof b.medido_em === 'string' && RE_SEM_FUSO.test(b.medido_em)) {
    const d = deBrasilia(b.medido_em)
    medidoEm = Number.isNaN(d.getTime()) ? null : d
  }

  // A bacia do Itajaí cabe folgada em lat −28..−26, lon −51..−48. Coordenada
  // fora disso é troca de campo ou defeito, e um marcador no lugar errado num
  // mapa de enchente é pior que nenhum: vira null.
  const lat0 = typeof b.lat === 'number' ? b.lat : Number.NaN
  const lon0 = typeof b.lon === 'number' ? b.lon : Number.NaN
  const coordOk = lat0 > -28 && lat0 < -26 && lon0 > -51 && lon0 < -48

  return {
    nome: b.nome,
    rio: typeof b.rio === 'string' ? b.rio : null,
    abertas,
    total,
    fechadas,
    percentUso,
    medidoEm,
    lat: coordOk ? lat0 : null,
    lon: coordOk ? lon0 : null,
  }
}

/** Mapa nome da barragem → estado. Corpo ruim vira mapa vazio, nunca palpite. */
export function montarBarragens(corpo: unknown): Map<string, Barragem> {
  const mapa = new Map<string, Barragem>()
  if (typeof corpo !== 'object' || corpo === null) return mapa
  const lista = (corpo as Record<string, unknown>).barragens
  if (!Array.isArray(lista)) return mapa
  for (const bruta of lista) {
    const b = barragemValida(bruta)
    if (b) mapa.set(b.nome, b)
  }
  return mapa
}

/** As barragens que a tela desta cidade deve mostrar. Vazio quando não há. */
export function barragensDaCidade(
  mapa: Map<string, Barragem>,
  cidadeId: string,
): Barragem[] {
  const nomes = BARRAGENS_DA_CIDADE[cidadeId] ?? []
  return nomes.map((n) => mapa.get(n)).filter((b): b is Barragem => b !== undefined)
}

export type Transporte = (url: string, init: RequestInit) => Promise<Response>

export async function buscarBarragens(
  sinal?: AbortSignal,
  transporte: Transporte = (url, init) => fetch(url, init),
): Promise<Map<string, Barragem>> {
  try {
    const resposta = await transporte(URL_BARRAGENS, { cache: 'no-store', signal: sinal })
    if (!resposta.ok) return new Map()
    return montarBarragens(await resposta.json())
  } catch {
    return new Map()
  }
}

/** Busca ao abrir a página e a cada `intervaloMin`. Falha vira mapa vazio. */
export function useBarragens(intervaloMin = 5): Map<string, Barragem> {
  const [mapa, setMapa] = useState<Map<string, Barragem>>(new Map())

  useEffect(() => {
    let vivo = true
    const emVoo = new Set<AbortController>()

    const buscar = async () => {
      const controle = new AbortController()
      emVoo.add(controle)
      const limite = setTimeout(() => controle.abort(), TEMPO_LIMITE_MS)
      try {
        const novo = await buscarBarragens(controle.signal)
        if (vivo) setMapa(novo)
      } finally {
        clearTimeout(limite)
        emVoo.delete(controle)
      }
    }

    void buscar()
    const relogio = setInterval(() => void buscar(), intervaloMin * 60_000)
    return () => {
      vivo = false
      clearInterval(relogio)
      for (const c of emVoo) c.abort()
    }
  }, [intervaloMin])

  return mapa
}
