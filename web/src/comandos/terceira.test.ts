/**
 * 3ª entrega dos comandos do chat: a rua no mapa (docs/CHAT-GLOBAL-COMANDOS.md, "Rua destacada sobre as
 * manchas"). Com as bases de verdade: vias de Itajaí, cruzamento rua × mancha e cotas de rua.
 */
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { executar, limparRetratos, type Ambiente, type DadosDoChat } from './executar'
import { textoDeAjuda } from './ajuda'
import { intersecoes, pontosDaRua, ruasSemCoordenada, textoDaRuaItajai, textoDosPontos } from './ruas'
import { acharVias, nomeLegivelDaVia, partesDaVia } from '../logica/viasItajai'
import type { RuasPorMancha } from '../chat-local/motor'
import type { CotaRua } from '../dados/tipos'
import type { ControleMonitor, MarcaNoMapa, Retrato } from './ponte'
import type { Contexto, Fundo } from './tipos'

const ler = (caminho: string) => JSON.parse(readFileSync(new URL(`../../../data/${caminho}`, import.meta.url), 'utf8'))
const cat = catalogoDoCadastro(ler('estacoes.json'))
const vias = ler('vias/itajai.geojson') as GeoJSON.FeatureCollection
const nomesDasVias = [...new Set(vias.features.map((f) => f.properties?.nome as string))]
const contagem: Record<string, number> = {}
for (const f of vias.features) contagem[f.properties?.nome] = (contagem[f.properties?.nome] ?? 0) + 1
const tabela = ler('manchas/itajai/ruas-por-mancha.json') as RuasPorMancha
const cotas = (ler('cotas-ruas.json') as { cotas: CotaRua[] }).cotas
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }

const passos = (texto: string, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', `"${texto}" devia virar comando, veio ${JSON.stringify(r)}`)
  return r.passos
}

// ---------------------------------------------------------------- casar o nome da via

test('via: tipo e núcleo do nome, como a Prefeitura abrevia e como a pessoa escreve', () => {
  assert.deepEqual(partesDaVia('R.Hamilton Pimentel'), { tipo: 'r', nucleo: 'hamilton pimentel' })
  assert.deepEqual(partesDaVia('rua hamilton pimentel'), { tipo: 'r', nucleo: 'hamilton pimentel' })
  assert.deepEqual(partesDaVia('Trav.Jorge Mattos'), { tipo: 'trav', nucleo: 'jorge mattos' })
  assert.deepEqual(partesDaVia('Bartolomeu Pruner'), { tipo: null, nucleo: 'bartolomeu pruner' })
  assert.equal(nomeLegivelDaVia('Av.7 de Setembro'), 'Avenida 7 de Setembro')
})

test('via: o nome inteiro vence o pedaço; o tipo escrito separa os homônimos; sem tipo, pergunta', () => {
  assert.deepEqual(acharVias('rua hamilton pimentel', nomesDasVias), ['R.Hamilton Pimentel'])
  assert.deepEqual(acharVias('avenida 7 de setembro', nomesDasVias), ['Av.7 de Setembro'])
  assert.deepEqual(acharVias('avenida carlos drumond de andrade', nomesDasVias), ['Av.Carlos Drumond de Andrade'])
  assert.deepEqual(acharVias('rua carlos drumond de andrade', nomesDasVias), ['R.Carlos Drumond de Andrade'])
  assert.deepEqual(acharVias('carlos drumond de andrade', nomesDasVias), ['Av.Carlos Drumond de Andrade', 'R.Carlos Drumond de Andrade'])
  assert.deepEqual(acharVias('rua que nao existe aqui', nomesDasVias), [])
})

// ---------------------------------------------------------------- interpretar

test('pedidos de rua: com verbo, com a cidade e o ano no fim; sem verbo continua pergunta', () => {
  assert.deepEqual(passos('mostrar a rua Hamilton Pimentel'), [{ tipo: 'rua', foco: 'mostrar', texto: 'rua hamilton pimentel' }])
  assert.deepEqual(passos('zoom na Avenida 7 de Setembro, Itajaí'), [{ tipo: 'rua', foco: 'mostrar', texto: 'avenida 7 de setembro', cidadeId: 'itajai' }])
  assert.deepEqual(passos('onde fica a rua Adriano Kormann em Gaspar?'), [{ tipo: 'rua', foco: 'mostrar', texto: 'rua adriano kormann', cidadeId: 'gaspar' }])
  assert.deepEqual(passos('manchas na rua Hamilton Pimentel'), [{ tipo: 'rua', foco: 'manchas', texto: 'rua hamilton pimentel' }])
  assert.deepEqual(passos('mancha de 2008 na Avenida 7 de Setembro em Itajaí'), [
    { tipo: 'rua', foco: 'manchas', texto: 'avenida 7 de setembro', cidadeId: 'itajai', ano: '2008' },
  ])
  // "Rua Brusque" (em Itajaí) é nome de rua, não a cidade de Brusque.
  assert.deepEqual(passos('mostrar a rua Brusque'), [{ tipo: 'rua', foco: 'mostrar', texto: 'rua brusque' }])
  assert.deepEqual(passos('remover destaque'), [{ tipo: 'remover_destaque' }])
  for (const q of ['Rua XV de Novembro, Blumenau', 'a rua Hamilton Pimentel alagou em 2011?', 'quantas cheias passaram da cota da Rua São Rafael em Blumenau?']) {
    assert.equal(interpretar(q, cat, fora), null, q)
  }
})

// ---------------------------------------------------------------- textos

test('rua de Itajaí: interseção com o cenário, nunca "alagou"; sem interseção não é rua segura', () => {
  const todas = textoDaRuaItajai({ nome: 'Av.7 de Setembro', tabela, evento: null, trechos: 1 })
  assert.match(todas, /^Avenida 7 de Setembro destacada no mapa das manchas de Itajaí/)
  assert.match(todas, /Interseção com as manchas: julho de 1983 \(15%\); agosto de 1984 \(47%\); novembro de 2008 \(32%\)/)
  assert.match(todas, /Sem interseção: 2001/)
  assert.match(todas, /rua fora da mancha não quer dizer rua segura/)
  assert.ok(!/alagou|vai alagar|seguro para/.test(todas.replace('cada casa alagou', '')))
  const em2008 = textoDaRuaItajai({ nome: 'Av.7 de Setembro', tabela, evento: '2008-11', trechos: 3 })
  assert.match(em2008, /Interseção com o cenário de novembro de 2008: 32% do trecho \(727 m\) dentro da mancha/)
  assert.match(em2008, /A base tem 3 trechos com este nome/)
  const nao = textoDaRuaItajai({ nome: 'Av.7 de Setembro', tabela, evento: '2001', trechos: 1 })
  assert.match(nao, /A rua não cruza a mancha de 2001\./)
  assert.match(nao, /não quer dizer rua segura/)
  assert.deepEqual(intersecoes(tabela, 'Av.Carlos Drumond de Andrade').dentro.map((d) => d.evento), ['2008-11'])
})

test('Gaspar e Brusque: os pontos COM coordenada; Blumenau: a rua tem cota, o mapa não marca', () => {
  const g = pontosDaRua(cotas, 'gaspar', 'rua adriano kormann')
  assert.equal(g.length, 1)
  assert.ok(g[0]!.pontos.length >= 5 && g[0]!.pontos.every((c) => typeof c.lat === 'number'))
  const t = textoDosPontos(g[0]!.rua, 'Gaspar', g[0]!.pontos)
  assert.match(t, /Localização aproximada: é o ponto da lista da Defesa Civil, não o traçado da rua/)
  assert.match(t, /cota de 8,25 m na régua de Gaspar/)
  assert.match(t, /Não é previsão/)
  assert.equal(pontosDaRua(cotas, 'blumenau', 'rua sao rafael').length, 0)
  assert.ok(ruasSemCoordenada(cotas, 'blumenau', 'rua sao rafael').includes('Rua São Rafael'))
})

// ---------------------------------------------------------------- executar

function monitorFalso(cidade: string | null) {
  const marcas: (MarcaNoMapa | null)[] = []
  let marca: MarcaNoMapa | null = null
  const c: ControleMonitor = {
    cidade,
    pronto: true,
    estado: () => ({ cidade, cidadeNome: cidade, regua: null, reguas: [], fundo: 'escuro' as Fundo, camada: null, camadasDisponiveis: [], reproducao: null, marca: marca?.rotulo ?? null }),
    escolherRegua: () => ({ ok: true, texto: '' }),
    enquadrarCidade: () => ({ ok: true, texto: '' }),
    zoom: () => ({ ok: true, texto: '' }),
    verBacia: () => ({ ok: true, texto: '' }),
    fundo: () => ({ ok: true, texto: '' }),
    camada: () => ({ ok: true, texto: '' }),
    aoVivo: () => ({ ok: true, texto: '' }),
    marcarPonto: (p) => { marcas.push(p); marca = p; return { ok: true, texto: 'marcado' } },
    explicar: () => null,
    retrato: (): Retrato => ({ rota: `/monitor/${cidade}`, cidade, marca }),
    restaurar: (r) => { marca = r.marca ?? null; marcas.push(marca); return { ok: true, texto: 'ok' } },
  }
  return { c, marcas }
}

const dados: DadosDoChat = {
  aoVivo: async () => null,
  cidade: () => null,
  reguasNoMapa: () => [],
  tracado: async () => null,
  base: () => 'https://site.example/',
  viasItajai: async () => contagem,
  ruasMancha: async () => tabela,
  cotasRuas: async () => cotas,
}

function ambiente(rota = '/', inicial: ReturnType<typeof monitorFalso> | null = null) {
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
      if (m) {
        const cid = m[1] ?? null
        if (!montados.has(cid)) montados.set(cid, monitorFalso(cid))
        atual = montados.get(cid)!
      } else atual = null
    },
    rotaAtual: () => r,
    monitor: () => atual?.c ?? null,
    esperarMonitor: async (cid) => (atual && atual.c.cidade === cid ? atual.c : null),
    dados,
  }
  return { amb, navegacoes, montados }
}
const ajuda = () => textoDeAjuda(fora, null)
const rodar = (texto: string, amb: Ambiente, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', texto)
  return executar(r.passos, amb, cat, ctx, ajuda)
}

beforeEach(() => limparRetratos())

test('rua de Itajaí: abre o mapa das manchas com a rua no endereço; com ano, o cenário junto', async () => {
  const { amb, navegacoes } = ambiente()
  const s = await rodar('mostrar a Avenida 7 de Setembro em Itajaí', amb)
  assert.equal(navegacoes.at(-1), '/itajai?secao=manchas&rua=Av.7+de+Setembro')
  assert.match(s.texto, /Avenida 7 de Setembro destacada/)
  await rodar('mancha de 2008 na Avenida 7 de Setembro em Itajaí', amb)
  assert.equal(navegacoes.at(-1), '/itajai?secao=manchas&rua=Av.7+de+Setembro&cenario=2008-11')
  const semAno = await rodar('mancha de 1950 na Avenida 7 de Setembro em Itajaí', amb)
  assert.match(semAno.texto, /não tem mancha de cheia de Itajaí de 1950[^]*Nada foi marcado/)
})

test('homônimos e "manchas na rua" com vários cenários: pergunta antes de marcar ou de ligar', async () => {
  const { amb, navegacoes } = ambiente()
  const semTipo = await executar([{ tipo: 'rua', foco: 'mostrar', texto: 'carlos drumond de andrade', cidadeId: 'itajai' }], amb, cat, fora, ajuda)
  assert.match(semTipo.texto, /Mais de uma via casa/)
  assert.deepEqual(semTipo.sugestoes, ['mostrar a Avenida Carlos Drumond de Andrade em Itajaí', 'mostrar a Rua Carlos Drumond de Andrade em Itajaí'])
  assert.equal(navegacoes.length, 0, 'nada foi marcado antes da escolha')
  const m = await rodar('manchas na Avenida 7 de Setembro em Itajaí', amb)
  assert.match(m.texto, /Qual cenário mostrar no mapa\?/)
  assert.deepEqual(m.sugestoes, ['mancha de 1983 na Avenida 7 de Setembro em Itajaí', 'mancha de 1984 na Avenida 7 de Setembro em Itajaí', 'mancha de 2008 na Avenida 7 de Setembro em Itajaí'])
  assert.ok(!navegacoes.at(-1)!.includes('cenario='), 'sem escolha, o cenário não é trocado')
})

test('rua em Gaspar: abre o Monitor e marca TODOS os pontos de cota da rua, sem linha entre eles', async () => {
  const { amb, navegacoes, montados } = ambiente()
  const s = await rodar('mostrar a rua Adriano Kormann em Gaspar', amb)
  assert.deepEqual(navegacoes, ['/monitor/gaspar'])
  const marca = montados.get('gaspar')!.marcas.at(-1)!
  assert.equal(1 + (marca.extras?.length ?? 0), cotas.filter((c) => c.cidade === 'gaspar' && c.rua === 'Rua Adriano Kormann' && c.lat != null).length)
  assert.match(marca.rotulo, /localização aproximada/)
  assert.ok((marca.km ?? 0) >= 1.2)
  assert.match(s.texto, /Localização aproximada/)
})

test('sem cidade: procura onde há rua no mapa; Blumenau não marca nada', async () => {
  const { amb, navegacoes } = ambiente()
  const s = await rodar('mostrar a rua Adriano Kormann', amb)
  assert.deepEqual(navegacoes, ['/monitor/gaspar'])
  assert.match(s.texto, /Gaspar/)
  const blu = ambiente()
  const b = await rodar('mostrar a rua São Rafael em Blumenau', blu.amb)
  assert.deepEqual(blu.navegacoes, [])
  // A lista de Blumenau tem a rua com e sem acento: as duas aparecem, nenhuma é marcada.
  assert.match(b.texto, /^Blumenau tem cota levantada para [^:]*Rua São Rafael[^:]*, mas a fonte não publica a coordenada/)
  assert.match(b.sugestoes?.[0] ?? '', /^quantas cheias passaram da cota da Rua S[aã]o Rafael em Blumenau\?$/)
})

test('remover destaque: tira a rua do endereço do mapa das manchas, ou a marca do Monitor', async () => {
  const pag = ambiente('/itajai?secao=manchas&rua=Av.7+de+Setembro&cenario=2008-11')
  await rodar('remover destaque', pag.amb)
  assert.equal(pag.navegacoes.at(-1), '/itajai?secao=manchas&cenario=2008-11')
  const m = monitorFalso('gaspar')
  const mon = ambiente('/monitor/gaspar', m)
  const ctx = { cidadeAtual: 'gaspar', naMonitor: true, reguaAtual: null }
  await rodar('mostrar a rua Adriano Kormann', mon.amb, ctx)
  await rodar('tirar a marca', mon.amb, ctx)
  assert.equal(m.marcas.at(-1), null)
  const nada = await rodar('remover destaque', ambiente('/acu').amb)
  assert.match(nada.texto, /Não há rua destacada/)
})

test('voltar depois de destacar uma rua volta ao endereço de antes', async () => {
  const { amb, navegacoes } = ambiente('/itajai?secao=manchas')
  await rodar('mostrar a Avenida 7 de Setembro em Itajaí', amb)
  await rodar('voltar', amb)
  assert.equal(navegacoes.at(-1), '/itajai?secao=manchas')
})
