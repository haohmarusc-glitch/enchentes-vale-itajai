/**
 * 16ª entrega dos comandos do chat (docs/CHAT-GLOBAL-COMANDOS.md): as ruas pela cota, cidade inteira — com um nível
 * dito, no nível de agora, as próximas e as que alagam primeiro.
 */
import { test, beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { catalogoDoCadastro } from './catalogo'
import { interpretar } from './interpretar'
import { executar, limparRetratos, type Ambiente, type DadosDoChat } from './executar'
import { textoDeAjuda } from './ajuda'
import { textoPrimeirasRuas, textoProximasRuas, textoRuasNoNivel, textoSemCotasDeRua, textoSemNivelDeAgora, type EntradaRuas } from './ruasPelaCota'
import type { LeituraAoVivo } from '../dados/tempoReal'
import type { AoVivo } from '../dados/usarAoVivo'
import type { NivelSc } from '../dados/nivelSc'
import type { Cidade, CotaRua } from '../dados/tipos'
import type { Contexto } from './tipos'

const ler = (c: string) => JSON.parse(readFileSync(new URL(`../../../data/${c}`, import.meta.url), 'utf8'))
const estacoes = ler('estacoes.json')
const cat = catalogoDoCadastro(estacoes)
const fora: Contexto = { cidadeAtual: null, naMonitor: false, reguaAtual: null }
const emBlumenau: Contexto = { cidadeAtual: 'blumenau', naMonitor: false, reguaAtual: null }
const AGORA = new Date('2026-10-06T18:00:00Z') // 15h00 em Brasília
const passos = (texto: string, ctx: Contexto = fora) => {
  const r = interpretar(texto, cat, ctx)
  assert.ok(r && r.tipo === 'comandos', `"${texto}" devia virar comando, veio ${JSON.stringify(r)}`)
  return r.passos
}
const cidadeDoCadastro = (id: string): { cidade: Cidade; rioId: string } | null => {
  for (const [rioId, r] of Object.entries(estacoes.rios as Record<string, { cidades: Cidade[] }>)) {
    const c = r.cidades.find((x) => x.id === id)
    if (c) return { cidade: c, rioId }
  }
  return null
}
const blumenau = cidadeDoCadastro('blumenau')!.cidade
const itajai = cidadeDoCadastro('itajai')!.cidade
const rioDoSul = cidadeDoCadastro('rio-do-sul')!.cidade

test('frases: nível dito, agora, próximas (com "mais 50 cm"), primeiro; rua por nome continua no motor e na 3ª', () => {
  assert.deepEqual(passos('quais ruas alagam com 8 m em Blumenau?'), [{ tipo: 'ruas_pela_cota', pergunta: 'nivel', nivelM: 8, cidadeId: 'blumenau' }])
  assert.deepEqual(passos('que ruas alagam com 8,50 m em Blumenau?'), [{ tipo: 'ruas_pela_cota', pergunta: 'nivel', nivelM: 8.5, cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quantas ruas alagam se o rio chegar a 9 metros em Gaspar?'), [{ tipo: 'ruas_pela_cota', pergunta: 'nivel', nivelM: 9, cidadeId: 'gaspar' }])
  assert.deepEqual(passos('se o rio chegar a 7 m, quais ruas alagam em Blumenau?'), [{ tipo: 'ruas_pela_cota', pergunta: 'nivel', nivelM: 7, cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quais ruas alagam com 8 m?', emBlumenau), [{ tipo: 'ruas_pela_cota', pergunta: 'nivel', nivelM: 8 }])
  assert.deepEqual(passos('quais ruas o rio já alcançou em Blumenau?'), [{ tipo: 'ruas_pela_cota', pergunta: 'agora', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('que ruas estão alagadas agora em Blumenau?'), [{ tipo: 'ruas_pela_cota', pergunta: 'agora', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quais ruas alagam agora em Blumenau?'), [{ tipo: 'ruas_pela_cota', pergunta: 'agora', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quais são as próximas ruas a alagar em Blumenau?'), [{ tipo: 'ruas_pela_cota', pergunta: 'proximas', cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quais ruas alagam se subir mais 50 cm em Blumenau?'), [{ tipo: 'ruas_pela_cota', pergunta: 'proximas', subirM: 0.5, cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quais ruas alagam com mais 1 m em Blumenau?'), [{ tipo: 'ruas_pela_cota', pergunta: 'proximas', subirM: 1, cidadeId: 'blumenau' }])
  assert.deepEqual(passos('quais ruas alagam primeiro em Gaspar?'), [{ tipo: 'ruas_pela_cota', pergunta: 'primeiras', cidadeId: 'gaspar' }])
  assert.deepEqual(passos('quais são as ruas mais baixas de Blumenau?'), [{ tipo: 'ruas_pela_cota', pergunta: 'primeiras', cidadeId: 'blumenau' }])
  // O que já existia continua igual.
  assert.deepEqual(passos('manchas na rua Lauro Müller em Itajaí')[0]!.tipo, 'rua')
  assert.deepEqual(passos('mostrar a rua São Paulo em Gaspar')[0]!.tipo, 'rua')
  assert.equal(interpretar('qual a cota da Rua São Rafael em Blumenau?', cat, fora), null, 'cota de UMA rua é do motor')
  assert.equal(interpretar('quantas cheias passaram da cota da Rua São Rafael em Blumenau?', cat, fora), null)
  assert.equal(interpretar('quais ruas alagam com 30 m em Blumenau?', cat, fora), null, 'nível impossível não vira comando')
  assert.equal(interpretar('quais ruas alagam com 8 m em Pomerode?', cat, fora), null)
})

// Uma tabela pequena com as três situações: cota normal, ponto bloqueado (Rio do Sul) e rua sem número.
const cota = (cidade: string, rua: string, cota_m: number | null, extra: Partial<CotaRua> = {}): CotaRua =>
  ({ cidade, rio: 'itajai-acu', rua, bairro: null, ponto: null, cota_m, referencia: 'régua', fonte: 'Defesa Civil', data_fonte: '2022-05', confianca: 'alta', ...extra }) as CotaRua
const COTAS: CotaRua[] = [
  cota('blumenau', 'Rua São Rafael', 7.4, { bairro: 'Itoupava Norte', ponto: 'final da rua' }),
  cota('blumenau', 'Rua São Rafael', 7.75, { bairro: 'Itoupava Norte', ponto: 'próximo ao nº 169' }),
  cota('blumenau', 'Rua Amazonas', 8.0, { bairro: 'Garcia', abrigo: 'Escola Pedro II' }),
  cota('blumenau', 'Rua XV de Novembro', 8.6, { bairro: 'Centro' }),
  cota('blumenau', 'Rua Progresso', 9.2, { bairro: 'Progresso' }),
  cota('blumenau', 'Rua da Glória', 10.5, { bairro: 'Glória' }),
  cota('blumenau', 'Rua Sem Número', null, { bairro: 'Centro', nota: 'cota não publicada' }),
  cota('rio-do-sul', 'Rua Pouso Redondo', 3.11, { usar_para_aviso: false, nota: 'abaixo do nível normal do rio' }),
  cota('rio-do-sul', 'Rua Oscar Barcelos', 5.2),
  cota('rio-do-sul', 'Rua Coronel Aristiliano Ramos', 6.1),
]
const entrada = (cidade: Cidade): EntradaRuas => ({ cidade, cotas: COTAS, cobertas: ['Blumenau', 'Rio do Sul'] })

test('textos: contagem e pontos mais perto do nível, bairros, bloqueados fora da conta, sem cota, Itajaí, o 199', () => {
  const oito = textoRuasNoNivel(entrada(blumenau), 8, { tipo: 'dito' })
  assert.match(oito, /^Se o rio em Blumenau chegar a 8,00 m, pela cota publicada 3 de 6 pontos de rua com cota levantada já estariam alagados\./)
  assert.match(oito, /Por bairro: Itoupava Norte \(2\), Garcia \(1\)\./)
  assert.match(oito, /• Rua Amazonas, Garcia — a partir de 8,00 m · abrigo: Escola Pedro II\n• Rua São Rafael \(próximo ao nº 169\), Itoupava Norte — a partir de 7,75 m\n• Rua São Rafael \(final da rua\), Itoupava Norte — a partir de 7,40 m/, 'os mais perto do nível primeiro')
  assert.match(oito, /1 rua citada pela fonte não tem número de cota e fica fora da conta\./)
  assert.match(oito, /não diz que a rua inteira alaga[^]*não é completa[^]*não observação na rua nem previsão[^]*199/)
  assert.doesNotMatch(oito, /já alagou|está alagada/, 'nível dito é hipótese, não afirmação')
  const sete = textoRuasNoNivel(entrada(blumenau), 7, { tipo: 'dito' })
  assert.match(sete, /0 de 6[^]*Nenhum ponto levantado alaga com o rio nesse nível\. O primeiro é Rua São Rafael \(final da rua\), Itoupava Norte, a partir de 7,40 m\./)
  const agora = textoRuasNoNivel(entrada(blumenau), 7.5, { tipo: 'agora', medidoEm: new Date('2026-10-06T17:50:00Z'), agora: AGORA })
  assert.match(agora, /^Régua de Blumenau: 7,50 m às 14:50 de 06\/10 \(há 10 min\)\. Pela cota publicada, 1 de 6 pontos de rua com cota levantada já estaria alagado\./)
  // Rio do Sul: o ponto bloqueado não entra na conta nem na lista; aparece à parte.
  const rs = textoRuasNoNivel(entrada(rioDoSul), 5.5, { tipo: 'dito' })
  assert.match(rs, /1 de 2 pontos de rua com cota levantada já estaria alagado/)
  assert.match(rs, /Fora da conta: 1 ponto com cota abaixo desse nível que a fonte marca como não conferido para aviso \(Rua Pouso Redondo\)\./)
  assert.doesNotMatch(rs, /• Rua Pouso Redondo/)
  // Próximas, com quanto falta; e "se subir mais 50 cm".
  const prox = textoProximasRuas(entrada(blumenau), 7.5, new Date('2026-10-06T17:50:00Z'), AGORA)
  assert.match(prox, /As próximas ruas a alagar, se o rio continuar subindo[^]*• Rua São Rafael \(próximo ao nº 169\), Itoupava Norte — a partir de 7,75 m \(faltam 25 cm\)\n• Rua Amazonas, Garcia — a partir de 8,00 m \(faltam 50 cm\) · abrigo: Escola Pedro II/)
  assert.match(prox, /hipótese, não previsão/)
  const mais = textoProximasRuas(entrada(blumenau), 7.5, new Date('2026-10-06T17:50:00Z'), AGORA, 0.5)
  assert.match(mais, /Se subisse mais 50 cm, para 8,00 m, pela cota publicada 2 pontos de rua a mais já estariam alagados:\n• Rua São Rafael \(próximo ao nº 169\)[^]*\n• Rua Amazonas/)
  // Primeiras.
  const primeiras = textoPrimeirasRuas(entrada(rioDoSul))
  assert.match(primeiras, /^As ruas que alagam primeiro em Rio do Sul[^]*de 2 pontos com cota\):\n• Rua Oscar Barcelos — a partir de 5,20 m/)
  assert.match(primeiras, /Fora da lista: 1 ponto que a fonte marca como não conferido para aviso \(Rua Pouso Redondo, 3,11 m\)/)
  // Sem cotas: Itajaí aponta as manchas; sem nível de agora: não afirma.
  assert.match(textoSemCotasDeRua(entrada(itajai)), /Ainda não há cota de rua levantada para Itajaí[^]*mapa das manchas/)
  assert.match(textoSemNivelDeAgora(blumenau, { nivel_m: 7, medidoEm: new Date('2026-10-06T12:00:00Z') }, AGORA, false), /Sem leitura de agora da régua de Blumenau, não digo quais ruas o rio já alcançou\. A última leitura é de 09:00 de 06\/10 \(há 6 h\), velha demais/)
  assert.match(textoSemNivelDeAgora(itajai, null, AGORA, true), /várias réguas/)
  for (const t of [oito, agora, rs, prox, mais, primeiras]) assert.match(t, /199/)
})

const leitura = (cidade: string, nivel_m: number, medidoEm: Date): LeituraAoVivo => ({ estacao: cidade, rio: 'itajai-acu', cidade, nivel_m, medidoEm, resgateDe: null })
function ambiente(leituras: LeituraAoVivo[]) {
  const aoVivo: AoVivo = {
    tempoReal: { situacao: 'ok', leituras, chuva: [], chuvaOk: true, coletadoEm: AGORA, fonte: null },
    nivelSc: new Map() as NivelSc,
    serie: { situacao: 'ok', series: {}, resgates: {}, janelaHoras: 48, geradoEm: AGORA },
    agora: AGORA,
  }
  const dados: DadosDoChat = { aoVivo: async () => aoVivo, cidade: cidadeDoCadastro, reguasNoMapa: () => [], tracado: async () => null, base: () => '', cotasRuas: async () => COTAS }
  const navegacoes: string[] = []
  const amb: Ambiente = { navegar: (p) => navegacoes.push(p), rotaAtual: () => '/', monitor: () => null, esperarMonitor: async () => null, dados }
  return { amb, navegacoes }
}
const rodar = (texto: string, amb: Ambiente, c: Contexto = fora) => {
  const r = interpretar(texto, cat, c)
  assert.ok(r && r.tipo === 'comandos', texto)
  return executar(r.passos, amb, cat, c, () => textoDeAjuda(fora, null))
}

beforeEach(() => limparRetratos())

test('executor: nível de agora só fresco; leitura velha recusa; link para a aba Minha rua; nada navega', async () => {
  const fresca = ambiente([leitura('blumenau', 7.5, new Date('2026-10-06T17:50:00Z'))])
  const r = await rodar('quais ruas o rio já alcançou em Blumenau?', fresca.amb)
  assert.match(r.texto, /^Régua de Blumenau: 7,50 m às 14:50 de 06\/10 \(há 10 min\)\. Pela cota publicada, 1 de 6/)
  assert.deepEqual(r.link, { texto: 'Minha rua em Blumenau →', para: '/acu/blumenau?aba=rua' })
  const p = await rodar('quais são as próximas ruas em Blumenau?', fresca.amb)
  assert.match(p.texto, /As próximas ruas a alagar/)
  const velha = ambiente([leitura('blumenau', 7.5, new Date('2026-10-06T12:00:00Z'))])
  assert.match((await rodar('quais ruas o rio já alcançou em Blumenau?', velha.amb)).texto, /velha demais para servir como nível de agora/)
  assert.match((await rodar('quais ruas alagam com 8 m em Blumenau?', velha.amb)).texto, /^Se o rio em Blumenau chegar a 8,00 m/, 'nível dito não depende de leitura')
  assert.match((await rodar('quais ruas alagam primeiro em Blumenau?', velha.amb)).texto, /^As ruas que alagam primeiro em Blumenau/)
  assert.match((await rodar('quais ruas alagam com 8 m em Itajaí?', velha.amb)).texto, /Ainda não há cota de rua levantada para Itajaí/)
  assert.match((await rodar('quais ruas alagam com 8 m?', velha.amb)).texto, /Em qual cidade\?/)
  assert.deepEqual(fresca.navegacoes, [])
  assert.deepEqual(velha.navegacoes, [])
})

test('a ajuda lista os pedidos da 16ª entrega', () => {
  for (const c of [fora, { cidadeAtual: null, naMonitor: true, reguaAtual: null } as Contexto]) {
    const t = textoDeAjuda(c, null).texto
    for (const f of ['quais ruas alagam com 8 m', 'o rio já alcançou', 'próximas ruas', 'alagam primeiro']) assert.ok(t.includes(f), f)
  }
})
