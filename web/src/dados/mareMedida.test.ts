import assert from 'node:assert/strict'
import { test } from 'node:test'
import { deBrasilia } from '../logica/tempoReal'
import {
  buscarMareMedida,
  comSinal,
  estadoDaMareMedida,
  montarMareMedida,
  textoDaMareMedida,
} from './mareMedida'

// Decisão do Jefferson de 07/10/2026: número só com horário, estação, unidade e referência vertical
// identificados; leitura antiga nunca como atual; a diferença só da mesma estação, no mesmo horário.

const AGORA = deBrasilia('2026-10-07T19:09:00')

/** O arquivo que o coletor publicou às 19:09 de 07/10/2026 (referência pendente). */
function publicado(extra: Record<string, unknown> = {}): Record<string, any> {
  return {
    versao: 1,
    gerado_em: '2026-10-07T22:09:00+00:00',
    fonte: 'EPAGRI/CIRAM — marégrafos',
    fonte_url: 'https://ciram.epagri.sc.gov.br/index.php/maregrafos/',
    estacao: { id: 'balneario-camboriu', nome: 'Balneário Camboriú', endpoint: 'getDataMare5_2927.php', km_da_foz: 13 },
    unidade: 'm',
    referencia_vertical: { status: 'pendente', descricao: null, fonte: null },
    situacao: 'medindo',
    ultima_medicao: { medido_em: '2026-10-07T18:30:00' },
    ...extra,
  }
}

const CONFIRMADA = {
  referencia_vertical: { status: 'confirmada', descricao: 'zero do marégrafo X', fonte: 'ofício Y' },
  ultima_medicao: {
    medido_em: '2026-10-07T18:30:00',
    observada_m: 0.618,
    astronomica_m: 0.45,
    diferenca_observado_astronomica_m: 0.168,
  },
}

test('hoje: o marégrafo mede, mas a referência está pendente e o número não aparece', () => {
  const e = estadoDaMareMedida(montarMareMedida(publicado()), AGORA)
  assert.equal(e.tipo, 'referencia-pendente')
  const { titulo, detalhe } = textoDaMareMedida(e)
  assert.equal(titulo, 'Referência pendente.')
  assert.match(detalhe, /07\/10 às 18:30 \(Brasília\), há 39 min/)
  assert.match(detalhe, /referência vertical/)
  assert.doesNotMatch(detalhe, /\d,\d{2} m/, 'saiu um nível sem referência')
})

test('número na referência pendente não aparece nem se o arquivo trouxer', () => {
  const comNumero = publicado({ ultima_medicao: { ...CONFIRMADA.ultima_medicao } })
  assert.equal(estadoDaMareMedida(montarMareMedida(comNumero), AGORA).tipo, 'referencia-pendente')
})

test('referência "confirmada" sem fonte não vale', () => {
  const semFonte = publicado({
    ...CONFIRMADA,
    referencia_vertical: { status: 'confirmada', descricao: 'zero X', fonte: '' },
  })
  assert.equal(estadoDaMareMedida(montarMareMedida(semFonte), AGORA).tipo, 'referencia-pendente')
})

test('com a referência confirmada: nível, hora e a diferença da mesma linha, com o nome combinado', () => {
  const e = estadoDaMareMedida(montarMareMedida(publicado(CONFIRMADA)), AGORA)
  assert.equal(e.tipo, 'medida')
  if (e.tipo !== 'medida') return
  assert.equal(e.observadaM, 0.618)
  assert.equal(e.diferencaM, 0.168)
  assert.match(textoDaMareMedida(e).titulo, /Nível observado: 0,62 m/)
  assert.match(textoDaMareMedida(e).detalhe, /zero do marégrafo X/)
  assert.equal(comSinal(0.168), '+0,17 m')
  assert.equal(comSinal(-0.016), '−0,02 m')
})

test('sem a astronômica na mesma linha, não há diferença', () => {
  const semAstr = publicado({
    ...CONFIRMADA,
    ultima_medicao: { medido_em: '2026-10-07T18:30:00', observada_m: 0.618, astronomica_m: null, diferenca_observado_astronomica_m: 0.168 },
  })
  const e = estadoDaMareMedida(montarMareMedida(semAstr), AGORA)
  assert.equal(e.tipo === 'medida' ? e.diferencaM : 'x', null)
})

test('leitura antiga nunca aparece como atual, nem com referência confirmada', () => {
  const m = montarMareMedida(publicado(CONFIRMADA))
  // 18:30 + 61 min: passou da hora de frescor (60 min), refeita no relógio de agora.
  const depois = deBrasilia('2026-10-07T19:31:00')
  const e = estadoDaMareMedida({ ...m!, geradoEm: new Date(depois.getTime() - 5 * 60_000) }, depois)
  assert.equal(e.tipo, 'antiga')
  const { titulo, detalhe } = textoDaMareMedida(e)
  assert.equal(titulo, 'Medição indisponível.')
  assert.match(detalhe, /Não é atual/)
  assert.doesNotMatch(detalhe, /0,62/)
})

test('arquivo de publicação parada ou do futuro: medição indisponível', () => {
  const m = montarMareMedida(publicado(CONFIRMADA))!
  assert.equal(estadoDaMareMedida(m, deBrasilia('2026-10-07T19:40:00')).tipo, 'indisponivel', '31 min')
  assert.equal(estadoDaMareMedida({ ...m, geradoEm: new Date(AGORA.getTime() + 20 * 60_000) }, AGORA).tipo, 'indisponivel')
})

test('medição do futuro não passa por atual', () => {
  const futuro = publicado({ ...CONFIRMADA, ultima_medicao: { ...CONFIRMADA.ultima_medicao, medido_em: '2026-10-07T20:00:00' } })
  const e = estadoDaMareMedida(montarMareMedida(futuro), AGORA)
  assert.equal(e.tipo, 'antiga')
  assert.match(textoDaMareMedida(e).detalhe, /ainda não chegou/)
})

test('arquivo fora do combinado é "medição indisponível"', () => {
  for (const ruim of [
    null,
    '<html>',
    publicado({ versao: 2 }),
    publicado({ unidade: 'cm' }),
    publicado({ gerado_em: '2026-10-07T22:09:00' }),
    publicado({ estacao: {} }),
    publicado({ ultima_medicao: { medido_em: '2026-10-07T18:30:00-03:00' } }),
  ]) {
    assert.equal(estadoDaMareMedida(montarMareMedida(ruim), AGORA).tipo, 'indisponivel', JSON.stringify(ruim))
  }
  assert.equal(estadoDaMareMedida(montarMareMedida(publicado({ ultima_medicao: null })), AGORA).tipo, 'indisponivel')
})

test('nenhum texto atribui a diferença só a vento e pressão', () => {
  const e = estadoDaMareMedida(montarMareMedida(publicado(CONFIRMADA)), AGORA)
  const tudo = Object.values(textoDaMareMedida(e)).join(' ').toLowerCase()
  assert.doesNotMatch(tudo, /meteorológica/)
})

test('sem o arquivo (rede fora, VPS sem a coleta): indisponível', async () => {
  assert.equal(await buscarMareMedida(undefined, async () => new Response('não', { status: 404 })), null)
  assert.equal(await buscarMareMedida(undefined, async () => { throw new Error('rede') }), null)
  const ok = await buscarMareMedida(undefined, async () => new Response(JSON.stringify(publicado()), { status: 200 }))
  assert.equal(ok?.estacao.nome, 'Balneário Camboriú')
})
