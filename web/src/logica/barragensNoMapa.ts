/**
 * As barragens como MARCADORES no mapa — e a regra da animação delas.
 *
 * O mapa já tem duas animações, e cada uma SIGNIFICA algo (ver `docs/kikikuru.md`):
 * a correnteza corre mais rápido onde o nível está mais alto, e a onda desce ao
 * mar. Uma terceira animação só entra se disser uma coisa nova e não puder ser
 * confundida com as duas. A comporta diz: **por aqui está passando água, ou
 * não** — operação da barragem, que o nível a jusante sozinho não revela.
 *
 * AS REGRAS QUE ESTE ARQUIVO PRENDE
 *
 * 1. **Animação = comporta aberta.** Comporta fechada não se mexe. É estado
 *    binário da fonte (`aberta: true|false`), não grau nem nível.
 * 2. **Leitura velha não anima** — o mesmo "cinza não corre" da correnteza.
 *    Não se anima uma comporta cujo estado não sabemos mais. `FRESCA_MIN` é o
 *    mesmo limite do coletor: 60 min sem leitura nova, com a fonte a cada 15,
 *    já é sinal de parada.
 * 3. **Cor própria, nunca a de faixa.** Segurar e soltar são operação normal;
 *    pintar "soltando" de laranja faria a manobra certa parecer emergência.
 * 4. **Só nos mapas do Açu.** As três barragens (Oeste, Sul, Norte) controlam
 *    afluentes do Açu; no mapa do Mirim elas não existem.
 * 5. **Sem coordenada, sem marcador.** Chutar posição num mapa de enchente é
 *    pior que não desenhar.
 */
import type { Barragem } from '../dados/barragens'
import { idadeMin } from './tempoReal'

/** Minutos sem leitura nova a partir dos quais a comporta deixa de animar. */
export const FRESCA_MIN = 60

/** Rios em cujo mapa as barragens aparecem. `bacia` é o Monitor inteiro. */
export const RIOS_COM_BARRAGEM: ReadonlySet<string> = new Set(['itajai-acu', 'bacia'])

/** Uma volta completa da água pela comporta aberta, em segundos. */
export const PERIODO_COMPORTA_S = 1.6

export type BarragemNoMapa = {
  nome: string
  lon: number
  lat: number
  abertas: number
  total: number
  fechadas: string[]
  percentUso: number | null
  /** Leitura nova o bastante para a comporta aberta animar. */
  fresca: boolean
  /** Idade em minutos, para o rótulo. `null` sem carimbo. */
  idadeMin: number | null
}

/**
 * Filtra e prepara as barragens para o mapa de um rio (ou da bacia).
 * Devolve `[]` em rio sem barragem e para quem não tem coordenada.
 */
export function barragensNoMapa(
  barragens: Iterable<Barragem>,
  agora: Date,
  rioId: string,
): BarragemNoMapa[] {
  if (!RIOS_COM_BARRAGEM.has(rioId)) return []
  const saida: BarragemNoMapa[] = []
  for (const b of barragens) {
    if (b.lat === null || b.lon === null) continue
    const idade = b.medidoEm ? idadeMin(b.medidoEm, agora) : null
    saida.push({
      nome: b.nome,
      lon: b.lon,
      lat: b.lat,
      abertas: b.abertas,
      total: b.total,
      fechadas: b.fechadas,
      percentUso: b.percentUso,
      // Sem carimbo não é "fresca por padrão": é não sei, e não sei não anima.
      fresca: idade !== null && idade >= 0 && idade <= FRESCA_MIN,
      idadeMin: idade,
    })
  }
  return saida
}

/**
 * Fase 0..1 da água passando pela comporta aberta, em função do tempo.
 * Com `tempo = 0` (o que o mapa passa em `prefers-reduced-motion`) fica em 0:
 * um quadro parado, sem sortear posição.
 */
export function faseComporta(tempo: number): number {
  if (!Number.isFinite(tempo) || tempo <= 0) return 0
  return ((tempo / PERIODO_COMPORTA_S) % 1 + 1) % 1
}

/**
 * Uma comporta está aberta? Pelo NOME da fonte contra a lista de fechadas — a
 * mesma fonte de verdade que o coletor e o bloco de texto usam. Comporta que
 * não está na lista de fechadas está aberta; a lista é que carrega a dúvida
 * (comporta sem campo entra nela).
 */
export function comportaAberta(nome: string, fechadas: readonly string[]): boolean {
  return !fechadas.includes(nome)
}

/**
 * As comportas de uma barragem, em ordem, com o estado de cada uma. Os nomes
 * são os da fonte (`C1`…`Cn`) quando `total` bate com o padrão; é só rótulo
 * interno para casar com `fechadas`.
 */
export function comportas(
  total: number,
  fechadas: readonly string[],
): { nome: string; aberta: boolean }[] {
  const lista: { nome: string; aberta: boolean }[] = []
  for (let i = 1; i <= total; i++) {
    const nome = `C${i}`
    lista.push({ nome, aberta: comportaAberta(nome, fechadas) })
  }
  return lista
}

/** Texto curto do estado, para o rótulo do marcador. */
export function rotuloComportas(b: Pick<BarragemNoMapa, 'abertas' | 'total'>): string {
  if (b.abertas === 0) return `${b.total} de ${b.total} fechadas`
  return `${b.abertas} de ${b.total} abertas`
}
