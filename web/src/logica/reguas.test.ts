import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { agruparPorCurso, reguasComCota, separarFonte, todasAsReguas } from './reguas'
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
test('Ilhota não tem régua própria — a DC-11 é de Itajaí, não dela', () => {
  // A DC-11 (Santa Regina / Volta de Cima) fica na divisa mas é estação de
  // Itajaí, confirmado no Plano de Contingência da COMPDEC Itajaí. Ler o nível
  // dela como o de Ilhota é comparar réguas de cidades diferentes.
  const saida = reguasComCota(estacoesTempoReal, 'itajai-acu', 'ilhota')
  assert.equal(saida.length, 0)
})

test('Itajaí mostra cota nas duas telas; no Açu a DC-11 dispara e o estuário não', () => {
  const acu = reguasComCota(estacoesTempoReal, 'itajai-acu', 'itajai')
  const mirim = reguasComCota(estacoesTempoReal, 'itajai-mirim', 'itajai')
  assert.ok(acu.length > 0, 'a tela do Açu ficaria dizendo que Itajaí não tem cota')
  assert.ok(mirim.length > 0, 'a tela do Mirim ficaria dizendo que Itajaí não tem cota')
  // DC-01 e DC-02 estão no estuário: não disparam sozinhas.
  assert.equal(acu.find((r) => r.id === 'DC-01')!.alertaAutomatico, false)
  assert.equal(acu.find((r) => r.id === 'DC-02')!.alertaAutomatico, false)
  // A DC-11, em Santa Regina, fica acima da maré e dispara — é a única de rio
  // no Açu de Itajaí.
  assert.equal(acu.find((r) => r.id === 'DC-11')!.alertaAutomatico, true)
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

test('agruparPorCurso: cursos na ordem rio→ribeirão e réguas montante→foz', () => {
  const todas = todasAsReguas(estacoesTempoReal, 'itajai')
  const grupos = agruparPorCurso(todas)
  // Os quatro cursos de Itajaí, nesta ordem: os dois rios, depois os ribeirões.
  assert.deepEqual(
    grupos.map((g) => g.rio),
    ['itajai-acu', 'itajai-mirim', 'ribeirao-murta', 'ribeirao-canhanduba'],
  )
  // No Mirim, Limoeiro (DC-10) é a mais a montante — vem primeiro.
  const mirim = grupos.find((g) => g.rio === 'itajai-mirim')!
  assert.equal(mirim.reguas[0]!.id, 'DC-10')
  // A ordem_descida é monótona não decrescente descendo a lista.
  for (let i = 1; i < mirim.reguas.length; i++) {
    const a = mirim.reguas[i - 1]!.ordemDescida
    const b = mirim.reguas[i]!.ordemDescida
    if (a != null && b != null) assert.ok(a <= b, `${mirim.reguas[i]!.id} fora de ordem`)
  }
})

test('agruparPorCurso: DC-04 e DC-06 ficam co-locadas, sem fila entre elas', () => {
  const grupos = agruparPorCurso(todasAsReguas(estacoesTempoReal, 'itajai'))
  const mirim = grupos.find((g) => g.rio === 'itajai-mirim')!
  const d4 = mirim.reguas.find((r) => r.id === 'DC-04')!
  const d6 = mirim.reguas.find((r) => r.id === 'DC-06')!
  assert.equal(d4.ordemDescida, d6.ordemDescida, 'mesma posição na descida')
  assert.ok(d4.ordemNota, 'a co-locada explica que a ordem entre elas é indefinível')
})

test('agruparPorCurso: o Mirim se divide em curso antigo e canal, com o reencontro', () => {
  const grupos = agruparPorCurso(todasAsReguas(estacoesTempoReal, 'itajai'))
  const mirim = grupos.find((g) => g.rio === 'itajai-mirim')!
  assert.ok(mirim.divisao, 'o Mirim deveria vir dividido em braços')
  const div = mirim.divisao!
  // DC-10 fica antes da bifurcação.
  assert.deepEqual(div.antes.map((r) => r.id), ['DC-10'])
  // Dois braços, curso antigo primeiro, canal depois.
  assert.deepEqual(div.bracos.map((b) => b.chave), ['curso antigo', 'canal retificado'])
  const antigo = div.bracos[0]!, canal = div.bracos[1]!
  assert.deepEqual(antigo.reguas.map((r) => r.id), ['DC-05', 'DC-06'])
  assert.deepEqual(canal.reguas.map((r) => r.id), ['DC-03', 'DC-04'])
  // O reencontro é o par co-locado, um de cada braço.
  assert.deepEqual(new Set(div.reencontro.map((r) => r.id)), new Set(['DC-06', 'DC-04']))
})

test('agruparPorCurso: cursos que não bifurcam não ganham divisao', () => {
  const grupos = agruparPorCurso(todasAsReguas(estacoesTempoReal, 'itajai'))
  for (const rio of ['itajai-acu', 'ribeirao-murta', 'ribeirao-canhanduba']) {
    assert.equal(grupos.find((g) => g.rio === rio)!.divisao, undefined, `${rio} não bifurca`)
  }
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
