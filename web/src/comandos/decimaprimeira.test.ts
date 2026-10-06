/**
 * 11ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): as palavras do rio (glossário) e a
 * resposta em voz alta.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { executar, type Ambiente } from './executar'
import { textoDeAjuda } from './ajuda'
import { TERMOS, textoDoVerbete, verbeteDe } from './glossario'
import { textoParaFala } from './fala'
import type { Contexto } from './tipos'

const ler = (c: string) => JSON.parse(readFileSync(new URL(`../../../data/${c}`, import.meta.url), 'utf8'))
const cat = catalogoDoCadastro(ler('estacoes.json'))
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const passos = (texto: string) => {
  const r = interpretar(texto, cat, fora)
  assert.ok(r && r.tipo === 'comandos', `"${texto}" devia virar comando, veio ${JSON.stringify(r)}`)
  return r.passos
}

test('frases: "o que é…", "qual a diferença entre…", lista, voz; as cores continuam com a legenda', () => {
  assert.deepEqual(passos('o que é cota?'), [{ tipo: 'glossario', termos: ['cota'] }])
  assert.deepEqual(passos('o que significa jusante?'), [{ tipo: 'glossario', termos: ['jusante'] }])
  assert.deepEqual(passos('o que é o zero da régua?'), [{ tipo: 'glossario', termos: ['o zero da regua'] }])
  assert.deepEqual(passos('o que quer dizer sizígia?'), [{ tipo: 'glossario', termos: ['sizigia'] }])
  assert.deepEqual(passos('qual a diferença entre enchente e alagamento?'), [{ tipo: 'glossario', termos: ['enchente', 'alagamento'] }])
  assert.deepEqual(passos('que palavras você explica?'), [{ tipo: 'termos' }])
  assert.deepEqual(passos('ler em voz alta'), [{ tipo: 'voz', acao: 'ler' }])
  assert.deepEqual(passos('parar de ler'), [{ tipo: 'voz', acao: 'parar' }])
  // A faixa e a cor continuam sendo da legenda (7ª entrega).
  assert.deepEqual(passos('o que é alerta?'), [{ tipo: 'legenda', tema: 'alerta' }])
  // Palavra que o glossário não tem segue para o motor.
  for (const q of ['o que é o atlas?', 'o que é bom para enchente?']) assert.equal(interpretar(q, cat, fora), null, q)
})

test('verbetes: régua de cada cidade, faixa não é metro, intervalo, alagamento sem o rio subir', () => {
  assert.match(verbeteDe('régua')!.texto, /8 m em Blumenau e 8 m em Brusque não são a mesma água/)
  assert.match(verbeteDe('faixa')!.texto, /nunca o metro/)
  assert.match(verbeteDe('tempo de descida')!.texto, /sempre um intervalo[^]*nunca uma hora exata/)
  assert.match(verbeteDe('alagamento')!.texto, /pode acontecer sem o rio subir/)
  assert.match(verbeteDe('cota de rua')!.texto, /não diz que a rua inteira alaga/)
  assert.equal(verbeteDe('montante'), verbeteDe('jusante'), 'os dois na mesma explicação')
  assert.equal(verbeteDe('palavra que não existe'), null)
  // Diferença entre dois sinônimos do mesmo verbete: um verbete só.
  const t = textoDoVerbete([verbeteDe('enchente')!, verbeteDe('alagamento')!])
  assert.equal(t.match(/Cheia, enchente, inundação e alagamento:/g)?.length, 1)
  assert.match(t, /199/)
  assert.ok(TERMOS.length >= 15)
})

test('fala: unidades por extenso, marcadores fora', () => {
  assert.equal(textoParaFala('• Rio do Sul: 4,80 m, ▲ subindo 12 cm/h · leva 7–10 h até Blumenau.'), 'Rio do Sul: 4,80 metros, subindo 12 centímetros por hora · leva 7 a 10 horas até Blumenau.')
  assert.equal(textoParaFala('1 h: 12,6 mm'), '1 horas: 12,6 milímetros')
})

function ambiente(voz: 'lendo' | 'parado' | 'nada' | 'sem_suporte' | null) {
  const pedidos: string[] = []
  const amb: Ambiente = {
    navegar: () => {},
    rotaAtual: () => '/',
    monitor: () => null,
    esperarMonitor: async () => null,
    dados: {
      aoVivo: async () => null,
      cidade: () => null,
      reguasNoMapa: () => [],
      tracado: async () => null,
      base: () => '',
      ...(voz ? { voz: (a: 'ler' | 'parar') => (pedidos.push(a), voz) } : {}),
    },
  }
  return { amb, pedidos }
}
const rodar = (texto: string, amb: Ambiente) => {
  const r = interpretar(texto, cat, fora)
  assert.ok(r && r.tipo === 'comandos', texto)
  return executar(r.passos, amb, cat, fora, () => textoDeAjuda(fora, null))
}

test('executor: o verbete com sugestões; a voz pelo aparelho, ou o aviso de que não há', async () => {
  const { amb, pedidos } = ambiente('lendo')
  const c = await rodar('o que é cota?', amb)
  assert.match(c.texto, /^Cota: Cota é uma marca de altura na régua da cidade/)
  assert.ok(c.sugestoes?.includes('quanto falta para a cota em Blumenau?'))
  assert.match((await rodar('ler em voz alta', amb)).texto, /Lendo a última resposta em voz alta/)
  assert.deepEqual(pedidos, ['ler'])
  assert.match((await rodar('ler em voz alta', ambiente(null).amb)).texto, /não tem leitura em voz alta/)
  assert.match((await rodar('parar de ler', ambiente('nada').amb)).texto, /Não estou lendo nada agora/)
})
