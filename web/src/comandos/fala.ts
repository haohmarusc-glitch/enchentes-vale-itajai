/**
 * 11ª entrega dos comandos do chat: "ler em voz alta". O texto da resposta vira fala do próprio navegador
 * (`speechSynthesis`), sem mandar nada a servidor do site. Aqui só se prepara o texto para soar natural:
 * símbolos e unidades por extenso, marcadores de lista fora.
 */
export function textoParaFala(texto: string): string {
  return texto
    .replace(/[•→▲▼▶]/g, ' ')
    .replace(/(\d)\s*cm\/h\b/g, '$1 centímetros por hora')
    .replace(/(\d)\s*cm\b/g, '$1 centímetros')
    .replace(/(\d)\s*mm\b/g, '$1 milímetros')
    .replace(/(\d)\s*km\b/g, '$1 quilômetros')
    .replace(/(\d)\s*m\b/g, '$1 metros')
    .replace(/(\d)\s*h(\d{2})\b/g, '$1 horas e $2')
    .replace(/(\d+)–(\d+)\s*h\b/g, '$1 a $2 horas')
    .replace(/(\d)\s*h\b/g, '$1 horas')
    .replace(/\s+/g, ' ')
    .trim()
}
