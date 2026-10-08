import { useEffect, useState } from 'react'
import { estadoDoCentro, textoDoCentro, useCentroItuporanga } from '../dados/ituporangaCentro'
import estilos from './PainelMare.module.css'

/**
 * A régua do CENTRO de Ituporanga, à parte da cor da cidade (decisão do Jefferson, 08/10/2026).
 *
 * A cor de Ituporanga vem da DCSC-00039, a jusante da Barragem Sul. A Prefeitura lê outra régua, no Centro,
 * duas vezes por dia. Ela entra aqui com horário e fonte e SEM cor: a fonte não informa o zero nem as cotas
 * desta régua, e a criticidade que ela escreve é repassada como texto dela. Nada aqui pinta o mapa.
 */
export default function PainelCentroItuporanga() {
  const { dado, carregado } = useCentroItuporanga()
  const [agora, setAgora] = useState(() => new Date())
  useEffect(() => {
    const id = setInterval(() => setAgora(new Date()), 60_000)
    return () => clearInterval(id)
  }, [])

  const estado = estadoDoCentro(dado, agora)
  const { titulo, detalhe } = textoDoCentro(estado)
  const fonte = dado?.fonte ?? 'Prefeitura de Ituporanga — Defesa Civil, Boletim Diário'
  const url = dado?.fonteUrl ?? 'https://www.ituporanga.sc.gov.br/nivel-rio'

  return (
    <section className={estilos.painel} aria-labelledby="centro-ituporanga-titulo">
      <h3 id="centro-ituporanga-titulo" className={estilos.titulo}>
        Régua do Centro (Prefeitura)
      </h3>
      <p className={estilos.nota}>
        Leitura manual da Defesa Civil de Ituporanga, duas vezes por dia — fonte:{' '}
        <a href={url} target="_blank" rel="noreferrer">
          {fonte}
        </a>
        .
      </p>
      {!carregado ? (
        <p className={estilos.nota}>Buscando a leitura…</p>
      ) : (
        <div className={estilos.avaliado} data-estado-centro={estado.tipo}>
          <p>
            <strong>{titulo}</strong> {detalhe}
          </p>
        </div>
      )}
      <p className={estilos.nota}>
        É <strong>outra régua</strong>, não a DCSC-00039 que dá a cor desta página (essa fica a jusante da Barragem
        Sul). A fonte não informa o zero nem as cotas dela: os metros não se comparam com os de cima, e esta
        leitura <strong>não recebe cor</strong> até a Defesa Civil confirmar as cotas na mesma régua.
      </p>
    </section>
  )
}
