/**
 * Roda antes de todo pedido ao site. Só faz uma coisa: anota o acesso de quem abriu uma página
 * (`registrarAcesso`, em `api/acessos.ts`), DEPOIS de a resposta sair — nunca atrasa nem derruba o site.
 */
import { registrarAcesso, type Ambiente } from './api/acessos'

interface Contexto {
  request: Request
  env: Ambiente
  next: () => Promise<Response>
  waitUntil: (p: Promise<unknown>) => void
}

export const onRequest = async (ctx: Contexto): Promise<Response> => {
  const resposta = await ctx.next()
  try {
    ctx.waitUntil(registrarAcesso(ctx.request, ctx.env).catch(() => undefined))
  } catch {
    // sem waitUntil (ambiente de teste): segue sem registrar
  }
  return resposta
}
