import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { reguasComCota, separarFonte, todasAsReguas } from './reguas'
import type { EstacaoTempoReal } from '../dados/tipos'

/*
 * Lê o JSON de `data/` direto do disco, e não por `dados/carregar`: o alias
 * `@dados` existe só na configuração do Vite, e o runner de teste é o `node`.
 * O arquivo é o mesmo que a tela carrega.
 */
const estacoesTempoReal: EstacaoTempoReal[] =
  JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'))
    .estacoes_tempo_real ?? []

function est(over: Partial<EstacaoTempoReal>): EstacaoTempoReal {
  return {
    titulo: 'Régua de teste',
    rio: 'itajai-acu',
    cidade: 'itajai',
    cotas_m: { atencao: 1 },
    verificado: true,
    ...over,
  }
}

const ids = (r: ReturnType<typeof reguasComCota>) => r.map((x) => x.id)

test('só traz régua da cidade e do rio pedidos', () => {
  const base = [
    est({ codigo: 'A', cidade: 'itajai', rio: 'itajai-acu' }),
    est({ codigo: 'B', cidade: 'itajai', rio: 'itajai-mirim' }),
    est({ codigo: 'C', cidade: 'ilhota', rio: 'itajai-acu' }),
  ]
  assert.deepEqual(ids(reguasComCota(base, 'itajai-acu', 'itajai')), ['A'])
})

test('descarta régua sem cota em vez de mostrar cota vazia', () => {
  const base = [est({ codigo: 'A', cotas_m: {} }), est({ codigo: 'B' })]
  assert.deepEqual(ids(reguasComCota(base, 'itajai-acu', 'itajai')), ['B'])
})

test('descarta pluviômetro: ele mede chuva, não nível', () => {
  const base = [est({ codigo: 'P', tipo: 'pluviometro', cotas_m: { atencao: 1 } })]
  assert.deepEqual(reguasComCota(base, 'itajai-acu', 'itajai'), [])
})

test('descarta cota que não é número finito', () => {
  const base = [
    est({ codigo: 'A', cotas_m: { atencao: 'alta' as unknown as number } }),
    est({ codigo: 'B', cotas_m: { atencao: Number.NaN } }),
    est({ codigo: 'C', cotas_m: { atencao: 2, alerta: null as unknown as number } }),
  ]
  const saida = reguasComCota(base, 'itajai-acu', 'itajai')
  assert.deepEqual(ids(saida), ['C'])
  assert.deepEqual(saida[0]!.cotas, [['atencao', 2]])
})

test('sem aviso automático é só quem tem o campo em false', () => {
  const base = [
    est({ codigo: 'MARE', alerta_automatico: false, motivo_sem_alerta: 'estuário' }),
    est({ codigo: 'RIO' }),
    est({ codigo: 'EXPLICITO', alerta_automatico: true }),
  ]
  const saida = reguasComCota(base, 'itajai-acu', 'itajai')
  assert.deepEqual(
    saida.map((r) => [r.id, r.alertaAutomatico]),
    [
      ['MARE', false],
      ['RIO', true],
      ['EXPLICITO', true],
    ],
  )
  assert.equal(saida[0]!.motivoSemAlerta, 'estuário')
})

test('usa o nome do plano oficial, com o código na frente quando falta', () => {
  const base = [
    est({ codigo: 'DC-10', titulo: 'DC-10 Rio Itajaí-Mirim', nome_no_plano: 'Limoeiro' }),
  ]
  assert.equal(reguasComCota(base, 'itajai-acu', 'itajai')[0]!.nome, 'DC-10 — Limoeiro')
})

test('não repete o código quando o nome já começa com ele', () => {
  const base = [est({ codigo: 'DC-10', titulo: 'DC-10 Limoeiro' })]
  assert.equal(reguasComCota(base, 'itajai-acu', 'itajai')[0]!.nome, 'DC-10 Limoeiro')
})

/*
 * Os dados reais. Itajaí e Ilhota TÊM cota oficial publicada (Plano de
 * Contingência da COMPDEC), e a tela dizia "cotas de referência não
 * levantadas" para as duas. Se alguém mexer no estacoes.json e essas cotas
 * sumirem da tela outra vez, é aqui que quebra.
 */
test('Ilhota mostra a régua DC-11, que vale para aviso', () => {
  const saida = reguasComCota(estacoesTempoReal, 'itajai-acu', 'ilhota')
  assert.equal(saida.length, 1)
  assert.equal(saida[0]!.id, 'DC-11')
  assert.equal(saida[0]!.alertaAutomatico, true)
  const cotas = Object.fromEntries(saida[0]!.cotas)
  assert.equal(cotas.atencao, 3)
  assert.equal(cotas.alerta, 4)
})

test('Itajaí mostra cota nas duas telas, e a do Açu é toda de estuário', () => {
  const acu = reguasComCota(estacoesTempoReal, 'itajai-acu', 'itajai')
  const mirim = reguasComCota(estacoesTempoReal, 'itajai-mirim', 'itajai')
  assert.ok(acu.length > 0, 'a tela do Açu ficaria dizendo que Itajaí não tem cota')
  assert.ok(mirim.length > 0, 'a tela do Mirim ficaria dizendo que Itajaí não tem cota')
  // DC-01 e DC-02 estão no estuário: nenhuma dispara aviso sozinha.
  assert.ok(acu.every((r) => !r.alertaAutomatico))
  // Limoeiro (DC-10) fica rio acima e não sofre maré.
  assert.equal(mirim.find((r) => r.id === 'DC-10')!.alertaAutomatico, true)
})

test('toda régua sem aviso automático explica por quê', () => {
  for (const rio of ['itajai-acu', 'itajai-mirim']) {
    for (const cidade of ['itajai', 'ilhota']) {
      for (const r of reguasComCota(estacoesTempoReal, rio, cidade)) {
        if (!r.alertaAutomatico) assert.ok(r.motivoSemAlerta, `${r.id} sem motivo escrito`)
      }
    }
  }
})

test('todas as réguas de Itajaí incluem os ribeirões, que não têm tela de rio', () => {
  const todas = todasAsReguas(estacoesTempoReal, 'itajai')
  const ribeiroes = todas.filter((r) => (r.rio ?? '').startsWith('ribeirao-'))
  assert.ok(ribeiroes.length > 0, 'Murta e Canhanduba sumiriam de todas as telas')
  // Nenhuma delas aparece nas telas de rio — é por isso que a tela de Itajaí
  // usa `todasAsReguas` e não `reguasComCota`.
  const nasTelas = [
    ...reguasComCota(estacoesTempoReal, 'itajai-acu', 'itajai'),
    ...reguasComCota(estacoesTempoReal, 'itajai-mirim', 'itajai'),
  ].map((r) => r.id)
  for (const r of ribeiroes) assert.ok(!nasTelas.includes(r.id))
})

test('separarFonte tira a URL do texto sem inventar link', () => {
  assert.deepEqual(separarFonte('Plano de Contingência, Tabela 11 — https://x.gov.br/a.pdf'), {
    texto: 'Plano de Contingência, Tabela 11',
    url: 'https://x.gov.br/a.pdf',
  })
  assert.deepEqual(separarFonte('  Levantamento sem link  '), {
    texto: 'Levantamento sem link',
    url: null,
  })
})

test('toda cota exibida em Itajaí diz de que documento veio', () => {
  for (const r of todasAsReguas(estacoesTempoReal, 'itajai')) {
    assert.ok(r.fonteCotas, `${r.id} mostraria cota oficial sem fonte`)
  }
})
