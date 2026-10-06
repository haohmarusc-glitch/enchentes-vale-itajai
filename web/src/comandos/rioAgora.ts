/**
 * 6ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): o rio agora, de cima a baixo. Funções puras,
 * com as contas que as telas já fazem — nada é calculado de novo aqui:
 *
 * - "quanto falta para a cota": a frase do cartão "Agora" (`situacaoNasCotas`), com as mesmas recusas: só leitura
 *   de agora, nunca em Gaspar ("maior que"), Ascurra (C18) nem Itajaí (várias réguas);
 * - "está subindo ou baixando": a seta do cartão (D7, `tendenciaDaLeitura`): só quando o último ponto da série É a
 *   leitura mostrada e é de agora;
 * - "máximo das últimas 24 h": a série publicada de UMA régua, com a hora de cada ponto;
 * - "quais cidades estão em alerta": a faixa de cada cidade NA RÉGUA DELA (mesma faixa não é mesmo metro); a faixa
 *   da Defesa Civil de SC aparece à parte, só onde a municipal não diz nada de agora;
 * - "o que vem de cima": as cidades acima pela árvore do cadastro, com a leitura de cada uma e o tempo de descida
 *   em intervalo (`caminho`, o mesmo da tela). Ligação não é previsão.
 *
 * Toda resposta é medição, nunca previsão nem conselho; a barreira do presente (199) continua valendo.
 */
import faixas from '../../../data/faixas.json'
import type { Cidade, Trecho, TrechoExperimental } from '../dados/tipos'
import { tendencia as tendenciaDaSerie, type PontoSerie } from '../dados/serie'
import type { EstadoDaCidade } from '../dados/usarAoVivo'
import { diaDeBrasilia, distancia, horaDeBrasilia, rotuloDaFaixa, situacaoNasCotas, tendenciaDaLeitura, textoTendencia } from '../logica/agora'
import { metros } from '../logica/formato'
import type { ReguaNoMapa } from '../logica/reguasNoMapa'
import { frescorDaCidade, idadeMin, textoIdade, type Faixa } from '../logica/tempoReal'
import { caminho, faixaHoras, trechoEmEstudo } from '../logica/transito'
import type { Catalogo } from './tipos'

const ROTULO = (faixas as unknown as { faixas: Record<string, { rotulo: string }> }).faixas
const ROTULO_ESTADUAL: Record<string, string> = { normal: 'Normal', atencao: 'Atenção', alerta: 'Alerta', emergencia: 'Emergência' }

/** As faixas acima de "abaixo da atenção", da mais alta para a mais baixa. */
export const FAIXAS_ACIMA_DO_NORMAL: readonly Faixa[] = ['emergencia', 'inundacao', 'alerta', 'atencao', 'monitoramento']

const quando = (d: Date, agora: Date) => `às ${horaDeBrasilia(d)} de ${diaDeBrasilia(d)} (${textoIdade(idadeMin(d, agora))})`
const sinal = (m: number) => `${m > 0 ? '+' : m < 0 ? '−' : ''}${metros(Math.abs(m))}`

export const AVISO_MEDICAO = 'É medição, não previsão: não diz se nem quando o rio chega a uma cota. Em emergência, ligue 199.'

// ---------------------------------------------------------------- quanto falta

export function textoQuantoFalta(cidade: Cidade, e: EstadoDaCidade, agora: Date): string {
  const nome = cidade.nome
  if (e.varias || cidade.id === 'itajai') {
    return `${nome} tem várias réguas, cada uma com as suas cotas e o seu zero: não há "quanto falta" para a cidade. As réguas de estuário nem ganham cor, porque a maré mexe nelas mais do que a distância até a cota. Cada régua está na página de ${nome}.`
  }
  if (cidade.id === 'gaspar') {
    return `Em Gaspar, a legenda da estação usa "maior que" e deixa 5 m exatos sem faixa definida: o site não faz a conta de quanto falta, só mostra a faixa. Peça "como está Gaspar?".`
  }
  if (cidade.id === 'ascurra') {
    return `Em Ascurra, a faixa vem do enquadramento da Defesa Civil de SC para a régua da Ponte do Beber (C18), não das cotas do cadastro: o site não faz a conta de quanto falta, para não pôr duas escalas na mesma tela. Peça "como está Ascurra?".`
  }
  const l = e.leitura
  if (!l || !l.medidoEm || !Number.isFinite(l.nivel_m)) {
    return `O site não tem leitura da régua de ${nome} nesta coleta: sem número, não há conta.`
  }
  if (frescorDaCidade(idadeMin(l.medidoEm, agora), cidade.id) !== 'agora') {
    return [
      `A última leitura da régua de ${nome} é de ${horaDeBrasilia(l.medidoEm)} de ${diaDeBrasilia(l.medidoEm)} (${textoIdade(idadeMin(l.medidoEm, agora))}): a conta de quanto falta só sai com leitura de agora, para não descrever o rio de horas atrás como se fosse o de agora.`,
      e.estadual?.medidoEm && frescorDaCidade(idadeMin(e.estadual.medidoEm, agora), cidade.id) !== 'velha'
        ? `A rede da Defesa Civil de SC tem leitura mais nova, mas é outra régua, de zero próprio: não se compara com as cotas de ${nome}.`
        : '',
    ]
      .filter(Boolean)
      .join('\n')
  }
  const s = situacaoNasCotas(cidade, l, agora)
  if (!s) return `O cadastro não tem cota para a régua de ${nome}: não há conta de quanto falta.`
  const frase = [
    s.acima
      ? s.acima.cm === 0
        ? `Está na cota de ${s.acima.nome} (${metros(s.acima.valor)}).`
        : `Está ${distancia(s.acima.cm / 100)} acima da cota de ${s.acima.nome} (${metros(s.acima.valor)}).`
      : '',
    s.proxima ? `Faltam ${distancia(s.proxima.faltam)} para a cota de ${s.proxima.nome} (${metros(s.proxima.valor)}).` : `Já passou da cota mais alta do cadastro.`,
  ]
    .filter(Boolean)
    .join(' ')
  return [
    `Régua de ${nome}: ${metros(l.nivel_m)}, medido ${quando(l.medidoEm, agora)}.`,
    frase,
    `Distância na régua de ${nome}, que tem zero próprio. ${AVISO_MEDICAO}`,
  ].join('\n')
}

// ---------------------------------------------------------------- subindo ou baixando

export function textoSubindoOuBaixando(cidade: Cidade, e: EstadoDaCidade, agora: Date): string {
  const nome = cidade.nome
  if (e.varias || cidade.id === 'itajai') {
    return `${nome} tem várias réguas, cada uma com o seu zero: a tendência é de uma régua só. Escolha uma no Monitor e peça "o que mudou na última hora?", ou veja as réguas lado a lado.`
  }
  const l = e.leitura
  if (!l || !l.medidoEm) return `O site não tem leitura da régua de ${nome} nesta coleta: não digo se o rio sobe ou desce.`
  const t = tendenciaDaLeitura(e.serie, l, agora)
  if (t) {
    const seta = t.rotulo === 'subindo' ? '▲ ' : t.rotulo === 'descendo' ? '▼ ' : ''
    return [
      `Régua de ${nome}: ${seta}${textoTendencia(t)} na última hora medida, até ${horaDeBrasilia(l.medidoEm)} (${metros(l.nivel_m)}).`,
      `É o que já foi medido, não previsão: o rio pode mudar de rumo. Em emergência, ligue 199.`,
    ].join('\n')
  }
  if (frescorDaCidade(idadeMin(l.medidoEm, agora), cidade.id) !== 'agora') {
    const subia = tendenciaDaSerie(e.serie)?.rotulo === 'subindo'
    return [
      `A última leitura da régua de ${nome} é de ${horaDeBrasilia(l.medidoEm)} de ${diaDeBrasilia(l.medidoEm)} (${textoIdade(idadeMin(l.medidoEm, agora))}): não digo se o rio sobe ou desce agora.`,
      subia ? 'Quando foi medido, o rio vinha subindo: agora pode estar mais alto.' : '',
    ]
      .filter(Boolean)
      .join('\n')
  }
  return `A série recente de ${nome} não chega até a leitura de ${horaDeBrasilia(l.medidoEm)}, então não digo a tendência (no cartão "Agora" a seta some pelo mesmo motivo). Peça "o que mudou na última hora em ${nome}?".`
}

// ---------------------------------------------------------------- máximo das últimas 24 h

export function textoMaximo24h(args: { nome: string; cidadeId: string; pontos: PontoSerie[]; publicacao: string | null; agora: Date }): string {
  const { nome, agora } = args
  const desde = agora.getTime() - 24 * 3_600_000
  const pts = args.pontos.filter((p) => Number.isFinite(p.nivel_m) && p.medidoEm.getTime() >= desde && p.medidoEm.getTime() <= agora.getTime() + 60_000)
  if (pts.length < 2) {
    return `A série publicada de ${nome} não tem pontos suficientes nas últimas 24 h para dizer máximo e mínimo.`
  }
  const max = pts.reduce((a, b) => (b.nivel_m > a.nivel_m ? b : a))
  const min = pts.reduce((a, b) => (b.nivel_m < a.nivel_m ? b : a))
  const primeiro = pts[0]!
  const ultimo = pts[pts.length - 1]!
  const hd = (d: Date) => `${horaDeBrasilia(d)} de ${diaDeBrasilia(d)}`
  const linhas = [
    `Últimas 24 h da série de ${nome}${args.publicacao ? ` (${args.publicacao})` : ''}, de ${hd(primeiro.medidoEm)} a ${hd(ultimo.medidoEm)}, ${pts.length} pontos:`,
    `• máximo: ${metros(max.nivel_m)} às ${hd(max.medidoEm)};`,
    `• mínimo: ${metros(min.nivel_m)} às ${hd(min.medidoEm)};`,
    `• do primeiro ao último ponto: ${sinal(Math.round((ultimo.nivel_m - primeiro.nivel_m) * 100) / 100)}.`,
  ]
  if (frescorDaCidade(idadeMin(ultimo.medidoEm, agora), args.cidadeId) === 'velha') {
    linhas.push(`O último ponto é de ${textoIdade(idadeMin(ultimo.medidoEm, agora))}: depois dele a série não diz nada.`)
  }
  linhas.push(`Tudo na régua de ${nome}: não compare com outras cidades. É o que já foi medido, não previsão.`)
  return linhas.join('\n')
}

// ---------------------------------------------------------------- panorama da bacia

export interface CidadeAgora {
  cidade: Cidade
  estado: EstadoDaCidade
}

export function textoPanorama(cidades: CidadeAgora[], reguas: ReguaNoMapa[], agora: Date): string {
  const porFaixa = new Map<Faixa, string[]>()
  const abaixo: string[] = []
  const estaduais: { texto: string; ordem: number }[] = []
  const hora = (d: Date) => `às ${horaDeBrasilia(d)}, ${textoIdade(idadeMin(d, agora))}`
  const semCor: string[] = []
  for (const { cidade, estado: e } of cidades) {
    if (e.varias || cidade.id === 'itajai') continue
    const f = e.faixa
    if (f !== 'sem-dado' && f !== 'varias' && e.leitura?.medidoEm) {
      if (f === 'normal') {
        abaixo.push(cidade.nome)
        continue
      }
      const l = e.leitura
      const lista = porFaixa.get(f) ?? []
      lista.push(`${cidade.nome} (${rotuloDaFaixa(f, cidade, ROTULO[f]?.rotulo ?? f)}: ${metros(l.nivel_m)} ${hora(l.medidoEm!)})`)
      porFaixa.set(f, lista)
    } else if (e.faixaEstadual) {
      const i = FAIXAS_ACIMA_DO_NORMAL.indexOf(e.faixaEstadual)
      estaduais.push({ texto: `${cidade.nome}: ${ROTULO_ESTADUAL[e.faixaEstadual] ?? e.faixaEstadual}`, ordem: i < 0 ? FAIXAS_ACIMA_DO_NORMAL.length : i })
    } else {
      semCor.push(cidade.nome)
    }
  }
  const linhas: string[] = ['Faixa de cada cidade agora, na régua dela (mesma faixa não é mesmo metro):']
  let algumaAcima = false
  for (const f of FAIXAS_ACIMA_DO_NORMAL) {
    const lista = porFaixa.get(f)
    if (!lista?.length) continue
    algumaAcima = true
    linhas.push(`• ${ROTULO[f]?.rotulo ?? f}: ${lista.join('; ')}`)
  }
  const dc = reguas.filter((r) => r.cidade === 'itajai')
  const dcAcima = dc.filter((r) => r.faixa && FAIXAS_ACIMA_DO_NORMAL.includes(r.faixa))
  const estadualAcima = estaduais.some((x) => x.ordem < FAIXAS_ACIMA_DO_NORMAL.length)
  if (!algumaAcima && !dcAcima.length) {
    linhas.push('• Nenhuma cidade com leitura municipal de agora está acima de "Abaixo da atenção".')
  }
  if (abaixo.length) linhas.push(`Abaixo da atenção (${abaixo.length}): ${abaixo.join(', ')}.`)
  if (dc.length) {
    linhas.push(
      dcAcima.length
        ? `Itajaí, por régua: ${dcAcima.map((r) => `${r.codigo} · ${r.nome} (${ROTULO[r.faixa!]?.rotulo ?? r.faixa}: ${r.nivel != null ? metros(r.nivel) : 'sem número'}${r.medidoEm ? ` ${hora(r.medidoEm)}` : ''})`).join('; ')}.`
        : `Itajaí: nenhuma das réguas com cor está acima de "Abaixo da atenção" (as de estuário não ganham cor, por causa da maré).`,
    )
  }
  if (estaduais.length) {
    const lista = [...estaduais].sort((a, b) => a.ordem - b.ordem).map((x) => x.texto)
    linhas.push(`Faixa publicada pela Defesa Civil de SC, onde não há leitura municipal de agora (régua estadual, zero próprio): ${lista.join('; ')}.`)
  }
  if (semCor.length) linhas.push(`Sem cor agora, por falta de leitura de agora ou de cota de acionamento (${semCor.length}): ${semCor.join(', ')}.`)
  linhas.push(
    !algumaAcima && !dcAcima.length && !estadualAcima
      ? 'Faixa baixa no rio não quer dizer que não há alagamento: ribeirão e enxurrada urbana não aparecem nas réguas. Não é alerta oficial; siga a Defesa Civil e, em emergência, ligue 199.'
      : 'Não é alerta oficial: siga a Defesa Civil de cada cidade e, em emergência, ligue 199.',
  )
  return linhas.join('\n')
}

// ---------------------------------------------------------------- o que vem de cima

export const AVISO_DE_CIMA =
  'Ligação não é previsão: a cheia de cima não chega igual aqui, e o tempo é o que cheias passadas levaram para descer (sempre um intervalo, nunca hora exata). Cada número vale na régua da sua cidade: não compare metros entre cidades. Em emergência, ligue 199.'

/** "5,20 m (Atenção, na régua de Rio do Sul), ▲ subindo 12 cm/h, medido às 15:00 (há 10 min)". */
export function leituraCurta(cidade: Cidade, e: EstadoDaCidade, agora: Date): string {
  if (e.varias || cidade.id === 'itajai') return 'várias réguas, cada uma com o seu zero'
  const l = e.leitura
  if (l?.medidoEm && Number.isFinite(l.nivel_m) && frescorDaCidade(idadeMin(l.medidoEm, agora), cidade.id) !== 'velha') {
    const f = e.faixa !== 'sem-dado' && e.faixa !== 'varias' ? `${rotuloDaFaixa(e.faixa, cidade, ROTULO[e.faixa]?.rotulo ?? e.faixa)}, ` : ''
    const t = tendenciaDaLeitura(e.serie, l, agora)
    return `${metros(l.nivel_m)} (${f}na régua de ${cidade.nome})${t ? `, ${t.rotulo === 'subindo' ? '▲ ' : t.rotulo === 'descendo' ? '▼ ' : ''}${textoTendencia(t)}` : ''}, medido ${quando(l.medidoEm, agora)}`
  }
  const est = e.estadual
  if (est?.medidoEm && Number.isFinite(est.nivelBrutoM) && frescorDaCidade(idadeMin(est.medidoEm, agora), cidade.id) !== 'velha') {
    return `sem leitura municipal de agora; na rede da Defesa Civil de SC, ${metros(est.nivelBrutoM)} (zero próprio), medido ${quando(est.medidoEm, agora)}`
  }
  return 'sem leitura de agora'
}

export function textoDeCima(args: {
  cat: Catalogo
  alvo: string
  estado: (id: string) => CidadeAgora | null
  trechos: readonly Trecho[]
  experimentais: readonly TrechoExperimental[]
  agora: Date
}): string {
  const { cat, alvo, agora } = args
  const nome = (id: string) => cat.cidades.find((c) => c.id === id)?.nome ?? id
  const linha = (id: string) => {
    const x = args.estado(id)
    return x ? leituraCurta(x.cidade, x.estado, agora) : 'fora do cadastro ao vivo'
  }
  const fora = cat.foraDaArvore?.find((f) => f.id === alvo)
  if (fora) {
    return `${nome(alvo)} não tem posição confirmada na árvore da bacia (fica no ${fora.rio}, que chega ao ${fora.chegaA}): nenhuma régua do cadastro está acima dela no mesmo rio.\n${AVISO_DE_CIMA}`
  }
  const secoes: string[] = []
  const topologias = args.cat.topologia ?? []
  for (const t of topologias) {
    const rioNome = t.rioId === 'itajai-mirim' ? 'Itajaí-Mirim' : 'Itajaí-Açu'
    const tempo = (de: string) => {
      const c = caminho([...args.trechos], t.rioId, de, alvo)
      if (c) return `leva ${faixaHoras(c)} até ${nome(alvo)}`
      if (trechoEmEstudo(args.experimentais, t.rioId, de, alvo)) return `tempo até ${nome(alvo)} em estudo (dados insuficientes)`
      return `sem tempo de descida até ${nome(alvo)} no cadastro`
    }
    const i = t.tronco.indexOf(alvo)
    if (i >= 0) {
      const acima = t.tronco.slice(0, i).reverse()
      const cabeceiras = t.cabeceiras.filter((c) => c !== alvo)
      const doTronco = [...acima, ...cabeceiras]
      // Afluentes com régua que entram acima (e os que entram neles, como o Rio dos Cedros no Benedito).
      const base = new Set(doTronco)
      const laterais: typeof t.laterais = []
      let mudou = true
      while (mudou) {
        mudou = false
        for (const l of t.laterais) {
          if (!laterais.includes(l) && base.has(l.entraPertoDe)) {
            laterais.push(l)
            base.add(l.id)
            mudou = true
          }
        }
      }
      const pertoDaqui = t.laterais.filter((l) => l.entraPertoDe === alvo)
      if (!doTronco.length && !laterais.length && !pertoDaqui.length) {
        secoes.push(`${rioNome}: ${nome(alvo)} é o ponto mais alto com régua neste rio; nada do cadastro fica acima.`)
        continue
      }
      const ls = [`${rioNome}, acima de ${nome(alvo)} (a mais perto primeiro):`]
      for (const id of doTronco) ls.push(`• ${nome(id)}${cabeceiras.includes(id) ? ' (cabeceira)' : ''}: ${linha(id)} · ${tempo(id)}.`)
      const rio = (r: string) => r.replace(/\s*\(.*\)/, '')
      for (const l of laterais) ls.push(`• ${nome(l.id)} (${rio(l.rio)}, afluente que entra perto de ${nome(l.entraPertoDe)}): ${linha(l.id)} · ${tempo(l.id)}.`)
      for (const l of pertoDaqui) ls.push(`• ${nome(l.id)} (${rio(l.rio)}, entra perto de ${nome(alvo)}; antes ou depois da régua, o cadastro não diz): ${linha(l.id)}.`)
      secoes.push(ls.join('\n'))
      continue
    }
    if (t.cabeceiras.includes(alvo)) {
      secoes.push(`${rioNome}: ${nome(alvo)} é cabeceira; nenhuma régua do cadastro fica acima dela no mesmo rio.`)
      continue
    }
    const lat = t.laterais.find((l) => l.id === alvo)
    if (lat) {
      const rio = lat.rio.replace(/\s*\(.*\)/, '')
      const ls = [`${nome(alvo)} fica no ${rio}, afluente que entra no ${rioNome} perto de ${nome(lat.entraPertoDe)}: as cidades do tronco não descem por ${nome(alvo)}.`]
      const acima = t.laterais.filter((l) => l.entraPertoDe === alvo)
      for (const l of acima) ls.push(`• ${nome(l.id)} (${l.rio.replace(/\s*\(.*\)/, '')}, entra perto de ${nome(alvo)}): ${linha(l.id)}.`)
      if (!acima.length) ls.push(`Nenhuma régua do cadastro fica acima de ${nome(alvo)} no ${rio}.`)
      secoes.push(ls.join('\n'))
    }
  }
  if (!secoes.length) return `${nome(alvo)} não está na árvore da bacia do cadastro.`
  return [...secoes, AVISO_DE_CIMA].join('\n')
}
