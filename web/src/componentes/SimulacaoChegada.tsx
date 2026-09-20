import { useState } from 'react'
import historico from '@dados/historico-chegada-itajai.json'
import { mareItajai } from '../dados/carregar'
import { simularChegada, type ResultadoSimulacao } from '../logica/simulacaoChegada'
import estilos from './SimulacaoChegada.module.css'

const hora = (d: Date) => d.toLocaleString('pt-BR', {
  timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short',
})
const numero = (n: number) => n.toLocaleString('pt-BR', { maximumFractionDigits: 2 })

export default function SimulacaoChegada() {
  const [partida, setPartida] = useState('')
  const [modo, setModo] = useState('estudo')
  const [minimo, setMinimo] = useState('14')
  const [maximo, setMaximo] = useState('17')
  const [resultado, setResultado] = useState<ResultadoSimulacao | null>(null)
  const referencia = historico.referencia_estudo
  const invalida = () => setResultado(null)
  return <section className={`cartao ${estilos.painel}`} aria-labelledby="simulacao-chegada-titulo">
    <p className={estilos.etiqueta}>Cenário experimental · calibração histórica pendente</p>
    <h2 id="simulacao-chegada-titulo">Chegada do pico × maré em Itajaí</h2>
    <p>Se o pico passar por Blumenau no horário informado e levar este intervalo para chegar a Itajaí,
      quais marés estarão previstas? O cálculo acompanha o <strong>pico da cheia</strong>; a subida do rio pode começar antes.</p>
    <p className={estilos.aviso}><strong>Média histórica indisponível.</strong> A pesquisa encontrou um atraso de 19 h
      relatado para setembro de 2011, mas ainda faltam séries e pares de picos conferidos para calibrar o trecho.
      Esse caso não foi usado para ajustar a faixa abaixo.</p>

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
      <p className={estilos.detalhe}>Informe um pico observado ou um horário hipotético. A última leitura do rio não é automaticamente um pico.</p>
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
      {resultado && ('erro' in resultado ? <p role="alert">{resultado.erro}</p> :
        <div className={estilos.resultado}>
          <h3>Janela de chegada neste cenário</h3>
          <p className={estilos.janela}>{hora(resultado.inicio)} até {hora(resultado.fim)}</p>
          <p className={estilos.detalhe}>Horário de Brasília. {modo === 'estudo' ? 'Referência de estudo, sem calibração histórica.' : 'Intervalo hipotético informado por você.'}</p>
          {!resultado.cobertura ? <p><strong>Tábua insuficiente para cobrir toda a janela.</strong> Não é possível concluir
            se haverá coincidência com a preamar. Os extremos disponíveis abaixo são apenas consulta.</p> :
            resultado.preamaresDentro > 0 ? <p><strong>Há preamar dentro da janela simulada.</strong> A coincidência de horários
              não determina a altura da enchente nem a probabilidade de alagamento.</p> :
              <p><strong>Nenhum pico de maré está dentro da janela simulada.</strong> A maré ainda pode influenciar o escoamento;
                isso não significa ausência de risco.</p>}
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
        </div>)}
    </div>

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
