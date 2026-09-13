/** Alternativa para falhas do CDN raw: lê o MESMO arquivo e branch pela API pública. */
export type TransportePublicacao = (url: string, init: RequestInit) => Promise<Response>

export function alternativaPublicacao(url: string): string | null {
  const prefixo = 'https://raw.githubusercontent.com/haohmarusc-glitch/enchentes-vale-itajai/tempo-real/'
  if (!url.startsWith(prefixo)) return null
  const arquivo = url.slice(prefixo.length)
  if (!/^[a-z0-9_-]+\.json$/.test(arquivo)) return null
  return `https://api.github.com/repos/haohmarusc-glitch/enchentes-vale-itajai/contents/${arquivo}?ref=tempo-real`
}

export async function buscarPublicacao(
  url: string,
  sinal?: AbortSignal,
  transporte: TransportePublicacao = (u, i) => fetch(u, i),
): Promise<unknown> {
  const alternativa = alternativaPublicacao(url)
  for (const destino of alternativa ? [url, alternativa] : [url]) {
    if (sinal?.aborted) throw new Error('Busca cancelada')
    const controle = new AbortController()
    const cancelar = () => controle.abort()
    sinal?.addEventListener('abort', cancelar, { once: true })
    const limite = setTimeout(cancelar, 3000)
    try {
      const resposta = await transporte(destino, {
        cache: 'no-store', signal: controle.signal,
        ...(destino === alternativa ? { headers: { Accept: 'application/vnd.github.raw+json' } } : {}),
      })
      if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`)
      return await resposta.json()
    } catch (erro) {
      if (!alternativa || destino === alternativa || sinal?.aborted) throw erro
    } finally {
      clearTimeout(limite)
      sinal?.removeEventListener('abort', cancelar)
    }
  }
  throw new Error('Publicação indisponível')
}
