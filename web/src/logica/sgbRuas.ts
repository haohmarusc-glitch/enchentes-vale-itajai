/**
 * O que o Serviço Geológico do Brasil (SGB) mapeou onde fica cada ponto de cota de rua — contexto, nunca cota.
 *
 * `data/sgb-ruas.json` é derivado (`scripts/cruzar_sgb_ruas.py`): para cada ponto com coordenada, a classe de
 * suscetibilidade a inundação da carta do SGB/IPT (2013) e os setores de risco de ÁGUA (inundação, enxurrada,
 * enchente, alagamento) que o contêm. Decisão do Jefferson de 04/11/2026: entra na "minha rua" como camada de
 * contexto. O que esta camada NUNCA faz: virar cota, previsão ou cor; dizer que "Baixa" é seguro; falar de
 * deslizamento (fora do assunto do site).
 */

export interface SuscetibilidadeSgb {
  classe: string
  ano: number | string | null
  executor: string | null
}

export interface RiscoSgb {
  setor: string | null
  grau: string | null
  tipologias: string[]
  data: string | null
  local: string | null
}

export interface PontoSgb {
  rua: string
  bairro: string | null
  ponto: string | null
  lat: number
  lon: number
  suscetibilidade: SuscetibilidadeSgb | null
  risco: RiscoSgb[]
}

export interface CamadaInundacaoSgb {
  poligonos: number
  classe: Record<string, number>
  anos: string[]
}

export interface CamadaRiscoSgb {
  setores: number
  setores_de_agua: number
  grau: Record<string, number>
  anos: string[]
}

export interface CidadeSgb {
  nome: string
  camadas: { inundacao?: CamadaInundacaoSgb; risco?: CamadaRiscoSgb }
  pontos: PontoSgb[]
  pontos_por_classe: Record<string, number>
  pontos_em_setor_de_risco: number
}

export interface SgbRuas {
  _meta?: { regras?: string[]; fonte?: string; acesso?: { quando?: string } }
  cidades: Record<string, CidadeSgb>
}

export const CLASSES_SGB = ['Alta', 'Média', 'Baixa'] as const

/** Chave de um ponto: a mesma coordenada do cadastro de cotas, sem arredondar (o cruzamento copiou os números). */
export const chaveDoPonto = (lat: number, lon: number): string => `${lat}|${lon}`

export function indexarPontos(cidade: CidadeSgb | null | undefined): Map<string, PontoSgb> {
  const m = new Map<string, PontoSgb>()
  for (const p of cidade?.pontos ?? []) m.set(chaveDoPonto(p.lat, p.lon), p)
  return m
}

/** O contexto de um ponto de cota de rua, ou null quando o ponto não tem coordenada ou não foi cruzado. */
export function contextoDoPonto(indice: Map<string, PontoSgb>, c: { lat?: number; lon?: number }): PontoSgb | null {
  if (typeof c.lat !== 'number' || typeof c.lon !== 'number') return null
  return indice.get(chaveDoPonto(c.lat, c.lon)) ?? null
}

const ano = (v: number | string | null | undefined): string => (v === null || v === undefined || v === '' ? 'ano não informado' : String(v).slice(0, 4))

/**
 * Uma linha por ponto, só com o que o SGB diz. Fora da carta é dito como tal (não como "sem risco"); sem setor
 * de água, nada se diz sobre setor. Nunca metro, nunca "vai alagar".
 */
export function textoSgbDoPonto(p: PontoSgb): string | null {
  const partes: string[] = []
  if (p.suscetibilidade) {
    partes.push(`terreno com suscetibilidade ${p.suscetibilidade.classe} a inundação na carta do SGB (${ano(p.suscetibilidade.ano)})`)
  } else {
    partes.push('ponto fora da carta de suscetibilidade do SGB (não quer dizer sem risco)')
  }
  for (const r of p.risco) {
    const tipo = r.tipologias.length > 0 ? r.tipologias.join(' e ').toLowerCase() : 'água'
    partes.push(`em setor de risco ${(r.grau ?? 'não informado').toLowerCase()} de ${tipo} (SGB, ${ano(r.data)})`)
  }
  return partes.join(' · ')
}

/** O resumo da cidade para a dobra "o que o SGB mapeou aqui". Sem pontos cruzados, diz só o que a carta tem. */
export function textoSgbDaCidade(c: CidadeSgb): string[] {
  const linhas: string[] = []
  const inund = c.camadas.inundacao
  if (inund) {
    const classes = CLASSES_SGB.filter((k) => inund.classe[k]).map((k) => `${inund.classe[k]} ${k.toLowerCase()}`)
    linhas.push(
      `Carta de suscetibilidade a inundação (${inund.anos.join(', ') || 'ano não informado'}): ${inund.poligonos} áreas mapeadas em ${c.nome}` +
        (classes.length ? ` — ${classes.join(', ')}.` : '.'),
    )
  } else {
    linhas.push(`O SGB não publicou carta de suscetibilidade a inundação para ${c.nome} neste serviço.`)
  }
  const risco = c.camadas.risco
  if (risco) {
    const graus = Object.entries(risco.grau)
      .sort((a, b) => b[1] - a[1])
      .map(([g, n]) => `${n} ${g.toLowerCase()}`)
    linhas.push(
      risco.setores_de_agua > 0
        ? `Setorização de risco (${risco.anos.join(', ') || 'ano não informado'}): ${risco.setores_de_agua} ${risco.setores_de_agua === 1 ? 'setor' : 'setores'} de água (inundação, enxurrada, enchente ou alagamento) — ${graus.join(', ')} — de ${risco.setores} mapeados; os demais são de deslizamento e afins, fora do assunto deste site.`
        : `Setorização de risco: ${risco.setores} ${risco.setores === 1 ? 'setor' : 'setores'} em ${c.nome}, nenhum de água (são de deslizamento e afins).`,
    )
  }
  if (c.pontos.length > 0) {
    const porClasse = CLASSES_SGB.filter((k) => c.pontos_por_classe[k]).map((k) => `${c.pontos_por_classe[k]} em ${k.toLowerCase()}`)
    const fora = c.pontos_por_classe['fora da carta']
    linhas.push(
      `Dos ${c.pontos.length} pontos de cota de rua com coordenada, ${porClasse.join(', ')}` +
        (fora ? `, ${fora} fora da carta` : '') +
        (c.pontos_em_setor_de_risco > 0 ? `; ${c.pontos_em_setor_de_risco} dentro de setor de risco de água.` : '.'),
    )
  } else {
    linhas.push(`As cotas de rua de ${c.nome} não têm coordenada no cadastro: o cruzamento ponto a ponto não existe aqui.`)
  }
  return linhas
}
