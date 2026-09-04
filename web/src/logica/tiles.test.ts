import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { enquadrar, projetar } from './mapaCanvas'
import {
  FUNDOS,
  LADO_TILE,
  latDoTile,
  lonDoTile,
  tileX,
  tileY,
  tilesVisiveis,
  urlDoTile,
  zoomPara,
  ehChaveDeFundo,
} from './tiles'

// A bacia inteira, com folga — é o enquadramento que o Monitor usa.
const BACIA = { minLon: -50.0, maxLon: -48.5, minLat: -27.6, maxLat: -26.4 }
const L = 1200
const A = 900
const E = enquadrar(BACIA, L, A, 24)

test('tile e coordenada são inversos um do outro', () => {
  for (const z of [8, 11, 14]) {
    for (const lon of [-50, -49.2, -48.5]) {
      assert.ok(Math.abs(lonDoTile(tileX(lon, z), z) - lon) < 1e-9, `lon ${lon} z${z}`)
    }
    for (const lat of [-27.6, -26.9, -26.4]) {
      assert.ok(Math.abs(latDoTile(tileY(lat, z), z) - lat) < 1e-9, `lat ${lat} z${z}`)
    }
  }
})

test('o zoom deixa o tile com cerca de 256 px, e respeita o teto do provedor', () => {
  const z = zoomPara(E, 19)
  const t = tilesVisiveis(E, L, A, z)
  assert.ok(t.length > 0, 'nenhum tile para a bacia inteira')
  const lados = t.map((x) => x.largura)
  const medio = lados.reduce((a, b) => a + b, 0) / lados.length
  assert.ok(medio > LADO_TILE / 2 && medio < LADO_TILE * 2,
    `tile saiu com ${medio.toFixed(0)} px — longe dos ${LADO_TILE} pretendidos`)
  // O teto é do provedor: passar dele devolve 404, não imagem melhor.
  assert.equal(zoomPara(E, 3), 3)
})

test('O QUE IMPORTA: o fundo alinha com o mapa', () => {
  /**
   * A prova de que tile Mercator e canvas equirretangular batem.
   *
   * Para cada ponto conhecido, o pixel onde o MAPA desenha a cidade tem de cair
   * DENTRO da caixa do tile que geograficamente a contém. Se as duas projeções
   * discordassem, o rio apareceria deslocado do leito na imagem de satélite —
   * e um morador procurando o próprio bairro seria mandado para o lugar errado.
   */
  const z = zoomPara(E, 19)
  const tiles = tilesVisiveis(E, L, A, z)
  const cidades: [string, number, number][] = [
    ['Blumenau', -49.0661, -26.9194],
    ['Itajaí', -48.6619, -26.9077],
    ['Rio do Sul', -49.6433, -27.2144],
    ['Brusque', -48.9106, -27.0977],
  ]
  for (const [nome, lon, lat] of cidades) {
    const [px, py] = projetar(E, [lon, lat])
    const tx = Math.floor(tileX(lon, z))
    const ty = Math.floor(tileY(lat, z))
    const dono = tiles.find((t) => t.x === tx && t.y === ty)
    assert.ok(dono, `${nome}: o tile que a contém não foi pedido`)
    const folga = 1.5 // a curvatura residual medida: ~1,2 px em 900
    assert.ok(
      px >= dono.px - folga && px <= dono.px + dono.largura + folga &&
        py >= dono.py - folga && py <= dono.py + dono.altura + folga,
      `${nome} cai em (${px.toFixed(1)}, ${py.toFixed(1)}) mas o tile dela ocupa ` +
        `(${dono.px.toFixed(1)}, ${dono.py.toFixed(1)}) + ${dono.largura.toFixed(1)}x${dono.altura.toFixed(1)}`,
    )
  }
})

test('o mosaico é contínuo — sem fresta entre tiles vizinhos', () => {
  const z = zoomPara(E, 19)
  const tiles = tilesVisiveis(E, L, A, z)
  const porChave = new Map(tiles.map((t) => [`${t.x},${t.y}`, t]))
  for (const t of tiles) {
    const dir = porChave.get(`${t.x + 1},${t.y}`)
    if (dir) assert.ok(Math.abs(t.px + t.largura - dir.px) < 0.01, 'fresta horizontal')
    const baixo = porChave.get(`${t.x},${t.y + 1}`)
    if (baixo) assert.ok(Math.abs(t.py + t.altura - baixo.py) < 0.01, 'fresta vertical')
  }
})

test('janela absurda não pede milhares de imagens', () => {
  // Numa noite de chuva o navegador não pode travar; sem fundo é melhor que
  // travado, e o mapa desenha igual sem ele.
  assert.deepEqual(tilesVisiveis(E, L, A, 19), [])
})

test('o Esri inverte y e x — errar isso traz tile de outro lugar', () => {
  for (const f of Object.values(FUNDOS)) {
    const u = urlDoTile(f, 111, 222, 12)
    assert.ok(!u.includes('{'), `sobrou marcador em ${u}`)
    const iX = u.indexOf('111')
    const iY = u.indexOf('222')
    if (f.invertido) {
      assert.ok(iY < iX, `${f.nome} está marcado invertido mas a URL põe x antes de y`)
    } else {
      assert.ok(iX < iY, `${f.nome} não está marcado invertido mas a URL põe y antes de x`)
    }
  }
})

test('toda camada declara atribuição — é condição de licença', () => {
  for (const [chave, f] of Object.entries(FUNDOS)) {
    assert.ok(f.atribuicao.trim().length > 0, `${chave} sem atribuição`)
    assert.ok(f.maxZoom > 0)
  }
  assert.equal(ehChaveDeFundo('satelite'), true)
  assert.equal(ehChaveDeFundo('google'), false)
})

test('nenhuma camada do Google — a licença não permite embutir os tiles', () => {
  for (const f of Object.values(FUNDOS)) {
    assert.ok(!/google/i.test(f.url), `${f.nome} aponta para o Google`)
  }
})

test('a TELA mostra a atribuição e ela troca com a camada', () => {
  // Atribuição é condição de licença. Um seletor que troca o fundo e deixa o
  // crédito antigo na tela põe o projeto em desacordo com a licença — e o erro
  // é invisível, porque a tela continua bonita.
  const tela = readFileSync(new URL('../telas/MonitorBacia.tsx', import.meta.url), 'utf-8')
  assert.match(tela, /FUNDOS\[fundo\]\.atribuicao/,
    'a atribuição tem de sair da camada ATIVA, não de um texto fixo')
  for (const f of Object.values(FUNDOS)) {
    assert.equal(tela.includes(f.atribuicao), false,
      `a tela repete o crédito "${f.atribuicao}" em vez de ler de FUNDOS`)
  }
})
