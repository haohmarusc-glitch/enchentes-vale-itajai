/**
 * Onde "Minha rua alaga?" leva em Itajaí (04/10/2026).
 *
 * Itajaí não tem cota por rua levantada: o que responde parte da pergunta é o
 * mapa das manchas de nove enchentes (1983–2015), na tela da foz. O botão levava
 * só a `/itajai`, que abria no topo — o mapa ficava várias telas abaixo, ainda
 * fechado, e no celular o clique parecia apenas mexer a tela. Agora o endereço
 * pede a seção, e a tela abre o mapa e rola até ele.
 */
export const SECAO_MANCHAS = 'manchas'

export const ROTA_MANCHAS_ITAJAI = `/itajai?secao=${SECAO_MANCHAS}`

/** O endereço pediu a seção do mapa das manchas? (`?secao=manchas`) */
export function pedeManchas(busca: string | URLSearchParams): boolean {
  const p = typeof busca === 'string' ? new URLSearchParams(busca) : busca
  return p.get('secao') === SECAO_MANCHAS
}
