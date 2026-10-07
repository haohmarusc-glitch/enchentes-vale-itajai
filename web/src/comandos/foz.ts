/**
 * 7ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): a foz e o que o mapa quer dizer.
 * Funções puras, com o que as telas já dizem:
 *
 * - "o pico de Blumenau já passou?": o "Hoje" do painel de chegada × maré de Itajaí (`logica/hojeEmItajai.ts`,
 *   a MESMA decisão que a tela usa), com a referência de estudo da JICA e a tábua da Marinha. Enquanto o rio
 *   sobe, a janela é a de "se o pico fosse agora"; janela que já terminou é dita como terminada;
 * - "se o pico de Blumenau for às 22h": a simulação com horário informado (`simularChegada`), como o formulário;
 * - "o que significa a cor laranja?": a legenda do Monitor e `data/faixas.json`, a fonte única dos textos.
 *
 * Nada aqui é previsão de altura nem conselho: a coincidência com a maré não diz se vai alagar.
 */
import faixas from '../../../data/faixas.json'
import type { HojeEmItajai } from '../logica/hojeEmItajai'
import type { ResultadoSimulacao } from '../logica/simulacaoChegada'
import { diaDeBrasilia, horaDeBrasilia } from '../logica/agora'
import { metros } from '../logica/formato'
import { deBrasilia, idadeMin, textoIdade } from '../logica/tempoReal'

const dh = (d: Date) => `${horaDeBrasilia(d)} de ${diaDeBrasilia(d)}`
const alturaTabua = (a: number | null) => (a == null ? 'sem altura na tábua' : `${a.toLocaleString('pt-BR', { maximumFractionDigits: 2 })} m na tábua`)

export interface ReferenciaChegada {
  horas_min: number
  horas_max: number
}

export const AVISO_FOZ =
  'A janela é a referência de estudo da JICA (picos de projeto, sem calibração com cheias observadas), não previsão. A altura da maré é a da tábua da Marinha, não o nível do rio, e vento, chuva local e afluentes não entram na conta. Siga a Defesa Civil de Itajaí; em emergência, ligue 199.'

/** A janela de chegada e as marés dentro dela — o mesmo quadro (`Resultado`) do painel, em texto. */
export function textoJanela(r: ResultadoSimulacao, qual: string): string {
  if ('erro' in r) return r.erro
  const janela = qual ? `janela ${qual}` : 'janela'
  const linhas = [`Janela: de ${dh(r.inicio)} a ${dh(r.fim)} (horário de Brasília).`]
  if (!r.cobertura) {
    linhas.push('A tábua de maré não cobre toda a janela: não dá para concluir se haverá coincidência com a preamar.')
  } else if (r.preamaresDentro > 0) {
    linhas.push(`Há preamar dentro da ${janela}. A coincidência de horários não determina a altura da enchente nem a probabilidade de alagamento.`)
  } else {
    linhas.push(`Nenhum pico de maré está dentro da ${janela}. A maré ainda pode influenciar o escoamento; isso não significa ausência de risco.`)
  }
  const dentro = r.extremos.filter((e) => e.dentro)
  if (dentro.length) linhas.push(`Na janela: ${dentro.map((e) => `${e.tipo === 'preamar' ? 'maré alta' : 'maré baixa'} às ${dh(e.quando)} (${alturaTabua(e.altura)})`).join('; ')}.`)
  return linhas.join('\n')
}

/** "Quanto tempo a água leva de Blumenau até Itajaí?": dito também quando não há pico para pôr na janela. */
const tempoDeDescida = (r: ReferenciaChegada) =>
  `Quando há pico, ele leva de ${r.horas_min} a ${r.horas_max} h de Blumenau até Itajaí, pela referência de estudo da JICA; cada cheia é diferente, não é previsão.`

export function textoChegadaItajai(h: HojeEmItajai, args: { cota: { nome: string; valor: number } | null; referencia: ReferenciaChegada; agora: Date }): string {
  const { referencia, agora } = args
  const ref = `pela referência de estudo (${referencia.horas_min} a ${referencia.horas_max} h)`
  switch (h.tipo) {
    case 'sem-dado':
      return `Sem leitura recente de Blumenau: não dá para dizer se o pico passou. ${tempoDeDescida(referencia)}\nSe a Defesa Civil ou o AlertaBlu informar o horário do pico, peça, por exemplo: "se o pico de Blumenau for às 22h", e eu digo se a janela de chegada pega maré alta. Em emergência, ligue 199.`
    case 'abaixo-da-cota':
      return `Blumenau está em ${metros(h.ultimo.nivel_m)} (medido às ${horaDeBrasilia(h.ultimo.medidoEm)}, ${textoIdade(idadeMin(h.ultimo.medidoEm, agora))})${args.cota ? `, abaixo da cota de ${args.cota.nome} (${metros(args.cota.valor)}), e não passou dela nas últimas 36 h` : ''}: não há pico de cheia descendo agora.\n${tempoDeDescida(referencia)}\nEm Itajaí a maré alta pesa mesmo sem cheia de cima. Em emergência, ligue 199.`
    case 'nao-confirmado':
      return [
        `Pico não confirmado. A maior leitura das últimas 36 h em Blumenau é ${metros(h.pico.nivel_m)}, às ${dh(h.pico.medidoEm)}, e é a primeira da janela: o pico de verdade pode ter sido antes. Agora está em ${metros(h.ultimo.nivel_m)}, descendo.`,
        h.janelaPassou
          ? `Se o pico tivesse sido nessa leitura, ${ref}, teria chegado a Itajaí numa janela que já terminou: ela não diz nada sobre as próximas horas.`
          : `Se o pico tivesse sido nessa leitura, ${ref}, chegaria a Itajaí:`,
        h.janelaPassou ? '' : textoJanela(h.resultado, 'desta hipótese'),
        AVISO_FOZ,
      ]
        .filter(Boolean)
        .join('\n')
    case 'passou':
      return [
        `O pico já passou por Blumenau: ${metros(h.pico.nivel_m)} às ${dh(h.pico.medidoEm)}${h.horasPlato >= 0.5 ? ` (o rio ficou a menos de 5 cm disso de ${dh(h.platoInicio)} até ${dh(h.platoFim)})` : ''}. Agora está em ${metros(h.ultimo.nivel_m)}, descendo.`,
        h.janelaPassou
          ? `${ref[0]!.toUpperCase()}${ref.slice(1)}, o pico teria chegado a Itajaí numa janela que já terminou${'erro' in h.resultado ? '' : `, às ${dh(h.resultado.fim)}`}: ela não diz nada sobre as próximas horas. Para o nível de agora, veja as réguas de Itajaí.`
          : `${ref[0]!.toUpperCase()}${ref.slice(1)}, o pico chegaria a Itajaí:`,
        h.janelaPassou ? '' : textoJanela(h.resultado, ''),
        AVISO_FOZ,
      ]
        .filter(Boolean)
        .join('\n')
    case 'subindo':
    case 'no-alto':
      return [
        h.tipo === 'subindo'
          ? `Blumenau ainda está subindo: ${metros(h.ultimo.nivel_m)} às ${horaDeBrasilia(h.ultimo.medidoEm)}${h.cmh != null ? ` (+${h.cmh} cm/h)` : ''}. O pico ainda não aconteceu, então o horário de chegada a Itajaí ainda não se sabe.`
          : `Blumenau está perto do ponto mais alto (${metros(h.ultimo.nivel_m)} às ${horaDeBrasilia(h.ultimo.medidoEm)}), mas ainda não desceu o bastante para confirmar que o pico passou.`,
        `Se o pico fosse agora, ${ref}, chegaria a Itajaí:`,
        textoJanela(h.resultado, 'deste cenário'),
        'A cada leitura nova de Blumenau esta janela é refeita; enquanto o rio subir, ela anda para frente.',
        AVISO_FOZ,
      ].join('\n')
  }
}

/** "às 22h", "amanhã às 3h": o instante do pico informado, no horário de Brasília. */
export function instanteDoPico(p: { hora: number; minuto?: number; dia?: 'hoje' | 'amanha' | 'ontem' }, agora: Date): Date | null {
  if (p.hora > 23 || (p.minuto ?? 0) > 59) return null
  const hoje = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit' }).format(agora)
  const t = deBrasilia(`${hoje}T${String(p.hora).padStart(2, '0')}:${String(p.minuto ?? 0).padStart(2, '0')}:00`)
  const desloca = p.dia === 'amanha' ? 1 : p.dia === 'ontem' ? -1 : 0
  return new Date(t.getTime() + desloca * 24 * 3_600_000)
}

export function textoSimulacao(pico: Date, r: ResultadoSimulacao, referencia: ReferenciaChegada, agora: Date): string {
  if ('erro' in r) return r.erro
  const passou = r.fim.getTime() < agora.getTime()
  return [
    `Se o pico em Blumenau for às ${dh(pico)}, pela referência de estudo (${referencia.horas_min} a ${referencia.horas_max} h), ${passou ? 'teria chegado' : 'chegaria'} a Itajaí:`,
    textoJanela(r, 'simulada'),
    passou ? 'Essa janela já terminou: ela não diz nada sobre as próximas horas.' : '',
    'O horário do pico é o que você informou (da Defesa Civil, do AlertaBlu ou hipotético): a última leitura do rio não é automaticamente um pico.',
    AVISO_FOZ,
  ]
    .filter(Boolean)
    .join('\n')
}

// ---------------------------------------------------------------- legenda

const F = (faixas as unknown as { faixas: Record<string, { rotulo: string; acao: string }>; disclaimer: string }).faixas
const DISCLAIMER = (faixas as unknown as { disclaimer: string }).disclaimer

export type TemaDaLegenda =
  | 'cores'
  | 'normal'
  | 'monitoramento'
  | 'atencao'
  | 'alerta'
  | 'inundacao'
  | 'sem-dado'
  | 'varias'
  | 'azul'
  | 'violeta'
  | 'tracejado'
  | 'ondas'
  | 'seta'
  | 'regua_mare'

const COR_DA_FAIXA: Record<string, string> = {
  normal: 'verde',
  monitoramento: 'verde-claro',
  atencao: 'amarelo',
  alerta: 'laranja',
  inundacao: 'vermelho',
  'sem-dado': 'cinza',
}

const faixa = (k: string) => `${COR_DA_FAIXA[k] ? `${COR_DA_FAIXA[k][0]!.toUpperCase()}${COR_DA_FAIXA[k].slice(1)} — ` : ''}${k === 'inundacao' ? 'Inundação / Emergência' : F[k]!.rotulo}: ${F[k]!.acao}`

const TEXTOS: Record<Exclude<TemaDaLegenda, 'cores'>, string> = {
  normal: faixa('normal'),
  monitoramento: faixa('monitoramento'),
  atencao: faixa('atencao'),
  alerta: faixa('alerta'),
  inundacao: faixa('inundacao'),
  'sem-dado': `${faixa('sem-dado')} Cinza = sem faixa para afirmar: não é seguro, é sem afirmação. Ribeirões e canais de Itajaí ficam cinza e parados mesmo tendo régua com número, porque são réguas de estuário. Para uma cidade, peça "por que essa régua está cinza?".`,
  varias: `${F.varias!.rotulo}: ${F.varias!.acao} Itajaí tem onze réguas, cada uma com o seu zero; nenhuma cor sozinha vale para a cidade.`,
  azul: 'Azul no mapa tem três sentidos, nenhum deles é faixa de cheia: o mar na foz, colorido pela maré (escala própria); a chuva recente, em mm, nos pluviômetros; e o pino de Itajaí, que tem várias réguas.',
  violeta: 'Violeta é o nível bruto da rede estadual (Defesa Civil de SC), com zero próprio: aparece quando não há fonte municipal e não vira faixa nem se compara com as cotas da cidade.',
  tracejado: 'Trecho tracejado é a faixa estadual: a classificação da própria Defesa Civil de SC, na régua da estação, só onde não há leitura municipal de agora. Não é cota deste site.',
  ondas: 'As ondas indicam apenas o sentido ilustrativo do curso, rumo à foz, com velocidade visual constante. Não representam a velocidade da água, a corrente real (que varia com a maré) nem a chegada da cheia; cinza em movimento não indica nível nem segurança. Peça "pausar as animações" para parar.',
  seta: 'A seta aparece onde os pinos se amontoam: o nome ficou afastado por falta de espaço, e a ponta indica a cidade dele.',
  regua_mare: 'Régua sem faixa (anel sem cor) é régua de estuário em Itajaí: mostra o número, mas não ganha cor, porque a maré cruza a cota sem enchente e uma cor que acende com a maré ensinaria a ignorar a cor.',
}

export function textoLegenda(tema: TemaDaLegenda): string {
  if (tema !== 'cores') return `${TEXTOS[tema]}\n${DISCLAIMER}`
  return [
    'As cores do rio são a faixa de cada cidade na régua dela, do calmo ao grave:',
    ...(['normal', 'monitoramento', 'atencao', 'alerta', 'inundacao', 'sem-dado'] as const).map((k) => `• ${faixa(k)}`),
    `• ${TEXTOS.tracejado}`,
    `• ${TEXTOS.violeta}`,
    `• ${TEXTOS.azul}`,
    DISCLAIMER,
    'O site descreve a faixa e remete à Defesa Civil; não é alerta oficial. Em emergência, ligue 199.',
  ].join('\n')
}
