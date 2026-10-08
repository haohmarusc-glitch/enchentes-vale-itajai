import test from 'node:test'
import assert from 'node:assert/strict'
import {
  FRESCA_MIN,
  PERIODO_COMPORTA_S,
  barragensNoMapa,
  comportaAberta,
  comportas,
  faseComporta,
  rotuloComportas,
} from './barragensNoMapa'
import type { Barragem } from '../dados/barragens'

const AGORA = new Date('2026-09-05T17:30:00Z')

const oeste = (extra: Partial<Barragem> = {}): Barragem => ({
  nome: 'Barragem Oeste Taió', rio: 'Itajaí do Oeste',
  abertas: 7, total: 7, fechadas: [], percentUso: 31.79,
  medidoEm: new Date('2026-09-05T17:05:06Z'),
  lat: -27.09743881225586, lon: -50.03879165649414,
  ...extra,
})

test('barragem fresca com coordenada vira marcador', () => {
  const [m] = barragensNoMapa([oeste()], AGORA, 'itajai-acu')
  assert.ok(m)
  assert.equal(m.lat, -27.09743881225586)
  assert.equal(m.fresca, true)
  assert.equal(m.idadeMin, 25)
})

test('só aparece nos mapas do Açu e da bacia — no Mirim não existe', () => {
  assert.equal(barragensNoMapa([oeste()], AGORA, 'itajai-mirim').length, 0)
  assert.equal(barragensNoMapa([oeste()], AGORA, 'itajai-acu').length, 1)
  assert.equal(barragensNoMapa([oeste()], AGORA, 'bacia').length, 1)
})

test('sem coordenada não vai ao mapa — chutar posição é pior que não desenhar', () => {
  assert.equal(barragensNoMapa([oeste({ lat: null, lon: null })], AGORA, 'bacia').length, 0)
})

/*
 * "Cinza não corre" para a comporta: leitura velha não anima. A fonte publica a
 * cada 15 min; uma hora sem leitura nova é sinal de parada, e uma comporta
 * animando com estado de duas horas atrás afirma uma operação que não sabemos.
 */
test('leitura velha NÃO é fresca — a comporta para de animar', () => {
  const velha = new Date(AGORA.getTime() - (FRESCA_MIN + 1) * 60_000)
  const [m] = barragensNoMapa([oeste({ medidoEm: velha })], AGORA, 'bacia')
  assert.equal(m!.fresca, false)
  assert.equal(m!.idadeMin, FRESCA_MIN + 1)
})

test('no limite exato ainda é fresca; um minuto depois não', () => {
  const limite = new Date(AGORA.getTime() - FRESCA_MIN * 60_000)
  assert.equal(barragensNoMapa([oeste({ medidoEm: limite })], AGORA, 'bacia')[0]!.fresca, true)
})

test('sem carimbo não é "fresca por padrão" — é não sei, e não sei não anima', () => {
  const [m] = barragensNoMapa([oeste({ medidoEm: null })], AGORA, 'bacia')
  assert.equal(m!.fresca, false)
  assert.equal(m!.idadeMin, null)
})

test('carimbo no futuro não é fresca (relógio errado não vira animação)', () => {
  const futuro = new Date(AGORA.getTime() + 30 * 60_000)
  assert.equal(barragensNoMapa([oeste({ medidoEm: futuro })], AGORA, 'bacia')[0]!.fresca, false)
})

test('a fase da comporta anda com o tempo e dá uma volta por período', () => {
  assert.equal(faseComporta(0), 0)
  assert.ok(faseComporta(PERIODO_COMPORTA_S * 0.25) > 0.24 && faseComporta(PERIODO_COMPORTA_S * 0.25) < 0.26)
  // Uma volta inteira volta a zero (módulo), então quadros seguem girando.
  assert.ok(faseComporta(PERIODO_COMPORTA_S) < 1e-9)
  assert.notEqual(faseComporta(1), faseComporta(1.3), 'quadros diferentes têm fases diferentes')
})

test('tempo zero (reduced-motion) e valores inválidos dão fase 0 — quadro parado, sem sorteio', () => {
  for (const t of [0, -5, Number.NaN, Number.POSITIVE_INFINITY]) assert.equal(faseComporta(t), 0)
})

test('comportas: nomes C1..Cn na ordem, estado pela lista de fechadas', () => {
  const lista = comportas(7, ['C4'])
  assert.equal(lista.length, 7)
  assert.deepEqual(lista.map((c) => c.nome), ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7'])
  assert.deepEqual(lista.filter((c) => !c.aberta).map((c) => c.nome), ['C4'])
})

test('comporta que está na lista de fechadas está fechada; fora dela, aberta', () => {
  assert.equal(comportaAberta('C2', ['C2']), false)
  assert.equal(comportaAberta('C2', ['C1']), true)
  assert.equal(comportaAberta('C2', []), true)
})

test('o rótulo diz quantas abertas — e "fechadas" quando são todas', () => {
  assert.equal(rotuloComportas({ abertas: 7, total: 7 }), '7 de 7 abertas')
  assert.equal(rotuloComportas({ abertas: 3, total: 7 }), '3 de 7 abertas')
  assert.equal(rotuloComportas({ abertas: 0, total: 5 }), '5 de 5 fechadas')
})

test('funciona com um Map (como o hook devolve) e com N barragens, não só duas', () => {
  const tres = new Map<string, Barragem>([
    ['a', oeste({ nome: 'A' })],
    ['b', oeste({ nome: 'B', lat: -27.5, lon: -49.55 })],
    ['c', oeste({ nome: 'C', lat: -26.95, lon: -49.6 })],
  ])
  assert.equal(barragensNoMapa(tres.values(), AGORA, 'bacia').length, 3)
})

// --- Painel do toque e armazenamento (07/10/2026) -------------------------------------------------------------

import { fichaDaBarragem, ROTULO_PERCENTUAL, textoPercentual } from './barragensNoMapa'
import { montarBarragens } from '../dados/barragens'

/** O corpo publicado às 19h38 de 07/10/2026 (Oeste), pelo mesmo leitor do site. */
const OESTE_PUBLICADA = montarBarragens({
  _meta: { fonte: ['https://public.asthon.com.br/public/dams?city_id=4214805'] },
  barragens: [{
    nome: 'Barragem Oeste Taió', rio: 'Itajaí do Oeste', lat: -27.0974, lon: -50.0388, medido_em: '2026-10-07T19:38:10',
    altitude_montante_m: 347.97, nivel_na_regua_da_barragem_m: 8.97, zero_da_regua_m: 339.0, jusante_m: 5.14,
    percent_use: 4.4937, percent_use_divergencia_pp: 0.0, capacidade_atual: 4.4919, capacidade_maxima: 99.96,
    comportas_abertas: 7, comportas_total: 7, comportas: Array.from({ length: 7 }, (_, i) => ({ nome: `C${i + 1}`, aberta: true })),
    vertido_bruto: 0,
  }],
}).get('Barragem Oeste Taió')!

const linha = (f: ReturnType<typeof fichaDaBarragem>, rotulo: string) => f.linhas.find((l) => l.rotulo === rotulo)!

test('o painel mostra o que a fonte publica e "não informado" no resto — nunca zero', () => {
  const [b] = barragensNoMapa([OESTE_PUBLICADA], new Date('2026-10-07T19:50:00-03:00'), 'bacia')
  const f = fichaDaBarragem(b!)
  assert.match(f.situacao, /há 12 min/)
  assert.equal(linha(f, 'Comportas').valor, '7 de 7 abertas')
  assert.equal(ROTULO_PERCENTUAL, 'Percentual de ocupação informado pela fonte')
  assert.equal(linha(f, ROTULO_PERCENTUAL).valor, '4,5 %')
  assert.equal(linha(f, 'Nível na régua da barragem').valor, '8,97 m')
  assert.match(linha(f, 'Nível na régua da barragem').nota!, /339 m de altitude/)
  assert.match(linha(f, 'Nível na régua da barragem').nota!, /Não se compara com régua de rio/)
  assert.match(linha(f, 'Capacidade atual / máxima').nota!, /Unidade não informada/)
  assert.doesNotMatch(JSON.stringify(f), /m³|hm³|volume útil/, 'unidade ou nome presumido')
  assert.match(linha(f, ROTULO_PERCENTUAL).nota!, /capacidade atual dividida pela máxima/)
  assert.equal(linha(f, 'Vazão de entrada e de saída').valor, 'Não publicadas', 'vazão não publicada virou número')
  assert.equal(linha(f, 'Nível a jusante').valor, 'Sem referência da medição', 'jusante sem referência virou número')
  assert.doesNotMatch(JSON.stringify(f), /5,14/, 'o número a jusante vazou')
  assert.match(linha(f, 'Nível a jusante').nota!, /não é usado para classificar/)
  assert.match(linha(f, 'Medido em').valor!, /07\/10\/2026.*19:38.*Brasília/)
  assert.match(linha(f, 'Fonte').valor!, /asthon/)
})

test('leitura antiga é dita como tal no painel', () => {
  const [b] = barragensNoMapa([OESTE_PUBLICADA], new Date('2026-10-07T23:00:00-03:00'), 'bacia')
  assert.equal(b!.fresca, false)
  assert.match(fichaDaBarragem(b!).situacao, /Leitura antiga.*pode ter mudado/)
})

test('campo ausente é "não informado"; percentual implausível diz o que veio', () => {
  const crua = montarBarragens({ barragens: [{ nome: 'Y', lat: -27.1, lon: -50, comportas_abertas: 0, comportas_total: 3, percent_use: 812 }] }).get('Y')!
  const [b] = barragensNoMapa([crua], new Date(), 'bacia')
  const f = fichaDaBarragem(b!)
  assert.equal(f.situacao, 'Leitura sem horário: estado não confirmado.')
  assert.equal(linha(f, ROTULO_PERCENTUAL).valor, null)
  assert.match(linha(f, ROTULO_PERCENTUAL).nota!, /812 %, valor implausível/)
  assert.equal(linha(f, 'Nível na régua da barragem').valor, null)
  assert.equal(linha(f, 'Capacidade atual / máxima').valor, null)
  assert.equal(linha(f, 'Fonte').valor, null)
})

test('acima de 100 %: o valor real e o aviso de que passa da capacidade máxima publicada', () => {
  const crua = montarBarragens({ barragens: [{ nome: 'Z', lat: -27.1, lon: -50, comportas_abertas: 1, comportas_total: 3, percent_use: 104.2 }] }).get('Z')!
  const [b] = barragensNoMapa([crua], new Date(), 'bacia')
  const p = linha(fichaDaBarragem(b!), ROTULO_PERCENTUAL)
  assert.equal(p.valor, '104 %')
  assert.match(p.nota!, /acima da capacidade máxima publicada/)
  assert.equal(textoPercentual(4.49), '4,5 %')
})
