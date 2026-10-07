/**
 * 14ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): a linha do tempo da cheia de agora — quando
 * passou da cota, há quanto tempo está na faixa, quando começou a subir, quanto subiu em N horas.
 */
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { executar, limparRetratos, type Ambiente, type DadosDoChat } from './executar'
import { textoDeAjuda } from './ajuda'
import { cruzamentos, inicioDaSubida, pontoHorasAntes, textoLinhaDoTempo } from './linhaDoTempo'
import type { LeituraAoVivo } from '../dados/tempoReal'
import type { AoVivo } from '../dados/usarAoVivo'
import type { NivelSc } from '../dados/nivelSc'
import type { PontoSerie } from '../dados/serie'
import type { Cidade } from '../dados/tipos'
import type { Contexto } from './tipos'

const ler = (c: string) => JSON.parse(readFileSync(new URL(`../../../data/${c}`, import.meta.url), 'utf8'))
const estacoes = ler('estacoes.json')
const cat = catalogoDoCadastro(estacoes)
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const emBlumenau: Contexto = { cidadeAtual: 'blumenau', naMonitor: false, reguaAtual: null }
const AGORA = new Date('2026-10-06T18:00:00Z') // 15h00 em Brasília
const blumenau = (estacoes.rios['itajai-acu'].cidades as Cidade[]).find((c) => c.id === 'blumenau')!
const gaspar = (estacoes.rios['itajai-acu'].cidades as Cidade[]).find((c) => c.id === 'gaspar')!

const passos = (texto: string, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', `"${texto}" devia virar comando, veio ${JSON.stringify(r)}`)
  return r.passos
}

/** Uma série de 15 em 15 min, das `horas` atrás até agora, com o nível dado por `nivel(h)` (h = horas atrás). */
function serie(horas: number, nivel: (h: number) => number, regua = 'Blumenau'): PontoSerie[] {
  const pts: PontoSerie[] = []
  for (let m = horas * 60; m >= 0; m -= 15) pts.push({ medidoEm: new Date(AGORA.getTime() - m * 60_000), nivel_m: Math.round(nivel(m / 60) * 100) / 100, regua })
  return pts
}
// Sobe 20 cm/h desde 12 h atrás, a partir de 3,50 m: passa de 4,00 (Atenção) há ~9,5 h e de 6,00 (Alerta) há ~0,5 h… ajustado abaixo.
const subindo = serie(24, (h) => (h >= 12 ? 3.5 : 3.5 + (12 - h) * 0.25)) // 15h00: 6,50 m; cruza 4,00 há 10 h, 6,00 há 2 h
const passouEVoltou = serie(24, (h) => (h >= 12 ? 3.5 : h >= 6 ? 3.5 + (12 - h) * 0.5 : 6.5 - (6 - h) * 0.6)) // pico 6,50 há 6 h; agora 2,90
const parado = serie(24, () => 2.5) // abaixo de todas as cotas de Blumenau (Observação = 3,00 m)

test('frases: as quatro perguntas, com a cidade antes ou depois do verbo; o que não é delas continua onde estava', () => {
  assert.deepEqual(passos('quando Blumenau passou da cota de alerta?'), [{ tipo: 'linha_do_tempo', pergunta: 'cruzou_cota', cota: 'alerta', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('a que hora o rio passou da cota de atenção em Blumenau?'), [{ tipo: 'linha_do_tempo', pergunta: 'cruzou_cota', cota: 'atencao', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quando o rio passou da cota em Blumenau?'), [{ tipo: 'linha_do_tempo', pergunta: 'cruzou_cota', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quando Blumenau entrou em alerta máximo?'), [{ tipo: 'linha_do_tempo', pergunta: 'cruzou_cota', cota: 'emergencia', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('há quanto tempo Blumenau está em alerta?'), [{ tipo: 'linha_do_tempo', pergunta: 'ha_quanto_tempo', cota: 'alerta', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('há quanto tempo o rio está acima da cota de atenção em Blumenau?'), [{ tipo: 'linha_do_tempo', pergunta: 'ha_quanto_tempo', cota: 'atencao', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('há quanto tempo está em alerta?', emBlumenau), [{ tipo: 'linha_do_tempo', pergunta: 'ha_quanto_tempo', cota: 'alerta' }])
  assert.deepEqual(passos('quando o rio começou a subir em Blumenau?'), [{ tipo: 'linha_do_tempo', pergunta: 'comecou_a_subir', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quando Blumenau começou a subir?'), [{ tipo: 'linha_do_tempo', pergunta: 'comecou_a_subir', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('há quanto tempo o rio está subindo em Blumenau?'), [{ tipo: 'linha_do_tempo', pergunta: 'comecou_a_subir', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quanto Blumenau subiu nas últimas 6 horas?'), [{ tipo: 'linha_do_tempo', pergunta: 'variacao', horas: 6, cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quanto o rio subiu nas últimas 12 h em Blumenau?'), [{ tipo: 'linha_do_tempo', pergunta: 'variacao', horas: 12, cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quanto subiu em Blumenau nas últimas 3 horas?'), [{ tipo: 'linha_do_tempo', pergunta: 'variacao', horas: 3, cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quanto baixou nas últimas 2 horas?', emBlumenau), [{ tipo: 'linha_do_tempo', pergunta: 'variacao', horas: 2 }])
  // O que já existia continua igual.
  assert.deepEqual(passos('Blumenau está subindo?'), [{ tipo: 'tendencia', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quanto falta para a cota em Blumenau?'), [{ tipo: 'quanto_falta', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('o que mudou na última hora em Blumenau?'), [{ tipo: 'ultima_hora', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('máximo das últimas 24 h em Blumenau'), [{ tipo: 'maximo_24h', cidadeId: 'blumenau' }])
  assert.equal(interpretar('quanto tempo a cheia leva de Rio do Sul até Blumenau?', cat, fora), null, 'tempo de descida continua no motor')
  assert.equal(interpretar('quando foi a maior cheia de Blumenau?', cat, fora), null, 'histórico continua no motor')
  assert.equal(interpretar('quanto Pomerode subiu nas últimas 6 horas?', cat, fora), null, 'cidade fora do cadastro não vira comando')
})

test('contas: cruzamentos, começo da subida e o ponto de N horas antes', () => {
  const c = cruzamentos(subindo, 6)
  assert.equal(c.length, 1)
  assert.equal(c[0]!.sentido, 'subiu')
  assert.equal(c[0]!.quando.medidoEm.toISOString(), '2026-10-06T16:00:00.000Z', 'o primeiro ponto em 6,00 m, 2 h atrás')
  const pv = cruzamentos(passouEVoltou, 6)
  assert.deepEqual(pv.map((x) => x.sentido), ['subiu', 'desceu'])
  assert.equal(cruzamentos(parado, 4).length, 0)
  assert.equal(inicioDaSubida(subindo)!.medidoEm.toISOString(), '2026-10-06T06:00:00.000Z', 'o último ponto do patamar de 3,50 m, 12 h atrás')
  assert.equal(inicioDaSubida(passouEVoltou), null, 'descendo: não há subida em curso')
  assert.equal(inicioDaSubida(parado), null)
  assert.equal(pontoHorasAntes(subindo, 6)!.medidoEm.toISOString(), '2026-10-06T12:00:00.000Z')
  assert.equal(pontoHorasAntes(subindo, 30), null, 'a série de 24 h não chega a 30 h')
})

const texto = (pergunta: 'cruzou_cota' | 'ha_quanto_tempo' | 'comecou_a_subir' | 'variacao', pontos: PontoSerie[], extra: { cota?: string; horas?: number } = {}, cidade = blumenau) =>
  textoLinhaDoTempo({ pergunta, cidade, rotulo: cidade.nome, pontos, publicacao: null, agora: AGORA, janelaHoras: 48, ...extra })

test('textos: cada resposta diz hora de medição, a régua e o 199; leitura velha e cidade sem frase de cota são ditas', () => {
  const q = texto('cruzou_cota', subindo, { cota: 'alerta' })
  assert.match(q, /^Régua de Blumenau: passou da cota de Alerta \(6,00 m\) às 13:00 de 06\/10 \(medição a cada ~15 min: o cruzamento pode ter sido até 15 min antes\), de 5,94 m para 6,00 m\./)
  assert.match(q, /Continua na cota ou acima: 6,50 m às 15:00 de 06\/10, há 2 h\./)
  assert.match(q, /não compare com outras cidades[^]*199/)
  // Sem cota dita: a cota da faixa de agora (Alerta), com o nome da Defesa Civil de Blumenau.
  assert.match(texto('cruzou_cota', subindo), /passou da cota de Alerta \(6,00 m\) às 13:00/)
  assert.match(texto('cruzou_cota', subindo, { cota: 'emergencia' }), /não passou da cota de Alerta Máximo \(8,00 m\): o mais alto foi 6,50 m/)
  assert.match(texto('cruzou_cota', passouEVoltou, { cota: 'alerta' }), /passou da cota de Alerta \(6,00 m\) às 08:00 de 06\/10[^]*Voltou para baixo dela às 10:00 de 06\/10/)
  assert.match(texto('cruzou_cota', parado), /não passou de nenhuma cota: está em 2,50 m/)
  const h = texto('ha_quanto_tempo', subindo, { cota: 'alerta' })
  assert.match(h, /^Blumenau está em Alerta \(6,00 m\) há 2 h: passou da cota às 13:00 de 06\/10/)
  assert.match(texto('ha_quanto_tempo', subindo), /está em Alerta \(6,00 m\) há 2 h/, 'sem cota dita, a faixa de agora')
  assert.match(texto('ha_quanto_tempo', subindo, { cota: 'atencao' }), /está em Atenção \(4,00 m\) há 10 h/)
  assert.match(texto('ha_quanto_tempo', passouEVoltou, { cota: 'alerta' }), /não está em Alerta na última medição: 2,90 m[^]*Saiu dela às 10:00 de 06\/10/)
  assert.match(texto('ha_quanto_tempo', parado), /abaixo de todas as cotas[^]*não passou de nenhuma cota/)
  const s = texto('comecou_a_subir', subindo)
  assert.match(s, /a subida que ainda dura começou às 03:00 de 06\/10, em 3,50 m\. Até 15:00 de 06\/10 subiu 3,00 m \(6,50 m\), em 12 h, ~25 cm\/h em média\./)
  assert.match(texto('comecou_a_subir', passouEVoltou), /não está subindo na última medição \(2,90 m às 15:00 de 06\/10\)\. O ponto mais alto das 48 h publicadas foi 6,50 m às 09:00 de 06\/10; desde então, o rio desceu 3,60 m\./)
  assert.match(texto('comecou_a_subir', parado), /não está subindo/)
  const v = texto('variacao', subindo, { horas: 6 })
  assert.match(v, /^Régua de Blumenau: de 5,00 m às 09:00 de 06\/10 para 6,50 m às 15:00 de 06\/10 — subiu 1,50 m em 6 h\./)
  assert.match(texto('variacao', passouEVoltou, { horas: 12 }), /de 3,50 m às 03:00[^]*para 2,90 m às 15:00[^]*baixou 60 cm em 12 h\. No meio, chegou a 6,50 m às 09:00 de 06\/10\./)
  assert.match(texto('variacao', subindo, { horas: 30 }), /não chega a 30 h antes da última medição/)
  // Série velha: nada descreve o agora.
  const velha = subindo.slice(0, -16) // termina 4 h atrás
  assert.match(texto('variacao', velha, { horas: 6 }), /A série de Blumenau para às 11:00 de 06\/10 \(há 4 h\): depois disso ela não diz nada/)
  // Gaspar e Itajaí: as perguntas de cota são recusadas pelo mesmo motivo do "quanto falta"; as outras funcionam.
  assert.match(texto('cruzou_cota', subindo, {}, gaspar), /legenda da estação usa "maior que"/)
  assert.match(texto('ha_quanto_tempo', subindo, {}, gaspar), /"maior que"/)
  assert.match(texto('comecou_a_subir', subindo, {}, gaspar), /a subida que ainda dura começou/)
  assert.doesNotMatch(texto('variacao', subindo, { horas: 6 }), /previs[ãa]o de/, 'nunca prevê')
})

const cidadeDoCadastro = (id: string): { cidade: Cidade; rioId: string } | null => {
  for (const [rioId, r] of Object.entries(estacoes.rios as Record<string, { cidades: Cidade[] }>)) {
    const c = r.cidades.find((x) => x.id === id)
    if (c) return { cidade: c, rioId }
  }
  return null
}
const leitura = (cidade: string, nivel_m: number): LeituraAoVivo => ({ estacao: cidade, rio: 'itajai-acu', cidade, nivel_m, medidoEm: AGORA, resgateDe: null })
function ambiente(seriesItajai = false) {
  const aoVivo: AoVivo = {
    tempoReal: { situacao: 'ok', leituras: [leitura('blumenau', 6.5)], chuva: [], chuvaOk: true, coletadoEm: AGORA, fonte: null },
    nivelSc: new Map() as NivelSc,
    serie: {
      situacao: 'ok',
      series: {
        'itajai-acu': {
          blumenau: subindo,
          ...(seriesItajai ? { itajai: [...serie(6, (h) => 1 + h * 0.1, 'Itajaí — DC-01'), ...serie(6, (h) => 2 + h * 0.1, 'Itajaí — DC-02')].sort((a, b) => a.medidoEm.getTime() - b.medidoEm.getTime()) } : {}),
        },
      },
      resgates: {},
      janelaHoras: 48,
      geradoEm: AGORA,
    },
    agora: AGORA,
  }
  const dados: DadosDoChat = { aoVivo: async () => aoVivo, cidade: cidadeDoCadastro, reguasNoMapa: () => [], tracado: async () => null, base: () => '' }
  const navegacoes: string[] = []
  const amb: Ambiente = { navegar: (p) => navegacoes.push(p), rotaAtual: () => '/', monitor: () => null, esperarMonitor: async () => null, dados }
  return { amb, navegacoes }
}
const rodar = (texto: string, amb: Ambiente, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', texto)
  return executar(r.passos, amb, cat, ctx, () => textoDeAjuda(fora, null))
}

beforeEach(() => limparRetratos())

test('executor: a série de uma régua, o link da cidade, a sugestão seguinte; Itajaí pede a régua; nada navega', async () => {
  const { amb, navegacoes } = ambiente(true)
  const r = await rodar('há quanto tempo Blumenau está em alerta?', amb)
  assert.match(r.texto, /^Blumenau está em Alerta \(6,00 m\) há 2 h/)
  assert.deepEqual(r.link, { texto: 'Ver Blumenau agora →', para: '/acu/blumenau' })
  assert.deepEqual(r.sugestoes, ['quando Blumenau começou a subir?'])
  const i = await rodar('quanto Itajaí subiu nas últimas 3 horas?', amb)
  assert.match(i.texto, /Itajaí tem 2 réguas, cada uma com o seu zero: a linha do tempo é de uma régua só/)
  const semCidade = await rodar('quando passou da cota de alerta?', amb)
  assert.match(semCidade.texto, /Em qual cidade\?/)
  assert.deepEqual(navegacoes, [])
})

test('a ajuda lista os pedidos da 14ª entrega', () => {
  for (const ctx of [fora, { cidadeAtual: null, naMonitor: true, reguaAtual: null } as Contexto]) {
    const t = textoDeAjuda(ctx, null).texto
    for (const f of ['passou da cota de alerta?', 'há quanto tempo', 'começou a subir', 'subiu nas últimas 6 horas?']) assert.ok(t.includes(f), f)
  }
})
