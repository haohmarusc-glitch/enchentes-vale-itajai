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

/**
 * Estações estaduais que SÃO a régua das cotas municipais da cidade: a COMPDEC declarou, ou a medição provou,
 * que as faixas estão na escala da própria estação. Espelho de `REGUAS_COM_COTA_PROPRIA` em
 * `scripts/coleta_estadual_com_cota.py` — o `teste_coleta_estadual_com_cota.py` trava os dois iguais. Nelas a
 * frase genérica "a referência vertical não está validada" seria falsa (Brusque; Rio dos Cedros desde o C29).
 */
export const REGUA_ESTADUAL_DAS_COTAS: Readonly<Record<string, string>> = {
  ascurra: 'DCSC-00003',
  brusque: 'DCSC-00019',
  'rio-dos-cedros': 'DCSC-00011',
}

/** A estação estadual `codigo` é a régua das cotas da cidade? Código diferente, nunca. */
export function estacaoEhReguaDasCotas(cidadeId: string, codigo: string | null | undefined): boolean {
  return !!codigo && REGUA_ESTADUAL_DAS_COTAS[cidadeId] === codigo
}

/** A ressalva embaixo do nível bruto da rede estadual. */
export function ressalvaDoBruto(temCotasMunicipais: boolean, corEstadual: boolean, reguaDasCotas = false): string {
  const partes = ['Nível na régua própria da estação estadual.']
  if (temCotasMunicipais && reguaDasCotas) {
    partes.push('Esta estação é a régua das cotas municipais acima: o número se compara com elas.')
    partes.push(
      corEstadual
        ? 'A cor do pino é a classificação que a própria rede publica para esta estação, não uma comparação com cota municipal.'
        : 'Com a leitura em dia, é a comparação deste número com as cotas que define a faixa do pino.',
    )
    return partes.join(' ')
  }
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

/**
 * "Cor do rio: …" — qual classificação pintou o pino (PR 3 da classificação estadual × municipal, 07/10/2026;
 * §9 do plano). Quando quem decidiu foi o motor (`ultimo_classificacao.json` desta coleta), o texto nomeia a
 * régua dele; pela regra de sempre, diz só o tipo — o site não confere ali a identidade da régua, e o texto
 * não pode afirmar mais do que a conta fez. Sem cor (cinza, várias réguas), não há o que atribuir: null, e o
 * "Por que está cinza?" explica.
 */
export function textoDaOrigemDaCor(p: {
  faixa: string
  origemFaixa?: 'municipal' | 'estadual'
  classificadaPor?: 'motor' | 'site'
  origemDoMotor?: { tipo: 'municipal' | 'estadual'; reguaId: string | null; rotulo: string } | null
  codigoEstadual?: string | null
}): string | null {
  if (p.faixa === 'sem-dado' || p.faixa === 'varias') return null
  const NAO_MUNICIPAL = 'Não representa as cotas municipais.'
  if (p.classificadaPor === 'motor' && p.origemDoMotor) {
    const o = p.origemDoMotor
    const regua = o.reguaId ? ` (${o.reguaId})` : ''
    if (o.tipo === 'estadual') {
      return `Cor do rio: classificação estadual (Defesa Civil de SC) — ${o.reguaId ?? 'estação estadual'}. ${NAO_MUNICIPAL}`
    }
    // O rótulo do motor já começa por "Classificação municipal — <régua>".
    return `Cor do rio: ${o.rotulo.charAt(0).toLowerCase()}${o.rotulo.slice(1)}${o.rotulo.includes(o.reguaId ?? '\u0000') ? '' : regua}.`
  }
  if (p.origemFaixa === 'estadual') {
    return `Cor do rio: classificação estadual (Defesa Civil de SC) — ${p.codigoEstadual ?? 'estação estadual'}. ${NAO_MUNICIPAL}`
  }
  return 'Cor do rio: classificação municipal — cotas da cidade.'
}
