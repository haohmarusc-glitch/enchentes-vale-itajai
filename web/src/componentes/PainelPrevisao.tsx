import { useMemo, useState } from 'react'
import type { Cidade, Evento, Trecho } from '../dados/tipos'
import { MIN_PARES, R2_MINIMO, prever } from '../logica/previsao'
import { caminho, faixaHoras } from '../logica/transito'
import { metros, numero } from '../logica/formato'
import SeloConfianca from './SeloConfianca'
import estilos from './PainelPrevisao.module.css'

interface Props {
  rioId: string
  eventos: Evento[]
  trechos: Trecho[]
  montante: Cidade
  jusante: Cidade
}

/**
 * Previsão do nível na próxima cidade a jusante.
 *
 * O padrão desta tela é NÃO dar número. Só aparece estimativa quando há pelo
 * menos cinco eventos pareados e a correlação se sustenta; em qualquer outro
 * caso o painel explica por que não dá, em vez de mostrar um valor bonito e
 * errado.
 */
export default function PainelPrevisao({ rioId, eventos, trechos, montante, jusante }: Props) {
  const [texto, setTexto] = useState('')
  const nivel = Number(texto.replace(',', '.'))
  const nivelValido = texto.trim() !== '' && Number.isFinite(nivel) && nivel > 0 && nivel < 40

  const resultado = useMemo(
    () => prever(eventos, montante.id, jusante.id, nivelValido ? nivel : 0),
    [eventos, montante.id, jusante.id, nivel, nivelValido],
  )
  const trecho = caminho(trechos, rioId, montante.id, jusante.id)

  return (
    <section className="cartao" aria-labelledby="previsao-titulo">
      <h2 id="previsao-titulo">
        De {montante.nome} para {jusante.nome}
      </h2>

      <p className={estilos.explicacao}>
        A estimativa compara os picos históricos das duas cidades nos mesmos eventos. Os metros de{' '}
        {montante.nome} e de {jusante.nome} estão em réguas diferentes — é justamente essa relação
        que a conta traduz.
      </p>

      <label className={estilos.campo}>
        <span>Nível agora em {montante.nome}, na régua local (m)</span>
        <input
          type="text"
          inputMode="decimal"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="ex.: 8,20"
          aria-describedby="previsao-resultado"
        />
      </label>

      <div id="previsao-resultado" className={estilos.resultado} aria-live="polite">
        {resultado.status === 'dados-insuficientes' ? (
          <Recusa titulo="Dados insuficientes">
            Só há <strong>{resultado.pares.length}</strong> evento
            {resultado.pares.length === 1 ? '' : 's'} com pico registrado nas duas cidades. São
            necessários pelo menos <strong>{MIN_PARES}</strong> para arriscar uma estimativa.
            Levantar esses picos é uma pendência aberta do projeto.
          </Recusa>
        ) : resultado.status === 'correlacao-fraca' ? (
          <Recusa titulo="Correlação fraca demais">
            Os {resultado.ajuste.n} eventos pareados não formam relação consistente (r² ={' '}
            {numero(resultado.ajuste.r2)}; o mínimo aceito é {numero(R2_MINIMO)}). Qualquer número
            aqui seria chute.
          </Recusa>
        ) : resultado.status === 'relacao-implausivel' ? (
          <Recusa titulo="Relação implausível">
            O ajuste indica que {jusante.nome} <em>desceria</em> quando {montante.nome} sobe, o que
            não faz sentido físico. Provável erro de pareamento ou de régua nos dados — conferir
            antes de usar.
          </Recusa>
        ) : !nivelValido ? (
          <p className={estilos.aguardando}>
            Há {resultado.ajuste.n} eventos pareados (r² = {numero(resultado.ajuste.r2)}). Digite o
            nível atual de {montante.nome} para ver a faixa estimada em {jusante.nome}.
          </p>
        ) : (
          <div>
            <p className={estilos.faixa}>
              Em {jusante.nome}, faixa estimada de{' '}
              <strong>
                {metros(resultado.minimo)} a {metros(resultado.maximo)}
              </strong>
            </p>
            <p className={estilos.detalheFaixa}>
              Intervalo de 95% a partir de {resultado.ajuste.n} eventos (r² ={' '}
              {numero(resultado.ajuste.r2)}). O centro da conta cai em {metros(resultado.central)},
              mas <strong>o que vale é a faixa inteira</strong>.
            </p>
            {resultado.extrapolacao ? (
              <p className={estilos.extrapolacao}>
                <strong>Atenção:</strong> {metros(nivel)} está fora da faixa já observada em{' '}
                {montante.nome} ({metros(resultado.ajuste.xMin)} a {metros(resultado.ajuste.xMax)}).
                A conta está extrapolando para além do que os dados sustentam — trate o resultado
                como ordem de grandeza, nada além disso.
              </p>
            ) : null}
            <p className={estilos.ressalva}>
              A estimativa ignora a chuva que cair entre as duas cidades, o estado das barragens e a
              maré. Ela só descreve o que aconteceu em cheias passadas.
            </p>
          </div>
        )}
      </div>

      <p className={estilos.transito}>
        {trecho ? (
          <>
            Tempo de trânsito da onda: <strong>{faixaHoras(trecho)}</strong>{' '}
            <SeloConfianca nivel={trecho.confianca} fonte={trecho.fontes.join(' · ')} />
          </>
        ) : (
          <span className={estilos.semDado}>
            Tempo de trânsito entre {montante.nome} e {jusante.nome} ainda não levantado.
          </span>
        )}
      </p>
    </section>
  )
}

function Recusa({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <div className={estilos.recusa}>
      <strong>{titulo}</strong>
      <p>{children}</p>
    </div>
  )
}
