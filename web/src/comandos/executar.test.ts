import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { executar, limparRetratos, type Ambiente } from './executar'
import { textoDeAjuda } from './ajuda'
import type { ControleMonitor, Retrato } from './ponte'
import type { Contexto, Fundo, Passo } from './tipos'

const cat = catalogoDoCadastro(JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8')))
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const ajuda = () => textoDeAjuda(fora, null)

/** Um Monitor de mentira que registra o que lhe pediram, como o de verdade responderia. */
function monitorFalso(cidade: string | null, opcoes: { camadas?: { arquivo: string; rotulo: string }[]; falhaZoom?: boolean } = {}) {
  const chamadas: string[] = []
  let fundo: Fundo = 'escuro'
  let regua: string | null = null
  let camada: string | null = null
  const c: ControleMonitor = {
    cidade,
    pronto: true,
    estado: () => ({
      cidade,
      cidadeNome: cidade,
      regua: regua ? { codigo: regua, rotulo: regua } : null,
      reguas: [],
      fundo,
      camada,
      camadasDisponiveis: opcoes.camadas ?? [],
      reproducao: null,
    }),
    escolherRegua: (codigo) => { chamadas.push(`regua:${codigo}`); regua = codigo === 'todas' ? null : codigo; return { ok: true, texto: `Régua ${codigo}.` } },
    enquadrarCidade: () => { chamadas.push('enquadrar'); return { ok: true, texto: 'Enquadrado.' } },
    zoom: (s) => { chamadas.push(`zoom:${s}`); return opcoes.falhaZoom ? { ok: false, texto: 'Zoom no limite.' } : { ok: true, texto: 'Zoom.' } },
    verBacia: () => { chamadas.push('bacia'); return { ok: true, texto: 'Bacia.' } },
    fundo: (f) => { chamadas.push(`fundo:${f}`); fundo = f; return { ok: true, texto: `Fundo ${f}.` } },
    camada: (a) => { chamadas.push(`camada:${a}`); camada = a === 'off' ? null : a; return { ok: true, texto: `Camada ${a}.` } },
    aoVivo: () => { chamadas.push('aovivo'); return { ok: true, texto: 'Ao vivo.' } },
    explicar: () => ({ cidadeNome: 'Lontras', faixa: 'Sem dado', motivoCinza: 'valor impossível.', posicao: 'Pino na coordenada do cadastro.', equivalencia: 'Equivalência não confirmada.' }),
    retrato: (): Retrato => ({ rota: cidade ? `/monitor/${cidade}` : '/monitor', cidade, regua, fundo, camada }),
    restaurar: (r) => { chamadas.push(`restaurar:${r.fundo}:${r.regua ?? '-'}:${r.camada ?? '-'}`); fundo = r.fundo ?? fundo; regua = r.regua ?? null; camada = r.camada ?? null; return { ok: true, texto: 'ok' } },
  }
  return { c, chamadas }
}

/** Ambiente: navegar troca o Monitor "montado" pelo da cidade da rota, como o roteador faria. */
function ambiente(inicial: ReturnType<typeof monitorFalso> | null, rota = '/acu', ops: { monitorNaoAbre?: boolean } = {}) {
  const montados = new Map<string | null, ReturnType<typeof monitorFalso>>()
  let atual = inicial
  if (inicial) montados.set(inicial.c.cidade, inicial)
  let r = rota
  const navegacoes: string[] = []
  const amb: Ambiente = {
    navegar: (para) => {
      navegacoes.push(para)
      r = para
      const m = para.match(/^\/monitor(?:\/([a-z-]+))?/)
      if (m && !ops.monitorNaoAbre) {
        const cid = m[1] ?? null
        if (!montados.has(cid)) montados.set(cid, monitorFalso(cid))
        atual = montados.get(cid)!
      } else {
        atual = null
      }
    },
    rotaAtual: () => r,
    monitor: () => atual?.c ?? null,
    esperarMonitor: async (cid) => (atual && atual.c.cidade === cid ? atual.c : null),
  }
  return { amb, navegacoes, montados, atual: () => atual }
}

beforeEach(() => limparRetratos())

test('fora do Monitor, pedido de mapa abre o Monitor da cidade em foco e só então executa', async () => {
  const { amb, navegacoes, montados } = ambiente(null, '/acu/timbo')
  const ctx = { cidadeAtual: 'timbo', naMonitor: false, reguaAtual: null }
  const s = await executar([{ tipo: 'fundo', fundo: 'satelite' }], amb, cat, ctx, ajuda)
  assert.deepEqual(navegacoes, ['/monitor/timbo'])
  assert.deepEqual(montados.get('timbo')!.chamadas, ['fundo:satelite'])
  assert.equal(s.texto, 'Fundo satelite.')
})

test('encadeado em ordem: cidade, régua da cidade, fundo', async () => {
  const { amb, montados } = ambiente(null)
  const passos: Passo[] = [{ tipo: 'ir_cidade', cidadeId: 'timbo' }, { tipo: 'aproximar_regua' }, { tipo: 'fundo', fundo: 'satelite' }]
  const s = await executar(passos, amb, cat, fora, ajuda)
  assert.deepEqual(montados.get('timbo')!.chamadas, ['enquadrar', 'fundo:satelite'])
  assert.match(s.texto, /^Monitor de Timbó aberto e enquadrado\. Enquadrado\. Fundo satelite\.$/)
})

test('um passo falha: os seguintes não rodam, e a resposta diz o que já foi feito', async () => {
  const m = monitorFalso('blumenau', { falhaZoom: true })
  const { amb } = ambiente(m, '/monitor/blumenau')
  const ctx = { cidadeAtual: 'blumenau', naMonitor: true, reguaAtual: null }
  const s = await executar([{ tipo: 'fundo', fundo: 'mapa' }, { tipo: 'zoom', sentido: 'mais' }, { tipo: 'ver_bacia' }], amb, cat, ctx, ajuda)
  assert.deepEqual(m.chamadas, ['fundo:mapa', 'zoom:mais'])
  assert.match(s.texto, /^Feito: Fundo mapa\. Zoom no limite\. Os passos seguintes não foram feitos\.$/)
})

test('o Monitor não abre: diz que não conseguiu, sem fingir', async () => {
  const { amb } = ambiente(null, '/acu', { monitorNaoAbre: true })
  const s = await executar([{ tipo: 'ir_cidade', cidadeId: 'gaspar' }], amb, cat, fora, ajuda)
  assert.match(s.texto, /Não consegui abrir o Monitor de Gaspar/)
})

test('régua DC fora de Itajaí: abre o Monitor de Itajaí e escolhe a régua', async () => {
  const m = monitorFalso('blumenau')
  const { amb, montados } = ambiente(m, '/monitor/blumenau')
  await executar([{ tipo: 'escolher_regua', codigo: 'DC-05' }], amb, cat, { cidadeAtual: 'blumenau', naMonitor: true, reguaAtual: null }, ajuda)
  assert.deepEqual(montados.get('itajai')!.chamadas, ['regua:DC-05'])
})

test('camadas: sem ano e várias opções, pergunta; com ano, liga a do ano; sem camada na cidade, diz', async () => {
  const camadas = [{ arquivo: 'a.geojson', rotulo: 'Novembro de 2008 — mancha' }, { arquivo: 'b.geojson', rotulo: 'Setembro de 2011 — mancha' }]
  const m = monitorFalso('itajai', { camadas })
  const { amb } = ambiente(m, '/monitor/itajai')
  const ctx = { cidadeAtual: 'itajai', naMonitor: true, reguaAtual: null }
  const pergunta = await executar([{ tipo: 'camada', acao: 'ligar' }], amb, cat, ctx, ajuda)
  assert.match(pergunta.texto, /tem 2 camadas\. Qual delas\?/)
  assert.deepEqual(m.chamadas, [])
  await executar([{ tipo: 'camada', acao: 'ligar', ano: '2008' }], amb, cat, ctx, ajuda)
  assert.deepEqual(m.chamadas, ['camada:a.geojson'])
  const vazio = monitorFalso('taio')
  const s = await executar([{ tipo: 'camada', acao: 'ligar' }], ambiente(vazio, '/monitor/taio').amb, cat, { ...ctx, cidadeAtual: 'taio' }, ajuda)
  assert.match(s.texto, /Não há camadas de cheia cadastradas para taio/)
})

test('voltar restaura vista, régua, fundo e camada de antes da última ação', async () => {
  const m = monitorFalso('itajai', { camadas: [{ arquivo: 'a.geojson', rotulo: '2008' }] })
  const { amb } = ambiente(m, '/monitor/itajai')
  const ctx = { cidadeAtual: 'itajai', naMonitor: true, reguaAtual: null }
  await executar([{ tipo: 'escolher_regua', codigo: 'DC-03' }], amb, cat, ctx, ajuda)
  await executar([{ tipo: 'fundo', fundo: 'satelite' }, { tipo: 'camada', acao: 'ligar', ano: '2008' }], amb, cat, ctx, ajuda)
  const s = await executar([{ tipo: 'voltar' }], amb, cat, ctx, ajuda)
  assert.match(s.texto, /Voltei ao mapa de antes/)
  // Antes do segundo pedido: régua DC-03, fundo escuro, sem camada.
  assert.equal(m.chamadas.at(-1), 'restaurar:escuro:DC-03:-')
})

test('voltar depois de navegar de outra página volta à página', async () => {
  const { amb, navegacoes } = ambiente(null, '/acu/gaspar')
  await executar([{ tipo: 'ir_cidade', cidadeId: 'gaspar' }], amb, cat, { cidadeAtual: 'gaspar', naMonitor: false, reguaAtual: null }, ajuda)
  const s = await executar([{ tipo: 'voltar' }], amb, cat, fora, ajuda)
  assert.equal(s.texto, 'Voltei à página de antes.')
  assert.equal(navegacoes.at(-1), '/acu/gaspar')
  const nada = await executar([{ tipo: 'voltar' }], amb, cat, fora, ajuda)
  assert.equal(nada.texto, 'Não há ação do chat para desfazer.')
})

test('perguntas sobre a tela não mudam o mapa e usam o mesmo texto do painel', async () => {
  const m = monitorFalso('lontras')
  const { amb } = ambiente(m, '/monitor/lontras')
  const ctx = { cidadeAtual: 'lontras', naMonitor: true, reguaAtual: null }
  const cinza = await executar([{ tipo: 'por_que_cinza' }], amb, cat, ctx, ajuda)
  assert.equal(cinza.texto, 'Lontras está cinza: valor impossível.')
  const coord = await executar([{ tipo: 'coordenada' }], amb, cat, ctx, ajuda)
  assert.equal(coord.texto, 'Pino na coordenada do cadastro. Equivalência não confirmada.')
  assert.deepEqual(m.chamadas, [])
  const fora2 = await executar([{ tipo: 'por_que_cinza', cidadeId: 'lontras' }], ambiente(null).amb, cat, fora, ajuda)
  assert.equal(fora2.link?.para, '/monitor/lontras')
})

test('página da cidade e rotas fixas', async () => {
  const { amb, navegacoes } = ambiente(null)
  await executar([{ tipo: 'abrir_pagina', cidadeId: 'gaspar', aba: 'historico' }], amb, cat, fora, ajuda)
  await executar([{ tipo: 'abrir_pagina', cidadeId: 'brusque', aba: 'rua' }], amb, cat, fora, ajuda)
  await executar([{ tipo: 'abrir_pagina', cidadeId: 'itajai' }], amb, cat, fora, ajuda)
  assert.deepEqual(navegacoes, ['/acu/gaspar?aba=historico', '/mirim/brusque?aba=rua', '/itajai'])
})
