import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
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

// Todo par de cidades do site (pedido do Jefferson, 04/10/2026): o chat dá o MESMO tempo
// que a tela e o bot — o gabarito `data/transito-esperado.json`, que os dois já seguem —
// e, onde o gabarito diz que não há tempo, explica o porquê sem dar número do par.
const GABARITO = JSON.parse(readFileSync(fileURLToPath(new URL('../../../data/transito-esperado.json', import.meta.url)), 'utf-8')) as {
  caminhos: { rio: string; de: string; para: string; resultado: { horas_min: number; horas_max: number } | null }[]
}
const NOMES = new Map(Object.values(dados.estacoes.rios).flatMap((rr) => rr.cidades.map((c) => [c.id, c.nome] as const)))
const faixa = (a: number, b: number) => {
  const f = (h: number) => h.toLocaleString('pt-BR', { maximumFractionDigits: 1 })
  return a === b ? `cerca de ${f(a)} h` : `de ${f(a)} a ${f(b)} h`
}

test('trânsito: todo par com tempo no gabarito sai com a mesma faixa, nas duas ordens da pergunta', () => {
  const com = GABARITO.caminhos.filter((c) => c.resultado)
  assert.ok(com.length >= 20)
  for (const c of com) {
    const [de, para] = [NOMES.get(c.de)!, NOMES.get(c.para)!]
    const esperado = `Da passagem do pico em ${de} até ${para}: ${faixa(c.resultado!.horas_min, c.resultado!.horas_max)}`
    const ida = r(`Quanto tempo a cheia leva de ${de} até ${para}?`)
    assert.equal(ida.intencao, 'transito', `${de} → ${para}`)
    assert.ok(ida.texto.includes(esperado), `${de} → ${para}: ${ida.texto}`)
    const volta = r(`Quanto tempo de ${para} até ${de}?`)
    assert.ok(volta.texto.startsWith(`A cheia desce de ${de} para ${para}, não o contrário.`) && volta.texto.includes(esperado), `${para} → ${de}: ${volta.texto}`)
  }
})

test('trânsito: par sem tempo no gabarito explica e não inventa número do par', () => {
  const sem = GABARITO.caminhos.filter((c) => !c.resultado)
  const comTempo = new Set(GABARITO.caminhos.filter((c) => c.resultado).map((c) => `${c.de}>${c.para}`))
  assert.ok(sem.length > 100)
  for (const c of sem) {
    if (comTempo.has(`${c.para}>${c.de}`)) continue // a ordem contrária tem tempo: coberto acima
    const [de, para] = [NOMES.get(c.de)!, NOMES.get(c.para)!]
    const x = r(`Quanto tempo a cheia leva de ${de} até ${para}?`)
    assert.equal(x.intencao, 'transito', `${de} → ${para}`)
    assert.ok(!x.texto.includes(`Da passagem do pico em ${de} até ${para}`), `${de} → ${para} ganhou número: ${x.texto}`)
    assert.ok(!x.texto.includes(`Da passagem do pico em ${para} até ${de}`), `${para} → ${de} ganhou número: ${x.texto}`)
    assert.ok(x.texto.length > 60, `${de} → ${para}: explicação curta demais`)
  }
})

test('trânsito: os porquês', () => {
  assert.match(r('quanto tempo de Brusque até Blumenau?').texto, /rios diferentes/)
  assert.match(r('quanto tempo de Timbó até Blumenau?').texto, /afluente/)
  assert.match(r('quanto tempo de Taió até Ituporanga?').texto, /rios paralelos/)
  assert.match(r('quanto tempo de Vidal Ramos até Itajaí?').texto, /em estudo.*dados insuficientes[\s\S]*Brusque até Itajaí, cerca de 6 h/)
  assert.match(r('quanto tempo de Lontras até Blumenau?').texto, /não tem o tempo medido[\s\S]*de Rio do Sul até Blumenau: de 7 a 10 h/)
  assert.match(r('quanto tempo de Trombudo Central até Blumenau?').texto, /posição definida/)
  assert.match(r('Quanto tempo a cheia leva de Taió até Itajaí?').texto, /de 25 a 35 h[\s\S]*Soma dos trechos/)
  assert.match(r('quanto tempo até Blumenau?').texto, /Diga as duas cidades/)
})

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

// Achados da prova do chat com IA (04/10/2026): "essa madrugada" e "como está o rio"
// passavam pela barreira; "alerta" sozinho barrava pergunta sobre a cota de alerta.
test('barreira: madrugada, "como está o rio" e alerta de AGORA', () => {
  for (const p of [
    'A água chega na minha casa no bairro Garcia essa madrugada?',
    'O rio vai subir daqui a pouco?',
    'Como está o rio em Rio do Sul?',
    'como estão os rios?',
    'Tem alerta em Blumenau?',
    'Blumenau está em alerta?',
    'Saiu alerta para Gaspar?',
    'tem algum alerta vigente?',
  ])
    assert.equal(r(p).texto, TEXTO_ALERTA, p)
})

test('barreira: a cota de alerta NÃO é pergunta sobre agora', () => {
  for (const p of [
    'Qual é a cota de alerta do rio em Blumenau?',
    'A partir de quantos metros é alerta em Ilhota?',
    'Qual o nível de alerta de Rio do Sul?',
  ])
    assert.equal(r(p).intencao, 'cotas', p)
})

test('cotas da Defesa Civil: escada na régua da cidade, com o nome local', () => {
  const b = r('Qual é a cota de alerta do rio em Blumenau?').texto
  for (const linha of ['Observação: a partir de 3 m', 'Atenção: a partir de 4 m', 'Alerta: a partir de 6 m', 'Alerta Máximo: a partir de 8 m']) assert.ok(b.includes(linha), linha)
  assert.match(b, /não se comparam com os de outra cidade/)
  assert.doesNotMatch(b, /não foram conferidas/) // Blumenau: cotas_verificado true

  const ilhota = r('A partir de quantos metros é alerta em Ilhota?').texto
  assert.ok(ilhota.includes('Prontidão: a partir de 10 m'), ilhota) // D6: o nome da Defesa Civil de Ilhota
  assert.match(ilhota, /não foram conferidas/)

  assert.match(r('Quais são as cotas da Defesa Civil para o rio em Gaspar?').texto, /Atenção: acima de 5 m[\s\S]*Emergência: acima de 7 m/) // legenda "maior que"
  assert.match(r('Qual a cota de alerta de Itajaí?').texto, /onze réguas/)
  // Timbó: só gatilho do plano, sem escada — não vira faixa.
  const timbo = r('Qual a cota de alerta de Timbó?').texto
  assert.match(timbo, /não tem cotas de faixa/)
  assert.doesNotMatch(timbo, /• /)
  assert.match(r('Qual a cota de alerta de Pomerode?').texto, /Não achei a cidade[\s\S]*Blumenau/)
})

test('cotas não roubam outras intenções', () => {
  assert.equal(r('Quantas cheias passaram de 10 m em Rio do Sul?').intencao, 'contar_acima')
  assert.equal(r('Cota da ANA em Brusque em novembro de 2008').intencao, 'cota_ana')
  assert.equal(r('Quantas cheias chegaram à cota da Rua São Rafael em Blumenau?').intencao, 'rua_historico')
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
