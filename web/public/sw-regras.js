/*
 * REGRAS DO MODO APLICATIVO (decisão D5, 03/10/2026) — o que o service worker
 * guarda no aparelho e de que jeito busca cada coisa.
 *
 * Arquivo à parte, sem dependência de navegador, para o teste
 * (`src/logica/swRegras.test.ts`) carregar as MESMAS funções que o `sw.js` usa.
 *
 * Três regras de segurança moram aqui:
 *  1. REDE PRIMEIRO para a página e para o nível ao vivo. O aparelho só serve
 *     o que guardou quando a rede falha — e o número guardado sai com a hora da
 *     medição, que o site já transforma em "medido há 3 h · não use como nível
 *     atual". Guardar nunca rejuvenesce leitura.
 *  2. NUNCA GUARDAR a tela de login do Cloudflare Access. Com a sessão vencida,
 *     o site responde com um desvio para `*.cloudflareaccess.com`; guardado,
 *     esse desvio viraria "o site" para sempre naquele aparelho.
 *  3. Os arquivos com hash no nome (`assets/index-AbC123.js`) nunca mudam de
 *     conteúdo: esses podem vir do aparelho primeiro, e economizam a rede ruim.
 */
;(function (global) {
  /** O branch que o coletor publica, pelo CDN e pela API (a alternativa do site). */
  var PREFIXOS_TEMPO_REAL = [
    'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/',
    'https://api.github.com/repos/haohmarusc-glitch/enchentes-vale-itajai/contents/',
  ]

  /** Nome com hash do Vite: `nome-<8+ caracteres>.ext` dentro de `assets/`. */
  var ASSET_COM_HASH = /\/assets\/[^/]+-[A-Za-z0-9_-]{8,}\.(?:js|css|woff2?|png|svg|jpg|webp|json)$/

  function hostDe(url) {
    try {
      return new URL(url).host
    } catch (e) {
      return ''
    }
  }

  /**
   * Como buscar um pedido:
   *  - 'pagina'      → rede primeiro, cópia guardada só sem rede;
   *  - 'imutavel'    → do aparelho primeiro (arquivo com hash);
   *  - 'site'        → rede primeiro (demais arquivos do próprio site);
   *  - 'tempo-real'  → rede primeiro, com prazo curto, cópia guardada sem rede;
   *  - 'ignorar'     → o service worker não se mete (mapas, outros sites,
   *                    pedidos que não são GET).
   */
  function estrategia(pedido, origemDoSite) {
    if (pedido.method !== 'GET') return 'ignorar'
    var url = pedido.url
    if (pedido.mode === 'navigate') return 'pagina'
    for (var i = 0; i < PREFIXOS_TEMPO_REAL.length; i++) {
      if (url.indexOf(PREFIXOS_TEMPO_REAL[i]) === 0) {
        // Só a publicação do coletor; o resto da API do GitHub não é do site.
        return i === 0 || /\?ref=tempo-real$/.test(url) ? 'tempo-real' : 'ignorar'
      }
    }
    if (url.indexOf(origemDoSite + '/') !== 0) return 'ignorar'
    // O interruptor de desligar nunca vem do aparelho.
    if (/\/pwa\.json(?:\?|$)/.test(url)) return 'ignorar'
    if (ASSET_COM_HASH.test(url.split('?')[0])) return 'imutavel'
    return 'site'
  }

  /**
   * Esta resposta pode ser guardada no aparelho?
   * `resposta` precisa ter: ok, status, type, redirected, url e o tipo de
   * conteúdo em `tipo`.
   */
  function podeGuardar(resposta, ehPagina) {
    if (!resposta || !resposta.ok || resposta.status !== 200) return false
    // Desvio (sessão do Access vencida) e resposta opaca: nunca.
    if (resposta.redirected) return false
    if (resposta.type === 'opaqueredirect' || resposta.type === 'opaque' || resposta.type === 'error') return false
    if (/(^|\.)cloudflareaccess\.com$/.test(hostDe(resposta.url))) return false
    var tipo = String(resposta.tipo || '').toLowerCase()
    // Um JS, CSS ou JSON que chega como HTML é a tela de login, não o arquivo.
    if (!ehPagina && tipo.indexOf('text/html') === 0) return false
    if (ehPagina && tipo && tipo.indexOf('text/html') !== 0) return false
    return true
  }

  /** O interruptor `pwa.json` desliga o modo aplicativo só com `"ativo": false` explícito. */
  function deveDesligar(corpo) {
    return !!corpo && typeof corpo === 'object' && corpo.ativo === false
  }

  global.SwRegras = {
    estrategia: estrategia,
    podeGuardar: podeGuardar,
    deveDesligar: deveDesligar,
    /** Prazo da rede para o nível ao vivo, abaixo dos 3 s em que o site desiste. */
    PRAZO_TEMPO_REAL_MS: 2500,
  }
})(typeof self !== 'undefined' ? self : globalThis)
