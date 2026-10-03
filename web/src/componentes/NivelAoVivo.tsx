import { faixaAscurra } from '../logica/municipal'
import type { Cidade } from '../dados/tipos'
import type { LeituraAoVivo } from '../dados/tempoReal'
import type { Tendencia } from '../dados/serie'
import { metros, rotuloCota } from '../logica/formato'
import { cotaAlcancada, frescorDaCidade, idadeMin, textoIdade, type Faixa } from '../logica/tempoReal'
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
  faixa,
}: {
  leitura: LeituraAoVivo
  cidade: Cidade
  agora: Date
  /**
   * A faixa da cidade AGORA, a mesma que pinta a bolinha e o selo ao lado.
   * Sem ela o selo ficava vermelho a partir de qualquer cota alcançada: Blumenau
   * a 3,72 m aparecia com a bolinha de monitoramento e o número em vermelho, e a
   * tela dizia duas coisas ao mesmo tempo.
   */
  faixa?: Faixa
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
  const estado = frescorDaCidade(idade, cidade.id)
  // A cota mais alta já passada, não a primeira da lista: com o rio dois
  // patamares acima, anunciar "atenção" é a frase mais fraca possível na hora
  // em que se precisa da mais forte.
  const cota = cotaAlcancada(cidade, leitura.nivel_m)
  const acimaDaCota = cota !== null
  const c18 = cidade.id === 'ascurra' ? faixaAscurra({cidade:'ascurra', codigo:leitura.codigo, estacao:leitura.estacao, nivelBrutoM:leitura.nivel_m, medidoEm:leitura.medidoEm}, agora) : null

  const classe =
    estado === 'velha'
      ? estilos.velha
      : faixa !== undefined
        ? classeDaFaixa(faixa, acimaDaCota)
        : acimaDaCota
          ? estilos.acima
          : estilos.normal

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
      ) : c18 ? (
        <span className={estilos.aviso}>{c18.nome} · enquadramento C18, DCSC-00003</span>
      ) : acimaDaCota && cota ? (
        <span className={estilos.aviso}>acima da cota de {rotuloCota(cota.chave, cidade.cotas_nomes_na_fonte)}</span>
      ) : null}
      {subiaQuandoMediu ? (
        <span className={estilos.subindo}>
          e <strong>subindo</strong>
          {tendencia && tendencia.cmh !== 0 ? ` ${Math.abs(tendencia.cmh)} cm/h` : ''} quando mediu
        </span>
      ) : null}
    </span>
  )
}

/**
 * Cor do selo = cor da faixa. Vermelho só em inundação e emergência; sem faixa
 * definida (cinza no mapa) o selo também não ganha cor de perigo, mas o texto
 * "acima da cota de …" continua, com o nome que a fonte deu.
 */
function classeDaFaixa(faixa: Faixa, acimaDaCota: boolean): string | undefined {
  switch (faixa) {
    case 'monitoramento':
      return estilos.monitoramento
    case 'atencao':
      return estilos.atencao
    case 'alerta':
      return estilos.alerta
    case 'inundacao':
    case 'emergencia':
      return estilos.acima
    case 'normal':
      return estilos.normal
    default:
      return acimaDaCota ? estilos.neutra : estilos.normal
  }
}
