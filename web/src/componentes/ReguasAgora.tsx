import type { ReactElement } from 'react'
import type { Cidade } from '../dados/tipos'
import type { LeituraAoVivo } from '../dados/tempoReal'
import { distancia } from '../logica/agora'
import { metros, numero, rotuloCota } from '../logica/formato'
import { agruparPorCurso, type GrupoDeCurso, type ReguaComCota } from '../logica/reguas'
import { reguasAgora, type ReguaAgora } from '../logica/reguasAgora'
import { frescorDaCidade, textoIdade } from '../logica/tempoReal'
import { ChipFaixa } from './CartaoAgora'
import MedidorCotas from './MedidorCotas'
import estilos from './ReguasAgora.module.css'

/**
 * AS RÉGUAS DE UMA CIDADE QUE TEM VÁRIAS, CADA UMA COMO UM CARTÃO "AGORA".
 *
 * Itajaí tem onze réguas, no Açu, no Mirim (com os dois braços) e em dois
 * ribeirões. Cada uma sai como o cartão de Blumenau, em miniatura: faixa (cor +
 * nome), número, idade da medição e a régua desenhada nas cotas DELA. Agrupadas
 * pelo curso d'água, da nascente para o mar — nunca numa fila só, que faria ler
 * a régua de um braço como se fosse do outro.
 *
 * O que continua proibido: somar, comparar ou eleger uma régua como "o nível de
 * Itajaí". O aviso vem antes dos números, no mesmo bloco.
 */
export default function ReguasAgora({
  cidade,
  reguas,
  leituras,
  agora,
}: {
  cidade: Cidade
  reguas: ReguaComCota[]
  leituras: LeituraAoVivo[]
  agora: Date
}) {
  if (reguas.length === 0) return null
  const grupos = agruparPorCurso(reguas)
  const porTitulo = new Map(reguasAgora(reguas, leituras, cidade.id, agora).map((x) => [x.regua.titulo, x]))
  const cartao = (r: ReguaComCota) => {
    const x = porTitulo.get(r.titulo)
    return x ? <CartaoRegua key={r.id} x={x} cidade={cidade} /> : null
  }
  const comMare = reguas.filter((r) => !r.alertaAutomatico && r.senteMare).length

  return (
    <div className={estilos.bloco}>
      <p className={estilos.aviso}>
        <strong>
          {reguas.length} réguas em {grupos.length === 1 ? 'um curso d’água' : `${grupos.length} cursos d’água`}
        </strong>
        , cada uma com o seu zero: os metros de uma não se comparam com os de outra. A cor de cada
        régua sai das cotas dela.
      </p>
      {grupos.map((g) => (
        <section key={g.rio} className={estilos.curso} aria-label={g.nome}>
          <h3 className={estilos.nomeCurso}>
            {g.nome}
            {g.reguas.length > 1 ? <span className={estilos.sentido}> · da nascente para o mar</span> : null}
          </h3>
          {g.divisao ? <ComBracos divisao={g.divisao} cartao={cartao} /> : g.reguas.map(cartao)}
        </section>
      ))}
      {comMare > 0 ? (
        <p className={estilos.explicacao}>
          As réguas marcadas com <strong>maré</strong> ficam no estuário: sobem e descem duas vezes por
          dia e podem passar da cota num dia sem chuva. A cota é a oficial, mas passar dela,
          sozinha, não quer dizer que há cheia chegando.
        </p>
      ) : null}
    </div>
  )
}

function ComBracos({
  divisao,
  cartao,
}: {
  divisao: NonNullable<GrupoDeCurso['divisao']>
  cartao: (r: ReguaComCota) => ReactElement | null
}) {
  const reencontro = divisao.reencontro.map((r) => r.id)
  return (
    <>
      {divisao.antes.map(cartao)}
      {divisao.antes.length > 0 ? (
        <p className={estilos.nota}>Daqui para baixo o rio se divide em dois braços paralelos:</p>
      ) : null}
      {divisao.bracos.map((b) => (
        <div key={b.chave} className={estilos.braco}>
          <p className={estilos.nomeBraco}>{b.nome}</p>
          {b.reguas.map(cartao)}
        </div>
      ))}
      {reencontro.length > 1 ? (
        <p className={estilos.nota}>
          {reencontro.join(' e ')} ficam no ponto onde os dois braços se reúnem, perto da foz — não há
          ordem entre elas.
        </p>
      ) : null}
    </>
  )
}

/** Uma régua, como o cartão "Agora" da cidade, em miniatura. */
function CartaoRegua({ x, cidade }: { x: ReguaAgora; cidade: Cidade }) {
  const { regua, leitura, faixa, idade, velha, proxima } = x
  const estadoIdade = idade === null ? 'velha' : frescorDaCidade(idade, cidade.id)
  return (
    <article className={estilos.regua} aria-label={regua.nome}>
      <div className={estilos.topo}>
        <h4 className={estilos.nome}>{regua.nome}</h4>
        <ChipFaixa faixa={faixa} cidade={cidade} compacto />
      </div>
      {leitura ? (
        <p className={estilos.linhaNumero}>
          <span className={`${estilos.numero} ${velha ? estilos.numeroVelho : ''}`}>{numero(leitura.nivel_m)}</span>
          <span className={estilos.unidade}>m</span>
          <span className={estilos.medido}>
            <span className={`${estilos.frescor} ${estilos[`frescor_${estadoIdade}`] ?? ''}`} aria-hidden="true" />
            {idade === null ? 'sem horário de medição' : `medido ${textoIdade(idade)}`}
          </span>
        </p>
      ) : (
        <p className={estilos.semLeitura}>
          Sem leitura ao vivo desta régua — não quer dizer que o rio esteja baixo.
        </p>
      )}
      {leitura && velha ? <p className={estilos.alerta}>Leitura antiga — não use como nível atual.</p> : null}
      <MedidorCotas
        cidade={cidade}
        cotas={Object.fromEntries(regua.cotas)}
        nivel={leitura && !velha ? leitura.nivel_m : null}
        rotulo={`Régua ${regua.nome}`}
      />
      {proxima ? (
        <p className={estilos.falta}>
          Faltam <strong>{distancia(proxima.faltam)}</strong> para a cota de {rotuloCota(proxima.chave)} desta
          régua ({metros(proxima.valor)}).
        </p>
      ) : null}
      {!regua.alertaAutomatico && regua.senteMare ? (
        <p className={estilos.mare} title={regua.motivoSemAlerta ?? undefined}>
          <span className={estilos.selo}>maré</span> sobe e desce com a maré — não dispara aviso sozinha
        </p>
      ) : !regua.alertaAutomatico ? (
        <p className={estilos.mare} title={regua.motivoSemAlerta ?? undefined}>
          <span className={estilos.selo}>sem aviso</span> não sente a maré; a cota desta régua ainda está em
          conferência, por isso não dispara aviso sozinha
        </p>
      ) : null}
    </article>
  )
}
