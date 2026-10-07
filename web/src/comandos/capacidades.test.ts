/**
 * 17ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md; PR 1 do handoff de qualidade): o catálogo único de
 * capacidades é fiel ao leitor e ao executor de hoje.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { MUDA_A_TELA, PRECISA_DO_MAPA } from './executar'
import { CAPACIDADES, EXEMPLOS_DE_ESCLARECIMENTO, GRUPOS, TIPOS, esquemaDoClassificador, textoDoCatalogo } from './capacidades'
import type { Contexto } from './tipos'

const cat = catalogoDoCadastro(JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8')))
const ctxDe = (c?: Partial<Contexto>): Contexto => ({ cidadeAtual: null, naMonitor: false, reguaAtual: null, ...(c ?? {}) })

test('todo exemplo do catálogo vira exatamente o passo da ficha, no contexto declarado', () => {
  let n = 0
  for (const tipo of TIPOS) {
    const c = CAPACIDADES[tipo]
    assert.ok(c.exemplos.length >= 1, `${tipo} sem exemplo`)
    for (const e of c.exemplos) {
      const r = interpretar(e.texto, cat, ctxDe(e.contexto))
      assert.ok(r && r.tipo === 'comandos' && r.passos.length === 1 && r.passos[0]!.tipo === tipo, `"${e.texto}" devia virar ${tipo}, veio ${JSON.stringify(r)}`)
      n++
    }
  }
  assert.ok(n >= 150, `poucos exemplos: ${n}`)
  for (const e of EXEMPLOS_DE_ESCLARECIMENTO) {
    const r = interpretar(e.texto, cat, ctxDe(e.contexto))
    assert.ok(r && r.tipo === 'esclarecer', `"${e.texto}" devia pedir esclarecimento, veio ${JSON.stringify(r)}`)
  }
})

test('mudaTela e precisaDoMapa batem com os conjuntos do executor; grupos e entregas válidos', () => {
  for (const tipo of TIPOS) {
    const c = CAPACIDADES[tipo]
    assert.equal(c.mudaTela, MUDA_A_TELA.has(tipo), `${tipo}: mudaTela`)
    assert.equal(c.precisaDoMapa, PRECISA_DO_MAPA.has(tipo), `${tipo}: precisaDoMapa`)
    assert.ok(c.grupo in GRUPOS, `${tipo}: grupo ${c.grupo}`)
    assert.ok(c.entrega >= 1 && c.entrega <= 16, `${tipo}: entrega ${c.entrega}`)
    assert.ok(c.titulo && c.descricao, `${tipo}: sem título ou descrição`)
    for (const a of c.argumentos) if (a.tipo === 'enum') assert.ok(a.valores && a.valores.length >= 2, `${tipo}.${a.nome}: enum sem valores`)
  }
  // Os dois conjuntos do executor não têm tipo fora do catálogo (o Record já cobra o inverso em compilação).
  for (const t of [...MUDA_A_TELA, ...PRECISA_DO_MAPA]) assert.ok(t in CAPACIDADES, `${t} fora do catálogo`)
})

test('esquema do classificador: só identificadores do catálogo mais "nao_sei"; texto do catálogo cobre todo passo', () => {
  const e = esquemaDoClassificador()
  assert.deepEqual(e.intencoes, [...TIPOS, 'nao_sei'])
  assert.deepEqual(Object.keys(e.argumentos).sort(), [...TIPOS].sort())
  const md = textoDoCatalogo()
  for (const t of TIPOS) assert.ok(md.includes(`\`${t}\``), `${t} fora do texto`)
  assert.match(md, /não editar à mão/)
  assert.doesNotMatch(md, /claude-|haiku|sonnet|opus/i, 'nenhum identificador de modelo no catálogo')
})
