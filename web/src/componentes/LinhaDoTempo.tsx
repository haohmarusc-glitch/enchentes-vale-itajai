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
import { faixaDaCidade, frescorDaCidade, idadeMin, textoIdade } from '../logica/tempoReal'
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
  resgates = {},
}: {
  cidade: Cidade
  serie: PontoSerie[]
  agora: Date
  /** Ver `EstadoSerie.resgates`. Ausente = trata tudo como régua distinta. */
  resgates?: Record<string, string>
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
  /**
   * DUAS FONTES OU DUAS RÉGUAS? (achado 5 da auditoria de 19/09/2026)
   *
   * A tela dizia, para toda série múltipla, que a cidade "tem N réguas, cada
   * uma com o seu próprio zero". Em Itajaí é verdade: são onze réguas, zeros
   * diferentes. Em Blumenau é FALSO: são duas PUBLICAÇÕES da mesma régua (a
   * estação ANA 83800002, pela Defesa Civil de Itajaí e pelo AlertaBlu), que
   * discordam ~6 cm de forma sistemática — medido em 04/09/2026, e é por isso
   * que as séries ficam separadas, decisão deliberada e correta.
   *
   * Separar as séries: certo. Chamar isso de duas réguas físicas: a regra nº 1
   * do projeto ao contrário — confundir FONTE com RÉGUA. E o bot já acertava
   * (junta pelo `resgate_de`), então as duas telas se contradiziam.
   *
   * Aqui a conta é sobre a régua COBERTA por cada fonte: se todas as séries
   * caem na mesma, são publicações do mesmo instrumento.
   */
  const reguaCoberta = (titulo: string | null) =>
    titulo === null ? null : (resgates[titulo] ?? titulo)
  const cobertas = new Set(grupos.map(([chave]) => reguaCoberta(chave || null)))
  const mesmaRegua = varias && cobertas.size === 1 && !cobertas.has(null)
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
  /**
   * A série está VENCIDA? (achado 3 da auditoria de 19/09/2026)
   *
   * Em Gaspar o gráfico dizia "Agora: 1,32 m", medido 18/09 às 18:03 — DEZENOVE
   * horas antes —, seguido de "descendo (3 cm/h)". O número e o horário estavam
   * certos, e o topo da página já avisava "sem leitura ao vivo": o que mentia
   * era o RÓTULO, que chamava de "agora" uma medição de ontem, e a tendência,
   * que soava como o que o rio está fazendo neste momento.
   *
   * O mesmo teto do resto do site (`frescorDaCidade`: 180 min, 120 em
   * Blumenau), para a série não ter uma noção de "velho" própria.
   */
  const vencida = (p: { medidoEm: Date }) =>
    frescorDaCidade(idadeMin(p.medidoEm, agora), cidade.id) === 'velha'
  const serieVencida = vencida(ultimo)
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
          {mesmaRegua ? (
            <p>
              {cidade.nome} tem <strong>uma régua</strong>, publicada por{' '}
              <strong>{grupos.length} fontes</strong> diferentes. É o mesmo instrumento,
              mas as publicações <strong>discordam entre si</strong> em alguns centímetros,
              de forma sistemática — por isso cada uma aparece como uma linha, em vez de
              virarem uma série costurada que inventaria subidas e descidas. A última
              leitura de cada fonte:
            </p>
          ) : (
            <p>
              {cidade.nome} tem <strong>{grupos.length} réguas</strong> nesta série, e cada
              uma tem o seu próprio zero — os metros de uma não se comparam com os da
              outra, nem entre si. Por isso não há um "nível da cidade" aqui, e sim a
              última leitura de cada régua:
            </p>
          )}
          <ul className={estilos.listaReguas}>
            {ultimos.map((u, i) => (
              <li key={u.regua || `sem-${i}`}>
                <span
                  className={estilos.amostra}
                  style={{ background: CORES_REGUA[i % CORES_REGUA.length] }}
                  aria-hidden="true"
                />
                {u.regua || (mesmaRegua ? 'fonte não identificada' : 'régua não identificada')}: <strong>{metros(u.ponto.nivel_m)}</strong>,
                medido {dataHora(u.ponto.medidoEm)}
                {vencida(u.ponto) ? (
                  <>
                    {' '}
                    ({textoIdade(idadeMin(u.ponto.medidoEm, agora))} — <strong>parada</strong>)
                  </>
                ) : null}
                {u.tend ? (
                  <>
                    {' — '}
                    {u.tend.rotulo}
                    {u.tend.cmh !== 0 ? ` (${Math.abs(u.tend.cmh)} cm/h)` : ''}
                    {vencida(u.ponto) ? ' até ali' : ''}
                  </>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className={estilos.resumo}>
          {serieVencida ? (
            <>
              <strong>Esta série está parada.</strong> A última leitura é de{' '}
              {dataHora(ultimo.medidoEm)} — {textoIdade(idadeMin(ultimo.medidoEm, agora))} —, e
              marcava <strong>{metros(ultimo.nivel_m)}</strong>.
            </>
          ) : (
            <>
              Agora: <strong>{metros(ultimo.nivel_m)}</strong> ({ROTULO_FAIXA[faixaAgora]}), medido{' '}
              {dataHora(ultimo.medidoEm)}.
            </>
          )}
          {tend ? (
            <>
              {' '}
              {serieVencida ? 'No período até ali' : 'Nas últimas horas'}:{' '}
              <strong>
                {tend.rotulo}
                {tend.cmh !== 0 ? ` (${Math.abs(tend.cmh)} cm/h)` : ''}
              </strong>
              {serieVencida ? ' — é o que o rio fazia até parar de publicar, não agora' : ''}.
            </>
          ) : null}
        </p>
      )}

      <div className={estilos.grafico}>
        <ResponsiveContainer width="100%" height={280}>
          {/*
            `key` pela cidade: o <Brush> guarda o endIndex em estado interno e só
            recebe startIndex por prop. Sem o key, trocar de cidade sem recarregar
            reaproveita a mesma instância e o endIndex da cidade anterior sobrevive
            — incoerente com a série nova, o intervalo do Brush vira negativo e o
            recharts escreve NaN em x/width do slide e x1/x2 das alças. Remontar ao
            trocar de cidade zera esse estado; nas re-renderizações normais (o
            relógio de `agora`) o key não muda, então o arraste do morador fica de pé.
          */}
          <LineChart
            key={cidade.id}
            data={dados}
            margin={{ top: 16, right: 12, left: -18, bottom: 4 }}
          >
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
                  value: `${rotuloCota(chave, cidade.cotas_nomes_na_fonte)} ${numero(valor)} m`,
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
