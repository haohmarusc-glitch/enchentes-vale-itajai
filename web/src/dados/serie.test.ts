import { test } from 'node:test'
import assert from 'node:assert/strict'
import { buscarSerie, leituraEm, porRegua, serieDaCidade, tendencia } from './serie'
import type { PontoSerie, Transporte } from './serie'

/*
 * O que estes casos protegem: a série é a matéria-prima do slider de 24 h. Se
 * entrar ponto quebrado, se o `medido_em` (hora de Brasília sem fuso) sair
 * convertido errado, ou se a ordenação falhar, o gráfico mente sobre como o rio
 * está subindo — e é justamente disso que alguém decide sair de casa.
 */

const CORPO = {
  gerado_em: '2026-09-01T13:00:00+00:00',
  janela_horas: 48,
  series: {
    'itajai-acu': {
      'rio-do-sul': [
        { medido_em: '2026-09-01T09:00:00', nivel_m: 6.1 },
        { medido_em: '2026-09-01T08:00:00', nivel_m: 5.8 }, // fora de ordem de propósito
        { medido_em: '2026-09-01T10:00:00', nivel_m: 6.6 },
        { medido_em: 'lixo', nivel_m: 9 }, // carimbo inválido: sai
        { medido_em: '2026-09-01T11:00:00', nivel_m: null }, // sem nível: sai
      ],
    },
  },
}

function responde(corpo: unknown): Transporte {
  return async () => ({ ok: true, json: async () => corpo }) as Response
}

test('parseia, descarta ponto inválido e ordena no tempo', async () => {
  const estado = await buscarSerie(undefined, responde(CORPO))
  assert.equal(estado.situacao, 'ok')
  assert.equal(estado.janelaHoras, 48)
  const serie = serieDaCidade(estado, 'itajai-acu', 'rio-do-sul')
  assert.equal(serie.length, 3) // dois inválidos fora
  assert.deepEqual(serie.map((p) => p.nivel_m), [5.8, 6.1, 6.6]) // do mais antigo
})

test('medido_em é lido como hora de Brasília (UTC-3)', async () => {
  const estado = await buscarSerie(undefined, responde(CORPO))
  const serie = serieDaCidade(estado, 'itajai-acu', 'rio-do-sul')
  // 09:00 em Brasília = 12:00 UTC.
  assert.equal(serie[1]!.medidoEm.toISOString(), '2026-09-01T12:00:00.000Z')
})

test('resposta não-ok vira estado indisponível, sem inventar série', async () => {
  const estado = await buscarSerie(undefined, async () => ({ ok: false }) as Response)
  assert.equal(estado.situacao, 'indisponivel')
  assert.deepEqual(serieDaCidade(estado, 'itajai-acu', 'rio-do-sul'), [])
})

test('JSON sem series não quebra', async () => {
  const estado = await buscarSerie(undefined, responde({ gerado_em: 'x' }))
  assert.equal(estado.situacao, 'indisponivel')
})

test('cidade sem pontos não aparece', async () => {
  const estado = await buscarSerie(
    undefined,
    responde({ series: { 'itajai-acu': { itajai: [] } } }),
  )
  assert.deepEqual(serieDaCidade(estado, 'itajai-acu', 'itajai'), [])
})

test('leituraEm pega a última medição até o instante, nunca a futura', () => {
  const pts: PontoSerie[] = [
    { medidoEm: new Date('2026-09-01T12:00:00Z'), nivel_m: 3.0, regua: 'r' },
    { medidoEm: new Date('2026-09-01T13:00:00Z'), nivel_m: 4.0, regua: 'r' },
    { medidoEm: new Date('2026-09-01T14:00:00Z'), nivel_m: 5.0, regua: 'r' },
  ]
  // Antes de tudo: nada.
  assert.equal(leituraEm(pts, new Date('2026-09-01T11:00:00Z').getTime()), null)
  // Entre a 2ª e a 3ª: devolve a 2ª (nunca a de 14h, que ainda não aconteceu).
  assert.equal(leituraEm(pts, new Date('2026-09-01T13:30:00Z').getTime())?.nivel_m, 4.0)
  // Exatamente no carimbo: conta.
  assert.equal(leituraEm(pts, new Date('2026-09-01T14:00:00Z').getTime())?.nivel_m, 5.0)
})

/*
 * `tendencia` saiu de dentro do gráfico para cá porque não serve só de rótulo:
 * é o que diz se uma leitura VELHA ainda vale como aproximação do agora. Um
 * "subindo" errado aqui vira um aviso a mais na tela de quem decide sair de
 * casa; um "estável" errado esconde o rio subindo.
 */
function pontos(...pares: [string, number][]): PontoSerie[] {
  // Todos na MESMA régua: é o caso em que a tendência existe. A série que
  // mistura réguas tem teste próprio, mais abaixo.
  return pares.map(([iso, nivel_m]) => ({ medidoEm: new Date(iso), nivel_m, regua: 'r' }))
}

test('tendencia: subindo acima de 2 cm/h, com a taxa em cm/h', () => {
  const t = tendencia(pontos(
    ['2026-09-01T12:00:00Z', 3.0],
    ['2026-09-01T13:00:00Z', 3.2],
  ))
  assert.equal(t?.rotulo, 'subindo')
  assert.equal(t?.cmh, 20)
})

test('tendencia: descendo é simétrico', () => {
  const t = tendencia(pontos(
    ['2026-09-01T12:00:00Z', 3.2],
    ['2026-09-01T13:00:00Z', 3.0],
  ))
  assert.equal(t?.rotulo, 'descendo')
  assert.equal(t?.cmh, -20)
})

test('tendencia: oscilação de sensor abaixo de 2 cm/h é estável, não "subindo"', () => {
  // 1 cm em uma hora: dizer "subindo" aqui viraria ruído em tendência.
  const t = tendencia(pontos(
    ['2026-09-01T12:00:00Z', 3.00],
    ['2026-09-01T13:00:00Z', 3.01],
  ))
  assert.equal(t?.rotulo, 'estável')
})

test('tendencia: compara com ~1 h antes, não com o começo da série', () => {
  // O rio subiu muito de madrugada e está parado na última hora: a tendência
  // é do agora, senão a tela diria "subindo" com o rio estabilizado.
  const t = tendencia(pontos(
    ['2026-09-01T08:00:00Z', 1.0],
    ['2026-09-01T12:00:00Z', 5.0],
    ['2026-09-01T13:00:00Z', 5.0],
  ))
  assert.equal(t?.rotulo, 'estável')
})

test('tendencia: sem dois pontos não inventa direção', () => {
  assert.equal(tendencia([]), null)
  assert.equal(tendencia(pontos(['2026-09-01T12:00:00Z', 3.0])), null)
})

test('tendencia: dois pontos no mesmo instante não viram divisão por zero', () => {
  assert.equal(tendencia(pontos(
    ['2026-09-01T12:00:00Z', 3.0],
    ['2026-09-01T12:00:00Z', 4.0],
  )), null)
})

/*
 * SÉRIE QUE MISTURA RÉGUAS — o defeito de 04/09/2026.
 *
 * Uma cidade pode ter várias réguas com ZEROS DIFERENTES: Itajaí tem onze. Até
 * aqui a série publicada não dizia de que régua vinha cada ponto, e a série da
 * cidade saía com todas intercaladas. Medido no arquivo publicado:
 * `itajai-acu/itajai` era 2,70 → 1,20 → 0,56 → 2,71 → 1,20 → 0,56 …, salto
 * MEDIANO de 1,70 m entre pontos vizinhos.
 *
 * `tendencia` pega o último ponto e o de ~1 h antes: entre réguas distintas
 * isso é a diferença entre dois ZEROS, não entre dois instantes do rio.
 * Simulando o site em cada instante da janela de 48 h, `itajai-mirim/itajai`
 * daria |cm/h| > 100 em 707 dos 949 instantes, com pico de +2448 — "o rio sobe
 * 24 metros por hora" para quem mora na foz.
 */
const DC01 = 'DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL'
const DC02 = 'DC-02 Rio Itajaí-Açu - Praça Celso Pereira da Silva'
const DC11 = 'DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)'

/** As três réguas do Açu em Itajaí, com os níveis reais de 04/09, intercaladas. */
function tresReguasDeItajai(): PontoSerie[] {
  const saida: PontoSerie[] = []
  for (const h of [12, 13]) {
    for (const [regua, nivel_m] of [[DC11, 2.7], [DC02, 1.2], [DC01, 0.56]] as const) {
      saida.push({ medidoEm: new Date(`2026-09-04T${h}:00:00Z`), nivel_m, regua })
    }
  }
  return saida
}

test('porRegua separa a série em uma lista por régua, na ordem do tempo', () => {
  const grupos = porRegua(tresReguasDeItajai())
  assert.equal(grupos.size, 3)
  assert.deepEqual(grupos.get(DC11)!.map((p) => p.nivel_m), [2.7, 2.7])
  assert.deepEqual(grupos.get(DC01)!.map((p) => p.nivel_m), [0.56, 0.56])
  for (const pontos of grupos.values()) {
    const t = pontos.map((p) => p.medidoEm.getTime())
    assert.deepEqual(t, [...t].sort((a, b) => a - b))
  }
})

test('ponto sem régua fica no seu próprio grupo — não entra na de ninguém', () => {
  // Juntá-lo com uma régua nomeada afirmaria um zero de medição que a fonte
  // não disse.
  const grupos = porRegua([
    { medidoEm: new Date('2026-09-04T12:00:00Z'), nivel_m: 1.0, regua: DC02 },
    { medidoEm: new Date('2026-09-04T12:00:00Z'), nivel_m: 9.9, regua: null },
  ])
  assert.equal(grupos.size, 2)
  assert.deepEqual(grupos.get('')!.map((p) => p.nivel_m), [9.9])
})

test('O QUE IMPORTA: tendência de série misturada é null, não um número', () => {
  const misturada = tresReguasDeItajai()

  // A prova de que o fixture reproduz o defeito: sem a guarda, a conta que a
  // `tendencia` faz daria um absurdo.
  const ult = misturada[misturada.length - 1]!
  const ref = misturada[0]!
  const horas = (ult.medidoEm.getTime() - ref.medidoEm.getTime()) / 3_600_000
  const cmhIngenuo = Math.round(((ult.nivel_m - ref.nivel_m) * 100) / horas)
  assert.ok(
    Math.abs(cmhIngenuo) > 100,
    `o fixture parou de reproduzir o defeito (${cmhIngenuo} cm/h) — teste vazio`,
  )

  assert.equal(
    tendencia(misturada),
    null,
    'a tendência de uma série que mistura réguas é uma diferença entre ZEROS, ' +
      'não entre instantes do rio — tem de ser "não sei"',
  )
})

test('a mesma série, separada por régua, VOLTA a ter tendência', () => {
  // A guarda não pode virar "Itajaí nunca tem tendência": cada régua sozinha
  // continua uma série legítima.
  const grupos = porRegua([
    { medidoEm: new Date('2026-09-04T12:00:00Z'), nivel_m: 2.5, regua: DC11 },
    { medidoEm: new Date('2026-09-04T13:00:00Z'), nivel_m: 2.7, regua: DC11 },
    { medidoEm: new Date('2026-09-04T12:00:00Z'), nivel_m: 0.5, regua: DC01 },
    { medidoEm: new Date('2026-09-04T13:00:00Z'), nivel_m: 0.56, regua: DC01 },
  ])
  assert.equal(tendencia(grupos.get(DC11)!)?.cmh, 20)
  assert.equal(tendencia(grupos.get(DC01)!)?.rotulo, 'subindo')
})

test('cidade de uma régua só continua com tendência — nada regrediu', () => {
  assert.equal(
    tendencia(pontos(['2026-09-01T12:00:00Z', 3.0], ['2026-09-01T13:00:00Z', 3.2]))?.cmh,
    20,
  )
})

test('a régua vem do índice r e da legenda reguas[rio][cidade]', async () => {
  const estado = await buscarSerie(
    undefined,
    responde({
      reguas: { 'itajai-acu': { itajai: [DC01, DC11] } },
      series: {
        'itajai-acu': {
          itajai: [
            { medido_em: '2026-09-04T12:00:00', nivel_m: 0.56, r: 0 },
            { medido_em: '2026-09-04T12:01:00', nivel_m: 2.7, r: 1 },
            // fora da legenda e sem `r`: viram "não sei", nunca a primeira.
            { medido_em: '2026-09-04T12:02:00', nivel_m: 9.9, r: 7 },
            { medido_em: '2026-09-04T12:03:00', nivel_m: 8.8 },
          ],
        },
      },
    }),
  )
  const serie = serieDaCidade(estado, 'itajai-acu', 'itajai')
  assert.deepEqual(serie.map((p) => p.regua), [DC01, DC11, null, null])
  assert.equal(tendencia(serie), null, 'três grupos: não há tendência da cidade')
})

test('arquivo ANTIGO, sem reguas nem r, não quebra o site', async () => {
  // O publicador roda em cron e o site é implantado à parte: durante a janela
  // entre os dois, o arquivo no ar é o de antes. Ele tem de continuar valendo.
  const estado = await buscarSerie(
    undefined,
    responde({
      series: {
        'itajai-acu': {
          'rio-do-sul': [
            { medido_em: '2026-09-04T12:00:00', nivel_m: 5.3 },
            { medido_em: '2026-09-04T13:00:00', nivel_m: 5.5 },
          ],
        },
      },
    }),
  )
  const serie = serieDaCidade(estado, 'itajai-acu', 'rio-do-sul')
  assert.equal(serie.length, 2)
  assert.deepEqual(serie.map((p) => p.regua), [null, null])
  // Um grupo só (todos "sem régua"), então a tendência continua saindo.
  assert.equal(tendencia(serie)?.cmh, 20)
})
