import { useMemo } from 'react'
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

/**
 * Todas as cidades, em ordem alfabética, com o endereço da página de cada uma.
 *
 * POR QUE ALFABÉTICA, e não na ordem do rio: quem chega aqui sabe o nome da
 * cidade DELE, não em que posição ela cai no curso. A ordem do rio é a resposta
 * a outra pergunta ("de onde vem a água"), e essa a tela do rio já dá.
 *
 * Itajaí entra uma vez só, apesar de estar nos dois rios: é a mesma cidade, e
 * o destino dela é a tela da foz, feita sob medida.
 */
function usarCidades() {
  return useMemo(() => {
    const vistas = new Map<string, { id: string; nome: string; rio: string; para: string }>()
    for (const [apelido, rioId, nomeRio] of [
      ['acu', 'itajai-acu', 'Açu'],
      ['mirim', 'itajai-mirim', 'Mirim'],
    ] as const) {
      for (const c of cidadesDoRio(rioId)) {
        const existente = vistas.get(c.id)
        if (existente) {
          // Cidade nos dois rios (Itajaí): nomeia os dois, sem duplicar a linha.
          existente.rio = `${existente.rio} e ${nomeRio}`
          continue
        }
        vistas.set(c.id, {
          id: c.id,
          nome: c.nome,
          rio: nomeRio,
          para: c.id === 'itajai' ? '/itajai' : `/${apelido}/${c.id}`,
        })
      }
    }
    return [...vistas.values()].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'))
  }, [])
}

export default function Inicio() {
  const cidades = usarCidades()
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

      {/* A porta mais curta: quem abre o site na chuva quer a cidade dele, e
          antes disto precisava saber em qual rio ela fica para chegar lá. */}
      <section className="cartao">
        <h2>Sua cidade</h2>
        <p className={estilos.instrucaoCidades}>
          {cidades.length} cidades com dados no site. Toque na sua para o nível na régua
          dela, as cotas, as ruas e de onde a água vem.
        </p>
        <ul className={estilos.listaCidades}>
          {cidades.map((c) => (
            <li key={c.id}>
              <Link to={c.para} className={estilos.chipCidade}>
                <span className={estilos.nomeCidade}>{c.nome}</span>
                <span className={estilos.rioCidade}>{c.rio}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

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
