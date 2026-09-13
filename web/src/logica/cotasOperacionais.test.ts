import assert from 'node:assert/strict'
import { test } from 'node:test'
import cadastro from '../../../data/estacoes.json'
import type { Cidade } from '../dados/tipos'
import { primeiraCota, cotaAlcancada, proximaCotaEntre, faixaDaCidade } from './tempoReal'
import { cotasOperacionais } from './cotasOperacionais'

const cidades = cadastro.rios['itajai-acu'].cidades as unknown as Cidade[]
test('marcas documentais nunca viram primeira cota, próxima cota ou cota ultrapassada', () => {
  for (const chave of ['seguranca_observada', 'ativacao_plancon', 'inundacao_historica']) {
    const cidade = { ...cidades[0]!, cotas_m: { [chave]: 9.2 } }
    assert.equal(primeiraCota(cidade), null)
    assert.equal(cotaAlcancada(cidade, 9.3), null)
    assert.equal(proximaCotaEntre(Object.entries(cidade.cotas_m), 9), null)
    assert.deepEqual(cotasOperacionais(cidade.cotas_m), [])
  }
})
test('Taió usa monitoramento como primeira fase em todos os painéis', () => {
  const taio = cidades.find(c => c.id === 'taio')!
  assert.deepEqual(primeiraCota(taio), { chave: 'monitoramento', valor: 5 })
  assert.deepEqual(cotasOperacionais(taio.cotas_m)[0], ['monitoramento', 5])
})
test('Ibirama sem vínculo não classifica leitura; Apiúna existe sem fonte ativada', () => {
  const agora = new Date()
  const ibirama = cidades.find(c => c.id === 'ibirama')!
  assert.equal(faixaDaCidade(ibirama, { nivel_m: 4.04, medidoEm: agora }, false, agora), 'sem-dado')
  assert.equal(primeiraCota(ibirama), null)
  const apiuna = cidades.find(c => c.id === 'apiuna')!
  assert.ok(apiuna)
  assert.deepEqual(apiuna.cotas_m, {})
  assert.equal(apiuna.codigo_ana, null)
  assert.equal(apiuna.codigo_dcsc, null)
})
test('limiares não finitos são recusados', () => {
  assert.deepEqual(cotasOperacionais({ atencao: NaN, alerta: Infinity }), [])
})

