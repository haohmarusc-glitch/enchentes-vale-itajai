import { strict as assert } from 'node:assert'
import { test } from 'node:test'
import { avisoDeEncosta } from './encosta'
import enchentes from '../../../data/enchentes.json'

type Evento = { rio: string; cidade: string; data: string; pico_m: number; nota?: string }
const eventos = (enchentes as { eventos: Evento[] }).eventos

const pontos = (cidade: string) =>
  eventos
    .filter((e) => e.cidade === cidade && typeof e.pico_m === 'number')
    .map((e) => ({ data: e.data, pico: e.pico_m, ...(e.nota ? { nota: e.nota } : {}) }))

test('o aviso geral aparece em qualquer lista com mais de um ponto', () => {
  const a = avisoDeEncosta([
    { data: '1983-07-09', pico: 15.34 },
    { data: '1984-08-07', pico: 15.46 },
  ])
  assert.ok(a, 'deveria haver aviso')
  assert.match(a.geral, /deslizamento não sobe régua/)
  // Sem nota de encosta, não se inventa exemplo.
  assert.equal(a.exemplo, null)
})

test('lista com menos de dois pontos não recebe aviso — não há ranking que engane', () => {
  assert.equal(avisoDeEncosta([]), null)
  assert.equal(avisoDeEncosta([{ data: '2008-11-24', pico: 11.52, nota: 'deslizamentos' }]), null)
})

test('2008 em Blumenau vira o exemplo, com a posição contada nos dados reais', () => {
  const a = avisoDeEncosta(pontos('blumenau'))
  assert.ok(a?.exemplo, 'Blumenau deveria produzir exemplo')
  assert.equal(a.exemplo.data, '2008-11-24')
  assert.equal(a.exemplo.pico, 11.52)
  // O número que dá o susto: dezenas de enchentes marcaram MAIS ALTO que a
  // mais letal da história do Vale. Se a série mudar, este teste muda junto —
  // o que se trava é que existem muitas acima, não o valor exato.
  assert.ok(
    a.exemplo.acima >= 10,
    `esperava muitas enchentes acima de 2008, achei ${a.exemplo.acima}`,
  )
  assert.equal(a.exemplo.posicao, a.exemplo.acima + 1)
})

test('acha a nota sem depender de acento ou caixa', () => {
  const a = avisoDeEncosta([
    { data: '1984-08-07', pico: 15.46 },
    { data: '2008-11-24', pico: 11.52, nota: 'As mortes vieram sobretudo dos DESLIZAMENTOS.' },
  ])
  assert.equal(a?.exemplo?.data, '2008-11-24')
})

test('evento de encosta que TAMBÉM é o pico mais alto não vira exemplo', () => {
  // Aí não há inversão a denunciar: a ordenação não está enganando ninguém, e
  // apontá-lo confundiria em vez de esclarecer. O aviso geral continua.
  const a = avisoDeEncosta([
    { data: '2008-11-24', pico: 20.0, nota: 'deslizamentos' },
    { data: '1984-08-07', pico: 15.46 },
  ])
  assert.ok(a)
  assert.equal(a.exemplo, null)
  assert.match(a.geral, /deslizamento não sobe régua/)
})

test('a nota de 2008 continua no dado — o aviso lê a fonte, não inventa', () => {
  const oitoOito = eventos.find((e) => e.cidade === 'blumenau' && e.data === '2008-11-24')
  assert.ok(oitoOito, 'o registro de 2008 em Blumenau sumiu do enchentes.json')
  assert.match(String(oitoOito.nota), /deslizamento/i)
})
