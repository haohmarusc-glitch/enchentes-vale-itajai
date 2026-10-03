import { Suspense, lazy, useMemo, useRef, useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import LegendaFaixas from '../componentes/LegendaFaixas'
import ListaRio from '../componentes/ListaRio'
import { cidadesDoRio, eventosDoRio, mareItajai, rio, topologiaDoRio } from '../dados/carregar'
import { leituraDaCidade } from '../dados/tempoReal'
import { serieDaCidade } from '../dados/serie'
import { useAoVivo } from '../dados/usarAoVivo'
import estilos from './TelaRio.module.css'

/**
 * A busca "minha rua" carrega à parte, e leva a tabela junto: são centenas de
 * cotas (Rio do Sul sozinha publica 554 logradouros), um quarto de megabyte
 * que não pode atrasar o nível do rio no celular, no meio da chuva.
 */
const CotasDeRua = lazy(() => import('../componentes/CotasDeRua'))
const MapaRios = lazy(() => import('../componentes/MapaRios'))
const AnimacaoOnda = lazy(() => import('../componentes/AnimacaoOnda'))

/**
 * A TELA DO RIO, versão 2 (03/10/2026): a lista compacta de cidades, de cima
 * para baixo, com a faixa e o número de cada uma — o detalhe fica na página da
 * cidade, a um toque. Picos históricos e perguntas sobre o histórico foram para
 * a aba Histórico de cada cidade.
 *
 * Continuam aqui: o mapa do rio (sob pedido no celular, aberto no desktop), a
 * reprodução das últimas horas e a busca "minha rua" por cidade — tocar numa
 * cidade no mapa escolhe a cidade da busca.
 */
export default function TelaRio({ rioId }: { rioId: string }) {
  const dadosRio = rio(rioId)
  const cidades = useMemo(() => cidadesDoRio(rioId), [rioId])
  const topologia = useMemo(() => topologiaDoRio(rioId), [rioId])
  const eventos = useMemo(() => eventosDoRio(rioId), [rioId])
  const aoVivo = useAoVivo()
  const { tempoReal, serie, agora } = aoVivo

  /** A cidade da busca começa na com mais histórico — é a que tem cota de rua para mostrar. */
  const padrao = useMemo(() => {
    const contagem: Record<string, number> = {}
    for (const e of eventos) contagem[e.cidade] = (contagem[e.cidade] ?? 0) + 1
    const comDados = cidades.filter((c) => (contagem[c.id] ?? 0) > 0)
    if (comDados.length === 0) return cidades[0]?.id ?? null
    return comDados.reduce((melhor, c) => ((contagem[c.id] ?? 0) > (contagem[melhor.id] ?? 0) ? c : melhor)).id
  }, [cidades, eventos])

  // No desktop o mapa fica na coluna da esquerda, então já abre; no celular
  // continua sob o botão, para não puxar o mapa numa rede ruim no meio da chuva.
  const [verMapa, setVerMapa] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(min-width: 1024px)').matches,
  )
  const [selecionadaId, setSelecionadaId] = useState<string | null>(null)
  const ruaRef = useRef<HTMLDivElement | null>(null)
  // Tocar numa cidade no mapa escolhe a cidade da busca e rola até ela: no
  // celular o detalhe fica fora da tela, e "não abre nada" é o que a pessoa vê.
  const selecionarERolar = (id: string) => {
    setSelecionadaId(id)
    requestAnimationFrame(() => ruaRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
  }

  if (!dadosRio) {
    return <p>Rio não encontrado em <code>estacoes.json</code>.</p>
  }
  const cidadeId = selecionadaId ?? padrao
  const selecionada = cidades.find((c) => c.id === cidadeId)
  const comSerie = cidades.some((c) => serieDaCidade(serie, rioId, c.id).length > 0)
  const rotaDoRio = rioId === 'itajai-mirim' ? '/mirim' : '/acu'

  return (
    <>
      <nav className={estilos.trocaRio} aria-label="Escolha o rio">
        <NavLink to="/acu" className={({ isActive }) => (isActive ? `${estilos.rio} ${estilos.rioAtivo}` : estilos.rio)}>
          Itajaí-Açu
        </NavLink>
        <NavLink to="/mirim" className={({ isActive }) => (isActive ? `${estilos.rio} ${estilos.rioAtivo}` : estilos.rio)}>
          Itajaí-Mirim
        </NavLink>
      </nav>

      <div className={estilos.cabeca}>
        <div>
          <p className={estilos.rotulo}>De cima para baixo</p>
          <h1 className={estilos.titulo}>{dadosRio.nome}</h1>
          <p className={estilos.foz}>Deságua em: {dadosRio.foz}</p>
        </div>
        <button
          type="button"
          className={`${estilos.botaoMapa} ${estilos.soCelular}`}
          aria-expanded={verMapa}
          onClick={() => setVerMapa((v) => !v)}
        >
          {verMapa ? 'Esconder mapa' : 'Mapa ▸'}
        </button>
      </div>

      <details className={`cartao ${estilos.cores}`}>
        <summary>O que as cores querem dizer?</summary>
        <LegendaFaixas />
      </details>

      <div className={estilos.layout}>
        <div className={estilos.colunaDados}>
          <ListaRio rioId={rioId} cidades={cidades} topologia={topologia} aoVivo={aoVivo} />

          {comSerie ? (
            <details className={`cartao ${estilos.cores}`}>
              <summary>Reprodução das últimas horas</summary>
              <p className={estilos.instrucao}>
                A cheia caminhando de cima para baixo — cada cidade na cor da faixa dela naquele
                instante. É o que foi medido, não previsão.
              </p>
              <Suspense fallback={<span className={`esqueleto ${estilos.esq}`} />}>
                <AnimacaoOnda rioId={rioId} cidades={cidades} serie={serie} leituras={tempoReal.leituras} />
              </Suspense>
            </details>
          ) : null}

          {selecionada ? (
            <div ref={ruaRef}>
              <div className={estilos.escolhaRua}>
                <label htmlFor="cidade-da-rua">Minha rua alaga? Cidade:</label>
                <select
                  id="cidade-da-rua"
                  value={selecionada.id}
                  onChange={(e) => setSelecionadaId(e.target.value)}
                >
                  {cidades.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nome}
                    </option>
                  ))}
                </select>
              </div>
              <Suspense fallback={<span className={`esqueleto ${estilos.esq}`} />}>
                <CotasDeRua
                  key={selecionada.id}
                  cidade={selecionada}
                  leitura={leituraDaCidade(tempoReal, rioId, selecionada.id)}
                  agora={agora}
                />
              </Suspense>
              <p className={estilos.abrirCidade}>
                <Link to={selecionada.id === 'itajai' ? '/itajai' : `${rotaDoRio}/${selecionada.id}`}>
                  Abrir a página de {selecionada.nome} →
                </Link>
              </p>
            </div>
          ) : null}
        </div>

        <div className={`${estilos.colunaMapa} ${verMapa ? '' : estilos.mapaFechado}`}>
          {verMapa ? (
            <section className="cartao">
              <h2>Mapa do rio</h2>
              <Suspense fallback={<span className={`esqueleto ${estilos.esq}`} />}>
                <MapaRios
                  rioId={rioId}
                  cidades={cidades}
                  tempoReal={tempoReal}
                  agora={agora}
                  aoSelecionar={selecionarERolar}
                  mare={mareItajai}
                />
              </Suspense>
            </section>
          ) : null}
        </div>
      </div>
    </>
  )
}
