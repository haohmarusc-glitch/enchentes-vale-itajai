/**
 * As regras do modo aplicativo (D5): o que o service worker guarda e como
 * busca. O teste carrega o MESMO `public/sw-regras.js` que o service worker
 * importa, num contexto isolado.
 */
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import vm from 'node:vm'

interface Regras {
  estrategia(pedido: { method: string; url: string; mode?: string }, origem: string): string
  podeGuardar(
    r: { ok: boolean; status: number; type: string; redirected: boolean; url: string; tipo: string } | null,
    ehPagina: boolean,
  ): boolean
  deveDesligar(corpo: unknown): boolean
  PRAZO_TEMPO_REAL_MS: number
}

const codigo = readFileSync(new URL('../../public/sw-regras.js', import.meta.url), 'utf8')
const ctx: { self: { SwRegras?: Regras }; URL: typeof URL } = { self: {}, URL }
vm.runInNewContext(codigo, ctx)
const R = ctx.self.SwRegras!

const SITE = 'https://enchentes.premercadosc.com'
const RAW = 'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/ultimo.json'
const API = 'https://api.github.com/repos/haohmarusc-glitch/enchentes-vale-itajai/contents/ultimo.json?ref=tempo-real'

const resposta = (extra: Partial<Parameters<Regras['podeGuardar']>[0] & object> = {}) => ({
  ok: true,
  status: 200,
  type: 'basic',
  redirected: false,
  url: `${SITE}/`,
  tipo: 'text/html; charset=utf-8',
  ...extra,
})

test('a página é rede primeiro; arquivos com hash vêm do aparelho', () => {
  assert.equal(R.estrategia({ method: 'GET', url: `${SITE}/`, mode: 'navigate' }, SITE), 'pagina')
  assert.equal(R.estrategia({ method: 'GET', url: `${SITE}/assets/index-B9x_k2Lq.js` }, SITE), 'imutavel')
  assert.equal(R.estrategia({ method: 'GET', url: `${SITE}/favicon.svg` }, SITE), 'site')
})

test('o nível ao vivo (CDN e a alternativa pela API) é rede primeiro, com prazo menor que o do site', () => {
  assert.equal(R.estrategia({ method: 'GET', url: RAW }, SITE), 'tempo-real')
  assert.equal(R.estrategia({ method: 'GET', url: API }, SITE), 'tempo-real')
  // O site desiste da busca aos 3 s: o aparelho tem de responder antes.
  assert.ok(R.PRAZO_TEMPO_REAL_MS < 3000)
})

test('o service worker não se mete com mapas, outros sites, POST nem o interruptor', () => {
  assert.equal(R.estrategia({ method: 'GET', url: 'https://tile.openstreetmap.org/1/1/1.png' }, SITE), 'ignorar')
  assert.equal(R.estrategia({ method: 'GET', url: 'https://api.github.com/repos/x/y/issues' }, SITE), 'ignorar')
  assert.equal(R.estrategia({ method: 'POST', url: `${SITE}/` }, SITE), 'ignorar')
  assert.equal(R.estrategia({ method: 'GET', url: `${SITE}/pwa.json` }, SITE), 'ignorar')
})

test('a tela de login do Cloudflare Access nunca é guardada', () => {
  // Sessão vencida: o Access desvia para o domínio dele.
  assert.equal(R.podeGuardar(resposta({ type: 'opaqueredirect', status: 0, ok: false }), true), false)
  assert.equal(R.podeGuardar(resposta({ redirected: true }), true), false)
  assert.equal(
    R.podeGuardar(resposta({ url: 'https://premercadosc.cloudflareaccess.com/cdn-cgi/access/login' }), true),
    false,
  )
  // Um JS que chega como HTML é o login no lugar do arquivo.
  assert.equal(R.podeGuardar(resposta({ url: `${SITE}/assets/index-B9x_k2Lq.js` }), false), false)
})

test('guarda a página e os arquivos normais', () => {
  assert.equal(R.podeGuardar(resposta(), true), true)
  assert.equal(
    R.podeGuardar(resposta({ url: `${SITE}/assets/index-B9x_k2Lq.js`, tipo: 'text/javascript' }), false),
    true,
  )
  assert.equal(R.podeGuardar(resposta({ url: RAW, type: 'cors', tipo: 'text/plain; charset=utf-8' }), false), true)
})

test('erro, resposta opaca e página que não é HTML não são guardados', () => {
  assert.equal(R.podeGuardar(resposta({ ok: false, status: 503 }), true), false)
  assert.equal(R.podeGuardar(resposta({ type: 'opaque', status: 0, ok: false }), false), false)
  assert.equal(R.podeGuardar(resposta({ tipo: 'application/json' }), true), false)
  assert.equal(R.podeGuardar(null, true), false)
})

test('o interruptor só desliga com "ativo": false explícito', () => {
  assert.equal(R.deveDesligar({ ativo: false }), true)
  assert.equal(R.deveDesligar({ ativo: true }), false)
  assert.equal(R.deveDesligar({}), false)
  assert.equal(R.deveDesligar(null), false)
  assert.equal(R.deveDesligar('<html>login</html>'), false)
})

test('o interruptor publicado está ligado', () => {
  const pwa = JSON.parse(readFileSync(new URL('../../public/pwa.json', import.meta.url), 'utf8'))
  assert.equal(pwa.ativo, true)
})
