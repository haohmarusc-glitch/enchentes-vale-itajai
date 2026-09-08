import type { Cidade, Evento } from '../dados/tipos'
import type { LeituraAoVivo } from '../dados/tempoReal'
import { dataLegivel } from '../logica/datas'
import { metros } from '../logica/formato'
import { cenarioDaCidade } from '../logica/cenarioAnterior'
import { frescor, idadeMin, textoIdade } from '../logica/tempoReal'
import estilos from './PainelCenarioAnterior.module.css'

/**
 * Quanto falta, na régua desta cidade, para o rio chegar em cada cheia antiga.
 *
 * POR QUE NÃO DIZ "PARECIDO COM 2008". O pedido original era mostrar "o cenário
 * mais próximo de uma enchente anterior". A frase esconde um erro: um nível
 * qualquer não se compara com um PICO. Estar em 8,0 m subindo não é igual à
 * cheia que picou em 8,5 — é possivelmente pior, porque ainda vai subir. Quem
 * lê "parecido com 2008" recebe um fim conhecido para uma história que não
 * terminou, e é assim que alguém se sente mais seguro do que está.
 *
 * Então o painel diz distância, que é fato: "faltam 5,34 m para a marca de
 * 2011". A comparação com o passado vira régua na parede, não profecia.
 *
 * SÓ APARECE COM LEITURA FRESCA. Distância calculada a partir de um número de
 * horas atrás é falsa nos dois sentidos: o rio pode ter subido meio metro desde
 * então, ou baixado.
 */
export default function PainelCenarioAnterior({
  cidade,
  eventos,
  leitura,
  agora,
}: {
  cidade: Cidade
  eventos: readonly Evento[]
  leitura: LeituraAoVivo | null
  agora: Date
}) {
  if (!leitura?.medidoEm || typeof leitura.nivel_m !== 'number') return null
  const idade = idadeMin(leitura.medidoEm, agora)
  if (frescor(idade) !== 'agora') return null

  const { cenario, motivo } = cenarioDaCidade(leitura.nivel_m, eventos)

  // As recusas por ESCALA são ditas na tela; as por falta de dado, não. A
  // diferença: "não temos pico de Ituporanga" o mapa já mostra em cinza, e
  // repetir vira ruído. Já "temos 113 picos de Blumenau e mesmo assim não
  // comparamos" é contraintuitivo — quem vê o gráfico logo acima merece saber
  // por que o número não virou distância.
  if (!cenario) {
    if (motivo === 'sem-leitura' || motivo === 'sem-picos') return null
    return (
      <section className="cartao" aria-labelledby="cenario-titulo">
        <h2 id="cenario-titulo">Quanto falta para as cheias antigas</h2>
        <p className={estilos.recusa}>
          <strong>Não dá para comparar em {cidade.nome}.</strong>{' '}
          {motivo === 'referencia-misturada'
            ? 'Os picos históricos desta cidade estão em mais de uma referência, e a leitura de agora é da régua. Subtrair um do outro daria um número com duas casas decimais e nenhum significado.'
            : 'Os picos históricos desta cidade foram medidos em outra referência — ou nenhuma fonte declarou qual —, e a leitura de agora é da régua. São escalas diferentes: a diferença entre elas entraria inteira na conta.'}{' '}
          Os valores continuam no gráfico acima, cada um com a sua fonte.
        </p>
      </section>
    )
  }

  const { nivel, marcas, proxima, ultimaPassada, referenciaConferida } = cenario

  return (
    <section className="cartao" aria-labelledby="cenario-titulo">
      <h2 id="cenario-titulo">Quanto falta para as cheias antigas</h2>

      <p className={estilos.agora}>
        {cidade.nome} está em <strong>{metros(nivel)}</strong> ({textoIdade(idade)}).
      </p>

      <p className={estilos.aviso}>
        <strong>Isto é distância, não semelhança.</strong> Cada número abaixo é o pico de uma
        cheia que já aconteceu. Estar a meio metro de uma marca não quer dizer que a cheia vai
        parar ali — o rio pode continuar subindo e passar dela.
      </p>

      {proxima ? (
        <p className={estilos.proxima}>
          A marca mais próxima acima é a de <strong>{dataLegivel(proxima.data)}</strong>, que
          chegou a {metros(proxima.pico)}. Faltam <strong>{metros(proxima.diferenca)}</strong>.
        </p>
      ) : (
        <p className={estilos.acima}>
          ⚠️ O rio está <strong>acima de todas as cheias registradas</strong> nesta cidade
          {ultimaPassada ? <> — a mais alta foi {dataLegivel(ultimaPassada.data)}, com {metros(ultimaPassada.pico)}</> : null}.
          Não há marca antiga para comparar. Siga a Defesa Civil, não este site.
        </p>
      )}

      <ul className={estilos.lista}>
        {marcas.map((m) => (
          <li key={`${m.data}-${m.pico}`} className={m.passou ? estilos.passada : estilos.acimaItem}>
            <span className={estilos.quando}>{dataLegivel(m.data)}</span>
            <span className={estilos.pico}>{metros(m.pico)}</span>
            <span className={estilos.falta}>
              {m.passou ? `${metros(-m.diferenca)} abaixo do nível de agora` : `faltam ${metros(m.diferenca)}`}
            </span>
          </li>
        ))}
      </ul>

      {!referenciaConferida ? (
        <p className={estilos.ressalva} role="note">
          <strong>Referência não conferida.</strong> Nenhum destes registros declara em que régua
          foi medido; o site assume a régua local, que é a convenção para registro antigo. Se
          algum deles vier de outra referência, a distância muda. Vale como ordem de grandeza,
          não como medida.
        </p>
      ) : null}

      <p className={estilos.regua}>
        Todos os números são da régua de {cidade.nome}. <strong>Não compare com outra cidade</strong> —
        cada régua tem o seu zero.
      </p>
    </section>
  )
}
