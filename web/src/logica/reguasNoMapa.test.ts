import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { reguasNoMapa, type LeituraDeRegua } from './reguasNoMapa'
import type { EstacaoTempoReal } from '../dados/tipos'

const AGORA = new Date('2026-09-04T02:10:00')
const fresca = (nivel: number): LeituraDeRegua => ({
  titulo: 'T', nivel_m: nivel, medidoEm: new Date('2026-09-04T02:05:00'),
})

const base = (extra: Partial<EstacaoTempoReal>): EstacaoTempoReal => ({
  titulo: 'T', rio: 'itajai-acu', cidade: 'itajai', cotas_m: {}, verificado: true,
  lat: -26.9, lon: -48.66, ...extra,
} as EstacaoTempoReal)

test('régua de MARÉ mostra o número e NUNCA a cor — a regra que protege o alarme', () => {
  /**
   * Nove das onze réguas de Itajaí são de estuário. A fonte registra que essa
   * faixa variou mais de 50 cm em três horas SEM enchente. Pintá-las pela cota
   * deixaria o mapa laranja duas vezes por dia, na maré — e quem vê isso todo
   * dia aprende a ignorar a cor, inclusive no dia em que ela for verdadeira.
   */
  const [r] = reguasNoMapa(
    [base({ cotas_m: { atencao: 1.16, alerta: 1.36 }, alerta_automatico: false,
            motivo_sem_alerta: 'régua no estuário' })],
    [fresca(1.5)], // acima de alerta: pintaria LARANJA sem esta regra
    AGORA,
  )
  assert.equal(r!.faixa, null, 'régua de maré não pode receber cor de perigo')
  assert.equal(r!.nivel, 1.5, 'mas o número tem de aparecer — não é censura, é a cor que sai')
  assert.match(r!.motivoSemCor!, /estuário/)
})

test('régua que PODE avisar recebe a faixa da própria cota', () => {
  const est = base({ titulo: 'T', codigo: 'DC-11', cotas_m: { atencao: 3, alerta: 4, emergencia: 5 } })
  const faixa = (n: number) => reguasNoMapa([est], [fresca(n)], AGORA)[0]!.faixa
  assert.equal(faixa(2.5), 'normal')
  assert.equal(faixa(3.1), 'atencao')
  assert.equal(faixa(4.1), 'alerta')
  assert.equal(faixa(5.1), 'emergencia')
})

test('leitura velha, ausente ou sem cota não vira cor — e o motivo fica escrito', () => {
  const est = base({ cotas_m: { atencao: 3 } })
  const velha = { titulo: 'T', nivel_m: 9, medidoEm: new Date('2026-09-03T02:00:00') }
  assert.equal(reguasNoMapa([est], [velha], AGORA)[0]!.faixa, null)
  assert.equal(reguasNoMapa([est], [], AGORA)[0]!.faixa, null)
  const semCota = reguasNoMapa([base({ cotas_m: {} })], [fresca(9)], AGORA)[0]!
  assert.equal(semCota.faixa, null)
  assert.match(semCota.motivoSemCor!, /sem cota/)
})

test('chave que não é fase de acionamento não pinta — o defeito de 04/09', () => {
  // Mesmo vocabulário fechado do faixaDaCidade: `monitoramento` não é vermelho.
  const est = base({ cotas_m: { monitoramento: 1 } })
  assert.equal(reguasNoMapa([est], [fresca(5)], AGORA)[0]!.faixa, null)
})

test('sem coordenada não entra — não se chuta posição em mapa de enchente', () => {
  assert.deepEqual(
    reguasNoMapa([base({ lat: undefined, lon: undefined })], [fresca(1)], AGORA), [])
  // E pluviômetro não é régua de rio.
  assert.deepEqual(
    reguasNoMapa([base({ tipo: 'pluviometro' })], [fresca(1)], AGORA), [])
  // Régua de OUTRA cidade com coordenada entra: o Monitor é da bacia inteira,
  // e o dia em que outra Defesa Civil publicar coordenada, ela aparece sozinha.
  assert.equal(reguasNoMapa([base({ cidade: 'gaspar' })], [fresca(1)], AGORA).length, 1)
})

test('contra os dados REAIS: as onze de Itajaí entram, e nove não podem pintar', () => {
  const d = JSON.parse(readFileSync(new URL('../../../data/estacoes.json', import.meta.url), 'utf-8'))
  const ets: EstacaoTempoReal[] = d.estacoes_tempo_real
  const rs = reguasNoMapa(ets, [], AGORA)
  assert.equal(rs.length, 11, `esperava 11 réguas com coordenada, vieram ${rs.length}`)
  const deMare = ets.filter((e) => e.alerta_automatico === false)
  assert.equal(deMare.length, 9, 'mudou o número de réguas de estuário no cadastro')
  for (const r of rs) {
    assert.ok(r.motivoSemCor, `${r.codigo} sem leitura tinha de dizer por que não tem cor`)
  }
})
