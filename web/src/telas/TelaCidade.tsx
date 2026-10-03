import { Suspense, lazy, useMemo, useRef, type KeyboardEvent } from 'react'
import { Link, Navigate, useParams, useSearchParams } from 'react-router-dom'
import { BotaoLetra, BotaoMinhaCidade } from '../componentes/BotoesPreferencia'
import CartaoAgora from '../componentes/CartaoAgora'
import { AcoesDaCidade, CartaoDescida } from '../componentes/CartoesDaCidade'
import ChuvaAoVivo from '../componentes/ChuvaAoVivo'
import EstadoDasBarragens from '../componentes/EstadoDasBarragens'
import LegendaFaixas from '../componentes/LegendaFaixas'
import PainelCenarioAnterior from '../componentes/PainelCenarioAnterior'
import ReguasDaCidade from '../componentes/ReguasDaCidade'
import { cidadesDoRio, eventosDoRio, estacoesTempoReal, rio, topologiaDoRio } from '../dados/carregar'
import { barragensDaCidade, useBarragens } from '../dados/barragens'
import { tendencia } from '../dados/serie'
import { estadoDaCidade, useAoVivo } from '../dados/usarAoVivo'
import { chuvaDaCidade } from '../logica/chuva'
import { ROTULO_CONFIANCA, fonteTempoReal, metros, rotuloCota } from '../logica/formato'
import { reguasComCota } from '../logica/reguas'
import estilos from './TelaCidade.module.css'

const MapaCotasItuporanga = lazy(() => import('../componentes/MapaCotasItuporanga'))
const CotasDeRua = lazy(() => import('../componentes/CotasDeRua'))
const GraficoPicos = lazy(() => import('../componentes/GraficoPicos'))
const LinhaDoTempo = lazy(() => import('../componentes/LinhaDoTempo'))
/** O chat do histórico (sem IA, sem API) carrega à parte — ver `chat-local/ChatLocal.tsx`. */
const ChatLocal = lazy(() => import('../chat-local/ChatLocal'))

/**
 * A página de UMA cidade.
 *
 * POR QUE EXISTE
 * Quem mora em Gaspar não quer as doze cidades: quer Gaspar, com o nível na
 * régua dela, as ruas dela e de onde a água vem. E quer poder mandar o endereço
 * para o vizinho — `/acu/gaspar` é um endereço; "abra o Açu e toque em Gaspar"
 * não é.
 *
 * VERSÃO 2 (03/10/2026): quatro abas, porque a página tinha dez cartões
 * empilhados e "minha rua", a pergunta mais provável, ficava no meio.
 *  - **Agora**: o cartão do nível, as ações, de onde a água vem e para onde
 *    vai, chuva, barragem, últimas horas e as cotas;
 *  - **Minha rua**: a busca das cotas de rua;
 *  - **Histórico**: os picos, a marca antiga mais próxima acima (D3: só aqui,
 *    para não soar previsão ao lado do nível) e as perguntas sobre o histórico;
 *  - **Fontes**: de onde vem cada número, a estação, e as notas técnicas.
 * A aba vai na URL (`?aba=rua`) para o endereço levar direto a ela.
 *
 * O QUE ELA NÃO FAZ
 * Não inventa vizinha. O Açu é uma ÁRVORE (ver `docs/TOPOLOGIA-CANONICA.md`):
 * "a cidade de cima" só existe ao longo do TRONCO.
 */
const RIO_DA_URL: Record<string, string> = {
  acu: 'itajai-acu',
  mirim: 'itajai-mirim',
}

/**
 * Cidades que já têm tela PRÓPRIA, mais rica que esta. Itajaí: a tela da foz
 * explica por que não existe "o nível de Itajaí" (onze réguas, zeros
 * diferentes); uma página genérica ao lado a contradiria.
 */
const TELA_PROPRIA: Record<string, string> = {
  itajai: '/itajai',
}

const ABAS = [
  { id: 'agora', rotulo: 'Agora' },
  { id: 'rua', rotulo: 'Minha rua' },
  { id: 'historico', rotulo: 'Histórico' },
  { id: 'fontes', rotulo: 'Fontes' },
] as const
type Aba = (typeof ABAS)[number]['id']

export default function TelaCidade() {
  const { rioId: apelido = '', cidadeId = '' } = useParams()
  const [busca, setBusca] = useSearchParams()
  const rioId = RIO_DA_URL[apelido] ?? ''
  const dadosRio = rio(rioId)
  const cidades = useMemo(() => cidadesDoRio(rioId), [rioId])
  const topologia = useMemo(() => topologiaDoRio(rioId), [rioId])
  const eventos = useMemo(() => eventosDoRio(rioId), [rioId])
  const aoVivo = useAoVivo()
  // Antes de qualquer `return` condicional: hook depois de saída antecipada
  // quebra a ordem entre renderizações.
  const mapaBarragens = useBarragens()
  const abasRef = useRef<(HTMLButtonElement | null)[]>([])

  const pedida = busca.get('aba')
  const aba: Aba = ABAS.some((a) => a.id === pedida) ? (pedida as Aba) : 'agora'
  const irPara = (nova: Aba, focar = false) => {
    const proxima = new URLSearchParams(busca)
    if (nova === 'agora') proxima.delete('aba')
    else proxima.set('aba', nova)
    setBusca(proxima, { replace: true })
    if (focar) abasRef.current[ABAS.findIndex((a) => a.id === nova)]?.focus()
  }
  // Setas trocam de aba, como o leitor de tela espera de um `tablist`.
  const teclaNasAbas = (e: KeyboardEvent) => {
    const i = ABAS.findIndex((a) => a.id === aba)
    if (e.key === 'ArrowRight') irPara(ABAS[(i + 1) % ABAS.length]!.id, true)
    else if (e.key === 'ArrowLeft') irPara(ABAS[(i - 1 + ABAS.length) % ABAS.length]!.id, true)
    else return
    e.preventDefault()
  }

  const cidade = cidades.find((c) => c.id === cidadeId)
  const telaPropria = TELA_PROPRIA[cidadeId]

  if (telaPropria && dadosRio) return <Navigate to={telaPropria} replace />

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

  const rioUrl = apelido === 'mirim' ? 'mirim' : 'acu'
  const estado = estadoDaCidade(cidade, rioId, aoVivo)
  const { leitura } = estado
  const { agora, tempoReal, serie } = aoVivo
  const chuva = chuvaDaCidade(tempoReal.chuva, cidade.id)
  const picos = eventos.filter((e) => e.cidade === cidade.id)
  const cotas = Object.entries(cidade.cotas_m ?? {}).filter(([, v]) => typeof v === 'number') as [string, number][]
  const reguas = reguasComCota(estacoesTempoReal, rioId, cidade.id)
  const barragens = barragensDaCidade(mapaBarragens, cidade.id)

  return (
    <>
      <div className={estilos.cabeca}>
        <div className={estilos.titulos}>
          <p className={estilos.migalha}>
            <Link to={`/${rioUrl}`}>{dadosRio.nome}</Link> ›
          </p>
          <h1 className={estilos.nome}>{cidade.nome}</h1>
        </div>
        <div className={estilos.preferencias}>
          <BotaoMinhaCidade cidade={cidade} rio={rioUrl} />
          <BotaoLetra />
        </div>
      </div>

      <div className={estilos.abas} role="tablist" aria-label={`Seções de ${cidade.nome}`} onKeyDown={teclaNasAbas}>
        {ABAS.map((a, i) => (
          <button
            key={a.id}
            ref={(el) => {
              abasRef.current[i] = el
            }}
            type="button"
            role="tab"
            id={`aba-${a.id}`}
            aria-selected={aba === a.id}
            aria-controls={`painel-${a.id}`}
            tabIndex={aba === a.id ? 0 : -1}
            className={`${estilos.aba} ${aba === a.id ? estilos.abaAtiva : ''}`}
            onClick={() => irPara(a.id)}
          >
            {a.rotulo}
          </button>
        ))}
      </div>

      <div
        key={aba}
        role="tabpanel"
        id={`painel-${aba}`}
        aria-labelledby={`aba-${aba}`}
        className={estilos.painel}
      >
        {aba === 'agora' ? (
          <>
            <CartaoAgora cidade={cidade} rioId={rioId} aoVivo={aoVivo} estado={estado}>
              <AcoesDaCidade cidade={cidade} rioId={rioId} aoVivo={aoVivo} estado={estado} />
            </CartaoAgora>

            <CartaoDescida cidade={cidade} rioId={rioId} cidades={cidades} topologia={topologia} />

            {chuva ? (
              <section className="cartao">
                <h2>Chuva em {cidade.nome}</h2>
                <ChuvaAoVivo resumo={chuva} agora={agora} cidade={cidade.nome} />
              </section>
            ) : tempoReal.chuvaOk ? null : (
              <p className={estilos.instrucao}>🌧 Chuva: não foi possível coletar agora.</p>
            )}

            {/* O estado da barragem junto do nível: é o que explica por que o
                número está onde está. Só nas cidades com barragem acima. */}
            {barragens.length > 0 ? (
              <section className="cartao">
                <EstadoDasBarragens barragens={barragens} agora={agora} tendencia={tendencia(estado.serie)} />
              </section>
            ) : null}

            {estado.serie.length > 0 && cotas.length > 0 ? (
              <section className="cartao">
                <h2>Últimas horas em {cidade.nome}</h2>
                <Suspense fallback={<span className={`esqueleto ${estilos.esqGrafico}`} />}>
                  <LinhaDoTempo cidade={cidade} serie={estado.serie} agora={agora} resgates={serie.resgates} />
                </Suspense>
              </section>
            ) : null}

            <details className={`cartao ${estilos.detalhes}`}>
              <summary>Cotas de referência, na régua daqui</summary>
              {cotas.length > 0 ? (
                <>
                  <ul className={estilos.cotas}>
                    {cotas.map(([chave, valor]) => (
                      <li key={chave}>
                        <span className={estilos.cotaNome}>{rotuloCota(chave, cidade.cotas_nomes_na_fonte)}</span>
                        <strong>{metros(valor)}</strong>
                      </li>
                    ))}
                  </ul>
                  <p className={estilos.instrucao}>
                    Nomes como a Defesa Civil da cidade escreve. Cada cidade tem a sua régua, com
                    zero próprio: <strong>estes metros não se comparam</strong> com os de outra
                    cidade.
                    {cidade.regua ? <> Régua: {cidade.regua}.</> : null}
                  </p>
                </>
              ) : reguas.length > 0 ? (
                /* Cidade de várias réguas: a escala não está NA CIDADE, está em
                   cada régua, com zeros diferentes. Um número só seria mentira. */
                <>
                  <p className={estilos.instrucao}>
                    As cotas desta cidade estão <strong>em cada régua</strong> — não numa escala
                    única. Elas têm zeros diferentes entre si. <strong>A cor sai da régua</strong>,
                    não daqui.
                  </p>
                  <ReguasDaCidade reguas={reguas} cidade={cidade.nome} agrupadoPorCurso />
                </>
              ) : (
                <p className={estilos.instrucao}>
                  Esta cidade ainda não tem cota de acionamento no cadastro. Sem ela, um número na
                  régua não vira faixa — e o site não a pinta nem dispara aviso por ela.
                </p>
              )}
            </details>
          </>
        ) : null}

        {aba === 'rua' ? (
          <>
            <Suspense fallback={<span className={`esqueleto ${estilos.esqGrafico}`} />}>
              <CotasDeRua key={cidade.id} cidade={cidade} leitura={leitura} agora={agora} />
            </Suspense>
            {cidade.id === 'ituporanga' ? (
              <Suspense fallback={<p className={estilos.instrucao}>Carregando o mapa de áreas por nível…</p>}>
                <MapaCotasItuporanga />
              </Suspense>
            ) : null}
          </>
        ) : null}

        {aba === 'historico' ? (
          <>
            <section className="cartao">
              <h2>Picos históricos em {cidade.nome}</h2>
              {picos.length > 0 ? (
                <Suspense fallback={<span className={`esqueleto ${estilos.esqGrafico}`} />}>
                  <GraficoPicos eventos={picos} cidade={cidade} nomeCidade={cidade.nome} />
                </Suspense>
              ) : (
                <p className={estilos.instrucao}>
                  Nenhum pico histórico levantado para {cidade.nome} ainda. A ausência é do{' '}
                  <strong>nosso levantamento</strong>, não da história da cidade.
                </p>
              )}
            </section>
            {/* D3: a marca antiga mais próxima acima do nível fica AQUI, depois
                das barras — longe do número de agora, para não soar previsão. */}
            <PainelCenarioAnterior cidade={cidade} eventos={picos} leitura={leitura} agora={agora} />
            {rioId === 'itajai-acu' || rioId === 'itajai-mirim' ? (
              <Suspense fallback={<p className={estilos.instrucao}>Carregando as perguntas sobre o histórico…</p>}>
                <ChatLocal rio={rioId} />
              </Suspense>
            ) : null}
          </>
        ) : null}

        {aba === 'fontes' ? (
          <>
            <section className="cartao">
              <h2>De onde vêm estes números</h2>
              {cidade.fontes_tempo_real.length > 0 ? (
                <>
                  <h3 className={estilos.subtitulo}>Nível e chuva ao vivo</h3>
                  <ul className={estilos.fontes}>
                    {cidade.fontes_tempo_real.map((bruto) => {
                      const { url, rotulo } = fonteTempoReal(bruto)
                      return (
                        <li key={bruto}>
                          <a href={url} target="_blank" rel="noreferrer">
                            {rotulo}
                          </a>
                        </li>
                      )
                    })}
                  </ul>
                </>
              ) : (
                <p className={estilos.instrucao}>Sem fonte de tempo real cadastrada para {cidade.nome}.</p>
              )}
              <h3 className={estilos.subtitulo}>A régua</h3>
              <ul className={estilos.fontes}>
                {cidade.regua ? <li>Régua: {cidade.regua}</li> : null}
                <li>
                  {cidade.codigo_ana
                    ? `Estação ANA ${cidade.codigo_ana}${cidade.verificado ? '' : ' (não conferida)'}`
                    : 'Sem estação ANA localizada'}
                </li>
                {cidade.sub_bacia ? <li>Sub-bacia: {cidade.sub_bacia}</li> : null}
                {cidade.km_da_foz !== undefined ? <li>{cidade.km_da_foz} km da foz</li> : null}
                <li>{picos.length} pico{picos.length === 1 ? '' : 's'} no histórico</li>
              </ul>
              <h3 className={estilos.subtitulo}>O que os selos de confiança querem dizer</h3>
              <ul className={estilos.fontes}>
                <li><strong>Confiança alta</strong> — {ROTULO_CONFIANCA.alta}</li>
                <li><strong>Confiança média</strong> — {ROTULO_CONFIANCA.media}</li>
                <li><strong>Confiança baixa</strong> — {ROTULO_CONFIANCA.baixa}</li>
              </ul>
              <p className={estilos.instrucao}>
                <Link to={`/monitor/${cidade.id}`}>Abrir no Monitor, com zoom e satélite →</Link>
              </p>
            </section>
            <details className={`cartao ${estilos.detalhes}`}>
              <summary>O que as cores querem dizer</summary>
              <LegendaFaixas />
            </details>
            {/* Nota de pesquisa (fontes, conferências, pendências): útil a quem
                confere o dado, ruído para quem quer saber do rio agora. */}
            {cidade.observacao ? (
              <details className={`cartao ${estilos.detalhes}`}>
                <summary>Detalhes técnicos desta régua</summary>
                <p className={estilos.observacao}>{cidade.observacao}</p>
              </details>
            ) : null}
          </>
        ) : null}
      </div>
    </>
  )
}
