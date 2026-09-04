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
import { porRegua, tendencia } from '../dados/serie'
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

/**
 * Uma cor por RÉGUA, para a cidade que tem mais de uma.
 *
 * Não é enfeite: em Itajaí são onze réguas com ZEROS DIFERENTES, e até
 * 04/09/2026 elas saíam TODAS na mesma linha azul, intercaladas — um serrilhado
 * de 1,70 m de salto mediano que não é o rio subindo e descendo, é a linha
 * pulando de régua em régua. Uma linha por régua desfaz isso; a cor só as
 * separa aos olhos.
 */
const CORES_REGUA = ['#1c6ea4', '#7b4fa8', '#2e8b57', '#b06a1a', '#9c2c4b', '#3a7d8c']


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

  // UMA LINHA POR RÉGUA. Réguas diferentes têm zeros diferentes; costurá-las
  // numa linha só faz o gráfico afirmar subidas e descidas que são troca de
  // régua, não movimento do rio.
  const grupos = [...porRegua(serie)]
  const varias = grupos.length > 1
  const chaveDe = (i: number) => `n${i}`
  const porInstante = new Map<number, Record<string, number>>()
  grupos.forEach(([, pontos], i) => {
    for (const p of pontos) {
      const t = p.medidoEm.getTime()
      const linha = porInstante.get(t) ?? {}
      linha[chaveDe(i)] = p.nivel_m
      porInstante.set(t, linha)
    }
  })
  const dados = [...porInstante.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([t, valores]) => ({ t, ...valores }))

  const cotas = Object.entries(cidade.cotas_m)
  const maiorCota = cotas.length > 0 ? Math.max(...cotas.map(([, v]) => v)) : 0
  const maiorNivel = Math.max(...serie.map((p) => p.nivel_m))
  const teto = Math.ceil(Math.max(maiorNivel, maiorCota) + 0.5)

  // A última leitura DE CADA RÉGUA. Com várias, não existe "o nível da cidade":
  // dizer um número só obrigaria a escolher uma régua por conta, e o número
  // escolhido apareceria como se fosse o da cidade inteira.
  // Cada régua leva a SUA tendência. A guarda que apaga a tendência da cidade
  // (série que mistura zeros) não pode virar "Blumenau nunca tem tendência":
  // dentro de UMA régua a conta é legítima, e é a informação que interessa.
  const ultimos = grupos.map(([chave, pontos]) => ({
    regua: chave,
    ponto: pontos[pontos.length - 1]!,
    tend: tendencia(pontos),
  }))
  const ultimo = serie[serie.length - 1]!
  const faixaAgora = faixaDaCidade(
    cidade,
    { nivel_m: ultimo.nivel_m, medidoEm: ultimo.medidoEm },
    false,
    agora,
  )
  // `tendencia` devolve null quando a série mistura réguas — é o certo, e é por
  // isso que a frase "subindo/descendo" some em Itajaí.
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
      {varias ? (
        <div className={estilos.resumo}>
          <p>
            {cidade.nome} tem <strong>{grupos.length} réguas</strong> nesta série, e cada
            uma tem o seu próprio zero — os metros de uma não se comparam com os da
            outra, nem entre si. Por isso não há um "nível da cidade" aqui, e sim a
            última leitura de cada régua:
          </p>
          <ul className={estilos.listaReguas}>
            {ultimos.map((u, i) => (
              <li key={u.regua || `sem-${i}`}>
                <span
                  className={estilos.amostra}
                  style={{ background: CORES_REGUA[i % CORES_REGUA.length] }}
                  aria-hidden="true"
                />
                {u.regua || 'régua não identificada'}: <strong>{metros(u.ponto.nivel_m)}</strong>,
                medido {dataHora(u.ponto.medidoEm)}
                {u.tend ? (
                  <>
                    {' — '}
                    {u.tend.rotulo}
                    {u.tend.cmh !== 0 ? ` (${Math.abs(u.tend.cmh)} cm/h)` : ''}
                  </>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : (
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
      )}

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
              formatter={(v, nome) => [metros(Number(v)), varias ? String(nome) : 'Nível']}
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
            {grupos.map(([chave], i) => (
              <Line
                key={chave || `sem-${i}`}
                type="monotone"
                dataKey={chaveDe(i)}
                name={chave || 'régua não identificada'}
                stroke={CORES_REGUA[i % CORES_REGUA.length]}
                strokeWidth={2}
                dot={false}
                // Cada régua reporta nos SEUS instantes; sem isto a linha some
                // nos instantes em que só a outra régua publicou.
                connectNulls
                isAnimationActive={false}
              />
            ))}
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
        {varias
          ? `Uma linha por régua de ${cidade.nome} — cada régua tem seu próprio zero, então não compare os metros de uma com os da outra, nem com os de outra cidade.`
          : `Nível na régua de ${cidade.nome} — cada cidade tem seu próprio zero, então não compare estes metros com os de outra cidade.`} Arraste as alças embaixo
        do gráfico para ver mais horas. A cor de cada linha tracejada é a faixa
        da cota; a ação de cada faixa está na legenda do mapa.
      </p>
    </div>
  )
}
