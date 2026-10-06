/**
 * O que os comandos podem nomear, tirado do cadastro (`data/estacoes.json`) e de mais nada.
 * Cidade: as dos dois rios (Itajaí aparece nos dois; fica uma). Régua: as `estacoes_tempo_real` com código
 * DC e coordenada própria — as mesmas que o seletor do Monitor oferece.
 *
 * 2ª entrega (docs/CHAT-GLOBAL-COMANDOS.md): a árvore de cada rio (`_topologia`) e os pontos de confluência
 * que o cadastro GRAVOU. Rio sem ponto gravado entra em `semPonto`, com o motivo: o chat diz que não há
 * ponto, nunca centra o mapa num lugar estimado.
 */
import { nomeDoLugar } from '../logica/reguasNoMapa'
import { normalizar } from './normalizar'
import type { Catalogo, CidadeDoCatalogo, Confluencia, ConfluenciaSemPonto, ReguaDoCatalogo, TopologiaDoRio } from './tipos'

interface CadastroMinimo {
  rios: Record<
    string,
    {
      nome?: string
      cidades: { id: string; nome: string; sub_bacia?: string | null; rio_chega_a?: { rio?: string; ponto?: number[]; fonte?: string } }[]
      _topologia?: {
        tronco_sequencia?: string[]
        cabeceiras_paralelas?: string[]
        confluencia_cabeceiras?: { lat?: number; lon?: number; nasce?: string; fonte?: string }
        afluentes_laterais?: { id: string; rio?: string; entra_perto_de?: string }[]
        afluentes_rios?: { nome: string; entra_perto_de?: string; ponto_exato?: string }[]
      }
    }
  >
  estacoes_tempo_real?: {
    codigo?: string
    titulo: string
    nome_no_plano?: string
    cidade?: string
    lat?: number | null
    lon?: number | null
  }[]
}

/**
 * A coordenada que o `ponto_exato` do Benedito ESCREVE ("… em −26,89134, −49,23557 (lat, lon) …"). O campo
 * é texto porque guarda também o método; o teste trava a leitura contra o cadastro de verdade, e um texto
 * sem "(lat, lon)" não vira ponto.
 */
export function pontoDoTexto(texto: string | undefined): { lat: number; lon: number } | null {
  const m = (texto ?? '').match(/([−-]\d{1,2},\d+),\s*([−-]\d{1,2},\d+)\s*\(lat, ?lon\)/)
  if (!m) return null
  const num = (s: string) => Number(s.replace('−', '-').replace(',', '.'))
  const lat = num(m[1]!)
  const lon = num(m[2]!)
  return Number.isFinite(lat) && Number.isFinite(lon) ? { lat, lon } : null
}

const SEM_FONTE = 'O cadastro não tem a coordenada da confluência: só diz perto de que cidade o rio entra.'

export function catalogoDoCadastro(e: CadastroMinimo): Catalogo {
  const cidades: CidadeDoCatalogo[] = []
  for (const [rioId, rio] of Object.entries(e.rios)) {
    for (const c of rio.cidades) {
      if (cidades.some((x) => x.id === c.id)) continue
      cidades.push({ id: c.id, nome: c.nome, rio: rioId === 'itajai-mirim' ? 'mirim' : 'acu' })
    }
  }
  const nome = (id: string) => cidades.find((c) => c.id === id)?.nome ?? id
  const reguas: ReguaDoCatalogo[] = (e.estacoes_tempo_real ?? [])
    .filter((r) => /^DC-\d+$/.test(r.codigo ?? '') && typeof r.lat === 'number' && typeof r.lon === 'number' && r.cidade)
    .map((r) => ({ codigo: r.codigo!, titulo: r.titulo, nome: nomeDoLugar(r), cidadeId: r.cidade! }))
    .sort((a, b) => a.codigo.localeCompare(b.codigo, 'pt-BR', { numeric: true }))

  const confluencias: Confluencia[] = []
  const semPonto: ConfluenciaSemPonto[] = []
  const topologia: TopologiaDoRio[] = []
  const foraDaArvore: NonNullable<Catalogo['foraDaArvore']> = []
  for (const [rioId, rio] of Object.entries(e.rios)) {
    const t = rio._topologia
    for (const c of rio.cidades) {
      const p = c.rio_chega_a?.ponto
      if (c.rio_chega_a?.rio && p && typeof p[0] === 'number' && typeof p[1] === 'number') {
        // O rio da cidade é o `sub_bacia` do cadastro ("Rio Trombudo"); sem ele, o nome da cidade.
        const rioDela = c.sub_bacia ?? c.nome
        foraDaArvore.push({ id: c.id, rio: rioDela, chegaA: c.rio_chega_a.rio, lat: p[0], lon: p[1], fonte: c.rio_chega_a.fonte ?? '' })
        confluencias.push({
          id: c.id,
          nome: `Encontro do ${rioDela} com o ${c.rio_chega_a.rio}`,
          chaves: [normalizar(rioDela).replace(/^rio /, ''), normalizar(c.nome)],
          lat: p[0],
          lon: p[1],
          fonte: c.rio_chega_a.fonte ?? '',
        })
      }
    }
    if (!t) continue
    const cc = t.confluencia_cabeceiras
    if (cc && typeof cc.lat === 'number' && typeof cc.lon === 'number') {
      confluencias.push({
        id: `${rioId}-nasce`,
        nome: `Encontro do Itajaí do Oeste com o Itajaí do Sul, onde nasce o ${rio.nome ?? 'Itajaí-Açu'}`,
        chaves: ['itajai do oeste', 'itajai do sul', 'oeste', 'cabeceiras', 'nasce', 'itajai acu', 'acu'],
        lat: cc.lat,
        lon: cc.lon,
        fonte: cc.fonte ?? '',
      })
    }
    for (const a of t.afluentes_rios ?? []) {
      const chave = normalizar(a.nome.replace(/\(.*\)/, '')).replace(/^rio /, '').trim()
      const chaves = [chave, ...(chave === 'luis alves' ? ['luiz alves'] : [])]
      const ponto = pontoDoTexto(a.ponto_exato)
      if (ponto) {
        // A fonte do ponto: as frases do `ponto_exato` que dizem como ele foi medido (a posição na ordem do rio
        // fica para "o que fica a montante").
        const fonte = (a.ponto_exato ?? '').split(/(?<=\.)\s+(?=[A-ZÁÉÍÓÚ])/).filter((f) => /OpenStreetMap|Método|docs\//.test(f)).join(' ')
        confluencias.push({ id: chave.replace(/ /g, '-'), nome: `Confluência do ${a.nome.replace(/\s*\(.*\)/, '')} com o ${rio.nome ?? rioId}`, chaves, ...ponto, fonte: fonte || (a.ponto_exato ?? '') })
      } else {
        semPonto.push({ id: chave.replace(/ /g, '-'), nome: a.nome, chaves, motivo: a.ponto_exato ? `O cadastro diz: "${a.ponto_exato}"` : SEM_FONTE })
      }
    }
    for (const l of t.afluentes_laterais ?? []) {
      const rioNome = (l.rio ?? '').replace(/\s*\(.*\)/, '')
      const chave = normalizar(rioNome).replace(/^(?:rio|ribeirao) /, '')
      if (!chave || confluencias.some((c) => c.chaves.includes(chave)) || semPonto.some((s) => s.chaves.includes(chave))) continue
      // O outro nome do rio, entre parênteses no cadastro ("Rio Hercílio (Itajaí do Norte)"), também nomeia.
      const outroNome = (l.rio ?? '').match(/\(([^)]+)\)/)?.[1]
      const outra = outroNome && !/desagua|deságua/i.test(outroNome) ? [normalizar(outroNome)] : []
      semPonto.push({
        id: l.id,
        nome: rioNome,
        chaves: [...new Set([chave, ...outra, normalizar(nome(l.id))])],
        motivo: `${SEM_FONTE} O ${rioNome} entra perto de ${nome(l.entra_perto_de ?? '')}.`,
      })
    }
    topologia.push({
      rioId,
      tronco: t.tronco_sequencia ?? [],
      cabeceiras: t.cabeceiras_paralelas ?? [],
      laterais: (t.afluentes_laterais ?? []).map((l) => ({ id: l.id, rio: l.rio ?? '', entraPertoDe: l.entra_perto_de ?? '' })),
      afluentesSemRegua: (t.afluentes_rios ?? []).map((a) => ({ nome: a.nome, entraPertoDe: a.entra_perto_de ?? '', pontoExato: a.ponto_exato ?? null })),
    })
  }
  return { cidades, reguas, confluencias, semPonto, topologia, foraDaArvore }
}
