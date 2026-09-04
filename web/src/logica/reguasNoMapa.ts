/**
 * As réguas individuais de uma cidade como PONTOS no mapa — a decisão de cor.
 *
 * Itajaí tem onze réguas da Defesa Civil, com coordenada própria: duas no
 * Itajaí-Açu, quatro no Mirim (dois braços), três em ribeirões (Murta,
 * Canhanduba) e duas mais acima. O Monitor mostrava a cidade como UM pino azul
 * de "várias réguas" — e os ribeirões, onde a enxurrada urbana acontece,
 * ficavam invisíveis.
 *
 * A ARMADILHA QUE ESTE ARQUIVO EXISTE PARA EVITAR
 * NOVE das onze têm `alerta_automatico: false` no cadastro, e o motivo está
 * escrito na fonte: são réguas de ESTUÁRIO, onde a oscilação da maré é maior
 * que a distância até a cota — em 30/08/2026 essa faixa de estações variou mais
 * de 50 cm em três horas SEM ENCHENTE NENHUMA. Pintar essas nove pela cota
 * deixaria o mapa laranja DUAS VEZES POR DIA, na maré, e quem vê isso todo dia
 * aprende a ignorar a cor — inclusive no dia em que ela for verdadeira.
 *
 * Então: elas aparecem, com o NÚMERO e a idade, e NÃO recebem cor de perigo. É
 * a mesma regra que o `alerta_cotas.py` já aplica para não tocar o Telegram com
 * a maré, e a que a tela de Itajaí já respeita. Aqui ela chega ao mapa.
 *
 * Mostrar o número sem a cor não é meia informação: é a informação inteira, com
 * a única parte que não sabemos afirmar removida.
 */
import type { EstacaoTempoReal } from '../dados/tipos'
import { cotaAlcancadaEntre, frescor, idadeMin, type Faixa } from './tempoReal'

/** As chaves que pintam faixa — o mesmo vocabulário fechado do `faixaDaCidade`. */
const CHAVES_QUE_PINTAM = new Set([
  'monitoramento',
  'atencao',
  'alerta',
  'inundacao',
  'emergencia',
])

export type ReguaNoMapa = {
  codigo: string
  titulo: string
  /**
   * O nome do LUGAR, para o rótulo no mapa — "Portal I", "Rio do Meio",
   * "Bairro Murta".
   *
   * O mapa rotulava com o código (`DC-07 0,32 m`), e ninguém que mora no
   * Portal I sabe o que é DC-07. O `nome_no_plano` do cadastro traz o nome que
   * a Defesa Civil usa no Plano de Contingência — e a parte depois do hífen é
   * justamente o ponto de referência, sem o nome do rio que já se vê no mapa.
   * O código continua no `codigo`, para o painel e para cruzar com o site da
   * Defesa Civil.
   */
  nome: string
  lon: number
  lat: number
  nivel: number | null
  medidoEm: Date | null
  /**
   * A faixa desta régua, ou `null` quando ela NÃO pode virar cor — por ser de
   * maré, por não ter cota, por não ter leitura ou por a leitura estar velha.
   * `null` não é "seguro": é "não afirmamos".
   */
  faixa: Faixa | null
  /** Por que não tem cor, para o painel poder dizer em vez de só omitir. */
  motivoSemCor: string | null
  /**
   * As cotas DESTA régua, não as da cidade.
   *
   * Em Itajaí cada uma tem as suas, com zeros diferentes: a DC-01 usa
   * 1,16/1,36/1,56 e a DC-10 usa 8/9/10. Mostrar a cota da cidade ao lado do
   * número de uma régua convidaria à comparação que a régua de cada uma proíbe.
   */
  cotas: Record<string, number>
}

export type LeituraDeRegua = { titulo: string; nivel_m: number; medidoEm: Date | null }

/**
 * O ponto de referência da régua, curto o bastante para caber no mapa.
 *
 * `"Ribeirão da Murta - Portal I"` -> `"Portal I"`. Sem o nome do rio, que o
 * mapa já mostra, e sem o código, que não diz nada a quem mora ali. Cai para o
 * código e depois para o título quando a fonte não nomeia — nunca fica vazio,
 * porque ponto sem rótulo no meio de outros dez é ponto que não se identifica.
 */
export function nomeDoLugar(e: {
  nome_no_plano?: string
  codigo?: string
  titulo: string
}): string {
  const n = e.nome_no_plano?.trim()
  if (n) {
    const corte = n.lastIndexOf(' - ')
    const curto = corte >= 0 ? n.slice(corte + 3).trim() : n
    if (curto) return curto
  }
  return e.codigo?.trim() || e.titulo
}

/**
 * Junta cadastro + leitura e decide a cor de cada régua.
 *
 * Só entra régua com coordenada: sem ela não há onde desenhar, e chutar uma
 * posição num mapa de enchente é pior que não desenhar. As leituras são
 * casadas por TÍTULO, que é a chave que a fonte usa e que já liga as duas
 * pontas em todo o resto do projeto.
 */
export function reguasNoMapa(
  estacoes: EstacaoTempoReal[],
  leituras: LeituraDeRegua[],
  agora: Date,
): ReguaNoMapa[] {
  const porTitulo = new Map(leituras.map((l) => [l.titulo, l]))
  const saida: ReguaNoMapa[] = []

  for (const e of estacoes) {
    // Sem filtro de cidade: o Monitor mostra a bacia inteira, e quem tem
    // coordenada entra. Hoje só Itajaí publica a das réguas; quando outra
    // Defesa Civil publicar, ela aparece sem tocar neste arquivo.
    if (typeof e.lat !== 'number' || typeof e.lon !== 'number') continue
    if (e.tipo === 'pluviometro') continue // chuva não é nível de rio

    const leitura = porTitulo.get(e.titulo) ?? null
    const base = {
      codigo: e.codigo ?? '',
      titulo: e.titulo,
      nome: nomeDoLugar(e),
      lon: e.lon,
      lat: e.lat,
      nivel: leitura?.nivel_m ?? null,
      medidoEm: leitura?.medidoEm ?? null,
      cotas: Object.fromEntries(
        Object.entries(e.cotas_m ?? {}).filter(([, v]) => typeof v === 'number'),
      ) as Record<string, number>,
    }

    // A ordem das recusas importa: a da maré vem PRIMEIRO, porque ela vale
    // mesmo com leitura fresca e cota cadastrada — é a única que não some
    // quando o dado melhora.
    if (e.alerta_automatico === false) {
      saida.push({
        ...base,
        faixa: null,
        motivoSemCor:
          e.motivo_sem_alerta ??
          'régua de estuário: a maré cruza a cota sem enchente, então o número aparece e a cor não',
      })
      continue
    }
    const cotas = Object.entries(e.cotas_m ?? {}).filter(([k]) => CHAVES_QUE_PINTAM.has(k))
    if (cotas.length === 0) {
      saida.push({ ...base, faixa: null, motivoSemCor: 'sem cota de acionamento cadastrada' })
      continue
    }
    if (!leitura || leitura.medidoEm === null) {
      saida.push({ ...base, faixa: null, motivoSemCor: 'sem leitura com horário' })
      continue
    }
    if (frescor(idadeMin(leitura.medidoEm, agora)) === 'velha') {
      saida.push({ ...base, faixa: null, motivoSemCor: 'leitura velha demais para dizer a faixa' })
      continue
    }

    const cota = cotaAlcancadaEntre(cotas, leitura.nivel_m)
    const faixa: Faixa =
      cota === null
        ? 'normal'
        : cota.chave === 'monitoramento' ||
            cota.chave === 'atencao' ||
            cota.chave === 'alerta'
          ? (cota.chave as Faixa)
          : cota.chave === 'inundacao'
            ? 'inundacao'
            : 'emergencia'
    saida.push({ ...base, faixa, motivoSemCor: null })
  }
  return saida
}
