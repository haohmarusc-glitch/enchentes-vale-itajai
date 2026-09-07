/**
 * O que a página promete ANTES de o JavaScript rodar.
 *
 * Três coisas deste projeto não podem depender do bundle carregar:
 * o telefone da Defesa Civil, o aviso de que o site não é alerta oficial, e
 * um caminho para a fonte oficial quando nada aqui funcionar. Elas ficam em
 * HTML estático no `index.html`, e estes testes travam isso — é fácil alguém
 * "limpar" o #root vazio num refactor e não notar que apagou o 199.
 */
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const HTML = readFileSync(new URL('../../index.html', import.meta.url), 'utf8')

test('o 199 está no HTML estático, antes de qualquer script', () => {
  const antesDoScript = HTML.split('<script')[0] ?? ''
  assert.match(antesDoScript, /199/)
  assert.match(antesDoScript, /Defesa Civil/i)
})

test('o aviso de que NÃO é alerta oficial vem junto — número sem ressalva engana', () => {
  const antesDoScript = HTML.split('<script')[0] ?? ''
  assert.match(antesDoScript, /não é<\/strong> sistema oficial de alerta/i)
})

test('sem JavaScript, a pessoa recebe um caminho para a fonte oficial', () => {
  assert.match(HTML, /<noscript>/)
  const noscript = HTML.slice(HTML.indexOf('<noscript>'), HTML.indexOf('</noscript>'))
  assert.match(noscript, /alertablu|defesacivil/i)
})

test('a casca fica DENTRO do #root, para o React apagá-la ao montar', () => {
  // Fora do #root ela duplicaria a FaixaEmergencia depois que o site carregasse.
  const root = HTML.slice(HTML.indexOf('<div id="root">'))
  assert.match(root.slice(0, root.indexOf('</script>')), /antes-de-carregar/)
})

test('o cartão de compartilhamento também diz que não é alerta oficial', () => {
  // O card do WhatsApp é lido por muito mais gente do que a página.
  const og = HTML.match(/property="og:description"[\s\S]{0,400}?\/>/)?.[0] ?? ''
  assert.match(og, /NÃO oficial|não substitui/i)
  assert.match(og, /199/)
})

test('viewport-fit=cover, senão o mapa em paisagem no iPhone perde as bordas', () => {
  assert.match(HTML, /viewport-fit=cover/)
})

test('preconnect aponta para o host de tile que o site REALMENTE usa', () => {
  // Varre o src inteiro em vez de um arquivo fixo: preconnect para um host que
  // ninguém mais pede é uma conexão aberta à toa, e o contrário — host novo sem
  // preconnect — é o custo que este teste existe para evitar. Se o mapa mudar de
  // provedor, este teste cai junto e lembra de atualizar o index.html.
  const fontes = ['./tiles.ts', '../componentes/MapaManchas.tsx']
    .map((f) => readFileSync(new URL(f, import.meta.url), 'utf8'))
    .join('\n')
  const hosts = new Set(
    [...fontes.matchAll(/https:\/\/([a-z0-9.-]*tile[a-z0-9.-]*)\//g)].map((m) => m[1]),
  )
  assert.ok(hosts.size > 0, 'esperava algum host de tile no código')
  for (const host of hosts) {
    assert.match(
      HTML,
      new RegExp(`rel="preconnect" href="https://${host}"`),
      `${host} serve tiles e não tem preconnect no index.html`,
    )
  }
})
