import assert from 'node:assert/strict'
import test from 'node:test'

import { readFileSync } from 'node:fs'

import { comoMostrar } from './fontesDoRodape'

const estacoes = JSON.parse(
  readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'),
)
const fontesGerais: Record<string, string> = estacoes.fontes_gerais
const fontesGeraisEstado = estacoes.fontes_gerais_estado

const FORA = {
  ceops_furb_acervo: { estado: 'fora_do_ar', observado: 'tempo de conexão esgotado' },
}

test('host que não responde não sai como link clicável', () => {
  const r = comoMostrar('ceops_furb_acervo', 'http://ceops.furb.br/x', FORA)
  assert.equal(r.tipo, 'fora_do_ar')
})

test('mas a fonte continua aparecendo, com o endereço e o motivo', () => {
  const r = comoMostrar('ceops_furb_acervo', 'http://ceops.furb.br/x', FORA)
  assert.equal(r.tipo === 'fora_do_ar' && r.endereco, 'http://ceops.furb.br/x')
  assert.match(r.tipo === 'fora_do_ar' ? r.observado : '', /esgotado/)
})

test('apagar a fonte seria pior que mostrá-la morta: ela segue na lista', () => {
  // Quem lê o rodapé quer saber DE ONDE veio o número. O link é secundário.
  assert.ok(Object.keys(fontesGerais).includes('ceops_furb_acervo'))
})

test('fonte sem registro de estado continua link normal', () => {
  const r = comoMostrar('ana_hidroweb', 'https://www.snirh.gov.br/x', FORA)
  assert.equal(r.tipo, 'link')
})

test('fonte marcada exige_cadastro ainda é link — ela abre, só pede login', () => {
  const r = comoMostrar('labgeo_furb', 'https://labgeo.furb.br/', {
    labgeo_furb: { estado: 'exige_cadastro', observado: 'pede login' },
  })
  assert.equal(r.tipo, 'link')
})

test('valor que não é URL (e-mail, descrição) nunca vira link', () => {
  const r = comoMostrar('ana_api_acesso', 'E-mail para hidro@ana.gov.br', undefined)
  assert.equal(r.tipo, 'texto')
})

test('nos dados REAIS, o CEOPS está marcado fora do ar', () => {
  // Trava o achado de 07/09/2026: se alguém reabrir o link sem conferir o host,
  // este teste cai junto.
  const r = comoMostrar('ceops_furb_acervo', fontesGerais.ceops_furb_acervo ?? '', fontesGeraisEstado)
  assert.equal(r.tipo, 'fora_do_ar')
})

test('nos dados REAIS, nenhuma fonte http:// insegura sobrou apontando para host vivo', () => {
  const inseguras = Object.entries(fontesGerais)
    .filter(([, v]) => v.startsWith('http://'))
    .filter(([k, v]) => comoMostrar(k, v ?? '', fontesGeraisEstado).tipo === 'link')
  assert.deepEqual(inseguras, [])
})
