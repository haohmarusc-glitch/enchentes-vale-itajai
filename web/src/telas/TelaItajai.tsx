import { useState } from 'react'
import AvisoLegal from '../componentes/AvisoLegal'
import SeloConfianca from '../componentes/SeloConfianca'
import { cidade, fontesGerais, trechos } from '../dados/carregar'
import { dataHora } from '../logica/formato'
import { caminho, faixaHoras, janelaChegada } from '../logica/transito'
import type { Caminho } from '../logica/transito'
import estilos from './TelaItajai.module.css'

interface Origem {
  rioId: string
  rioNome: string
  cidadeId: string
}

const ORIGENS: Origem[] = [
  { rioId: 'itajai-acu', rioNome: 'Itajaí-Açu', cidadeId: 'blumenau' },
  { rioId: 'itajai-mirim', rioNome: 'Itajaí-Mirim', cidadeId: 'brusque' },
]

/**
 * Itajaí recebe os dois rios. O que a tela faz é somar o tempo de trânsito ao
 * horário do pico informado rio acima — nada mais. Não há previsão de altura
 * aqui: não existem pares históricos suficientes entre as cidades de montante e
 * Itajaí, e a maré, que muda tudo na foz, ainda não está integrada.
 */
export default function TelaItajai() {
  const [horarios, setHorarios] = useState<Record<string, string>>({})

  return (
    <>
      <h1>Itajaí — foz</h1>
      <p className={estilos.intro}>
        Itajaí recebe o Itajaí-Açu e o Itajaí-Mirim, e ainda sofre com a maré. Informe o horário do
        pico rio acima para ver quando a onda costuma chegar.
      </p>

      <AvisoLegal />

      <div className={estilos.painel}>
        {ORIGENS.map((origem) => {
          const c = cidade(origem.rioId, origem.cidadeId)
          const trecho = caminho(trechos, origem.rioId, origem.cidadeId, 'itajai')
          const valor = horarios[origem.cidadeId] ?? ''
          const partida = valor ? new Date(valor) : null
          const valida = partida !== null && !Number.isNaN(partida.getTime())

          return (
            <section className="cartao" key={origem.cidadeId}>
              <h2>
                Pico de {c?.nome ?? origem.cidadeId} — rio {origem.rioNome}
              </h2>

              <label className={estilos.campo}>
                <span>Data e hora do pico em {c?.nome ?? origem.cidadeId}</span>
                <input
                  type="datetime-local"
                  value={valor}
                  onChange={(e) =>
                    setHorarios((atual) => ({ ...atual, [origem.cidadeId]: e.target.value }))
                  }
                />
              </label>

              <div aria-live="polite">
                {!trecho ? (
                  <p className={estilos.semDado}>
                    O tempo de trânsito entre {c?.nome ?? origem.cidadeId} e Itajaí ainda não está em{' '}
                    <code>transito.json</code>. Sem esse dado, não há como estimar a chegada.
                  </p>
                ) : !valida ? (
                  <p className={estilos.aguardando}>
                    Trecho conhecido: <strong>{faixaHoras(trecho)}</strong>{' '}
                    <SeloConfianca nivel={trecho.confianca} fonte={trecho.fontes.join(' · ')} />.
                    Informe o horário do pico para ver a janela de chegada.
                  </p>
                ) : (
                  <Chegada partida={partida} trecho={trecho} />
                )}
              </div>
            </section>
          )
        })}
      </div>

      <section className="cartao">
        <h2>Maré — ainda não integrada</h2>
        <p>
          Na foz, a maré alta segura a vazante e o rio sobe mais do que a chuva sozinha explicaria.
          Isso é decisivo em Itajaí, e por isso <strong>não vamos estimar altura aqui</strong>{' '}
          enquanto a tábua de maré não estiver conectada.
        </p>
        <p className={estilos.fonteMare}>
          Fonte prevista: {fontesGerais.mare_itajai ?? 'tábuas de maré da Marinha do Brasil (DHN)'}.
          Enquanto isso, consulte a{' '}
          <a
            href="https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios"
            target="_blank"
            rel="noreferrer"
          >
            Defesa Civil de Itajaí
          </a>
          , que publica o nível dos dois rios e dos ribeirões em tempo real.
        </p>
      </section>

      <section className="cartao">
        <h2>Por que não há previsão de altura nesta tela</h2>
        <p>
          A previsão do site nasce da comparação entre picos das mesmas enchentes em duas cidades.
          Para Itajaí ainda <strong>não existem picos registrados</strong> em{' '}
          <code>enchentes.json</code>: sem eles, qualquer altura mostrada aqui seria invenção.
          Levantar esses picos, com data e hora, é a pendência mais importante do projeto.
        </p>
      </section>
    </>
  )
}

function Chegada({ partida, trecho }: { partida: Date; trecho: Caminho }) {
  const { inicio, fim } = janelaChegada(partida, trecho)
  // Alguns trechos vêm da fonte com valor único, não com faixa. Mostrar
  // "entre 15:30 e 15:30" daria a impressão de horário cravado; é o oposto
  // do que o dado sustenta.
  const valorUnico = trecho.horasMin === trecho.horasMax

  return (
    <div className={estilos.chegada}>
      <p className={estilos.janela}>
        {valorUnico ? (
          <>
            Chegada em Itajaí por volta de <strong>{dataHora(inicio)}</strong>
          </>
        ) : (
          <>
            Chegada estimada em Itajaí entre <strong>{dataHora(inicio)}</strong> e{' '}
            <strong>{dataHora(fim)}</strong>
          </>
        )}
      </p>
      <p className={estilos.detalhe}>
        Trecho de {faixaHoras(trecho)}{' '}
        <SeloConfianca nivel={trecho.confianca} fonte={trecho.fontes.join(' · ')} />
        {!trecho.direto ? ` — soma de ${trecho.trechos.length} trechos` : ''}. Horários no fuso do
        seu aparelho.
      </p>
      {valorUnico ? (
        <p className={estilos.detalhe}>
          A fonte deste trecho traz <strong>um único valor</strong>, não uma faixa. O horário acima é
          aproximação grosseira: a chegada real pode variar horas para mais ou para menos.
        </p>
      ) : null}
      <p className={estilos.ressalva}>
        A janela vale para a onda que já está descendo. Chuva nova entre as duas cidades, manobra de
        barragem ou maré alta podem adiantar, atrasar ou aumentar a cheia.
      </p>
    </div>
  )
}
