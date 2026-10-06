/**
 * O que os comandos podem nomear, tirado do cadastro (`data/estacoes.json`) e de mais nada.
 * Cidade: as dos dois rios (Itajaí aparece nos dois; fica uma). Régua: as `estacoes_tempo_real` com código
 * DC e coordenada própria — as mesmas que o seletor do Monitor oferece.
 */
import { nomeDoLugar } from '../logica/reguasNoMapa'
import type { Catalogo, CidadeDoCatalogo, ReguaDoCatalogo } from './tipos'

interface CadastroMinimo {
  rios: Record<string, { cidades: { id: string; nome: string }[] }>
  estacoes_tempo_real?: {
    codigo?: string
    titulo: string
    nome_no_plano?: string
    cidade?: string
    lat?: number | null
    lon?: number | null
  }[]
}

export function catalogoDoCadastro(e: CadastroMinimo): Catalogo {
  const cidades: CidadeDoCatalogo[] = []
  for (const [rioId, rio] of Object.entries(e.rios)) {
    for (const c of rio.cidades) {
      if (cidades.some((x) => x.id === c.id)) continue
      cidades.push({ id: c.id, nome: c.nome, rio: rioId === 'itajai-mirim' ? 'mirim' : 'acu' })
    }
  }
  const reguas: ReguaDoCatalogo[] = (e.estacoes_tempo_real ?? [])
    .filter((r) => /^DC-\d+$/.test(r.codigo ?? '') && typeof r.lat === 'number' && typeof r.lon === 'number' && r.cidade)
    .map((r) => ({ codigo: r.codigo!, nome: nomeDoLugar(r), cidadeId: r.cidade! }))
    .sort((a, b) => a.codigo.localeCompare(b.codigo, 'pt-BR', { numeric: true }))
  return { cidades, reguas }
}
