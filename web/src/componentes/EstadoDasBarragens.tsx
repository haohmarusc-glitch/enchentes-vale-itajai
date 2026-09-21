import type { Barragem } from '../dados/barragens'
import type { Tendencia } from '../dados/serie'
import { estadoDeEsvaziamento } from '../logica/esvaziamento'
import { frescor, idadeMin, textoIdade } from '../logica/tempoReal'
import estilos from './EstadoDasBarragens.module.css'

/**
 * O que a barragem acima está fazendo com a água: segurando ou soltando.
 *
 * O mesmo nível a jusante significa coisas opostas nos dois casos, e até aqui
 * o site mostrava só o número. Em 05/09/2026 Rio do Sul ficou dias em 5,4 m
 * enquanto o sistema esvaziava com as doze comportas abertas — quem olhasse a
 * tela via um rio alto e parado, sem nada que explicasse por quê.
 *
 * ⚠️ O QUE ESTE COMPONENTE NÃO DIZ, DE PROPÓSITO
 *
 * * **Não dá veredito sobre a cheia.** "O pico já passou" depende da tendência
 *   do rio, não da comporta. Aqui o texto afirma só o que o estado da comporta
 *   sustenta sozinho: aberta = soltando, fechada = segurando. Quem mostra a
 *   tendência é a linha do tempo, na mesma tela, e é o morador que junta as
 *   duas — como faria com o boletim da Defesa Civil.
 * * **Não mostra o nível da barragem em metros.** A régua dela tem zero próprio
 *   (339 m de altitude na Oeste). Pôr "14,66 m" ao lado dos "5,24 m" do rio
 *   convidaria a comparação que é o erro central do projeto.
 *
 * * **Não tira a cor do nível.** Decisão do Jefferson (21/09/2026): com
 *   comportas abertas e o rio parado ou baixando, o bloco acrescenta o estado
 *   "esvaziando" — e a cor do nível continua a do nível, porque retirá-la
 *   poderia transmitir segurança antes de a água baixar. Com o rio subindo, o
 *   estado é "vertendo com o rio subindo". Ver `logica/esvaziamento.ts`.
 *
 * Isto não é aviso oficial. Quem decide evacuação é a Defesa Civil (199).
 */
export default function EstadoDasBarragens({
  barragens,
  agora,
  tendencia = null,
}: {
  barragens: Barragem[]
  agora: Date
  /** Tendência do rio a jusante (de UMA régua); null quando não se sabe. */
  tendencia?: Tendencia | null
}) {
  if (barragens.length === 0) return null

  return (
    <div className={estilos.bloco}>
      <span className={estilos.titulo}>
        {barragens.length > 1 ? 'Barragens acima' : 'Barragem acima'}
      </span>

      {barragens.map((b) => {
        const todasAbertas = b.abertas === b.total
        const todasFechadas = b.abertas === 0
        const idade = b.medidoEm ? idadeMin(b.medidoEm, agora) : null
        const estado = idade === null ? 'velha' : frescor(idade)
        const esvaziamento = estado === 'velha' ? null : estadoDeEsvaziamento(b.abertas, b.total, tendencia)

        return (
          <div key={b.nome} className={estilos.barragem}>
            <div className={estilos.linhaTopo}>
              <span className={estilos.nome}>{b.nome}</span>
              <span className={`${estilos.idade} ${estilos[estado] ?? ''}`}>
                {idade === null ? 'sem horário' : textoIdade(idade)}
              </span>
            </div>

            <div className={estilos.comportas}>
              <strong className={todasFechadas ? estilos.segurando : estilos.soltando}>
                {b.abertas} de {b.total} comportas abertas
              </strong>
              <span className={estilos.oQueSignifica}>
                {todasFechadas
                  ? '— a barragem está segurando água'
                  : todasAbertas
                    ? '— a barragem está soltando água'
                    : '— a barragem está soltando água por parte das comportas'}
              </span>
            </div>

            {esvaziamento ? (
              <span
                className={`${estilos.esvaziamento} ${
                  esvaziamento.rotulo === 'esvaziando' ? estilos.esvaziando : estilos.vertendo
                }`}
              >
                <strong>{esvaziamento.rotulo}</strong> — {esvaziamento.frase}
              </span>
            ) : null}

            {b.fechadas.length > 0 && b.fechadas.length < b.total ? (
              <span className={estilos.quais}>fechadas: {b.fechadas.join(', ')}</span>
            ) : null}

            {b.percentUso !== null ? (
              <span className={estilos.capacidade}>
                reservatório em <strong>{b.percentUso.toFixed(0)}%</strong> da capacidade
              </span>
            ) : null}
          </div>
        )
      })}

      {/* A ressalva fica no bloco, não em rodapé: quem lê "soltando água"
          precisa saber, na mesma olhada, que isto não diz se a cheia passou. */}
      <span className={estilos.ressalva}>
        Isto diz o que a barragem está fazendo — <strong>não</strong> se a cheia passou. Para
        saber se o rio sobe ou desce, veja o nível e a linha do tempo desta cidade. Aviso
        oficial é da Defesa Civil: <strong>199</strong>.
      </span>
    </div>
  )
}
