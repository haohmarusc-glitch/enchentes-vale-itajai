/**
 * Como cada fonte do rodapé deve aparecer na tela.
 *
 * O rodapé promete: *"cada número na tela mostra sua fonte"*. Oferecer o
 * endereço de um host que não responde quebra essa promessa em silêncio —
 * quem clica descobre sozinho, e descobre no pior momento, que é quando quer
 * conferir um número com o rio subindo.
 *
 * Em 07/09/2026 o `ceops.furb.br` passou a dar tempo de conexão esgotado em
 * `http://` e em `https://`, conferido num navegador comum de dentro do
 * Brasil. Não é queda geral da FURB: o `labgeo.furb.br` responde da mesma
 * rede, no mesmo minuto. O CEOPS estava no rodapé como "acervo de picos", que
 * é exatamente o link que alguém usaria para checar um pico do gráfico.
 *
 * Fonte fora do ar continua APARECENDO — some o link, não a fonte. Apagá-la
 * esconderia de onde o dado veio, que é a informação mais importante da lista.
 */
import type { EstadoDasFontes } from '../dados/tipos'

export type ComoMostrar =
  | { tipo: 'link'; href: string }
  | { tipo: 'texto' }
  | { tipo: 'fora_do_ar'; endereco: string; observado: string }

/** Só `http…` vira link; o resto do `fontes_gerais` já é texto (e-mail, descrição). */
export function comoMostrar(
  chave: string,
  valor: string,
  estado: EstadoDasFontes | undefined,
): ComoMostrar {
  if (!valor.startsWith('http')) return { tipo: 'texto' }
  const registro = estado?.[chave]
  if (foraDoAr(registro)) {
    return { tipo: 'fora_do_ar', endereco: valor, observado: registro.observado }
  }
  return { tipo: 'link', href: valor }
}

/**
 * O bloco `fontes_gerais_estado` mistura chaves de documentação (`_o_que_e`,
 * `_estados`) com os registros de verdade, então cada valor é conferido em vez
 * de suposto. Só `fora_do_ar` tira o link — `exige_cadastro` não: a página
 * abre, e o rodapé não tem como saber se quem lê já tem cadastro.
 */
function foraDoAr(v: unknown): v is { estado: 'fora_do_ar'; observado: string } {
  if (typeof v !== 'object' || v === null) return false
  const r = v as { estado?: unknown; observado?: unknown }
  return r.estado === 'fora_do_ar' && typeof r.observado === 'string'
}
