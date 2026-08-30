import type { Ajuste, Par } from '../logica/previsao'
import { dataCurta } from '../logica/datas'
import { numero } from '../logica/formato'
import estilos from './DispersaoPares.module.css'

/**
 * Os pares (pico de montante, pico de jusante) desenhados.
 *
 * Existe para tornar visível a razão de a tela não dar um número. Quando a
 * nuvem não forma reta nenhuma, ninguém precisa acreditar no r² — dá para ver.
 *
 * SVG na mão, sem biblioteca: este painel carrega junto com a tela e puxar o
 * recharts para cá dobraria o pacote inicial.
 */
const L = 44
const B = 30
const LARG = 320
const ALT = 210

export default function DispersaoPares({
  pares,
  ajuste,
  nomeMontante,
  nomeJusante,
  mostrarReta,
}: {
  pares: Par[]
  ajuste: Ajuste | null
  nomeMontante: string
  nomeJusante: string
  mostrarReta: boolean
}) {
  if (pares.length < 2) return null

  const xs = pares.map((p) => p.x)
  const ys = pares.map((p) => p.y)
  const folga = (v: number[]) => Math.max(0.5, (Math.max(...v) - Math.min(...v)) * 0.15)
  const x0 = Math.min(...xs) - folga(xs)
  const x1 = Math.max(...xs) + folga(xs)
  const y0 = Math.min(...ys) - folga(ys)
  const y1 = Math.max(...ys) + folga(ys)

  const px = (x: number) => L + ((x - x0) / (x1 - x0)) * (LARG - L - 10)
  const py = (y: number) => ALT - B - ((y - y0) / (y1 - y0)) * (ALT - B - 12)

  const marcas = (a: number, b: number) => [a, (a + b) / 2, b]

  return (
    <figure className={estilos.figura}>
      <svg
        viewBox={`0 0 ${LARG} ${ALT}`}
        className={estilos.svg}
        role="img"
        aria-label={`Dispersão de ${pares.length} eventos: pico em ${nomeMontante} contra pico em ${nomeJusante}`}
      >
        <line x1={L} y1={12} x2={L} y2={ALT - B} className={estilos.eixo} />
        <line x1={L} y1={ALT - B} x2={LARG - 10} y2={ALT - B} className={estilos.eixo} />

        {marcas(y0, y1).map((v) => (
          <g key={`y${v}`}>
            <line x1={L - 4} y1={py(v)} x2={L} y2={py(v)} className={estilos.eixo} />
            <text x={L - 6} y={py(v) + 3} textAnchor="end" className={estilos.rotulo}>
              {numero(v, 1)}
            </text>
          </g>
        ))}
        {marcas(x0, x1).map((v) => (
          <g key={`x${v}`}>
            <line x1={px(v)} y1={ALT - B} x2={px(v)} y2={ALT - B + 4} className={estilos.eixo} />
            <text x={px(v)} y={ALT - B + 15} textAnchor="middle" className={estilos.rotulo}>
              {numero(v, 1)}
            </text>
          </g>
        ))}

        {mostrarReta && ajuste ? (
          <line
            x1={px(x0)}
            y1={py(ajuste.a + ajuste.b * x0)}
            x2={px(x1)}
            y2={py(ajuste.a + ajuste.b * x1)}
            className={estilos.reta}
          />
        ) : null}

        {pares.map((p) => (
          <g key={p.data}>
            <circle cx={px(p.x)} cy={py(p.y)} r={5} className={estilos.ponto} />
            <title>
              {dataCurta(p.data)}: {numero(p.x)} m em {nomeMontante} → {numero(p.y)} m em{' '}
              {nomeJusante}
            </title>
          </g>
        ))}
      </svg>
      <figcaption className={estilos.legenda}>
        Cada ponto é uma cheia: no eixo horizontal o pico em <strong>{nomeMontante}</strong>, no
        vertical o pico em <strong>{nomeJusante}</strong>, em metros das réguas de cada uma.
      </figcaption>
    </figure>
  )
}
