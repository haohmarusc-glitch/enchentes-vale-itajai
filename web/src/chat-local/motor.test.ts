import assert from 'node:assert/strict'
import { test } from 'node:test'
import { TEXTO_ALERTA, citaRua, dataBR, escalaDoPico, extrair, responder, termoDaRua } from './motor'
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

test('Itajaí: lista os picos por estação e não elege a maior (tese da UEM, 25/09/2026)', () => {
  const x = r('qual maior cheia de itajai ?')
  assert.equal(x.intencao, 'maiores_cheias')
  assert.match(x.texto, /onze réguas/)
  assert.match(x.texto, /09\/09\/2011, Rio Itajaí-Açu: 3,2 m/)
  assert.match(x.texto, /09\/09\/2011, Rio Itajaí-Mirim: 4,29 m/)
  assert.match(x.texto, /não se comparam/)
  assert.doesNotMatch(x.texto, /A maior cheia registrada de Itajaí/)
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

// ---------------------------------------------------------------------------
// 04/10/2026: a contagem não mistura escalas, e o chat responde pela cota da rua.

test('contagem em Blumenau conta só a régua e diz quantos ficaram de fora', () => {
  const x = r('Quantas cheias passaram de 10 m em Blumenau?')
  assert.equal(x.intencao, 'contar_acima')
  assert.match(x.texto, /32 pico\(s\) registrado\(s\) de 10 m ou mais, na régua de Blumenau/)
  assert.match(x.texto, /Fora da conta: 40 pico/)
  assert.match(x.texto, /27 no zero do IBGE/)
  assert.doesNotMatch(x.texto, /72 pico/, 'régua, IBGE e sem referência nunca na mesma soma')
})

test('Brusque: picos anteriores a 2019 ficam fora da régua declarada (opção B)', () => {
  const x = r('Quantas cheias passaram de 7 m em Brusque?')
  assert.match(x.texto, /3 pico\(s\) registrado\(s\) de 7 m ou mais, na régua de Brusque/)
  assert.match(x.texto, /antes do trecho que a cidade declara na régua/)
})

test('Rio do Sul: uma escala só, sem régua declarada — conta e diz que não compara com hoje', () => {
  const x = r('Quantas cheias passaram de 10 m em Rio do Sul?')
  assert.match(x.texto, /sem referência declarada pela fonte — não compare com o nível de hoje/)
})

test('Itajaí, várias réguas: não conta', () => {
  const x = r('Quantas cheias passaram de 2 m em Itajaí?')
  assert.match(x.texto, /não conta quantas cheias/)
  assert.doesNotMatch(x.texto, /pico\(s\) registrado/)
})

test('escala de cada pico', () => {
  const base = { cidade: 'x', data: '2000-01-01', pico_m: 1, confianca: 'alta', fonte: 'Defesa Civil' }
  assert.equal(escalaDoPico({ ...base }, dados), 'regua')
  assert.equal(escalaDoPico({ ...base, referencia: 'régua' }, dados), 'regua')
  assert.equal(escalaDoPico({ ...base, referencia: null }, dados), 'nao-declarada')
  assert.equal(escalaDoPico({ ...base, referencia: 'IBGE (régua + 0,20 m)' }, dados), 'ibge')
  assert.equal(escalaDoPico({ ...base, fonte: 'ANA/HidroWeb, estação 1' }, dados), 'ana')
  assert.equal(escalaDoPico({ ...base, cidade: 'brusque', data: '2011-09' }, dados), 'antes-da-regua')
  assert.equal(escalaDoPico({ ...base, cidade: 'brusque', data: '2023-11-17' }, dados), 'regua')
})

test('rua: conta as cheias na régua que chegaram à cota, com a ressalva', () => {
  const x = r('Quantas cheias passaram da cota da Rua São Rafael em Blumenau?')
  assert.equal(x.intencao, 'rua_historico')
  assert.match(x.texto, /Rua São Rafael \(final da rua\), Itoupava Norte: cota 7,4 m\. O rio chegou a essa cota em \d+ das 58 cheias registradas na régua de Blumenau/)
  assert.match(x.texto, /NÃO quer dizer que a rua alagou todas essas vezes/)
  assert.doesNotMatch(x.texto, /alagou \d+ vezes/)
})

test('rua: casamento pela palavra inteira vence o de pedaço', () => {
  const x = r('a rua Lino em Gaspar ja alagou quantas vezes?')
  assert.match(x.texto, /Rua Lino: cota 6,57 m/)
  assert.doesNotMatch(x.texto, /Wandelino/)
  assert.match(x.texto, /só traz as cheias grandes/, 'Gaspar: lista esparsa')
})

test('rua em cidade sem pico na régua não conta', () => {
  const x = r('quantas cheias pegaram a rua XV de novembro em Rio do Sul')
  assert.match(x.texto, /não dá para contar/)
})

test('rua sem cidade pede a cidade; sem cotas carregadas diz que está carregando', () => {
  const sem = r('quantas cheias passaram da cota da rua São Rafael?')
  assert.equal(sem.falha?.motivo, 'faltou_cidade')
  const carregando = responder('quantas cheias passaram da cota da Rua São Rafael em Blumenau?', { ...dados, cotasRuas: undefined })
  assert.match(carregando.texto, /carregando/)
})

test('rua que não está na lista não vira "não alaga"', () => {
  assert.match(r('rua coelho neto em brusque alagou quantas vezes').texto, /não quer dizer que ela não alaga/)
})

test('"a minha rua vai alagar?" continua indo para a Defesa Civil', () => {
  assert.equal(r('a minha rua vai alagar?').texto, TEXTO_ALERTA)
})

test('extração do nome da rua', () => {
  assert.equal(citaRua('Quantas cheias passaram da cota da Rua São Rafael em Blumenau?'), true)
  assert.equal(citaRua('Qual foi a maior cheia de Rio do Sul?'), false)
  assert.equal(termoDaRua(extrair('Quantas cheias passaram da cota da Rua São Rafael em Blumenau?', dados)), 'sao rafael')
  assert.equal(termoDaRua(extrair('a rua Lino em Gaspar ja alagou quantas vezes?', dados)), 'lino')
})
