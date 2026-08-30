import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fonteTempoReal, metros, numero, rotuloCota } from './formato'

test('cotas conhecidas saem acentuadas', () => {
  assert.equal(rotuloCota('atencao'), 'Atenção')
  assert.equal(rotuloCota('alerta'), 'Alerta')
  assert.equal(rotuloCota('inundacao'), 'Inundação')
  assert.equal(rotuloCota('transbordamento'), 'Transbordamento')
})

test('inundação histórica não sai como Inundacao_historica', () => {
  // Apareceu assim na tela de Blumenau: chave crua, sem acento e com sublinhado.
  assert.equal(rotuloCota('inundacao_historica'), 'Inundação histórica')
})

test('cota ainda não cadastrada perde o sublinhado', () => {
  assert.equal(rotuloCota('cota_de_rua'), 'Cota de rua')
  assert.equal(rotuloCota('transbordo'), 'Transbordo')
})

test('metros em português, sempre com duas casas', () => {
  assert.equal(metros(8.5), '8,50 m')
  assert.equal(metros(12), '12,00 m')
  assert.equal(numero(0.213), '0,21')
})

test('fonte de tempo real separa a URL do rótulo entre parênteses', () => {
  const { url, rotulo } = fonteTempoReal('https://defesacivil.itajai.sc.gov.br/x (DC-01, DC-02)')
  assert.equal(url, 'https://defesacivil.itajai.sc.gov.br/x')
  assert.equal(rotulo, 'defesacivil.itajai.sc.gov.br — DC-01, DC-02')
})

test('fonte sem rótulo mostra só o domínio', () => {
  assert.equal(fonteTempoReal('https://alertablu.blumenau.sc.gov.br/').rotulo, 'alertablu.blumenau.sc.gov.br')
})

test('texto que não é URL aparece como veio, em vez de sumir', () => {
  // O recorte por parênteses só vale quando o começo é mesmo uma URL (sem
  // espaços). Texto solto é mostrado inteiro — perder a informação seria pior
  // que mostrá-la sem formatação.
  const t = fonteTempoReal('tábua da Marinha (DHN)')
  assert.equal(t.rotulo, 'tábua da Marinha (DHN)')
  assert.equal(t.url, 'tábua da Marinha (DHN)')
})
