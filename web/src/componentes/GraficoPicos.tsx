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
import {
  ehIBGE,
  legendaDaEscala,
  misturaReferencias as misturaDeReferencias,
  nomeDaReferenciaPublicada,
  textoDaConversao,
  textoDaReferencia,
} from '../logica/referencias'
import { avisoDeEncosta } from '../logica/encosta'
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
  nota?: string
  divergencias?: { pico_m: number; fonte: string; referencia_publicada?: string | null }[]
  referencia?: string | null
  /** Só em registro convertido para a régua de hoje: como foi publicado. */
  conversao?: string
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
      ...(e.nota ? { nota: e.nota } : {}),
      ...(e.divergencias ? { divergencias: e.divergencias } : {}),
      ...('referencia' in e ? { referencia: e.referencia } : {}),
      ...(e.referencia_publicada ? { conversao: textoDaConversao(e.pico_publicado_m, e.referencia_publicada) } : {}),
    }))

  // Referências diferentes na mesma cidade não são detalhe de nota de rodapé:
  // a série longa de Blumenau está no zero do IBGE, 20 cm ABAIXO da régua de
  // hoje (e 20 cm acima da antiga, trocada depois de 2011), e as cotas de
  // atenção e alerta estão na régua de hoje. Quem olha o gráfico precisa saber
  // que os pontos não estão todos na mesma escala.
  const misturaReferencias = misturaDeReferencias(dados.map((d) => d.referencia))
  const temIBGE = dados.some((d) => ehIBGE(d.referencia))
  const legendaEscala = legendaDaEscala(nomeCidade, cidade?.regua, dados.map((d) => d.referencia))

  // O gráfico ordena por metro de rio, e há um contraexemplo enorme no Vale:
  // novembro de 2008 tem dezenas de cotas acima dele em Blumenau e foi o evento mais letal
  // da região, porque o que matou foi encosta, não régua. Sem este aviso, a
  // altura da barra diz "evento médio" — a conclusão exata que este projeto
  // existe para não deixar acontecer.
  const encosta = avisoDeEncosta(dados)

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
      <p
        className={legendaEscala.ehAviso ? estilos.legendaAviso : estilos.legenda}
        role={legendaEscala.ehAviso ? 'note' : undefined}
      >
        {legendaEscala.ehAviso ? <strong>⚠️ </strong> : null}
        {legendaEscala.texto}
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
              formatter={(v) => [metros(Number(v)), 'Pico']}
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
                  value: `${rotuloCota(chave, cidade?.cotas_nomes_na_fonte)} ${numero(valor)} m`,
                  position: 'insideTopLeft',
                  fontSize: 11,
                  fill: '#b3261e',
                }}
              />
            ))}
            <Bar dataKey="pico" isAnimationActive={false}>
              <LabelList dataKey="pico" position="top" fontSize={11} formatter={(v) => numero(Number(v))} />
              {dados.map((d) => (
                <Cell key={`${d.data}-${d.pico}`} fill={COR[d.confianca]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {encosta ? (
        <p className={estilos.encosta} role="note">
          <strong>⚠️ A régua mede o rio, não a encosta.</strong> {encosta.geral}
          {encosta.exemplo ? (
            <>
              {' '}
              Aqui mesmo: <strong>{dataLegivel(encosta.exemplo.data)}</strong> aparece com{' '}
              {metros(encosta.exemplo.pico)}, em {encosta.exemplo.posicao}º lugar nesta lista, com{' '}
              {encosta.exemplo.acima}{' '}
              {encosta.exemplo.acima === 1 ? 'enchente mais alta' : 'enchentes mais altas'} acima —
              e é dele que a fonte diz que as mortes vieram sobretudo dos deslizamentos.
            </>
          ) : null}
        </p>
      ) : null}

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

      {misturaReferencias ? (
        <p className={estilos.referencias} role="note">
          <strong>Atenção: estes pontos não estão todos na mesma referência.</strong>{' '}
          {temIBGE ? (
            <>
              Desde 03/10/2026 os picos de {nomeCidade} que puderam ser conferidos estão{' '}
              <strong>na régua de hoje</strong>: a FURB confirmou que a régua instalada depois da cheia de
              2011 lê 40 cm acima da antiga, e o zero do IBGE fica no meio. A cheia de 1983, publicada como
              15,34 m na tabela de Cordero &amp; Medeiros, aparece como 15,54 m. Os que continuam no IBGE
              (20 cm abaixo da régua de hoje) ou sem referência têm conflito entre fontes e não foram
              convertidos.{' '}
            </>
          ) : (
            <>Alguns registros não declaram a referência. </>
          )}
          As cotas de atenção, alerta e inundação e o nível de agora estão <em>na régua de hoje</em>, e só
          os pontos na régua entram na comparação com o nível de agora. Cada linha da tabela abaixo diz a
          sua referência e, quando foi convertida, como foi publicada.
        </p>
      ) : null}

      <details className={estilos.tabela}>
        <summary>Ver os {dados.length} registros com fonte</summary>
        <div className="rolagem-h">
          <table>
            <thead>
              <tr>
                <th>Data</th>
                <th>Pico</th>
                <th>Referência</th>
                <th>Fonte</th>
              </tr>
            </thead>
            <tbody>
              {[...dados].reverse().map((d) => (
                <tr key={`${d.data}-${d.pico}`}>
                  <td>{dataLegivel(d.data)}</td>
                  <td>
                    {metros(d.pico)}
                    {d.divergencias?.length ? (
                      <span className={estilos.divergencia}>
                        {' '}
                        outras fontes:{' '}
                        {d.divergencias
                          .map((x) =>
                            'referencia_publicada' in x
                              ? `${metros(x.pico_m)} (${nomeDaReferenciaPublicada(x.referencia_publicada)}, como publicado)`
                              : metros(x.pico_m),
                          )
                          .join(', ')}
                      </span>
                    ) : null}
                  </td>
                  <td className={estilos.referenciaCelula}>
                    {textoDaReferencia(d.referencia)}
                    {d.conversao ? <span className={estilos.nota}> {d.conversao}</span> : null}
                  </td>
                  <td>
                    {d.fonte}
                    {d.nota ? <span className={estilos.nota}> {d.nota}</span> : null}
                    {d.divergencias?.map((x) => (
                      <span key={x.fonte} className={estilos.nota}>
                        {' '}
                        {metros(x.pico_m)}: {x.fonte}.
                      </span>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  )
}
