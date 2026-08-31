import { test } from 'node:test'
import assert from 'node:assert/strict'
import { buscarComLimite } from './tempoReal'
import type { Transporte } from './tempoReal'

/*
 * O defeito que estes casos travam: o controle de aborto era criado UMA vez, ao
 * montar a tela, com `setTimeout(abort, 8 s)` que nunca era cancelado no
 * sucesso. Aos 8 segundos o sinal virava abortado para sempre, e a busca de 5
 * em 5 minutos reusava esse mesmo sinal — a página mostrava o nível ao abrir e
 * o perdia na primeira atualização, sem voltar enquanto ficasse aberta.
 *
 * Quem deixa a tela aberta durante a chuva é exatamente quem mais precisa dela.
 */

const CORPO = {
  coletado_em: '2026-08-31T03:00:00+00:00',
  leituras: [
    { estacao: 'Rio do Sul Estação MKS', rio: 'itajai-acu', cidade: 'rio-do-sul',
      nivel_m: 3.5, medido_em: '2026-08-31T00:00' },
  ],
  chuva: [],
}

function respondeCom(corpo: unknown, atrasoMs = 0): Transporte {
  return (_url, init) =>
    new Promise((resolve, reject) => {
      const sinal = init.signal as AbortSignal | undefined
      if (sinal?.aborted) {
        reject(new Error('AbortError'))
        return
      }
      const t = setTimeout(
        () => resolve({ ok: true, json: async () => corpo } as Response),
        atrasoMs,
      )
      sinal?.addEventListener('abort', () => {
        clearTimeout(t)
        reject(new Error('AbortError'))
      })
    })
}

test('uma busca que responde a tempo traz as leituras', async () => {
  const estado = await buscarComLimite(500, respondeCom(CORPO))
  assert.equal(estado.situacao, 'ok')
  assert.equal(estado.leituras.length, 1)
  assert.equal(estado.leituras[0]!.nivel_m, 3.5)
})

test('a SEGUNDA busca também funciona — era aqui que a tela morria', async () => {
  const transporte = respondeCom(CORPO)
  const primeira = await buscarComLimite(500, transporte)
  const segunda = await buscarComLimite(500, transporte)
  const terceira = await buscarComLimite(500, transporte)
  for (const [i, e] of [primeira, segunda, terceira].entries()) {
    assert.equal(e.situacao, 'ok', `busca ${i + 1} devia trazer dado`)
    assert.equal(e.leituras.length, 1)
  }
})

test('uma busca que estoura o limite não contamina a seguinte', async () => {
  // A primeira demora mais que o limite e é abortada; a segunda responde
  // rápido. Com um controle só, a segunda nascia abortada.
  const estourada = await buscarComLimite(10, respondeCom(CORPO, 200))
  assert.equal(estourada.situacao, 'indisponivel', 'a que estourou não inventa dado')

  const seguinte = await buscarComLimite(500, respondeCom(CORPO))
  assert.equal(seguinte.situacao, 'ok', 'a seguinte precisa voltar a funcionar')
  assert.equal(seguinte.leituras.length, 1)
})

test('cada busca recebe o seu próprio controle', async () => {
  const vistos: AbortController[] = []
  const registrar = (c: AbortController) => vistos.push(c)
  await buscarComLimite(500, respondeCom(CORPO), registrar)
  await buscarComLimite(500, respondeCom(CORPO), registrar)
  assert.equal(vistos.length, 2)
  assert.notEqual(vistos[0], vistos[1], 'o controle não pode ser reaproveitado')
  // E o limite é cancelado no sucesso: nenhum dos dois fica abortado depois.
  assert.equal(vistos[0]!.signal.aborted, false)
  assert.equal(vistos[1]!.signal.aborted, false)
})

test('rede fora não vira nível inventado', async () => {
  const quebrado: Transporte = () => Promise.reject(new Error('rede fora'))
  const estado = await buscarComLimite(500, quebrado)
  assert.equal(estado.situacao, 'indisponivel')
  assert.deepEqual(estado.leituras, [])
})

test('chuva vazia por FALHA não se confunde com ausência de pluviômetro', async () => {
  // `chuva: []` significava as duas coisas: "a fonte não publica pluviômetro
  // nesta cidade" e "não conseguimos buscar". No meio de uma chuva, a segunda
  // aparecendo como a primeira lê-se na tela como "não está chovendo".
  const falhou = await buscarComLimite(500, respondeCom({ ...CORPO, chuva_ok: false }))
  assert.equal(falhou.situacao, 'ok')
  assert.equal(falhou.chuvaOk, false)
})

test('arquivo antigo, sem a marca, não vira "falhou"', async () => {
  // Compatibilidade: os ultimo.json já publicados não têm chuva_ok, e neles a
  // lista vazia sempre quis dizer "sem pluviômetro".
  const antigo = await buscarComLimite(500, respondeCom(CORPO))
  assert.equal(antigo.chuvaOk, true)
})

test('chuva_ok verdadeiro é respeitado como veio', async () => {
  const ok = await buscarComLimite(500, respondeCom({ ...CORPO, chuva_ok: true }))
  assert.equal(ok.chuvaOk, true)
})

test('sem resposta nenhuma não se afirma que a chuva falhou', async () => {
  // Não saber nada sobre a chuva é diferente de saber que ela falhou.
  const fora = await buscarComLimite(500, () =>
    Promise.resolve({ ok: false, json: async () => ({}) } as Response))
  assert.equal(fora.situacao, 'indisponivel')
  assert.equal(fora.chuvaOk, true)
})
