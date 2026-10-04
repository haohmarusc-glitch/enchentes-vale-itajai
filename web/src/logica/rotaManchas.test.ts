import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { ROTA_MANCHAS_ITAJAI, pedeManchas } from './rotaManchas'

test('a rota de Itajaí pede a seção do mapa das manchas', () => {
  assert.equal(ROTA_MANCHAS_ITAJAI, '/itajai?secao=manchas')
  assert.equal(pedeManchas(ROTA_MANCHAS_ITAJAI.split('?')[1]!), true)
  assert.equal(pedeManchas('?secao=manchas'), true)
  assert.equal(pedeManchas(''), false)
  assert.equal(pedeManchas('aba=rua'), false)
})

test('"Minha rua alaga?" de Itajaí não leva mais só ao topo da foz', () => {
  // A Início de Itajaí mostrava o botão apontando para `/itajai`, que abre no
  // topo, longe do mapa — no celular parecia que o botão só mexia a tela.
  const cartoes = readFileSync(new URL('../componentes/CartoesDaCidade.tsx', import.meta.url), 'utf8')
  assert.match(cartoes, /cidade\.id === 'itajai' \? ROTA_MANCHAS_ITAJAI/)
  const inicio = readFileSync(new URL('../telas/Inicio.tsx', import.meta.url), 'utf8')
  assert.doesNotMatch(inicio, /Tudo sobre \{cidade\.nome\}: minha rua, histórico e fontes/, 'a foz não tem essas abas')
})
