import type { Cidade } from '../dados/tipos'
import type { LeituraAoVivo } from '../dados/tempoReal'
import type { ReguaComCota } from '../logica/reguas'
import { metros, rotuloCota } from '../logica/formato'
import { frescor, idadeMin, textoIdade } from '../logica/tempoReal'
import { parear } from '../logica/variasReguas'
import estilos from './VariasReguas.module.css'

/**
 * O nível de uma cidade que tem VÁRIAS réguas — todas, sem eleger nenhuma.
 *
 * Itajaí tem onze, com zeros diferentes. A tela sempre se recusou a dizer "o
 * nível de Itajaí", o que é certo: esse número não existe. Mas a consequência
 * era a cidade da foz, que recebe os dois rios, aparecer sem número nenhum
 * enquanto o dado estava ali.
 *
 * Aqui elas saem lado a lado, cada uma com o nome e com a cota DELA. O aviso de
 * que não se comparam vem junto, no mesmo bloco — não em rodapé, porque quem
 * olha os números precisa ler isso antes de somá-los na cabeça.
 */
export default function VariasReguas({
  leituras,
  reguas,
  cidade,
  agora,
}: {
  leituras: LeituraAoVivo[]
  reguas: ReguaComCota[]
  cidade: Cidade
  agora: Date
}) {
  if (leituras.length === 0) return null
  const pareadas = parear(leituras, reguas)

  return (
    <span className={estilos.bloco}>
      <span className={estilos.aviso}>
        {cidade.nome} tem {leituras.length} réguas, com zeros diferentes:{' '}
        <strong>estes números não se comparam entre si</strong>.
      </span>

      <span className={estilos.lista}>
        {pareadas.map(({ leitura, regua, cota, proxima }) => {
          const idade = leitura.medidoEm ? idadeMin(leitura.medidoEm, agora) : null
          const estado = idade === null ? 'velha' : frescor(idade)
          return (
            <span key={leitura.estacao} className={estilos.linha}>
              <span className={`${estilos.nivel} ${cota ? estilos.acima : ''}`}>
                {metros(leitura.nivel_m)}
              </span>
              <span className={estilos.nome}>{regua?.nome ?? leitura.estacao}</span>
              {regua?.nomeNoPlano ? (
                <span className={estilos.noPlano}>
                  no Plano de Contingência: {regua.nomeNoPlano}
                </span>
              ) : null}
              <span className={`${estilos.idade} ${estilos[estado] ?? ''}`}>
                {idade === null ? 'sem horário' : textoIdade(idade)}
              </span>
              {/* A cota aparece SEMPRE que a régua tem uma — atingida ou não.
                  Antes só a atingida era mostrada, e régua abaixo de tudo
                  ficava sem linha nenhuma, indistinguível de régua sem cota
                  cadastrada. Era o caso da DC-11: 2,63 m com atenção em 3,00 m
                  aparecia vazia, quando o que faltavam eram 37 cm. É essa
                  distância que decide, e ela tem que estar escrita. */}
              {cota ? (
                <span className={estilos.cota}>
                  {rotuloCota(cota.chave)} desta régua: {metros(cota.valor)}
                </span>
              ) : proxima ? (
                <span className={estilos.abaixo}>
                  {rotuloCota(proxima.chave)} desta régua: {metros(proxima.valor)} · faltam{' '}
                  {metros(proxima.valor - leitura.nivel_m)}
                </span>
              ) : null}
              {regua && !regua.alertaAutomatico ? (
                <span className={estilos.semAlerta} title={regua.motivoSemAlerta ?? undefined}>
                  sobe e desce com a maré — não dispara aviso sozinha
                </span>
              ) : null}
            </span>
          )
        })}
      </span>
    </span>
  )
}
