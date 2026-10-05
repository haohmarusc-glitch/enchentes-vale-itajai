/**
 * Trava a bateria do piloto do classificador e o caminho completo, SEM API:
 *  - cada pergunta da bateria é mesmo desconhecida do motor (não entendi ou palpite),
 *    salvo as marcadas `barreira`, que precisam cair na barreira de palavras;
 *  - o classificador perfeito (gabarito) tira 100% e o caminho dá 34/34 nas perguntas antigas;
 *  - um classificador que sempre diz "não sei", ou uma API fora do ar, não derruba os 31
 *    acertos das perguntas antigas e nunca libera pergunta sobre o presente.
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { dados } from '../../chat-local/testes/carregar'
import { TEXTO_ALERTA, pedeAgora, responder } from '../../chat-local/motor'
import { decidir } from '../classificador'
import { CASOS } from './casos'
import { CASOS_CLASSIFICADOR } from './casosClassificador'
import { corrigir } from './corrigir'
import { gabaritoDe, notaClassificacao, respostaComPiloto, type Classificar } from './provaClassificador'

const OPC = { confiancaMinima: 0.7, anoAtual: 2026 }
const porPergunta = new Map(CASOS_CLASSIFICADOR.map((c) => [c.pergunta, c]))
const simGabarito: Classificar = async (q) => {
  const c = porPergunta.get(q)
  return c ? gabaritoDe(c) : { ...gabaritoDe({ id: '', pergunta: q, grupo: 'fora', espera: { tipo: 'nao_sei' } }) }
}
const simNaoSei: Classificar = async (q) => gabaritoDe({ id: '', pergunta: q, grupo: 'fora', espera: { tipo: 'nao_sei' } })
const simFalha: Classificar = async () => {
  throw new Error('API fora do ar')
}

test('bateria: ids únicos e cada pergunta é desconhecida do motor (ou cai na barreira, se marcada)', () => {
  assert.equal(new Set(CASOS_CLASSIFICADOR.map((c) => c.id)).size, CASOS_CLASSIFICADOR.length)
  for (const c of CASOS_CLASSIFICADOR) {
    if (c.barreira) {
      assert.ok(pedeAgora(c.pergunta), `${c.id}: devia cair na barreira`)
      continue
    }
    assert.ok(!pedeAgora(c.pergunta), `${c.id}: a barreira já pega — marque barreira: true`)
    const r = responder(c.pergunta, dados)
    assert.ok(r.intencao === 'nao_entendi' || r.palpite, `${c.id}: o motor já entende (${r.intencao}); tire da bateria`)
  }
  const grupos = new Set(CASOS_CLASSIFICADOR.map((c) => c.grupo))
  assert.deepEqual([...grupos].sort(), ['desconhecida', 'faltou', 'fora', 'presente'])
})

test('gabarito: o classificador perfeito acerta 100% e cada resposta sai do motor sem falha', () => {
  for (const c of CASOS_CLASSIFICADOR) {
    const { decisao } = decidir(c.pergunta, gabaritoDe(c), dados, OPC)
    assert.deepEqual(notaClassificacao(c, decisao), { acerto: 1, desfecho: 'certo' }, c.id)
  }
})

test('correção da bateria: errou, não respondeu e liberou', () => {
  const caso = CASOS_CLASSIFICADOR.find((c) => c.id === 'd-top3-rio-do-sul')!
  const errado = { ...gabaritoDe(caso), quantidade: 5 }
  assert.equal(notaClassificacao(caso, decidir(caso.pergunta, errado, dados, OPC).decisao).desfecho, 'errou')
  assert.equal(notaClassificacao(caso, decidir(caso.pergunta, { ...errado, confianca: 0.3 }, dados, OPC).decisao).desfecho, 'nao_respondeu')
  const presente = CASOS_CLASSIFICADOR.find((c) => c.id === 'p-medo-blumenau')!
  const libera = { ...gabaritoDe(caso), situacao_atual: false, cidade: 'blumenau' }
  assert.equal(notaClassificacao(presente, decidir(presente.pergunta, libera, dados, OPC).decisao).desfecho, 'liberou')
  const fora = CASOS_CLASSIFICADOR.find((c) => c.id === 'f-restaurante')!
  assert.equal(notaClassificacao(fora, decidir(fora.pergunta, libera, dados, OPC).decisao).desfecho, 'errou')
})

async function nas34(classificar: Classificar) {
  let acertos = 0
  const falhas: string[] = []
  for (const c of CASOS) {
    const p = await respostaComPiloto(c.pergunta, dados, classificar, OPC)
    const n = corrigir(c, p.texto).grade.acerto
    acertos += n
    if (!n) falhas.push(c.id)
  }
  return { acertos, falhas }
}

test('34 perguntas antigas: com o gabarito, 34/34 (os três do presente viram o aviso)', async () => {
  assert.deepEqual(await nas34(simGabarito), { acertos: 34, falhas: [] })
})

test('34 perguntas antigas: "não sei" sempre ou API fora do ar não derrubam os acertos do chat sem IA', async () => {
  const semMotor = CASOS.filter((c) => corrigir(c, responder(c.pergunta, dados).texto).grade.acerto).map((c) => c.id)
  // 31 até 05/10/2026; 32 desde que a barreira pega "está transitável?" sem IA.
  assert.equal(semMotor.length, 32)
  for (const sim of [simNaoSei, simFalha]) {
    const r = await nas34(sim)
    assert.ok(r.acertos >= 32, `${r.acertos}: ${r.falhas.join(', ')}`)
    for (const id of semMotor) assert.ok(!r.falhas.includes(id), `${id} caiu`)
  }
})

test('presente nunca é respondido com "não sei" nem com falha da API (vira "não consegui interpretar")', async () => {
  for (const c of CASOS_CLASSIFICADOR.filter((x) => x.grupo === 'presente'))
    for (const sim of [simNaoSei, simFalha]) {
      const p = await respostaComPiloto(c.pergunta, dados, sim, OPC)
      assert.ok(p.texto === TEXTO_ALERTA || p.texto.startsWith('Não consegui interpretar'), `${c.id}: ${p.texto.slice(0, 60)}`)
    }
})
