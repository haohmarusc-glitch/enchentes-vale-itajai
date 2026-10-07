import { useMemo } from 'react'
import ListaRio, { type DestinoDaCidade } from './ListaRio'
import { cidadesDoRio, rio, topologiaDoRio } from '../dados/carregar'
import { useAoVivo } from '../dados/usarAoVivo'
import estilos from './ReguasDoMonitor.module.css'

/**
 * A aba "Réguas" do Monitor no celular (redesenho de 07/10/2026, etapa 3): as cidades dos dois rios em
 * lista compacta — faixa, número, tendência e idade —, a MESMA `ListaRio` das telas do Açu e do Mirim, com
 * as mesmas regras (cor = faixa, leitura velha sem número, estadual dito "zero próprio", árvore e não fila).
 * A única diferença é o destino do toque: aqui a cidade abre no mapa do Monitor, não na página dela.
 */
const RIOS = ['itajai-acu', 'itajai-mirim'] as const

const noMonitor: DestinoDaCidade = (cidade) => `/monitor/${cidade.id}`

export default function ReguasDoMonitor({ aoEscolher }: { aoEscolher: () => void }) {
  const aoVivo = useAoVivo()
  const rios = useMemo(
    () => RIOS.map((id) => ({ id, nome: rio(id)?.nome ?? id, cidades: cidadesDoRio(id), topologia: topologiaDoRio(id) })),
    [],
  )
  return (
    <section
      className={estilos.folha}
      aria-label="Réguas agora"
      // Tocar numa cidade leva ao mapa: a lista sai da frente, e o painel da cidade abre no pino.
      onClick={(e) => {
        if ((e.target as Element).closest('a')) aoEscolher()
      }}
    >
      <p className={estilos.instrucao}>
        Cada cidade na faixa da <strong>régua dela</strong> — não compare metros entre cidades. Toque numa
        cidade para vê-la no mapa.
      </p>
      {rios.map((r) => (
        <div key={r.id} className={estilos.rio}>
          <h2 className={estilos.nomeRio}>{r.nome}</h2>
          <ListaRio rioId={r.id} cidades={r.cidades} topologia={r.topologia} aoVivo={aoVivo} destino={noMonitor} />
        </div>
      ))}
    </section>
  )
}
