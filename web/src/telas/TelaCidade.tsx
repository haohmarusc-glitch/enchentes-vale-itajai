import { Suspense, lazy, useMemo } from 'react'
import { Link, useParams } from 'react-router-dom'
import AvisoLegal from '../componentes/AvisoLegal'
import ChuvaAoVivo from '../componentes/ChuvaAoVivo'
import NivelAoVivo from '../componentes/NivelAoVivo'
import PainelPrevisao from '../componentes/PainelPrevisao'
import PainelSePicoAgora from '../componentes/PainelSePicoAgora'
import ReguasDaCidade from '../componentes/ReguasDaCidade'
import SeloConfianca from '../componentes/SeloConfianca'
import {
  cidadesDoRio,
  eventosDoRio,
  estacoesTempoReal,
  mareItajai,
  rio,
  topologiaDoRio,
  trechos,
} from '../dados/carregar'
import { leituraDaCidade, leiturasDaCidade, useTempoReal } from '../dados/tempoReal'
import { useNivelSc } from '../dados/nivelSc'
import { serieDaCidade, useSerieRecente } from '../dados/serie'
import { chuvaDaCidade } from '../logica/chuva'
import { metros } from '../logica/formato'
import { reguasComCota } from '../logica/reguas'
import { caminho, faixaHoras } from '../logica/transito'
import estilos from './TelaCidade.module.css'

const CotasDeRua = lazy(() => import('../componentes/CotasDeRua'))
const GraficoPicos = lazy(() => import('../componentes/GraficoPicos'))
const LinhaDoTempo = lazy(() => import('../componentes/LinhaDoTempo'))
const MapaRios = lazy(() => import('../componentes/MapaRios'))

/**
 * A página de UMA cidade.
 *
 * POR QUE EXISTE
 * A tela do rio mostra as doze cidades e o detalhe da que estiver selecionada.
 * Quem mora em Gaspar não quer as doze: quer Gaspar, com o mapa já no trecho
 * dela, o nível na régua dela, as ruas dela e de onde a água vem. E quer poder
 * mandar o endereço para o vizinho — `/acu/gaspar` é um endereço; "abra o Açu e
 * toque em Gaspar" não é.
 *
 * O QUE ELA NÃO FAZ
 * Não inventa vizinha. O Açu é uma ÁRVORE (ver `docs/TOPOLOGIA-CANONICA.md`):
 * "a cidade de cima" só existe ao longo do TRONCO. Para quem está numa
 * cabeceira paralela ou num afluente lateral, a página diz isso com todas as
 * letras em vez de encadear um tempo de descida que a geografia não sustenta —
 * que é o erro que faria alguém esperar a água por um caminho que ela não faz.
 */
/**
 * O pedaço da URL para o id do rio no cadastro. A URL usa a mesma palavra que
 * as telas de rio já usam (`/acu`, `/mirim`) — trocar por `itajai-acu` no
 * endereço só dificultaria ditar o link por telefone.
 */
const RIO_DA_URL: Record<string, string> = {
  acu: 'itajai-acu',
  mirim: 'itajai-mirim',
}

export default function TelaCidade() {
  const { rioId: apelido = '', cidadeId = '' } = useParams()
  const rioId = RIO_DA_URL[apelido] ?? ''
  const dadosRio = rio(rioId)
  const cidades = useMemo(() => cidadesDoRio(rioId), [rioId])
  const topologia = useMemo(() => topologiaDoRio(rioId), [rioId])
  const eventos = useMemo(() => eventosDoRio(rioId), [rioId])

  const tempoReal = useTempoReal()
  const nivelSc = useNivelSc()
  const serie = useSerieRecente()
  const agora = useMemo(() => new Date(), [tempoReal])

  const cidade = cidades.find((c) => c.id === cidadeId)

  /**
   * A sequência que a água realmente segue. No Açu é o tronco; no Mirim, onde
   * não há ramificação, é a própria ordem das cidades. Fora dela não se afirma
   * montante nem jusante.
   */
  const eixo = useMemo(() => {
    if (topologia?.tronco_sequencia?.length) return topologia.tronco_sequencia
    return cidades.map((c) => c.id)
  }, [topologia, cidades])

  const iEixo = eixo.indexOf(cidadeId)
  const montante = iEixo > 0 ? cidades.find((c) => c.id === eixo[iEixo - 1]) : undefined
  const jusante =
    iEixo >= 0 && iEixo < eixo.length - 1 ? cidades.find((c) => c.id === eixo[iEixo + 1]) : undefined

  const doMontante = useMemo(
    () => (montante && cidade ? caminho(trechos, rioId, montante.id, cidade.id) : null),
    [montante, cidade, rioId],
  )
  const paraJusante = useMemo(
    () => (cidade && jusante ? caminho(trechos, rioId, cidade.id, jusante.id) : null),
    [cidade, jusante, rioId],
  )

  if (!dadosRio) {
    return (
      <>
        <h1>Endereço não encontrado</h1>
        <p>
          <code>/{apelido}</code> não é um rio deste site. As páginas de cidade ficam em{' '}
          <code>/acu/&lt;cidade&gt;</code> e <code>/mirim/&lt;cidade&gt;</code>.
        </p>
        <p>
          <Link to="/acu">Itajaí-Açu</Link> · <Link to="/mirim">Itajaí-Mirim</Link> ·{' '}
          <Link to="/itajai">Itajaí (foz)</Link>
        </p>
      </>
    )
  }
  if (!cidade) {
    return (
      <>
        <h1>Cidade não encontrada</h1>
        <p>
          <code>{cidadeId}</code> não está no cadastro de {dadosRio.nome}.{' '}
          <Link to={rioId === 'itajai-mirim' ? '/mirim' : '/acu'}>Ver o rio inteiro</Link>.
        </p>
      </>
    )
  }

  const leitura = leituraDaCidade(tempoReal, rioId, cidade.id)
  const daCidade = leiturasDaCidade(tempoReal, rioId, cidade.id)
  const reguas = reguasComCota(estacoesTempoReal, rioId, cidade.id)
  const chuva = chuvaDaCidade(tempoReal.chuva, cidade.id)
  const serieDela = serieDaCidade(serie, rioId, cidade.id)
  const picos = eventos.filter((e) => e.cidade === cidade.id)
  const cotas = Object.entries(cidade.cotas_m ?? {}).filter(([, v]) => typeof v === 'number')
  const rotaDoRio = rioId === 'itajai-mirim' ? '/mirim' : '/acu'
  const bruto = nivelSc.get(cidade.id) ?? null

  return (
    <>
      <p className={estilos.migalha}>
        <Link to={rotaDoRio}>{dadosRio.nome}</Link> → <strong>{cidade.nome}</strong>
      </p>
      <h1>{cidade.nome}</h1>

      <AvisoLegal />

      {/* AGORA — o cartão que a pessoa abriu a página para ver. Vem primeiro, e
          diz "sem dado" com todas as letras quando é o caso: cartão vazio
          parece normalidade, e normalidade é a afirmação mais perigosa que
          este site pode fazer sem medir. */}
      <section className="cartao">
        <h2>Agora</h2>
        {leitura ? (
          <p className={estilos.agora}>
            <NivelAoVivo leitura={leitura} cidade={cidade} agora={agora} />
          </p>
        ) : bruto ? (
          <p className={estilos.semDado}>
            Sem régua municipal aqui. A rede estadual publica{' '}
            <strong>{metros(bruto.nivelBrutoM)}</strong>, numa régua com{' '}
            <strong>zero próprio</strong> — serve para ver o rio subir ou baixar,{' '}
            <strong>não</strong> para comparar com as cotas desta cidade.
          </p>
        ) : (
          <p className={estilos.semDado}>
            <strong>Sem leitura ao vivo.</strong> Isto não quer dizer que o rio esteja
            baixo: quer dizer que não estamos medindo. Acompanhe pela Defesa Civil.
          </p>
        )}

        {reguas.length > 0 ? (
          <ReguasDaCidade reguas={reguas} cidade={cidade.nome} agrupadoPorCurso />
        ) : null}

        {daCidade.length > 1 && reguas.length === 0 ? (
          <p className={estilos.instrucao}>
            {daCidade.length} réguas nesta cidade, cada uma com o seu zero — os metros
            não se comparam entre elas.
          </p>
        ) : null}

        {chuva ? <ChuvaAoVivo resumo={chuva} agora={agora} cidade={cidade.nome} /> : null}

        {cotas.length > 0 ? (
          <>
            <h3 className={estilos.subtitulo}>Cotas de referência, na régua daqui</h3>
            <ul className={estilos.cotas}>
              {cotas.map(([chave, valor]) => (
                <li key={chave}>
                  <span className={estilos.cotaNome}>{chave.replace(/_/g, ' ')}</span>
                  <strong>{metros(valor)}</strong>
                </li>
              ))}
            </ul>
            <p className={estilos.instrucao}>
              Cada cidade tem a sua régua, com zero próprio.{' '}
              <strong>Estes metros não se comparam</strong> com os de outra cidade.
            </p>
          </>
        ) : (
          <p className={estilos.instrucao}>
            Esta cidade ainda não tem cota de acionamento no cadastro. Sem ela, um número
            na régua não vira faixa — e o site não a pinta nem dispara aviso por ela.
          </p>
        )}
      </section>

      {/* MAPA já no trecho desta cidade — é o que o zoom do Monitor destravou.
          O rio inteiro continua desenhado; só a janela é menor, então rolar
          para os lados ainda mostra de onde a água vem. */}
      <section className="cartao">
        <h2>O rio em {cidade.nome}</h2>
        {cidade.coordenadas ? (
          <Suspense fallback={<p className={estilos.instrucao}>Carregando o mapa…</p>}>
            <MapaRios
              rioId={rioId}
              cidades={cidades}
              tempoReal={tempoReal}
              agora={agora}
              mare={mareItajai}
              focarEm={cidade}
            />
          </Suspense>
        ) : (
          <p className={estilos.instrucao}>
            Ainda não temos a coordenada da régua desta cidade, então não há onde
            aproximar o mapa. Chutar a posição num mapa de enchente é pior que não
            aproximar. <Link to={rotaDoRio}>Ver o rio inteiro</Link>.
          </p>
        )}
      </section>

      {/* DE ONDE VEM / PARA ONDE VAI — só ao longo do eixo. */}
      <section className="cartao">
        <h2>De onde a água vem, para onde vai</h2>
        {iEixo < 0 ? (
          <p className={estilos.instrucao}>
            {cidade.nome} não está na sequência do tronco — é{' '}
            {cidade.ramo ? <>uma cabeceira ou afluente ({cidade.ramo.replace(/_/g, ' ')})</> : 'um ponto fora do eixo'}
            . A cheia daqui <strong>não é a mesma</strong> que desce o rio principal, então
            encadear um tempo de descida por esta cidade daria resultado errado. Ver a{' '}
            <Link to={rotaDoRio}>tela do rio</Link> para a árvore inteira.
          </p>
        ) : (
          <ul className={estilos.vizinhas}>
            <li>
              <span className={estilos.rotuloVizinha}>Acima (a água vem de)</span>
              {montante ? (
                <>
                  <Link to={`${rotaDoRio}/${montante.id}`}>{montante.nome}</Link>
                  {doMontante ? (
                    <>
                      {' '}— leva <strong>{faixaHoras(doMontante)}</strong> para chegar aqui{' '}
                      <SeloConfianca
                        nivel={doMontante.confianca}
                        fonte={doMontante.fontes.join('; ')}
                        tipo="trecho"
                      />
                    </>
                  ) : (
                    <> — tempo de descida ainda não levantado para este trecho</>
                  )}
                </>
              ) : (
                <>é o início do tronco nesta tela</>
              )}
            </li>
            <li>
              <span className={estilos.rotuloVizinha}>Abaixo (a água segue para)</span>
              {jusante ? (
                <>
                  <Link to={`${rotaDoRio}/${jusante.id}`}>{jusante.nome}</Link>
                  {paraJusante ? (
                    <>
                      {' '}— leva <strong>{faixaHoras(paraJusante)}</strong> daqui até lá{' '}
                      <SeloConfianca
                        nivel={paraJusante.confianca}
                        fonte={paraJusante.fontes.join('; ')}
                        tipo="trecho"
                      />
                    </>
                  ) : (
                    <> — tempo de descida ainda não levantado para este trecho</>
                  )}
                </>
              ) : (
                <>é o fim do curso nesta tela</>
              )}
            </li>
          </ul>
        )}
        <p className={estilos.instrucao}>
          O tempo é sempre um <strong>intervalo</strong>, nunca um horário exato: depende
          de quanto choveu, de onde e de quanto o solo já está encharcado.
        </p>
      </section>

      {leitura ? (
        <PainelSePicoAgora
          rioId={rioId}
          cidades={cidades}
          trechos={trechos}
          origem={cidade}
          leitura={leitura}
          agora={agora}
        />
      ) : null}

      <Suspense fallback={<p className={estilos.instrucao}>Carregando as cotas de rua…</p>}>
        <CotasDeRua cidade={cidade} leitura={leitura} agora={agora} />
      </Suspense>

      {serieDela.length > 0 && cotas.length > 0 ? (
        <section className="cartao">
          <h2>Últimas horas em {cidade.nome}</h2>
          <Suspense fallback={<p className={estilos.instrucao}>Carregando a linha do tempo…</p>}>
            <LinhaDoTempo cidade={cidade} serie={serieDela} agora={agora} />
          </Suspense>
        </section>
      ) : null}

      <section className="cartao">
        <h2>Picos históricos em {cidade.nome}</h2>
        {picos.length > 0 ? (
          <Suspense fallback={<p className={estilos.instrucao}>Carregando o gráfico…</p>}>
            <GraficoPicos eventos={picos} cidade={cidade} nomeCidade={cidade.nome} />
          </Suspense>
        ) : (
          <p className={estilos.instrucao}>
            Nenhum pico histórico levantado para {cidade.nome} ainda. A ausência é do{' '}
            <strong>nosso levantamento</strong>, não da história da cidade.
          </p>
        )}
      </section>

      {jusante ? (
        <PainelPrevisao
          rioId={rioId}
          eventos={eventos}
          trechos={trechos}
          montante={cidade}
          jusante={jusante}
        />
      ) : null}

      {cidade.observacao ? (
        <section className="cartao">
          <h2>Observação sobre esta régua</h2>
          <p>{cidade.observacao}</p>
        </section>
      ) : null}
    </>
  )
}
