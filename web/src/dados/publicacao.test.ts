import { test } from 'node:test'
import assert from 'node:assert/strict'
import { alternativaPublicacao, buscarPublicacao } from './publicacao'
import { buscarNivelSc, montarNivelSc } from './nivelSc'

const url = 'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/ultimo_nivel_sc.json'
test('erro 503 do CDN recupera exatamente o arquivo estadual pela API', async () => {
  const vistos: string[] = []
  const corpo = {leituras:[{cidade:'indaial',estacao:'DCSC',nivel_bruto_m:6.73,medido_em:'2026-09-12T18:46:23'}]}
  const resultado = await buscarNivelSc(undefined, async (u, init) => {
    vistos.push(u)
    if (u === url) return new Response('Backend.max_conn reached', {status:503})
    assert.equal(new Headers(init.headers).get('Accept'), 'application/vnd.github.raw+json')
    return Response.json(corpo)
  })
  assert.deepEqual(vistos,[url,alternativaPublicacao(url)])
  assert.equal(resultado.get('indaial')?.nivelBrutoM,6.73)
})
test('falha dos dois caminhos preserva medição e carimbo, sem renovar sua idade', async () => {
  const anterior=montarNivelSc({leituras:[{cidade:'ilhota',estacao:'DCSC',nivel_bruto_m:11.05,medido_em:'2026-09-12T18:46:18'}]})
  const resultado=await buscarNivelSc(undefined,async()=>{throw new Error('offline')},anterior)
  assert.equal(resultado,anterior)
  assert.equal(resultado.get('ilhota')?.medidoEm?.toISOString(),'2026-09-12T21:46:18.000Z')
})
test('fonte configurada não é substituída pela publicação padrão e cancelamento é respeitado', async () => {
  assert.equal(alternativaPublicacao('https://example.com/ultimo.json'),null)
  let chamadas=0
  await assert.rejects(buscarPublicacao('https://example.com/ultimo.json',undefined,async()=>{chamadas++;throw new Error('offline')}))
  assert.equal(chamadas,1)
  const c=new AbortController();c.abort()
  await assert.rejects(buscarPublicacao(url,c.signal,async()=>{chamadas++;return Response.json({})}))
  assert.equal(chamadas,1)
})
test('JSON inválido no CDN usa alternativa; publicação vazia válida limpa o mapa anterior', async () => {
  assert.deepEqual(await buscarPublicacao(url,undefined,async(u)=>u===url?new Response('<html>'):Response.json({leituras:[]})),{leituras:[]})
  const anterior=montarNivelSc({leituras:[{cidade:'x',estacao:'X',nivel_bruto_m:2}]})
  assert.equal((await buscarNivelSc(undefined,async()=>Response.json({leituras:[]}),anterior)).size,0)
})
