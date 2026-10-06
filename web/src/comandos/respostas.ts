/**
 * As respostas da 2ª entrega dos comandos (docs/CHAT-GLOBAL-COMANDOS.md, 06/10/2026). Funções puras: recebem o
 * que o site já carregou (leituras ao vivo, série, cadastro) e devolvem texto. Nada aqui calcula regra nova —
 * idade, frescor, faixa e texto de compartilhar saem dos mesmos módulos que as telas usam.
 *
 * Limites (os mesmos do chat de hoje):
 * - toda leitura vai com a hora da medição e a idade; leitura velha nunca aparece como de agora;
 * - réguas diferentes não se subtraem nem se comparam em metros (cada uma tem o seu zero);
 * - ligação pelo rio não é previsão: não diz se nem quando a água de cima chega;
 * - compartilhar é preparar o texto; quem envia é a pessoa.
 */
import faixas from '../../../data/faixas.json'
import { porRegua, type PontoSerie } from '../dados/serie'
import { reguaDe, type LeituraAoVivo } from '../dados/tempoReal'
import type { AoVivo } from '../dados/usarAoVivo'
import { diaDeBrasilia, horaDeBrasilia } from '../logica/agora'
import { metros } from '../logica/formato'
import { frescorDaCidade, idadeMin, textoIdade } from '../logica/tempoReal'
import type { ReguaNoMapa } from '../logica/reguasNoMapa'
import type { Catalogo, Fundo, TopologiaDoRio } from './tipos'

const quando = (d: Date, agora: Date) => `às ${horaDeBrasilia(d)} de ${diaDeBrasilia(d)} (${textoIdade(idadeMin(d, agora))})`

function nomeCidade(cat: Catalogo, id: string | null): string {
  return (id && cat.cidades.find((c) => c.id === id)?.nome) || id || 'cidade não informada'
}

/** A estação estadual pelo nome da cidade do cadastro; sem cidade no cadastro, só o nome da estação. */
const rotuloEstadual = (cat: Catalogo, cidadeId: string, estacao: string) => {
  const c = cat.cidades.find((x) => x.id === cidadeId)
  return c ? `${c.nome} (${estacao})` : estacao
}

// ---------------------------------------------------------------- leituras atrasadas

/**
 * "Quais leituras estão atrasadas?" — pela regra de idade que o site inteiro usa (`frescorDaCidade`): até
 * 90 min vale como agora (Blumenau, 120 min de série horária), até 3 h é atrasada, depois é velha e não vale
 * como nível de agora. Não mostra o número da leitura atrasada: só onde, a hora e a idade.
 */
export function textoAtrasadas(v: AoVivo, cat: Catalogo): string {
  if (v.tempoReal.situacao === 'carregando') return 'As leituras ainda estão carregando. Peça de novo em instantes.'
  if (v.tempoReal.situacao === 'indisponivel') {
    return 'Não consegui buscar as leituras agora, então não sei dizer quais estão atrasadas. Em emergência, ligue 199.'
  }
  const agora = v.agora
  const grupos = new Map<string, LeituraAoVivo[]>()
  for (const l of v.tempoReal.leituras) {
    const k = reguaDe(l)
    grupos.set(k, [...(grupos.get(k) ?? []), l])
  }
  const porCidade = new Map<string, number>()
  for (const ls of grupos.values()) porCidade.set(ls[0]!.cidade ?? '', (porCidade.get(ls[0]!.cidade ?? '') ?? 0) + 1)
  const rotulo = (titulo: string, l: LeituraAoVivo) => {
    const r = cat.reguas.find((x) => x.titulo === titulo)
    if (r) return `${r.codigo} · ${r.nome} (${nomeCidade(cat, r.cidadeId)})`
    const cidade = nomeCidade(cat, l.cidade)
    return (porCidade.get(l.cidade ?? '') ?? 0) > 1 ? `${cidade} · ${titulo}` : cidade
  }

  const emDia: string[] = []
  const atrasadas: string[] = []
  const velhas: string[] = []
  const semHora: string[] = []
  for (const [titulo, ls] of grupos) {
    // Primária e resgate da mesma régua: vale a mais fresca ("viva se qualquer das duas está fresca").
    const comHora = ls.filter((l) => l.medidoEm).sort((a, b) => b.medidoEm!.getTime() - a.medidoEm!.getTime())
    const l = comHora[0]
    if (!l) {
      semHora.push(rotulo(titulo, ls[0]!))
      continue
    }
    const f = frescorDaCidade(idadeMin(l.medidoEm!, agora), l.cidade)
    const item = `${rotulo(titulo, l)}: medida ${quando(l.medidoEm!, agora)}`
    if (f === 'agora') emDia.push(item)
    else if (f === 'atrasada') atrasadas.push(item)
    else velhas.push(item)
  }

  const estaduais: string[] = []
  for (const [cidadeId, b] of v.nivelSc) {
    if (!b.medidoEm) {
      estaduais.push(`${rotuloEstadual(cat, cidadeId, b.estacao)}: sem horário publicado`)
      continue
    }
    const f = frescorDaCidade(idadeMin(b.medidoEm, agora), cidadeId)
    if (f !== 'agora') estaduais.push(`${rotuloEstadual(cat, cidadeId, b.estacao)}: ${f === 'velha' ? 'velha' : 'atrasada'}, medida ${quando(b.medidoEm, agora)}`)
  }
  for (const [cidadeId, s] of v.nivelSc.situacoes ?? []) {
    if (s.tipo === 'sem_leitura') estaduais.push(`${rotuloEstadual(cat, cidadeId, s.estacao)}: a estação não publicou nível`)
  }

  const total = grupos.size
  const linhas = [
    total === 0
      ? 'O site não recebeu nenhuma leitura municipal nesta coleta.'
      : `Réguas municipais: ${emDia.length} de ${total} com leitura de agora (até 90 min; em Blumenau, até 2 h).`,
  ]
  if (atrasadas.length) linhas.push(`Atrasadas (até 3 h; o número já pode não ser o do rio agora):\n• ${atrasadas.join('\n• ')}`)
  if (velhas.length) linhas.push(`Velhas (mais de 3 h, ou horário impossível; não valem como nível de agora):\n• ${velhas.join('\n• ')}`)
  if (semHora.length) linhas.push(`Sem horário publicado (o site não usa como nível de agora):\n• ${semHora.join('\n• ')}`)
  if (!atrasadas.length && !velhas.length && !semHora.length && total > 0) linhas.push('Nenhuma régua municipal está atrasada.')
  if (estaduais.length) linhas.push(`Rede da Defesa Civil de SC (zero próprio de cada estação):\n• ${estaduais.join('\n• ')}`)
  if (v.tempoReal.falhaEntrega) linhas.push('A última busca falhou: estas são as leituras da busca anterior.')
  linhas.push('A idade conta da hora da medição, não da coleta.')
  return linhas.join('\n')
}

// ---------------------------------------------------------------- o que mudou na última hora

export type UltimaHora = { texto: string } | { escolher: string[] }

/**
 * A série de UMA régua da cidade. Primária e resgate (Blumenau: Defesa Civil de Itajaí e AlertaBlu) são duas
 * publicações da mesma régua e NÃO se fundem — fundir dava um serrilhado de ±6 cm (`dados/serie.ts`). Vale a
 * publicação com a medição mais recente. Réguas DIFERENTES (Itajaí): devolve os títulos para perguntar qual.
 */
export function serieDeUmaRegua(
  pontos: PontoSerie[],
  resgates: Record<string, string>,
  titulo: string | null,
): { pontos: PontoSerie[]; publicacao: string | null } | { escolher: string[] } {
  const grupos = porRegua(pontos)
  if (titulo) return { pontos: grupos.get(titulo) ?? [], publicacao: null }
  const primarias = new Set([...grupos.keys()].map((k) => resgates[k] ?? k))
  if (primarias.size > 1) return { escolher: [...primarias].sort() }
  let melhor: { pontos: PontoSerie[]; publicacao: string | null } = { pontos: [], publicacao: null }
  for (const [k, ps] of grupos) {
    const ult = ps.at(-1)?.medidoEm.getTime() ?? -Infinity
    if (ult > (melhor.pontos.at(-1)?.medidoEm.getTime() ?? -Infinity)) melhor = { pontos: ps, publicacao: resgates[k] ? k : null }
  }
  return melhor
}

export function textoUltimaHora(args: {
  nome: string
  cidadeId: string
  pontos: PontoSerie[]
  publicacao: string | null
  agora: Date
}): string {
  const { nome, cidadeId, pontos, agora } = args
  const ult = pontos.at(-1)
  if (!ult) return `O site não tem série recente da régua de ${nome}.`
  const idade = idadeMin(ult.medidoEm, agora)
  const de = args.publicacao ? ` (publicação ${args.publicacao})` : ''
  if (idade > 60 || frescorDaCidade(idade, cidadeId) === 'velha') {
    return `Não há medição da régua de ${nome}${de} na última hora: a última é de ${horaDeBrasilia(ult.medidoEm)} de ${diaDeBrasilia(ult.medidoEm)} (${textoIdade(idade)}).`
  }
  const inicio = agora.getTime() - 60 * 60_000
  let janela = pontos.filter((p) => p.medidoEm.getTime() >= inicio && p.medidoEm.getTime() <= agora.getTime() + 15 * 60_000)
  // Série horária (AlertaBlu): uma medição só na última hora. Compara com a anterior, se ela tem até 90 min.
  const anterior = pontos.filter((p) => p.medidoEm.getTime() < inicio).at(-1)
  if (janela.length === 1 && anterior && janela[0]!.medidoEm.getTime() - anterior.medidoEm.getTime() <= 90 * 60_000) {
    janela = [anterior, ...janela]
  }
  if (janela.length < 2) {
    return `Só uma medição da régua de ${nome}${de} na última hora: ${metros(ult.nivel_m)} às ${horaDeBrasilia(ult.medidoEm)} (${textoIdade(idade)}). Com uma medição só, não dá para dizer o que mudou.`
  }
  const primeiro = janela[0]!
  const ultimo = janela.at(-1)!
  const cm = Math.round((ultimo.nivel_m - primeiro.nivel_m) * 100)
  const passos = janela.slice(1).map((p, i) => (p.medidoEm.getTime() - janela[i]!.medidoEm.getTime()) / 60_000).sort((a, b) => a - b)
  const passo = Math.round(passos[Math.floor(passos.length / 2)]!)
  const lacunas = janela
    .slice(1)
    .map((p, i) => ({ de: janela[i]!.medidoEm, ate: p.medidoEm, min: (p.medidoEm.getTime() - janela[i]!.medidoEm.getTime()) / 60_000 }))
    .filter((g) => g.min > 2 * passo && g.min >= 20)
  const variacao = Math.abs(cm) < 2 ? 'praticamente parado (menos de 2 cm)' : `${cm > 0 ? 'subiu' : 'baixou'} ${Math.abs(cm)} cm`
  const linhas = [
    `Régua de ${nome}${de}, de ${horaDeBrasilia(primeiro.medidoEm)} a ${horaDeBrasilia(ultimo.medidoEm)}: de ${metros(primeiro.nivel_m)} para ${metros(ultimo.nivel_m)} — ${variacao}.`,
    `${janela.length} medições, uma a cada ~${passo} min.` +
      (lacunas.length
        ? ` Lacuna: ${lacunas.map((g) => `${Math.round(g.min)} min sem medição entre ${horaDeBrasilia(g.de)} e ${horaDeBrasilia(g.ate)}`).join('; ')}.`
        : ' Sem lacunas.'),
    `Última medição ${textoIdade(idade)}. É o que já foi medido, não previsão.`,
  ]
  return linhas.join('\n')
}

// ---------------------------------------------------------------- comparar as réguas

/** Os nomes das faixas do site ("Abaixo da atenção", nunca "Normal": cor não diz que está seguro). */
const NOME_FAIXA = Object.fromEntries(
  Object.entries((faixas as unknown as { faixas: Record<string, { rotulo: string }> }).faixas).map(([k, v]) => [k, v.rotulo]),
) as Record<string, string>

/**
 * As réguas de uma cidade lado a lado (Itajaí, onze). Cada uma na régua DELA: o texto não subtrai nem
 * ordena por metro, porque um número maior numa régua não é água mais alta que na outra.
 */
export function textoComparar(nome: string, reguas: ReguaNoMapa[], agora: Date): string {
  const ordem = [...reguas].sort((a, b) => a.codigo.localeCompare(b.codigo, 'pt-BR', { numeric: true }))
  const linhas = ordem.map((r) => {
    const rot = `${r.codigo} · ${r.nome}`
    if (r.nivel == null) return `${rot}: sem leitura nesta coleta`
    if (!r.medidoEm) return `${rot}: ${metros(r.nivel)}, sem horário publicado (não vale como nível de agora)`
    const idade = idadeMin(r.medidoEm, agora)
    const velha = frescorDaCidade(idade, r.cidade) === 'velha'
    const faixa = velha ? '' : r.faixa ? ` · ${NOME_FAIXA[r.faixa] ?? r.faixa}` : ' · sem faixa'
    return `${rot}: ${metros(r.nivel)} ${quando(r.medidoEm, agora)}${velha ? ' — leitura velha, não é o nível de agora' : faixa}`
  })
  return [
    `As ${ordem.length} réguas de ${nome}, cada uma no zero dela: os números não se comparam entre si nem se subtraem.`,
    `• ${linhas.join('\n• ')}`,
    '"Sem faixa" é régua sem cota de referência ou de maré: não quer dizer que está tudo bem.',
  ].join('\n')
}

// ---------------------------------------------------------------- montante e afluentes

const AVISO_LIGACAO = 'Ligação pelo rio não é previsão: não diz se nem quando a água de cima chega aqui. O tempo de descida entre cidades do tronco fica na página do rio, sempre em intervalo.'

/**
 * O que fica a montante (ou os afluentes do trecho), pela árvore que o cadastro declara. Afluente que entra
 * "perto de" uma cidade vizinha não é afirmado antes nem depois da régua: o cadastro só diz "perto de", e o
 * ponto exato só vale quando o cadastro o escreve (Benedito).
 */
export function textoMontante(cat: Catalogo, cidadeId: string, foco: 'montante' | 'afluentes'): string {
  const nome = (id: string) => nomeCidade(cat, id)
  const topo = cat.topologia ?? []
  const fora = cat.foraDaArvore?.find((f) => f.id === cidadeId)
  if (fora) {
    return [
      `${nome(cidadeId)} fica no ${fora.rio}, que chega ao ${fora.chegaA} em ${coord(fora.lat, fora.lon)} (fonte: OpenStreetMap). A cidade não tem posição confirmada na árvore da bacia, e nenhuma régua do cadastro fica acima dela no mesmo rio.`,
      AVISO_LIGACAO,
    ].join('\n')
  }
  const partes: string[] = []
  for (const t of topo) {
    const i = t.tronco.indexOf(cidadeId)
    if (i >= 0) partes.push(...doTronco(t, i, foco, cat))
    if (t.cabeceiras.includes(cidadeId)) {
      partes.push(`${nome(cidadeId)} é cabeceira: nenhuma régua do cadastro fica acima dela no mesmo rio.`)
    }
    const lat = t.laterais.find((l) => l.id === cidadeId)
    if (lat) {
      const rio = lat.rio.replace(/\s*\(.*\)/, '')
      partes.push(`${nome(cidadeId)} fica no ${rio}, que entra perto de ${nome(lat.entraPertoDe)}. Não é elo do tronco: a cheia dela entra no rio principal, não desce por ele.`)
      const acima = t.laterais.filter((x) => x.entraPertoDe === cidadeId)
      const rotulo = (x: { id: string; rio: string }) => {
        const r = x.rio.replace(/\s*\(.*\)/, '')
        return r === nome(x.id) ? r : `${r}, de ${nome(x.id)}`
      }
      if (acima.length) partes.push(`Chega perto de ${nome(cidadeId)}: ${acima.map(rotulo).join('; ')} — a posição em relação à régua de ${nome(cidadeId)} não está confirmada.`)
      else if (foco === 'montante') partes.push(`Nenhuma régua do cadastro fica acima de ${nome(cidadeId)} nesse rio.`)
    }
  }
  if (!partes.length) return `${nome(cidadeId)} não está na árvore da bacia do cadastro.`
  return [...partes, AVISO_LIGACAO].join('\n')
}

interface Afluente {
  texto: string
  /** Índice, no tronco, da cidade perto da qual entra. */
  j: number
  /** O cadastro ESCREVE que entra depois da régua desta cidade (Benedito: "Entra depois de Indaial"). */
  depoisDe: string | null
}

function doTronco(t: TopologiaDoRio, i: number, foco: 'montante' | 'afluentes', cat: Catalogo): string[] {
  const nome = (id: string) => nomeCidade(cat, id)
  const aqui = t.tronco[i]!
  const rioNome = t.rioId === 'itajai-mirim' ? 'Itajaí-Mirim' : 'Itajaí-Açu'
  const semParenteses = (s: string) => s.replace(/\s*\(.*\)/, '')
  // O ponto que o cadastro escreve para um rio (só o Benedito, hoje), com o "Entra depois de X".
  const pontoDe = (rio: string) =>
    t.afluentesSemRegua.find((a) => a.pontoExato && /\(lat, ?lon\)/.test(a.pontoExato) && semParenteses(a.nome) === rio)?.pontoExato ?? null
  const depoisDe = (ponto: string | null) => ponto?.match(/^Entra depois de (.+?) \(/)?.[1] ?? null
  const posicao = (perto: string, j: number, ponto: string | null) => {
    if (ponto) return ponto.split('. Confluência')[0] + '.'
    if (j < i - 1) return `entra perto de ${nome(perto)}, acima de ${nome(aqui)}.`
    if (j === i - 1) return `entra perto de ${nome(perto)}, acima de ${nome(aqui)} (o cadastro não diz se antes ou depois da régua de ${nome(perto)}).`
    return `entra perto de ${nome(perto)}; o cadastro não diz se antes ou depois da régua de ${nome(aqui)}.`
  }

  const afluentes: Afluente[] = []
  const porRio = new Map<string, Afluente>()
  // Primeiro os que entram no tronco; depois os que entram noutro afluente (Rio dos Cedros → Benedito).
  const laterais = [...t.laterais].sort((a, b) => Number(!t.tronco.includes(a.entraPertoDe)) - Number(!t.tronco.includes(b.entraPertoDe)))
  for (const l of laterais) {
    const rio = semParenteses(l.rio)
    const j = t.tronco.indexOf(l.entraPertoDe)
    if (j >= 0) {
      const ponto = pontoDe(rio)
      const a = { texto: `${rio}, de ${nome(l.id)}: ${posicao(l.entraPertoDe, j, ponto)}`, j, depoisDe: depoisDe(ponto) }
      afluentes.push(a)
      porRio.set(l.id, a)
      continue
    }
    const pai = porRio.get(l.entraPertoDe)
    if (!pai) continue
    const a = { texto: `${rio}, de ${nome(l.id)}: chega ao rio de ${nome(l.entraPertoDe)}, que segue a posição acima.`, j: pai.j, depoisDe: pai.depoisDe }
    afluentes.push(a)
    porRio.set(l.id, a)
  }
  for (const a of t.afluentesSemRegua) {
    const rio = semParenteses(a.nome)
    const j = t.tronco.indexOf(a.entraPertoDe)
    if (j < 0 || afluentes.some((x) => x.texto.startsWith(rio + ','))) continue
    const ponto = pontoDe(rio)
    afluentes.push({ texto: `${rio} (sem régua no cadastro): ${posicao(a.entraPertoDe, j, ponto)}`, j, depoisDe: depoisDe(ponto) })
  }

  const linhas: string[] = []
  if (foco === 'montante') {
    if (i === 0 && t.cabeceiras.length === 0) linhas.push(`${nome(aqui)} é a primeira régua do ${rioNome} no cadastro.`)
    else if (i > 0) linhas.push(`Pelo ${rioNome}, acima de ${nome(aqui)}: ${t.tronco.slice(0, i).map(nome).join(' → ')} → ${nome(aqui)}.`)
    if (t.cabeceiras.length) {
      linhas.push(`As cabeceiras ${t.cabeceiras.map(nome).join(' e ')} correm em paralelo e se juntam em ${nome(t.tronco[0]!)}, onde nasce o ${rioNome}.`)
      for (const f of cat.foraDaArvore ?? []) linhas.push(`${nome(f.id)}: o ${f.rio} chega ao ${f.chegaA} acima de ${nome(t.tronco[0]!)} (sem posição confirmada na árvore).`)
    }
  }
  const noTrecho = (a: Afluente) => (foco === 'montante' ? a.j <= i : a.j === i || a.j === i - 1)
  const depoisDaqui = afluentes.filter((a) => noTrecho(a) && a.depoisDe === nome(aqui))
  const lista = afluentes.filter((a) => noTrecho(a) && a.depoisDe !== nome(aqui))
  if (lista.length) {
    linhas.push(`${foco === 'montante' ? `Afluentes do ${rioNome} acima` : `Afluentes no trecho do ${rioNome} que chega a ${nome(aqui)}`}:\n• ${lista.map((a) => a.texto).join('\n• ')}`)
  } else if (foco === 'afluentes') {
    linhas.push(`O cadastro não registra afluente entrando no trecho do ${rioNome} que chega a ${nome(aqui)}.`)
  }
  if (depoisDaqui.length) {
    linhas.push(`Entram logo DEPOIS da régua de ${nome(aqui)}, não acima: ${depoisDaqui.map((a) => a.texto.split(',')[0]).join(', ')}.`)
  }
  return linhas
}

function coord(lat: number, lon: number): string {
  const f = (n: number) => n.toLocaleString('pt-BR', { minimumFractionDigits: 5, maximumFractionDigits: 5 }).replace('-', '−')
  return `${f(lat)}, ${f(lon)}`
}
export { coord as textoDaCoordenada }

// ---------------------------------------------------------------- origem do traçado

export interface PropriedadesDoTracado {
  rio?: string
  fonte?: string
  trechos?: number
  cobertura?: string
  origem?: { bruto: string; base_osm: string | null }[]
}

function dataDaBase(iso: string): string {
  const d = new Date(iso)
  if (!Number.isFinite(d.getTime())) return iso
  return `${d.toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo' })}, ${horaDeBrasilia(d)} de Brasília`
}

/** Fonte, cobertura e a data da base do OSM do traçado — a cópia do mapa que o espelho respondeu. */
export function textoOrigemTracado(nomeDoRio: string, p: PropriedadesDoTracado): string {
  const linhas = [`Traçado do ${nomeDoRio}: ${p.fonte ?? 'fonte não registrada no arquivo'}${p.trechos ? `, ${p.trechos} trechos` : ''}.`]
  const bases = (p.origem ?? []).filter((o) => o.base_osm)
  if (bases.length) {
    linhas.push(`Base do OpenStreetMap: ${bases.map((o) => `${dataDaBase(o.base_osm!)} (arquivo bruto ${o.bruto})`).join('; ')}. É a data da cópia do mapa usada, não a do download.`)
  } else if (p.origem?.length) {
    linhas.push(`Veio de ${p.origem.map((o) => o.bruto).join(', ')}; a data da base do OpenStreetMap não ficou registrada nesse bruto.`)
  } else {
    linhas.push('A data da base não está gravada no arquivo.')
  }
  if (p.cobertura) linhas.push(`Cobertura: ${p.cobertura}`)
  linhas.push('O desenho mostra por onde a água corre; não é mancha de inundação.')
  return linhas.join('\n')
}

// ---------------------------------------------------------------- link e resumo

const AVISO_ACESSO = 'O site só abre para e-mail cadastrado: quem não tem cadastro vê a tela de acesso. Para pedir cadastro, a pessoa manda o e-mail dela.'

/** O endereço do Monitor aberto, com a régua e o fundo — os mesmos parâmetros que ele lê ao abrir. */
export function linkDoMonitor(base: string, e: { cidade: string | null; regua: { codigo: string } | null; fundo: Fundo }): string {
  const busca = new URLSearchParams()
  if (e.regua) busca.set('regua', e.regua.codigo)
  busca.set('fundo', e.fundo)
  return `${base}#/monitor${e.cidade ? `/${e.cidade}` : ''}?${busca.toString()}`
}

export function textoDoLink(link: string, descricao: string): string {
  return `Link desta visualização (${descricao}):\n${link}\n${AVISO_ACESSO}`
}

/** A base do endereço (sem o `#`), para montar o link da tela. */
export function baseDoSite(href: string): string {
  return href.split('#')[0] ?? href
}
