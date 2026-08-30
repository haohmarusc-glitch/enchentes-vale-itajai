import { Link } from 'react-router-dom'
import AvisoLegal from '../componentes/AvisoLegal'
import { cidadesDoRio, eventosDoRio } from '../dados/carregar'
import estilos from './Inicio.module.css'

const RIOS = [
  {
    para: '/acu',
    id: 'itajai-acu',
    titulo: 'Rio Itajaí-Açu',
    descricao: 'Taió e Rio do Sul → Ibirama → Indaial → Blumenau → Gaspar → Ilhota → Itajaí',
  },
  {
    para: '/mirim',
    id: 'itajai-mirim',
    titulo: 'Rio Itajaí-Mirim',
    descricao: 'Vidal Ramos → Botuverá → Brusque → Itajaí',
  },
]

export default function Inicio() {
  return (
    <>
      <h1>Enchentes do Vale do Itajaí</h1>
      <p className={estilos.entrada}>
        Onde o rio já chegou em cada cidade, quanto tempo a cheia leva para descer e o que os
        eventos passados sugerem para a cidade seguinte.
      </p>

      <AvisoLegal />

      <h2>Escolha o rio</h2>
      <ul className={estilos.lista}>
        {RIOS.map((rio) => {
          const cidades = cidadesDoRio(rio.id).length
          const registros = eventosDoRio(rio.id).length
          return (
            <li key={rio.id}>
              <Link to={rio.para} className={estilos.cartaoRio}>
                <span className={estilos.tituloRio}>{rio.titulo}</span>
                <span className={estilos.descricao}>{rio.descricao}</span>
                <span className={estilos.contagem}>
                  {cidades} cidades · {registros} picos históricos registrados
                </span>
              </Link>
            </li>
          )
        })}
        <li>
          <Link to="/itajai" className={estilos.cartaoRio}>
            <span className={estilos.tituloRio}>Itajaí (foz)</span>
            <span className={estilos.descricao}>
              Onde os dois rios se encontram, com influência da maré
            </span>
            <span className={estilos.contagem}>chegada dos dois picos</span>
          </Link>
        </li>
      </ul>

      <section className="cartao">
        <h2>Como ler este site</h2>
        <p>
          <strong>Cada cidade tem sua própria régua.</strong> O zero de cada uma foi cravado numa
          altura diferente, então os metros não se comparam entre cidades. O que se compara é a
          cidade com ela mesma, ao longo do tempo.
        </p>
        <p>
          <strong>Todo número mostra de onde veio.</strong> Onde a fonte é oficial ou acadêmica, o
          selo diz "confiança alta". Onde é imprensa ou compilação de internet, o selo avisa. Onde
          não existe dado, a tela diz que não existe — não preenchemos buraco com estimativa.
        </p>
        <p>
          <strong>Tempo de chegada é sempre faixa.</strong> "14–17 h" quer dizer que a cheia costumou
          levar entre 14 e 17 horas naquele trecho. Não é horário marcado, e chuva no meio do
          caminho muda a conta.
        </p>
      </section>
    </>
  )
}
