/**
 * As estações da ANA que os picos históricos de uma cidade citam na fonte,
 * fora a estação do cadastro dela.
 *
 * Auditoria de 03/10/2026, item 6: a aba Fontes de Apiúna dizia "Sem estação
 * ANA localizada" enquanto os cinco picos da mesma cidade vinham da ANA
 * 83500000; a de Ituporanga mostrava a 83145140 e os picos eram da 83250000.
 * Eram referências diferentes de propósito (estação do cadastro × estação da
 * série histórica, cada uma com o seu zero), mas a tela não separava as duas.
 */
export function estacoesAnaDosPicos(
  picos: ReadonlyArray<{ fonte?: string | null }>,
  codigoAna: string | null | undefined,
): string[] {
  const codigos = new Set<string>()
  for (const p of picos) {
    for (const m of (p.fonte ?? '').matchAll(/ANA[^.;]*?\b(8\d{7})\b/g)) codigos.add(m[1]!)
  }
  if (codigoAna) codigos.delete(codigoAna)
  return [...codigos].sort()
}
