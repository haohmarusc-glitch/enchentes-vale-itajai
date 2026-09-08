/**
 * A ressalva das cotas chega à TELA — não fica só no JSON.
 *
 * Achado de 08/09/2026, do apontamento do Jefferson: algumas cidades mudam de
 * estado prevendo a descida da água das cidades de cima, mesmo com o nível
 * daqui baixo. Brusque é o caso provado — a Defesa Civil olha
 * Vidal Ramos → Botuverá → Brusque e a tendência, e pode declarar atenção
 * antes de o número de Brusque subir.
 *
 * O projeto JÁ SABIA disso: estava em `cotas_ressalva` desde 07/09. E a tela
 * não lia esse campo, nem nenhum irmão dele — cinco cidades carregavam
 * ressalva no cadastro e ZERO chegavam a quem abre a página. Ressalva que não
 * aparece é ressalva que não existe: quem lê a cor decide sem ela.
 */
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

import estacoes from '../../../data/estacoes.json'

const TELA = readFileSync(new URL('../telas/TelaCidade.tsx', import.meta.url), 'utf8')

type Cidade = { id: string; cotas_aviso_publico?: string; cotas_m?: Record<string, unknown> }

const cidades: Cidade[] = Object.values(
  (estacoes as { rios: Record<string, { cidades: Cidade[] }> }).rios,
).flatMap((r) => r.cidades)

const comAviso = cidades.filter((c) => typeof c.cotas_aviso_publico === 'string')

test('a tela renderiza o aviso — sem isto o campo é decoração no JSON', () => {
  assert.match(TELA, /cidade\.cotas_aviso_publico/)
})

test('o aviso vem ANTES da lista de cotas, não como rodapé', () => {
  const iAviso = TELA.indexOf('cotas_aviso_publico')
  const iLista = TELA.indexOf('Cotas de referência, na régua daqui')
  assert.ok(iAviso > 0 && iLista > 0)
  assert.ok(iAviso < iLista, 'o aviso ficou depois dos números — vira rodapé')
})

test('Brusque tem o aviso, e ele diz que a decisão olha rio acima', () => {
  const brusque = cidades.find((c) => c.id === 'brusque')
  assert.ok(brusque?.cotas_aviso_publico, 'Brusque perdeu o aviso')
  const texto = brusque.cotas_aviso_publico as string
  assert.match(texto, /Vidal Ramos/)
  assert.match(texto, /Botuver/)
  assert.match(texto, /antes/i)
})

test('as duas cidades sem cor por régua alheia dizem por quê', () => {
  for (const id of ['ituporanga', 'vidal-ramos']) {
    const c = cidades.find((x) => x.id === id)
    assert.ok(c?.cotas_aviso_publico, `${id} perdeu o aviso`)
    assert.match(c.cotas_aviso_publico as string, /outra régua|Salseiro/i)
    assert.equal(
      Object.keys(c.cotas_m ?? {}).length,
      0,
      `${id} ganhou cota: reveja o aviso, que diz que a tela não pinta cor`,
    )
  }
})

test('o aviso é curto — em cheia ninguém lê parágrafo de auditoria', () => {
  for (const c of comAviso) {
    const texto = c.cotas_aviso_publico as string
    assert.ok(
      texto.length <= 420,
      `${c.id}: aviso com ${texto.length} caracteres. Se precisa de mais, o lugar é ` +
        '`cotas_ressalva`, que é o registro interno.',
    )
  }
})

test('o aviso público não despeja o texto interno', () => {
  // Os campos internos citam campos, arquivos e datas de auditoria. Se um deles
  // vazar para a tela, a pessoa recebe prosa de projeto no meio de uma cheia.
  for (const c of comAviso) {
    const texto = c.cotas_aviso_publico as string
    for (const marca of ['cotas_m', 'transito.json', 'docs/', '.json', '`']) {
      assert.ok(!texto.includes(marca), `${c.id}: o aviso público cita "${marca}"`)
    }
  }
})

test('Itajaí: a tela não diz mais "não tem cota" em cima das onze escalas', () => {
  // Até 08/09/2026 a página se desmentia: mostrava o painel das onze réguas com
  // as escalas de cada uma e, logo abaixo, "esta cidade ainda não tem cota de
  // acionamento... o site não a pinta". As duas metades eram falsas para Itajaí.
  const iRamo = TELA.indexOf('reguas.length > 0 ?')
  assert.ok(iRamo > 0, 'sumiu o ramo que trata cidade sem cota MAS com réguas')
  const iSemCota = TELA.indexOf('ainda não tem cota de acionamento')
  assert.ok(iRamo < iSemCota, 'o caso das réguas tem de ser testado ANTES do "sem cota"')
  assert.match(TELA, /A cor sai da régua/)
})

test('Itajaí traz o aviso da foz: a decisão vem do rio acima', () => {
  const itajai = cidades.filter((c) => c.id === 'itajai')
  assert.equal(itajai.length, 2, 'Itajaí aparece nos dois rios — os dois precisam do aviso')
  for (const c of itajai) {
    assert.ok(c.cotas_aviso_publico, 'Itajaí perdeu o aviso da foz')
    assert.match(c.cotas_aviso_publico as string, /Blumenau/)
    assert.match(c.cotas_aviso_publico as string, /correnteza/i)
  }
})

test('nenhuma cota de Itajaí virou 7,15 m — aquilo é a régua de Blumenau', () => {
  // O evento é datado por um nível de OUTRA cidade. Copiá-lo para cá seria o
  // erro que este projeto persegue: metro de uma régua vestido de outra.
  for (const c of cidades.filter((x) => x.id === 'itajai')) {
    assert.deepEqual(Object.keys(c.cotas_m ?? {}), [], 'Itajaí ganhou cota de cidade')
  }
})
