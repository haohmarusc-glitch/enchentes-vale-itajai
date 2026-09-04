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
// A FUNÇÃO DE VERDADE, não uma cópia dela. Este arquivo já reimplementou a
// regra aqui dentro, e foi por isso que passou verde enquanto o pino de ITAJAÍ
// dizia "sem régua" numa cidade com onze — a cópia olhava só `cidade.regua`, e
// as réguas de Itajaí moram em `estacoes_tempo_real`. Teste que copia a regra
// testa a cópia.
import { semNumero } from './mapaMotor'
import type { Cidade } from '../dados/tipos'

const g = globalThis as unknown as { getComputedStyle?: unknown }
g.getComputedStyle = () => ({ getPropertyValue: () => '' })

const MOTOR = readFileSync(new URL('./mapaMotor.ts', import.meta.url), 'utf-8')
const estacoes = JSON.parse(
  readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf8'),
) as {
  rios: Record<string, { cidades: { id: string; regua?: string }[] }>
  estacoes_tempo_real: { cidade?: string | null; tipo?: string }[]
}

function cidade(rioId: string, id: string) {
  const c = estacoes.rios[rioId]?.cidades.find((x) => x.id === id)
  assert.ok(c, `${id} sumiu do cadastro de ${rioId}`)
  return c! as unknown as Cidade
}

/**
 * A MESMA regra que `dados/carregar` aplica, sobre os MESMOS dados reais.
 *
 * Reimplementada aqui só porque o alias `@dados` do `carregar` existe apenas na
 * configuração do Vite e o runner é o node — é o mesmo motivo pelo qual
 * `reguas.test.ts` lê o JSON do disco. A regra em si (`semNumero`) vem
 * importada do motor, que é o que faltava antes.
 */
const temRegua = (cidadeId: string): boolean =>
  estacoes.estacoes_tempo_real.some((e) => e.tipo !== 'pluviometro' && e.cidade === cidadeId)

test('o motor NÃO deixa mais o pino sem número mudo', () => {
  assert.match(
    MOTOR,
    /idade \?\? semNumero\(p\.cidade, opcoes\.temRegua\)/,
    'o fallback do rótulo voltou a ser só a idade (ou perdeu o `temRegua`): ' +
      'pino sem dado fica mudo de novo, ou volta a dizer "sem régua" em Itajaí',
  )
})

test('quem desenha pino PASSA o temRegua — senão o rótulo volta a mentir', () => {
  // A regra certa no motor não basta: `temRegua` tem valor padrão conservador
  // (`() => false`), então um componente que esqueça de passá-lo volta a dizer
  // "sem régua" em Itajaí, e sem erro de tipo nenhum. A falsificação de 04/09
  // mostrou exatamente isso passando verde.
  for (const arquivo of ['../telas/MonitorBacia.tsx', '../componentes/MapaRios.tsx']) {
    const fonte = readFileSync(new URL(arquivo, import.meta.url), 'utf-8')
    assert.ok(
      fonte.includes('temRegua: temReguaCadastrada'),
      `${arquivo} desenha pinos sem passar temRegua: o pino de Itajaí volta a ` +
        'dizer "sem régua" numa cidade com onze',
    )
  }
})

test('Gaspar diz "sem leitura" — tem régua, falta a fonte publicar', () => {
  const g = cidade('itajai-acu', 'gaspar')
  assert.ok(g.regua, 'Gaspar perdeu a régua do cadastro; o rótulo mudaria de sentido')
  assert.equal(semNumero(g, temRegua), 'sem leitura')
})

test('ITAJAÍ diz "sem leitura" — tem ONZE réguas, não zero', () => {
  // O defeito que este teste não pegava, visto no mapa em 04/09/2026: o pino da
  // foz dizia "sem régua" na cidade com mais réguas da bacia. A cópia local da
  // regra que vivia neste arquivo olhava só `cidade.regua`, e as onze réguas de
  // Itajaí moram em `estacoes_tempo_real`.
  const quantas = estacoes.estacoes_tempo_real.filter(
    (e) => e.cidade === 'itajai' && e.tipo !== 'pluviometro',
  ).length
  assert.ok(quantas >= 10, `Itajaí tem ${quantas} réguas no cadastro — o teste virou vazio`)

  for (const rioId of ['itajai-acu', 'itajai-mirim']) {
    const c = cidade(rioId, 'itajai')
    assert.ok(!c.regua, 'Itajaí ganhou campo `regua` na cidade; revise este teste')
    assert.equal(
      semNumero(c, temRegua),
      'sem leitura',
      `o pino de Itajaí em /${rioId} voltaria a dizer "sem régua" numa cidade com ${quantas}`,
    )
  }
})

test('Guabiruba diz "sem régua" — não há instrumento cadastrado', () => {
  const g = cidade('itajai-mirim', 'guabiruba')
  assert.ok(!g.regua, 'Guabiruba ganhou régua: revise o rótulo e este teste')
  assert.ok(!temRegua('guabiruba'), 'Guabiruba ganhou régua em estacoes_tempo_real')
  assert.equal(semNumero(g, temRegua), 'sem régua')
})

test('as duas frases são DIFERENTES — juntá-las apagaria a distinção', () => {
  assert.notEqual(
    semNumero(cidade('itajai-acu', 'gaspar'), temRegua),
    semNumero(cidade('itajai-mirim', 'guabiruba'), temRegua),
  )
})

test('nenhuma das frases é "normal" ou vazia — pino mudo lê-se como está tudo bem', () => {
  for (const f of ['sem leitura', 'sem régua']) {
    assert.ok(f.trim().length > 0)
    assert.ok(!/normal|ok|seguro/i.test(f))
  }
})
