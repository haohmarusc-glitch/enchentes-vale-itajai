/**
 * Avisos da Defesa Civil de SC na tela (04/11/2026): por região, nunca por cidade; nada de faixa; arquivo fora do
 * combinado vira "indisponível"; aviso velho nunca sai como recente.
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { estadoDosAvisos, linhaDoAviso, montarAvisosDcsc, textoDosAvisos } from './avisosDcsc'

const AGORA = new Date('2026-11-04T13:00:00Z') // 10:00 em Brasília

const AVISO_BACIA = {
  id: 101,
  categoria: 'Alerta',
  titulo: 'ATENÇÃO – 04/11 09:34 – TEMPORAIS',
  publicado_em: '2026-11-04T09:34:00',
  publicado_em_utc: '2026-11-04T12:34:00',
  link: 'https://www.defesacivil.sc.gov.br/atencao-04-11-0934-temporais/',
  regioes: ['Vale do Itajaí', 'Litoral Norte'],
  estado_inteiro: false,
  inclui_bacia: true,
  trecho: 'Temporais com raios e rajadas nas próximas 4 horas…',
}
const AVISO_OESTE = {
  ...AVISO_BACIA, id: 102, categoria: 'Aviso', titulo: 'AVISO – 04/11 08:00 – CHUVA NO OESTE',
  publicado_em: '2026-11-04T08:00:00', regioes: ['Oeste'], inclui_bacia: false,
}
const AVISO_VELHO = {
  ...AVISO_BACIA, id: 90, titulo: 'ALERTA – 01/11 06:00 – CHUVA FORTE', publicado_em: '2026-11-01T06:00:00',
}

const ARQUIVO = {
  versao: 1,
  fonte: 'Defesa Civil de Santa Catarina — www.defesacivil.sc.gov.br (categorias Alerta e Aviso)',
  fonte_url: 'https://www.defesacivil.sc.gov.br/wp-json/wp/v2/posts?categories=7,6',
  gerado_em: '2026-11-04T12:50:00+00:00',
  regioes_da_bacia: ['Alto Vale', 'Foz do Itajaí', 'Litoral Norte', 'Médio Vale', 'Vale do Itajaí'],
  avisos: [AVISO_BACIA, AVISO_OESTE, AVISO_VELHO],
}

test('arquivo bom: avisos recentes da bacia, hora de Brasília, outras regiões só contadas', () => {
  const d = montarAvisosDcsc(ARQUIVO)!
  assert.ok(d)
  assert.equal(d.avisos[0]!.publicadoEm.toISOString(), '2026-11-04T12:34:00.000Z', '09:34 de Brasília = 12:34 UTC')
  const e = estadoDosAvisos(d, AGORA)
  assert.equal(e.tipo, 'avisos')
  if (e.tipo !== 'avisos') return
  assert.deepEqual(e.recentes.map((a) => a.id), [101], 'o do Oeste não cita a bacia; o de 01/11 tem mais de 24 h')
  assert.equal(e.outrasRegioes, 1)
  const t = textoDosAvisos(e)
  assert.match(t.titulo, /Um aviso recente da Defesa Civil de SC para a região/)
  assert.match(t.detalhe, /não é aviso para uma cidade nem faixa do rio/)
  assert.match(t.detalhe, /um aviso recente para outras regiões/)
  assert.equal(linhaDoAviso(e.recentes[0]!), 'Alerta · 04/11 às 09:34 (Brasília), há 26 min · Vale do Itajaí, Litoral Norte')
  assert.doesNotMatch(JSON.stringify(e), /faixa|cidade/, 'nenhuma faixa nem cidade sai daqui')
})

test('sem aviso recente da bacia: diz quando foi o último, e conta os de outras regiões', () => {
  const d = montarAvisosDcsc({ ...ARQUIVO, avisos: [AVISO_OESTE, AVISO_VELHO] })!
  const e = estadoDosAvisos(d, AGORA)
  assert.equal(e.tipo, 'nenhum')
  const t = textoDosAvisos(e)
  assert.equal(t.titulo, 'Nenhum aviso recente para a região.')
  assert.match(t.detalhe, /O último que citou uma região da bacia foi em 01\/11 às 06:00 \(Brasília\)/)
  assert.match(t.detalhe, /um aviso recente para outras regiões/)
})

test('"todo o Estado" cobre a bacia e sai como todo o Estado na linha', () => {
  const d = montarAvisosDcsc({ ...ARQUIVO, avisos: [{ ...AVISO_BACIA, regioes: [], estado_inteiro: true, inclui_bacia: true }] })!
  const e = estadoDosAvisos(d, AGORA)
  assert.equal(e.tipo, 'avisos')
  if (e.tipo === 'avisos') assert.match(linhaDoAviso(e.recentes[0]!), /· todo o Estado$/)
})

test('arquivo de publicação parada (> 30 min) é indisponível, mesmo com aviso dentro', () => {
  const d = montarAvisosDcsc(ARQUIVO)!
  assert.equal(estadoDosAvisos(d, new Date('2026-11-04T13:25:00Z')).tipo, 'indisponivel')
  assert.equal(estadoDosAvisos(null, AGORA).tipo, 'indisponivel')
  assert.match(textoDosAvisos({ tipo: 'indisponivel' }).detalhe, /Confira direto no site dela/)
})

test('publicado_em com fuso quebra o contrato: o aviso cai; gerado_em sem fuso recusa o arquivo', () => {
  const d = montarAvisosDcsc({ ...ARQUIVO, avisos: [{ ...AVISO_BACIA, publicado_em: '2026-11-04T09:34:00-03:00' }] })!
  assert.equal(d.avisos.length, 0)
  assert.equal(montarAvisosDcsc({ ...ARQUIVO, gerado_em: '2026-11-04T12:50:00' }), null)
  assert.equal(montarAvisosDcsc({ ...ARQUIVO, versao: 2 }), null)
  assert.equal(montarAvisosDcsc(null), null)
})

test('aviso do futuro não é recente; categoria desconhecida cai; link fora do site da DCSC não passa', () => {
  const d = montarAvisosDcsc({
    ...ARQUIVO,
    avisos: [
      { ...AVISO_BACIA, publicado_em: '2026-11-04T12:00:00' }, // 15:00 UTC, 2 h no futuro
      { ...AVISO_BACIA, id: 7, categoria: 'Monitoramento' },
      { ...AVISO_BACIA, id: 8, link: 'http://exemplo.com/x' },
    ],
  })!
  assert.deepEqual(d.avisos.map((a) => a.id), [101, 8])
  assert.equal(d.avisos.find((a) => a.id === 8)!.link, null)
  const e = estadoDosAvisos(d, AGORA)
  assert.equal(e.tipo, 'avisos')
  if (e.tipo === 'avisos') assert.deepEqual(e.recentes.map((a) => a.id), [8], 'o do futuro fica de fora')
})
