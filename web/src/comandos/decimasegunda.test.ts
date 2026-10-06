/**
 * 12ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): o Monitor, peça por peça — enquadrar um rio
 * inteiro ou as barragens, fechar o painel da cidade, abrir e fechar o menu de cidades.
 */
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { executar, limparRetratos, type Ambiente } from './executar'
import { textoDeAjuda } from './ajuda'
import type { ControleMonitor, Retrato } from './ponte'
import type { Contexto, Fundo } from './tipos'

const ler = (c: string) => JSON.parse(readFileSync(new URL(`../../../data/${c}`, import.meta.url), 'utf8'))
const cat = catalogoDoCadastro(ler('estacoes.json'))
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const passos = (texto: string) => {
  const r = interpretar(texto, cat, fora)
  assert.ok(r && r.tipo === 'comandos', `"${texto}" devia virar comando, veio ${JSON.stringify(r)}`)
  return r.passos
}

test('frases; "mostrar o Itajaí-Açu" continua abrindo a página do rio', () => {
  assert.deepEqual(passos('ver o Itajaí-Mirim no mapa'), [{ tipo: 'enquadrar', alvo: 'rio', rioId: 'itajai-mirim' }])
  assert.deepEqual(passos('zoom no Itajaí-Açu'), [{ tipo: 'enquadrar', alvo: 'rio', rioId: 'itajai-acu' }])
  assert.deepEqual(passos('enquadrar o rio Itajaí-Açu inteiro'), [{ tipo: 'enquadrar', alvo: 'rio', rioId: 'itajai-acu' }])
  assert.deepEqual(passos('zoom nas barragens'), [{ tipo: 'enquadrar', alvo: 'barragens' }])
  assert.deepEqual(passos('onde ficam as barragens?'), [{ tipo: 'enquadrar', alvo: 'barragens' }])
  assert.deepEqual(passos('fechar o painel'), [{ tipo: 'fechar_painel' }])
  assert.deepEqual(passos('abrir o menu de cidades'), [{ tipo: 'menu_cidades', acao: 'abrir' }])
  assert.deepEqual(passos('fechar o menu'), [{ tipo: 'menu_cidades', acao: 'fechar' }])
  assert.deepEqual(passos('mostrar o Itajaí-Açu'), [{ tipo: 'abrir_rota', rota: '/acu', descricao: 'a página do Itajaí-Açu' }])
  // No Monitor, o mesmo pedido é o rio no mapa.
  const noMonitor = interpretar('mostrar o Itajaí-Mirim', cat, { cidadeAtual: null, naMonitor: true, reguaAtual: null })
  assert.deepEqual(noMonitor, { tipo: 'comandos', passos: [{ tipo: 'enquadrar', alvo: 'rio', rioId: 'itajai-mirim' }] })
  assert.deepEqual(passos('mostrar as barragens no mapa'), [{ tipo: 'enquadrar', alvo: 'barragens' }])
  // "Como estão as barragens?" continua sendo o estado das comportas (5ª entrega).
  assert.deepEqual(passos('como estão as barragens?'), [{ tipo: 'barragens' }])
})

function monitorFalso(cidade: string | null) {
  const chamadas: string[] = []
  const c: ControleMonitor = {
    cidade,
    pronto: true,
    estado: () => ({ cidade, cidadeNome: cidade, regua: null, reguas: [], fundo: 'escuro' as Fundo, camada: null, camadasDisponiveis: [], reproducao: null }),
    escolherRegua: () => ({ ok: true, texto: '' }),
    enquadrarCidade: () => ({ ok: true, texto: '' }),
    zoom: () => ({ ok: true, texto: '' }),
    verBacia: () => ({ ok: true, texto: '' }),
    fundo: () => ({ ok: true, texto: '' }),
    camada: () => ({ ok: true, texto: '' }),
    aoVivo: () => ({ ok: true, texto: '' }),
    enquadrar: (a) => (chamadas.push(a.tipo === 'rio' ? `rio:${a.rioId}` : 'barragens'), { ok: true, texto: 'enquadrado' }),
    fecharPainel: () => (chamadas.push('fechar'), { ok: true, texto: 'painel fechado' }),
    menuDeCidades: (a) => (chamadas.push(`menu:${a}`), { ok: true, texto: `menu ${a}` }),
    explicar: () => null,
    retrato: (): Retrato => ({ rota: `/monitor/${cidade}`, cidade }),
    restaurar: () => ({ ok: true, texto: 'ok' }),
  }
  return { c, chamadas }
}

beforeEach(() => limparRetratos())

test('executor: abre o Monitor se preciso e usa a ponte', async () => {
  let atual: ReturnType<typeof monitorFalso> | null = null
  const navegacoes: string[] = []
  const amb: Ambiente = {
    navegar: (para) => {
      navegacoes.push(para)
      const m = para.match(/^\/monitor(?:\/([a-z-]+))?/)
      atual = m ? monitorFalso(m[1] ?? null) : null
    },
    rotaAtual: () => '/',
    monitor: () => atual?.c ?? null,
    esperarMonitor: async (cid) => (atual && atual.c.cidade === cid ? atual.c : null),
    dados: { aoVivo: async () => null, cidade: () => null, reguasNoMapa: () => [], tracado: async () => null, base: () => '' },
  }
  const rodar = (texto: string, ctx: Contexto = fora) => {
    const r = interpretar(texto, cat, ctx)
    assert.ok(r && r.tipo === 'comandos', texto)
    return executar(r.passos, amb, cat, ctx, () => textoDeAjuda(fora, null))
  }
  assert.match((await rodar('ver o Itajaí-Mirim no mapa')).texto, /enquadrado/)
  assert.deepEqual(navegacoes, ['/monitor'])
  const noMonitor: Contexto = { cidadeAtual: null, naMonitor: true, reguaAtual: null }
  await rodar('zoom nas barragens', noMonitor)
  await rodar('fechar o painel', noMonitor)
  await rodar('abrir o menu de cidades', noMonitor)
  assert.deepEqual((atual as ReturnType<typeof monitorFalso> | null)!.chamadas, ['rio:itajai-mirim', 'barragens', 'fechar', 'menu:abrir'])
})

test('a ajuda lista os pedidos da 12ª entrega', () => {
  const t = textoDeAjuda({ cidadeAtual: null, naMonitor: true, reguaAtual: null }, null).texto
  for (const f of ['ver o Itajaí-Mirim no mapa', 'zoom nas barragens', 'fechar o painel', 'abrir o menu de cidades']) assert.ok(t.includes(f), f)
})
