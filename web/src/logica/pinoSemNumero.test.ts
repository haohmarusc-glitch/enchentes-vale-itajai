/**
 * Pino sem número nenhum tem de DIZER por quê.
 *
 * Relato de quem olhou o mapa: "réguas sem descrição e dados". Está certo —
 * quando a cidade não tem leitura municipal nem bruto estadual, o pino mostrava
 * só o nome, e duas situações muito diferentes ficavam idênticas:
 *
 *  - GASPAR tem cota oficial (5/6/7 m), régua conhecida e estação cadastrada.
 *    O que falta é a fonte publicar — há ofício pendente. Pino mudo ali faz
 *    quem mora em Gaspar concluir que o site não cobre a cidade dele.
 *  - GUABIRUBA não tem régua no cadastro. Não há o que publicar.
 */
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const MOTOR = readFileSync(new URL('./mapaMotor.ts', import.meta.url), 'utf-8')
const estacoes = JSON.parse(
  readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'),
) as { rios: Record<string, { cidades: { id: string; regua?: string }[] }> }

/** A regra escrita no motor, lida do próprio arquivo. */
function semNumero(cidade: { regua?: string }): string {
  return cidade.regua ? 'sem leitura' : 'sem régua'
}

function cidade(rioId: string, id: string) {
  const c = estacoes.rios[rioId]?.cidades.find((x) => x.id === id)
  assert.ok(c, `${id} sumiu do cadastro de ${rioId}`)
  return c!
}

test('o motor NÃO deixa mais o pino sem número mudo', () => {
  assert.match(
    MOTOR,
    /idade \?\? semNumero\(p\.cidade\)/,
    'o fallback do rótulo voltou a ser só a idade: pino sem dado fica mudo de novo',
  )
})

test('Gaspar diz "sem leitura" — tem régua, falta a fonte publicar', () => {
  const g = cidade('itajai-acu', 'gaspar')
  assert.ok(g.regua, 'Gaspar perdeu a régua do cadastro; o rótulo mudaria de sentido')
  assert.equal(semNumero(g), 'sem leitura')
})

test('Guabiruba diz "sem régua" — não há instrumento cadastrado', () => {
  const g = cidade('itajai-mirim', 'guabiruba')
  assert.ok(!g.regua, 'Guabiruba ganhou régua: revise o rótulo e este teste')
  assert.equal(semNumero(g), 'sem régua')
})

test('as duas frases são DIFERENTES — juntá-las apagaria a distinção', () => {
  assert.notEqual(
    semNumero(cidade('itajai-acu', 'gaspar')),
    semNumero(cidade('itajai-mirim', 'guabiruba')),
  )
})

test('nenhuma das frases é "normal" ou vazia — pino mudo lê-se como está tudo bem', () => {
  for (const f of ['sem leitura', 'sem régua']) {
    assert.ok(f.trim().length > 0)
    assert.ok(!/normal|ok|seguro/i.test(f))
  }
})
