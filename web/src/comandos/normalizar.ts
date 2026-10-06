/** Minúsculo, sem acento, sem pontuação; hífen vira espaço ("DC-05" → "dc 05", "rio-do-sul" → "rio do sul"). */
export function normalizar(s: string): string {
  return s
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}
