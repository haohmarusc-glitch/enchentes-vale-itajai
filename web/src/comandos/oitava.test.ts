/**
 * 8ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): o site e os seus dados — atualizar as
 * leituras, "isso é oficial?", instalar o aplicativo, o que o site guarda, apagar preferências, contagem do
 * chat, limpar a conversa e os números de emergência.
 */
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { executar, limparRetratos, type Ambiente, type DadosDoChat } from './executar'
import { textoDeAjuda } from './ajuda'
import { TEXTO_EMERGENCIA, TEXTO_OFICIAL, textoAtualizacao, textoInstalar, textoPrivacidade } from './site'
import { MIN_ENTRE_PEDIDOS_MS, pedirAtualizacao, zerarPedidos } from '../dados/atualizar'
import { CHAVE_AVISO, CHAVE_CIDADES, CHAVE_CONTAGEM_CHAT, CHAVE_LETRA, esquecerPreferencias, temMemoria, type Armazem } from '../logica/preferencias'
import type { Contexto } from './tipos'

const ler = (c: string) => JSON.parse(readFileSync(new URL(`../../../data/${c}`, import.meta.url), 'utf8'))
const cat = catalogoDoCadastro(ler('estacoes.json'))
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const AGORA = new Date('2026-10-06T18:00:00Z') // 15h00 em Brasília
const minAtras = (m: number) => new Date(AGORA.getTime() - m * 60_000)

const passos = (texto: string, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', `"${texto}" devia virar comando, veio ${JSON.stringify(r)}`)
  return r.passos
}

class Memoria implements Armazem {
  m = new Map<string, string>()
  getItem(c: string) {
    return this.m.get(c) ?? null
  }
  setItem(c: string, v: string) {
    this.m.set(c, v)
  }
  removeItem(c: string) {
    this.m.delete(c)
  }
}
const quebrado: Armazem = {
  getItem: () => {
    throw new Error('bloqueado')
  },
  setItem: () => {
    throw new Error('bloqueado')
  },
  removeItem: () => {
    throw new Error('bloqueado')
  },
}

// ---------------------------------------------------------------- interpretar

test('frases da 8ª entrega; pedido de conselho continua fora dos comandos', () => {
  assert.deepEqual(passos('atualizar as leituras'), [{ tipo: 'atualizar' }])
  assert.deepEqual(passos('tem leitura nova?'), [{ tipo: 'atualizar' }])
  assert.deepEqual(passos('isso é oficial?'), [{ tipo: 'oficial' }])
  assert.deepEqual(passos('ler o aviso'), [{ tipo: 'oficial' }])
  assert.deepEqual(passos('como instalar o aplicativo?'), [{ tipo: 'instalar' }])
  assert.deepEqual(passos('tem app?'), [{ tipo: 'instalar' }])
  assert.deepEqual(passos('o que o site guarda de mim?'), [{ tipo: 'privacidade' }])
  assert.deepEqual(passos('apagar minhas preferências'), [{ tipo: 'esquecer', confirmado: false }])
  assert.deepEqual(passos('sim, apagar minhas preferências'), [{ tipo: 'esquecer', confirmado: true }])
  assert.deepEqual(passos('não contar minhas perguntas'), [{ tipo: 'contagem', permitir: false }])
  assert.deepEqual(passos('pode contar minhas perguntas'), [{ tipo: 'contagem', permitir: true }])
  assert.deepEqual(passos('limpar a conversa'), [{ tipo: 'limpar_conversa' }])
  assert.deepEqual(passos('qual o telefone da Defesa Civil?'), [{ tipo: 'emergencia' }])
  assert.deepEqual(passos('para quem devo ligar?'), [{ tipo: 'emergencia' }])
  // "Limpar filtros" e "limpar o histórico" não são a conversa.
  assert.deepEqual(passos('limpar filtros'), [{ tipo: 'filtro', filtro: null }])
  for (const q of ['devo sair de casa?', 'apagar o histórico de Blumenau', 'o site vai avisar quando encher?']) assert.equal(interpretar(q, cat, fora), null, q)
})

// ---------------------------------------------------------------- atualizar

test('atualizar: um pedido por 30 s; o texto diz se a coleta é nova e nunca promete leitura nova', () => {
  zerarPedidos()
  assert.equal(pedirAtualizacao(1_000_000), true)
  assert.equal(pedirAtualizacao(1_000_000 + MIN_ENTRE_PEDIDOS_MS - 1), false)
  assert.equal(pedirAtualizacao(1_000_000 + MIN_ENTRE_PEDIDOS_MS), true)
  zerarPedidos()
  const mesma = textoAtualizacao({ pedido: true, coletaAntes: minAtras(12), coletaDepois: minAtras(12), medicaoMaisNova: minAtras(20), agora: AGORA })
  assert.match(mesma, /a coleta mais recente ainda é a de 14:48 de 06\/10 \(há 12 min\)\. As fontes não publicaram leitura nova/)
  assert.match(mesma, /A medição mais nova entre todas as réguas é de 14:40 de 06\/10 \(há 20 min\)[^]*leitura velha continua marcada como velha/)
  assert.match(textoAtualizacao({ pedido: true, coletaAntes: minAtras(12), coletaDepois: minAtras(2), medicaoMaisNova: null, agora: AGORA }), /chegou a coleta de 14:58/)
  assert.match(textoAtualizacao({ pedido: true, coletaAntes: null, coletaDepois: null, medicaoMaisNova: null, agora: AGORA }), /não respondeu/)
  assert.match(textoAtualizacao({ pedido: false, coletaAntes: null, coletaDepois: null, medicaoMaisNova: null, agora: AGORA }), /menos de 30 segundos[^]*a cada 5 minutos/)
})

// ---------------------------------------------------------------- textos

test('oficial e emergência: o aviso de toda tela e só os números da faixa (199 e 193)', () => {
  assert.match(TEXTO_OFICIAL, /^Não\. Este site não é sistema oficial de alerta[^]*AlertaBlu[^]*8 m em Blumenau e 8 m em Brusque[^]*199/)
  assert.match(TEXTO_EMERGENCIA, /199 \(Defesa Civil\) ou 193 \(Bombeiros\)/)
  assert.doesNotMatch(TEXTO_EMERGENCIA, /\b19[0-2]\b/, 'nenhum número além dos da faixa')
})

test('instalar: iPhone, botão do Início ou menu do navegador; já instalado; nunca instala sozinho', () => {
  assert.match(textoInstalar({ instalado: true, iphone: false, pode: false }), /já está aberto como aplicativo/)
  assert.match(textoInstalar({ instalado: false, iphone: true, pode: false }), /Compartilhar[^]*Adicionar à Tela de Início/)
  assert.match(textoInstalar({ instalado: false, iphone: false, pode: true }), /botão "Instalar" no Início[^]*o chat não instala sozinho/)
  assert.match(textoInstalar({ instalado: false, iphone: false, pode: false }), /três pontos[^]*hora da medição[^]*e-mail cadastrado/)
})

test('privacidade: o que está guardado, lido na hora, e o que nunca é guardado', () => {
  const t = textoPrivacidade({ memoria: true, seguidas: ['Gaspar', 'Blumenau'], letraGrande: true, avisoLido: true, contagem: false })
  assert.match(t, /• cidades: Gaspar \(a sua\), e segue Blumenau;\n• letra: maior;\n• aviso legal: lido;\n• contagem [^]*desligada/)
  assert.match(t, /Não guarda: a sua localização[^]*esta conversa/)
  assert.match(textoPrivacidade({ memoria: false, seguidas: [], letraGrande: false, avisoLido: false, contagem: false }), /não deixa o site guardar nada/)
})

test('apagar preferências: tira as quatro chaves; armazenamento bloqueado não derruba nada', () => {
  const a = new Memoria()
  for (const c of [CHAVE_CIDADES, CHAVE_LETRA, CHAVE_AVISO, CHAVE_CONTAGEM_CHAT, 'outra-coisa']) a.setItem(c, 'x')
  assert.equal(esquecerPreferencias(a), true)
  assert.deepEqual([...a.m.keys()], ['outra-coisa'])
  assert.equal(esquecerPreferencias(quebrado), false)
  assert.equal(esquecerPreferencias(null), false)
  assert.equal(temMemoria(new Memoria()), true)
  assert.equal(temMemoria(quebrado), false)
})

// ---------------------------------------------------------------- executar

function ambiente() {
  const chamadas: string[] = []
  const navegacoes: string[] = []
  const dados: DadosDoChat = {
    aoVivo: async () => null,
    cidade: () => null,
    reguasNoMapa: () => [],
    tracado: async () => null,
    base: () => '',
    atualizar: async () => {
      chamadas.push('atualizar')
      return { pedido: true, coletaAntes: minAtras(12), coletaDepois: minAtras(2), medicaoMaisNova: minAtras(5), agora: AGORA }
    },
    aplicativo: () => ({ instalado: false, iphone: false, pode: true }),
    privacidade: () => ({ memoria: true, seguidas: ['rio-do-sul'], letraGrande: false, avisoLido: false, contagem: true }),
    esquecer: () => {
      chamadas.push('esquecer')
      return true
    },
    contagem: (p) => {
      chamadas.push(`contagem:${p}`)
      return true
    },
    limparConversa: () => {
      chamadas.push('limpar')
    },
  }
  const amb: Ambiente = {
    navegar: (para) => navegacoes.push(para),
    rotaAtual: () => '/acu/blumenau',
    monitor: () => null,
    esperarMonitor: async () => null,
    dados,
  }
  return { amb, chamadas, navegacoes }
}
const ajuda = () => textoDeAjuda(fora, null)
const rodar = (texto: string, amb: Ambiente) => {
  const r = interpretar(texto, cat, fora)
  assert.ok(r && r.tipo === 'comandos', texto)
  return executar(r.passos, amb, cat, fora, ajuda)
}

beforeEach(() => limparRetratos())

test('executor: apagar só depois de confirmar; contagem, conversa e atualizar pelas funções do aparelho', async () => {
  const { amb, chamadas, navegacoes } = ambiente()
  const pergunta = await rodar('apagar minhas preferências', amb)
  assert.match(pergunta.texto, /Para confirmar, peça "sim, apagar minhas preferências"/)
  assert.deepEqual(pergunta.sugestoes?.[0], 'sim, apagar minhas preferências')
  assert.deepEqual(chamadas, [], 'nada é apagado sem confirmar')
  assert.match((await rodar('sim, apagar minhas preferências', amb)).texto, /Preferências apagadas/)
  assert.match((await rodar('não contar minhas perguntas', amb)).texto, /Contagem desligada/)
  assert.match((await rodar('limpar a conversa', amb)).texto, /Conversa limpa/)
  assert.match((await rodar('atualizar as leituras', amb)).texto, /chegou a coleta de 14:58/)
  assert.deepEqual(chamadas, ['esquecer', 'contagem:false', 'limpar', 'atualizar'])
  assert.match((await rodar('o que o site guarda de mim?', amb)).texto, /cidades: Rio do Sul \(a sua\)/)
  const inst = await rodar('como instalar o aplicativo?', amb)
  assert.equal(inst.link?.para, '/')
  assert.deepEqual(navegacoes, [], 'nada navega sozinho')
})

test('a ajuda lista os pedidos da 8ª entrega', () => {
  const t = textoDeAjuda({ cidadeAtual: null, naMonitor: true, reguaAtual: null }, null).texto
  for (const f of ['atualizar as leituras', 'isso é oficial?', 'como instalar o aplicativo?', 'o que o site guarda de mim?', 'apagar minhas preferências', 'limpar a conversa']) assert.ok(t.includes(f), f)
})
