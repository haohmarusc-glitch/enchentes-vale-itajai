import type { ResumoChuva } from '../logica/chuva'
import { JANELAS, ROTULO_JANELA, textoFaixa } from '../logica/chuva'
import { idadeMin, textoIdade, MIN_VELHA } from '../logica/tempoReal'
import estilos from './ChuvaAoVivo.module.css'

interface Props {
  resumo: ResumoChuva
  agora: Date
  /** Nome da cidade, para o rótulo acessível. */
  cidade: string
}

/**
 * Chuva acumulada na cidade, ao lado do nível do rio.
 *
 * A fonte publica 10 min, 1 h, 12 h, 24 h e 48 h. **Não publica 6 h**, e aqui
 * não se estima: numa cheia a chuva não é constante, e dividir o acumulado de
 * 12 h suporia justamente o contrário. Mostrar as janelas que existem é o
 * máximo honesto.
 *
 * O destaque é 24 h, que é a janela que melhor conversa com a cheia do
 * Itajaí-Açu — o rio leva mais de um dia para descer da cabeceira até a foz.
 * As outras ficam ao lado, menores.
 */
export default function ChuvaAoVivo({ resumo, agora, cidade }: Props) {
  const idade = resumo.medidoEm ? idadeMin(resumo.medidoEm, agora) : null
  const velha = idade !== null && idade > MIN_VELHA

  if (resumo.pluviometros === 0) {
    // Havia pluviômetro, mas nenhum publicou série que fecha. Isso é problema
    // da fonte e precisa ser dito — calar pareceria "não choveu".
    return (
      <span className={estilos.problema}>
        🌧 chuva: dado inconsistente na fonte
        {resumo.descartados > 1 ? ` (${resumo.descartados} pluviômetros)` : ''}
      </span>
    )
  }

  const destaque = resumo.porJanela.h24
  const outras = JANELAS.filter((j) => j !== 'h24' && j !== 'min10' && resumo.porJanela[j])

  return (
    <span className={`${estilos.chuva} ${velha ? estilos.velha : ''}`}>
      <span className={estilos.icone} aria-hidden="true">
        🌧
      </span>
      {destaque ? (
        <span className={estilos.destaque}>
          <span className={estilos.valor}>{textoFaixa(destaque)}</span>
          <span className={estilos.janela}>em 24 h</span>
        </span>
      ) : null}

      {outras.length > 0 ? (
        <span className={estilos.outras}>
          {outras.map((j) => (
            <span key={j} className={estilos.outra}>
              {ROTULO_JANELA[j]}: {textoFaixa(resumo.porJanela[j]!)}
            </span>
          ))}
        </span>
      ) : null}

      <span className={estilos.meta}>
        {resumo.pluviometros > 1
          ? `maior de ${resumo.pluviometros} pluviômetros em ${cidade}`
          : 'um pluviômetro'}
        {idade !== null ? ` · ${textoIdade(idade)}` : ''}
        {resumo.descartados > 0
          ? ` · ${resumo.descartados} descartado${resumo.descartados > 1 ? 's' : ''} por dado inconsistente`
          : ''}
      </span>
    </span>
  )
}
