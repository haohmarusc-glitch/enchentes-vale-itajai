/**
 * 5ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): o tempo e a bacia — chuva, barragens, maré
 * e a fonte de cada leitura. Funções puras, com as regras que as telas já seguem:
 *
 * - chuva: só pluviômetro com leitura que não é velha; as janelas que a fonte publica (1 h e 24 h aqui; ela não
 *   publica 6 h); chuva acumulada não é previsão de cheia;
 * - barragens: o estado das comportas e o percentual de uso COMO A FONTE PUBLICA. Nunca o nível da barragem em
 *   metros (zero próprio, a 339–370 m de altitude) e nunca um veredito sobre a cheia (`dados/barragens.ts`);
 * - maré: a tábua da Marinha para o porto de Itajaí (previsão astronômica). Maré alta não é cheia; ela dificulta
 *   o escoamento do rio na foz;
 * - fonte: a estação e a hora da leitura, e as fontes que o cadastro lista para a cidade.
 */
import type { Barragem } from '../dados/barragens'
import type { ChuvaAoVivo, LeituraAoVivo } from '../dados/tempoReal'
import type { BrutoEstadual } from '../dados/nivelSc'
import type { TabuaMare } from '../dados/tipos'
import { diaDeBrasilia, horaDeBrasilia } from '../logica/agora'
import { chuvaDaCidade, textoFaixa } from '../logica/chuva'
import { metros } from '../logica/formato'
import { estadoMareAgora, regimeMare } from '../logica/mare'
import { rotuloComportas } from '../logica/barragensNoMapa'
import { deBrasilia, frescorDaCidade, idadeMin, textoIdade } from '../logica/tempoReal'
import type { Catalogo } from './tipos'

const quando = (d: Date, agora: Date) => `às ${horaDeBrasilia(d)} de ${diaDeBrasilia(d)} (${textoIdade(idadeMin(d, agora))})`

// ---------------------------------------------------------------- chuva

const MAX_CIDADES_CHUVA = 6

export function textoChuvaAgora(chuva: ChuvaAoVivo[], chuvaOk: boolean, cat: Catalogo, agora: Date): string {
  if (!chuvaOk) return 'Não consegui buscar a chuva agora. Em emergência, ligue 199.'
  const linhas: { nome: string; h1: number; h24: number; texto: string }[] = []
  let semLeituraRecente = 0
  for (const c of cat.cidades) {
    const r = chuvaDaCidade(chuva, c.id)
    if (!r || !r.pluviometros) continue
    if (!r.medidoEm || frescorDaCidade(idadeMin(r.medidoEm, agora), c.id) === 'velha') {
      semLeituraRecente++
      continue
    }
    const h1 = r.porJanela.h1
    const h24 = r.porJanela.h24
    const partes = [h1 ? `1 h: ${textoFaixa(h1)}` : null, h24 ? `24 h: ${textoFaixa(h24)}` : null].filter(Boolean)
    if (!partes.length) continue
    const quantos = r.pluviometros === 1 ? '1 pluviômetro' : `${r.pluviometros} pluviômetros`
    linhas.push({ nome: c.nome, h1: h1?.maior ?? 0, h24: h24?.maior ?? 0, texto: `${c.nome}: ${partes.join(' · ')} (${quantos}, até ${horaDeBrasilia(r.medidoEm)})` })
  }
  if (!linhas.length) {
    return semLeituraRecente
      ? 'Nenhum pluviômetro das cidades do site tem leitura recente agora: não dá para dizer onde chove.'
      : 'O site não recebeu leitura de pluviômetro das cidades da bacia nesta coleta.'
  }
  linhas.sort((a, b) => b.h1 - a.h1 || b.h24 - a.h24)
  const chovendo = linhas.filter((l) => l.h1 > 0)
  const topo = (chovendo.length ? chovendo : [...linhas].sort((a, b) => b.h24 - a.h24)).slice(0, MAX_CIDADES_CHUVA)
  const cabeca = chovendo.length
    ? `Onde mais choveu na última hora, entre as cidades com pluviômetro de leitura recente (${linhas.length}):`
    : linhas.some((l) => l.h24 > 0)
      ? `Nenhum pluviômetro com leitura recente marcou chuva na última hora. Em 24 h, o acumulado maior foi em:`
      : `Nenhum pluviômetro com leitura recente marcou chuva na última hora nem em 24 h (${linhas.length} cidades com leitura).`
  const resto = chovendo.length || linhas.some((l) => l.h24 > 0) ? `\n• ${topo.map((l) => l.texto).join('\n• ')}` : ''
  return [
    cabeca + resto,
    semLeituraRecente ? `${semLeituraRecente} cidade(s) com pluviômetro ficaram de fora por leitura velha.` : '',
    'Acumulado medido, não previsão: chuva forte aqui não quer dizer cheia aqui, e a cheia de baixo depende da chuva de cima. A fonte não publica 6 h.',
  ]
    .filter(Boolean)
    .join('\n')
}

// ---------------------------------------------------------------- barragens

/** Leitura de barragem com mais que isto já pode ter mudado (mesmo corte do mapa, `FRESCA_MIN`). */
const BARRAGEM_FRESCA_MIN = 60

export function textoBarragens(barragens: ReadonlyMap<string, Barragem>, agora: Date): string {
  if (barragens.size === 0) return 'Não consegui buscar o estado das barragens agora.'
  const linhas = [...barragens.values()]
    .sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'))
    .map((b) => {
      const uso = b.percentUso != null ? ` · ${b.percentUso.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}% de uso do reservatório, como a fonte publica` : ''
      const hora = b.medidoEm ? `, ${quando(b.medidoEm, agora)}` : ', sem horário publicado'
      const velha = !b.medidoEm || idadeMin(b.medidoEm, agora) > BARRAGEM_FRESCA_MIN ? ' — pode ter mudado desde então' : ''
      return `${b.nome}: comportas ${rotuloComportas(b)}${uso}${hora}${velha}.`
    })
  return [
    `Barragens de contenção do Alto Vale:\n• ${linhas.join('\n• ')}`,
    'Comporta fechada é a barragem segurando água; aberta, soltando. O estado das comportas não diz se a cheia já passou: isso é a tendência do rio, na página da cidade.',
    'O nível da barragem em metros não aparece de propósito: a régua dela tem zero próprio e não se compara com a régua das cidades.',
  ].join('\n')
}

// ---------------------------------------------------------------- maré

export function textoMare(tabua: TabuaMare, agora: Date): string {
  const para = (e: { quando: string; altura_m?: number }) => ({ quando: deBrasilia(e.quando), ...(e.altura_m != null ? { altura_m: e.altura_m } : {}) })
  const pre = tabua.preamares.map(para)
  const bai = tabua.baixamares.map(para)
  const m = estadoMareAgora(pre, bai, agora)
  if (m.estado === 'sem-dado') {
    return 'A tábua de maré do site não cobre este horário, então não digo se a maré sobe ou desce agora. A tábua oficial é a da Marinha (porto de Itajaí).'
  }
  const proximaPre = pre.find((p) => p.quando.getTime() > agora.getTime())
  const proximaBai = bai.find((p) => p.quando.getTime() > agora.getTime())
  const alt = (a?: number) => (a != null ? ` (${metros(a)} na tábua)` : '')
  const regime = regimeMare(agora)
  return [
    `Pela tábua de maré da Marinha para o porto de Itajaí, a maré está ${m.estado === 'subindo' ? 'subindo (enchente)' : 'baixando (vazante)'} agora.`,
    [
      proximaPre ? `Próxima preamar: ${horaDeBrasilia(proximaPre.quando)} de ${diaDeBrasilia(proximaPre.quando)}${alt(proximaPre.altura_m)}.` : '',
      proximaBai ? `Próxima baixamar: ${horaDeBrasilia(proximaBai.quando)} de ${diaDeBrasilia(proximaBai.quando)}${alt(proximaBai.altura_m)}.` : '',
    ].filter(Boolean).join(' '),
    regime === 'sizigia' ? 'Período de sizígia (lua cheia ou nova): as preamares são as mais altas do mês.' : '',
    'É previsão astronômica da tábua, não medição: vento e chuva mudam a maré real. Maré alta não é cheia, mas dificulta o escoamento do rio na foz.',
  ]
    .filter(Boolean)
    .join('\n')
}

// ---------------------------------------------------------------- fonte da leitura

export function textoFonteDaLeitura(args: {
  nome: string
  leituras: LeituraAoVivo[]
  estadual: BrutoEstadual | null
  fontesCadastradas: string[]
  agora: Date
}): string {
  const { nome, agora } = args
  const linhas: string[] = []
  if (args.leituras.length) {
    const porEstacao = args.leituras
      .slice(0, 12)
      .map((l) => `${l.estacao}${l.resgateDe ? ` (resgate da "${l.resgateDe}")` : ''}: ${l.medidoEm ? `medida ${quando(l.medidoEm, agora)}` : 'sem horário publicado'}`)
    linhas.push(`As leituras municipais de ${nome} nesta coleta vêm de:\n• ${porEstacao.join('\n• ')}`)
  } else {
    linhas.push(`O site não recebeu leitura municipal de ${nome} nesta coleta.`)
  }
  if (args.estadual) {
    linhas.push(
      `Rede da Defesa Civil de SC: ${args.estadual.estacao}${args.estadual.codigo ? ` (${args.estadual.codigo})` : ''}, ${args.estadual.medidoEm ? `medida ${quando(args.estadual.medidoEm, agora)}` : 'sem horário publicado'}. Zero próprio: não se compara com as cotas da cidade.`,
    )
  }
  if (args.fontesCadastradas.length) linhas.push(`Fontes de tempo real cadastradas para ${nome}:\n• ${args.fontesCadastradas.join('\n• ')}`)
  linhas.push('A hora é a da medição, não a da coleta. A lista completa, com as cotas e o histórico, está na aba Fontes da cidade.')
  return linhas.join('\n')
}

// ---------------------------------------------------------------- reprodução

/** "às 14h", "às 14:30", "há 3 horas" → o instante pedido, no passado. Hora sem data: a última vez que foi aquela hora. */
export function instantePedido(p: { hora?: number; minuto?: number; horasAtras?: number }, agora: Date): Date | null {
  if (p.horasAtras != null) return new Date(agora.getTime() - p.horasAtras * 3_600_000)
  if (p.hora == null || p.hora > 23 || (p.minuto ?? 0) > 59) return null
  // A hora é de Brasília: monta o instante de hoje nessa hora e, se ainda não chegou, usa o de ontem.
  const hoje = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit' }).format(agora)
  const hh = String(p.hora).padStart(2, '0')
  const mm = String(p.minuto ?? 0).padStart(2, '0')
  let t = deBrasilia(`${hoje}T${hh}:${mm}:00`)
  if (t.getTime() > agora.getTime()) t = new Date(t.getTime() - 24 * 3_600_000)
  return t
}
