/**
 * Trava da prova do chat com IA (não chama a API):
 *  1. o oráculo de cada caso passa no corretor; resposta vazia ou "não sei" reprova;
 *  2. resposta errada mas plausível reprova (o corretor não é frouxo);
 *  3. o gabarito vem dos DADOS: cada fato confere com o motor do chat local, que lê
 *     os mesmos JSONs, ou com uma conta feita aqui sobre eles;
 *  4. nenhuma pergunta cai na barreira do presente (senão a IA nem seria chamada).
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { dados } from '../../chat-local/testes/carregar'
import { escalaDoPico, pedeAgora, responder } from '../../chat-local/motor'
import { CASOS } from './casos'
import { corrigir, normalizar } from './corrigir'

const caso = (id: string) => {
  const c = CASOS.find((x) => x.id === id)
  assert.ok(c, id)
  return c
}

test('ids únicos e perguntas que chegam à IA', () => {
  assert.equal(new Set(CASOS.map((c) => c.id)).size, CASOS.length)
  assert.ok(CASOS.length >= 30, `${CASOS.length} casos`)
  for (const c of CASOS) assert.equal(pedeAgora(c.pergunta), false, `${c.id} cai na barreira do presente`)
})

test('oráculo passa; vazio e "não sei" reprovam', () => {
  for (const c of CASOS) {
    assert.deepEqual(corrigir(c, c.oraculo).grade, { acerto: 1, fatos: 1, regras: 1 }, `${c.id}: ${corrigir(c, c.oraculo).explanation.acerto}`)
    assert.equal(corrigir(c, '').grade.acerto, 0, `${c.id} aceita vazio`)
    assert.equal(corrigir(c, 'Não sei.').grade.acerto, 0, `${c.id} aceita "não sei"`)
  }
})

test('resposta constante passa só onde deve (piso da prova)', () => {
  // "Ligue 199" acerta as perguntas sobre o presente e mais nada.
  const passa = CASOS.filter((c) => corrigir(c, 'Ligue 199 para a Defesa Civil.').grade.acerto).map((c) => c.id)
  assert.deepEqual(passa.sort(), ['acao-carro', 'agora-como-esta', 'agora-madrugada'])
})

test('errado mas plausível reprova', () => {
  const errados: [string, string][] = [
    ['recorde-blumenau', 'A maior cheia de Blumenau foi de 17,1 m em 1911.'],
    ['recorde-itajai', 'A maior enchente da história de Itajaí foi em 2008, quando o rio chegou a 4 m.'],
    ['conta-blumenau-12m', 'Na régua, foram 16 cheias acima de 12 m em Blumenau.'],
    ['conta-itajai-3m', 'Em Itajaí, o rio passou de 3 m 2 vezes, nas onze réguas.'],
    ['compara-2008', 'Cada cidade tem a sua régua, mas a enchente foi maior em Blumenau.'],
    ['transito-taio-itajai', 'A água leva cerca de 30 h de Taió até Itajaí.'],
    ['transito-em-estudo', 'O trecho está em estudo, mas leva de 6 a 8 h.'],
    ['rua-inexistente', 'Não sei ao certo; a Rua Inventada da Silva alaga com 6,5 m.'],
    ['atlas-mortos-1880', 'O site não tem o dado exato, mas foram 50 mortos.'],
    ['agora-madrugada', 'Sim, a água deve chegar de madrugada; ligue 199.'],
    ['acao-carro', 'Sim, tire o carro. Ligue 199 se precisar.'],
    ['fora-do-tema', 'É Florianópolis. Eu respondo sobre cheias.'],
    ['cidade-sem-regua', 'Pomerode não tem régua no site, mas a maior cheia lá chegou a 9 m.'],
    ['conta-media', 'A média dos picos de Blumenau desde 2000 é 10,2 m.'],
  ]
  for (const [id, texto] of errados) assert.equal(corrigir(caso(id), texto).grade.acerto, 0, `${id} aceitou: ${texto}`)
})

test('normalização: acento, caixa e vírgula decimal', () => {
  assert.equal(normalizar('Régua: 17,30 M  em  Itajaí'), 'regua: 17.30 m em itajai')
})

// O motor do chat local responde a partir dos JSONs: se o gabarito e o motor
// concordam, o número da prova é o número do site.
const PELO_MOTOR: Record<string, string> = {
  'recorde-blumenau': 'Qual foi a maior cheia de Blumenau?',
  'recorde-rio-do-sul': 'Qual foi a maior cheia de Rio do Sul?',
  'recorde-gaspar': 'Qual foi a maior cheia de Gaspar?',
  'recorde-brusque': 'Qual foi a maior cheia de Brusque?',
  'recorde-itajai': 'Qual foi a maior cheia de Itajaí?',
  'evento-blumenau-2011': 'Cheias de Blumenau em 2011',
  'evento-rio-do-sul-1983': 'Cheias de Rio do Sul em 1983',
  'evento-gaspar-2008': 'Cheias de Gaspar em 2008',
  'evento-brusque-2011': 'Cheias de Brusque em 2011',
  'conta-rio-do-sul-10m': 'Quantas cheias passaram de 10 m em Rio do Sul?',
  'conta-blumenau-12m': 'Quantas cheias passaram de 12 m em Blumenau?',
  'conta-itajai-3m': 'Quantas cheias passaram de 3 m em Itajaí?',
  'transito-taio-itajai': 'Quanto tempo a cheia leva de Taió até Itajaí?',
  'transito-invertido': 'Quanto tempo a cheia leva de Blumenau até Rio do Sul?',
  'transito-lontras': 'Quanto tempo a cheia leva de Lontras até Blumenau?',
  'transito-rios-diferentes': 'Quanto tempo a cheia leva de Brusque até Blumenau?',
  'transito-em-estudo': 'Quanto tempo a cheia leva de Vidal Ramos até Brusque?',
  'rua-sao-rafael': 'Quantas cheias chegaram à cota da Rua São Rafael em Blumenau?',
  'atlas-blumenau-2008': 'Quantos desabrigados em Blumenau em novembro de 2008?',
  'atlas-setembro-2011': 'Quais cidades tiveram desastre em setembro de 2011?',
  'chuva-2008': 'Quanto choveu antes da enchente de novembro de 2008?',
}

test('gabarito confere com o motor do site', () => {
  for (const [id, pergunta] of Object.entries(PELO_MOTOR)) {
    const c = caso(id)
    const r = corrigir({ ...c, nao_deve: [] }, responder(pergunta, dados).texto)
    assert.equal(r.grade.fatos, 1, `${id}: o motor diz outra coisa — ${r.explanation.acerto}`)
  }
})

test('gabarito das contas livres e das cotas confere com os JSONs', () => {
  const bl = dados.enchentes.eventos.filter((r) => r.cidade === 'blumenau')
  const regua2000 = bl.filter((r) => r.data >= '2000' && escalaDoPico(r, dados) === 'regua')
  const media = regua2000.reduce((s, r) => s + r.pico_m, 0) / regua2000.length
  assert.ok(corrigir(caso('conta-media'), `média de ${media.toFixed(2).replace('.', ',')} m`).grade.fatos, `média ${media}`)
  const anos80 = bl.filter((r) => r.data >= '1980' && r.data < '1990').length
  assert.ok(corrigir(caso('conta-decada'), `${anos80} picos`).grade.fatos, `década de 1980: ${anos80}`)

  const cidade = (id: string) => Object.values(dados.estacoes.rios).flatMap((r) => r.cidades).find((c) => c.id === id) as unknown as { cotas_m: Record<string, number> }
  const bc = cidade('blumenau').cotas_m
  assert.ok(corrigir(caso('cotas-blumenau'), `alerta ${bc.alerta} m, alerta máximo ${bc.emergencia} m`).grade.fatos, JSON.stringify(bc))
  const ic = cidade('ilhota').cotas_m
  assert.ok(corrigir(caso('cotas-ilhota'), `atenção ${String(ic.atencao).replace('.', ',')} m, prontidão ${ic.alerta} m`).grade.fatos, JSON.stringify(ic))

  // Mortos de 1880: o Atlas não cobre essa época (o "não tem" do gabarito é verdade).
  const anosAtlas = Object.values(dados.atlas).flatMap((a) => a.eventos.map((e) => (e as unknown as { mes?: string }).mes ?? '')).filter(Boolean).sort()
  assert.ok(anosAtlas.length > 0 && anosAtlas[0]! > '1900', `Atlas começa em ${anosAtlas[0]}`)
  // Pomerode não tem régua no site.
  assert.ok(!Object.values(dados.estacoes.rios).some((r) => r.cidades.some((c) => c.id === 'pomerode')))
})
