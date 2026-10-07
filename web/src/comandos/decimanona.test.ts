/**
 * 19ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): o contexto da conversa, separado do da tela.
 */
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { continuar } from './continuar'
import { cidadeCitada, contextoComConversa, decidirContinuacao, memoriaDaConversa } from './conversa'
import { executar, limparRetratos } from './executar'
import { textoDeAjuda } from './ajuda'
import { chaveDoDiaDito, textoLinhaDoTempo } from './linhaDoTempo'
import { AGORA, CENARIOS, estacoes, serie } from './avaliacao/cenarios'
import type { Cidade } from '../dados/tipos'
import type { Contexto } from './tipos'

const cat = catalogoDoCadastro(estacoes)
const nomes = cat.cidades
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const monitorBlumenau: Contexto = { cidadeAtual: 'blumenau', naMonitor: true, reguaAtual: null }
const blumenau = (estacoes.rios['itajai-acu']!.cidades as Cidade[]).find((c) => c.id === 'blumenau')!

beforeEach(() => limparRetratos())

test('continuações novas: dia, número (com unidade), cota — uma troca só, na frase como foi escrita', () => {
  assert.deepEqual(continuar('e ontem?', 'quando Blumenau passou da cota de alerta?', nomes), { texto: 'quando Blumenau passou da cota de alerta ontem?', troca: 'dia' })
  assert.deepEqual(continuar('e hoje?', 'quando o rio passou da cota ontem em Blumenau?', nomes), { texto: 'quando o rio passou da cota hoje em Blumenau?', troca: 'dia' })
  assert.ok('erro' in continuar('e ontem?', 'como está Blumenau?', nomes)!, '"ontem" só troca o dia de uma pergunta de "quando"')
  assert.deepEqual(continuar('e com 9 m?', 'quais ruas alagam com 8 m em Blumenau?', nomes), { texto: 'quais ruas alagam com 9 m em Blumenau?', troca: 'numero' })
  assert.deepEqual(continuar('e 9,5 m?', 'quais ruas alagam com 8,50 m em Blumenau?', nomes), { texto: 'quais ruas alagam com 9,5 m em Blumenau?', troca: 'numero' })
  assert.deepEqual(continuar('e nas últimas 12 horas?', 'quanto Blumenau subiu nas últimas 6 horas?', nomes), { texto: 'quanto Blumenau subiu nas últimas 12 horas?', troca: 'numero' })
  assert.ok('erro' in continuar('e com 9 m?', 'quanto Blumenau subiu nas últimas 6 horas?', nomes)!, 'unidade diferente (m × h): não troca às cegas')
  assert.ok('erro' in continuar('e 12?', 'quais ruas alagam com 8 m em Blumenau e 9 m em Gaspar?', nomes)!, 'dois números: pergunta')
  assert.deepEqual(continuar('e de atenção?', 'quando Blumenau passou da cota de alerta?', nomes), { texto: 'quando Blumenau passou da cota de atencao?', troca: 'cota' })
  assert.deepEqual(continuar('e a de alerta máximo?', 'há quanto tempo Blumenau está em atenção?', nomes), { texto: 'há quanto tempo Blumenau está em alerta maximo?', troca: 'cota' })
  assert.ok('erro' in continuar('e de atenção?', 'como está Blumenau?', nomes)!, 'sem cota no anterior: pergunta')
  // O que já existia continua igual.
  assert.deepEqual(continuar('e Gaspar?', 'como está Blumenau?', nomes), { texto: 'como está Gaspar?', troca: 'cidade' })
  assert.deepEqual(continuar('de novo', 'satélite', nomes), { texto: 'satélite', troca: 'repetir' })
})

test('memória da conversa: a última cidade citada; rio não é cidade; duas cidades não valem', () => {
  assert.equal(cidadeCitada('como está Blumenau?', nomes), 'blumenau')
  assert.equal(cidadeCitada('quanto falta para a cota em Rio do Sul?', nomes), 'rio-do-sul')
  assert.equal(cidadeCitada('mostrar o Itajaí-Açu', nomes), null, 'o rio não é a cidade de Itajaí')
  assert.equal(cidadeCitada('mostrar Itajaí', nomes), 'itajai')
  assert.equal(cidadeCitada('como estão Blumenau e Gaspar?', nomes), null)
  assert.deepEqual(memoriaDaConversa(['como está Blumenau?', 'quais cidades estão em alerta?', 'como está Gaspar?', 'e a tendência?'], nomes), { cidade: 'gaspar', ultimoPedido: 'e a tendência?' })
  // A tela vence a conversa; sem tela, a conversa entra como `cidadeDaConversa`.
  assert.deepEqual(contextoComConversa(fora, { cidade: 'gaspar', ultimoPedido: null }), { ...fora, cidadeDaConversa: 'gaspar' })
  assert.deepEqual(contextoComConversa(monitorBlumenau, { cidade: 'gaspar', ultimoPedido: null }), { ...monitorBlumenau, cidadeDaConversa: null })
})

test('decisão da continuação: refazer o que responde; CONFIRMAR o que mudaria a tela; perguntar sem como trocar', () => {
  const m1 = memoriaDaConversa(['mostrar Blumenau'], nomes)
  const d1 = decidirContinuacao('e Gaspar?', m1, nomes, cat, contextoComConversa(monitorBlumenau, m1))
  assert.ok(d1 && d1.tipo === 'confirmar' && d1.texto === 'mostrar Gaspar' && d1.sugestoes[0] === 'mostrar Gaspar' && /nada foi feito/i.test(d1.pergunta), JSON.stringify(d1))
  const m2 = memoriaDaConversa(['como está Gaspar?'], nomes)
  assert.deepEqual(decidirContinuacao('e Blumenau?', m2, nomes, cat, contextoComConversa(fora, m2)), { tipo: 'refazer', texto: 'como está Blumenau?', troca: 'cidade' })
  const m3 = memoriaDaConversa(['copiar resumo de Blumenau'], nomes)
  assert.deepEqual(decidirContinuacao('e Gaspar?', m3, nomes, cat, contextoComConversa(fora, m3)), { tipo: 'refazer', texto: 'copiar resumo de Gaspar', troca: 'cidade' })
  const m4 = memoriaDaConversa(['como estão Blumenau e Gaspar?'], nomes)
  assert.equal(decidirContinuacao('e Brusque?', m4, nomes, cat, contextoComConversa(fora, m4))?.tipo, 'perguntar')
  assert.equal(decidirContinuacao('quanto falta para a cota?', m2, nomes, cat, contextoComConversa(fora, m2)), null, 'não é continuação: segue o caminho normal')
})

test('leitor: "e a tendência?" continua o assunto; "ontem"/"hoje" entram no passo de linha do tempo', () => {
  const ctx = { ...fora, cidadeDaConversa: 'blumenau' }
  assert.deepEqual(interpretar('e a tendência?', cat, ctx), { tipo: 'comandos', passos: [{ tipo: 'tendencia' }] })
  assert.deepEqual(interpretar('e quanto falta?', cat, ctx), { tipo: 'comandos', passos: [{ tipo: 'quanto_falta' }] })
  assert.equal(interpretar('e Gaspar?', cat, ctx), null, '"e Gaspar?" é continuação, não pedido: segue para a conversa')
  assert.deepEqual(interpretar('quando Blumenau passou da cota de alerta ontem?', cat, fora), { tipo: 'comandos', passos: [{ tipo: 'linha_do_tempo', pergunta: 'cruzou_cota', cota: 'alerta', dia: 'ontem', cidadeId: 'blumenau' }] })
  assert.deepEqual(interpretar('quando o rio passou da cota hoje em Blumenau?', cat, fora), { tipo: 'comandos', passos: [{ tipo: 'linha_do_tempo', pergunta: 'cruzou_cota', dia: 'hoje', cidadeId: 'blumenau' }] })
})

test('executor: sem cidade na tela, a da conversa responde e a resposta diz que foi ela; a tela vence a conversa', async () => {
  const ajuda = () => textoDeAjuda(fora, null)
  const ctx = { ...fora, cidadeDaConversa: 'blumenau' }
  const r = interpretar('quanto falta para a cota?', cat, ctx)!
  assert.equal(r.tipo, 'comandos')
  const s = await executar(r.passos, CENARIOS.fresca().amb, cat, ctx, ajuda)
  assert.match(s.texto, /^Pela conversa, entendi que é de Blumenau\.\n\nRégua de Blumenau: 6,50 m/)
  // Cidade dita: sem a nota.
  const r2 = interpretar('quanto falta para a cota em Gaspar?', cat, ctx)!
  assert.equal(r2.tipo, 'comandos')
  assert.doesNotMatch((await executar(r2.passos, CENARIOS.fresca().amb, cat, ctx, ajuda)).texto, /Pela conversa/)
  // Panorama não tem cidade: sem a nota.
  const r3 = interpretar('quais cidades estão em alerta?', cat, ctx)!
  assert.equal(r3.tipo, 'comandos')
  assert.doesNotMatch((await executar(r3.passos, CENARIOS.fresca().amb, cat, ctx, ajuda)).texto, /Pela conversa/)
})

test('linha do tempo por dia: o dia em Brasília, o que o rio fez nele, e fora da janela diz isso', () => {
  // AGORA = 06/10 15h00 em Brasília. Sobe 25 cm/h desde 12 h atrás: cruza 6,00 m hoje, de manhã… ajustado pela série.
  const subindo = serie(24, (h) => (h >= 12 ? 3.5 : 3.5 + (12 - h + 1 / 6) * 0.25))
  const base = { pergunta: 'cruzou_cota' as const, cidade: blumenau, rotulo: 'Blumenau', pontos: subindo, publicacao: null, agora: AGORA, janelaHoras: 48, cota: 'alerta' }
  assert.equal(chaveDoDiaDito('hoje', AGORA), '2026-10-06')
  assert.equal(chaveDoDiaDito('ontem', AGORA), '2026-10-05')
  assert.match(textoLinhaDoTempo({ ...base, dia: 'hoje' }), /^Régua de Blumenau, hoje \(06\/10\), cota de Alerta \(6,00 m\): passou da cota às 12:50 de 06\/10 \(de 5,94 m para 6,00 m\)/)
  assert.match(textoLinhaDoTempo({ ...base, dia: 'ontem' }), /^Nas medições publicadas de ontem \(05\/10\), a régua de Blumenau não passou da cota de Alerta \(6,00 m\): ficou entre 3,50 m e 3,50 m\./)
  assert.match(textoLinhaDoTempo({ ...base, dia: 'anteontem' }), /não cobre anteontem \(04\/10\)/)
  for (const d of ['hoje', 'ontem', 'anteontem'] as const) assert.match(textoLinhaDoTempo({ ...base, dia: d }), /não previsão[^]*199/)
})
