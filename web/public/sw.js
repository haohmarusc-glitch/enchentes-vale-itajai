/*
 * SERVICE WORKER do modo aplicativo (decisão D5, 03/10/2026).
 *
 * O que ele faz, e só isso:
 *  - com rede, busca TUDO na rede, como sem ele (exceto arquivos com hash, que
 *    nunca mudam e vêm do aparelho);
 *  - sem rede, abre o site com a última cópia guardada e mostra o último nível
 *    guardado — com a hora da medição, que o site transforma em "medido há
 *    3 h · não use como nível atual";
 *  - nunca guarda a tela de login do Cloudflare Access (ver `sw-regras.js`);
 *  - desliga sozinho, e apaga o que guardou, se `pwa.json` disser
 *    `"ativo": false` — o interruptor para o dia em que algo der errado.
 *
 * Regras em `sw-regras.js`, testadas por `src/logica/swRegras.test.ts`.
 * Instruções de operação em `docs/PUBLICACAO-E-ACESSO.md`, seção "Modo aplicativo".
 */
/* global SwRegras */
importScripts('./sw-regras.js')

var VERSAO = 'v1'
var CACHE_SITE = 'enchentes-site-' + VERSAO
var CACHE_ARQUIVOS = 'enchentes-arquivos-' + VERSAO
var CACHE_DADOS = 'enchentes-dados-' + VERSAO
var CACHES = [CACHE_SITE, CACHE_ARQUIVOS, CACHE_DADOS]
/** Arquivos com hash de versões antigas se acumulam; guarda só os mais recentes. */
var MAX_ARQUIVOS = 80

var ORIGEM = self.location.origin
/** A página é uma só (rotas no `#`): guardada sempre na mesma chave. */
var CHAVE_PAGINA = new URL('./', self.registration.scope).href

/** Sem rede e sem cópia: ao menos o telefone da Defesa Civil. */
var PAGINA_SEM_REDE =
  '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">' +
  '<meta name="viewport" content="width=device-width, initial-scale=1">' +
  '<title>Sem conexão — Enchentes do Vale do Itajaí</title></head>' +
  '<body style="font-family:system-ui,sans-serif;padding:1.25rem;max-width:32rem;margin:auto;line-height:1.5">' +
  '<p style="background:#a8211a;color:#fff;padding:.75rem 1rem;border-radius:8px">' +
  '<strong>Emergência: ligue 199</strong> (Defesa Civil) ou 193 (Bombeiros).</p>' +
  '<h1 style="font-size:1.3rem">Sem conexão</h1>' +
  '<p>Este aparelho ainda não tem uma cópia do site guardada. Assim que a internet voltar, ' +
  'abra de novo. Este site não é sistema oficial de alerta: acompanhe a Defesa Civil.</p>' +
  '</body></html>'

function comTipo(resposta) {
  return {
    ok: resposta.ok,
    status: resposta.status,
    type: resposta.type,
    redirected: resposta.redirected,
    url: resposta.url,
    tipo: resposta.headers.get('content-type') || '',
  }
}

function guardar(nomeCache, chave, resposta, ehPagina) {
  if (!SwRegras.podeGuardar(comTipo(resposta), ehPagina)) return Promise.resolve()
  return caches.open(nomeCache).then(function (c) {
    return c.put(chave, resposta)
  })
}

function aparar() {
  return caches.open(CACHE_ARQUIVOS).then(function (c) {
    return c.keys().then(function (chaves) {
      var excesso = chaves.length - MAX_ARQUIVOS
      return Promise.all(chaves.slice(0, Math.max(0, excesso)).map(function (k) {
        return c.delete(k)
      }))
    })
  })
}

function comPrazo(promessa, ms) {
  return new Promise(function (resolve, reject) {
    var t = setTimeout(function () {
      reject(new Error('prazo'))
    }, ms)
    promessa.then(
      function (r) {
        clearTimeout(t)
        resolve(r)
      },
      function (e) {
        clearTimeout(t)
        reject(e)
      },
    )
  })
}

/** Lê o interruptor e, se mandar, desliga tudo: caches, registro, e recarrega as abas. */
function conferirInterruptor() {
  return fetch(new URL('./pwa.json', self.registration.scope).href, { cache: 'no-store' })
    .then(function (r) {
      if (!r.ok || r.redirected) return null
      return r.json()
    })
    .then(function (corpo) {
      if (!SwRegras.deveDesligar(corpo)) return
      return Promise.all(CACHES.map(function (n) {
        return caches.delete(n)
      }))
        .then(function () {
          return self.registration.unregister()
        })
        .then(function () {
          return self.clients.matchAll({ type: 'window' })
        })
        .then(function (abas) {
          abas.forEach(function (aba) {
            aba.navigate(aba.url)
          })
        })
    })
    .catch(function () {
      // Sem rede, sessão vencida, JSON quebrado: não decide nada.
    })
}

self.addEventListener('install', function () {
  // Versão nova assume na hora: regra de segurança velha não pode esperar todas as abas fecharem.
  self.skipWaiting()
})

self.addEventListener('activate', function (evento) {
  evento.waitUntil(
    caches
      .keys()
      .then(function (nomes) {
        return Promise.all(
          nomes
            .filter(function (n) {
              return n.indexOf('enchentes-') === 0 && CACHES.indexOf(n) < 0
            })
            .map(function (n) {
              return caches.delete(n)
            }),
        )
      })
      .then(function () {
        return self.clients.claim()
      })
      .then(conferirInterruptor),
  )
})

self.addEventListener('fetch', function (evento) {
  var pedido = evento.request
  var tipo = SwRegras.estrategia(pedido, ORIGEM)
  if (tipo === 'ignorar') return

  if (tipo === 'pagina') {
    evento.respondWith(
      fetch(pedido)
        .then(function (resposta) {
          evento.waitUntil(guardar(CACHE_SITE, CHAVE_PAGINA, resposta.clone(), true).then(conferirInterruptor))
          return resposta
        })
        .catch(function () {
          return caches.match(CHAVE_PAGINA).then(function (copia) {
            return copia || new Response(PAGINA_SEM_REDE, { headers: { 'content-type': 'text/html; charset=utf-8' } })
          })
        }),
    )
    return
  }

  if (tipo === 'imutavel') {
    evento.respondWith(
      caches.match(pedido).then(function (copia) {
        if (copia) return copia
        return fetch(pedido).then(function (resposta) {
          evento.waitUntil(guardar(CACHE_ARQUIVOS, pedido, resposta.clone(), false).then(aparar))
          return resposta
        })
      }),
    )
    return
  }

  var nomeCache = tipo === 'tempo-real' ? CACHE_DADOS : CACHE_SITE
  var rede = fetch(pedido)
  var tentativa = tipo === 'tempo-real' ? comPrazo(rede, SwRegras.PRAZO_TEMPO_REAL_MS) : rede
  evento.respondWith(
    tentativa
      .then(function (resposta) {
        evento.waitUntil(guardar(nomeCache, pedido, resposta.clone(), false))
        return resposta
      })
      .catch(function (erro) {
        if (erro && erro.message === 'prazo') {
          // A rede só demorou: a resposta que chegar depois fica guardada para a próxima vez.
          evento.waitUntil(
            rede
              .then(function (resposta) {
                return guardar(nomeCache, pedido, resposta.clone(), false)
              })
              .catch(function () {}),
          )
        }
        return caches.match(pedido).then(function (copia) {
          if (copia) return copia
          // Sem cópia: se a rede só demorou, espera por ela; se caiu, falha como sem o SW.
          if (erro && erro.message === 'prazo') return rede
          throw erro
        })
      }),
  )
})
