import type { Cidade, Trecho } from '../dados/tipos'
import { caminho, faixaHoras } from '../logica/transito'
import { rotuloCota } from '../logica/formato'
import { metros } from '../logica/formato'
import SeloConfianca from './SeloConfianca'
import estilos from './DiagramaRio.module.css'

interface Props {
  rioId: string
  cidades: Cidade[]
  trechos: Trecho[]
  /** Quantos picos históricos existem para cada cidade, para mostrar cobertura. */
  registrosPorCidade: Record<string, number>
  cidadeSelecionada: string | null
  aoSelecionar: (cidadeId: string) => void
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
}: Props) {
  return (
    <ol className={estilos.diagrama}>
      {cidades.map((cidade, i) => {
        const proxima = cidades[i + 1]
        const trecho = proxima ? caminho(trechos, rioId, cidade.id, proxima.id) : null
        const registros = registrosPorCidade[cidade.id] ?? 0
        const selecionada = cidadeSelecionada === cidade.id
        const cotas = Object.entries(cidade.cotas_m)

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
                  {cotas.length > 0 ? (
                    <span className={estilos.cotas}>
                      {cotas.map(([chave, valor]) => (
                        <span key={chave} className={estilos.cota}>
                          {rotuloCota(chave)}: <strong>{metros(valor)}</strong>
                        </span>
                      ))}
                    </span>
                  ) : (
                    <span className={estilos.semDado}>cotas de referência não levantadas</span>
                  )}

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
                      {cidade.fontes_tempo_real.map((url, k) => (
                        <span key={url}>
                          {k > 0 ? ' · ' : ''}
                          <a
                            href={url}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {new URL(url).hostname}
                          </a>
                        </span>
                      ))}
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
                  {trecho ? (
                    <>
                      a onda leva <strong>{faixaHoras(trecho)}</strong> até {proxima.nome}{' '}
                      <SeloConfianca
                        nivel={trecho.confianca}
                        fonte={trecho.fontes.join(' · ')}
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
