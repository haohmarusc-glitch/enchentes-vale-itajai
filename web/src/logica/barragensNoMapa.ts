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
import { metros, numero } from './formato'
import { idadeMin, textoIdade } from './tempoReal'

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
  /** O resto do que a fonte publica, para o painel do toque (07/10/2026). Ausente = não informado. */
  rio?: string | null
  medidoEm?: Date | null
  percentPublicado?: number | null
  percentDivergenciaPp?: number | null
  capacidadeAtual?: number | null
  capacidadeMaxima?: number | null
  nivelReguaM?: number | null
  zeroReguaM?: number | null
  altitudeM?: number | null
  fonte?: string | null
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
      rio: b.rio,
      medidoEm: b.medidoEm,
      percentPublicado: b.percentPublicado ?? null,
      percentDivergenciaPp: b.percentDivergenciaPp ?? null,
      capacidadeAtual: b.capacidadeAtual ?? null,
      capacidadeMaxima: b.capacidadeMaxima ?? null,
      nivelReguaM: b.nivelReguaM ?? null,
      zeroReguaM: b.zeroReguaM ?? null,
      altitudeM: b.altitudeM ?? null,
      fonte: b.fonte ?? null,
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

// --- Armazenamento e painel do toque (07/10/2026, "Monitor: Ituporanga e barragens", seção 2) ---------------
//
// O armazenamento NÃO tem faixas operacionais oficiais publicadas para estas barragens: nada de atenção,
// alerta ou emergência aqui. Sai um indicador QUANTITATIVO, numa escala azul própria, com o número. E ele
// não pinta o rio a jusante nem muda a correnteza: a cor do rio continua sendo a régua do trecho.

/** As cores da escala de armazenamento (azul): do vazio ao cheio. Fora da paleta de faixa. */
export const AZUL_VAZIO = 'rgba(70,120,170,0.35)'
export const AZUL_CHEIO = 'rgb(90,170,240)'

/** Texto do percentual: o valor real, também acima de 100. */
export function textoPercentual(p: number): string {
  return `${numero(p, p < 10 ? 1 : 0)} %`
}

/** Uma linha do painel da barragem. `valor` null = "não informado". */
export interface LinhaDaBarragem {
  rotulo: string
  valor: string | null
  nota?: string
}

const BRASILIA_DATA_HORA = new Intl.DateTimeFormat('pt-BR', {
  timeZone: 'America/Sao_Paulo', day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
})

/**
 * O que o painel mostra de uma barragem, linha por linha, com "não informado" no que a fonte não publica.
 * Nunca preenche com zero nem supõe funcionamento normal. A leitura velha é dita como tal.
 */
export function fichaDaBarragem(b: BarragemNoMapa): { situacao: string; linhas: LinhaDaBarragem[] } {
  const quando = b.medidoEm ? `${BRASILIA_DATA_HORA.format(b.medidoEm)} (Brasília)` : null
  const situacao = b.idadeMin === null
    ? 'Leitura sem horário: estado não confirmado.'
    : b.fresca
      ? `Leitura de ${textoIdade(b.idadeMin)}.`
      : `Leitura antiga (${textoIdade(b.idadeMin)}): pode ter mudado desde então.`
  const nivel: LinhaDaBarragem = b.nivelReguaM != null && b.zeroReguaM != null && b.altitudeM != null
    ? {
        rotulo: 'Nível na régua da barragem',
        valor: metros(b.nivelReguaM),
        nota: `Régua própria da barragem: o zero fica a ${numero(b.zeroReguaM, 0)} m de altitude, então a água está a ` +
          `${numero(b.altitudeM, 2)} m acima do nível do mar. Não se compara com régua de rio nem com a outra barragem.`,
      }
    : { rotulo: 'Nível na régua da barragem', valor: null, nota: 'Sem a referência da régua coerente na fonte.' }
  const percentual: LinhaDaBarragem = b.percentUso != null
    ? {
        rotulo: 'Percentual informado pela fonte',
        valor: textoPercentual(b.percentUso),
        nota: 'A fonte não define o percentual. Ele bate com a capacidade atual dividida pela máxima que ela publica' +
          (b.percentDivergenciaPp ? ` (diferença de ${numero(Math.abs(b.percentDivergenciaPp), 2)} ponto percentual)` : '') +
          (b.percentUso > 100 ? '. Acima de 100 %: acima da capacidade máxima publicada.' : '.'),
      }
    : {
        rotulo: 'Percentual informado pela fonte',
        valor: null,
        nota: b.percentPublicado != null ? `A fonte publicou ${numero(b.percentPublicado, 0)} %, valor implausível.` : undefined,
      }
  const capacidade: LinhaDaBarragem = b.capacidadeAtual != null && b.capacidadeMaxima != null
    ? {
        rotulo: 'Capacidade atual / máxima',
        valor: `${numero(b.capacidadeAtual, 1)} de ${numero(b.capacidadeMaxima, 1)}`,
        nota: 'A fonte não informa a unidade.',
      }
    : { rotulo: 'Capacidade atual / máxima', valor: null }
  return {
    situacao,
    linhas: [
      { rotulo: 'Comportas', valor: rotuloComportas(b), nota: b.fechadas.length > 0 && b.abertas > 0 ? `fechadas: ${b.fechadas.join(', ')}` : undefined },
      percentual,
      nivel,
      capacidade,
      { rotulo: 'Vazão de entrada e de saída', valor: null },
      { rotulo: 'Nível a jusante', valor: null, nota: 'A fonte publica um número sem referência identificada; ele não é mostrado.' },
      { rotulo: 'Medido em', valor: quando },
      { rotulo: 'Fonte', valor: b.fonte ?? null },
    ],
  }
}
