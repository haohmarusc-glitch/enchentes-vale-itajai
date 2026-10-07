/**
 * 13ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): várias cidades de uma vez — uma lista dita,
 * ou as cidades que a pessoa segue; e o resumo de todas para copiar.
 */
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { executar, limparRetratos, type Ambiente, type DadosDoChat } from './executar'
import { textoDeAjuda } from './ajuda'
import { textoParaCopiarVarias } from './variasCidades'
import type { LeituraAoVivo } from '../dados/tempoReal'
import type { AoVivo } from '../dados/usarAoVivo'
import type { NivelSc } from '../dados/nivelSc'
import type { Cidade } from '../dados/tipos'
import type { CidadeSeguida } from '../logica/preferencias'
import type { Contexto } from './tipos'

const ler = (c: string) => JSON.parse(readFileSync(new URL(`../../../data/${c}`, import.meta.url), 'utf8'))
const estacoes = ler('estacoes.json')
const cat = catalogoDoCadastro(estacoes)
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const AGORA = new Date('2026-10-06T18:00:00Z') // 15h00 em Brasília
const minAtras = (m: number) => new Date(AGORA.getTime() - m * 60_000)
const passos = (texto: string) => {
  const r = interpretar(texto, cat, fora)
  assert.ok(r && r.tipo === 'comandos', `"${texto}" devia virar comando, veio ${JSON.stringify(r)}`)
  return r.passos
}

test('frases: duas ou mais cidades, ou "minhas cidades"; uma cidade só continua no motor', () => {
  assert.deepEqual(passos('como estão Blumenau e Gaspar?'), [{ tipo: 'varias_cidades', cidadeIds: ['blumenau', 'gaspar'] }])
  assert.deepEqual(passos('como estão Blumenau, Gaspar e Itajaí agora?'), [{ tipo: 'varias_cidades', cidadeIds: ['blumenau', 'gaspar', 'itajai'] }])
  assert.deepEqual(passos('como estão as minhas cidades?'), [{ tipo: 'varias_cidades', seguidas: true }])
  assert.deepEqual(passos('as cidades que eu sigo'), [{ tipo: 'varias_cidades', seguidas: true }])
  assert.deepEqual(passos('copiar o resumo das minhas cidades'), [{ tipo: 'varias_cidades', seguidas: true, copiar: true }])
  assert.deepEqual(passos('copiar o resumo de Blumenau e Gaspar'), [{ tipo: 'varias_cidades', cidadeIds: ['blumenau', 'gaspar'], copiar: true }])
  // Uma cidade só: continua sendo a pergunta "como está Blumenau?" (motor) e o resumo de uma cidade (2ª entrega).
  assert.equal(interpretar('como está Blumenau?', cat, fora), null)
  assert.deepEqual(passos('copiar resumo de Blumenau'), [{ tipo: 'copiar_resumo', cidadeId: 'blumenau' }])
  // Cidade fora do cadastro na lista: não vira comando com cidade a menos.
  // 18ª entrega: a cidade fora do cadastro é dita, em vez de a lista cair na barreira do presente.
  const pomerode = interpretar('como estão Blumenau e Pomerode?', cat, fora)
  assert.ok(pomerode && pomerode.tipo === 'esclarecer' && /"pomerode" não está entre as cidades/.test(pomerode.texto), JSON.stringify(pomerode))
})

test('texto para copiar: um rodapé só, Itajaí sem número, cidade sem leitura dita', () => {
  const t = textoParaCopiarVarias([
    { nome: 'Blumenau', texto: 'Blumenau — 6,40 m (faixa Alerta, na régua de Blumenau)\nMedido às 14:50 de 06/10 (há 10 min)\n\nNão é alerta oficial. Em emergência, ligue 199. Siga a Defesa Civil.' },
    { nome: 'Itajaí', texto: 'varias' },
    { nome: 'Taió', texto: null },
  ])!
  assert.equal(t.match(/Não é alerta oficial/g)?.length, 1)
  assert.match(t, /Itajaí: várias réguas/)
  assert.match(t, /Taió: sem leitura de agora/)
  assert.doesNotMatch(t, /https?:|pages\.dev/, 'sem endereço do site (D4)')
  assert.equal(textoParaCopiarVarias([{ nome: 'Taió', texto: null }]), null, 'sem nenhuma leitura de agora, não sai resumo')
})

const cidadeDoCadastro = (id: string): { cidade: Cidade; rioId: string } | null => {
  for (const [rioId, r] of Object.entries(estacoes.rios as Record<string, { cidades: Cidade[] }>)) {
    const c = r.cidades.find((x) => x.id === id)
    if (c) return { cidade: c, rioId }
  }
  return null
}
const leitura = (cidade: string, nivel_m: number, min: number): LeituraAoVivo => ({ estacao: cidade, rio: 'itajai-acu', cidade, nivel_m, medidoEm: minAtras(min), resgateDe: null })
const aoVivo: AoVivo = {
  tempoReal: { situacao: 'ok', leituras: [leitura('blumenau', 6.4, 10), leitura('gaspar', 4.0, 15)], chuva: [], chuvaOk: true, coletadoEm: AGORA, fonte: null },
  nivelSc: new Map() as NivelSc,
  serie: { situacao: 'ok', series: {}, resgates: {}, janelaHoras: 48, geradoEm: AGORA },
  agora: AGORA,
}
function ambiente(seguidas: CidadeSeguida[]) {
  const dados: DadosDoChat = {
    aoVivo: async () => aoVivo,
    cidade: cidadeDoCadastro,
    reguasNoMapa: () => [],
    tracado: async () => null,
    base: () => '',
    preferencias: {
      seguidas: () => seguidas,
      tornarMinha: () => seguidas,
      seguir: () => 'seguindo',
      deixarDeSeguir: () => seguidas,
      letra: () => {},
    },
  }
  const navegacoes: string[] = []
  const amb: Ambiente = { navegar: (p) => navegacoes.push(p), rotaAtual: () => '/', monitor: () => null, esperarMonitor: async () => null, dados }
  return { amb, navegacoes }
}
const rodar = (texto: string, amb: Ambiente) => {
  const r = interpretar(texto, cat, fora)
  assert.ok(r && r.tipo === 'comandos', texto)
  return executar(r.passos, amb, cat, fora, () => textoDeAjuda(fora, null))
}

beforeEach(() => limparRetratos())

test('executor: cada cidade na régua dela, numa resposta só; nada navega', async () => {
  const { amb, navegacoes } = ambiente([])
  const r = await rodar('como estão Blumenau, Gaspar e Taió?', amb)
  assert.match(r.texto, /^Agora, cada cidade na régua dela \(não compare os metros de uma cidade com os de outra\):/)
  assert.match(r.texto, /• Blumenau: 6,40 m \(Alerta, na régua de Blumenau\), medido às 14:50 de 06\/10 \(há 10 min\)/)
  assert.match(r.texto, /• Gaspar: 4,00 m \(Abaixo da atenção, na régua de Gaspar\)/)
  assert.match(r.texto, /• Taió: sem leitura de agora/)
  assert.match(r.texto, /não previsão[^]*199/)
  assert.deepEqual(r.sugestoes, ['copiar o resumo de Blumenau e Gaspar e Taió'])
  assert.deepEqual(navegacoes, [])
})

test('executor: as cidades seguidas; sem nenhuma, ensina a escolher; o resumo para copiar', async () => {
  const sem = await rodar('como estão as minhas cidades?', ambiente([]).amb)
  assert.match(sem.texto, /ainda não escolheu cidades/)
  const { amb } = ambiente([{ id: 'gaspar', rio: 'acu' }, { id: 'blumenau', rio: 'acu' }])
  const r = await rodar('como estão as minhas cidades?', amb)
  assert.ok(r.texto.indexOf('• Gaspar') < r.texto.indexOf('• Blumenau'), 'na ordem das seguidas (a sua primeiro)')
  const c = await rodar('copiar o resumo das minhas cidades', amb)
  assert.ok(c.copiar)
  assert.match(c.copiar!, /^Gaspar — 4,00 m/)
  assert.match(c.copiar!, /Blumenau — 6,40 m \(faixa Alerta, na régua de Blumenau\)/)
  assert.equal(c.copiar!.match(/Não é alerta oficial/g)?.length, 1)
})

test('a ajuda lista os pedidos da 13ª entrega', () => {
  const t = textoDeAjuda({ cidadeAtual: null, naMonitor: true, reguaAtual: null }, null).texto
  for (const f of ['como estão Blumenau e Gaspar?', 'como estão as minhas cidades?', 'copiar o resumo das minhas cidades']) assert.ok(t.includes(f), f)
})
