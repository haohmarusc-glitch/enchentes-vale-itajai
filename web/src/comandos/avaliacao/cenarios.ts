/**
 * Os cenários congelados da bateria de avaliação (17ª entrega — PR 1 do handoff de qualidade do chat).
 *
 * Cada cenário é um `Ambiente` de mentira com dados fixos — leitura fresca, leitura velha, cidade sem leitura,
 * Itajaí com várias réguas, série curta, leituras indisponíveis, Monitor que não abre, publicação com nível
 * impossível — para a bateria medir o que o EXECUTOR responde nas situações de qualidade de dado e de falha
 * externa, sem rede e sem relógio de verdade. O relógio é sempre `AGORA` (06/10/2026 15h00 em Brasília), o mesmo
 * dos testes das entregas.
 *
 * Nada aqui inventa regra: os textos saem dos executores de hoje; a bateria só confere que eles respeitam as
 * regras escritas (leitura velha nunca é "agora", nível impossível é indisponibilidade, Itajaí não faz conta com
 * várias réguas, Gaspar/Ascurra não têm frase de cota, falha externa é dita e não mascarada).
 */
import { readFileSync } from 'node:fs'
import type { LeituraAoVivo } from '../../dados/tempoReal'
import { buscarTempoReal } from '../../dados/tempoReal'
import type { AoVivo } from '../../dados/usarAoVivo'
import type { NivelSc } from '../../dados/nivelSc'
import type { PontoSerie } from '../../dados/serie'
import type { Cidade, CotaRua } from '../../dados/tipos'
import type { ControleMonitor, Retrato } from '../ponte'
import type { Ambiente, DadosDoChat } from '../executar'
import type { Fundo } from '../tipos'

export const AGORA = new Date('2026-10-06T18:00:00Z') // 15h00 em Brasília

const ler = (c: string) => JSON.parse(readFileSync(new URL(`../../../../data/${c}`, import.meta.url), 'utf8'))
export const estacoes = ler('estacoes.json') as { rios: Record<string, { cidades: Cidade[] }> }
const transito = ler('transito.json')

export function cidadeDoCadastro(id: string): { cidade: Cidade; rioId: string } | null {
  for (const [rioId, r] of Object.entries(estacoes.rios)) {
    const c = r.cidades.find((x) => x.id === id)
    if (c) return { cidade: c, rioId }
  }
  return null
}

const minutosAtras = (min: number) => new Date(AGORA.getTime() - min * 60_000)

export const leitura = (cidade: string, nivel_m: number, idadeMin: number, extra: Partial<LeituraAoVivo> = {}): LeituraAoVivo =>
  ({ estacao: cidade, rio: 'itajai-acu', cidade, nivel_m, medidoEm: minutosAtras(idadeMin), resgateDe: null, ...extra }) as LeituraAoVivo

/**
 * Uma série de 15 em 15 min, das `horas` atrás até o último ponto (10 min atrás, a mesma hora da leitura fresca —
 * a D7 só dá tendência quando o último ponto É a leitura mostrada), com o nível em função das horas atrás.
 */
export function serie(horas: number, nivel: (h: number) => number, regua = 'Blumenau', passoMin = 15, fimMin = 10): PontoSerie[] {
  const pts: PontoSerie[] = []
  for (let m = horas * 60 + fimMin; m >= fimMin; m -= passoMin) pts.push({ medidoEm: minutosAtras(m), nivel_m: Math.round(nivel(m / 60) * 100) / 100, regua })
  return pts
}

const cota = (cidade: string, rua: string, cota_m: number | null, extra: Partial<CotaRua> = {}): CotaRua =>
  ({ cidade, rio: 'itajai-acu', rua, bairro: null, ponto: null, cota_m, referencia: 'régua', fonte: 'Defesa Civil', data_fonte: '2022-05', confianca: 'alta', ...extra }) as CotaRua
export const COTAS: CotaRua[] = [
  cota('blumenau', 'Rua São Rafael', 7.4, { bairro: 'Itoupava Norte' }),
  cota('blumenau', 'Rua Amazonas', 8.0, { bairro: 'Garcia' }),
  cota('blumenau', 'Rua XV de Novembro', 8.6, { bairro: 'Centro' }),
  cota('blumenau', 'Rua Progresso', 9.2, { bairro: 'Progresso' }),
  cota('gaspar', 'Rua São Paulo', 7.0),
  cota('gaspar', 'Rua Itajaí', 8.2),
]

export interface Congelado {
  leituras: LeituraAoVivo[]
  series?: Record<string, Record<string, PontoSerie[]>>
  situacao?: 'ok' | 'indisponivel'
}

export function aoVivoCongelado(c: Congelado): AoVivo {
  return {
    tempoReal: { situacao: c.situacao ?? 'ok', leituras: c.leituras, chuva: [], chuvaOk: true, coletadoEm: AGORA, fonte: null },
    nivelSc: new Map() as NivelSc,
    serie: { situacao: 'ok', series: c.series ?? {}, resgates: {}, janelaHoras: 48, geradoEm: AGORA },
    agora: AGORA,
  }
}

/** Um Monitor de mentira que aceita tudo e anota as chamadas. */
export function monitorFalso(cidade: string | null) {
  const chamadas: string[] = []
  let fundo: Fundo = 'escuro'
  let regua: string | null = null
  let camada: string | null = null
  const c: ControleMonitor = {
    cidade,
    pronto: true,
    estado: () => ({ cidade, cidadeNome: cidade, regua: regua ? { codigo: regua, rotulo: regua } : null, reguas: [], fundo, camada, camadasDisponiveis: [{ arquivo: 'm2008', rotulo: '2008' }, { arquivo: 'm2011', rotulo: '2011' }], reproducao: null }),
    escolherRegua: (codigo) => { chamadas.push(`regua:${codigo}`); regua = codigo === 'todas' ? null : codigo; return { ok: true, texto: `Régua ${codigo}.` } },
    enquadrarCidade: () => { chamadas.push('enquadrar'); return { ok: true, texto: 'Enquadrado.' } },
    zoom: (s) => { chamadas.push(`zoom:${s}`); return { ok: true, texto: 'Zoom.' } },
    verBacia: () => { chamadas.push('bacia'); return { ok: true, texto: 'Bacia.' } },
    fundo: (f) => { chamadas.push(`fundo:${f}`); fundo = f; return { ok: true, texto: `Fundo ${f}.` } },
    camada: (a) => { chamadas.push(`camada:${a}`); camada = a === 'off' ? null : a; return { ok: true, texto: `Camada ${a}.` } },
    aoVivo: () => { chamadas.push('aovivo'); return { ok: true, texto: 'Ao vivo.' } },
    explicar: () => ({ cidadeNome: cidade ?? '', faixa: 'Sem dado', motivoCinza: 'sem leitura.', posicao: 'Pino na coordenada do cadastro.', equivalencia: '' }),
    retrato: (): Retrato => ({ rota: cidade ? `/monitor/${cidade}` : '/monitor', cidade, regua, fundo, camada }),
    restaurar: (r) => { chamadas.push('restaurar'); fundo = r.fundo ?? fundo; regua = r.regua ?? null; camada = r.camada ?? null; return { ok: true, texto: 'ok' } },
  }
  return { c, chamadas }
}

export interface Cenario {
  amb: Ambiente
  navegacoes: string[]
  chamadas: () => string[]
}

export interface OpcoesDoCenario {
  /** `null` = as leituras não carregaram (rede fora). */
  aoVivo: AoVivo | null
  monitorNaoAbre?: boolean
  rota?: string
  cotasRuas?: CotaRua[] | null
  semTransito?: boolean
}

export function cenario(o: OpcoesDoCenario): Cenario {
  let atual: ReturnType<typeof monitorFalso> | null = null
  let r = o.rota ?? '/'
  const navegacoes: string[] = []
  const dados: DadosDoChat = {
    aoVivo: async () => o.aoVivo,
    cidade: cidadeDoCadastro,
    reguasNoMapa: () => [],
    tracado: async () => null,
    base: () => '',
    cotasRuas: async () => (o.cotasRuas === undefined ? COTAS : o.cotasRuas),
    ...(o.semTransito ? {} : { transito: () => ({ trechos: transito.trechos, experimentais: transito.trechos_experimentais }) }),
  }
  const amb: Ambiente = {
    navegar: (para) => {
      navegacoes.push(para)
      r = para
      const m = para.match(/^\/monitor(?:\/([a-z-]+))?/)
      atual = m && !o.monitorNaoAbre ? monitorFalso(m[1] ?? null) : null
    },
    rotaAtual: () => r,
    monitor: () => atual?.c ?? null,
    esperarMonitor: async (cid) => (atual && atual.c.cidade === cid ? atual.c : null),
    dados,
  }
  return { amb, navegacoes, chamadas: () => atual?.chamadas ?? [] }
}

// --- As séries e leituras de cada cenário. Blumenau: Observação 3,00 · Atenção 4,00 · Alerta 6,00 · Alerta Máximo 8,00 (régua).
const subindo = serie(24, (h) => (h >= 12 ? 3.5 : 3.5 + (12 - h + 1 / 6) * 0.25)) // último ponto (14:50): 6,50 m, igual à leitura; cruzou 4,00 há ~10 h e 6,00 há ~2 h
const curta = serie(0.5, () => 6.5) // só 3 pontos
const ponto = (cidade: string, pts: PontoSerie[]) => ({ 'itajai-acu': { [cidade]: pts } })

export const CENARIOS = {
  /** Blumenau 6,50 m há 10 min, subindo; Gaspar 5,20 m há 10 min; Ascurra 7,00 m há 10 min. */
  fresca: () => cenario({ aoVivo: aoVivoCongelado({ leituras: [leitura('blumenau', 6.5, 10), leitura('gaspar', 5.2, 10), leitura('ascurra', 7.0, 10)], series: ponto('blumenau', subindo) }) }),
  /** Blumenau 6,50 m há 6 h: leitura velha (o limite de Blumenau é 120 min). */
  velha: () => cenario({ aoVivo: aoVivoCongelado({ leituras: [leitura('blumenau', 6.5, 360)], series: ponto('blumenau', serie(24, () => 6.5).filter((p) => p.medidoEm.getTime() <= AGORA.getTime() - 360 * 60_000)) }) }),
  /** Leituras carregaram, mas Lontras não tem nenhuma. */
  semLeitura: () => cenario({ aoVivo: aoVivoCongelado({ leituras: [leitura('blumenau', 6.5, 10)] }) }),
  /** Itajaí com três réguas frescas (zeros diferentes). */
  itajaiVarias: () => cenario({
    aoVivo: aoVivoCongelado({
      leituras: [
        leitura('itajai', 1.2, 10, { estacao: 'DC-05 Centro' }), leitura('itajai', 2.4, 10, { estacao: 'DC-08 Murta' }), leitura('itajai', 0.9, 10, { estacao: 'DC-11 Espinheiros' }),
      ],
      series: { 'itajai-acu': { itajai: [...serie(6, () => 1.2, 'DC-05 Centro'), ...serie(6, () => 2.4, 'DC-08 Murta')] } },
    }),
  }),
  /** Série de Blumenau com só meia hora de pontos. */
  serieCurta: () => cenario({ aoVivo: aoVivoCongelado({ leituras: [leitura('blumenau', 6.5, 10)], series: ponto('blumenau', curta) }) }),
  /** As leituras não carregaram. */
  semDados: () => cenario({ aoVivo: null }),
  /** A publicação veio "indisponível" (coletor fora), sem leitura nenhuma. */
  indisponivel: () => cenario({ aoVivo: aoVivoCongelado({ leituras: [], situacao: 'indisponivel' }) }),
  /** Tudo certo nas leituras, mas o Monitor não monta. */
  monitorNaoAbre: () => cenario({ aoVivo: aoVivoCongelado({ leituras: [leitura('blumenau', 6.5, 10)] }), monitorNaoAbre: true }),
  /** Sem a tabela de cotas de rua e sem o trânsito do cadastro. */
  semTabelas: () => cenario({ aoVivo: aoVivoCongelado({ leituras: [leitura('blumenau', 6.5, 10)] }), cotasRuas: null, semTransito: true }),
} satisfies Record<string, () => Cenario>

export type NomeDoCenario = keyof typeof CENARIOS

/**
 * A publicação de tempo real com um nível impossível (30 m em Blumenau) e um negativo em Gaspar, lida pelo MESMO
 * `buscarTempoReal` do site com um transporte de mentira: as duas leituras têm de cair na validação e a publicação
 * virar "sem leitura", nunca um número na tela.
 */
export async function aoVivoComNivelImpossivel(): Promise<AoVivo> {
  const corpo = {
    coletado_em: AGORA.toISOString(),
    fonte: 'teste',
    leituras: [
      { estacao: 'Blumenau', rio: 'itajai-acu', cidade: 'blumenau', nivel_m: 30, medido_em: '2026-10-06 14:50' },
      { estacao: 'Gaspar', rio: 'itajai-acu', cidade: 'gaspar', nivel_m: -0.5, medido_em: '2026-10-06 14:50' },
    ],
  }
  const transporte = async () => new Response(JSON.stringify(corpo), { status: 200, headers: { 'content-type': 'application/json' } })
  const tempoReal = await buscarTempoReal(undefined, transporte)
  return { tempoReal, nivelSc: new Map() as NivelSc, serie: { situacao: 'ok', series: {}, resgates: {}, janelaHoras: 48, geradoEm: AGORA }, agora: AGORA }
}
