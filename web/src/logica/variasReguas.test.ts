import { test } from 'node:test'
import assert from 'node:assert/strict'
import { maisCritica, parear } from './variasReguas'
import type { LeituraComRegua } from './variasReguas'
import type { ReguaComCota } from './reguas'
import type { LeituraAoVivo } from '../dados/tempoReal'

function leitura(estacao: string, nivel: number): LeituraAoVivo {
  return {
    estacao, rio: 'itajai-mirim', cidade: 'itajai',
    nivel_m: nivel, medidoEm: new Date('2026-08-31T18:00:00'),
  } as LeituraAoVivo
}

function regua(titulo: string, cotas: [string, number][]): ReguaComCota {
  return {
    id: titulo.split(' ')[0]!, titulo, nome: titulo, cotas,
    alertaAutomatico: true, motivoSemAlerta: null, referencia: 'régua',
    rio: 'itajai-mirim', fonteCotas: null,
  }
}

// Os números reais de Itajaí em 31/08/2026.
const DC10 = 'DC-10 Rio Itajaí-Mirim – Bairro Limoeiro'
const DC03 = 'DC-03 Rio Itajaí-Mirim (canal retificado) - Captação SEMASA'

test('cada leitura casa com a régua dela, pelo título exato', () => {
  const p = parear(
    [leitura(DC10, 6.75), leitura(DC03, 1.39)],
    [regua(DC10, [['atencao', 8], ['alerta', 9]]), regua(DC03, [['atencao', 1.2]])],
  )
  assert.equal(p[0]!.regua?.titulo, DC10)
  assert.equal(p[1]!.regua?.titulo, DC03)
})

test('a cota comparada é a DA RÉGUA, não a de outra', () => {
  // O caso que justifica tudo: 6,75 m é "abaixo de tudo" na DC-10, que usa
  // 8/9/10 m, e seria alarme numa régua de estuário, que usa pouco mais de 1 m.
  const p = parear(
    [leitura(DC10, 6.75), leitura(DC03, 1.39)],
    [regua(DC10, [['atencao', 8], ['alerta', 9]]), regua(DC03, [['atencao', 1.2]])],
  )
  assert.equal(p[0]!.cota, null, 'DC-10 a 6,75 não alcançou a cota dela, de 8 m')
  assert.equal(p[1]!.cota?.chave, 'atencao', 'DC-03 a 1,39 passou da cota dela, de 1,20 m')
})

test('a cota é a MAIS ALTA alcançada, não a primeira', () => {
  const p = parear([leitura(DC10, 9.5)],
                   [regua(DC10, [['atencao', 8], ['alerta', 9], ['emergencia', 10]])])
  assert.equal(p[0]!.cota?.chave, 'alerta')
})

test('leitura sem régua cadastrada não some da tela', () => {
  // É nível medido de verdade, só sem cota com que comparar.
  const p = parear([leitura('Estação Nova', 2.5)], [])
  assert.equal(p.length, 1)
  assert.equal(p[0]!.regua, null)
  assert.equal(p[0]!.cota, null)
})

test('nunca casa por prefixo de código', () => {
  // "DC-1" não pode casar com "DC-10". Prefixo casa errado calado.
  const p = parear([leitura(DC10, 6.75)], [regua('DC-1 Outra Régua', [['atencao', 2]])])
  assert.equal(p[0]!.regua, null)
})

test('a régua em destaque é a mais perto da PRÓPRIA cota, não a de maior número', () => {
  // A DC-10 marca 6,75 m e está 1,25 m abaixo da cota dela.
  // A DC-03 marca 1,39 m e já passou da dela. É esta que importa.
  const p = parear(
    [leitura(DC10, 6.75), leitura(DC03, 1.39)],
    [regua(DC10, [['atencao', 8]]), regua(DC03, [['atencao', 1.2]])],
  )
  assert.equal(maisCritica(p)?.leitura.estacao, DC03)
})

test('sem nenhuma cota não há destaque nenhum', () => {
  // Eleger pelo número seria comparar metros entre zeros diferentes.
  const p = parear([leitura(DC10, 9.9), leitura(DC03, 1.0)], [])
  assert.equal(maisCritica(p), null)
})

test('régua sem cota é ignorada no destaque, mas a com cota vence', () => {
  const p = parear(
    [leitura(DC10, 99), leitura(DC03, 0.1)],
    [regua(DC03, [['atencao', 1.2]])],
  )
  assert.equal(maisCritica(p)?.leitura.estacao, DC03)
})

test('empate não quebra: devolve uma, e é uma das empatadas', () => {
  const p: LeituraComRegua[] = parear(
    [leitura(DC10, 8), leitura(DC03, 1.2)],
    [regua(DC10, [['atencao', 8]]), regua(DC03, [['atencao', 1.2]])],
  )
  const escolhida = maisCritica(p)
  assert.ok(escolhida !== null)
  assert.ok([DC10, DC03].includes(escolhida!.leitura.estacao))
})
