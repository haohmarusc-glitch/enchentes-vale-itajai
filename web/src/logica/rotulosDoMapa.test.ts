/**
 * A anticolisão dos rótulos do mapa.
 *
 * Os defeitos que estes testes travam foram vistos nas capturas do celular do
 * Jefferson em 06/09/2026: Blumenau, Gaspar, Ilhota e Itajaí empilhadas umas
 * sobre as outras; "Ibirama" e "Brusque" com o NÍVEL cortado na borda direita;
 * "Taió" por cima de "Oeste Taió · 7 de 7 abertas".
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  FATOR_SUB,
  FONTE_PINO,
  caixaDaEtiquetaMare,
  caixaDoRotuloDoPino,
  colide,
  pinoNaTela,
  planejarRotulosDosPinos,
  textoDoPino,
  type Caixa,
  type Cena,
  type Pino,
} from './mapaMotor'

const CENA_LARGURA = 400

/** Mede como uma fonte de largura fixa: 6 px por caractere na fonte 11. */
const medir = (texto: string, fonte: number) => texto.length * 6 * (fonte / FONTE_PINO)

const pino = (id: string, x: number, y: number, extra: Partial<Pino> = {}): Pino =>
  ({
    cidade: { id, nome: id, cotas_m: {}, regua: null } as unknown as Pino['cidade'],
    rioId: 'itajai-acu',
    x,
    y,
    faixa: 'normal',
    nivel: null,
    medidoEm: null,
    nivelBruto: null,
    ...extra,
  }) as Pino

const cena = (pinos: Pino[]): Cena =>
  ({ pinos, largura: CENA_LARGURA, altura: 300 }) as unknown as Cena

test('A CAIXA USA O TEXTO MAIS LARGO — o defeito que empilhava os rótulos', () => {
  /**
   * "Ilhota" mede 36 px; "≈9,77 m bruto · há 5 min" mede 111. A caixa era
   * medida só com o NOME, reservava um terço do espaço real, e o vizinho
   * entrava por cima. Este é o teste que reprova a versão antiga.
   */
  const nome = medir('Ilhota', FONTE_PINO)
  const sub = medir('≈9,77 m bruto · há 5 min', Math.round(FONTE_PINO * FATOR_SUB))
  assert.ok(sub > nome * 2, 'a sub-linha é mesmo muito mais larga que o nome')
  const { caixa } = caixaDoRotuloDoPino({ x: 200, y: 150 }, { nome, sub }, { largura: CENA_LARGURA })
  assert.ok(caixa.x1 - caixa.x0 >= sub, 'a caixa tem de caber a sub-linha inteira')
})

test('a caixa não cruza a borda da tela — nível cortado é pior que nível nenhum', () => {
  // "Ibirama" e "Brusque": o nome cabia, o número saía pela direita.
  const nome = medir('Ibirama', FONTE_PINO)
  const sub = medir('≈2,29 m bruto · há 6 min', Math.round(FONTE_PINO * FATOR_SUB))
  for (const x of [-50, 0, 5, 200, CENA_LARGURA - 5, CENA_LARGURA + 80]) {
    const { caixa } = caixaDoRotuloDoPino({ x, y: 150 }, { nome, sub }, { largura: CENA_LARGURA })
    assert.ok(caixa.x0 >= -1, `saiu pela esquerda em x=${x}`)
    assert.ok(caixa.x1 <= CENA_LARGURA + 1, `saiu pela direita em x=${x}`)
  }
})

test('sem sub-linha a caixa é mais baixa — não reserva espaço que não usa', () => {
  const a = caixaDoRotuloDoPino({ x: 200, y: 150 }, { nome: 40, sub: 0 }, { largura: CENA_LARGURA })
  const b = caixaDoRotuloDoPino({ x: 200, y: 150 }, { nome: 40, sub: 40 }, { largura: CENA_LARGURA })
  assert.ok(a.caixa.y1 - a.caixa.y0 < b.caixa.y1 - b.caixa.y0)
})

test('colide só quando os retângulos de fato se cruzam', () => {
  const c: Caixa = { x0: 0, y0: 0, x1: 10, y1: 10 }
  assert.equal(colide(c, [{ x0: 5, y0: 5, x1: 15, y1: 15 }]), true)
  assert.equal(colide(c, [{ x0: 10, y0: 0, x1: 20, y1: 10 }]), false, 'encostar não é cruzar')
  assert.equal(colide(c, []), false)
})

test('dois pinos colados: o de faixa MAIS GRAVE fica com o rótulo', () => {
  const c = cena([
    pino('normal', 200, 150, { faixa: 'normal' }),
    pino('inundacao', 205, 150, { faixa: 'inundacao' }),
  ])
  const plano = planejarRotulosDosPinos(medir, c, null, {}, [])
  assert.deepEqual([...plano.keys()], ['inundacao'])
})

test('a cidade SELECIONADA nunca perde o rótulo', () => {
  const c = cena([
    pino('normal', 200, 150, { faixa: 'normal' }),
    pino('inundacao', 205, 150, { faixa: 'inundacao' }),
  ])
  const plano = planejarRotulosDosPinos(medir, c, 'normal', {}, [])
  assert.ok(plano.has('normal'), 'quem a pessoa tocou tem de continuar nomeado')
})

test('A LISTA É COMPARTILHADA: o rótulo da barragem já colocado tira o da cidade', () => {
  /**
   * "Taió" saía por cima de "Oeste Taió · 7 de 7 abertas" porque cada
   * desenhista tinha a sua lista. Aqui a lista chega com um rótulo dentro, e o
   * pino que cai em cima dele cede.
   */
  const ocupada: Caixa[] = [{ x0: 180, y0: 120, x1: 320, y1: 150 }]
  const c = cena([pino('taio', 200, 150)])
  assert.equal(planejarRotulosDosPinos(medir, c, null, {}, ocupada).size, 0)
  // Longe do rótulo já colocado, cabe.
  assert.equal(planejarRotulosDosPinos(medir, cena([pino('taio', 60, 280)]), null, {}, ocupada).size, 1)
})

test('o plano ACRESCENTA à lista — quem vier depois enxerga as cidades', () => {
  const caixas: Caixa[] = []
  planejarRotulosDosPinos(medir, cena([pino('a', 100, 150), pino('b', 300, 250)]), null, {}, caixas)
  assert.equal(caixas.length, 2, 'barragens e réguas precisam ver estas duas')
})

test('o texto do pino diz o que se sabe, e diz quando não sabe', () => {
  const agora = new Date('2026-09-06T12:00:00')
  const medidoEm = new Date('2026-09-06T11:45:00')
  const comNivel = textoDoPino(pino('x', 0, 0, { nivel: 5.24, medidoEm }), {
    mostrarIdade: true,
    agora,
  })
  assert.equal(comNivel.sub, '5,24 m · há 15 min')

  const soBruto = textoDoPino(
    pino('x', 0, 0, { nivelBruto: { nivelBrutoM: 2.29, medidoEm, estacao: 'SDC' } as never }),
    { mostrarIdade: true, agora },
  )
  assert.match(soBruto.sub, /^≈2,29 m bruto · há 15 min$/, 'bruto sai marcado como bruto')

  const semNada = textoDoPino(pino('x', 0, 0), {})
  assert.equal(semNada.sub, 'sem régua', 'ausência de instrumento é dita, não omitida')
})

test('o chip da maré reserva o canto e o rótulo da cidade se acomoda', () => {
  /**
   * O "sem leitura" de Itajaí, que fica logo abaixo do chip fixo no
   * topo-direito, saía por baixo dele. O chip não cede — é fixo na tela —,
   * então entra na lista antes de todo mundo.
   */
  const comMar = { mar: { rotulo: 'Maré subindo ▲' }, largura: CENA_LARGURA } as never
  const chip = caixaDaEtiquetaMare(medir, comMar)!
  assert.ok(chip, 'há chip quando a cena tem mar')
  assert.ok(chip.x1 <= CENA_LARGURA, 'o chip fica dentro da tela')
  assert.ok(chip.y0 >= 0)

  // Um pino colado no chip perde o rótulo; longe dele, mantém.
  const colado = cena([pino('itajai', CENA_LARGURA - 40, chip.y1 + 12)])
  assert.equal(planejarRotulosDosPinos(medir, colado, null, {}, [chip]).size, 0)
  const longe = cena([pino('itajai', 100, 250)])
  assert.equal(planejarRotulosDosPinos(medir, longe, null, {}, [chip]).size, 1)
})

test('cena sem mar não inventa chip', () => {
  assert.equal(caixaDaEtiquetaMare(medir, { mar: null, largura: CENA_LARGURA } as never), null)
})



/**
 * PINO FORA DA TELA NÃO TEM RÓTULO.
 *
 * Capturas do Jefferson de 07/09/2026, mapa aproximado em Itajaí: "Ascurra",
 * "Blumenau" e "Indaial" apareciam presos na margem esquerda, SEM bolinha
 * nenhuma — os pinos estavam a 60 km dali. A trava de borda existe para o pino
 * que encosta na beirada; com o pino longe, ela virava um nível do rio escrito
 * em cima de um bairro que não é o dele.
 */
test('pino fora da tela não ganha rótulo — nem preso na margem', () => {
  const fora = pino('ascurra', -420, 150, { nivelBruto: { nivelBrutoM: 7.74, medidoEm: null } as unknown as Pino['nivelBruto'] })
  const plano = planejarRotulosDosPinos(medir, cena([fora]), null, {}, [])
  assert.equal(plano.size, 0, 'o nome saía sobre Itaipava, a 60 km de Ascurra')
})

test('pino encostado na borda MANTÉM o rótulo, preso para dentro', () => {
  // Este é o caso que a trava de borda existe para atender: a bolinha aparece
  // pela metade, o nome tem de continuar legível e inteiro.
  const encostado = pino('itajai', 2, 150)
  const plano = planejarRotulosDosPinos(medir, cena([encostado]), null, {}, [])
  const r = plano.get('itajai')
  assert.ok(r, 'quem está na tela não pode perder o nome')
  assert.ok(r!.caixa.x0 >= 0, 'e o nome não pode sair cortado pela esquerda')
})

test('fora da tela em qualquer um dos quatro lados', () => {
  for (const [x, y] of [[-50, 150], [CENA_LARGURA + 50, 150], [200, -50], [200, 350]] as const) {
    assert.equal(pinoNaTela({ x, y }, { largura: CENA_LARGURA, altura: 300 }), false, `${x},${y}`)
  }
  assert.equal(pinoNaTela({ x: 200, y: 150 }, { largura: CENA_LARGURA, altura: 300 }), true)
})

test('nem a cidade SELECIONADA ganha rótulo estando fora da tela', () => {
  // A selecionada fura a anticolisão de propósito (quem tocou nela quer o
  // número dela). Furar a borda é outra coisa: apontaria para o lugar errado.
  const plano = planejarRotulosDosPinos(medir, cena([pino('blumenau', -300, 100)]), 'blumenau', {}, [])
  assert.equal(plano.size, 0)
})
