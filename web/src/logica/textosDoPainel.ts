/**
 * Os textos do painel da cidade no Monitor que dependem de DE ONDE veio a cor (auditoria das cidades
 * sem cor, 06/10/2026). Antes eram fixos e se contradiziam:
 * - "Sem cota de referência cadastrada — a faixa fica cinza" aparecia embaixo de um chip ATENÇÃO da
 *   Defesa Civil de SC (Ibirama, Botuverá…);
 * - a ressalva do nível estadual dizia que ele "não é comparável à faixa de cor deste pino" justamente
 *   quando a cor do pino ERA a classificação estadual;
 * - Itajaí listava as cotas de cada régua e, logo abaixo, "sem cota".
 * E a ressalva afirmava "zero diferente" sem documento que o prove. O que se sabe é que a referência
 * vertical NÃO está validada para as cotas municipais — é isso que o texto diz agora.
 */

/** De onde veio a cor do pino. `varias` é a cidade de várias réguas (Itajaí), sem faixa única. */
export type OrigemDaCor = 'municipal' | 'estadual' | 'varias'

/** O que dizer quando a cidade não tem cota cadastrada — depende de onde a cor veio. */
export function textoSemCota(origem: OrigemDaCor): string {
  if (origem === 'varias') {
    return 'Não há uma faixa única da cidade: cada régua tem as próprias cotas e a própria situação, listadas acima.'
  }
  if (origem === 'estadual') {
    return 'Sem cota municipal cadastrada. A cor do pino é a classificação que a Defesa Civil de SC publica para a estação estadual.'
  }
  return 'Sem cota de referência cadastrada — a faixa fica cinza.'
}

/** A ressalva embaixo do nível bruto da rede estadual. */
export function ressalvaDoBruto(temCotasMunicipais: boolean, corEstadual: boolean): string {
  const partes = ['Nível na régua própria da estação estadual.']
  partes.push(
    temCotasMunicipais
      ? 'A referência vertical não está validada para as cotas municipais acima: este número não se compara com elas.'
      : 'A referência vertical não está validada para cotas municipais.',
  )
  partes.push(
    corEstadual
      ? 'A cor do pino é a classificação que a própria rede publica para esta estação, não uma comparação com cota municipal.'
      : 'Este número não define a cor do pino.',
  )
  return partes.join(' ')
}

/** "Por que está cinza?" na cidade de várias réguas: não falta cota — falta uma faixa única, que não existe. */
export const MOTIVO_VARIAS_REGUAS =
  'A cidade tem várias réguas, cada uma com zero e cotas próprias: não existe uma faixa única da cidade, e a cor não é a média nem a maior delas. A situação de cada régua está abaixo.'

/**
 * A equivalência entre a régua municipal e a estação estadual perto dela (decisão de 06/10/2026). O painel
 * mostrava o nível estadual sem dizer que a ligação não está confirmada (conferência do Jefferson, 06/10).
 */
export function textoEquivalencia(eq: {
  codigo: string
  nome_na_dcsc?: string
  distancia_km?: number
  status: string
  fonte?: string
}): string {
  const nome = eq.nome_na_dcsc ? ` (${eq.nome_na_dcsc})` : ''
  const km = typeof eq.distancia_km === 'number' ? `, a ${eq.distancia_km.toLocaleString('pt-BR')} km` : ''
  if (eq.status === 'confirmada') {
    return `A estação estadual ${eq.codigo}${nome} é a régua das cotas desta cidade${eq.fonte ? ` (fonte: ${eq.fonte})` : ''}.`
  }
  return `Equivalência entre a régua municipal e a estação estadual ${eq.codigo}${nome}${km}: não confirmada. ` +
    'Proximidade não basta: falta documento, código comum ou comparação de referência/zero da régua.'
}
