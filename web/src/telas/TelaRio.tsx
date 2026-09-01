import { Suspense, lazy, useMemo, useState } from 'react'
import AvisoLegal from '../componentes/AvisoLegal'
import DiagramaRio from '../componentes/DiagramaRio'
import PainelPrevisao from '../componentes/PainelPrevisao'
import PainelSePicoAgora from '../componentes/PainelSePicoAgora'
import { cidadesDoRio, eventosDoRio, rio, trechos } from '../dados/carregar'
import { parear } from '../logica/previsao'
import { leituraDaCidade, useTempoReal } from '../dados/tempoReal'
import { serieDaCidade, useSerieRecente } from '../dados/serie'
import estilos from './TelaRio.module.css'

/**
 * O gráfico carrega a biblioteca recharts, que sozinha pesa mais que o resto do
 * site inteiro. Fica em carregamento sob demanda para que o diagrama do rio, os
 * tempos de trânsito e os avisos apareçam primeiro — numa noite de chuva, com
 * rede ruim, é essa informação que precisa chegar.
 */
const GraficoPicos = lazy(() => import('../componentes/GraficoPicos'))

/**
 * A busca "minha rua" carrega à parte, e leva a tabela junto.
 *
 * São 611 cotas e crescendo — Rio do Sul sozinha publica 554 logradouros. No
 * pacote inicial isso é um quarto de megabyte que todo mundo baixa e
 * interpreta, inclusive quem abriu o site no celular, no meio da chuva, só
 * para ver o nível do rio.
 */
const CotasDeRua = lazy(() => import('../componentes/CotasDeRua'))
const MapaRios = lazy(() => import('../componentes/MapaRios'))
const LinhaDoTempo = lazy(() => import('../componentes/LinhaDoTempo'))
const AnimacaoOnda = lazy(() => import('../componentes/AnimacaoOnda'))

export default function TelaRio({ rioId }: { rioId: string }) {
  const dadosRio = rio(rioId)
  const cidades = useMemo(() => cidadesDoRio(rioId), [rioId])
  const eventos = useMemo(() => eventosDoRio(rioId), [rioId])

  const registrosPorCidade = useMemo(() => {
    const contagem: Record<string, number> = {}
    for (const e of eventos) contagem[e.cidade] = (contagem[e.cidade] ?? 0) + 1
    return contagem
  }, [eventos])

  /** Começa na cidade com mais histórico — é a que tem algo para mostrar. */
  const padrao = useMemo(() => {
    const comDados = cidades.filter((c) => (registrosPorCidade[c.id] ?? 0) > 0)
    if (comDados.length === 0) return cidades[0]?.id ?? null
    return comDados.reduce((melhor, c) =>
      (registrosPorCidade[c.id] ?? 0) > (registrosPorCidade[melhor.id] ?? 0) ? c : melhor,
    ).id
  }, [cidades, registrosPorCidade])

  const tempoReal = useTempoReal()
  const serie = useSerieRecente()
  // Um único "agora" por render: assim todos os cartões contam a idade das
  // leituras a partir do mesmo instante.
  const agora = useMemo(() => new Date(), [tempoReal])
  const [verMapa, setVerMapa] = useState(false)

  const [selecionadaId, setSelecionadaId] = useState<string | null>(null)
  const cidadeId = selecionadaId ?? padrao
  const selecionada = cidades.find((c) => c.id === cidadeId)
  const indice = cidades.findIndex((c) => c.id === cidadeId)

  /**
   * Cidade a jusante para a estimativa.
   *
   * A vizinha imediata quase sempre não tem pico levantado, e parear com ela só
   * produz "dados insuficientes" — escondendo a comparação que existe mais
   * abaixo. Procura a primeira cidade a jusante com algum evento em comum; se
   * nenhuma tiver, cai na vizinha, e a tela explica o que falta.
   */
  const jusante = useMemo(() => {
    if (indice < 0) return undefined
    for (let j = indice + 1; j < cidades.length; j++) {
      const alvo = cidades[j]!
      if (parear(eventos, cidades[indice]!.id, alvo.id).length > 0) return alvo
    }
    return cidades[indice + 1]
  }, [cidades, eventos, indice])

  if (!dadosRio) {
    return <p>Rio não encontrado em <code>estacoes.json</code>.</p>
  }

  const semCobertura = cidades.filter((c) => (registrosPorCidade[c.id] ?? 0) === 0).length

  return (
    <>
      <h1>{dadosRio.nome}</h1>
      <p className={estilos.foz}>Deságua em: {dadosRio.foz}</p>

      <AvisoLegal />

      <section className="cartao">
        <h2>Curso do rio, de cima para baixo</h2>
        <p className={estilos.instrucao}>
          A água desce nesta ordem. Toque numa cidade para ver o histórico dela e a estimativa para a
          cidade seguinte.
        </p>
        <DiagramaRio
          rioId={rioId}
          cidades={cidades}
          trechos={trechos}
          registrosPorCidade={registrosPorCidade}
          cidadeSelecionada={cidadeId}
          aoSelecionar={setSelecionadaId}
          tempoReal={tempoReal}
          agora={agora}
        />
        {semCobertura > 0 ? (
          <p className={estilos.cobertura}>
            {semCobertura} de {cidades.length} cidades ainda não têm pico histórico levantado. Elas
            aparecem no diagrama para deixar claro o que falta, não para sugerir que há dado.
          </p>
        ) : null}
      </section>

      <section className="cartao">
        <h2>Mapa do rio</h2>
        {verMapa ? (
          <Suspense fallback={<p className={estilos.instrucao}>Carregando o mapa…</p>}>
            <MapaRios
              rioId={rioId}
              cidades={cidades}
              tempoReal={tempoReal}
              agora={agora}
              aoSelecionar={setSelecionadaId}
            />
          </Suspense>
        ) : (
          <>
            <p className={estilos.instrucao}>
              O rio no mapa, com cada trecho na cor da faixa da cidade a montante — a mesma do
              diagrama. Aproxime para ver os nomes; toque numa cidade para as cotas de rua e o
              abrigo dela. Carrega sob pedido para não pesar no celular.
            </p>
            <button type="button" className={estilos.botaoMapa} onClick={() => setVerMapa(true)}>
              Ver mapa do rio
            </button>
          </>
        )}
      </section>

      {cidades.some((c) => serieDaCidade(serie, rioId, c.id).length > 0) ? (
        <section className="cartao">
          <h2>Reprodução das últimas horas</h2>
          <p className={estilos.instrucao}>
            Toque em reproduzir para ver a cheia caminhar de cima para baixo — cada cidade na cor
            da faixa dela naquele instante. É o que foi medido, não previsão.
          </p>
          <Suspense fallback={<p className={estilos.instrucao}>Carregando a reprodução…</p>}>
            <AnimacaoOnda rioId={rioId} cidades={cidades} serie={serie} />
          </Suspense>
        </section>
      ) : null}

      {selecionada && leituraDaCidade(tempoReal, rioId, selecionada.id) ? (
        <PainelSePicoAgora
          rioId={rioId}
          cidades={cidades}
          trechos={trechos}
          origem={selecionada}
          leitura={leituraDaCidade(tempoReal, rioId, selecionada.id)!}
          agora={agora}
        />
      ) : null}

      {selecionada ? (
        <Suspense fallback={<p className={estilos.instrucao}>Carregando as cotas de rua…</p>}>
          <CotasDeRua
            cidade={selecionada}
            leitura={leituraDaCidade(tempoReal, rioId, selecionada.id)}
            agora={agora}
          />
        </Suspense>
      ) : null}

      {selecionada && selecionada.cotas_m && Object.keys(selecionada.cotas_m).length > 0 ? (
        <section className="cartao">
          <h2>Últimas horas em {selecionada.nome}</h2>
          <p className={estilos.instrucao}>
            Como o nível vem se comportando na régua desta cidade. A linha cruza as
            faixas de cota — é a cheia subindo ou baixando.
          </p>
          <Suspense fallback={<p className={estilos.instrucao}>Carregando a linha do tempo…</p>}>
            <LinhaDoTempo
              cidade={selecionada}
              serie={serieDaCidade(serie, rioId, selecionada.id)}
              agora={agora}
            />
          </Suspense>
        </section>
      ) : null}

      {selecionada ? (
        <section className="cartao">
          <h2>Picos históricos em {selecionada.nome}</h2>
          <Suspense fallback={<p className={estilos.instrucao}>Carregando o gráfico…</p>}>
            <GraficoPicos
              eventos={eventos.filter((e) => e.cidade === selecionada.id)}
              cidade={selecionada}
              nomeCidade={selecionada.nome}
            />
          </Suspense>
        </section>
      ) : null}

      {selecionada && jusante ? (
        <PainelPrevisao
          rioId={rioId}
          eventos={eventos}
          trechos={trechos}
          montante={selecionada}
          jusante={jusante}
        />
      ) : selecionada ? (
        <section className="cartao">
          <h2>{selecionada.nome} é o fim do curso nesta tela</h2>
          <p className={estilos.instrucao}>
            Não há cidade a jusante para estimar. Para a chegada dos picos na foz, veja a tela de{' '}
            Itajaí.
          </p>
        </section>
      ) : null}
    </>
  )
}
