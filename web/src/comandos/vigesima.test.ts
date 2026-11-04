/**
 * 20ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): os avisos meteorológicos da Defesa Civil de SC,
 * por região — nunca por cidade, nunca faixa do rio; pedido de contato com a Defesa Civil não é consulta.
 */
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { executar, limparRetratos } from './executar'
import { textoDeAjuda } from './ajuda'
import { textoAvisosDcsc } from './avisosDcsc'
import { AGORA, AVISOS_DCSC, CENARIOS, estacoes } from './avaliacao/cenarios'
import type { Contexto } from './tipos'

const cat = catalogoDoCadastro(estacoes)
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const paginaBlumenau: Contexto = { cidadeAtual: 'blumenau', naMonitor: false, reguaAtual: null }
const ajuda = () => textoDeAjuda(fora, null)

beforeEach(() => limparRetratos())

test('o leitor: as formas de perguntar pelo aviso viram o passo, sem cidade', () => {
  for (const frase of [
    'tem aviso da Defesa Civil?', 'tem algum alerta da Defesa Civil de SC hoje?', 'avisos da Defesa Civil', 'tem alerta de chuva?',
    'tem aviso de temporal para a região?', 'aviso meteorológico', 'a Defesa Civil emitiu alerta?', 'o que a Defesa Civil está avisando?',
    'qual é o último aviso da Defesa Civil?', 'saiu aviso da Defesa Civil de Santa Catarina?', 'tem alerta da dc?', 'alerta estadual de chuva',
  ]) {
    assert.deepEqual(interpretar(frase, cat, fora), { tipo: 'comandos', passos: [{ tipo: 'avisos_dcsc' }] }, frase)
  }
})

test('o leitor não rouba o que já existia: alerta do rio, aviso do site, "tem alerta?" sozinho', () => {
  assert.deepEqual(interpretar('quais cidades estão em alerta?', cat, fora), { tipo: 'comandos', passos: [{ tipo: 'panorama' }] })
  assert.deepEqual(interpretar('ler o aviso legal', cat, fora), { tipo: 'comandos', passos: [{ tipo: 'oficial' }] })
  const soAlerta = interpretar('tem alerta?', cat, fora)
  assert.ok(!soAlerta || soAlerta.tipo !== 'comandos' || soAlerta.passos.every((p) => p.tipo !== 'avisos_dcsc'), '"tem alerta?" não decide sozinho que é o da Defesa Civil')
})

test('contato com a Defesa Civil: ligar vira o telefone de emergência; avisar/acionar diz que o chat não fala com ninguém', () => {
  assert.deepEqual(interpretar('ligar para a Defesa Civil', cat, fora), { tipo: 'comandos', passos: [{ tipo: 'emergencia' }] })
  for (const frase of ['avisar a Defesa Civil que o rio subiu', 'acionar a defesa civil', 'chamar a Defesa Civil em Gaspar']) {
    const r = interpretar(frase, cat, fora)
    assert.equal(r?.tipo, 'esclarecer', frase)
    if (r?.tipo === 'esclarecer') {
      assert.match(r.texto, /não fala com a Defesa Civil nem com ninguém/)
      assert.match(r.texto, /199/)
    }
  }
})

test('o texto: por região, com hora de Brasília, idade, link, fonte e a ressalva; nunca "para a sua cidade"', () => {
  const t = textoAvisosDcsc(AVISOS_DCSC, AGORA)
  assert.match(t, /^Um aviso recente da Defesa Civil de SC para a região\./)
  assert.match(t, /• ATENÇÃO – 06\/10 14:34 – TEMPORAIS\n {2}Alerta · 06\/10 às 14:34 \(Brasília\), há 26 min · Vale do Itajaí, Litoral Norte\n {2}https:\/\/www\.defesacivil\.sc\.gov\.br\/atencao-06-10-1434-temporais\//)
  assert.match(t, /Há um aviso recente para outras regiões do Estado\./, 'o do Oeste conta, não lista')
  assert.doesNotMatch(t, /CHUVA NO OESTE|03\/10/, 'nem o de outra região nem o de mais de 24 h aparecem')
  assert.match(t, /Fonte: Defesa Civil de Santa Catarina — www\.defesacivil\.sc\.gov\.br/)
  assert.match(t, /não para uma cidade, e não é a faixa do rio/)
  assert.match(t, /ligue 199/)
  assert.doesNotMatch(t, /para a sua cidade|Blumenau|Gaspar/)
})

test('sem arquivo: "indisponíveis", com a fonte padrão e o 199; aviso de mais de 24 h diz quando foi o último', () => {
  const t = textoAvisosDcsc(null, AGORA)
  assert.match(t, /^Avisos indisponíveis\. Não há publicação recente da Defesa Civil de SC lida pelo site\. Confira direto no site dela\./)
  assert.match(t, /Fonte: Defesa Civil de Santa Catarina \(www\.defesacivil\.sc\.gov\.br\)\./)
  const umDiaDepois = new Date(AGORA.getTime() + 25 * 60 * 60_000)
  const arquivoFresco = { ...AVISOS_DCSC, geradoEm: new Date(umDiaDepois.getTime() - 60_000) }
  const t2 = textoAvisosDcsc(arquivoFresco, umDiaDepois)
  assert.match(t2, /^Nenhum aviso recente para a região\. O último que citou uma região da bacia foi em 06\/10 às 14:34 \(Brasília\): “ATENÇÃO – 06\/10 14:34 – TEMPORAIS”\./)
})

test('o executor: o relógio é o das leituras; o link vai para as fontes da cidade da tela, senão para o site da DCSC', async () => {
  const fresca = CENARIOS.fresca()
  const semCidade = await executar([{ tipo: 'avisos_dcsc' }], fresca.amb, cat, fora, ajuda)
  assert.match(semCidade.texto, /Um aviso recente da Defesa Civil de SC para a região/)
  assert.equal(semCidade.link?.para, 'https://www.defesacivil.sc.gov.br/wp-json/wp/v2/posts?categories=7,6')
  const naPagina = await executar([{ tipo: 'avisos_dcsc' }], CENARIOS.fresca().amb, cat, paginaBlumenau, ajuda)
  assert.deepEqual(naPagina.link, { texto: 'Abrir as fontes de Blumenau →', para: '/acu/blumenau?aba=fontes' })
  assert.doesNotMatch(naPagina.texto, /Blumenau/, 'a cidade da tela só decide o link; o texto continua por região')
  assert.deepEqual(fresca.navegacoes, [], 'não muda a tela')
  const semDados = await executar([{ tipo: 'avisos_dcsc' }], CENARIOS.semDados().amb, cat, fora, ajuda)
  assert.match(semDados.texto, /^Avisos indisponíveis/)
})

test('a ajuda lista o pedido, dentro e fora do Monitor', () => {
  assert.match(textoDeAjuda(fora, null).texto, /"tem aviso da Defesa Civil\?", "tem alerta de chuva\?"/)
  assert.match(textoDeAjuda({ cidadeAtual: 'blumenau', naMonitor: true, reguaAtual: null }, 'Blumenau').texto, /"tem aviso da Defesa Civil\?"/)
})
