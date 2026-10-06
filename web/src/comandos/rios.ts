/**
 * Qual arquivo de `data/rios/` é o rio de uma cidade, ou o rio citado pelo nome. Só para o chat responder
 * "de onde vem esse traçado?" (docs/CHAT-GLOBAL-COMANDOS.md); o Monitor desenha pela lista dele.
 */

/** O arquivo de `data/rios/` do rio de uma cidade: o tronco ou o afluente em que ela fica. */
export function arquivoDoRioDaCidade(cidadeId: string, rioDaPagina: 'acu' | 'mirim'): string {
  const PROPRIO: Record<string, string> = {
    ituporanga: 'itajai-do-sul',
    ibirama: 'hercilio',
    timbo: 'benedito',
    'rio-dos-cedros': 'rio-dos-cedros',
    'trombudo-central': 'trombudo',
    guabiruba: 'guabiruba',
  }
  return PROPRIO[cidadeId] ?? (rioDaPagina === 'mirim' ? 'itajai-mirim' : 'itajai-acu')
}

/** O arquivo de `data/rios/` citado pelo nome do rio ("Benedito", "Itajaí do Sul"), ou null. */
export function arquivoPeloNome(alvo: string): string | null {
  const t = alvo.replace(/^(?:rio|ribeirao) /, '')
  const NOMES: [RegExp, string][] = [
    [/^itajai mirim$|^mirim$/, 'itajai-mirim'],
    [/^itajai acu$|^acu$|^itajai do oeste$|^oeste$/, 'itajai-acu'],
    [/^itajai do sul$|^sul$/, 'itajai-do-sul'],
    [/^benedito$/, 'benedito'],
    [/^hercilio$|^itajai do norte$/, 'hercilio'],
    [/^trombudo$/, 'trombudo'],
    [/^dos cedros$/, 'rio-dos-cedros'],
    [/^guabiruba(?: norte)?$/, 'guabiruba'],
    [/^(?:da )?murta$/, 'ribeirao-murta'],
    [/^(?:da )?canhanduba$|^do meio$/, 'ribeirao-canhanduba'],
    [/^conceicao$/, 'rio-conceicao'],
  ]
  return NOMES.find(([r]) => r.test(t))?.[1] ?? null
}

export const NOME_DO_ARQUIVO: Record<string, string> = {
  'itajai-acu': 'Rio Itajaí-Açu (com o Itajaí do Oeste)',
  'itajai-mirim': 'Rio Itajaí-Mirim',
  'itajai-do-sul': 'Rio Itajaí do Sul',
  benedito: 'Rio Benedito',
  hercilio: 'Rio Hercílio (Itajaí do Norte)',
  trombudo: 'Rio Trombudo',
  'rio-dos-cedros': 'Rio dos Cedros',
  guabiruba: 'Rio Guabiruba',
  'ribeirao-murta': 'Ribeirão da Murta',
  'ribeirao-canhanduba': 'Rio Canhanduba',
  'rio-conceicao': 'Rio Conceição',
  'mirim-canal-retificado': 'canal retificado do Itajaí-Mirim',
}
