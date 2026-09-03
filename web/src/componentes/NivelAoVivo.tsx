import type { Cidade } from '../dados/tipos'
import type { LeituraAoVivo } from '../dados/tempoReal'
import type { Tendencia } from '../dados/serie'
import { metros, rotuloCota } from '../logica/formato'
import { cotaAlcancada, frescor, idadeMin, textoIdade } from '../logica/tempoReal'
import estilos from './NivelAoVivo.module.css'

/**
 * O nível agora, com a idade da leitura sempre à vista.
 *
 * A idade não é detalhe: numa cheia o rio sobe metros em horas, e um número de
 * quatro horas atrás exibido como "nível atual" faz alguém decidir errado. Aqui
 * ela vem junto do número, e quando a leitura passa do limite a tela diz, em
 * letras, que aquilo não serve como nível atual.
 *
 * A idade sozinha, porém, não conta a história toda. Blumenau publica de três em
 * três horas (conferido: é a cadência da estação, não atraso da nossa coleta), e
 * "5,11 m há 3 h" com o rio SUBINDO significa que o rio está mais alto agora —
 * enquanto o mesmo número com o rio parado provavelmente ainda vale. A tela
 * mostrava os dois igual. Por isso `tendencia`: quando a leitura está atrasada e
 * a série vinha subindo, a tela diz para onde ela ia, sem inventar o nível de
 * agora (que ninguém mediu).
 */
export default function NivelAoVivo({
  leitura,
  cidade,
  agora,
  tendencia,
}: {
  leitura: LeituraAoVivo
  cidade: Cidade
  agora: Date
  /** Para onde o nível ia na última hora medida. Ausente sem série publicada. */
  tendencia?: Tendencia | null
}) {
  if (!leitura.medidoEm) {
    return (
      <span className={estilos.semHorario}>
        {metros(leitura.nivel_m)} — a fonte não publicou o horário desta medição, então não dá
        para saber se é recente
      </span>
    )
  }

  const idade = idadeMin(leitura.medidoEm, agora)
  const estado = frescor(idade)
  // A cota mais alta já passada, não a primeira da lista: com o rio dois
  // patamares acima, anunciar "atenção" é a frase mais fraca possível na hora
  // em que se precisa da mais forte.
  const cota = cotaAlcancada(cidade, leitura.nivel_m)
  const acimaDaCota = cota !== null

  const classe =
    estado === 'velha' ? estilos.velha : acimaDaCota ? estilos.acima : estilos.normal

  // Só avisa quando a combinação muda a leitura do número: a medição não é do
  // agora E o rio vinha subindo. Com a leitura fresca, o número já é o estado
  // atual; com o rio descendo ou parado, o número velho erra para o lado
  // seguro. Subindo, ele erra para baixo — que é o lado que machuca.
  const subiaQuandoMediu = estado !== 'agora' && tendencia?.rotulo === 'subindo'

  return (
    <span className={`${estilos.selo} ${classe}`}>
      <span className={estilos.numero}>{metros(leitura.nivel_m)}</span>
      <span className={estilos.idade}>
        {estado === 'agora' ? '' : estado === 'atrasada' ? 'medido ' : 'última leitura '}
        {textoIdade(idade)}
      </span>
      {estado === 'velha' ? (
        <span className={estilos.aviso}>não use como nível atual</span>
      ) : acimaDaCota && cota ? (
        <span className={estilos.aviso}>acima da cota de {rotuloCota(cota.chave)}</span>
      ) : null}
      {subiaQuandoMediu ? (
        <span className={estilos.subindo}>
          e <strong>subindo</strong>
          {tendencia && tendencia.cmh !== 0 ? ` ${Math.abs(tendencia.cmh)} cm/h` : ''} quando mediu —
          o rio deve estar mais alto agora
        </span>
      ) : null}
    </span>
  )
}
