import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { estacoesAnaDosPicos } from './estacoesAna'

const eventos: { cidade: string; fonte?: string }[] =
  JSON.parse(readFileSync(new URL('../../../data/enchentes.json', import.meta.url), 'utf8')).eventos
const picos = (cidade: string) => eventos.filter((e) => e.cidade === cidade)

test('Ituporanga: os picos são da 83250000, não da 83145140 do cadastro', () => {
  assert.deepEqual(estacoesAnaDosPicos(picos('ituporanga'), '83145140'), ['83250000'])
})

test('Apiúna: sem código no cadastro, a estação dos picos aparece', () => {
  assert.deepEqual(estacoesAnaDosPicos(picos('apiuna'), null), ['83500000'])
})

test('a estação do cadastro não se repete', () => {
  assert.deepEqual(estacoesAnaDosPicos(picos('blumenau'), '83800002'), [])
  assert.deepEqual(estacoesAnaDosPicos([{ fonte: 'ANA/HidroWeb, estação 83900000' }], '83900000'), [])
})

test('fonte sem ANA não inventa estação', () => {
  assert.deepEqual(estacoesAnaDosPicos([{ fonte: 'AlertaBlu, 12/09/2026, 83900000 leituras' }, {}], null), [])
})
