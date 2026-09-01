/**
 * Leitura de nível em tempo real: idade, frescor e chegada a jusante.
 *
 * A regra que organiza este arquivo: **leitura velha não pode passar por
 * nível atual**. Numa cheia o rio sobe metros em horas; alguém olhando um
 * número de quatro horas atrás e achando que é agora decide errado sobre sair
 * de casa. Por isso a idade aparece sempre, e o cálculo de chegada só roda com
 * leitura fresca.
 */
import type { Cidade, Trecho } from '../dados/tipos'
import { caminho, janelaChegada, type Caminho } from './transito'

/**
 * Até aqui a leitura vale como "agora".
 *
 * Noventa minutos, e não os 45 de antes, por duas razões medidas em campo.
 *
 * A primeira: as fontes não publicam no mesmo ritmo. As estações DC de Itajaí
 * atualizam a cada 15-20 min, mas a estação MKS de Rio do Sul anda quase uma
 * hora atrás delas. Um limite abaixo do ritmo da própria fonte recusa SEMPRE,
 * e recusa justamente na cidade que é o melhor indicador de montante da bacia.
 *
 * A segunda: a janela de chegada é ancorada no horário da MEDIÇÃO, não em
 * "agora" — veja `chegadasSePicoAgora`. Uma leitura de uma hora atrás desloca
 * a janela em uma hora contra um intervalo que já tem três de largura. A idade
 * não distorce os horários; ela só diz o quanto o NÍVEL ainda representa o rio,
 * e para isso a tela mostra a idade sempre.
 *
 * Quando `scripts/auditar.py` tiver algumas semanas de série, dá para trocar
 * este número único pela cadência real de cada estação.
 */
export const MIN_AGORA = 90
/** Daqui em diante o número deixa de servir para decidir qualquer coisa. */
export const MIN_VELHA = 180

export type Frescor = 'agora' | 'atrasada' | 'velha'

/**
 * Converte um horário SEM FUSO, que a Defesa Civil publica em hora de
 * Brasília, para o instante real.
 *
 * Sem isso, quem abrir o site fora do fuso do Brasil veria a idade da leitura
 * deslocada em horas — e a idade é justamente o que diz se dá para confiar no
 * número. `Intl` resolve pelo fuso nomeado, então continua correto mesmo para
 * datas antigas, de quando o Brasil ainda tinha horário de verão.
 */
export function deBrasilia(semFuso: string): Date {
  const comoUtc = new Date(`${semFuso}Z`)
  if (Number.isNaN(comoUtc.getTime())) return comoUtc

  const partes = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Sao_Paulo',
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).formatToParts(comoUtc)

  const valor = (tipo: string) => Number(partes.find((p) => p.type === tipo)?.value ?? '0')
  const emBrasilia = Date.UTC(
    valor('year'),
    valor('month') - 1,
    valor('day'),
    valor('hour') % 24,
    valor('minute'),
    valor('second'),
  )
  return new Date(comoUtc.getTime() - (emBrasilia - comoUtc.getTime()))
}

/** Minutos entre a medição e agora. Negativo vira 0: relógio adiantado não é futuro. */
export function idadeMin(medidoEm: Date, agora: Date): number {
  return Math.max(0, Math.round((agora.getTime() - medidoEm.getTime()) / 60_000))
}

export function frescor(idade: number): Frescor {
  if (idade <= MIN_AGORA) return 'agora'
  if (idade <= MIN_VELHA) return 'atrasada'
  return 'velha'
}

/** `há 12 min`, `há 2 h 05`, `há 3 dias`. */
export function textoIdade(minutos: number): string {
  if (minutos < 1) return 'agora mesmo'
  if (minutos < 60) return `há ${minutos} min`
  const horas = Math.floor(minutos / 60)
  if (horas < 24) {
    const resto = minutos % 60
    return resto === 0 ? `há ${horas} h` : `há ${horas} h ${String(resto).padStart(2, '0')}`
  }
  const dias = Math.floor(horas / 24)
  return dias === 1 ? 'há 1 dia' : `há ${dias} dias`
}

export interface ChegadaPrevista {
  cidade: Cidade
  trecho: Caminho
  inicio: Date
  fim: Date
}

/**
 * Se o pico for AGORA, quando a cheia chega em cada cidade a jusante.
 *
 * O "se" não é retórico: o tempo de descida é medido de pico a pico, e saber
 * que o rio está em 8,20 m não diz que esse é o pico — ele pode subir mais por
 * horas. Esta função responde a uma pergunta condicional, e a tela precisa
 * dizer isso com todas as letras.
 */
export function chegadasSePicoAgora(
  trechos: Trecho[],
  rioId: string,
  cidades: Cidade[],
  origem: Cidade,
  quando: Date,
): ChegadaPrevista[] {
  const indice = cidades.findIndex((c) => c.id === origem.id)
  if (indice < 0) return []

  const saida: ChegadaPrevista[] = []
  for (const cidade of cidades.slice(indice + 1)) {
    const trecho = caminho(trechos, rioId, origem.id, cidade.id)
    if (!trecho) continue
    const { inicio, fim } = janelaChegada(quando, trecho)
    saida.push({ cidade, trecho, inicio, fim })
  }
  return saida
}

/**
 * As janelas saem fora da ordem do rio?
 *
 * A água passa por cada cidade na ordem em que elas aparecem no curso, então a
 * janela de uma cidade nunca deveria começar antes da janela da cidade acima.
 * Quando começa, é porque os trechos de `transito.json` vêm de fontes que não
 * concordam entre si — o hidrograma de projeto da JICA e os modelos acadêmicos
 * dão números que, somados por caminhos diferentes, se cruzam.
 *
 * A tela precisa dizer isso. Empurrar o horário para "consertar" a ordem seria
 * inventar uma precisão que a fonte não tem, e apresentar como sequência algo
 * que os dados não sustentam.
 */
export function foraDeOrdem(chegadas: ChegadaPrevista[]): boolean {
  for (let i = 1; i < chegadas.length; i++) {
    if (chegadas[i]!.inicio < chegadas[i - 1]!.inicio) return true
  }
  return false
}

/** A cota mais baixa da cidade — a primeira que importa quando o rio sobe. */
/**
 * A cota MAIS ALTA que o nível já passou — e não a primeira da lista.
 *
 * `primeiraCota` responde "a partir de quando é cheia aqui", que é a pergunta
 * certa para um painel condicional. Para um nível ao vivo ela é a resposta
 * errada: com Blumenau em 12,00 m, dizer "acima da cota de atenção" (4,50 m) é
 * verdade e é a frase mais fraca possível no momento em que se precisa da mais
 * forte — a cidade está dois patamares acima disso.
 *
 * Devolve nulo quando o nível não passou nenhuma: aí não há o que anunciar.
 */
export function cotaAlcancada(
  cidade: Cidade,
  nivel: number,
): { chave: string; valor: number } | null {
  return cotaAlcancadaEntre(Object.entries(cidade.cotas_m), nivel)
}

/**
 * A cota mais alta alcançada, a partir de uma lista de cotas solta.
 *
 * Existe para a cidade de VÁRIAS réguas: cada uma tem as suas, e comparar o
 * nível de uma com a cota da cidade — ou com a de outra régua — é o erro que
 * este projeto recusa. Em Itajaí a DC-10 usa 8/9/10 m enquanto a cidade tem
 * outras cotas: o mesmo 6,75 m seria "abaixo de tudo" numa e alarme na outra.
 */
export function cotaAlcancadaEntre(
  cotas: [string, unknown][],
  nivel: number,
): { chave: string; valor: number } | null {
  let maior: { chave: string; valor: number } | null = null
  for (const [chave, valor] of cotas) {
    if (typeof valor !== 'number' || !Number.isFinite(valor)) continue
    if (nivel < valor) continue
    if (maior === null || valor > maior.valor) maior = { chave, valor }
  }
  return maior
}

export function primeiraCota(cidade: Cidade): { chave: string; valor: number } | null {
  const ordem = ['atencao', 'alerta', 'emergencia', 'inundacao', 'inundacao_historica']
  for (const chave of ordem) {
    const valor = cidade.cotas_m[chave]
    if (typeof valor === 'number') return { chave, valor }
  }
  const entradas = Object.entries(cidade.cotas_m)
  if (entradas.length === 0) return null
  const menor = entradas.reduce((a, b) => (b[1] < a[1] ? b : a))
  return { chave: menor[0], valor: menor[1] }
}

/**
 * A faixa de perigo de uma cidade AGORA — a cor do mapa, no espírito do
 * Kikikuru (o mapa de risco da agência meteorológica do Japão), adaptada à
 * REGRA BLOQUEANTE deste projeto.
 *
 * A cor representa a FAIXA da própria cidade (a cota mais alta que o nível dela
 * cruzou, na régua dela), NUNCA o metro absoluto: duas cidades em "alerta"
 * podem ambas ser laranja, e isso é comparar faixa, não metro. O que a regra
 * proíbe — comparar metros entre cidades — continua proibido.
 *
 * Três estados NÃO recebem cor de nível, e o mais importante é o primeiro:
 *  - sem cota, ou sem leitura, ou leitura VELHA → `sem-dado`. Nunca verde:
 *    verde lê-se como "seguro", e não sabemos disso. É o `発表なし` (sem
 *    informação) que o próprio Kikikuru distingue do estado de normalidade.
 *  - cidade de várias réguas (a foz, Itajaí) → `varias`: pintar a foz de uma
 *    cor só seria eleger uma régua, o que a tela recusa em todo lugar.
 */
export type Faixa =
  | 'normal'
  | 'atencao'
  | 'alerta'
  | 'inundacao'
  | 'emergencia'
  | 'sem-dado'
  | 'varias'

export function faixaDaCidade(
  cidade: Cidade,
  aoVivo: { nivel_m: number; medidoEm: Date | null } | null,
  temVariasReguas: boolean,
  agora: Date,
): Faixa {
  if (temVariasReguas) return 'varias'
  if (Object.keys(cidade.cotas_m).length === 0) return 'sem-dado'
  if (!aoVivo || !aoVivo.medidoEm) return 'sem-dado'
  // Leitura velha não pinta: um número de horas atrás não diz a faixa de agora,
  // e uma cor forte sobre dado velho é a mentira mais perigosa da tela.
  if (frescor(idadeMin(aoVivo.medidoEm, agora)) === 'velha') return 'sem-dado'
  const cota = cotaAlcancada(cidade, aoVivo.nivel_m)
  if (cota === null) return 'normal'
  if (cota.chave === 'atencao' || cota.chave === 'alerta') return cota.chave
  // 'inundacao', 'emergencia' e qualquer cota de topo caem na faixa vermelha.
  return cota.chave === 'inundacao' ? 'inundacao' : 'emergencia'
}
