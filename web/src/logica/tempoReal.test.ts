import assert from 'node:assert/strict'
import { test } from 'node:test'
import type { Cidade, Trecho } from '../dados/tipos'
import {
  faixaDaCidade,
  MIN_AGORA,
  MIN_VELHA,
  chegadasSePicoAgora,
  deBrasilia,
  frescor,
  foraDeOrdem,
  idadeMin,
  cotaAlcancada,
  primeiraCota,
  textoIdade,
} from './tempoReal'

test('horário sem fuso é lido como hora de Brasília', () => {
  // 16:01 em Brasília (UTC-3) é 19:01 UTC.
  assert.equal(deBrasilia('2026-08-30T16:01:00').toISOString(), '2026-08-30T19:01:00.000Z')
})

test('a conversão não depende do fuso de quem abre a página', () => {
  // O valor é um instante absoluto: qualquer aparelho chega ao mesmo número.
  const instante = deBrasilia('2026-08-30T16:01:00').getTime()
  assert.equal(instante, Date.UTC(2026, 7, 30, 19, 1, 0))
})

test('horário inválido não vira data silenciosamente errada', () => {
  assert.ok(Number.isNaN(deBrasilia('ontem').getTime()))
})

test('idade em minutos, sem futuro negativo', () => {
  const medido = new Date('2026-08-30T19:00:00Z')
  assert.equal(idadeMin(medido, new Date('2026-08-30T19:12:00Z')), 12)
  assert.equal(idadeMin(medido, new Date('2026-08-30T18:50:00Z')), 0, 'relógio adiantado não é futuro')
})

test('frescor separa o que serve do que não serve', () => {
  assert.equal(frescor(10), 'agora')
  assert.equal(frescor(MIN_AGORA), 'agora')
  assert.equal(frescor(MIN_AGORA + 1), 'atrasada')
  assert.equal(frescor(MIN_VELHA), 'atrasada')
  assert.equal(frescor(MIN_VELHA + 1), 'velha')
})

test('leitura de uma hora ainda serve — é o ritmo real de algumas fontes', () => {
  // A estação MKS de Rio do Sul publica quase uma hora atrás das DC de Itajaí.
  // Com o limite antigo de 45 min ela ficaria permanentemente indisponível.
  assert.equal(frescor(52), 'agora')
  assert.equal(frescor(60), 'agora')
})

test('texto da idade em português', () => {
  assert.equal(textoIdade(0), 'agora mesmo')
  assert.equal(textoIdade(12), 'há 12 min')
  assert.equal(textoIdade(120), 'há 2 h')
  assert.equal(textoIdade(125), 'há 2 h 05')
  assert.equal(textoIdade(60 * 24), 'há 1 dia')
  assert.equal(textoIdade(60 * 72), 'há 3 dias')
})

const cidade = (id: string, nome: string, ordem: number, cotas: Record<string, number> = {}): Cidade => ({
  id,
  nome,
  ordem,
  codigo_ana: null,
  verificado: false,
  cotas_m: cotas,
  fontes_tempo_real: [],
})

const CIDADES = [
  cidade('rio-do-sul', 'Rio do Sul', 1, { atencao: 4.5, alerta: 5.5, inundacao: 6.5 }),
  cidade('blumenau', 'Blumenau', 2, { inundacao: 7.4, atencao: 6.0 }),
  cidade('gaspar', 'Gaspar', 3),
  cidade('itajai', 'Itajaí', 4),
]

const TRECHOS: Trecho[] = [
  { rio: 'itajai-acu', de: 'rio-do-sul', para: 'blumenau', horas_min: 7, horas_max: 10, confianca: 'alta', fonte: 'JICA' },
  { rio: 'itajai-acu', de: 'blumenau', para: 'itajai', horas_min: 14, horas_max: 17, confianca: 'alta', fonte: 'JICA' },
]

test('chegada a jusante a partir de um pico agora', () => {
  const agora = new Date('2026-08-30T19:00:00Z')
  const chegadas = chegadasSePicoAgora(TRECHOS, 'itajai-acu', CIDADES, CIDADES[0]!, agora)
  assert.equal(chegadas.length, 2, 'Blumenau direto e Itajaí pela soma dos trechos')
  assert.equal(chegadas[0]!.cidade.id, 'blumenau')
  assert.equal(chegadas[0]!.inicio.toISOString(), '2026-08-31T02:00:00.000Z')
  assert.equal(chegadas[0]!.fim.toISOString(), '2026-08-31T05:00:00.000Z')
  assert.equal(chegadas[1]!.cidade.id, 'itajai')
  assert.equal(chegadas[1]!.inicio.toISOString(), '2026-08-31T16:00:00.000Z')
})

test('cidade sem trecho conhecido fica de fora, não vira palpite', () => {
  const chegadas = chegadasSePicoAgora(TRECHOS, 'itajai-acu', CIDADES, CIDADES[0]!, new Date())
  assert.ok(!chegadas.some((c) => c.cidade.id === 'gaspar'))
})

test('a última cidade não tem para onde mandar', () => {
  const chegadas = chegadasSePicoAgora(TRECHOS, 'itajai-acu', CIDADES, CIDADES[3]!, new Date())
  assert.deepEqual(chegadas, [])
})

/*
 * `primeiraCota` responde "a partir de quando é cheia aqui" — a pergunta certa
 * para um painel condicional, e a errada para um nível ao vivo. Com o rio dois
 * patamares acima, anunciar a cota de atenção é a frase mais fraca possível na
 * hora em que se precisa da mais forte.
 */
test('cota alcançada é a mais ALTA já passada', () => {
  const rioDoSul = CIDADES[0]!  // atenção 4,5 · alerta 5,5 · inundação 6,5
  assert.deepEqual(cotaAlcancada(rioDoSul, 7.0), { chave: 'inundacao', valor: 6.5 })
  assert.deepEqual(cotaAlcancada(rioDoSul, 6.5), { chave: 'inundacao', valor: 6.5 },
    'na cota exata já conta como alcançada')
  assert.deepEqual(cotaAlcancada(rioDoSul, 5.6), { chave: 'alerta', valor: 5.5 })
  assert.deepEqual(cotaAlcancada(rioDoSul, 4.5), { chave: 'atencao', valor: 4.5 })
})

test('nível abaixo de tudo não anuncia cota nenhuma', () => {
  assert.equal(cotaAlcancada(CIDADES[0]!, 4.49), null)
  assert.equal(cotaAlcancada(CIDADES[2]!, 99), null, 'cidade sem cota levantada não inventa')
})

test('cota alcançada não depende da ordem em que as cotas foram escritas', () => {
  // Blumenau, no teste, tem `inundacao` ANTES de `atencao` no objeto.
  assert.deepEqual(cotaAlcancada(CIDADES[1]!, 8.0), { chave: 'inundacao', valor: 7.4 })
})

test('primeira cota é a mais baixa que importa', () => {
  assert.deepEqual(primeiraCota(CIDADES[0]!), { chave: 'atencao', valor: 4.5 })
  assert.deepEqual(primeiraCota(CIDADES[1]!), { chave: 'atencao', valor: 6.0 })
  assert.equal(primeiraCota(CIDADES[2]!), null, 'sem cota levantada, sem palpite')
})

test('janela fora da ordem do rio é detectada', () => {
  // A água passa pelas cidades na ordem do curso. Quando os trechos vêm de
  // fontes que não concordam, uma cidade pode aparecer recebendo antes de
  // outra acima dela — e isso tem de ser dito, não arrumado por baixo.
  const chegada = (h: number) =>
    ({ inicio: new Date(2026, 7, 31, h), fim: new Date(2026, 7, 31, h + 3) }) as never

  assert.equal(foraDeOrdem([chegada(1), chegada(2), chegada(5)]), false)
  assert.equal(foraDeOrdem([chegada(2), chegada(1)]), true)
  assert.equal(foraDeOrdem([]), false)
  assert.equal(foraDeOrdem([chegada(4)]), false)
})

test('faixaDaCidade colore pela cota da própria cidade', () => {
  const blumenau = {
    id: 'blumenau', nome: 'Blumenau', ordem: 7,
    cotas_m: { atencao: 6.0, alerta: 6.5, inundacao: 7.4 },
    codigo_ana: null, verificado: false, fontes_tempo_real: [],
  } as unknown as Parameters<typeof faixaDaCidade>[0]
  const agora = new Date('2026-09-01T12:00:00Z')
  const leitura = (n: number) => ({ nivel_m: n, medidoEm: new Date('2026-09-01T11:55:00Z') })
  assert.equal(faixaDaCidade(blumenau, leitura(5.0), false, agora), 'normal')
  assert.equal(faixaDaCidade(blumenau, leitura(6.1), false, agora), 'atencao')
  assert.equal(faixaDaCidade(blumenau, leitura(6.6), false, agora), 'alerta')
  assert.equal(faixaDaCidade(blumenau, leitura(7.6), false, agora), 'inundacao')
})

test('leitura VELHA nunca pinta de cor — vira sem-dado', () => {
  const blumenau = {
    id: 'blumenau', nome: 'Blumenau', ordem: 7,
    cotas_m: { atencao: 6.0, alerta: 6.5, inundacao: 7.4 },
    codigo_ana: null, verificado: false, fontes_tempo_real: [],
  } as unknown as Parameters<typeof faixaDaCidade>[0]
  const agora = new Date('2026-09-01T12:00:00Z')
  // 6 horas atrás, acima da inundação: se pintasse, mentiria vermelho sobre
  // dado velho. Tem de virar cinza.
  const velha = { nivel_m: 7.6, medidoEm: new Date('2026-09-01T06:00:00Z') }
  assert.equal(faixaDaCidade(blumenau, velha, false, agora), 'sem-dado')
})

test('sem cota e sem leitura viram sem-dado, nunca verde', () => {
  const agora = new Date('2026-09-01T12:00:00Z')
  const semCota = {
    id: 'vidal-ramos', nome: 'Vidal Ramos', ordem: 1, cotas_m: {},
    codigo_ana: null, verificado: false, fontes_tempo_real: [],
  } as unknown as Parameters<typeof faixaDaCidade>[0]
  const leitura = { nivel_m: 3.0, medidoEm: new Date('2026-09-01T11:55:00Z') }
  // Tem leitura, mas não tem cota: não dá para dizer a faixa. Cinza.
  assert.equal(faixaDaCidade(semCota, leitura, false, agora), 'sem-dado')

  const comCota = {
    id: 'brusque', nome: 'Brusque', ordem: 3, cotas_m: { atencao: 4.8, inundacao: 6.0 },
    codigo_ana: null, verificado: false, fontes_tempo_real: [],
  } as unknown as Parameters<typeof faixaDaCidade>[0]
  // Tem cota, mas nenhuma leitura: cinza também.
  assert.equal(faixaDaCidade(comCota, null, false, agora), 'sem-dado')
})

test('fase branda da cidade NUNCA vira vermelho — o defeito de 04/09/2026', () => {
  const agora = new Date('2026-09-01T12:00:00Z')
  const leitura = (n: number) => ({ nivel_m: n, medidoEm: new Date('2026-09-01T11:55:00Z') })

  // Taió, como está no estacoes.json: o Plano da COMPDEC tem CINCO fases, e a
  // mais branda (monitoramento, 5,00 m) fica a QUATRO metros da emergência.
  const taio = {
    id: 'taio', nome: 'Taió', ordem: null,
    cotas_m: { monitoramento: 5.0, atencao: 7.0, alerta: 8.0, emergencia: 9.0 },
    codigo_ana: null, verificado: false, fontes_tempo_real: [],
  } as unknown as Parameters<typeof faixaDaCidade>[0]

  // O defeito: a cota mais alta ALCANÇADA era 'monitoramento', e todo nome
  // desconhecido caía na cor mais forte. A leitura real de 03/09 (5,25 m), que
  // a Defesa Civil de Taió pintava de amarelo, saía VERMELHA aqui.
  assert.equal(faixaDaCidade(taio, leitura(5.25), false, agora), 'normal')
  // E a escala verdadeira continua inteira — este é o outro lado do teste:
  // recusar o alarme falso não pode calar o alarme certo.
  assert.equal(faixaDaCidade(taio, leitura(7.1), false, agora), 'atencao')
  assert.equal(faixaDaCidade(taio, leitura(8.1), false, agora), 'alerta')
  assert.equal(faixaDaCidade(taio, leitura(9.1), false, agora), 'emergencia')

  // Ibirama: `observacao_cota` 3,00 é observação, e a emergência é 4,00.
  const ibirama = {
    id: 'ibirama', nome: 'Ibirama', ordem: null,
    cotas_m: { observacao_cota: 3.0, atencao: 3.5, emergencia: 4.0 },
    codigo_ana: null, verificado: false, fontes_tempo_real: [],
  } as unknown as Parameters<typeof faixaDaCidade>[0]
  assert.equal(faixaDaCidade(ibirama, leitura(3.05), false, agora), 'normal')
  assert.equal(faixaDaCidade(ibirama, leitura(4.05), false, agora), 'emergencia')
})

test('cidade só com marca de comportamento fica CINZA, não vermelha', () => {
  const agora = new Date('2026-09-01T12:00:00Z')
  const leitura = (n: number) => ({ nivel_m: n, medidoEm: new Date('2026-09-01T11:55:00Z') })

  // Os três casos que o estacoes.json descreve como "chave que o código não
  // desenha". Não há escala de acionamento publicada para nenhuma delas, então
  // a resposta honesta é "não sei" — cinza —, e não a cor mais forte.
  const casos: [string, Record<string, number>, number][] = [
    ['lontras', { seguranca_observada: 9.2 }, 9.25],          // número de imprensa
    ['timbo', { ativacao_plancon: 5.0, ruas_alerta_citadas: 6.0 }, 6.05], // gatilho de gabinete
    ['trombudo-central', { inundacao_historica: 8.71 }, 8.76], // marca histórica
  ]
  for (const [id, cotas_m, nivel] of casos) {
    const cidade = {
      id, nome: id, ordem: null, cotas_m,
      codigo_ana: null, verificado: false, fontes_tempo_real: [],
    } as unknown as Parameters<typeof faixaDaCidade>[0]
    assert.equal(faixaDaCidade(cidade, leitura(nivel), false, agora), 'sem-dado', id)
  }
})

test('cidade de várias réguas (foz) não recebe uma cor só', () => {
  const agora = new Date('2026-09-01T12:00:00Z')
  const itajai = {
    id: 'itajai', nome: 'Itajaí', ordem: 8, cotas_m: {},
    codigo_ana: null, verificado: false, fontes_tempo_real: [],
  } as unknown as Parameters<typeof faixaDaCidade>[0]
  assert.equal(faixaDaCidade(itajai, null, true, agora), 'varias')
})
