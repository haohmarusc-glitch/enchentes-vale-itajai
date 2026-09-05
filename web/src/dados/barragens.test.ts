import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import {
  BARRAGENS_DA_CIDADE,
  barragensDaCidade,
  buscarBarragens,
  montarBarragens,
} from './barragens'
import type { Cidade } from './tipos'

/*
 * O corpo REAL, capturado na VPS em 05/09/2026, depois de passar pelo
 * `scripts/coleta_barragens.py`.
 */
const CORPO = {
  _meta: { fonte: 'asthon /dams' },
  barragens: [
    {
      nome: 'Barragem Oeste Taió',
      rio: 'Itajaí do Oeste',
      lat: -27.09743881225586,
      lon: -50.03879165649414,
      medido_em: '2026-09-05T14:05:06',
      altitude_montante_m: 353.66,
      nivel_na_regua_da_barragem_m: 14.66,
      percent_use: 31.79,
      comportas_abertas: 7,
      comportas_total: 7,
      comportas: Array.from({ length: 7 }, (_, i) => ({ nome: `C${i + 1}`, aberta: true })),
    },
    {
      nome: 'Barragem Sul Ituporanga',
      rio: 'Itajaí do Sul',
      lat: -27.503854751586914,
      lon: -49.55359649658203,
      medido_em: '2026-09-05T14:04:55',
      altitude_montante_m: 392.58,
      nivel_na_regua_da_barragem_m: 22.58,
      percent_use: 35.47,
      comportas_abertas: 5,
      comportas_total: 5,
      comportas: Array.from({ length: 5 }, (_, i) => ({ nome: `C${i + 1}`, aberta: true })),
    },
  ],
}

test('o corpo real vira as duas barragens', () => {
  const m = montarBarragens(CORPO)
  assert.equal(m.size, 2)
  const oeste = m.get('Barragem Oeste Taió')!
  assert.equal(oeste.abertas, 7)
  assert.equal(oeste.total, 7)
  assert.equal(oeste.fechadas.length, 0)
  assert.equal(oeste.percentUso, 31.79)
  // Comparado como INSTANTE, não como hora local: `getHours()` leria no fuso de
  // quem roda o teste, e a mesma asserção passaria aqui e falharia na CI.
  // 14:05:06 em Brasília é 17:05:06Z.
  assert.equal(oeste.medidoEm?.toISOString(), '2026-09-05T17:05:06.000Z')
})

/*
 * A régua da barragem tem zero PRÓPRIO (339 m de altitude na Oeste). Se o metro
 * dela atravessar para a tela, alguém o compara com os 5,24 m de Rio do Sul —
 * o erro central deste projeto, em forma de dois números lado a lado.
 */
test('o nível da barragem em metros NÃO atravessa para a tela', () => {
  const oeste = montarBarragens(CORPO).get('Barragem Oeste Taió')!
  const chaves = Object.keys(oeste)
  assert.ok(!chaves.some((k) => /nivel|altitude|montante/i.test(k)),
    `campo de nível vazou para a tela: ${chaves.join(', ')}`)
  assert.ok(!JSON.stringify(oeste).includes('353.66'))
  assert.ok(!JSON.stringify(oeste).includes('14.66'))
})

test('comporta sem o campo `aberta` conta como FECHADA', () => {
  // "Não sei" não pode virar "soltando água": a barragem pode estar segurando,
  // e o morador leria o contrário do que está acontecendo.
  const corpo = {
    barragens: [{
      nome: 'X', comportas_abertas: 2, comportas_total: 2,
      comportas: [{ nome: 'C1' }, { nome: 'C2', aberta: true }],
    }],
  }
  const b = montarBarragens(corpo).get('X')!
  assert.deepEqual(b.fechadas, ['C1'])
})

test('comporta com `aberta` que não é booleano true conta como fechada', () => {
  const corpo = {
    barragens: [{
      nome: 'X', comportas_abertas: 1, comportas_total: 1,
      comportas: [{ nome: 'C1', aberta: 'sim' }],
    }],
  }
  assert.deepEqual(montarBarragens(corpo).get('X')!.fechadas, ['C1'])
})

test('abertas maior que o total é corpo incoerente e a barragem some', () => {
  const corpo = { barragens: [{ nome: 'X', comportas_abertas: 9, comportas_total: 7 }] }
  assert.equal(montarBarragens(corpo).size, 0)
})

test('sem saber o total, "N de M" não significa nada e a barragem some', () => {
  assert.equal(montarBarragens({ barragens: [{ nome: 'X', comportas_abertas: 3 }] }).size, 0)
  assert.equal(
    montarBarragens({ barragens: [{ nome: 'X', comportas_abertas: 0, comportas_total: 0 }] }).size,
    0)
})

test('percent_use fora de 0..100 vira null em vez de número absurdo', () => {
  const corpo = {
    barragens: [{ nome: 'X', comportas_abertas: 1, comportas_total: 2, percent_use: 812 }],
  }
  assert.equal(montarBarragens(corpo).get('X')!.percentUso, null)
})

test('corpo quebrado vira mapa vazio, nunca palpite', () => {
  for (const ruim of [null, undefined, 42, 'texto', {}, { barragens: 'x' }, { barragens: [] }]) {
    assert.equal(montarBarragens(ruim).size, 0, JSON.stringify(ruim))
  }
})

test('resposta ruim da rede vira mapa vazio e não derruba a tela', async () => {
  const m = await buscarBarragens(undefined, async () => new Response('', { status: 500 }))
  assert.equal(m.size, 0)
  const n = await buscarBarragens(undefined, async () => { throw new Error('rede') })
  assert.equal(n.size, 0)
})

/*
 * O mapa cidade → barragem sai da topologia. Se a topologia mudar e o mapa não,
 * o site mostraria a barragem errada acima de uma cidade — este teste quebra
 * antes disso.
 */
test('o mapa cidade→barragem bate com os ramos do cadastro', () => {
  const estacoes = JSON.parse(
    readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'),
  ) as { rios: Record<string, { cidades: Cidade[] }> }
  const acu = estacoes.rios['itajai-acu']!.cidades
  const ramo = (id: string) => acu.find((c) => c.id === id)?.ramo ?? null

  // Taió está na cabeceira Oeste; Ituporanga, na Sul.
  assert.match(String(ramo('taio')), /oeste/i)
  assert.match(String(ramo('ituporanga')), /sul/i)
  // Rio do Sul é onde as duas se encontram — por isso, e só por isso, é a
  // única cidade com as DUAS barragens.
  assert.equal(ramo('rio-do-sul'), 'tronco_acu')

  assert.deepEqual(BARRAGENS_DA_CIDADE['taio'], ['Barragem Oeste Taió'])
  assert.deepEqual(BARRAGENS_DA_CIDADE['ituporanga'], ['Barragem Sul Ituporanga'])
  assert.equal(BARRAGENS_DA_CIDADE['rio-do-sul']!.length, 2)
})

test('cidade sem barragem acima não recebe nenhuma', () => {
  const m = montarBarragens(CORPO)
  for (const cidade of ['blumenau', 'itajai', 'gaspar', 'brusque']) {
    assert.deepEqual(barragensDaCidade(m, cidade), [], cidade)
  }
})

test('Rio do Sul recebe as duas; Taió, só a Oeste', () => {
  const m = montarBarragens(CORPO)
  assert.equal(barragensDaCidade(m, 'rio-do-sul').length, 2)
  const taio = barragensDaCidade(m, 'taio')
  assert.equal(taio.length, 1)
  assert.equal(taio[0]!.nome, 'Barragem Oeste Taió')
})

test('barragem que o cadastro pede mas a fonte não trouxe simplesmente não aparece', () => {
  // Meia resposta não pode virar meia verdade: some, em vez de mostrar "0 de 0".
  const soUma = { barragens: [CORPO.barragens[0]] }
  assert.equal(barragensDaCidade(montarBarragens(soUma), 'rio-do-sul').length, 1)
})

test('a coordenada da fonte atravessa — é o que põe o marcador no lugar exato', () => {
  const oeste = montarBarragens(CORPO).get('Barragem Oeste Taió')!
  assert.equal(oeste.lat, -27.09743881225586)
  assert.equal(oeste.lon, -50.03879165649414)
})

test('coordenada fora da bacia vira null, não marcador no lugar errado', () => {
  // Troca lat/lon, ou altitude no lugar de lat: num mapa de enchente, marcador
  // errado é pior que nenhum.
  for (const [lat, lon] of [[-50.03, -27.09], [353.66, -50.03], [0, 0]] as const) {
    const corpo = { barragens: [{ nome: 'X', comportas_abertas: 1, comportas_total: 1, lat, lon }] }
    const b = montarBarragens(corpo).get('X')!
    assert.equal(b.lat, null, `lat=${lat} lon=${lon}`)
    assert.equal(b.lon, null)
  }
})

test('sem coordenada a barragem segue existindo — só não vai ao mapa', () => {
  const corpo = { barragens: [{ nome: 'X', comportas_abertas: 1, comportas_total: 1 }] }
  const b = montarBarragens(corpo).get('X')!
  assert.equal(b.abertas, 1)
  assert.equal(b.lat, null)
})
