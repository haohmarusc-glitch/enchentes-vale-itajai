import { useEffect, useState } from 'react'
import { mareItajai } from '../dados/carregar'
import { comSinal, estadoDaMareMedida, textoDaMareMedida, useMareMedida } from '../dados/mareMedida'
import estilos from './PainelMare.module.css'

/**
 * A maré MEDIDA perto da foz (EPAGRI/CIRAM, Balneário Camboriú), à parte da previsão.
 *
 * Decisão do Jefferson de 07/10/2026: número só com horário, estação, unidade e referência vertical
 * identificados; leitura antiga nunca como atual; a diferença para a maré astronômica só quando as duas são
 * da mesma estação, no mesmo horário e na mesma referência — e com o nome "diferença entre nível observado e
 * maré astronômica prevista", sem atribuir a causa só a vento e pressão. A tábua da Marinha continua sendo a
 * previsão astronômica desta tela.
 */
export default function PainelMareMedida() {
  const { dado, carregado } = useMareMedida()
  const [agora, setAgora] = useState(() => new Date())
  useEffect(() => {
    const id = setInterval(() => setAgora(new Date()), 60_000)
    return () => clearInterval(id)
  }, [])

  const estado = estadoDaMareMedida(dado, agora)
  const { titulo, detalhe } = textoDaMareMedida(estado)
  const fonte = dado?.fonte ?? 'EPAGRI/CIRAM — marégrafos'
  const url = dado?.fonteUrl ?? 'https://ciram.epagri.sc.gov.br/index.php/maregrafos/'
  const fonteTabua = mareItajai._meta.fonte_curta ?? 'não identificada'

  return (
    <section className={estilos.painel} aria-labelledby="mare-medida-titulo">
      <h3 id="mare-medida-titulo" className={estilos.titulo}>
        Maré medida perto da foz
      </h3>
      <p className={estilos.nota}>
        Estação de {dado?.estacao.nome ?? 'Balneário Camboriú'}
        {dado?.estacao.kmDaFoz != null ? `, a ${dado.estacao.kmDaFoz} km da foz` : ''} — fonte:{' '}
        <a href={url} target="_blank" rel="noreferrer">
          {fonte}
        </a>
        . É contexto do mar perto da foz, não o nível de Itajaí.
      </p>

      {!carregado ? (
        <p className={estilos.nota}>Buscando a medição…</p>
      ) : (
        <div className={estilos.avaliado} data-estado-mare={estado.tipo}>
          <p>
            <strong>{titulo}</strong> {detalhe}
          </p>
          {estado.tipo === 'medida' && estado.diferencaM !== null ? (
            <>
              <p>
                Diferença entre nível observado e maré astronômica prevista:{' '}
                <strong>{comSinal(estado.diferencaM)}</strong>.
              </p>
              <p className={estilos.nota}>
                A maré astronômica desta conta é a que o CIRAM calcula para a mesma estação, no mesmo
                horário. A diferença pode vir de vento, pressão, da influência do rio e de outros
                efeitos; não tem uma causa só.
              </p>
            </>
          ) : null}
        </div>
      )}

      <p className={estilos.nota}>
        A previsão astronômica desta tela continua sendo a tábua do porto de Itajaí ({fonteTabua}). A
        medição e a previsão vêm de fontes e lugares diferentes, e cada uma aparece com a sua hora.
      </p>
    </section>
  )
}
