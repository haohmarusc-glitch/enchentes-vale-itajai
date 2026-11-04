import { useEffect, useState } from 'react'
import { estadoDosAvisos, linhaDoAviso, textoDosAvisos, useAvisosDcsc } from '../dados/avisosDcsc'
import estilos from './PainelMare.module.css'

/**
 * Avisos meteorológicos da Defesa Civil de SC, por REGIÃO (decisão do Jefferson, 04/11/2026).
 *
 * A DCSC escreve os avisos em prosa e nomeia regiões ("Vale do Itajaí", "Foz do Itajaí", "todo o Estado"), nunca
 * município. Por isso o painel diz "para a região" e nunca "para a sua cidade", repassa a categoria como a fonte
 * escreve, dá a hora de Brasília e o link do original. Nada aqui é faixa do rio nem pinta coisa alguma.
 */
export default function PainelAvisosDcsc() {
  const { dado, carregado } = useAvisosDcsc()
  const [agora, setAgora] = useState(() => new Date())
  useEffect(() => {
    const id = setInterval(() => setAgora(new Date()), 60_000)
    return () => clearInterval(id)
  }, [])

  const estado = estadoDosAvisos(dado, agora)
  const { titulo, detalhe } = textoDosAvisos(estado)
  const fonte = dado?.fonte ?? 'Defesa Civil de Santa Catarina — www.defesacivil.sc.gov.br'
  const url = dado?.fonteUrl ?? 'https://www.defesacivil.sc.gov.br/'

  return (
    <section className={estilos.painel} aria-labelledby="avisos-dcsc-titulo">
      <h3 id="avisos-dcsc-titulo" className={estilos.titulo}>
        Avisos da Defesa Civil de SC (por região)
      </h3>
      <p className={estilos.nota}>
        Avisos meteorológicos oficiais do Estado, como a Defesa Civil publica — fonte:{' '}
        <a href={url} target="_blank" rel="noreferrer">
          {fonte}
        </a>
        .
      </p>
      {!carregado ? (
        <p className={estilos.nota}>Buscando os avisos…</p>
      ) : (
        <div className={estilos.avaliado} data-estado-avisos={estado.tipo}>
          <p>
            <strong>{titulo}</strong> {detalhe}
          </p>
          {estado.tipo === 'avisos' ? (
            <ul className={estilos.lista}>
              {estado.recentes.map((a) => (
                <li key={a.id}>
                  <strong>{a.titulo}</strong>
                  <br />
                  {linhaDoAviso(a)}
                  {a.link ? (
                    <>
                      {' · '}
                      <a href={a.link} target="_blank" rel="noreferrer">
                        ler no site da Defesa Civil
                      </a>
                    </>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      )}
      <p className={estilos.nota}>
        O aviso vale para a <strong>região</strong> que a Defesa Civil nomeia, não para uma cidade, e <strong>não é a
        faixa do rio</strong>: a cor desta página continua vindo só da régua. Em emergência, ligue 199.
      </p>
    </section>
  )
}
