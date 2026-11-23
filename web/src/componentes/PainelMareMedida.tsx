import { useEffect, useId, useState } from 'react'
import { mareItajai } from '../dados/carregar'
import {
  comSinal,
  estadoDaMareMedida,
  extremosFuturos,
  quandoBrasilia,
  textoDaMareMedida,
  URL_MARE_MEDIDA,
  useMareMedida,
} from '../dados/mareMedida'
import { metros } from '../logica/formato'
import estilos from './PainelMare.module.css'

interface Props {
  /** O arquivo publicado (versão 1). Padrão: a maré do CIRAM, Balneário Camboriú. */
  url?: string
  titulo?: string
  /** Enquanto o arquivo não chega: o nome da estação, a fonte e o endereço dela. */
  estacaoPadrao?: string
  fontePadrao?: string
  urlPadrao?: string
  /** O que o número é e o que não é, quando o arquivo não traz `aviso`. */
  contextoPadrao?: string
  /** A nota de que a tábua da tela é outra fonte. Com dois painéis seguidos, só um a leva. */
  notaDaTabua?: boolean
}

/**
 * A maré MEDIDA, à parte da previsão. Serve ao CIRAM (Balneário Camboriú, desde 07/10/2026) e ao marégrafo MRG01
 * de Cabeçudas, na foz (portal da Defesa Civil de Itajaí, decisão do Jefferson de 23/11/2026).
 *
 * Regras (decisão de 07/10/2026): número só com horário, estação, unidade e referência vertical identificados;
 * leitura antiga nunca como atual; a diferença para a maré astronômica só quando as duas são da mesma estação, no
 * mesmo horário e na mesma referência — com o nome "diferença entre nível observado e maré astronômica prevista",
 * sem atribuir a causa só a vento e pressão. A tábua do porto de Itajaí (a da UNIVALI) continua sendo a previsão
 * astronômica da tela, à parte; os extremos previstos que este painel mostra são os da MESMA fonte da medição, com
 * a referência que ela escreve.
 */
export default function PainelMareMedida({
  url = URL_MARE_MEDIDA,
  titulo = 'Maré medida perto da foz',
  estacaoPadrao = 'Balneário Camboriú',
  fontePadrao = 'EPAGRI/CIRAM — marégrafos',
  urlPadrao = 'https://ciram.epagri.sc.gov.br/index.php/maregrafos/',
  contextoPadrao = 'É contexto do mar perto da foz, não o nível de Itajaí.',
  notaDaTabua = true,
}: Props) {
  const idTitulo = useId()
  const { dado, carregado } = useMareMedida(5, url)
  const [agora, setAgora] = useState(() => new Date())
  useEffect(() => {
    const id = setInterval(() => setAgora(new Date()), 60_000)
    return () => clearInterval(id)
  }, [])

  const estado = estadoDaMareMedida(dado, agora)
  const { titulo: frase, detalhe } = textoDaMareMedida(estado)
  const fonte = dado?.fonte ?? fontePadrao
  const endereco = dado?.fonteUrl ?? urlPadrao
  const fonteTabua = mareItajai._meta.fonte_curta ?? 'não identificada'
  const km = dado?.estacao.kmDaFoz
  // Os extremos só saem com a medição de agora: previsão de uma publicação parada também é velha.
  const extremos = estado.tipo === 'medida' ? extremosFuturos(dado, agora) : []

  return (
    <section className={estilos.painel} aria-labelledby={idTitulo}>
      <h3 id={idTitulo} className={estilos.titulo}>
        {titulo}
      </h3>
      <p className={estilos.nota}>
        Estação de {dado?.estacao.nome ?? estacaoPadrao}
        {km != null && km > 0 ? `, a ${km} km da foz` : ''} — fonte:{' '}
        <a href={endereco} target="_blank" rel="noreferrer">
          {fonte}
        </a>
        . {dado?.aviso ?? contextoPadrao}
      </p>

      {!carregado ? (
        <p className={estilos.nota}>Buscando a medição…</p>
      ) : (
        <div className={estilos.avaliado} data-estado-mare={estado.tipo}>
          <p>
            <strong>{frase}</strong> {detalhe}
          </p>
          {estado.tipo === 'medida' && estado.diferencaM !== null ? (
            <>
              <p>
                Diferença entre nível observado e maré astronômica prevista:{' '}
                <strong>{comSinal(estado.diferencaM)}</strong>.
              </p>
              <p className={estilos.nota}>
                A maré astronômica desta conta é{' '}
                {dado?.astronomicaFonte ?? 'a que o CIRAM calcula para a mesma estação, no mesmo horário'}. A
                diferença pode vir de vento, pressão, da influência do rio e de outros efeitos; não tem uma
                causa só.
              </p>
            </>
          ) : null}
          {extremos.length && dado?.referenciaDosExtremos ? (
            <>
              <p>Próximas marés previstas para esta estação, com a altura no {dado.referenciaDosExtremos}:</p>
              <ul className={estilos.nota} data-extremos-mare="">
                {extremos.map((e) => (
                  <li key={e.quando.toISOString()}>
                    {e.tipo === 'preamar' ? 'Preamar' : 'Baixa-mar'} em {quandoBrasilia(e.quando)}: {metros(e.alturaM)}
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </div>
      )}

      {notaDaTabua ? (
        <p className={estilos.nota}>
          A tábua de maré desta tela continua sendo a do porto de Itajaí ({fonteTabua}). A medição e a tábua
          vêm de fontes diferentes, e cada uma aparece com a sua hora.
        </p>
      ) : null}
    </section>
  )
}
