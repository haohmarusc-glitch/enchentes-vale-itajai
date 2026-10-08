/**
 * A régua do Centro de Ituporanga na tela (08/10/2026): com horário e fonte, sem cor; leitura antiga nunca
 * como atual; arquivo fora do combinado vira "indisponível".
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { estadoDoCentro, montarCentroItuporanga, textoDoCentro } from './ituporangaCentro'

const AGORA = new Date('2026-10-08T12:46:00Z') // 09:46 em Brasília

const ARQUIVO = {
  versao: 1,
  gerado_em: '2026-10-08T12:45:30+00:00',
  fonte: 'Prefeitura de Ituporanga — Defesa Civil, Boletim Diário (Nível do Rio)',
  fonte_url: 'https://www.ituporanga.sc.gov.br/nivel-rio',
  cidade: 'ituporanga',
  regua: { nome: 'Centro', identificada: false, nota: 'A fonte não nomeia a régua… Sem cor até confirmar.' },
  unidade: 'm',
  ultima_leitura: { medido_em: '2026-10-08T07:00:00', nivel_m: 2.04, criticidade_na_fonte: 'Alerta' },
}

test('arquivo bom: leitura com horário de Brasília, fonte e a criticidade como a fonte escreve', () => {
  const c = montarCentroItuporanga(ARQUIVO)!
  assert.ok(c)
  assert.equal(c.ultima.nivelM, 2.04)
  assert.equal(c.ultima.medidoEm.toISOString(), '2026-10-08T10:00:00.000Z', '07:00 de Brasília = 10:00 UTC')
  assert.equal(c.regua.identificada, false)
  const e = estadoDoCentro(c, AGORA)
  assert.equal(e.tipo, 'leitura')
  const t = textoDoCentro(e)
  assert.match(t.titulo, /Régua do Centro: 2,04 m/)
  assert.match(t.detalhe, /Lida em 08\/10 às 07:00 \(Brasília\)/)
  assert.match(t.detalhe, /classifica como “Alerta” — classificação dela, nas cotas dela/)
  assert.doesNotMatch(JSON.stringify(e), /faixa/, 'nenhuma faixa deste site sai daqui')
})

test('medido_em com fuso quebra o contrato: arquivo recusado', () => {
  assert.equal(montarCentroItuporanga({ ...ARQUIVO, ultima_leitura: { ...ARQUIVO.ultima_leitura, medido_em: '2026-10-08T07:00:00-03:00' } }), null)
})

test('gerado_em sem fuso, cidade errada ou unidade errada: arquivo recusado', () => {
  assert.equal(montarCentroItuporanga({ ...ARQUIVO, gerado_em: '2026-10-08T12:45:30' }), null)
  assert.equal(montarCentroItuporanga({ ...ARQUIVO, cidade: 'itajai' }), null)
  assert.equal(montarCentroItuporanga({ ...ARQUIVO, unidade: 'cm' }), null)
  assert.equal(montarCentroItuporanga(null), null)
})

test('arquivo de publicação parada (> 30 min) é indisponível, mesmo com leitura dentro', () => {
  const c = montarCentroItuporanga(ARQUIVO)!
  assert.equal(estadoDoCentro(c, new Date('2026-10-08T13:30:00Z')).tipo, 'indisponivel')
})

test('leitura com mais de 18 h não é atual: a hora aparece, o número não', () => {
  // 07:00 de Brasília em 08/10 = 10:00Z; 18 h depois é 04:00Z de 09/10. Às 05:00Z já passou.
  const c = montarCentroItuporanga({ ...ARQUIVO, gerado_em: '2026-10-09T04:55:00+00:00' })!
  const e = estadoDoCentro(c, new Date('2026-10-09T05:00:00Z'))
  assert.equal(e.tipo, 'antiga')
  const t = textoDoCentro(e)
  assert.match(t.titulo, /indisponível/)
  assert.match(t.detalhe, /08\/10 às 07:00/)
  assert.doesNotMatch(t.detalhe, /2,04/)
})

test('leitura do futuro nunca é atual', () => {
  const c = montarCentroItuporanga({ ...ARQUIVO, ultima_leitura: { ...ARQUIVO.ultima_leitura, medido_em: '2026-10-08T17:00:00' } })!
  assert.equal(estadoDoCentro(c, AGORA).tipo, 'antiga')
})
