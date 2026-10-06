/**
 * O seletor de régua do Monitor de Itajaí (pedido do Jefferson, 06/10/2026).
 *
 * Itajaí tem onze réguas e nenhum "nível da cidade". O Monitor abre enquadrando as onze; no celular,
 * achar uma delas era arrastar e pinçar o mapa. O seletor fica na própria tela (sem página nova):
 * "Todas as 11 réguas" é o padrão, e escolher uma centraliza o mapa nela e abre o painel dela.
 */
import type { Vista } from './mapaCanvas'
import { type Limites, vistaAcimaDaFolha, vistaDaCidade } from './vistaDaCidade'

/** Largura da tela, em km, ao abrir uma régua: o bairro em volta dela, com o rio. */
export const KM_NA_TELA_REGUA = 3

export type Opcao = { valor: string; rotulo: string }

/** O valor da opção "todas". Vazio, porque nenhuma régua tem código vazio no mapa. */
export const TODAS = ''

type ReguaDoSeletor = { codigo: string; titulo: string; nome: string; cidade: string | null }

/** A chave de uma régua no mapa — a mesma que o toque usa (`codigo || titulo`). */
export const chaveDaRegua = (r: Pick<ReguaDoSeletor, 'codigo' | 'titulo'>) => r.codigo || r.titulo

/** "Todas as N réguas" e uma opção por régua da cidade, em ordem de código (DC-01, DC-02…). */
export function opcoesDoSeletor(reguas: readonly ReguaDoSeletor[], cidadeId: string): Opcao[] {
  const daCidade = reguas
    .filter((r) => r.cidade === cidadeId)
    .sort((a, b) => chaveDaRegua(a).localeCompare(chaveDaRegua(b), 'pt-BR', { numeric: true }))
  if (daCidade.length < 2) return []
  return [
    { valor: TODAS, rotulo: `Todas as ${daCidade.length} réguas` },
    ...daCidade.map((r) => ({
      valor: chaveDaRegua(r),
      rotulo: r.codigo && r.nome && r.nome !== r.codigo ? `${r.codigo} · ${r.nome}` : chaveDaRegua(r),
    })),
  ]
}

/**
 * A vista centrada na régua, com o painel dela aberto: no celular, o ponto sobe para acima da folha
 * (`vistaAcimaDaFolha`), como acontece com o pino de cidade.
 */
export function vistaDaRegua(
  regua: { lat: number; lon: number },
  limites: Limites,
  largura: number,
  altura: number,
  margem?: number,
): Vista | null {
  const v = vistaDaCidade([regua.lat, regua.lon], limites, KM_NA_TELA_REGUA)
  return v ? vistaAcimaDaFolha(v, limites, largura, altura, margem) : null
}
