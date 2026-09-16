import { lazy, Suspense, useMemo, useState } from 'react'
import AvisoLegal from '../componentes/AvisoLegal'

/**
 * O mapa carrega à parte, como o gráfico de picos.
 *
 * O Leaflet sozinho pesa mais que todo o resto do site somado, e o mapa existe
 * só nesta tela. Embutido no pacote inicial, quem abre o site no celular
 * durante a chuva para ver o nível do rio pagaria por ele sem chegar a usá-lo.
 */
const MapaManchas = lazy(() => import('../componentes/MapaManchas'))

import { cidade, estacoesTempoReal, fontesGerais, mareItajai } from '../dados/carregar'
import { separarFonte, todasAsReguas } from '../logica/reguas'
import { leiturasDaCidadeEmTodosOsRios, useTempoReal } from '../dados/tempoReal'
import VariasReguas from '../componentes/VariasReguas'
import ReguasDaCidade from '../componentes/ReguasDaCidade'
import estilos from './TelaItajai.module.css'

/**
 * Itajaí recebe os dois rios. O que a tela faz é somar o tempo que a cheia leva
 * para descer ao horário do pico informado rio acima — nada mais. Não há previsão de altura
 * aqui: não existem pares históricos suficientes entre as cidades de montante e
 * Itajaí, e a maré, que muda tudo na foz, ainda não está integrada.
 */
export default function TelaItajai() {
  const [mapaAberto, setMapaAberto] = useState(false)
  const tempoReal = useTempoReal()
  // As onze réguas de Itajaí estão espalhadas por quatro cursos d'água (Açu,
  // Mirim e dois ribeirões): pedir por rio devolveria um terço da cidade.
  const leiturasDeItajai = leiturasDaCidadeEmTodosOsRios(tempoReal, 'itajai')
  const reguas = todasAsReguas(estacoesTempoReal, 'itajai')
  // Itajaí está cadastrada no Açu; é o mesmo município das réguas do Mirim e
  // dos ribeirões — o que varia é o curso d'água de cada régua, não a cidade.
  const cidadeItajai = cidade('itajai-acu', 'itajai')
  const agora = useMemo(() => new Date(), [tempoReal])

  return (
    <>
      <h1>Itajaí — foz</h1>
      <p className={estilos.intro}>
        Itajaí recebe o Itajaí-Açu e o Itajaí-Mirim, e ainda sofre com a maré. Consulte as medições de cada régua e as áreas atingidas em eventos históricos.
      </p>

      <AvisoLegal />

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

      {/* AGORA, RÉGUA POR RÉGUA.

          Esta seção dizia "por que esta tela não mostra o nível de Itajaí ao
          vivo", e a decisão estava certa quando foi tomada: eleger uma das onze
          e chamar de "o nível de Itajaí" seria comparar réguas de zeros
          diferentes, que é o erro que esta tela existe para não cometer.

          Mas o próprio texto dizia a condição: "ENQUANTO NÃO HOUVER cota de
          referência por régua". Ela foi cumprida — as ONZE têm cota própria
          cadastrada, e é por isso que a tabela mais abaixo consegue listá-las
          uma a uma. Com cota por régua, cada leitura é comparada com a cota
          DELA, e não há comparação entre réguas em lugar nenhum.

          O que continuava acontecendo, enquanto a condição já estava cumprida:
          a cidade da foz — a única cortada pelos dois rios — mandava o morador
          para outro site atrás de um número que este projeto já tinha, onze
          vezes. "A tela cala alguma coisa que ela mediu" é uma das quatro
          falhas do roteiro de teste. */}
      <section className="cartao">
        <h2>Como estão as réguas de Itajaí agora</h2>
        {leiturasDeItajai.length > 0 && cidadeItajai ? (
          <VariasReguas
            leituras={leiturasDeItajai}
            reguas={reguas}
            cidade={cidadeItajai}
            agora={agora}
          />
        ) : (
          <p>
            Sem leitura ao vivo neste momento. As cotas de cada régua continuam na tabela
            abaixo, e a fonte é a{' '}
            <a
              href="https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios"
              target="_blank"
              rel="noreferrer"
            >
              página da Defesa Civil de Itajaí
            </a>
            .
          </p>
        )}
        <p className={estilos.fonteMare}>
          <strong>Não existe "o nível de Itajaí".</strong> As réguas têm zeros diferentes:
          numa mesma hora podem marcar 0,92 m e 4,82 m sem que uma esteja pior que a outra.
          Cada número acima é comparado com a cota <em>daquela</em> régua — nunca com a de
          outra, nem com a de outra cidade. Fonte:{' '}
          <a
            href="https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios"
            target="_blank"
            rel="noreferrer"
          >
            Defesa Civil de Itajaí
          </a>
          .
        </p>
      </section>

      <ReguasDeItajai />

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
 * oficial.
 *
 * Esta tabela é a REFERÊNCIA (o que cada régua considera atenção, alerta e
 * emergência). A leitura ao vivo de cada uma fica no bloco "Como estão as
 * réguas de Itajaí agora", acima. Continua não existindo "o nível de Itajaí":
 * são onze réguas com zeros diferentes, e cada leitura é comparada com a cota
 * DELA.
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
