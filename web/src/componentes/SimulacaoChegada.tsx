import { useMemo, useState } from 'react'
import historico from '@dados/historico-chegada-itajai.json'
import { cidadesDoRio, mareItajai } from '../dados/carregar'
import { porRegua, serieDaCidade, useSerieRecente } from '../dados/serie'
import { publicacaoMaisRecente, situacaoDoPico, type SituacaoPico } from '../logica/picoBlumenau'
import { entradaBrasilia, simularChegada, type ResultadoSimulacao } from '../logica/simulacaoChegada'
import { primeiraCota } from '../logica/tempoReal'
import { rotuloCota, metros } from '../logica/formato'
import estilos from './SimulacaoChegada.module.css'

const hora = (d: Date) => d.toLocaleString('pt-BR', {
  timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short',
})
const soHora = (d: Date) => d.toLocaleString('pt-BR', {
  timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit',
})
const dia = (d: Date) => d.toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo' })
const mesmoDia = (a: Date, b: Date) => dia(a) === dia(b)
const numero = (n: number) => n.toLocaleString('pt-BR', { maximumFractionDigits: 2 })
const HORA = 3_600_000

/**
 * CHEGADA DO PICO × MARÉ EM ITAJAÍ.
 *
 * Desde 03/10/2026 (pedido do Jefferson: "a pessoa precisa saber no dia se
 * coincide com a maré, e não data histórica"), o painel abre pelo DIA DE HOJE:
 * lê a série de Blumenau e diz se o pico já passou, quando, e que marés caem na
 * janela de chegada. Enquanto o rio sobe, o pico ainda não aconteceu — a tela
 * diz isso e mostra um "se o pico fosse agora", rotulado assim. A simulação com
 * horário digitado continua embaixo, para um pico informado pela Defesa Civil ou
 * para um cenário.
 */
export default function SimulacaoChegada() {
  const referencia = historico.referencia_estudo
  return <section className={`cartao ${estilos.painel}`} aria-labelledby="simulacao-chegada-titulo">
    <p className={estilos.etiqueta}>Cenário experimental · calibração histórica pendente</p>
    <h2 id="simulacao-chegada-titulo">Chegada do pico × maré em Itajaí</h2>
    <p>Quando o pico da cheia passa por Blumenau, ele leva horas para chegar a Itajaí. Se chegar junto com a
      maré alta, a água escoa pior. Este painel cruza o pico de Blumenau com a tábua de marés.</p>

    <Hoje />

    <p className={estilos.aviso}><strong>Média histórica indisponível.</strong> O intervalo usado é o do estudo da
      JICA ({referencia.horas_min} a {referencia.horas_max} h), não uma média de cheias observadas. A pesquisa achou
      um atraso de 19 h relatado em setembro de 2011, mas ainda faltam pares de picos conferidos nas duas cidades
      para calibrar o trecho — e em Itajaí o nível sobe e desce com a maré, o que esconde o pico da cheia.</p>

    <Manual />

    <details className={estilos.pesquisa}>
      <summary>Dados históricos encontrados e o que falta conferir</summary>
      <p>Pesquisa de {historico.consultado_em.split('-').reverse().join('/')}. {historico.nota}</p>
      {historico.eventos.map((e) => <article key={e.id}>
        <h3>{e.evento}: {numero(e.atraso_relatado_h)} h relatadas</h3>
        <p>{e.estacao_jusante}. {e.nota}</p>
        <p><a href={e.url} target="_blank" rel="noreferrer">{e.fonte}</a></p>
      </article>)}
      <p>Precisamos de séries com data, hora, fuso e estação identificada nas duas cidades,
        além de avaliar a maré em Itajaí. A média só será calculada com ao menos {historico.min_eventos} eventos independentes
        conferidos por par de estações; seu uso como previsão ainda exige teste em outras cheias.</p>
      <ul>{historico.fontes_consultadas.map((f) => <li key={f.url}>
        <a href={f.url} target="_blank" rel="noreferrer">{f.rotulo}</a>: {f.resultado}
      </li>)}</ul>
    </details>
    <p className={estilos.detalhe}>Não substitui os avisos da Defesa Civil e do AlertaBlu. Emergência: 199.</p>
  </section>
}

/** O pico de hoje em Blumenau e a maré na janela de chegada. */
function Hoje() {
  const serie = useSerieRecente()
  const agora = useMemo(() => new Date(), [serie])
  const referencia = historico.referencia_estudo
  const blumenau = cidadesDoRio('itajai-acu').find((c) => c.id === 'blumenau')
  const pontos = publicacaoMaisRecente(porRegua(serieDaCidade(serie, 'itajai-acu', 'blumenau')))
  const situacao = situacaoDoPico(pontos, agora)
  const cota = blumenau ? primeiraCota(blumenau) : null
  const nomeCota = cota ? rotuloCota(cota.chave, blumenau?.cotas_nomes_na_fonte) : null

  return <div className={estilos.hoje} aria-live="polite">
    <h3 className={estilos.tituloHoje}>Hoje</h3>
    {serie.situacao === 'carregando' && situacao.tipo === 'sem-dado' ? (
      <p className={estilos.detalhe}>Buscando as últimas horas de Blumenau…</p>
    ) : (
      <ConteudoHoje situacao={situacao} referencia={referencia} cota={cota} nomeCota={nomeCota} />
    )}
  </div>
}

function ConteudoHoje({ situacao, referencia, cota, nomeCota }: {
  situacao: SituacaoPico
  referencia: { horas_min: number; horas_max: number }
  cota: { valor: number } | null
  nomeCota: string | null
}) {
  if (situacao.tipo === 'sem-dado') {
    return <p>Sem leitura recente de Blumenau: não dá para calcular hoje. Se a Defesa Civil ou o AlertaBlu
      informar o horário do pico, use a simulação abaixo.</p>
  }
  const nivel = situacao.tipo === 'passou' ? situacao.pico.nivel_m : situacao.ultimo.nivel_m
  // Rio abaixo da primeira cota: não há cheia descendo para cruzar com a maré.
  if (cota && nivel < cota.valor) {
    return <p>Blumenau está em <strong>{metros(situacao.ultimo.nivel_m)}</strong> (medido às{' '}
      {soHora(situacao.ultimo.medidoEm)}), abaixo da cota de {nomeCota} ({metros(cota.valor)}), e não passou dela
      nas últimas 36 h: <strong>não há pico de cheia descendo agora.</strong></p>
  }

  if (situacao.tipo === 'passou') {
    const horasPlato = (situacao.platoFim.getTime() - situacao.platoInicio.getTime()) / HORA
    const resultado = simularChegada(entradaBrasilia(situacao.platoInicio), referencia.horas_min,
      referencia.horas_max + Math.round(horasPlato * 10) / 10, mareItajai)
    return <>
      <p><strong>O pico já passou por Blumenau:</strong> {metros(situacao.pico.nivel_m)} às{' '}
        {hora(situacao.pico.medidoEm)}
        {horasPlato >= 0.5 ? <> (o rio ficou a menos de 5 cm disso de {mesmoDia(situacao.platoInicio, situacao.pico.medidoEm)
          ? soHora(situacao.platoInicio) : hora(situacao.platoInicio)} até {mesmoDia(situacao.platoFim, situacao.pico.medidoEm)
          ? soHora(situacao.platoFim) : hora(situacao.platoFim)})</> : null}. Agora está em {metros(situacao.ultimo.nivel_m)}, descendo.</p>
      {situacao.inicioIncerto ? <p className={estilos.detalhe}>O rio já estava alto no começo das últimas 36 h:
        o pico pode ter sido antes disso, e a janela abaixo, mais cedo.</p> : null}
      <Resultado resultado={resultado} rotulo={`Pela referência de estudo (${referencia.horas_min} a ${referencia.horas_max} h), o pico chegaria a Itajaí entre`} />
    </>
  }

  const resultado = simularChegada(entradaBrasilia(situacao.ultimo.medidoEm), referencia.horas_min,
    referencia.horas_max, mareItajai)
  return <>
    {situacao.tipo === 'subindo' ? (
      <p><strong>Blumenau ainda está subindo:</strong> {metros(situacao.ultimo.nivel_m)} às{' '}
        {soHora(situacao.ultimo.medidoEm)}
        {situacao.tendencia ? <> (+{Math.abs(situacao.tendencia.cmh)} cm/h)</> : null}. O pico ainda não aconteceu,
        então o horário de chegada a Itajaí <strong>ainda não se sabe</strong>.</p>
    ) : (
      <p><strong>Blumenau está perto do ponto mais alto</strong> ({metros(situacao.ultimo.nivel_m)} às{' '}
        {soHora(situacao.ultimo.medidoEm)}), mas ainda não desceu o bastante para confirmar que o pico passou.</p>
    )}
    <Resultado resultado={resultado} hipotese qual="deste cenário"
      rotulo={`Se o pico fosse agora, pela referência de estudo (${referencia.horas_min} a ${referencia.horas_max} h), chegaria a Itajaí entre`} />
    <p className={estilos.detalhe}>A cada leitura nova de Blumenau esta janela é refeita; enquanto o rio subir, ela
      anda para frente.</p>
  </>
}

/** A simulação com horário digitado: um pico informado pela Defesa Civil, ou um cenário. */
function Manual() {
  const [partida, setPartida] = useState('')
  const [modo, setModo] = useState('estudo')
  const [minimo, setMinimo] = useState('14')
  const [maximo, setMaximo] = useState('17')
  const [resultado, setResultado] = useState<ResultadoSimulacao | null>(null)
  const referencia = historico.referencia_estudo
  const invalida = () => setResultado(null)
  return <div className={estilos.manual}>
    <h3 className={estilos.tituloHoje}>Simular outro horário</h3>
    <form onSubmit={(e) => {
      e.preventDefault()
      setResultado(simularChegada(partida,
        modo === 'estudo' ? referencia.horas_min : Number(minimo),
        modo === 'estudo' ? referencia.horas_max : Number(maximo), mareItajai))
    }}>
      <label className={estilos.campo} htmlFor="pico-blumenau">Data e hora do pico em Blumenau — Brasília
        <input id="pico-blumenau" type="datetime-local" required value={partida}
          onChange={(e) => { setPartida(e.target.value); invalida() }} />
      </label>
      <p className={estilos.detalhe}>Por exemplo, o horário do pico informado pela Defesa Civil ou pelo AlertaBlu,
        ou um horário hipotético. A última leitura do rio não é automaticamente um pico.</p>
      <label className={estilos.campo} htmlFor="base-chegada">Tempo entre os picos
        <select id="base-chegada" value={modo} onChange={(e) => { setModo(e.target.value); invalida() }}>
          <option value="estudo">Referência JICA: {referencia.horas_min} a {referencia.horas_max} horas</option>
          <option value="manual">Informar um intervalo hipotético</option>
        </select>
      </label>
      {modo === 'estudo' ? <p className={estilos.detalhe}>
        <a href={referencia.url} target="_blank" rel="noreferrer">{referencia.rotulo}</a>.
        {' '}{referencia.nota}
      </p> : <div className={estilos.intervalo}>
        <label className={estilos.campo} htmlFor="transito-min">Mínimo (horas)
          <input id="transito-min" type="number" min="0.1" max="72" step="0.1" required value={minimo}
            onChange={(e) => { setMinimo(e.target.value); invalida() }} />
        </label>
        <label className={estilos.campo} htmlFor="transito-max">Máximo (horas)
          <input id="transito-max" type="number" min="0.1" max="72" step="0.1" required value={maximo}
            onChange={(e) => { setMaximo(e.target.value); invalida() }} />
        </label>
        <p className={estilos.detalhe}>Hipótese escolhida por você; não representa calibração nem previsão oficial.</p>
      </div>}
      <button type="submit" className={estilos.botao}>Simular coincidência com a maré</button>
    </form>

    <div aria-live="polite" aria-atomic="true">
      {resultado ? <Resultado resultado={resultado} titulo="Janela de chegada neste cenário" qual="simulada"
        nota={modo === 'estudo' ? 'Referência de estudo, sem calibração histórica.' : 'Intervalo hipotético informado por você.'} /> : null}
    </div>
  </div>
}

/** A janela de chegada e as marés dentro dela — o mesmo quadro no "Hoje" e na simulação. */
function Resultado({ resultado, titulo, rotulo, nota, hipotese = false, qual = '' }: {
  resultado: ResultadoSimulacao
  titulo?: string
  rotulo?: string
  nota?: string
  hipotese?: boolean
  /** Como chamar a janela na conclusão: "simulada", "deste cenário"… */
  qual?: string
}) {
  if ('erro' in resultado) return <p role="alert">{resultado.erro}</p>
  return <div className={`${estilos.resultado} ${hipotese ? estilos.hipotese : ''}`}>
    {titulo ? <h3>{titulo}</h3> : null}
    {rotulo ? <p className={estilos.rotuloJanela}>{rotulo}</p> : null}
    <p className={estilos.janela}>{hora(resultado.inicio)} até {hora(resultado.fim)}</p>
    <p className={estilos.detalhe}>Horário de Brasília.{nota ? ` ${nota}` : ''}</p>
    {!resultado.cobertura ? <p><strong>Tábua insuficiente para cobrir toda a janela.</strong> Não é possível concluir
      se haverá coincidência com a preamar. Os extremos disponíveis abaixo são apenas consulta.</p> :
      resultado.preamaresDentro > 0 ? <p><strong>Há preamar dentro da janela{qual ? ` ${qual}` : ''}.</strong> A
        coincidência de horários não determina a altura da enchente nem a probabilidade de alagamento. Siga a Defesa
        Civil de Itajaí.</p> :
        <p><strong>Nenhum pico de maré está dentro da janela{qual ? ` ${qual}` : ''}.</strong> A maré ainda
          pode influenciar o escoamento; isso não significa ausência de risco.</p>}
    {resultado.extremos.length > 0 && <div className={estilos.tabela}>
      <table>
        <caption>Extremos da maré astronômica: dentro e nos limites próximos da janela</caption>
        <thead><tr><th scope="col">Extremo e horário</th><th scope="col">Altura sobre NR</th><th scope="col">Posição</th></tr></thead>
        <tbody>{resultado.extremos.map((p) => <tr key={`${p.tipo}-${p.quando.toISOString()}`}>
          <th scope="row">{p.tipo === 'preamar' ? 'Maré alta' : 'Maré baixa'}<br />{hora(p.quando)}</th>
          <td>{p.altura === null ? 'Sem altura' : `${numero(p.altura)} m`}</td>
          <td>{p.dentro ? 'Dentro' : p.quando < resultado.inicio ? 'Antes' : 'Depois'}</td>
        </tr>)}</tbody>
      </table>
    </div>}
    <p className={estilos.detalhe}>Fonte: {mareItajai._meta.fonte_curta}. NR é a referência de altura da carta náutica.
      Essas alturas são dos extremos publicados, não de cada instante da janela. Não são o nível do rio e não devem
      ser somadas à régua de Blumenau. Vento, pressão atmosférica, afluentes e chuva local não estão modelados.</p>
  </div>
}
