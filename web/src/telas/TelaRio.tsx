import { Suspense, lazy, useMemo, useState } from 'react'
import AvisoLegal from '../componentes/AvisoLegal'
import DiagramaRio from '../componentes/DiagramaRio'
import PainelPrevisao from '../componentes/PainelPrevisao'
import { cidadesDoRio, eventosDoRio, rio, trechos } from '../dados/carregar'
import estilos from './TelaRio.module.css'

/**
 * O gráfico carrega a biblioteca recharts, que sozinha pesa mais que o resto do
 * site inteiro. Fica em carregamento sob demanda para que o diagrama do rio, os
 * tempos de trânsito e os avisos apareçam primeiro — numa noite de chuva, com
 * rede ruim, é essa informação que precisa chegar.
 */
const GraficoPicos = lazy(() => import('../componentes/GraficoPicos'))

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

  const [selecionadaId, setSelecionadaId] = useState<string | null>(null)
  const cidadeId = selecionadaId ?? padrao
  const selecionada = cidades.find((c) => c.id === cidadeId)
  const indice = cidades.findIndex((c) => c.id === cidadeId)
  const jusante = indice >= 0 ? cidades[indice + 1] : undefined

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
        />
        {semCobertura > 0 ? (
          <p className={estilos.cobertura}>
            {semCobertura} de {cidades.length} cidades ainda não têm pico histórico levantado. Elas
            aparecem no diagrama para deixar claro o que falta, não para sugerir que há dado.
          </p>
        ) : null}
      </section>

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
