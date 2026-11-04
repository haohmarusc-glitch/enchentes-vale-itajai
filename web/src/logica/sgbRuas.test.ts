/**
 * O contexto do SGB na "minha rua" (04/11/2026): só o que a carta e a setorização dizem; nunca metro, nunca previsão.
 */
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { contextoDoPonto, indexarPontos, textoSgbDaCidade, textoSgbDoPonto, type CidadeSgb } from './sgbRuas'

const BRUSQUE: CidadeSgb = {
  nome: 'Brusque',
  camadas: {
    inundacao: { poligonos: 1384, classe: { Alta: 227, Média: 798, Baixa: 359 }, anos: ['2013'] },
    risco: { setores: 199, setores_de_agua: 36, grau: { Alto: 27, 'Muito alto': 9 }, anos: ['2018', '2019'] },
  },
  pontos: [
    { rua: 'Bartolomeu Pruner', bairro: 'Jardim Maluche', ponto: null, lat: -27.1, lon: -48.9, suscetibilidade: { classe: 'Alta', ano: 2013, executor: 'IPT' }, risco: [{ setor: 'SC_BRUSQUE_SR_1_CPRM', grau: 'Muito alto', tipologias: ['Inundação'], data: '2018-11-20', local: 'Centro' }] },
    { rua: 'Rua X', bairro: null, ponto: 'nº 10', lat: -27.2, lon: -48.95, suscetibilidade: null, risco: [] },
  ],
  pontos_por_classe: { Alta: 1, 'fora da carta': 1 },
  pontos_em_setor_de_risco: 1,
}

test('o ponto: classe, ano e setor de água como o SGB escreve; fora da carta não vira "sem risco"', () => {
  const indice = indexarPontos(BRUSQUE)
  const p = contextoDoPonto(indice, { lat: -27.1, lon: -48.9 })!
  assert.ok(p)
  assert.equal(textoSgbDoPonto(p), 'terreno com suscetibilidade Alta a inundação na carta do SGB (2013) · em setor de risco muito alto de inundação (SGB, 2018)')
  assert.equal(textoSgbDoPonto(contextoDoPonto(indice, { lat: -27.2, lon: -48.95 })!), 'ponto fora da carta de suscetibilidade do SGB (não quer dizer sem risco)')
  assert.equal(contextoDoPonto(indice, { lat: -27.3, lon: -48.9 }), null, 'coordenada que não foi cruzada')
  assert.equal(contextoDoPonto(indice, {}), null, 'cota sem coordenada')
  for (const t of [textoSgbDoPonto(p)!]) {
    assert.doesNotMatch(t, /\d,\d\d m|metros|vai alagar|previs/, 'nunca metro nem previsão')
  }
})

test('a cidade: carta, setores de água (os de deslizamento ficam fora) e os pontos cruzados', () => {
  const linhas = textoSgbDaCidade(BRUSQUE)
  assert.equal(linhas[0], 'Carta de suscetibilidade a inundação (2013): 1384 áreas mapeadas em Brusque — 227 alta, 798 média, 359 baixa.')
  assert.match(linhas[1]!, /^Setorização de risco \(2018, 2019\): 36 setores de água .* — 27 alto, 9 muito alto — de 199 mapeados; os demais são de deslizamento/)
  assert.equal(linhas[2], 'Dos 2 pontos de cota de rua com coordenada, 1 em alta, 1 fora da carta; 1 dentro de setor de risco de água.')
})

test('cidade sem carta e sem coordenada diz isso, e setorização sem água também', () => {
  const semNada: CidadeSgb = { nome: 'Ilhota', camadas: { risco: { setores: 13, setores_de_agua: 0, grau: {}, anos: [] } }, pontos: [], pontos_por_classe: {}, pontos_em_setor_de_risco: 0 }
  const linhas = textoSgbDaCidade(semNada)
  assert.equal(linhas[0], 'O SGB não publicou carta de suscetibilidade a inundação para Ilhota neste serviço.')
  assert.equal(linhas[1], 'Setorização de risco: 13 setores em Ilhota, nenhum de água (são de deslizamento e afins).')
  assert.match(linhas[2]!, /não têm coordenada no cadastro/)
})
