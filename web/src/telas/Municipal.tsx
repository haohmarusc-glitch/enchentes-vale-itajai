import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { cidade, eventos } from '../dados/carregar'
import { useNivelSc } from '../dados/nivelSc'
import { useTempoReal } from '../dados/tempoReal'
import { fontesGovernamentais, historicoMunicipal } from '../logica/municipal'
import { frescor, idadeMin } from '../logica/tempoReal'
import estilos from './Municipal.module.css'
import MapaMunicipal from '../componentes/MapaMunicipal'

const PILOTO = 'ascurra'
const MUNICIPIOS = [PILOTO, 'lontras', 'rio-do-sul']
const dataHora = (data: Date | null) => data ? data.toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' }) + ' (Brasília)' : 'Horário não informado'
const numero = (n: number) => n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
export default function Municipal() {
  const estadual = useNivelSc()
  const operacional = useTempoReal()
  const [agora, setAgora] = useState(() => new Date())
  useEffect(() => { const id = setInterval(() => setAgora(new Date()), 60_000); return () => clearInterval(id) }, [])
  const historico = historicoMunicipal(eventos, PILOTO)
  const chuvaLocal = estadual.get(PILOTO)
  function leitura(id: string) {
    const c = cidade('itajai-acu', id)!
    const bruto = estadual.get(id)
    const locais = operacional.leituras.filter((l) => l.cidade === id && l.rio === 'itajai-acu')
    const linhas = locais.length ? locais.map((l) => ({ nome: l.estacao, nivel: l.nivel_m, data: l.medidoEm, bruto: false }))
      : bruto ? [{ nome: bruto.estacao, nivel: bruto.nivelBrutoM, data: bruto.medidoEm, bruto: true }] : []
    return <article className={estilos.cartao} key={id}>
      <h3>{c.nome}</h3>
      {linhas.length === 0 && <p>Nível indisponível nesta consulta.</p>}
      {linhas.map((l) => <div key={l.nome}>
        <p><strong>{numero(l.nivel)} m</strong> · {l.nome}</p>
        <p>Medição: {dataHora(l.data)}</p>
        <p>{!l.data || frescor(idadeMin(l.data, agora)) === 'velha' ? 'Leitura sem atualidade confirmada.' : 'Leitura dentro da janela de atualização.'}</p>
        <p>{l.bruto ? 'Referência própria da estação estadual. Classificação automática não disponível.' : 'Nível observado na régua identificada. Classificação não apresentada nesta etapa do piloto.'}</p>
      </div>)}
      <p>Fonte: <a href={locais.length && id === 'rio-do-sul' ? 'https://defesacivil.riodosul.sc.gov.br/' : 'https://monitoramento.defesacivil.sc.gov.br/mapa'} target="_blank" rel="noreferrer">Defesa Civil · consultar origem</a></p>
    </article>
  }
  return <div className={estilos.pagina}>
    <header><p>Enchentes do Vale · piloto municipal</p><h1>Monitor de Ascurra</h1>
      <p>Dados observados e histórico com fontes governamentais. Não é um sistema oficial de alerta.</p>
      <nav aria-label="Seções municipais">{[['local', 'Minha cidade'], ['montante', 'Água chegando'], ['historico', 'Histórico']].map(([id, titulo]) => <button key={id} onClick={() => document.getElementById(id!)?.scrollIntoView()}>{titulo}</button>)}</nav>
    </header>
    <section id="local"><h2>Minha cidade</h2>{leitura(PILOTO)}
      <article className={estilos.cartao}><h3>Referências municipais</h3><p>{cidade('itajai-acu', PILOTO)?.cotas_aviso_publico}</p>
        <p>Fonte: Defesa Civil de Ascurra, resposta ao ofício C18, 11/09/2026. As faixas são referências; esta tela não emite alertas.</p>
        <h3>Chuva observada · últimas 24 horas</h3>
        {chuvaLocal?.chuva24hMm != null ? <>
          <p><strong>{numero(chuvaLocal.chuva24hMm)} mm</strong> · {chuvaLocal.estacao}</p>
          <p>Carimbo da estação: {dataHora(chuvaLocal.medidoEm)}. {!chuvaLocal.medidoEm || frescor(idadeMin(chuvaLocal.medidoEm, agora)) === 'velha' ? 'Atualidade não confirmada.' : 'Dentro da janela de atualização.'}</p>
          <p>Acumulado publicado pela estação; não é uma média de chuva de todo o município. A fonte não fornece um horário independente para este acumulado no arquivo utilizado.</p>
        </> : <p>Acumulado de 24 horas indisponível nesta consulta. Ausência de leitura não significa chuva zero.</p>}
        <p>Fonte da chuva: <a href="https://monitoramento.defesacivil.sc.gov.br/mapa">Defesa Civil de Santa Catarina</a>. Sete dias: série completa ainda não disponível para comparação histórica.</p>
      </article>
    </section>
    <section id="montante"><h2>Água chegando · observações de montante</h2>
      <p>Lontras e Rio do Sul ficam rio acima no tronco do Itajaí-Açu. Esta seção apresenta medições, sem estimar chegada ou nível futuro. Cada régua tem seu próprio zero; as alturas não são comparadas entre cidades.</p>
      <div className={estilos.grade}>{MUNICIPIOS.slice(1).map(leitura)}</div>
    </section>
    {cidade('itajai-acu', PILOTO)?.coordenadas && <MapaMunicipal cidade={PILOTO} centro={cidade('itajai-acu', PILOTO)!.coordenadas!} leituras={operacional.leituras.filter((l) => l.cidade === PILOTO)} agora={agora} />}
    <section id="historico"><h2>Histórico de Ascurra</h2>
      {historico.length ? <div className={estilos.tabela}><table><thead><tr><th>Evento</th><th>Pico</th><th>Referência</th><th>Fonte</th></tr></thead><tbody>{historico.map((e) => <tr key={e.data + e.fonte}><td>{e.data}</td><td>{numero(e.pico_m)} m</td><td>{e.referencia ?? 'Não documentada'}{e.nota && <p>{e.nota}</p>}</td><td>{fontesGovernamentais(e.fonte).map((url) => <a href={url} key={url}>Consultar documento governamental</a>)}</td></tr>)}</tbody></table></div> : <p>Ainda não há picos de Ascurra com endereço de fonte governamental identificado no cadastro. Nenhuma comparação numérica foi calculada.</p>}
      <p>Camadas históricas de inundação de Ascurra: não disponíveis no cadastro.</p>
    </section>
    <footer><p>Última conferência da idade das leituras: {dataHora(agora)}. A hora da medição aparece em cada estação.</p>
      <p>Piloto dentro do site regional; ainda não é uma distribuição de código e arquivos exclusiva do município.</p><Link to="/">Voltar ao site regional</Link></footer>
  </div>
}
