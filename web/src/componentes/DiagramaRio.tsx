import type { Cidade, Trecho } from '../dados/tipos'
import type { EstadoTempoReal } from '../dados/tempoReal'
import { leituraDaCidade, leiturasDaCidade } from '../dados/tempoReal'
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
  agora: Date
}

/**
 * Diagrama linear do rio, de montante para jusante — a ordem em que a água
 * chega. Mapa geográfico fica para depois; o que importa aqui é a sequência.
 */
export default function DiagramaRio({
  rioId,
  cidades,
  trechos,
  registrosPorCidade,
  cidadeSelecionada,
  aoSelecionar,
  tempoReal,
  agora,
}: Props) {
  return (
    <ol className={estilos.diagrama}>
      {cidades.map((cidade, i) => {
        const proxima = cidades[i + 1]
        // Nem todo par vizinho tem tempo levantado, mas quase sempre existe o
        // tempo até alguma cidade mais abaixo — e é essa a informação útil para
        // quem mora lá. Procura a primeira cidade a jusante com caminho conhecido.
        let alvo: Cidade | undefined
        let trecho: ReturnType<typeof caminho> = null
        for (let j = i + 1; j < cidades.length; j++) {
          const c = caminho(trechos, rioId, cidade.id, cidades[j]!.id)
          if (c) {
            alvo = cidades[j]
            trecho = c
            break
          }
        }
        const registros = registrosPorCidade[cidade.id] ?? 0
        const aoVivo = leituraDaCidade(tempoReal, rioId, cidade.id)
        // Cidade de várias réguas: `leituraDaCidade` desiste, corretamente, e
        // por causa disso Itajaí — a foz, que recebe os dois rios — aparecia
        // sem número nenhum. Aqui elas saem todas, cada uma com a cota dela.
        const todasAsLeituras = leiturasDaCidade(tempoReal, rioId, cidade.id)
        // Chuva vem por cidade, não por rio: o pluviômetro mede o que caiu
        // naquele ponto, e não pertence a uma calha em particular.
        // Quando a coleta da chuva falhou, `chuva` vem null para TODA cidade.
        // Sem dizer isso, a tela fica igual a "não há pluviômetro aqui" — e,
        // durante uma chuva, isso lê-se como "não está chovendo".
        const chuva = chuvaDaCidade(tempoReal.chuva, cidade.id)
        const selecionada = cidadeSelecionada === cidade.id
        const cotas = Object.entries(cidade.cotas_m)
        // Cidade sem cota própria pode ter cotas oficiais por régua — Itajaí
        // tem onze, Ilhota tem uma. Dizer "não levantadas" nesses casos seria
        // esconder dado publicado.
        const reguas = reguasComCota(estacoesTempoReal, rioId, cidade.id)

        return (
          <li key={cidade.id} className={estilos.item}>
            <button
              type="button"
              onClick={() => aoSelecionar(cidade.id)}
              aria-pressed={selecionada}
              className={`${estilos.cidade} ${selecionada ? estilos.selecionada : ''}`}
            >
              <span className={estilos.marcador} aria-hidden="true" />
              <span className={estilos.corpo}>
                <span className={estilos.nome}>
                  {cidade.nome}
                  {cidade.regua ? <span className={estilos.regua}> — régua: {cidade.regua}</span> : null}
                </span>

                <span className={estilos.detalhes}>
                  {aoVivo ? (
                    <span className={estilos.aoVivo}>
                      <NivelAoVivo leitura={aoVivo} cidade={cidade} agora={agora} />
                    </span>
                  ) : todasAsLeituras.length > 1 ? (
                    <VariasReguas
                      leituras={todasAsLeituras}
                      reguas={reguas}
                      cidade={cidade}
                      agora={agora}
                    />
                  ) : null}

                  {chuva ? (
                    <ChuvaAoVivo resumo={chuva} agora={agora} cidade={cidade.nome} />
                  ) : tempoReal.chuvaOk ? null : (
                    <span className={estilos.chuvaFalhou}>
                      🌧 chuva: não foi possível coletar agora
                    </span>
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

                  {reguas.length > 0 ? (
                    <ReguasDaCidade reguas={reguas} cidade={cidade.nome} />
                  ) : null}

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

            {proxima ? (
              <div className={estilos.seta}>
                <span className={estilos.setaLinha} aria-hidden="true" />
                <span className={estilos.setaTexto}>
                  {trecho && alvo ? (
                    <>
                      {alvo.id !== proxima.id ? (
                        <span className={estilos.semDado}>
                          tempo até {proxima.nome} não levantado;{' '}
                        </span>
                      ) : null}
                      a cheia leva <strong>{faixaHoras(trecho)}</strong> até {alvo.nome}{' '}
                      <SeloConfianca
                        nivel={trecho.confianca}
                        fonte={trecho.fontes.join(' · ')}
                      tipo="trecho"
                      />
                      {!trecho.direto ? (
                        <span className={estilos.somaTrechos}>
                          {' '}
                          (soma de {trecho.trechos.length} trechos)
                        </span>
                      ) : null}
                    </>
                  ) : (
                    <span className={estilos.semDado}>
                      tempo até {proxima.nome} ainda não levantado
                    </span>
                  )}
                </span>
              </div>
            ) : null}
          </li>
        )
      })}
    </ol>
  )
}
