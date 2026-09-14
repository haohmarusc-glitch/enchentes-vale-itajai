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

test('chuva fica abaixo do pino e reserva espaço contra rótulos vizinhos', () => {
  // B está a 70 px: a chuva de A (quatro linhas) desce até ~156 sem tocar o
  // pino de B (163..177), e o rótulo de B tem de respeitar a chuva de A.
  const c = cena([pino('A', 200, 100), pino('B', 200, 170)])
  const chuva = new Map([['A', ['1 h: 0 mm', '12 h: 12 mm', '24 h: 20 mm', 'Chuva · há 5 min']]])
  const plano = planejarRotulosDosPinos(medir, c, null, { chuva }, [])
  const a = plano.get('A')!
  assert.ok(a.chuvaY! > 107)
  assert.ok(a.caixa.y1 >= a.chuvaY! + 4 * 11)
  assert.deepEqual(a.chuva, chuva.get('A'))
  // B acha lugar sem cruzar a caixa de A (14/09/2026: o rótulo tenta outras
  // posições antes de sumir).
  const b = plano.get('B')!
  assert.ok(b, 'B ganha rótulo em outra posição')
  assert.equal(colide(a.caixa, [b.caixa]), false)
})

test('a chuva nunca cobre pino colorido: antes de esconder o nome, o rótulo abre mão da chuva', () => {
  // B (colorido) está logo abaixo de A: as quatro linhas de chuva de A
  // escreveriam por cima do pino de B. A fica com nome e nível, sem chuva.
  const a = pino('A', 200, 100, { faixa: 'atencao', nivel: 4.6, medidoEm: new Date() })
  const b = pino('B', 200, 150, { faixa: 'alerta', nivel: 6.1, medidoEm: new Date() })
  const chuva = new Map([['A', ['1 h: 0 mm', '12 h: 12 mm', '24 h: 20 mm', 'Chuva · há 5 min']]])
  const plano = planejarRotulosDosPinos(medir, cena([a, b]), null, { chuva, mostrarIdade: true, agora: new Date() }, [])
  const ra = plano.get('A')!
  assert.ok(ra, 'A mantém o rótulo')
  assert.deepEqual(ra.chuva, [], 'sem a chuva, que cobriria o pino de B')
  assert.equal(colide(ra.caixa, [{ x0: 193, y0: 143, x1: 207, y1: 157 }]), false)
  // Com B cinza, a chuva pode ficar (regra 2: rótulo com nível cobre só pino cinza).
  const cinza = pino('B', 200, 150, { faixa: 'sem-dado' })
  const plano2 = planejarRotulosDosPinos(medir, cena([a, cinza]), null, { chuva, mostrarIdade: true, agora: new Date() }, [])
  assert.deepEqual(plano2.get('A')!.chuva, chuva.get('A'))
})

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
  // O mais grave fica no lugar de sempre (acima, centrado); o outro tenta as
  // demais posições e, cabendo sem cruzar, também aparece.
  const grave = plano.get('inundacao')!
  assert.ok(grave)
  assert.equal(grave.baseY, 150 - 9, 'o mais grave fica acima do pino')
  const outro = plano.get('normal')
  if (outro) assert.equal(colide(outro.caixa, [grave.caixa]), false, 'o outro nunca cruza o do mais grave')
})

test('quando nenhuma posição cabe, o rótulo SOME — nunca escreve por cima', () => {
  // Rótulos já colocados em cima, à direita, à esquerda e embaixo do pino.
  const cerco: Caixa[] = [
    { x0: 0, y0: 100, x1: 400, y1: 141 }, // acima
    { x0: 0, y0: 159, x1: 400, y1: 300 }, // abaixo
  ]
  const plano = planejarRotulosDosPinos(medir, cena([pino('x', 200, 150)]), null, {}, cerco)
  assert.equal(plano.size, 0)
})

test('"sem leitura" nunca cobre pino; rótulo com nível cobre só pino CINZA, nunca colorido', () => {
  // Dois pinos cinzas colados à cidade em atenção, um de cada lado e acima.
  const atencao = pino('a', 200, 150, { faixa: 'atencao', nivel: 4.6, medidoEm: new Date() })
  const cinzaEsq = pino('c1', 170, 135, { faixa: 'sem-dado' })
  const cinzaDir = pino('c2', 230, 135, { faixa: 'sem-dado' })
  const bolinha = (p: Pino): Caixa => ({ x0: p.x - 7, y0: p.y - 7, x1: p.x + 7, y1: p.y + 7 })
  const plano = planejarRotulosDosPinos(medir, cena([atencao, cinzaEsq, cinzaDir]), null, { mostrarIdade: true, agora: new Date() }, [])
  const a = plano.get('a')!
  assert.ok(a, 'a cidade em atenção tem rótulo mesmo cercada de pinos cinzas')
  for (const id of ['c1', 'c2']) {
    const r = plano.get(id)
    if (r) assert.equal(colide(r.caixa, [bolinha(atencao), bolinha(id === 'c1' ? cinzaDir : cinzaEsq)]), false, `"sem leitura" de ${id} cobriu um pino`)
  }
  // Com um pino COLORIDO no mesmo lugar, o rótulo não pode cobri-lo: procura outra posição.
  const alerta = pino('b', 230, 135, { faixa: 'alerta', nivel: 6.1, medidoEm: new Date() })
  const plano2 = planejarRotulosDosPinos(medir, cena([atencao, cinzaEsq, alerta]), null, { mostrarIdade: true, agora: new Date() }, [])
  for (const [id, r] of plano2) {
    for (const q of [atencao, cinzaEsq, alerta]) {
      if (q.cidade.id === id || q.faixa === 'sem-dado') continue
      assert.equal(colide(r.caixa, [bolinha(q)]), false, `o rótulo de ${id} cobre o pino colorido de ${q.cidade.id}`)
    }
  }
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
  const plano = planejarRotulosDosPinos(medir, c, null, {}, ocupada)
  // A cidade cede o lugar de cima e vai para baixo do pino — nunca por cima da barragem.
  const taio = plano.get('taio')
  if (taio) assert.equal(colide(taio.caixa, [ocupada[0]!]), false, '"Taió" por cima da barragem de novo')
  // Longe do rótulo já colocado, cabe no lugar de sempre.
  const longe = planejarRotulosDosPinos(medir, cena([pino('taio', 60, 280)]), null, {}, [ocupada[0]!]).get('taio')!
  assert.equal(longe.baseY, 280 - 9)
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

  // Um pino colado no chip não escreve por cima dele: acha outra posição ou some.
  const colado = cena([pino('itajai', CENA_LARGURA - 40, chip.y1 + 12)])
  const r = planejarRotulosDosPinos(medir, colado, null, {}, [chip]).get('itajai')
  if (r) assert.equal(colide(r.caixa, [chip]), false, 'rótulo de Itajaí por baixo do chip da maré')
  const longe = cena([pino('itajai', 100, 250)])
  assert.equal(planejarRotulosDosPinos(medir, longe, null, {}, [chip]).size, 1)
})

test('cena sem mar não inventa chip', () => {
  assert.equal(caixaDaEtiquetaMare(medir, { mar: null, largura: CENA_LARGURA } as never), null)
})



/**
 * PINO FORA DA TELA NÃO TEM RÓTULO.
 *
 * Capturas do Jefferson de 06/09/2026, mapa aproximado em Itajaí: "Ascurra",
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

/**
 * 14/09/2026, captura do Jefferson: o rótulo de Ituporanga (alerta, FAIXA
 * ESTADUAL) tomou o lugar do de Rio do Sul (atenção, COTA MUNICIPAL) e ainda
 * ficou em cima do pino de Rio do Sul. Duas regras nascem daqui.
 */
test('municipal manda também na disputa por espaço: estadual perde para a municipal vizinha', () => {
  const rioDoSul = pino('rio-do-sul', 300, 100, { faixa: 'atencao', origemFaixa: 'municipal', nivel: 5.33, medidoEm: new Date() })
  const ituporanga = pino('ituporanga', 300, 118, { faixa: 'alerta', origemFaixa: 'estadual',
    nivelBruto: { cidade: 'ituporanga', estacao: 'SDC-SC Ituporanga', nivelBrutoM: 3.44, medidoEm: new Date(), faixaEstadual: 'alerta' } })
  const plano = planejarRotulosDosPinos(medir, cena([ituporanga, rioDoSul]), null, {}, [])
  const rds = plano.get('rio-do-sul')!
  assert.ok(rds, 'a cidade com cota municipal ganha o rótulo')
  assert.equal(rds.baseY, 100 - 9, 'e fica no lugar de sempre, acima do pino')
  const itu = plano.get('ituporanga')
  const bolinhaRds: Caixa = { x0: 293, y0: 93, x1: 307, y1: 107 }
  if (itu) {
    assert.equal(colide(itu.caixa, [bolinhaRds]), false, 'o rótulo estadual nunca cobre o pino de Rio do Sul')
    assert.equal(colide(itu.caixa, [rds.caixa]), false, 'nem o rótulo de Rio do Sul')
  }
})

test('um rótulo nunca cobre a bolinha de OUTRO pino, seja qual for a gravidade', () => {
  const emergencia = pino('a', 300, 118, { faixa: 'emergencia' })
  const normal = pino('b', 300, 100, { faixa: 'normal' })
  const plano = planejarRotulosDosPinos(medir, cena([emergencia, normal]), null, {}, [])
  const a = plano.get('a')!
  const bolinhaB = { x0: 293, y0: 93, x1: 307, y1: 107 }
  assert.ok(a, 'a emergência ganha rótulo')
  // O lugar de sempre cobriria o pino de B: o rótulo vai para o lado.
  assert.equal(colide(a.caixa, [bolinhaB]), false, 'rótulo de A em cima do pino de B')
  const b = plano.get('b')
  if (b) assert.equal(colide(a.caixa, [b.caixa]), false)
})

test('estadual mais grave ainda ganha de municipal sem dado e de municipal menos grave', () => {
  const cinza = pino('c', 100, 100, { faixa: 'sem-dado', origemFaixa: 'municipal' })
  const estadualAlerta = pino('e', 100, 118, { faixa: 'alerta', origemFaixa: 'estadual' })
  const plano = planejarRotulosDosPinos(medir, cena([cinza, estadualAlerta]), null, {}, [])
  // 'e' vem primeiro na ordem; o lugar de sempre cobriria o pino cinza de 'c',
  // então vai para o lado, e 'c' ainda acha lugar.
  const e = plano.get('e')!
  assert.ok(e)
  assert.equal(colide(e.caixa, [{ x0: 93, y0: 93, x1: 107, y1: 107 }]), false)
  assert.ok(plano.has('c'))
  // Longe um do outro, ambos aparecem — e a ordem de prioridade é a esperada.
  const longe = planejarRotulosDosPinos(medir, cena([cinza, pino('e2', 300, 250, { faixa: 'alerta', origemFaixa: 'estadual' })]), null, {}, [])
  assert.ok(longe.has('c') && longe.has('e2'))
})
