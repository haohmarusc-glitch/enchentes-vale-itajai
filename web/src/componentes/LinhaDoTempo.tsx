import {
  Brush,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { Cidade } from '../dados/tipos'
import type { PontoSerie } from '../dados/serie'
import { tendencia } from '../dados/serie'
import { faixaDaCidade } from '../logica/tempoReal'
import { dataHora, metros, numero, rotuloCota } from '../logica/formato'
import { ROTULO_FAIXA } from './LegendaFaixas'
import estilos from './LinhaDoTempo.module.css'

/**
 * A linha do tempo do nível de UMA cidade nas últimas horas — a metade de
 * "histórico" do slider do Kikikuru. Uma cidade só, de propósito: os metros de
 * cada régua têm zeros diferentes, e sobrepor cidades num eixo só daria a
 * impressão falsa de que uma "enche mais" que a outra (a mesma regra do gráfico
 * de picos). As cotas da própria cidade entram como faixas de cor, e a linha as
 * cruza — é assim que se vê a cheia subindo.
 *
 * Lê a série publicada (régua, sempre): nada de referência IBGE aqui, então não
 * há mistura de escala a avisar.
 */
const COR_COTA: Record<string, string> = {
  atencao: '#e6a700',
  alerta: '#e2661a',
  inundacao: '#c62828',
  emergencia: '#c62828',
}

const JANELA_PADRAO_H = 24


export default function LinhaDoTempo({
  cidade,
  serie,
  agora,
}: {
  cidade: Cidade
  serie: PontoSerie[]
  agora: Date
}) {
  if (serie.length === 0) {
    return (
      <p className={estilos.vazio}>
        Ainda não há série publicada para {cidade.nome} nas últimas horas. A coleta
        acumula a cada 15 minutos — quando houver leituras, a linha do tempo
        aparece aqui.
      </p>
    )
  }

  const dados = serie.map((p) => ({ t: p.medidoEm.getTime(), nivel: p.nivel_m }))
  const cotas = Object.entries(cidade.cotas_m)
  const maiorCota = cotas.length > 0 ? Math.max(...cotas.map(([, v]) => v)) : 0
  const maiorNivel = Math.max(...serie.map((p) => p.nivel_m))
  const teto = Math.ceil(Math.max(maiorNivel, maiorCota) + 0.5)

  const ultimo = serie[serie.length - 1]!
  const faixaAgora = faixaDaCidade(
    cidade,
    { nivel_m: ultimo.nivel_m, medidoEm: ultimo.medidoEm },
    false,
    agora,
  )
  const tend = tendencia(serie)

  // Abre mostrando as últimas 24 h; a janela cheia (48 h) fica no arraste.
  const corte = ultimo.medidoEm.getTime() - JANELA_PADRAO_H * 3_600_000
  const inicio = Math.max(
    0,
    dados.findIndex((d) => d.t >= corte),
  )

  const horaMin = (t: number) =>
    new Date(t).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })

  return (
    <div>
      <p className={estilos.resumo}>
        Agora: <strong>{metros(ultimo.nivel_m)}</strong> ({ROTULO_FAIXA[faixaAgora]}), medido{' '}
        {dataHora(ultimo.medidoEm)}.
        {tend ? (
          <>
            {' '}
            Nas últimas horas:{' '}
            <strong>
              {tend.rotulo}
              {tend.cmh !== 0 ? ` (${Math.abs(tend.cmh)} cm/h)` : ''}
            </strong>
            .
          </>
        ) : null}
      </p>

      <div className={estilos.grafico}>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={dados} margin={{ top: 16, right: 12, left: -18, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--borda)" />
            <XAxis
              dataKey="t"
              type="number"
              scale="time"
              domain={['dataMin', 'dataMax']}
              tickFormatter={horaMin}
              tick={{ fontSize: 11 }}
              minTickGap={40}
            />
            <YAxis domain={[0, teto]} tick={{ fontSize: 11 }} unit=" m" width={56} />
            <Tooltip
              formatter={(v) => [metros(Number(v)), 'Nível']}
              labelFormatter={(t) => dataHora(new Date(Number(t)))}
            />
            {cotas.map(([chave, valor]) => (
              <ReferenceLine
                key={chave}
                y={valor}
                stroke={COR_COTA[chave] ?? 'var(--alerta)'}
                strokeDasharray="5 4"
                label={{
                  value: `${rotuloCota(chave)} ${numero(valor)} m`,
                  position: 'insideTopLeft',
                  fontSize: 11,
                  fill: COR_COTA[chave] ?? '#b3261e',
                }}
              />
            ))}
            <Line
              type="monotone"
              dataKey="nivel"
              stroke="#1c6ea4"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <Brush
              dataKey="t"
              height={22}
              startIndex={inicio}
              tickFormatter={horaMin}
              stroke="#1c6ea4"
              travellerWidth={8}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <p className={estilos.nota}>
        Nível na régua de {cidade.nome} — cada cidade tem seu próprio zero, então
        não compare estes metros com os de outra cidade. Arraste as alças embaixo
        do gráfico para ver mais horas. A cor de cada linha tracejada é a faixa
        da cota; a ação de cada faixa está na legenda do mapa.
      </p>
    </div>
  )
}
