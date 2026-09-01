import type { Faixa } from '../logica/tempoReal'
import estilos from './LegendaFaixas.module.css'

/** Rótulo curto de cada faixa, para a legenda e para o selo ao lado da cidade. */
export const ROTULO_FAIXA: Record<Faixa, string> = {
  normal: 'Abaixo da atenção',
  atencao: 'Atenção',
  alerta: 'Alerta',
  inundacao: 'Inundação',
  emergencia: 'Emergência',
  'sem-dado': 'Sem cota / sem leitura',
  varias: 'Várias réguas',
}

/**
 * O que a faixa significa em AÇÃO — a ideia do Kikikuru (a cor diz o que fazer,
 * não é enfeite). Mas com o limite deste projeto: NÃO somos alerta oficial.
 * Por isso toda ação forte devolve à Defesa Civil e ao 199, e nenhuma frase diz
 * "a tela mandou". A tela informa; quem manda evacuar é a autoridade.
 */
export const ACAO_FAIXA: Record<Faixa, string> = {
  normal: 'Rio abaixo da cota de atenção.',
  atencao: 'Fique atento e confira a cota da sua rua.',
  alerta: 'Prepare o que levar. Siga a Defesa Civil; 199 em emergência.',
  inundacao: 'Se sua rua tem cota baixa, procure lugar seguro e ligue 199.',
  emergencia: 'Se sua rua tem cota baixa, procure lugar seguro e ligue 199.',
  'sem-dado': 'Sem dado para dizer a faixa aqui — não conclua que está seguro.',
  varias: 'Vários pontos de medição; veja cada régua abaixo.',
}

// A ordem em que a legenda aparece: do calmo ao grave, e os dois estados
// "sem cor de nível" por último, porque não são pontos da escala.
const NA_LEGENDA: Faixa[] = [
  'normal',
  'atencao',
  'alerta',
  'inundacao',
  'sem-dado',
  'varias',
]

/**
 * A legenda das cores do rio. A cor é a faixa da PRÓPRIA cidade, não o metro —
 * está escrito aqui, porque sem isso a tela convidaria a comparar cidades pela
 * cor, que é o que a régua de cada uma proíbe.
 */
export default function LegendaFaixas() {
  return (
    <div className={estilos.legenda}>
      <p className={estilos.aviso}>
        A cor é a faixa de cada cidade na <strong>régua dela</strong> — não o
        nível em metros. Cidades em cores iguais não estão no mesmo metro.
      </p>
      <ul className={estilos.itens}>
        {NA_LEGENDA.map((f) => (
          <li key={f} className={estilos.item}>
            <span
              className={`${estilos.amostra} ${estilos[f] ?? ''}`}
              aria-hidden="true"
            />
            <span>
              <strong>{f === 'inundacao' ? 'Inundação / Emergência' : ROTULO_FAIXA[f]}</strong>
              <span className={estilos.acao}> — {ACAO_FAIXA[f]}</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
