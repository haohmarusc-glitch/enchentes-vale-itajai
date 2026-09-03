import { lazy, Suspense, useState } from 'react'
import AvisoLegal from '../componentes/AvisoLegal'
import PainelMare from '../componentes/PainelMare'
import AbrigoMaisProximo from '../componentes/AbrigoMaisProximo'

/**
 * O mapa carrega à parte, como o gráfico de picos.
 *
 * O Leaflet sozinho pesa mais que todo o resto do site somado, e o mapa existe
 * só nesta tela. Embutido no pacote inicial, quem abre o site no celular
 * durante a chuva para ver o nível do rio pagaria por ele sem chegar a usá-lo.
 */
const MapaManchas = lazy(() => import('../componentes/MapaManchas'))

import SeloConfianca from '../componentes/SeloConfianca'
import { cidade, estacoesTempoReal, fontesGerais, mareItajai, trechos } from '../dados/carregar'
import { separarFonte, todasAsReguas } from '../logica/reguas'
import ReguasDaCidade from '../componentes/ReguasDaCidade'
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
 * Itajaí recebe os dois rios. O que a tela faz é somar o tempo que a cheia leva
 * para descer ao horário do pico informado rio acima — nada mais. Não há previsão de altura
 * aqui: não existem pares históricos suficientes entre as cidades de montante e
 * Itajaí, e a maré, que muda tudo na foz, ainda não está integrada.
 */
export default function TelaItajai() {
  const [horarios, setHorarios] = useState<Record<string, string>>({})
  const [mapaAberto, setMapaAberto] = useState(false)

  return (
    <>
      <h1>Itajaí — foz</h1>
      <p className={estilos.intro}>
        Itajaí recebe o Itajaí-Açu e o Itajaí-Mirim, e ainda sofre com a maré. Informe o horário do
        pico rio acima para ver quando a cheia costuma chegar.
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
                    O tempo que a cheia leva de {c?.nome ?? origem.cidadeId} até Itajaí ainda não está em{' '}
                    <code>transito.json</code>. Sem esse dado, não há como estimar a chegada.
                  </p>
                ) : !valida ? (
                  <p className={estilos.aguardando}>
                    Trecho conhecido: <strong>{faixaHoras(trecho)}</strong>{' '}
                    <SeloConfianca nivel={trecho.confianca} fonte={trecho.fontes.join(' · ')} tipo="trecho"
                      />.
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
        <h2>Por que a maré pesa tanto aqui</h2>
        <p>
          Itajaí é o único município cortado pelos dois maiores rios da bacia. Na foz, a maré alta{' '}
          <strong>trava a saída da água</strong>: o rio não deixa de descer por falta de força, e
          sim porque o mar está no caminho. A mesma cheia que passaria batido na vazante empoça na
          preamar.
        </p>
        <p>
          O Itajaí-Mirim sofre duas vezes. A UNIVALI documenta, no estudo do canal extravasor, que a
          inundação de Itajaí se deve também ao transbordamento do Mirim — cujas águas{' '}
          <strong>não escoam para o Açu</strong> quando os dois leitos já estão cheios. Some a isso
          uma preamar de sizígia e o Mirim não tem para onde ir.
        </p>
        <p className={estilos.fonteMare}>
          Fonte da tábua usada nesta tela:{' '}
          {mareItajai._meta.fonte_url ? (
            <a href={mareItajai._meta.fonte_url} target="_blank" rel="noreferrer">
              {mareItajai._meta.fonte_curta ?? 'não identificada'}
            </a>
          ) : (
            mareItajai._meta.fonte_curta ?? 'não identificada'
          )}
          . Fonte de origem: {fontesGerais.mare_itajai}. A UNIVALI e a Defesa Civil ampliaram o
          marégrafo do porto justamente para medir esse efeito sobre o Açu e o Mirim.
          {mareItajai._meta.aviso_interino ? (
            <>
              {' '}
              <strong>Aviso:</strong> {mareItajai._meta.aviso_interino}
            </>
          ) : null}
        </p>
      </section>

      <section className="cartao">
        <h2>Por que esta tela não mostra o nível de Itajaí ao vivo</h2>
        <p>
          A Defesa Civil de Itajaí publica <strong>várias réguas na cidade</strong> — DC-01 e
          DC-02 no Açu, DC-03 a DC-06 e DC-10 no Mirim, DC-11 na divisa. Elas têm zeros
          diferentes: numa mesma hora podem marcar 0,92 m e 4,82 m. Escolher uma delas e chamar
          de "o nível de Itajaí" seria comparar réguas, que é o erro que esta tela avisa para
          ninguém cometer.
        </p>
        <p className={estilos.fonteMare}>
          Enquanto não houver cota de referência por régua, o caminho é ver estação por estação
          na{' '}
          <a
            href="https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios"
            target="_blank"
            rel="noreferrer"
          >
            página da Defesa Civil de Itajaí
          </a>
          .
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
      <ReguasDeItajai />
      <AbrigoMaisProximo />

      {/*
        O mapa só é montado quando a pessoa pede. Antes ele era renderizado de
        imediato: mesmo com o chunk em `lazy`, o componente aparecia na primeira
        pintura, então TODO visitante baixava o Leaflet e puxava dezenas de
        tiles do OpenStreetMap — quisesse ver o mapa ou não.

        Isso custa duas vezes, e as duas doem no mesmo momento. Para quem abre o
        site no celular durante a chuva, é download que atrasa justamente o
        número que a pessoa veio buscar, na hora em que a rede está pior. E para
        o OpenStreetMap, cujos tiles públicos têm política que desencoraja uso
        pesado, é tráfego que multiplica numa noite de enchente — exatamente
        quando o site não pode cair.

        Quem quer o mapa clica e recebe. Quem quer o nível do rio não paga por
        um mapa de 1983.
      */}
      {mapaAberto ? (
        <Suspense
          fallback={
            <section className="cartao">
              <p>Carregando o mapa das enchentes…</p>
            </section>
          }
        >
          <MapaManchas />
        </Suspense>
      ) : (
        <section className="cartao">
          <h2>Até onde a água chegou</h2>
          <p className={estilos.introMapa}>
            Áreas atingidas em nove enchentes de Itajaí, entre 1983 e 2015, publicadas pela{' '}
            <strong>própria prefeitura</strong> na organização GeoItajaí, sob licença MIT.
          </p>
          <button type="button" className={estilos.abrirMapa} onClick={() => setMapaAberto(true)}>
            Ver o mapa das áreas atingidas
          </button>
          <p className={estilos.avisoMapa}>
            O mapa fica fora do carregamento inicial de propósito: ele baixa bem mais dados que o
            resto da página, e numa noite de chuva quem abre o site quer primeiro o nível do rio.
          </p>
        </section>
      )}

    </>
  )
}

/**
 * As réguas de Itajaí, com as cotas do Plano de Contingência.
 *
 * Esta tela é o único lugar onde os ribeirões aparecem: Murta e Canhanduba não
 * estão em nenhum dos dois eixos, mas alagam bairro em Itajaí, e a cota deles é
 * oficial. Aqui não há nível ao vivo — o que a cidade tem são onze réguas com
 * zeros diferentes, e eleger uma como "o nível de Itajaí" seria produzir um
 * número que não existe.
 */
function ReguasDeItajai() {
  const reguas = todasAsReguas(estacoesTempoReal, 'itajai')
  if (reguas.length === 0) return null

  const fontes = [...new Set(reguas.map((r) => r.fonteCotas).filter((f): f is string => !!f))]

  return (
    <section className="cartao">
      <h2>Cotas oficiais das réguas de Itajaí</h2>
      <p className={estilos.introReguas}>
        As onze réguas aparecem sob o seu curso d'água — os dois rios e os dois ribeirões — e na
        ordem em que o rio desce, da nascente para o mar. É a posição física de cada uma, não o
        número da régua.
      </p>
      <ReguasDaCidade reguas={reguas} cidade="Itajaí" comTitulo={false} agrupadoPorCurso />
      {fontes.map((bruta) => {
        const { texto, url } = separarFonte(bruta)
        return (
          <p className={estilos.detalhe} key={bruta}>
            Fonte:{' '}
            {url ? (
              <a href={url} target="_blank" rel="noreferrer">
                {texto}
              </a>
            ) : (
              texto
            )}
          </p>
        )
      })}
    </section>
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
        <SeloConfianca nivel={trecho.confianca} fonte={trecho.fontes.join(' · ')} tipo="trecho"
                      />
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
        A janela vale para a cheia que já está descendo. Chuva nova entre as duas cidades ou manobra
        de barragem podem adiantar, atrasar ou aumentar a cheia.
      </p>

      <PainelMare inicio={inicio} fim={fim} />

    </div>
  )
}
