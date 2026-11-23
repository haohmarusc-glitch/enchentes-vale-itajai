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

// --- Marégrafo de Itajaí, MRG01 (decisão do Jefferson de 23/11/2026) ---------------------------------------------

const AGORA_MRG = deBrasilia('2026-11-23T09:42:00')

/** O arquivo que `coleta_maregrafo_itajai.py` publicou às 09:42 de 23/11/2026, conferido contra o portal. */
function maregrafo(extra: Record<string, unknown> = {}): Record<string, any> {
  return {
    versao: 1,
    gerado_em: '2026-11-23T12:42:00+00:00',
    fonte: 'Defesa Civil de Itajaí / UNIVALI — marégrafo de Cabeçudas',
    fonte_url: 'https://monitoramento.defesacivil.itajai.sc.gov.br/monitoramento/maregrafo',
    estacao: { id: 'itajai-cabecudas', nome: 'Cabeçudas Iate Clube (MRG01), na foz do Itajaí-Açu', km_da_foz: 0 },
    unidade: 'm',
    referencia_vertical: {
      status: 'confirmada',
      descricao: 'zero da DHN (nível de redução)',
      fonte: 'portal da Defesa Civil de Itajaí, painel "MRG01 - Iate Clube - Maré Medida e Maré Prevista (DHN)"',
    },
    situacao: 'medindo',
    ultima_medicao: {
      medido_em: '2026-11-23T09:40:03',
      observada_m: 0.584,
      astronomica_m: 0.379,
      diferenca_observado_astronomica_m: 0.205,
    },
    astronomica_fonte: 'a previsão que o próprio portal publica para o MRG01, no mesmo horário e no zero da DHN',
    previsao: {
      referencia: 'zero da DHN (nível de redução)',
      extremos: [
        { tipo: 'preamar', quando: '2026-11-23T13:00', altura_m: 0.96 },
        { tipo: 'baixamar', quando: '2026-11-23T20:05', altura_m: 0.15 },
      ],
    },
    aviso: 'Nível do mar na foz do Itajaí-Açu, no zero da DHN: não é régua de rio.',
    ...extra,
  }
}

test('marégrafo de Itajaí: nível no zero da DHN, com a diferença da mesma estação', () => {
  const m = montarMareMedida(maregrafo())
  const e = estadoDaMareMedida(m, AGORA_MRG)
  assert.equal(e.tipo, 'medida')
  const { titulo, detalhe } = textoDaMareMedida(e)
  assert.equal(titulo, 'Nível observado: 0,58 m')
  assert.match(detalhe, /23\/11 às 09:40 \(Brasília\)/)
  assert.match(detalhe, /zero da DHN/)
  assert.equal(e.tipo === 'medida' ? comSinal(e.diferencaM!) : '', '+0,21 m')
  assert.match(m!.astronomicaFonte!, /mesmo horário/)
  assert.match(m!.aviso!, /não é régua de rio/)
})

test('marégrafo de Itajaí: extremos previstos com a referência escrita, só os que não passaram', async () => {
  const { extremosFuturos } = await import('./mareMedida')
  const m = montarMareMedida(maregrafo())!
  assert.equal(m.referenciaDosExtremos, 'zero da DHN (nível de redução)')
  assert.deepEqual(extremosFuturos(m, AGORA_MRG).map((e) => e.alturaM), [0.96, 0.15])
  assert.deepEqual(extremosFuturos(m, deBrasilia('2026-11-23T14:00:00')).map((e) => e.tipo), ['baixamar'])
})

test('marégrafo de Itajaí: extremo sem referência, com fuso ou sem altura não entra', () => {
  assert.deepEqual(montarMareMedida(maregrafo({ previsao: { extremos: maregrafo().previsao.extremos } }))!.extremos, [])
  const ruins = montarMareMedida(
    maregrafo({
      previsao: {
        referencia: 'zero da DHN',
        extremos: [
          { tipo: 'preamar', quando: '2026-11-23T13:00-03:00', altura_m: 0.96 },
          { tipo: 'baixamar', quando: '2026-11-23T20:05', altura_m: null },
          { tipo: 'maré', quando: '2026-11-23T20:05', altura_m: 0.1 },
        ],
      },
    }),
  )!
  assert.deepEqual(ruins.extremos, [])
  assert.equal(ruins.referenciaDosExtremos, null)
})

test('marégrafo de Itajaí: medição de mais de 60 min não aparece como atual', () => {
  const e = estadoDaMareMedida(montarMareMedida(maregrafo()), deBrasilia('2026-11-23T10:41:00'))
  assert.equal(e.tipo, 'indisponivel', 'o arquivo também passou dos 30 min')
  const velha = maregrafo({ gerado_em: '2026-11-23T13:41:00+00:00' })
  assert.equal(estadoDaMareMedida(montarMareMedida(velha), deBrasilia('2026-11-23T10:41:00')).tipo, 'antiga')
})

test('o arquivo do CIRAM, sem os campos novos, continua igual', () => {
  const m = montarMareMedida(publicado(CONFIRMADA))!
  assert.equal(m.astronomicaFonte, null)
  assert.equal(m.aviso, null)
  assert.deepEqual(m.extremos, [])
})
