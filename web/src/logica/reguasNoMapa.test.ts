import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { nomeDoLugar, reguasNoMapa, type LeituraDeRegua } from './reguasNoMapa'
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
  // Mesmo vocabulário FECHADO do faixaDaCidade. `seguranca_observada` e
  // `inundacao_historica` são marca de comportamento, não gatilho: não pintam.
  for (const chave of ['seguranca_observada', 'inundacao_historica', 'ativacao_plancon']) {
    const est = base({ cotas_m: { [chave]: 1 } })
    assert.equal(reguasNoMapa([est], [fresca(5)], AGORA)[0]!.faixa, null, chave)
  }
  // `monitoramento` É fase declarada de Plano, e desde 04/09 tem faixa PRÓPRIA
  // — branda, entre normal e atenção. Não vira vermelho, que era o defeito, e
  // também não vira verde, que calaria a fase.
  const taio = base({ cotas_m: { monitoramento: 5, atencao: 7 } })
  assert.equal(reguasNoMapa([taio], [fresca(5.25)], AGORA)[0]!.faixa, 'monitoramento')
  assert.equal(reguasNoMapa([taio], [fresca(4.5)], AGORA)[0]!.faixa, 'normal')
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

test('o rótulo é o nome do LUGAR, não o código', () => {
  /**
   * O mapa rotulava `DC-07 0,32 m`. Ninguém que mora no Portal I sabe o que é
   * DC-07 — e é justamente quem mora ali que precisa ler aquele número.
   */
  assert.equal(nomeDoLugar({ nome_no_plano: 'Ribeirão da Murta - Portal I', titulo: 'x' }), 'Portal I')
  assert.equal(nomeDoLugar({ nome_no_plano: 'Ribeirão da Canhanduba - Rio do Meio', titulo: 'x' }), 'Rio do Meio')
  // Sem hífen, fica o nome inteiro.
  assert.equal(nomeDoLugar({ nome_no_plano: 'Limoeiro', titulo: 'x' }), 'Limoeiro')
  // Sem nome no plano, cai para o código; sem código, para o título. Nunca
  // vazio: ponto sem rótulo no meio de outros dez não se identifica.
  assert.equal(nomeDoLugar({ codigo: 'DC-99', titulo: 'T' }), 'DC-99')
  assert.equal(nomeDoLugar({ titulo: 'T' }), 'T')
  assert.equal(nomeDoLugar({ nome_no_plano: '   ', codigo: 'DC-1', titulo: 'T' }), 'DC-1')
})

test('cada régua leva as cotas DELA, não as da cidade', () => {
  /**
   * Em Itajaí os zeros são diferentes: a DC-01 usa 1,16/1,36/1,56 e a DC-10 usa
   * 8/9/10. Mostrar a cota da cidade ao lado do número de uma régua convidaria
   * exatamente à comparação que a régua de cada uma proíbe.
   */
  const est = base({ cotas_m: { atencao: 1.16, alerta: 1.36 }, alerta_automatico: false })
  const r = reguasNoMapa([est], [fresca(1.2)], AGORA)[0]!
  assert.deepEqual(r.cotas, { atencao: 1.16, alerta: 1.36 })
  // Cota não-numérica não entra: o painel formata metros e um texto viraria NaN.
  const sujo = base({ cotas_m: { atencao: 1.16, nota: 'ver plano' } as never })
  assert.deepEqual(reguasNoMapa([sujo], [], AGORA)[0]!.cotas, { atencao: 1.16 })
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
    // Todas as onze têm nome de lugar no Plano — nenhuma cai para o código.
    assert.ok(r.nome && !/^DC-\d/.test(r.nome), `${r.codigo} ficou rotulada com o código: ${r.nome}`)
    // E cada uma traz as cotas dela — é o que o painel mostra ao ser tocada.
    assert.ok(Object.keys(r.cotas).length >= 3, `${r.codigo} sem as cotas próprias`)
  }
  // Os três dos ribeirões, que são os que o mapa escondia.
  const nomes = rs.map((r) => r.nome)
  for (const esperado of ['Portal I', 'Rio do Meio', 'Bairro Murta']) {
    assert.ok(nomes.includes(esperado), `faltou "${esperado}" — ver nome_no_plano no cadastro`)
  }
})
