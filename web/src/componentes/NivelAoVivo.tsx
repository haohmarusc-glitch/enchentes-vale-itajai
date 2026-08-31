import type { Cidade } from '../dados/tipos'
import type { LeituraAoVivo } from '../dados/tempoReal'
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
 */
export default function NivelAoVivo({
  leitura,
  cidade,
  agora,
}: {
  leitura: LeituraAoVivo
  cidade: Cidade
  agora: Date
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
    </span>
  )
}
