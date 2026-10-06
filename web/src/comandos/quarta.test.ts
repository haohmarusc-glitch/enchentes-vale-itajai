/**
 * 4ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): localização, relato, cidades guardadas no
 * aparelho, letra e tela cheia.
 */
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { executar, limparRetratos, type Ambiente, type DadosDoChat } from './executar'
import { textoDeAjuda } from './ajuda'
import { AVISO_DISTANCIA, AVISO_PRIVACIDADE, reguasPerto, textoDaLocalizacao, textoDoRelato } from './aparelho'
import { cidadesSeguidas, seguir, MAX_CIDADES, type Armazem, type CidadeSeguida } from '../logica/preferencias'
import type { AoVivo } from '../dados/usarAoVivo'
import type { NivelSc } from '../dados/nivelSc'
import type { Cidade } from '../dados/tipos'
import type { ControleMonitor, MarcaNoMapa, Retrato } from './ponte'
import type { Contexto, Fundo } from './tipos'

const estacoes = JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'))
const cat = catalogoDoCadastro(estacoes)
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const AGORA = new Date('2026-10-06T18:00:00Z')

const passos = (texto: string, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', `"${texto}" devia virar comando, veio ${JSON.stringify(r)}`)
  return r.passos
}

function armazem(): Armazem & { dados: Map<string, string> } {
  const dados = new Map<string, string>()
  return { dados, getItem: (k) => dados.get(k) ?? null, setItem: (k, v) => void dados.set(k, v), removeItem: (k) => void dados.delete(k) }
}

// ---------------------------------------------------------------- preferências e textos

test('seguir: no fim da lista, sem duplicar, sem passar do máximo e sem fingir que guardou', () => {
  const a = armazem()
  assert.equal(seguir({ id: 'gaspar', rio: 'acu' }, a), 'seguindo')
  assert.equal(seguir({ id: 'gaspar', rio: 'acu' }, a), 'ja_seguia')
  for (const id of ['blumenau', 'ilhota', 'brusque']) seguir({ id, rio: 'acu' }, a)
  assert.equal(cidadesSeguidas(a).length, MAX_CIDADES)
  assert.equal(seguir({ id: 'taio', rio: 'acu' }, a), 'cheia')
  assert.equal(cidadesSeguidas(a)[0]!.id, 'gaspar', 'a primeira continua sendo a minha')
  const quebrado: Armazem = { getItem: () => null, setItem: () => { throw new Error('cheio') }, removeItem: () => {} }
  assert.equal(seguir({ id: 'gaspar', rio: 'acu' }, quebrado), 'sem_memoria')
})

test('localização: a régua mais perto em linha reta, com os avisos; Itajaí pelas réguas dela', () => {
  const perto = textoDaLocalizacao({ lat: -26.93, lon: -48.97, precisaoM: 30 }, cat)
  assert.equal(perto.perto?.cidadeId, 'gaspar')
  assert.match(perto.texto, /^A régua mais perto de você, em linha reta, é a de Gaspar \(0,7 km\)\./)
  assert.ok(perto.texto.includes(AVISO_DISTANCIA) && perto.texto.includes(AVISO_PRIVACIDADE))
  assert.ok(!/-26|−26|48,97/.test(perto.texto), 'a posição da pessoa não aparece no texto')
  const foz = reguasPerto({ lat: -26.9334, lon: -48.7478, precisaoM: null }, cat)
  assert.match(foz[0]!.rotulo, /^DC-05 · .+, em Itajaí$/)
  assert.ok(!foz.some((r) => r.rotulo === 'Itajaí'), 'Itajaí não tem "a régua da cidade"')
})

test('localização: fora da área, posição imprecisa e régua de coordenada não confirmada', () => {
  const sp = textoDaLocalizacao({ lat: -23.55, lon: -46.63, precisaoM: 20 }, cat)
  assert.equal(sp.fora, true)
  assert.match(sp.texto, /fora da área das réguas do site/)
  const vaga = textoDaLocalizacao({ lat: -26.93, lon: -48.97, precisaoM: 5000 }, cat)
  assert.match(vaga.texto, /incerteza de cerca de 5 km: a régua mais perto pode ser outra/)
  const timbo = textoDaLocalizacao({ lat: -26.824, lon: -49.271, precisaoM: 20 }, cat)
  assert.match(timbo.texto, /A posição da régua de Timbó no mapa não está confirmada/)
})

test('relato: o texto para copiar, com a hora de Brasília e o espaço para descrever', () => {
  const t = textoDoRelato({ tela: 'Monitor de Itajaí, régua DC-05 · Sítio Sr. Hilário', caminho: '#/monitor/itajai?regua=DC-05', mostra: '1,62 m', agora: AGORA })
  assert.match(t, /^Relato de problema — site Enchentes do Vale do Itajaí\nQuando: 06\/10, 15:00 \(horário de Brasília\)/)
  assert.match(t, /O problema: \[descreva aqui o que está errado\]$/)
  assert.ok(!/https?:|pages\.dev/.test(t))
})

// ---------------------------------------------------------------- interpretar

test('frases da 4ª entrega; perguntas continuam perguntas', () => {
  assert.deepEqual(passos('usar minha localização'), [{ tipo: 'localizacao' }])
  assert.deepEqual(passos('qual a régua mais perto de mim?'), [{ tipo: 'localizacao' }])
  assert.deepEqual(passos('relatar problema nesta régua'), [{ tipo: 'relatar' }])
  assert.deepEqual(passos('essa leitura está errada'), [{ tipo: 'relatar' }])
  assert.deepEqual(passos('minha cidade é Gaspar'), [{ tipo: 'preferencia_cidade', acao: 'minha', cidadeId: 'gaspar' }])
  assert.deepEqual(passos('definir Rio do Sul como minha cidade'), [{ tipo: 'preferencia_cidade', acao: 'minha', cidadeId: 'rio-do-sul' }])
  assert.deepEqual(passos('seguir Blumenau'), [{ tipo: 'preferencia_cidade', acao: 'seguir', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('deixar de seguir Blumenau'), [{ tipo: 'preferencia_cidade', acao: 'deixar', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quais cidades eu sigo?'), [{ tipo: 'preferencia_cidade', acao: 'listar' }])
  assert.deepEqual(passos('aumentar a letra'), [{ tipo: 'letra', tamanho: 'grande' }])
  assert.deepEqual(passos('letra normal'), [{ tipo: 'letra', tamanho: 'normal' }])
  assert.deepEqual(passos('tela cheia'), [{ tipo: 'tela_cheia' }])
  for (const q of ['moro em Gaspar, minha rua alaga?', 'seguir o rio até o mar?', 'onde estou errando?']) {
    assert.equal(interpretar(q, cat, fora), null, q)
  }
  const pomerode = interpretar('minha cidade é Pomerode', cat, fora)
  assert.ok(pomerode?.tipo === 'esclarecer' && /"pomerode" não está entre as cidades do site/.test(pomerode.texto))
})

// ---------------------------------------------------------------- executar

function monitorFalso(cidade: string | null, regua: { codigo: string; rotulo: string } | null = null) {
  const marcas: (MarcaNoMapa | null)[] = []
  const c: ControleMonitor = {
    cidade,
    pronto: true,
    estado: () => ({ cidade, cidadeNome: cidade === 'itajai' ? 'Itajaí' : cidade, regua, reguas: [], fundo: 'escuro' as Fundo, camada: null, camadasDisponiveis: [], reproducao: null }),
    escolherRegua: () => ({ ok: true, texto: '' }),
    enquadrarCidade: () => ({ ok: true, texto: '' }),
    zoom: () => ({ ok: true, texto: '' }),
    verBacia: () => ({ ok: true, texto: '' }),
    fundo: () => ({ ok: true, texto: '' }),
    camada: () => ({ ok: true, texto: '' }),
    aoVivo: () => ({ ok: true, texto: '' }),
    marcarPonto: (p) => { marcas.push(p); return { ok: true, texto: 'marcado' } },
    explicar: () => null,
    retrato: (): Retrato => ({ rota: `/monitor/${cidade}`, cidade }),
    restaurar: () => ({ ok: true, texto: 'ok' }),
  }
  return { c, marcas }
}

function aoVivoCom(estacao: string, nivel: number): AoVivo {
  return {
    tempoReal: { situacao: 'ok', leituras: [{ estacao, rio: 'itajai-mirim', cidade: 'itajai', nivel_m: nivel, medidoEm: new Date(AGORA.getTime() - 13 * 60_000), resgateDe: null }], chuva: [], chuvaOk: true, coletadoEm: AGORA, fonte: null },
    nivelSc: new Map() as NivelSc,
    serie: { situacao: 'ok', series: {}, resgates: {}, janelaHoras: 48, geradoEm: AGORA },
    agora: AGORA,
  }
}

function dados(ops: { pos?: Awaited<ReturnType<NonNullable<DadosDoChat['localizacao']>>>; v?: AoVivo | null } = {}) {
  const lista: CidadeSeguida[] = []
  let letra = 'normal'
  const d: DadosDoChat = {
    aoVivo: async () => ops.v ?? null,
    cidade: (id) => {
      for (const [rioId, r] of Object.entries(estacoes.rios as Record<string, { cidades: Cidade[] }>)) {
        const c = r.cidades.find((x) => x.id === id)
        if (c) return { cidade: c, rioId }
      }
      return null
    },
    reguasNoMapa: () => [],
    tracado: async () => null,
    base: () => 'https://site.example/',
    localizacao: async () => ops.pos ?? { erro: 'negada' },
    preferencias: {
      seguidas: () => [...lista],
      tornarMinha: (c) => {
        const i = lista.findIndex((x) => x.id === c.id)
        if (i >= 0) lista.splice(i, 1)
        lista.unshift(c)
        return [...lista]
      },
      seguir: (c) => (lista.some((x) => x.id === c.id) ? 'ja_seguia' : (lista.push(c), 'seguindo')),
      deixarDeSeguir: (id) => {
        const i = lista.findIndex((x) => x.id === id)
        if (i >= 0) lista.splice(i, 1)
        return [...lista]
      },
      letra: (l) => void (letra = l),
    },
  }
  return { d, lista, letra: () => letra }
}

function ambiente(d: DadosDoChat, rota = '/', inicial: ReturnType<typeof monitorFalso> | null = null) {
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
    dados: d,
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

test('localização: abre o Monitor da cidade mais perto e marca a posição; recusada, nada acontece', async () => {
  const { d } = dados({ pos: { lat: -26.93, lon: -48.97, precisaoM: 40 } })
  const { amb, navegacoes, montados } = ambiente(d)
  const s = await rodar('usar minha localização', amb)
  assert.deepEqual(navegacoes, ['/monitor/gaspar'])
  const marca = montados.get('gaspar')!.marcas.at(-1)!
  assert.match(marca.rotulo, /não fica guardado/)
  assert.match(s.texto, /a de Gaspar/)
  assert.deepEqual(s.sugestoes, ['como está Gaspar?', 'definir Gaspar como minha cidade'])
  const negada = ambiente(dados().d)
  const n = await rodar('usar minha localização', negada.amb)
  assert.deepEqual(negada.navegacoes, [])
  assert.match(n.texto, /Você não permitiu a localização[^]*Nada foi lido nem guardado/)
  const sp = ambiente(dados({ pos: { lat: -23.55, lon: -46.63, precisaoM: 20 } }).d)
  const f = await rodar('usar minha localização', sp.amb)
  assert.deepEqual(sp.navegacoes, [], 'fora da área, o mapa não muda')
  assert.match(f.texto, /fora da área/)
})

test('relato no Monitor: a tela, a régua e a leitura de agora, prontos para copiar', async () => {
  const titulo = cat.reguas.find((r) => r.codigo === 'DC-05')!.titulo
  const m = monitorFalso('itajai', { codigo: 'DC-05', rotulo: 'DC-05 · Sítio Sr. Hilário' })
  const { amb } = ambiente(dados({ v: aoVivoCom(titulo, 1.62) }).d, '/monitor/itajai?regua=DC-05', m)
  const s = await rodar('relatar problema nesta régua', amb, { cidadeAtual: 'itajai', naMonitor: true, reguaAtual: 'DC-05' })
  assert.ok(s.copiar)
  assert.match(s.copiar!, /Tela: Monitor de Itajaí, régua DC-05 · Sítio Sr\. Hilário \(#\/monitor\/itajai\?regua=DC-05\)/)
  assert.match(s.copiar!, /O site mostra: 1,62 m, medido às 14:47 \(há 13 min\) na DC-05/)
  assert.match(s.texto, /não tem um canal de relato[^]*ligue 199/)
})

test('cidades no aparelho: minha, seguir, listar, deixar de seguir', async () => {
  const { d, lista } = dados()
  const { amb } = ambiente(d)
  assert.match((await rodar('minha cidade é Gaspar', amb)).texto, /Gaspar agora é a sua cidade neste aparelho/)
  assert.match((await rodar('seguir Blumenau', amb)).texto, /Agora você segue Blumenau/)
  assert.match((await rodar('seguir Blumenau', amb)).texto, /Você já segue Blumenau/)
  assert.equal((await rodar('quais cidades eu sigo?', amb)).texto, 'Sua cidade neste aparelho: Gaspar. Também segue: Blumenau. Fica só neste aparelho.')
  assert.match((await rodar('deixar de seguir Blumenau', amb)).texto, /deixou de seguir Blumenau/)
  assert.deepEqual(lista.map((c) => c.id), ['gaspar'])
})

test('letra: grava a escolha; no Monitor avisa que o mapa não muda. Tela cheia aponta o botão', async () => {
  const x = dados()
  const { amb } = ambiente(x.d)
  assert.match((await rodar('aumentar a letra', amb)).texto, /Letra maior ligada neste aparelho\. É o mesmo botão/)
  assert.equal(x.letra(), 'grande')
  const mon = await rodar('letra normal', amb, { cidadeAtual: null, naMonitor: true, reguaAtual: null })
  assert.match(mon.texto, /O Monitor mantém o desenho dele/)
  const cheia = await rodar('tela cheia', amb, { cidadeAtual: 'gaspar', naMonitor: false, reguaAtual: null })
  assert.equal(cheia.link?.para, '/monitor/gaspar')
  assert.match((await rodar('tela cheia', amb, { cidadeAtual: null, naMonitor: true, reguaAtual: null })).texto, /use o botão "Tela cheia"/)
})
