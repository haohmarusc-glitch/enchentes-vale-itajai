/**
 * Abrigo mais próximo, por distância REAL (coordenada), não por bairro.
 *
 * Regras que não são cosméticas:
 *  - Distância em LINHA RETA, não a pé. A tela diz isso — quem foge de uma
 *    cheia não anda em linha reta, e prometer "1,2 km" como se fosse caminhada
 *    engana. É ordenação e ordem de grandeza, não rota.
 *  - Abrigo sem nome/endereço NÃO entra na sugestão: não dá para mandar alguém
 *    para um ponto sem nome. Ele existe no arquivo (tem coordenada), mas indicar
 *    "vá para o abrigo sem nome a 800 m" seria pior que não indicar.
 *  - Nada aqui diz que o abrigo está ABERTO. Isso é decisão da Defesa Civil; a
 *    tela mostra a ressalva junto. Ver `avisoAbrigos`.
 */
import type { Abrigo } from '../dados/tipos'

/** Distância em km entre dois pontos [lat, lon] (Haversine). */
export function distanciaKm(a: [number, number], b: [number, number]): number {
  const r = 6371
  const rad = (g: number) => (g * Math.PI) / 180
  const dLat = rad(b[0] - a[0])
  const dLon = rad(b[1] - a[1])
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(rad(a[0])) * Math.cos(rad(b[0])) * Math.sin(dLon / 2) ** 2
  return 2 * r * Math.asin(Math.min(1, Math.sqrt(h)))
}

export interface AbrigoProximo {
  abrigo: Abrigo
  distanciaKm: number
}

/**
 * Os `n` abrigos NOMEADOS mais próximos de um ponto, do mais perto ao mais
 * longe. Ignora registros sem nome ou sem coordenada finita.
 */
/** Abrigo com coordenada finita — o `filter` abaixo estreita o tipo para cá. */
type AbrigoLocalizado = Abrigo & { lat: number; lon: number }

export function maisProximos(
  abrigos: Abrigo[],
  lat: number,
  lon: number,
  n = 3,
): AbrigoProximo[] {
  return abrigos
    .filter(
      (a): a is AbrigoLocalizado =>
        !!a.nome && Number.isFinite(a.lat) && Number.isFinite(a.lon),
    )
    .map((abrigo) => ({ abrigo, distanciaKm: distanciaKm([lat, lon], [abrigo.lat, abrigo.lon]) }))
    .sort((x, y) => x.distanciaKm - y.distanciaKm)
    .slice(0, n)
}
