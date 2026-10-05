/**
 * "Como está Blumenau?" (05/10/2026, opção A): o chat mostra a última leitura com as regras
 * do cartão "Agora" e a chuva de 1/12/24 h; previsão e conselho continuam só com o aviso.
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { dados } from './testes/carregar'
import { TEXTO_ALERTA, cidadesConhecidas } from './motor'
import { RODAPE_PRESENTE, pedePrevisaoOuConselho, respostaDoPresente } from './situacaoAgora'
import { deBrasilia } from '../logica/tempoReal'
import type { AoVivo } from '../dados/usarAoVivo'
import type { ChuvaAoVivo, EstadoTempoReal, LeituraAoVivo } from '../dados/tempoReal'
import type { BrutoEstadual } from '../dados/nivelSc'
import type { Cidade } from '../dados/tipos'

const AGORA = deBrasilia('2026-10-05T15:50:00')
const RIOS = dados.estacoes.rios as unknown as Record<string, { cidades: Cidade[] }>

const leitura = (cidade: string, iso: string, nivel = 4.2, estacao = `Régua ${cidade}`): LeituraAoVivo => ({
  estacao, rio: 'itajai-acu', cidade, nivel_m: nivel, medidoEm: deBrasilia(iso), resgateDe: null,
})
const chuva = (cidade: string, iso: string, mm: Partial<ChuvaAoVivo['mm']>, coerente = true): ChuvaAoVivo => ({
  estacao: `Pluviômetro ${cidade}`, rio: 'itajai-acu', cidade, medidoEm: deBrasilia(iso), coerente, incoerencias: [],
  mm: { min10: 0.2, h1: 1.4, h12: 18.6, h24: 32, h48: 40.2, ...mm },
})
function aoVivo(leituras: LeituraAoVivo[], chuvas: ChuvaAoVivo[] = [], estaduais: BrutoEstadual[] = [], chuvaOk = true): AoVivo {
  return {
    tempoReal: { situacao: 'ok', leituras, chuva: chuvas, chuvaOk } as unknown as EstadoTempoReal,
    nivelSc: new Map(estaduais.map((b) => [b.cidade, b])),
    serie: { series: {} } as unknown as AoVivo['serie'],
    agora: AGORA,
  }
}
const responder = (pergunta: string, v: AoVivo | null) => respostaDoPresente({ pergunta, dados, rios: RIOS, aoVivo: v })

test('"como está Blumenau?": leitura de agora com hora, faixa da cidade, chuva 1/12/24 h, 199 e atalho', () => {
  const r = responder('como está Blumenau?', aoVivo([leitura('blumenau', '2026-10-05T15:40:00')], [chuva('blumenau', '2026-10-05T15:30:00', {})]))
  assert.match(r.texto, /^Última leitura da régua de Blumenau:\nBlumenau — 4,20 m \(faixa [^)]+, na régua de Blumenau\)/)
  assert.match(r.texto, /Medido às 15:40 de 05\/10 \(há 10 min\)/)
  assert.match(r.texto, /Chuva acumulada em Blumenau \(1 pluviômetro, medida até 15:30\): 1 h: 1,4 mm · 12 h: 18,6 mm · 24 h: 32,0 mm\./)
  assert.doesNotMatch(r.texto, /\b6 h\b|10 min:|48 h/)
  assert.ok(r.texto.endsWith(RODAPE_PRESENTE))
  assert.match(r.texto, /199/)
  assert.deepEqual(r.link, { texto: 'Ver Blumenau agora →', para: '/acu/blumenau' })
})

test('leitura velha não vira "agora": diz que não há leitura recente, sem número', () => {
  const r = responder('como está Blumenau?', aoVivo([leitura('blumenau', '2026-10-05T09:00:00', 9.99)]))
  assert.match(r.texto, /^O site não tem leitura recente da régua de Blumenau agora\./)
  assert.doesNotMatch(r.texto, /9,99/)
})

test('sem municipal de agora, a régua estadual aparece com o zero próprio escrito', () => {
  const est: BrutoEstadual = { cidade: 'ibirama', estacao: 'SDC-SC Ibirama', codigo: 'DCSC-00000', nivelBrutoM: 2.35, medidoEm: deBrasilia('2026-10-05T15:20:00'), faixaEstadual: 'atencao' }
  const r = responder('tem perigo em Ibirama?', aoVivo([], [], [est]))
  assert.match(r.texto, /rede da Defesa Civil de SC \(SDC-SC Ibirama\): 2,35 m, medido às 15:20/)
  assert.match(r.texto, /zero próprio/)
  assert.match(r.texto, /Faixa publicada pela Defesa Civil de SC: Atenção\./)
})

test('Itajaí (várias réguas): nenhum número, manda para a página de Itajaí', () => {
  const r = responder('como está Itajaí?', aoVivo([leitura('itajai', '2026-10-05T15:40:00', 1.1, 'Régua A'), leitura('itajai', '2026-10-05T15:40:00', 2.2, 'Régua B')]))
  assert.match(r.texto, /Itajaí tem várias réguas/)
  assert.doesNotMatch(r.texto, /1,10|2,20/)
  assert.equal(r.link?.para, '/itajai')
})

test('previsão ou conselho: só o aviso e o atalho, nenhum número', () => {
  const v = aoVivo([leitura('blumenau', '2026-10-05T15:40:00')], [chuva('blumenau', '2026-10-05T15:30:00', {})])
  for (const q of ['O rio vai encher hoje em Blumenau?', 'Devo sair de casa em Blumenau?', 'Estou com medo do rio em Blumenau, o que você acha?', 'Qual a previsão para Blumenau?', 'Compensa levar os móveis para cima em Blumenau?']) {
    assert.ok(pedePrevisaoOuConselho(q), q)
    const r = responder(q, v)
    assert.equal(r.texto, TEXTO_ALERTA, q)
    assert.equal(r.link?.para, '/acu/blumenau', q)
  }
  for (const q of ['como está Blumenau?', 'tem perigo em Rio do Sul?', 'o rio está alto em Timbó?']) assert.equal(pedePrevisaoOuConselho(q), false, q)
})

test('sem cidade, sem dado ao vivo ou cidade sem régua: o aviso de sempre', () => {
  assert.deepEqual(responder('como está o rio agora?', aoVivo([])), { texto: TEXTO_ALERTA })
  assert.deepEqual(responder('como está Blumenau?', null), { texto: TEXTO_ALERTA, link: { texto: 'Ver Blumenau agora →', para: '/acu/blumenau' } })
  const ids = new Set(Object.values(RIOS).flatMap((r) => r.cidades.map((c) => c.id)))
  const semRegua = cidadesConhecidas(dados).find((c) => !ids.has(c.id))
  if (semRegua) {
    const r = responder(`como está ${semRegua.nome}?`, aoVivo([]))
    assert.ok(r.texto.startsWith(`${semRegua.nome} não tem régua de rio neste site.`), r.texto)
    assert.equal(r.link, undefined)
  }
})

test('chuva velha, incoerente ou com a coleta falhando não aparece', () => {
  const l = [leitura('blumenau', '2026-10-05T15:40:00')]
  assert.doesNotMatch(responder('como está Blumenau?', aoVivo(l, [chuva('blumenau', '2026-10-05T08:00:00', {})])).texto, /Chuva/)
  assert.doesNotMatch(responder('como está Blumenau?', aoVivo(l, [chuva('blumenau', '2026-10-05T15:30:00', {}, false)])).texto, /Chuva/)
  assert.doesNotMatch(responder('como está Blumenau?', aoVivo(l, [chuva('blumenau', '2026-10-05T15:30:00', {})], [], false)).texto, /Chuva/)
  // Dois pluviômetros que discordam: a faixa dos dois, como no painel de chuva.
  const dois = responder('como está Blumenau?', aoVivo(l, [chuva('blumenau', '2026-10-05T15:30:00', { h24: 20 }), chuva('blumenau', '2026-10-05T15:30:00', { h24: 32 })]))
  assert.match(dois.texto, /2 pluviômetros.*24 h: 20,0–32,0 mm/)
})
