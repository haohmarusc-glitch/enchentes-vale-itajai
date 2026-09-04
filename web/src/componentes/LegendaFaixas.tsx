import faixas from '@dados/faixas.json'
import type { Faixa } from '../logica/tempoReal'
import estilos from './LegendaFaixas.module.css'

/**
 * Os textos das faixas vêm de `data/faixas.json` — fonte ÚNICA. O site DESCREVE
 * a faixa e remete à Defesa Civil (199); NUNCA recomenda ação, porque não é
 * alerta oficial. As únicas chamadas permitidas são "Siga a Defesa Civil" e
 * "ligue 199". Mudar texto de faixa é mudar o JSON, não este arquivo.
 */
const F = faixas.faixas as Record<Faixa, { rotulo: string; acao: string }>

/** Rótulo curto de cada faixa, para a legenda e para o selo ao lado da cidade. */
export const ROTULO_FAIXA: Record<Faixa, string> = {
  normal: F.normal.rotulo,
  monitoramento: F.monitoramento.rotulo,
  atencao: F.atencao.rotulo,
  alerta: F.alerta.rotulo,
  inundacao: F.inundacao.rotulo,
  emergencia: F.emergencia.rotulo,
  'sem-dado': F['sem-dado'].rotulo,
  varias: F.varias.rotulo,
}

/** O que cada faixa DIZ — descrição + remissão à autoridade, nunca ordem. */
export const ACAO_FAIXA: Record<Faixa, string> = {
  normal: F.normal.acao,
  monitoramento: F.monitoramento.acao,
  atencao: F.atencao.acao,
  alerta: F.alerta.acao,
  inundacao: F.inundacao.acao,
  emergencia: F.emergencia.acao,
  'sem-dado': F['sem-dado'].acao,
  varias: F.varias.acao,
}

// A ordem em que a legenda aparece: do calmo ao grave, e os dois estados
// "sem cor de nível" por último, porque não são pontos da escala.
const NA_LEGENDA = faixas.ordem_legenda as Faixa[]

/**
 * A legenda das cores do rio. A cor é a faixa da PRÓPRIA cidade, não o metro —
 * está escrito aqui, porque sem isso a tela convidaria a comparar cidades pela
 * cor, que é o que a régua de cada uma proíbe.
 */
export default function LegendaFaixas() {
  return (
    <div className={estilos.legenda}>
      <p className={estilos.aviso}>{faixas.disclaimer}</p>
      <ul className={estilos.itens}>
        {NA_LEGENDA.map((f) => (
          <li key={f} className={estilos.item}>
            <span
              className={`${estilos.amostra} ${estilos[f] ?? ''}`}
              aria-hidden="true"
            />
            <span>
              <strong>{f === 'inundacao' ? faixas.rotulo_legenda_inundacao : ROTULO_FAIXA[f]}</strong>
              <span className={estilos.acao}> — {ACAO_FAIXA[f]}</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
