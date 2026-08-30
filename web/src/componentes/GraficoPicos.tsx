import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { Cidade, Confianca, Evento } from '../dados/tipos'
import { comparaData, dataCurta, dataLegivel } from '../logica/datas'
import { metros, numero, rotuloCota } from '../logica/formato'
import estilos from './GraficoPicos.module.css'

/**
 * Picos históricos de UMA cidade. Nunca de várias no mesmo eixo: os metros de
 * cada cidade estão em réguas com zeros diferentes e o gráfico comparativo
 * daria a impressão errada de que Blumenau "enche mais" que Brusque.
 */
const COR: Record<Confianca, string> = {
  alta: '#1c6ea4',
  media: '#c98a1a',
  baixa: '#8d8d96',
}

interface Ponto {
  rotulo: string
  data: string
  pico: number
  confianca: Confianca
  fonte: string
}

export default function GraficoPicos({
  eventos,
  cidade,
  nomeCidade,
}: {
  eventos: Evento[]
  cidade: Cidade | undefined
  nomeCidade: string
}) {
  const dados: Ponto[] = [...eventos]
    .sort((a, b) => comparaData(a.data, b.data))
    .map((e) => ({
      rotulo: dataCurta(e.data),
      data: e.data,
      pico: e.pico_m,
      confianca: e.confianca,
      fonte: e.fonte,
    }))

  if (dados.length === 0) {
    return (
      <p className={estilos.vazio}>
        Não há picos registrados para {nomeCidade} em <code>enchentes.json</code>. Levantar esses
        dados é uma das pendências do projeto.
      </p>
    )
  }

  const cotas = Object.entries(cidade?.cotas_m ?? {})
  const maiorCota = cotas.length > 0 ? Math.max(...cotas.map(([, v]) => v)) : 0
  const teto = Math.ceil(Math.max(...dados.map((d) => d.pico), maiorCota) + 1)

  return (
    <div>
      <p className={estilos.legenda}>
        Alturas na régua de <strong>{nomeCidade}</strong>
        {cidade?.regua ? ` (${cidade.regua})` : ''}. Não compare com outra cidade.
      </p>

      <div className={estilos.grafico}>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={dados} margin={{ top: 16, right: 8, left: -18, bottom: 4 }}>
            <XAxis dataKey="rotulo" tick={{ fontSize: 11 }} interval={0} angle={-40} height={64} textAnchor="end" />
            <YAxis
              domain={[0, teto]}
              tick={{ fontSize: 11 }}
              unit=" m"
              width={64}
            />
            <Tooltip
              formatter={(v: number) => [metros(v), 'Pico']}
              labelFormatter={(_rotulo, carga) => {
                const p = carga?.[0]?.payload as Ponto | undefined
                return p ? dataLegivel(p.data) : ''
              }}
            />
            {cotas.map(([chave, valor]) => (
              <ReferenceLine
                key={chave}
                y={valor}
                stroke="var(--alerta)"
                strokeDasharray="5 4"
                label={{
                  value: `${rotuloCota(chave)} ${numero(valor)} m`,
                  position: 'insideTopLeft',
                  fontSize: 11,
                  fill: '#b3261e',
                }}
              />
            ))}
            <Bar dataKey="pico" isAnimationActive={false}>
              <LabelList dataKey="pico" position="top" fontSize={11} formatter={(v: number) => numero(v)} />
              {dados.map((d) => (
                <Cell key={`${d.data}-${d.pico}`} fill={COR[d.confianca]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <ul className={estilos.legendaCores}>
        <li>
          <span className={estilos.amostra} style={{ background: COR.alta }} /> fonte oficial ou
          acadêmica
        </li>
        <li>
          <span className={estilos.amostra} style={{ background: COR.media }} /> imprensa ou
          compilação
        </li>
        <li>
          <span className={estilos.amostra} style={{ background: COR.baixa }} /> compilação informal
          ou dado disputado
        </li>
      </ul>

      <details className={estilos.tabela}>
        <summary>Ver os {dados.length} registros com fonte</summary>
        <div className="rolagem-h">
          <table>
            <thead>
              <tr>
                <th>Data</th>
                <th>Pico</th>
                <th>Fonte</th>
              </tr>
            </thead>
            <tbody>
              {[...dados].reverse().map((d) => (
                <tr key={`${d.data}-${d.pico}`}>
                  <td>{dataLegivel(d.data)}</td>
                  <td>{metros(d.pico)}</td>
                  <td>{d.fonte}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  )
}
