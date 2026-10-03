import assert from 'node:assert/strict'
import { test } from 'node:test'
import type { Cidade } from '../dados/tipos'
import type { PontoSerie } from '../dados/serie'
import {
  distancia,
  rotuloDaFaixa,
  situacaoNasCotas,
  tendenciaDaLeitura,
  textoParaCompartilhar,
  vizinhasNoEixo,
} from './agora'

const AGORA = new Date('2026-10-03T16:00:00Z')
const minAtras = (m: number) => new Date(AGORA.getTime() - m * 60_000)

const blumenau: Cidade = {
  id: 'blumenau',
  nome: 'Blumenau',
  ordem: null,
  codigo_ana: null,
  verificado: false,
  cotas_m: { monitoramento: 3, atencao: 4, alerta: 6, emergencia: 8 },
  cotas_nomes_na_fonte: {
    monitoramento: 'Observação',
    atencao: 'Atenção',
    alerta: 'Alerta',
    emergencia: 'Alerta Máximo',
  },
  fontes_tempo_real: [],
}

const comoBlumenau = (id: string, cotas: Record<string, number> = blumenau.cotas_m): Cidade => ({
  ...blumenau,
  id,
  nome: id,
  cotas_m: cotas,
  cotas_nomes_na_fonte: undefined,
})

test('a frase usa o nome da fonte e conta em cm acima e metros até a próxima', () => {
  const s = situacaoNasCotas(blumenau, { nivel_m: 6.4, medidoEm: minAtras(12) }, AGORA)
  assert.deepEqual(s, {
    acima: { nome: 'Alerta', valor: 6, cm: 40 },
    proxima: { nome: 'Alerta Máximo', valor: 8, faltam: 1.6 },
  })
})

test('abaixo de todas as cotas, só diz quanto falta para a primeira', () => {
  const s = situacaoNasCotas(blumenau, { nivel_m: 2.63, medidoEm: minAtras(5) }, AGORA)
  assert.equal(s?.acima, null)
  assert.deepEqual(s?.proxima, { nome: 'Observação', valor: 3, faltam: 0.37 })
})

test('acima da última cota, não inventa uma próxima', () => {
  const s = situacaoNasCotas(blumenau, { nivel_m: 9.1, medidoEm: minAtras(5) }, AGORA)
  assert.equal(s?.acima?.nome, 'Alerta Máximo')
  assert.equal(s?.proxima, null)
})

test('sem frase em Gaspar, Ascurra e Itajaí, mesmo com cotas', () => {
  for (const id of ['gaspar', 'ascurra', 'itajai']) {
    assert.equal(situacaoNasCotas(comoBlumenau(id), { nivel_m: 6.4, medidoEm: minAtras(5) }, AGORA), null, id)
  }
})

test('sem frase sem cota de acionamento (marca de comportamento não conta)', () => {
  const lontras = comoBlumenau('lontras', { seguranca_observada: 9.2 })
  assert.equal(situacaoNasCotas(lontras, { nivel_m: 9.5, medidoEm: minAtras(5) }, AGORA), null)
})

test('sem frase com leitura que não é de agora, sem horário ou sem leitura', () => {
  assert.equal(situacaoNasCotas(blumenau, { nivel_m: 6.4, medidoEm: minAtras(150) }, AGORA), null)
  assert.equal(situacaoNasCotas(blumenau, { nivel_m: 6.4, medidoEm: null }, AGORA), null)
  assert.equal(situacaoNasCotas(blumenau, null, AGORA), null)
})

test('distância em cm abaixo de 1 m, em metros a partir dele', () => {
  assert.equal(distancia(0.37), '37 cm')
  assert.equal(distancia(1.6).replace(/\s/g, ' '), '1,60 m')
})

test('D6: o chip usa o nome da Defesa Civil da cidade, com a mesma faixa', () => {
  assert.equal(rotuloDaFaixa('emergencia', blumenau, 'Emergência'), 'Alerta Máximo')
  assert.equal(rotuloDaFaixa('monitoramento', blumenau, 'Monitoramento'), 'Observação')
  assert.equal(rotuloDaFaixa('alerta', comoBlumenau('rio-do-sul'), 'Alerta'), 'Alerta')
  assert.equal(rotuloDaFaixa('sem-dado', blumenau, 'Sem leitura'), 'Sem leitura')
  assert.equal(rotuloDaFaixa('normal', blumenau, 'Abaixo da atenção'), 'Abaixo da atenção')
})

const ponto = (min: number, nivel: number): PontoSerie => ({ medidoEm: minAtras(min), nivel_m: nivel, regua: null })
const serieSubindo = [ponto(70, 6.2), ponto(60, 6.22), ponto(30, 6.31), ponto(12, 6.4)]

test('D7: a seta só aparece quando o último ponto da série é a leitura mostrada', () => {
  const t = tendenciaDaLeitura(serieSubindo, { nivel_m: 6.4, medidoEm: minAtras(12) }, AGORA)
  assert.equal(t?.rotulo, 'subindo')
  // Série de outro instante, ou outro nível: some.
  assert.equal(tendenciaDaLeitura(serieSubindo, { nivel_m: 6.4, medidoEm: minAtras(2) }, AGORA), null)
  assert.equal(tendenciaDaLeitura(serieSubindo, { nivel_m: 6.55, medidoEm: minAtras(12) }, AGORA), null)
})

test('D7: série que não é de agora não dá seta', () => {
  const velha = [ponto(400, 6.0), ponto(300, 6.3)]
  assert.equal(tendenciaDaLeitura(velha, { nivel_m: 6.3, medidoEm: minAtras(300) }, AGORA), null)
})

test('WhatsApp: hora da medição, sem endereço do site, sem leitura velha', () => {
  const texto = textoParaCompartilhar({
    cidade: blumenau,
    leitura: { nivel_m: 6.4, medidoEm: new Date('2026-10-03T15:48:00Z'), estacao: 'AlertaBlu' },
    rotuloFaixa: 'Alerta',
    tendencia: { rotulo: 'subindo', cmh: 12 },
    agora: AGORA,
  })
  assert.ok(texto)
  assert.match(texto!, /^Blumenau — 6,40\sm \(faixa Alerta, na régua de Blumenau\)/)
  assert.match(texto!, /▲ subindo 12 cm\/h/)
  assert.match(texto!, /Medido às 12:48 de 03\/10 \(há 12 min\) · AlertaBlu/)
  assert.match(texto!, /Não é alerta oficial\. Em emergência, ligue 199\. Siga a Defesa Civil\./)
  assert.doesNotMatch(texto!, /https?:|pages\.dev|github/)
  const velho = textoParaCompartilhar({
    cidade: blumenau,
    leitura: { nivel_m: 6.4, medidoEm: minAtras(300) },
    rotuloFaixa: null,
    tendencia: null,
    agora: AGORA,
  })
  assert.equal(velho, null)
})

test('vizinhas só no eixo; fora dele, nenhuma', () => {
  const eixo = ['rio-do-sul', 'lontras', 'indaial', 'blumenau', 'gaspar']
  assert.deepEqual(vizinhasNoEixo(eixo, 'blumenau'), { acima: 'indaial', abaixo: 'gaspar' })
  assert.deepEqual(vizinhasNoEixo(eixo, 'rio-do-sul'), { acima: null, abaixo: 'lontras' })
  assert.deepEqual(vizinhasNoEixo(eixo, 'taio'), { acima: null, abaixo: null })
})
