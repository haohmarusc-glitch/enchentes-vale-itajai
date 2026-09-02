import type { ReactNode } from 'react'
import type { Cidade, Topologia, Trecho } from '../dados/tipos'
import type { EstadoTempoReal } from '../dados/tempoReal'
import { leituraDaCidade, leiturasDaCidade } from '../dados/tempoReal'
import type { NivelSc } from '../dados/nivelSc'
import { faixaDaCidade, idadeMin, textoIdade } from '../logica/tempoReal'
import LegendaFaixas, { ROTULO_FAIXA, ACAO_FAIXA } from './LegendaFaixas'
import { estacoesTempoReal } from '../dados/carregar'
import { reguasComCota } from '../logica/reguas'
import ReguasDaCidade from './ReguasDaCidade'
import { chuvaDaCidade } from '../logica/chuva'
import NivelAoVivo from './NivelAoVivo'
import ChuvaAoVivo from './ChuvaAoVivo'
import { caminho, faixaHoras } from '../logica/transito'
import { fonteTempoReal, metros, rotuloCota } from '../logica/formato'
import SeloConfianca from './SeloConfianca'
import VariasReguas from './VariasReguas'
import estilos from './DiagramaRio.module.css'

interface Props {
  rioId: string
  cidades: Cidade[]
  trechos: Trecho[]
  /** Quantos picos históricos existem para cada cidade, para mostrar cobertura. */
  registrosPorCidade: Record<string, number>
  cidadeSelecionada: string | null
  aoSelecionar: (cidadeId: string) => void
  tempoReal: EstadoTempoReal
  /** Nível BRUTO estadual por cidade, para preencher (rotulado) as lacunas. */
  nivelSc?: NivelSc
  /** A árvore do rio, quando ele é ramificado (o Açu). Ausente = rio em fila. */
  topologia?: Topologia
  agora: Date
}

type Faixa = ReturnType<typeof faixaDaCidade>
type Papel = 'cabeceira' | 'tronco' | 'afluente'

/**
 * Diagrama do rio, de montante para jusante — a ordem em que a água chega.
 *
 * Rio em fila (o Mirim): uma lista só, cada cidade com a seta do tempo até a
 * próxima. Rio em árvore (o Açu): a bacia NÃO é uma fila. Mostrar Taió → Rio do
 * Sul → Ibirama → Indaial como sequência afirma um caminho de água que não
 * existe — Taió e Ituporanga são cabeceiras paralelas, e Ibirama é afluente
 * lateral (Rio Hercílio), cujo pico ENTRA no tronco, não desce por ele. Então a
 * seta de "a cheia leva X até Y" só aparece DENTRO do tronco; cabeceiras e
 * afluentes vêm sob o seu papel, com a nota de onde se juntam.
 */
export default function DiagramaRio(props: Props) {
  const { cidades, topologia } = props
  const porId = new Map(cidades.map((c) => [c.id, c]))

  if (!topologia) {
    // Rio em fila: comportamento de sempre — a ordem do array é a descida.
    return (
      <>
        <LegendaFaixas />
        <ol className={estilos.diagrama}>
          {cidades.map((cidade, i) => (
            <ItemCidade
              key={cidade.id}
              cidade={cidade}
              papel={null}
              conector={conectorLinear(props, cidade, i)}
              props={props}
            />
          ))}
        </ol>
      </>
    )
  }

  // Rio em árvore (o Açu). Três blocos: cabeceiras (paralelas), tronco (a única
  // sequência real) e afluentes laterais.
  const cabeceiras = topologia.cabeceiras_paralelas
    .map((id) => porId.get(id))
    .filter((c): c is Cidade => Boolean(c))
  const tronco = topologia.tronco_sequencia
    .map((id) => porId.get(id))
    .filter((c): c is Cidade => Boolean(c))
  const afluentes = topologia.afluentes_laterais
    .map((a) => porId.get(a.id))
    .filter((c): c is Cidade => Boolean(c))
  const nomeInicioTronco = tronco[0]?.nome ?? 'Rio do Sul'
  // Rede de segurança: nenhuma cidade pode sumir da tela em silêncio. Se alguém
  // adicionar uma cidade sem colocá-la na _topologia, ela cai aqui, visível.
  const mostradas = new Set([...cabeceiras, ...tronco, ...afluentes].map((c) => c.id))
  const resto = cidades.filter((c) => !mostradas.has(c.id))

  return (
    <>
      <LegendaFaixas />

      {cabeceiras.length > 0 ? (
        <section className={estilos.ramo}>
          <h3 className={estilos.tituloRamo}>Cabeceiras</h3>
          <p className={estilos.notaRamo}>
            Correm em <strong>paralelo</strong> e se juntam em {nomeInicioTronco}, onde nasce o
            Itajaí-Açu. Nenhuma vem “antes” da outra.
          </p>
          <ol className={estilos.diagrama}>
            {cabeceiras.map((cidade) => (
              <ItemCidade
                key={cidade.id}
                cidade={cidade}
                papel="cabeceira"
                conector={
                  <ConectorNota>junta-se ao tronco em {nomeInicioTronco}</ConectorNota>
                }
                props={props}
              />
            ))}
          </ol>
        </section>
      ) : null}

      <section className={estilos.ramo}>
        <h3 className={estilos.tituloRamo}>Tronco do Itajaí-Açu</h3>
        <p className={estilos.notaRamo}>
          A <strong>única</strong> sequência que a água segue, de {nomeInicioTronco} até a foz. É por
          aqui que a cheia desce.
        </p>
        <ol className={estilos.diagrama}>
          {tronco.map((cidade, i) => (
            <ItemCidade
              key={cidade.id}
              cidade={cidade}
              papel="tronco"
              conector={conectorTronco(props, tronco, i)}
              props={props}
            />
          ))}
        </ol>
      </section>

      {afluentes.length > 0 ? (
        <section className={estilos.ramo}>
          <h3 className={estilos.tituloRamo}>Afluentes laterais</h3>
          <p className={estilos.notaRamo}>
            Entram no tronco de lado — <strong>não são elos da fila</strong>. O pico de um afluente
            chega ao tronco, não desce por ele.
          </p>
          <ol className={estilos.diagrama}>
            {afluentes.map((cidade) => {
              const info = topologia.afluentes_laterais.find((a) => a.id === cidade.id)
              const onde = porId.get(info?.entra_perto_de ?? '')?.nome
              return (
                <ItemCidade
                  key={cidade.id}
                  cidade={cidade}
                  papel="afluente"
                  conector={
                    <ConectorNota>
                      {info?.rio ? `${info.rio} — ` : ''}entra no tronco
                      {onde ? ` perto de ${onde}` : ''}; não é elo da fila
                    </ConectorNota>
                  }
                  props={props}
                />
              )
            })}
          </ol>
        </section>
      ) : null}

      {resto.length > 0 ? (
        <section className={estilos.ramo}>
          <h3 className={estilos.tituloRamo}>Outros pontos</h3>
          <p className={estilos.notaRamo}>
            Ainda sem posição definida na árvore do rio — aparecem para não sumir da tela.
          </p>
          <ol className={estilos.diagrama}>
            {resto.map((cidade) => (
              <ItemCidade key={cidade.id} cidade={cidade} papel={null} conector={null} props={props} />
            ))}
          </ol>
        </section>
      ) : null}
    </>
  )
}

const ROTULO_PAPEL: Record<Papel, string> = {
  cabeceira: 'cabeceira (paralela)',
  tronco: 'tronco',
  afluente: 'afluente lateral',
}

/** Uma cidade no diagrama: o botão com todo o detalhe, e o conector abaixo. */
function ItemCidade({
  cidade,
  papel,
  conector,
  props,
}: {
  cidade: Cidade
  papel: Papel | null
  conector: ReactNode
  props: Props
}) {
  const { rioId, cidadeSelecionada, aoSelecionar, tempoReal, nivelSc, agora, registrosPorCidade } =
    props
  const registros = registrosPorCidade[cidade.id] ?? 0
  const aoVivo = leituraDaCidade(tempoReal, rioId, cidade.id)
  // Cidade de várias réguas: `leituraDaCidade` desiste, corretamente, e por
  // causa disso Itajaí — a foz, que recebe os dois rios — aparecia sem número
  // nenhum. Aqui elas saem todas, cada uma com a cota dela.
  const todasAsLeituras = leiturasDaCidade(tempoReal, rioId, cidade.id)
  // Chuva vem por cidade, não por rio. Quando a coleta falhou, `chuva` vem null
  // para TODA cidade — sem dizer isso, a tela lê-se como "não está chovendo".
  const chuva = chuvaDaCidade(tempoReal.chuva, cidade.id)
  const selecionada = cidadeSelecionada === cidade.id
  const cotas = Object.entries(cidade.cotas_m)
  // Cidade sem cota própria pode ter cotas oficiais por régua (Itajaí tem onze).
  const reguas = reguasComCota(estacoesTempoReal, rioId, cidade.id)
  // A faixa de perigo AGORA, para a cor do marcador. Várias réguas (a foz) não
  // viram uma cor só; leitura velha ou sem cota viram cinza.
  const temVarias = aoVivo === null && todasAsLeituras.length > 1
  const faixa = faixaDaCidade(cidade, aoVivo, temVarias, agora)
  // Sem leitura municipal (e não sendo a foz de várias réguas), o nível BRUTO
  // estadual preenche a lacuna — rotulado e SEM cor de faixa.
  const bruto =
    aoVivo === null && todasAsLeituras.length <= 1 ? nivelSc?.get(cidade.id) ?? null : null

  return (
    <li className={estilos.item}>
      <button
        type="button"
        onClick={() => aoSelecionar(cidade.id)}
        aria-pressed={selecionada}
        className={`${estilos.cidade} ${selecionada ? estilos.selecionada : ''}`}
      >
        <span
          className={`${estilos.marcador} ${estilos[faixa]}`}
          aria-label={`faixa: ${ROTULO_FAIXA[faixa]}`}
          title={ROTULO_FAIXA[faixa]}
        />
        <span className={estilos.corpo}>
          <span className={estilos.nome}>
            {cidade.nome}
            <span className={`${estilos.selo} ${estilos[faixa]}`}>{ROTULO_FAIXA[faixa]}</span>
            {papel ? <span className={estilos.papel}>{ROTULO_PAPEL[papel]}</span> : null}
            {cidade.regua ? <span className={estilos.regua}> — régua: {cidade.regua}</span> : null}
          </span>

          {faixa === 'atencao' || faixa === 'alerta' || faixa === 'inundacao' || faixa === 'emergencia' ? (
            <span className={`${estilos.acao} ${estilos[`acao_${faixa}`] ?? ''}`}>
              {ACAO_FAIXA[faixa]}
            </span>
          ) : null}

          <span className={estilos.detalhes}>
            {aoVivo ? (
              <span className={estilos.aoVivo}>
                <NivelAoVivo leitura={aoVivo} cidade={cidade} agora={agora} />
              </span>
            ) : todasAsLeituras.length > 1 ? (
              <VariasReguas leituras={todasAsLeituras} reguas={reguas} cidade={cidade} agora={agora} />
            ) : bruto ? (
              <span className={estilos.brutoEstadual}>
                <strong>{metros(bruto.nivelBrutoM)}</strong> — {bruto.estacao} (rede estadual)
                {bruto.medidoEm ? <> · {textoIdade(idadeMin(bruto.medidoEm, agora))}</> : null}
                <span className={estilos.brutoNota}>
                  nível bruto — régua própria da estação, não comparável com as cotas desta cidade
                </span>
              </span>
            ) : null}

            {chuva ? (
              <ChuvaAoVivo resumo={chuva} agora={agora} cidade={cidade.nome} />
            ) : tempoReal.chuvaOk ? null : (
              <span className={estilos.chuvaFalhou}>🌧 chuva: não foi possível coletar agora</span>
            )}

            {cotas.length > 0 ? (
              <span className={estilos.cotas}>
                {cotas.map(([chave, valor]) => (
                  <span key={chave} className={estilos.cota}>
                    {rotuloCota(chave)}: <strong>{metros(valor)}</strong>
                  </span>
                ))}
              </span>
            ) : reguas.length === 0 ? (
              <span className={estilos.semDado}>cotas de referência não levantadas</span>
            ) : null}

            {reguas.length > 0 ? <ReguasDaCidade reguas={reguas} cidade={cidade.nome} /> : null}

            {cidade.sub_bacia || cidade.km_da_foz !== undefined ? (
              <span className={estilos.linhaMeta}>
                {cidade.sub_bacia ? `Sub-bacia: ${cidade.sub_bacia}` : ''}
                {cidade.sub_bacia && cidade.km_da_foz !== undefined ? ' · ' : ''}
                {cidade.km_da_foz !== undefined ? `${cidade.km_da_foz} km da foz` : ''}
              </span>
            ) : null}

            <span className={estilos.linhaMeta}>
              {registros > 0 ? (
                <>
                  {registros} pico{registros > 1 ? 's' : ''} no histórico
                </>
              ) : (
                <span className={estilos.semDado}>sem picos registrados</span>
              )}
              {cidade.codigo_ana ? (
                <>
                  {' · '}estação ANA {cidade.codigo_ana}
                  {!cidade.verificado ? ' (não conferida)' : ''}
                </>
              ) : (
                <>{' · '}sem estação ANA localizada</>
              )}
            </span>

            {cidade.observacao ? (
              <span className={estilos.observacao}>{cidade.observacao}</span>
            ) : null}

            {cidade.fontes_tempo_real.length > 0 ? (
              <span className={estilos.linhaMeta}>
                Tempo real oficial:{' '}
                {cidade.fontes_tempo_real.map((bruto, k) => {
                  const { url, rotulo } = fonteTempoReal(bruto)
                  return (
                    <span key={bruto}>
                      {k > 0 ? ' · ' : ''}
                      <a
                        href={url}
                        target="_blank"
                        rel="noreferrer"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {rotulo}
                      </a>
                    </span>
                  )
                })}
              </span>
            ) : (
              <span className={estilos.semDado}>sem fonte de tempo real cadastrada</span>
            )}
          </span>
        </span>
      </button>
      {conector}
    </li>
  )
}

/** O conector com a seta e o tempo de trânsito até uma cidade a jusante. */
function ConectorSeta({
  faixa,
  proximaNome,
  alvoNome,
  trecho,
}: {
  faixa: Faixa
  proximaNome: string
  alvoNome: string
  trecho: NonNullable<ReturnType<typeof caminho>>
}) {
  return (
    <div className={estilos.seta}>
      <span className={`${estilos.setaLinha} ${estilos[`seg_${faixa}`] ?? ''}`} aria-hidden="true" />
      <span className={estilos.setaTexto}>
        {alvoNome !== proximaNome ? (
          <span className={estilos.semDado}>tempo até {proximaNome} não levantado; </span>
        ) : null}
        a cheia leva <strong>{faixaHoras(trecho)}</strong> até {alvoNome}{' '}
        <SeloConfianca nivel={trecho.confianca} fonte={trecho.fontes.join(' · ')} tipo="trecho" />
        {!trecho.direto ? (
          <span className={estilos.somaTrechos}> (soma de {trecho.trechos.length} trechos)</span>
        ) : null}
      </span>
    </div>
  )
}

/** Uma nota abaixo da cidade, sem seta de tempo (cabeceira / afluente). */
function ConectorNota({ children }: { children: ReactNode }) {
  return (
    <div className={estilos.seta}>
      <span className={estilos.notaConector}>↳ {children}</span>
    </div>
  )
}

/** Conector do rio em fila (Mirim): seta até a próxima cidade com caminho. */
function conectorLinear(props: Props, cidade: Cidade, i: number): ReactNode {
  const { cidades, rioId, trechos } = props
  const proxima = cidades[i + 1]
  if (!proxima) return null
  const faixa = faixaAgora(props, cidade)
  const { alvo, trecho } = primeiroComCaminho(trechos, rioId, cidade.id, cidades, i + 1)
  if (trecho && alvo) {
    return (
      <ConectorSeta faixa={faixa} proximaNome={proxima.nome} alvoNome={alvo.nome} trecho={trecho} />
    )
  }
  return (
    <div className={estilos.seta}>
      <span className={`${estilos.setaLinha} ${estilos[`seg_${faixa}`] ?? ''}`} aria-hidden="true" />
      <span className={estilos.setaTexto}>
        <span className={estilos.semDado}>tempo até {proxima.nome} ainda não levantado</span>
      </span>
    </div>
  )
}

/** Conector DENTRO do tronco: seta até a próxima cidade do tronco. */
function conectorTronco(props: Props, tronco: Cidade[], i: number): ReactNode {
  const { rioId, trechos } = props
  const proxima = tronco[i + 1]
  if (!proxima) return null // foz: fim do tronco
  const cidade = tronco[i]!
  const faixa = faixaAgora(props, cidade)
  const { alvo, trecho } = primeiroComCaminho(trechos, rioId, cidade.id, tronco, i + 1)
  if (trecho && alvo) {
    return (
      <ConectorSeta faixa={faixa} proximaNome={proxima.nome} alvoNome={alvo.nome} trecho={trecho} />
    )
  }
  return (
    <div className={estilos.seta}>
      <span className={`${estilos.setaLinha} ${estilos[`seg_${faixa}`] ?? ''}`} aria-hidden="true" />
      <span className={estilos.setaTexto}>
        <span className={estilos.semDado}>tempo até {proxima.nome} ainda não levantado</span>
      </span>
    </div>
  )
}

/** A primeira cidade a jusante (a partir de `desde`) com tempo de trânsito conhecido. */
function primeiroComCaminho(
  trechos: Trecho[],
  rioId: string,
  deId: string,
  lista: Cidade[],
  desde: number,
): { alvo?: Cidade; trecho: ReturnType<typeof caminho> } {
  for (let j = desde; j < lista.length; j++) {
    const c = caminho(trechos, rioId, deId, lista[j]!.id)
    if (c) return { alvo: lista[j], trecho: c }
  }
  return { trecho: null }
}

/** A faixa de perigo AGORA de uma cidade, para colorir a seta. */
function faixaAgora(props: Props, cidade: Cidade): Faixa {
  const { rioId, tempoReal, agora } = props
  const aoVivo = leituraDaCidade(tempoReal, rioId, cidade.id)
  const temVarias = aoVivo === null && leiturasDaCidade(tempoReal, rioId, cidade.id).length > 1
  return faixaDaCidade(cidade, aoVivo, temVarias, agora)
}
