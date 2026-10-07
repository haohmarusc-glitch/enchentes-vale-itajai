/**
 * 14ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): a linha do tempo da cheia de agora.
 *
 * Quatro perguntas que o morador faz olhando o rio subir, todas respondidas pela série publicada de UMA régua
 * (a janela de ~48 h de `serie.ts`), sem nenhuma conta nova sobre o futuro:
 *  - "quando passou da cota de alerta?": o primeiro ponto da série em que o nível ficou na cota ou acima, depois
 *    de estar abaixo. Se o rio já voltou para baixo, diz isso também;
 *  - "há quanto tempo está em alerta?": desde o último cruzamento, para cima, da cota que acende a faixa de agora;
 *  - "quando começou a subir?": o começo da subida que ainda dura — o último ponto no mínimo do trecho que só sobe
 *    (com 2 cm de tolerância para o ruído do sensor, o mesmo limiar de `tendencia`);
 *  - "quanto subiu nas últimas 6 horas?": o ponto de agora contra o ponto de N horas antes, na mesma régua.
 *
 * As regras das outras respostas de agora continuam: cota só nas cidades em que a faixa sai do cadastro (nunca
 * Gaspar, Ascurra nem Itajaí — `SEM_FRASE_DE_COTA`); série velha é dita como velha; metros de uma régua não se
 * comparam com os de outra. Hora de cruzamento é hora da MEDIÇÃO, com o passo da série: entre duas medições o
 * rio pode ter cruzado antes. Nada aqui é previsão nem conselho; em emergência, 199.
 */
import type { PontoSerie } from '../dados/serie'
import type { DiaDito } from './tipos'
import type { Cidade } from '../dados/tipos'
import { SEM_FRASE_DE_COTA, diaDeBrasilia, horaDeBrasilia } from '../logica/agora'
import { cotasOperacionais } from '../logica/cotasOperacionais'
import { metros, rotuloCota } from '../logica/formato'
import { cotaAlcancadaEntre, frescorDaCidade, idadeMin, textoIdade } from '../logica/tempoReal'

export type PerguntaDaLinha = 'cruzou_cota' | 'ha_quanto_tempo' | 'comecou_a_subir' | 'variacao'

/** O que a pessoa pode dizer no lugar da chave da cota (sem acento, como `normalizar` entrega). */
export const NOMES_DE_COTA: Record<string, string> = {
  monitoramento: 'monitoramento',
  observacao: 'monitoramento',
  atencao: 'atencao',
  alerta: 'alerta',
  prontidao: 'alerta',
  'alerta maximo': 'emergencia',
  emergencia: 'emergencia',
  inundacao: 'inundacao',
  transbordamento: 'inundacao',
}

/** Oscilação de até 2 cm é ruído de sensor, não movimento do rio (o mesmo limiar de `tendencia`). */
const RUIDO_M = 0.02

export const AVISO_LINHA = 'É o que já foi medido, não previsão: o rio pode mudar de rumo. Em emergência, ligue 199.'

const hd = (d: Date) => `${horaDeBrasilia(d)} de ${diaDeBrasilia(d)}`
const sinal = (m: number) => `${m > 0 ? '+' : m < 0 ? '−' : ''}${metros(Math.abs(m))}`
const horas = (min: number) => {
  if (min < 60) return `${Math.round(min)} min`
  const h = Math.floor(min / 60)
  const m = Math.round(min % 60)
  return m ? `${h} h ${m} min` : `${h} h`
}

export interface Cruzamento {
  sentido: 'subiu' | 'desceu'
  /** O primeiro ponto já do outro lado da cota. */
  quando: PontoSerie
  /** O último ponto ainda do lado de antes. */
  antes: PontoSerie
}

/** Todos os cruzamentos de `valor` na série, na ordem do tempo. Igual à cota conta como "na cota ou acima". */
export function cruzamentos(pontos: PontoSerie[], valor: number): Cruzamento[] {
  const saida: Cruzamento[] = []
  for (let i = 1; i < pontos.length; i++) {
    const a = pontos[i - 1]!
    const b = pontos[i]!
    if (a.nivel_m < valor && b.nivel_m >= valor) saida.push({ sentido: 'subiu', quando: b, antes: a })
    else if (a.nivel_m >= valor && b.nivel_m < valor) saida.push({ sentido: 'desceu', quando: b, antes: a })
  }
  return saida
}

/** O passo típico da série, em minutos (mediana dos intervalos), para dizer a precisão da hora de cruzamento. */
export function passoDaSerie(pontos: PontoSerie[]): number | null {
  if (pontos.length < 2) return null
  const passos = pontos.slice(1).map((p, i) => (p.medidoEm.getTime() - pontos[i]!.medidoEm.getTime()) / 60_000).sort((a, b) => a - b)
  return Math.round(passos[Math.floor(passos.length / 2)]!)
}

/**
 * O começo da subida que ainda dura, ou `null` quando o rio não está subindo (o último trecho desce ou está parado).
 * Anda para trás enquanto cada ponto está no máximo 2 cm acima do anterior; no trecho achado, o começo é o ÚLTIMO
 * ponto a 2 cm do mínimo — assim um patamar antes da subida não é contado como subida.
 */
export function inicioDaSubida(pontos: PontoSerie[]): PontoSerie | null {
  if (pontos.length < 2) return null
  const ultimo = pontos[pontos.length - 1]!
  let i = pontos.length - 1
  while (i > 0 && pontos[i - 1]!.nivel_m <= pontos[i]!.nivel_m + RUIDO_M) i--
  const trecho = pontos.slice(i)
  const minimo = Math.min(...trecho.map((p) => p.nivel_m))
  if (ultimo.nivel_m - minimo < RUIDO_M) return null
  let inicio = trecho[0]!
  for (const p of trecho) if (p.nivel_m <= minimo + RUIDO_M) inicio = p
  return inicio === ultimo ? null : inicio
}

/** O ponto medido há `horasAtras` horas (o último até esse instante), ou `null` se a série não chega lá. */
export function pontoHorasAntes(pontos: PontoSerie[], horasAtras: number): PontoSerie | null {
  const ultimo = pontos[pontos.length - 1]
  if (!ultimo) return null
  const alvo = ultimo.medidoEm.getTime() - horasAtras * 3_600_000
  let ref: PontoSerie | null = null
  for (const p of pontos) {
    if (p.medidoEm.getTime() <= alvo) ref = p
    else break
  }
  // Até meio passo ou 20 min de folga: "há 6 h" numa série de 15 em 15 min é o ponto de 6 h ± 15 min.
  if (!ref) {
    const primeiro = pontos[0]!
    if (primeiro.medidoEm.getTime() - alvo <= 20 * 60_000 && primeiro !== ultimo) return primeiro
    return null
  }
  return ref
}

export interface EntradaDaLinha {
  pergunta: PerguntaDaLinha
  cidade: Cidade
  /** Como chamar a régua na resposta ("Blumenau", "Itajaí (DC-05)"). */
  rotulo: string
  pontos: PontoSerie[]
  publicacao: string | null
  agora: Date
  janelaHoras: number | null
  /** A chave da cota pedida (já traduzida por `NOMES_DE_COTA`), quando a pessoa disse uma. */
  cota?: string
  /** As horas de "quanto subiu nas últimas N horas". */
  horas?: number
  /** 19ª: só os cruzamentos de um dia (Brasília): "quando passou da cota ontem?", "e ontem?". */
  dia?: DiaDito
}

const DIA_BR = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit' })
/** A chave do dia em Brasília (AAAA-MM-DD) de um instante. */
export const chaveDoDia = (d: Date) => DIA_BR.format(d)
/** A chave do dia pedido ("ontem" = o dia de Brasília anterior ao de `agora`). */
export function chaveDoDiaDito(dia: DiaDito, agora: Date): string {
  const desloca = dia === 'hoje' ? 0 : dia === 'ontem' ? 1 : 2
  return chaveDoDia(new Date(agora.getTime() - desloca * 24 * 3_600_000))
}
const NOME_DO_DIA: Record<DiaDito, string> = { hoje: 'hoje', ontem: 'ontem', anteontem: 'anteontem' }

function recusaDeCota(cidade: Cidade): string | null {
  if (cidade.id === 'itajai' || !SEM_FRASE_DE_COTA.has(cidade.id)) {
    return cidade.id === 'itajai'
      ? 'Itajaí tem várias réguas, cada uma com as suas cotas e o seu zero: não há "a cota de Itajaí". As réguas de estuário nem ganham cor, porque a maré mexe nelas mais do que a distância até a cota. Para uma régua, peça "quanto subiu nas últimas 6 horas" com ela escolhida no Monitor.'
      : null
  }
  if (cidade.id === 'gaspar') return 'Em Gaspar, a legenda da estação usa "maior que" e deixa 5 m exatos sem faixa definida: o site não marca a hora em que o rio "passou da cota". Peça "quando Gaspar começou a subir?" ou "quanto Gaspar subiu nas últimas 6 horas?".'
  return 'Em Ascurra, a faixa vem do enquadramento da Defesa Civil de SC para a régua da Ponte do Beber (C18), não das cotas do cadastro: o site não marca a hora em que o rio "passou da cota". Peça "quando Ascurra começou a subir?" ou "quanto Ascurra subiu nas últimas 6 horas?".'
}

export function textoLinhaDoTempo(e: EntradaDaLinha): string {
  const { cidade, rotulo, pontos, agora } = e
  const ultimo = pontos[pontos.length - 1]
  if (!ultimo || pontos.length < 2) return `O site não tem série recente da régua de ${rotulo}: sem a sequência de medições, não há linha do tempo.`
  const de = e.publicacao ? ` (publicação ${e.publicacao})` : ''
  const idade = idadeMin(ultimo.medidoEm, agora)
  const velha = frescorDaCidade(idade, cidade.id) === 'velha'
  const rodape = [
    velha ? `A série de ${rotulo} para às ${hd(ultimo.medidoEm)} (${textoIdade(idade)}): depois disso ela não diz nada, e nada aqui descreve o rio de agora.` : '',
    `Tudo na régua de ${rotulo}: não compare com outras cidades. ${AVISO_LINHA}`,
  ].filter(Boolean)
  const janela = e.janelaHoras ? `as ${e.janelaHoras} h publicadas` : 'a janela publicada'
  const passo = passoDaSerie(pontos)
  const precisao = passo ? ` (medição a cada ~${passo} min: o cruzamento pode ter sido até ${passo} min antes)` : ''

  if (e.pergunta === 'variacao') {
    const h = e.horas ?? 6
    const ref = pontoHorasAntes(pontos, h)
    if (!ref) {
      const primeiro = pontos[0]!
      return [
        `A série de ${rotulo}${de} não chega a ${h} h antes da última medição: começa às ${hd(primeiro.medidoEm)} (${metros(primeiro.nivel_m)}) e vai até ${hd(ultimo.medidoEm)} (${metros(ultimo.nivel_m)}), ${sinal(Math.round((ultimo.nivel_m - primeiro.nivel_m) * 100) / 100)} nesse trecho.`,
        ...rodape,
      ].join('\n')
    }
    const cm = Math.round((ultimo.nivel_m - ref.nivel_m) * 100)
    const variacao = Math.abs(cm) < 2 ? 'praticamente parado (menos de 2 cm)' : `${cm > 0 ? 'subiu' : 'baixou'} ${Math.abs(cm) >= 100 ? metros(Math.abs(cm) / 100) : `${Math.abs(cm)} cm`}`
    const max = pontos.filter((p) => p.medidoEm.getTime() >= ref.medidoEm.getTime()).reduce((a, b) => (b.nivel_m > a.nivel_m ? b : a))
    const extra = max !== ultimo && max !== ref && max.nivel_m > Math.max(ultimo.nivel_m, ref.nivel_m) + RUIDO_M ? ` No meio, chegou a ${metros(max.nivel_m)} às ${hd(max.medidoEm)}.` : ''
    return [
      `Régua de ${rotulo}${de}: de ${metros(ref.nivel_m)} às ${hd(ref.medidoEm)} para ${metros(ultimo.nivel_m)} às ${hd(ultimo.medidoEm)} — ${variacao} em ${horas((ultimo.medidoEm.getTime() - ref.medidoEm.getTime()) / 60_000)}.${extra}`,
      ...rodape,
    ].join('\n')
  }

  if (e.pergunta === 'comecou_a_subir') {
    const inicio = inicioDaSubida(pontos)
    if (!inicio) {
      const pico = pontos.reduce((a, b) => (b.nivel_m >= a.nivel_m ? b : a))
      return [
        `A régua de ${rotulo}${de} não está subindo na última medição (${metros(ultimo.nivel_m)} às ${hd(ultimo.medidoEm)}).` +
          (pico !== ultimo && pico.nivel_m > ultimo.nivel_m + RUIDO_M ? ` O ponto mais alto d${janela} foi ${metros(pico.nivel_m)} às ${hd(pico.medidoEm)}; desde então, o rio desceu ${sinal(Math.round((ultimo.nivel_m - pico.nivel_m) * 100) / 100).replace('−', '')}.` : ''),
        ...rodape,
      ].join('\n')
    }
    const subiu = Math.round((ultimo.nivel_m - inicio.nivel_m) * 100) / 100
    const dur = (ultimo.medidoEm.getTime() - inicio.medidoEm.getTime()) / 60_000
    const noComeco = inicio === pontos[0] ? ` A série começa aí: pode ter começado a subir antes d${janela}.` : ''
    return [
      `Régua de ${rotulo}${de}: a subida que ainda dura começou às ${hd(inicio.medidoEm)}, em ${metros(inicio.nivel_m)}. Até ${hd(ultimo.medidoEm)} subiu ${subiu >= 1 ? metros(subiu) : `${Math.round(subiu * 100)} cm`} (${metros(ultimo.nivel_m)}), em ${horas(dur)}${dur >= 60 ? `, ~${Math.round((subiu * 100) / (dur / 60))} cm/h em média` : ''}.${noComeco}`,
      ...rodape,
    ].join('\n')
  }

  // As duas perguntas de cota.
  const recusa = recusaDeCota(cidade)
  if (recusa) return recusa
  const cotas = cotasOperacionais(cidade.cotas_m ?? {})
  if (!cotas.length) return `O cadastro não tem cota de acionamento para a régua de ${rotulo}: não há "passou da cota" nem faixa para contar o tempo.`
  const nomes = cidade.cotas_nomes_na_fonte
  const nomeDa = (chave: string) => rotuloCota(chave, nomes)
  const lista = cotas.map(([k, v]) => `${nomeDa(k)} (${metros(v)})`).join(', ')
  const alcancada = cotaAlcancadaEntre(cotas, ultimo.nivel_m)

  if (e.pergunta === 'ha_quanto_tempo') {
    const pedida = e.cota ? cotas.find(([k]) => k === e.cota) : null
    if (e.cota && !pedida) return `O cadastro de ${rotulo} não tem a cota "${nomeDa(e.cota)}". As cotas são: ${lista}.`
    if (pedida && ultimo.nivel_m < pedida[1]) {
      const c = cruzamentos(pontos, pedida[1])
      const ultimoC = c[c.length - 1]
      return [
        `${rotulo} não está em ${nomeDa(pedida[0])} na última medição: ${metros(ultimo.nivel_m)} às ${hd(ultimo.medidoEm)}, abaixo da cota de ${metros(pedida[1])}.` +
          (ultimoC?.sentido === 'desceu' ? ` Saiu dela às ${hd(ultimoC.quando.medidoEm)}${precisao}.` : c.length ? '' : ` N${janela}, não passou dessa cota.`),
        ...rodape,
      ].join('\n')
    }
    const cota = pedida ?? alcancada
    if (!cota) {
      const primeira = cotas[0]!
      const c = cruzamentos(pontos, primeira[1])
      const ultimoC = c[c.length - 1]
      return [
        `${rotulo} está abaixo de todas as cotas na última medição: ${metros(ultimo.nivel_m)} às ${hd(ultimo.medidoEm)}, e a primeira cota é ${nomeDa(primeira[0])} (${metros(primeira[1])}).` +
          (ultimoC?.sentido === 'desceu' ? ` Voltou para baixo dela às ${hd(ultimoC.quando.medidoEm)}${precisao}.` : ` N${janela}, não passou de nenhuma cota.`),
        ...rodape,
      ].join('\n')
    }
    const [chave, valor] = Array.isArray(cota) ? cota : [cota.chave, cota.valor]
    const c = cruzamentos(pontos, valor)
    const ultimoC = c[c.length - 1]
    if (!ultimoC || ultimoC.sentido !== 'subiu') {
      return [
        `${rotulo} está em ${nomeDa(chave)} (${metros(valor)}) desde antes do começo da série: já estava na cota ou acima às ${hd(pontos[0]!.medidoEm)} (${metros(pontos[0]!.nivel_m)}), então são mais de ${horas((ultimo.medidoEm.getTime() - pontos[0]!.medidoEm.getTime()) / 60_000)}.`,
        ...rodape,
      ].join('\n')
    }
    const dur = (ultimo.medidoEm.getTime() - ultimoC.quando.medidoEm.getTime()) / 60_000
    const antesDesta = c.filter((x) => x !== ultimoC && x.sentido === 'subiu')
    return [
      `${rotulo} está em ${nomeDa(chave)} (${metros(valor)}) há ${horas(dur)}: passou da cota às ${hd(ultimoC.quando.medidoEm)}${precisao}, de ${metros(ultimoC.antes.nivel_m)} para ${metros(ultimoC.quando.nivel_m)}. Agora está em ${metros(ultimo.nivel_m)} (${hd(ultimo.medidoEm)}).` +
        (antesDesta.length ? ` N${janela}, já tinha passado dessa cota ${antesDesta.length === 1 ? 'uma vez' : `${antesDesta.length} vezes`} antes e voltado.` : ''),
      ...rodape,
    ].join('\n')
  }

  // cruzou_cota
  const alvoCota = e.cota ? cotas.find(([k]) => k === e.cota) : alcancada ? cotas.find(([k]) => k === alcancada.chave) : null
  if (e.cota && !alvoCota) return `O cadastro de ${rotulo} não tem a cota "${nomeDa(e.cota)}". As cotas são: ${lista}.`
  if (!alvoCota) {
    // Nenhuma cota pedida e o rio está abaixo de todas: a última que ele cruzou, se cruzou.
    const cruzadas = cotas.map(([k, v]) => ({ k, v, c: cruzamentos(pontos, v) })).filter((x) => x.c.length)
    if (!cruzadas.length) return [`N${janela}, a régua de ${rotulo}${de} não passou de nenhuma cota: está em ${metros(ultimo.nivel_m)} (${hd(ultimo.medidoEm)}), e a primeira cota é ${nomeDa(cotas[0]![0])} (${metros(cotas[0]![1])}).`, ...rodape].join('\n')
    const maisAlta = cruzadas.reduce((a, b) => (b.v > a.v ? b : a))
    const subiu = maisAlta.c.filter((x) => x.sentido === 'subiu').at(-1)
    const desceu = maisAlta.c.filter((x) => x.sentido === 'desceu').at(-1)
    return [
      `N${janela}, a régua de ${rotulo}${de} chegou a passar da cota de ${nomeDa(maisAlta.k)} (${metros(maisAlta.v)})${subiu ? ` às ${hd(subiu.quando.medidoEm)}` : ''}${desceu ? ` e voltou para baixo dela às ${hd(desceu.quando.medidoEm)}` : ''}${precisao}. Agora está em ${metros(ultimo.nivel_m)} (${hd(ultimo.medidoEm)}), abaixo de todas as cotas.`,
      ...rodape,
    ].join('\n')
  }
  const [chave, valor] = alvoCota
  const todos = cruzamentos(pontos, valor)
  if (e.dia) {
    // Só o dia pedido, em Brasília. Fora da janela publicada, diz isso; sem cruzamento no dia, diz o que o rio fez nele.
    const k = chaveDoDiaDito(e.dia, agora)
    const doDia = pontos.filter((p) => chaveDoDia(p.medidoEm) === k)
    const rotuloDia = `${NOME_DO_DIA[e.dia]} (${k.slice(8, 10)}/${k.slice(5, 7)})`
    if (!doDia.length) {
      return [`A série publicada de ${rotulo} vai de ${hd(pontos[0]!.medidoEm)} a ${hd(ultimo.medidoEm)} e não cobre ${rotuloDia}: não dá para dizer se passou da cota nesse dia.`, ...rodape].join('\n')
    }
    const cDia = todos.filter((x) => chaveDoDia(x.quando.medidoEm) === k)
    if (!cDia.length) {
      const min = Math.min(...doDia.map((p) => p.nivel_m))
      const max = Math.max(...doDia.map((p) => p.nivel_m))
      const onde = min >= valor ? `ficou o tempo todo na cota de ${nomeDa(chave)} (${metros(valor)}) ou acima` : `não passou da cota de ${nomeDa(chave)} (${metros(valor)})`
      return [`Nas medições publicadas de ${rotuloDia}, a régua de ${rotulo}${de} ${onde}: ficou entre ${metros(min)} e ${metros(max)}.`, ...rodape].join('\n')
    }
    const frases = cDia.map((x) => `${x.sentido === 'subiu' ? 'passou da cota' : 'voltou para baixo dela'} às ${hd(x.quando.medidoEm)} (de ${metros(x.antes.nivel_m)} para ${metros(x.quando.nivel_m)})`)
    return [`Régua de ${rotulo}${de}, ${rotuloDia}, cota de ${nomeDa(chave)} (${metros(valor)}): ${frases.join('; ')}${precisao}.`, ...rodape].join('\n')
  }
  const c = todos
  if (!c.length) {
    const acima = pontos[0]!.nivel_m >= valor
    return [
      acima
        ? `N${janela}, a régua de ${rotulo}${de} esteve o tempo todo na cota de ${nomeDa(chave)} (${metros(valor)}) ou acima: já estava assim às ${hd(pontos[0]!.medidoEm)} (${metros(pontos[0]!.nivel_m)}), então passou da cota antes do começo da série. Agora: ${metros(ultimo.nivel_m)} (${hd(ultimo.medidoEm)}).`
        : `N${janela}, a régua de ${rotulo}${de} não passou da cota de ${nomeDa(chave)} (${metros(valor)}): o mais alto foi ${metros(Math.max(...pontos.map((p) => p.nivel_m)))}, e agora está em ${metros(ultimo.nivel_m)} (${hd(ultimo.medidoEm)}).`,
      ...rodape,
    ].join('\n')
  }
  const subidas = c.filter((x) => x.sentido === 'subiu')
  const ultimaSubida = subidas[subidas.length - 1]
  const ultimoC = c[c.length - 1]!
  const linhas = [
    ultimaSubida
      ? `Régua de ${rotulo}${de}: passou da cota de ${nomeDa(chave)} (${metros(valor)}) às ${hd(ultimaSubida.quando.medidoEm)}${precisao}, de ${metros(ultimaSubida.antes.nivel_m)} para ${metros(ultimaSubida.quando.nivel_m)}.`
      : `Régua de ${rotulo}${de}: já estava na cota de ${nomeDa(chave)} (${metros(valor)}) ou acima no começo da série (${hd(pontos[0]!.medidoEm)}).`,
    ultimoC.sentido === 'desceu'
      ? `Voltou para baixo dela às ${hd(ultimoC.quando.medidoEm)}${precisao}. Agora está em ${metros(ultimo.nivel_m)} (${hd(ultimo.medidoEm)}).`
      : `Continua na cota ou acima: ${metros(ultimo.nivel_m)} às ${hd(ultimo.medidoEm)}, há ${horas((ultimo.medidoEm.getTime() - ultimoC.quando.medidoEm.getTime()) / 60_000)}.`,
  ]
  if (subidas.length > 1) linhas.push(`N${janela}, cruzou essa cota para cima ${subidas.length} vezes: ${subidas.map((x) => hd(x.quando.medidoEm)).join(', ')}.`)
  return [...linhas, ...rodape].join('\n')
}
