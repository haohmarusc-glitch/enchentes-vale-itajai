import assert from 'node:assert/strict'
import { test } from 'node:test'
import { TEXTO_ALERTA, dataBR, extrair, responder } from './motor'
import { dados } from './testes/carregar'

const r = (p: string) => responder(p, dados)

test('datas em formato brasileiro', () => {
  assert.equal(dataBR('2023-10-13'), '13/10/2023')
  assert.equal(dataBR('1983-07'), 'julho de 1983')
})

test('extrai cidade composta, rio e ano', () => {
  const e = extrair('cheias de rio do sul em 2011 no itajaí-açu', dados)
  assert.equal(e.cidade?.id, 'rio-do-sul')
  assert.equal(e.rio, 'itajai-acu')
  assert.equal(e.ano, 2011)
  // "itajai" do nome do rio não vira cidade
  assert.equal(extrair('maior cheia do itajaí mirim', dados).cidade, undefined)
})

test('maior cheia de Rio do Sul', () => {
  const x = r('Qual foi a maior cheia de Rio do Sul?')
  assert.equal(x.intencao, 'maiores_cheias')
  assert.match(x.texto, /13,58 m/)
  assert.match(x.texto, /julho de 1983/)
})

test('contagem acima de nível', () => assert.match(r('Quantas cheias passaram de 10 m em Rio do Sul?').texto, /14 pico/))

test('cidade sem dados diz que não tem', () => {
  const x = r('qual a maior cheia de Guabiruba?')
  assert.match(x.texto, /não tem o nível do rio/)
  assert.doesNotMatch(x.texto, /\d+,\d+ m/)
})

test('Itajaí sem pico: diz por quê e responde pelo impacto do Atlas, sem metro', () => {
  const x = r('qual maior cheia de itajai ?')
  assert.equal(x.intencao, 'maiores_cheias')
  assert.match(x.texto, /onze réguas/)
  assert.match(x.texto, /23\/11\/2008.*18\.208 desabrigados/)
  assert.match(x.texto, /09\/09\/2011/)
  assert.match(x.texto, /não a altura do rio/)
  assert.doesNotMatch(x.texto, /\d+,\d+ m\b/)
})

test('chuva de 2008 mostra sensor sem dado em vez de zero', () => {
  const x = r('Quanto choveu antes da enchente de novembro de 2008?')
  assert.match(x.texto, /141,2 mm/)
  assert.match(x.texto, /Sem dado válido.*Rio do Campo/)
})

test('chuva em cidade sem estação avisa', () => assert.match(r('quanto choveu em Brusque em 2011').texto, /Não há estação do INMET em Brusque/))

test('tempo de trânsito com fonte', () => assert.match(r('Quanto tempo a cheia leva de Rio do Sul até Blumenau?').texto, /de 7 a 10 h/))

test('trânsito inexistente não soma trechos', () => assert.match(r('quanto tempo leva de Taió até Itajaí?').texto, /não tem tempo de trânsito/))

test('cota ANA vem com aviso de régua', () => {
  const x = r('Cota da ANA em Brusque em novembro de 2008')
  assert.match(x.texto, /507 cm/)
  assert.match(x.texto, /não a régua da Defesa Civil/)
})

test('cota ANA antes de as cotas chegarem diz que está carregando, nunca um número', () => {
  const { cotasAna: _fora, ...semCotas } = dados
  const x = responder('Cota da ANA em Brusque em novembro de 2008', semCotas)
  assert.match(x.texto, /carregando/)
  assert.doesNotMatch(x.texto, /\d+ cm/)
})

test('atlas por mês', () => assert.match(r('Quais cidades tiveram desastre em setembro de 2011?').texto, /Blumenau — 11\/09\/2011/))

test('perguntas de agora recebem o texto fixo', () => {
  for (const p of ['vai encher hoje?', 'Devo sair de casa?', 'tá subindo em gaspar?', 'qual a previsão para amanhã']) assert.equal(r(p).texto, TEXTO_ALERTA, p)
})

test('fora do tema não inventa', () => {
  const x = r('me conta uma piada')
  assert.equal(x.intencao, 'nao_entendi')
  assert.ok(x.sugestoes?.length)
})

test('Rio do Sul 2018: o mês duvidoso sai com a confiança baixa e a nota (decisão de 22/09/2026)', () => {
  const x = r('cheias de Rio do Sul em 2018')
  assert.match(x.texto, /7,55 m/)
  assert.match(x.texto, /confiança BAIXA/)
  assert.match(x.texto, /MÊS DUVIDOSO/)
})

test('pico da série da ANA diz que é a régua da ANA, não a local (24/09/2026)', () => {
  const x = r('maior cheia de Ilhota')
  assert.match(x.texto, /10,45 m/)
  assert.match(x.texto, /régua da ANA, que tem zero próprio/)
  assert.doesNotMatch(x.texto, /na régua local/)
})
