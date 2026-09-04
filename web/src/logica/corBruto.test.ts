import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { COR_BRUTO } from './mapaMotor'

const MOTOR = readFileSync(new URL('./mapaMotor.ts', import.meta.url), 'utf-8')
const MONITOR = readFileSync(new URL('../telas/MonitorBacia.tsx', import.meta.url), 'utf-8')
const CSS = readFileSync(new URL('../telas/MonitorBacia.module.css', import.meta.url), 'utf-8')

/**
 * O violeta do nível BRUTO estadual, e por que ele tem teste.
 *
 * Ele aparecia no mapa e NÃO tinha entrada na legenda: uma cor com significado
 * e sem explicação, que é pior do que não usar cor nenhuma — quem olha inventa
 * um significado, e num mapa de enchente o significado inventado é "perigo".
 *
 * Achado por quem usa o site, olhando a tela, em 04/09/2026.
 */
test('a legenda usa a MESMA cor que o mapa desenha, sem repetir o literal', () => {
  assert.match(MOTOR, /export const COR_BRUTO/, 'o motor tem de exportar a cor')
  assert.match(MONITOR, /COR_BRUTO/, 'a legenda tem de importar a cor, não copiá-la')
  assert.equal(
    MONITOR.includes(COR_BRUTO),
    false,
    `a legenda repete o literal ${COR_BRUTO} em vez de usar COR_BRUTO — ` +
      'duas cópias divergem em silêncio, e a legenda passa a mentir sobre o mapa',
  )
})

test('o violeta fica FORA da escala de faixas — não pode virar grau de perigo', () => {
  // Verde, amarelo, laranja e vermelho são graus. Violeta marca outro TIPO de
  // dado: régua estadual, zero próprio, não comparável às cotas municipais.
  // Se um dia ele coincidir com uma cor de faixa, a distinção morre.
  const faixas = CSS.match(/--[a-z-]*(verde|amarelo|laranja|vermelho|agua)[a-z-]*:\s*([^;]+);/gi) ?? []
  for (const linha of faixas) {
    assert.equal(
      linha.toLowerCase().includes(COR_BRUTO.toLowerCase()),
      false,
      `a cor do bruto colidiu com uma faixa: ${linha}`,
    )
  }
})
