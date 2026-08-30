import { useMemo, useState } from 'react'
import { fontesGerais, mareItajai } from '../dados/carregar'
import { dataHora } from '../logica/formato'
import {
  JANELA_PREAMAR_H,
  TEXTO_REGIME,
  agravamento,
  cruzarComMare,
  type Preamar,
} from '../logica/mare'
import estilos from './PainelMare.module.css'

/**
 * A maré na chegada da cheia.
 *
 * Em Itajaí a preamar trava o escoamento: a mesma cheia que passaria na vazante
 * empoça na maré alta, e o Itajaí-Mirim deixa de entregar água ao Açu. Este
 * painel não diz quantos centímetros a maré acrescenta — não há nada nos dados
 * do projeto que calibre isso. Ele responde ao que dá para verificar: a cheia
 * chega junto com a preamar, e é período de maré grande?
 */
export default function PainelMare({ inicio, fim }: { inicio: Date; fim: Date }) {
  const [manuais, setManuais] = useState<string[]>(['', ''])

  const daTabua = useMemo(() => {
    const margem = 36 * 3_600_000
    return mareItajai.preamares
      .map((e) => ({ quando: new Date(e.quando), altura_m: e.altura_m }))
      .filter(
        (p) =>
          p.quando.getTime() >= inicio.getTime() - margem &&
          p.quando.getTime() <= fim.getTime() + margem,
      )
  }, [inicio, fim])

  const informadas: Preamar[] = useMemo(() => {
    if (daTabua.length > 0) return daTabua
    return manuais
      .filter((v) => v.trim() !== '')
      .map((v) => ({ quando: new Date(v) }))
      .filter((p) => !Number.isNaN(p.quando.getTime()))
  }, [daTabua, manuais])

  const cruzamento = cruzarComMare(inicio, fim, informadas)
  const nivel = agravamento(cruzamento)
  const daFonte = daTabua.length > 0

  return (
    <section className={estilos.painel} aria-labelledby="mare-titulo">
      <h3 id="mare-titulo" className={estilos.titulo}>
        A maré na hora da chegada
      </h3>

      <p className={estilos.regime}>
        No horário previsto: <strong>{TEXTO_REGIME[cruzamento.regime]}</strong>.
      </p>
      <p className={estilos.nota}>
        O regime vem da fase da lua, que é cálculo exato. Ele diz se as preamares do período são
        as maiores do mês — <strong>não</strong> a que horas elas acontecem. Para isso é preciso a
        tábua.
      </p>

      {nivel === 'sem-tabua' ? (
        <div className={estilos.semTabua}>
          <p>
            <strong>Não temos a tábua de maré deste dia.</strong> Sem ela não dá para dizer se a
            cheia chega na preamar — e horário de maré não se estima.
          </p>
          <p className={estilos.nota}>
            Consulte a{' '}
            <a href={fontesGerais.mare_dc_itajai} target="_blank" rel="noreferrer">
              tábua da Defesa Civil de Itajaí
            </a>{' '}
            ({fontesGerais.mare_itajai}) e informe as preamares abaixo. Quem mantém o site preenche
            isso automaticamente rodando <code>scripts/coleta_mares.py</code>.
          </p>
          <div className={estilos.campos}>
            {manuais.map((valor, i) => (
              <label key={i} className={estilos.campo}>
                <span>{i + 1}ª preamar do período</span>
                <input
                  type="datetime-local"
                  value={valor}
                  onChange={(e) =>
                    setManuais((atual) => atual.map((v, k) => (k === i ? e.target.value : v)))
                  }
                />
              </label>
            ))}
          </div>
        </div>
      ) : (
        <div className={nivel === 'agrava' ? estilos.agrava : estilos.avaliado}>
          <p className={estilos.veredito}>
            {nivel === 'agrava' ? (
              <>
                <strong>A cheia chega na preamar, em maré de sizígia.</strong> É a pior combinação:
                a maré alta segura a vazante justo quando o pico passa.
              </>
            ) : nivel === 'atencao' ? (
              cruzamento.coincide ? (
                <>
                  <strong>A cheia chega junto com a preamar.</strong> O escoamento fica represado
                  no momento do pico.
                </>
              ) : (
                <>
                  <strong>Nenhuma preamar cai na janela</strong>, mas é período de maré grande. As
                  preamares em volta são as mais altas do mês.
                </>
              )
            ) : (
              <>
                <strong>O horário não agrava.</strong> Nenhuma preamar cai na janela de chegada e a
                maré do período não é das maiores.
              </>
            )}
          </p>

          {cruzamento.coincidentes.length > 0 ? (
            <ul className={estilos.lista}>
              {cruzamento.coincidentes.map((p) => (
                <li key={p.quando.toISOString()}>
                  Preamar às <strong>{dataHora(p.quando)}</strong>
                  {p.altura_m !== undefined ? ` — ${p.altura_m.toFixed(2)} m na tábua` : ''}
                </li>
              ))}
            </ul>
          ) : null}

          <p className={estilos.nota}>
            Conta como coincidência qualquer preamar até {JANELA_PREAMAR_H} h da janela de chegada:
            o rio já começa a represar antes do instante da maré alta.{' '}
            {daFonte ? (
              <>
                Tábua de{' '}
                <a href={fontesGerais.mare_dc_itajai} target="_blank" rel="noreferrer">
                  Defesa Civil de Itajaí
                </a>
                .
              </>
            ) : (
              'Preamares informadas nesta tela.'
            )}
          </p>
        </div>
      )}

      <p className={estilos.mecanismo}>
        A maré não soma centímetros a uma previsão — ela <strong>impede o rio de descer</strong>.
        Por isso esta tela não converte maré em metros: não há, nos dados deste projeto, nada que
        calibre esse número. Itajaí é o único município cortado pelos dois maiores rios da bacia, e
        a UNIVALI documenta que o Itajaí-Mirim transborda justamente por não conseguir entregar
        água ao Itajaí-Açu quando os dois leitos já estão cheios.
      </p>
    </section>
  )
}
