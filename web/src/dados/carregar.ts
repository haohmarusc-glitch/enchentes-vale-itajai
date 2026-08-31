/**
 * Ponto único de leitura dos JSONs de `data/`.
 *
 * Nada aqui inventa, completa ou arredonda valor: os dados chegam à tela
 * exatamente como estão no arquivo. Registros malformados são DESCARTADOS
 * com aviso no console — nunca corrigidos por adivinhação.
 */
import estacoesJson from '@dados/estacoes.json'
import enchentesJson from '@dados/enchentes.json'
import transitoJson from '@dados/transito.json'
import mareJson from '@dados/mare-itajai.json'
import type {
  AfluenteMonitorado,
  Cidade,
  Confianca,
  Enchentes,
  Estacoes,
  EstacaoTempoReal,
  Evento,
  Rio,
  TabuaMare,
  Transito,
  Trecho,
} from './tipos'

const CONFIANCAS: Confianca[] = ['alta', 'media', 'baixa']

function ehConfianca(v: unknown): v is Confianca {
  return typeof v === 'string' && (CONFIANCAS as string[]).includes(v)
}

/** `AAAA`, `AAAA-MM` ou `AAAA-MM-DD`. */
const RE_DATA = /^\d{4}(-\d{2}(-\d{2})?)?$/

function descarta(motivo: string, registro: unknown): void {
  // Visível no console para quem mantém os dados; a tela simplesmente não mostra o registro.
  console.warn(`[dados] registro descartado — ${motivo}`, registro)
}

export const estacoes = estacoesJson as unknown as Estacoes
const enchentes = enchentesJson as unknown as Enchentes
const transito = transitoJson as unknown as Transito

/** Ids de cidade que existem em `estacoes.json`, por rio. */
const cidadesPorRio = new Map<string, Map<string, Cidade>>()
for (const [rioId, rio] of Object.entries(estacoes.rios)) {
  const mapa = new Map<string, Cidade>()
  for (const cidade of rio.cidades) mapa.set(cidade.id, cidade)
  cidadesPorRio.set(rioId, mapa)
}

function eventoValido(e: Evento): boolean {
  for (const d of e.divergencias ?? []) {
    if (typeof d.pico_m !== 'number' || !Number.isFinite(d.pico_m)) {
      descarta('divergência com pico_m inválido', e)
      return false
    }
  }
  if (typeof e.rio !== 'string' || !cidadesPorRio.has(e.rio)) {
    descarta('rio desconhecido', e)
    return false
  }
  if (typeof e.cidade !== 'string' || e.cidade.length === 0) {
    descarta('cidade ausente', e)
    return false
  }
  if (typeof e.pico_m !== 'number' || !Number.isFinite(e.pico_m) || e.pico_m <= 0) {
    descarta('pico_m ausente ou fora de faixa', e)
    return false
  }
  if (typeof e.data !== 'string' || !RE_DATA.test(e.data)) {
    descarta('data fora do formato ISO parcial', e)
    return false
  }
  if (!ehConfianca(e.confianca)) {
    descarta('confianca inválida', e)
    return false
  }
  if (typeof e.fonte !== 'string' || e.fonte.trim().length === 0) {
    // Regra do CLAUDE.md: todo registro precisa de fonte.
    descarta('sem fonte', e)
    return false
  }
  return true
}

function trechoValido(t: Trecho): boolean {
  if (!cidadesPorRio.has(t.rio)) {
    descarta('trecho com rio desconhecido', t)
    return false
  }
  if (
    typeof t.horas_min !== 'number' ||
    typeof t.horas_max !== 'number' ||
    !Number.isFinite(t.horas_min) ||
    !Number.isFinite(t.horas_max) ||
    t.horas_min < 0 ||
    t.horas_max < t.horas_min
  ) {
    descarta('faixa de horas inválida', t)
    return false
  }
  if (!ehConfianca(t.confianca)) {
    descarta('confianca inválida', t)
    return false
  }
  return true
}

export const eventos: Evento[] = enchentes.eventos.filter(eventoValido)
export const trechos: Trecho[] = transito.trechos.filter(trechoValido)

export function rio(rioId: string): Rio | undefined {
  return estacoes.rios[rioId]
}

export function cidadesDoRio(rioId: string): Cidade[] {
  const r = estacoes.rios[rioId]
  if (!r) return []
  return [...r.cidades].sort((a, b) => a.ordem - b.ordem)
}

export function cidade(rioId: string, cidadeId: string): Cidade | undefined {
  return cidadesPorRio.get(rioId)?.get(cidadeId)
}

/** Nome legível de uma cidade; cai no próprio id quando ela não está em `estacoes.json`. */
export function nomeCidade(rioId: string, cidadeId: string): string {
  const c = cidade(rioId, cidadeId)
  if (c) return c.nome
  const afluente = (estacoes.afluentes_monitorados ?? []).find((a) => a.id === cidadeId)
  if (afluente) return afluente.nome
  const emOutroRio = [...cidadesPorRio.values()]
    .map((m) => m.get(cidadeId))
    .find((x): x is Cidade => Boolean(x))
  return emOutroRio?.nome ?? cidadeId
}

/**
 * O nome de uma cidade quando não se sabe (nem importa) o rio dela — o caso de
 * uma lista de cidades cobertas por alguma tabela. `nomeCidade` já procura nos
 * dois rios quando não acha no que recebeu; isto só deixa a intenção à vista.
 */
export function nomeDeCidade(cidadeId: string): string {
  return nomeCidade('', cidadeId)
}

export function eventosDoRio(rioId: string): Evento[] {
  return eventos.filter((e) => e.rio === rioId)
}

export function eventosDaCidade(rioId: string, cidadeId: string): Evento[] {
  return eventos.filter((e) => e.rio === rioId && e.cidade === cidadeId)
}

/** Cidades que aparecem em `enchentes.json` para um rio, mesmo sem estação cadastrada. */
export function cidadesComHistorico(rioId: string): string[] {
  return [...new Set(eventosDoRio(rioId).map((e) => e.cidade))]
}

/**
 * Cidades com régua própria fora da sequência do eixo (Timbó, no Benedito).
 * Elas aparecem nos dados mas nunca entram no encadeamento de tempo de descida.
 */
export const afluentesMonitorados: AfluenteMonitorado[] = estacoes.afluentes_monitorados ?? []

/**
 * As estações de tempo real cadastradas — é nelas que ficam as cotas oficiais
 * das cidades com mais de uma régua (Itajaí) ou cuja régua não é a da cidade
 * (Ilhota). Ver `logica/reguas.ts` para o porquê de não escolher uma delas.
 */
export const estacoesTempoReal: EstacaoTempoReal[] = estacoes.estacoes_tempo_real ?? []

const RE_QUANDO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/

const tabua = mareJson as unknown as TabuaMare

function entradaMareValida(e: { quando: string; altura_m?: number }): boolean {
  if (typeof e.quando !== 'string' || !RE_QUANDO.test(e.quando)) {
    descarta('entrada de maré com horário fora do formato AAAA-MM-DDTHH:MM', e)
    return false
  }
  if (Number.isNaN(new Date(e.quando).getTime())) {
    descarta('entrada de maré com horário que não existe no calendário', e)
    return false
  }
  return true
}

/**
 * Tábua de maré de Itajaí, coletada por `scripts/coleta_mares.py`.
 *
 * Vem vazia enquanto ninguém rodou o coletor. Vazia é um estado legítimo: a
 * tela pede a tábua a quem está usando em vez de estimar horário de preamar.
 */
export const mareItajai: TabuaMare = {
  ...tabua,
  preamares: (tabua.preamares ?? []).filter(entradaMareValida),
  baixamares: (tabua.baixamares ?? []).filter(entradaMareValida),
}

export const fontesGerais = estacoes.fontes_gerais

// --- Cotas de rua -----------------------------------------------------------
//
// As cotas de rua saíram daqui para `dados/cotasRuas.ts`, que é carregado à
// parte junto do componente da busca: são 611 registros e crescendo, e quem
// abre o site para ver o nível do rio não precisa baixá-los.
