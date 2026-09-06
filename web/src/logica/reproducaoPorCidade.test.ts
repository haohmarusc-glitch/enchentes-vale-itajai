import { test } from 'node:test'
import assert from 'node:assert/strict'
import { linhaDaReproducao, quantasReguas, type PontoDaReproducao } from './reproducaoPorCidade'

const p = (nivel: number, regua: string | null, min = 0): PontoDaReproducao => ({
  medidoEm: new Date(2026, 8, 6, 16, min),
  nivel_m: nivel,
  regua,
})

/** A série do Açu em Itajaí, como veio publicada em 06/09/2026. */
const ITAJAI_ACU = [
  p(1.54, 'DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL', 41),
  p(0.65, 'DC-02 Rio Itajaí-Açu - Praça Celso Pereira da Silva', 41),
  p(3.10, 'DC-11 Rio Itajaí-Açú – Santa Regina (Volta de Cima)', 50),
  p(1.47, 'DC-01 Rio Itajaí-Açu - ICMBio/CEPSUL', 51),
]

test('ITAJAÍ NÃO MOSTRA NÚMERO NA REPRODUÇÃO — são três réguas com zeros diferentes', () => {
  // Sem esta regra a linha escrevia 3,10 m e, um minuto depois, 1,47 m: um
  // salto de 1,63 m que é a régua trocando, não o rio.
  const linha = linhaDaReproducao(ITAJAI_ACU, ITAJAI_ACU[2]!)
  assert.equal(linha.tipo, 'varias-reguas')
  assert.equal(linha.tipo === 'varias-reguas' && linha.quantas, 3)
})

test('cidade de uma régua só mostra o número, como sempre', () => {
  const blumenau = [p(3.2, 'Blumenau', 0), p(3.25, 'Blumenau', 15)]
  const linha = linhaDaReproducao(blumenau, blumenau[1]!)
  assert.equal(linha.tipo, 'leitura')
  assert.equal(linha.tipo === 'leitura' && linha.nivel_m, 3.25)
})

test('sem ponto no instante é sem leitura, não zero', () => {
  assert.equal(linhaDaReproducao([p(3.2, 'Blumenau')], null).tipo, 'sem-leitura')
  assert.equal(linhaDaReproducao([], null).tipo, 'sem-leitura')
})

test('duas réguas DESCONHECIDAS não são a mesma régua', () => {
  // Mesma escolha do resumo24h: juntá-las afirmaria um zero que ninguém disse.
  assert.equal(quantasReguas([p(1, null), p(2, null)]), 1, 'desconhecidas contam como UMA desconhecida')
  assert.equal(quantasReguas([p(1, null), p(2, 'DC-10')]), 2, 'uma nomeada + uma desconhecida = duas')
})

test('nível não-finito não vira número na tela', () => {
  const ruim = [{ medidoEm: new Date(), nivel_m: Number.NaN, regua: 'X' }]
  assert.equal(linhaDaReproducao(ruim, ruim[0]!).tipo, 'sem-leitura')
})

test('BLUMENAU NÃO PERDE O NÚMERO — primária e resgate são a mesma régua', () => {
  // "Blumenau" e "Blumenau (AlertaBlu)" são a régua ANA 83800002, mesmo zero.
  // Contá-las como duas é o defeito que o teste 11 de docs/testes-navegador.md
  // vigia: "sumiu a tendência de Blumenau".
  const pontos = [p(3.2, 'Blumenau', 0), p(3.25, 'Blumenau (AlertaBlu)', 45)]
  const vinculo = new Map([['Blumenau (AlertaBlu)', 'Blumenau']])
  const linha = linhaDaReproducao(pontos, pontos[1]!, vinculo)
  assert.equal(linha.tipo, 'leitura', 'sem o vínculo, Blumenau perderia o metro')
  assert.equal(linha.tipo === 'leitura' && linha.nivel_m, 3.25)
  assert.equal(quantasReguas(pontos, vinculo), 1)
  assert.equal(quantasReguas(pontos), 2, 'e sem o vínculo seriam mesmo duas')
})

test('o vínculo não salva Itajaí: as onze são réguas de verdade', () => {
  const vinculo = new Map([['Blumenau (AlertaBlu)', 'Blumenau']])
  assert.equal(linhaDaReproducao(ITAJAI_ACU, ITAJAI_ACU[0]!, vinculo).tipo, 'varias-reguas')
})

test('vínculo CIRCULAR não junta — o lado seguro é ficar sem número', () => {
  // Se A diz socorrer B e B diz socorrer A, não há primária. Juntar as duas
  // afirmaria um zero comum que ninguém garantiu; mantê-las separadas faz a
  // cidade cair em "várias réguas" e não mostrar metro nenhum.
  const ciclo = new Map([['A', 'B'], ['B', 'A']])
  assert.equal(quantasReguas([p(1, 'A'), p(2, 'B')], ciclo), 2)
  assert.equal(linhaDaReproducao([p(1, 'A'), p(2, 'B')], p(2, 'B'), ciclo).tipo, 'varias-reguas')
})

test('cadeia de dois saltos chega na primária', () => {
  const cadeia = new Map([['C', 'B'], ['B', 'A']])
  assert.equal(quantasReguas([p(1, 'A'), p(2, 'B'), p(3, 'C')], cadeia), 1)
})
