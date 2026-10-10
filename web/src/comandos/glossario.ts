/**
 * 11ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): as palavras do rio, para quem não é técnico.
 *
 * Cada verbete diz o que a palavra quer dizer NESTE site, com as regras que as telas já seguem (régua de cada
 * cidade com zero próprio, faixa não é metro, intervalo e não hora exata, leitura velha não é de agora). Nada
 * aqui é conselho: quem diz o que fazer é a Defesa Civil (199).
 */
import { normalizar } from './normalizar'

export interface Verbete {
  termo: string
  texto: string
  /** Outros pedidos que a pessoa pode fazer a partir dele. */
  veja?: string[]
}

const V: Record<string, Verbete> = {
  regua: {
    termo: 'Régua',
    texto:
      'A régua é a escala de metros fixada no rio (ou o sensor que faz o mesmo papel) onde se lê o nível da água. Cada cidade tem a sua, com o zero numa altura própria: 8 m em Blumenau e 8 m em Brusque não são a mesma água. Itajaí tem onze réguas, cada uma com o seu zero.',
    veja: ['o que é o zero da régua?', 'o que é cota?'],
  },
  zero: {
    termo: 'Zero da régua',
    texto:
      'É a marca 0 da régua, escolhida quando ela foi instalada. Não é o fundo do rio nem o nível do mar. Por isso metros de réguas diferentes não se comparam: cada número vale só na régua dele.',
  },
  nivel: {
    termo: 'Nível do rio',
    texto:
      'É a altura da água lida na régua, em metros, contada a partir do zero dela. O site mostra sempre a hora da medição: leitura velha (mais de 3 horas) nunca aparece como o nível de agora.',
  },
  cota: {
    termo: 'Cota',
    texto:
      'Cota é uma marca de altura na régua da cidade que a Defesa Civil usa como referência: cota de atenção, de alerta, de inundação. Quando o rio passa de uma cota, muda a faixa (a cor) da cidade. Cota de rua é o nível da régua em que a fonte diz que a água chega àquela rua, num ponto dela; não diz que a rua inteira alaga.',
    veja: ['quanto falta para a cota em Blumenau?', 'explicar as cores'],
  },
  faixa: {
    termo: 'Faixa',
    texto:
      'Faixa é o trecho entre duas cotas da cidade: abaixo da atenção, monitoramento, atenção, alerta, inundação. No mapa ela vira cor. A cor é a faixa da cidade na régua dela, nunca o metro: cidades da mesma cor não estão no mesmo metro.',
    veja: ['explicar as cores', 'quais cidades estão em alerta?'],
  },
  montante: {
    termo: 'Montante e jusante',
    texto:
      'Montante é rio acima, de onde a água vem; jusante é rio abaixo, para onde ela vai. Rio do Sul fica a montante de Blumenau; Itajaí fica a jusante de Blumenau, na foz.',
    veja: ['o que vem de cima para Blumenau?', 'o que fica a montante de Blumenau?'],
  },
  afluente: {
    termo: 'Afluente',
    texto:
      'Afluente é um rio menor que deságua num maior. O Benedito, de Timbó, deságua no Itajaí-Açu perto de Indaial; o ribeirão Guabiruba, no Itajaí-Mirim perto de Brusque. A cheia de um afluente entra no rio principal; ela não desce pelo rio principal.',
  },
  foz: {
    termo: 'Foz',
    texto:
      'Foz é onde o rio encontra o mar. A do Itajaí-Açu é em Itajaí, que recebe também o Itajaí-Mirim. Ali a maré mexe no nível do rio.',
    veja: ['como está a maré?', 'o pico de Blumenau já passou?'],
  },
  preamar: {
    termo: 'Preamar e baixamar',
    texto:
      'Preamar é a maré alta; baixamar, a maré baixa. Os horários vêm da tábua de maré do porto de Itajaí usada no site (a fonte está escrita na tela da foz), que é previsão astronômica: vento e chuva mudam a maré real. Maré alta não é cheia, mas dificulta o rio de escoar na foz.',
    veja: ['como está a maré?'],
  },
  sizigia: {
    termo: 'Sizígia',
    texto: 'Sizígia é o período de lua cheia ou lua nova, quando as preamares são as mais altas do mês.',
    veja: ['como está a maré?'],
  },
  estuario: {
    termo: 'Estuário',
    texto:
      'Estuário é o trecho final do rio onde a maré entra. Em Itajaí, nas réguas de estuário, a maré sobe e desce mais do que a distância até a cota, mesmo sem enchente. Por isso essas réguas mostram o número, mas não ganham cor.',
  },
  pluviometro: {
    termo: 'Pluviômetro e milímetro de chuva',
    texto:
      'Pluviômetro é o aparelho que mede a chuva acumulada. 1 milímetro de chuva é 1 litro de água em cada metro quadrado. O site mostra o acumulado de 1 h, 12 h e 24 h, como a fonte publica; ela não publica 6 h. Chuva acumulada é medição, não previsão de cheia.',
    veja: ['onde está chovendo mais?'],
  },
  pico: {
    termo: 'Pico e platô',
    texto:
      'Pico é o ponto mais alto do rio numa cheia. Platô é quando o rio fica parado perto do pico por horas. Enquanto o rio sobe, o pico ainda não aconteceu: a última leitura não é o pico.',
    veja: ['o pico de Blumenau já passou?', 'máximo das últimas 24 h em Blumenau'],
  },
  descida: {
    termo: 'Tempo de descida',
    texto:
      'É quanto tempo a cheia levou, em cheias passadas e em estudos, para ir do pico de uma cidade ao pico da cidade de baixo. O site mostra sempre um intervalo ("16–18 h") ou, quando a fonte traz um valor só, "cerca de 10 h", nunca uma hora exata, e só onde há dado; ligação entre cidades não é previsão.',
    veja: ['quanto tempo a cheia leva de Rio do Sul até Blumenau?', 'o que vem de cima para Blumenau?'],
  },
  bruto: {
    termo: 'Nível bruto da rede estadual',
    texto:
      'É a leitura da régua da Defesa Civil de SC numa estação, com zero próprio. Aparece quando não há leitura municipal de agora, em violeta no mapa, e não se compara com as cotas da cidade.',
  },
  barragem: {
    termo: 'Barragem de contenção',
    texto:
      'As barragens do Alto Vale seguram água do rio durante a cheia. Comporta fechada é a barragem segurando água; aberta, soltando. O estado das comportas não diz se a cheia já passou.',
    veja: ['como estão as barragens?'],
  },
  enchente: {
    termo: 'Cheia, enchente, inundação e alagamento',
    texto:
      'Cheia ou enchente é o rio subindo acima do normal. Inundação é quando a água sai do leito e cobre a área ao redor. Alagamento é água acumulada na rua por chuva forte que a drenagem não dá conta: pode acontecer sem o rio subir, e as réguas do rio não o mostram. Enxurrada é a água correndo forte depois de chuva intensa.',
  },
  defesa: {
    termo: 'Defesa Civil e AlertaBlu',
    texto:
      'A Defesa Civil de cada município, a Defesa Civil de SC e, em Blumenau, o AlertaBlu são os sistemas oficiais de alerta. Este site não é: ele mostra medições e referências e remete a eles. Em emergência, 199 (Defesa Civil) ou 193 (Bombeiros).',
  },
}

/** Palavra (sem acento) → verbete. */
const SINONIMOS: Record<string, string> = {
  regua: 'regua', 'regua linimetrica': 'regua', linimetro: 'regua',
  'zero da regua': 'zero', zero: 'zero', 'zero proprio': 'zero',
  nivel: 'nivel', 'nivel do rio': 'nivel',
  cota: 'cota', cotas: 'cota', 'cota de rua': 'cota', 'cota da rua': 'cota', 'cota de atencao': 'cota', 'cota de alerta': 'cota', 'cota de inundacao': 'cota', 'cota de emergencia': 'cota',
  faixa: 'faixa', faixas: 'faixa',
  montante: 'montante', jusante: 'montante', 'a montante': 'montante', 'a jusante': 'montante', 'rio acima': 'montante', 'rio abaixo': 'montante',
  afluente: 'afluente', afluentes: 'afluente',
  foz: 'foz',
  preamar: 'preamar', baixamar: 'preamar', 'mare alta': 'preamar', 'mare baixa': 'preamar',
  sizigia: 'sizigia',
  estuario: 'estuario', 'regua de estuario': 'estuario',
  pluviometro: 'pluviometro', 'milimetro de chuva': 'pluviometro', 'mm de chuva': 'pluviometro', milimetro: 'pluviometro',
  pico: 'pico', plato: 'pico', 'pico da cheia': 'pico',
  'tempo de descida': 'descida', 'tempo de chegada': 'descida', transito: 'descida',
  'nivel bruto': 'bruto', 'rede estadual': 'bruto',
  barragem: 'barragem', barragens: 'barragem', 'barragem de contencao': 'barragem', comporta: 'barragem', comportas: 'barragem',
  enchente: 'enchente', cheia: 'enchente', inundacao: 'enchente', alagamento: 'enchente', enxurrada: 'enchente',
  'defesa civil': 'defesa', alertablu: 'defesa', 'alerta blu': 'defesa',
}

/** O verbete pedido: "o que é cota?", "o que significa jusante", "o que quer dizer sizígia". */
export function verbeteDe(termo: string): Verbete | null {
  const t = normalizar(termo).replace(/^(?:um|uma|o|a|os|as)\s+/, '')
  const chave = SINONIMOS[t]
  return chave ? V[chave]! : null
}

/** "Qual a diferença entre enchente e alagamento?": os dois verbetes, ou um só se forem o mesmo. */
export function textoDoVerbete(vs: Verbete[]): string {
  const unicos = vs.filter((v, i) => vs.indexOf(v) === i)
  return [...unicos.map((v) => `${v.termo}: ${v.texto}`), 'Em emergência, ligue 199.'].join('\n')
}

export function sugestoesDoVerbete(vs: Verbete[]): string[] {
  return [...new Set(vs.flatMap((v) => v.veja ?? []))].slice(0, 3)
}

/** Os termos que o chat explica, para a ajuda e para "que palavras você explica?". */
export const TERMOS = Object.values(V).map((v) => v.termo)
