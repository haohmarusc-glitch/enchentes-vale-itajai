import type { ReguaComCota } from '../logica/reguas'
import { agruparPorCurso } from '../logica/reguas'
import { metros, rotuloCota } from '../logica/formato'
import estilos from './ReguasDaCidade.module.css'

/**
 * As cotas de uma cidade que tem mais de uma régua — ou cuja régua não é a
 * "régua da cidade".
 *
 * Três regras aqui, todas para o mesmo fim de não enganar:
 *
 * 1. Cada régua aparece com nome. Sem nome, onze conjuntos de cota viram um
 *    borrão de números e alguém compara o 1,16 m do estuário com o 8,00 m de
 *    Limoeiro como se fossem a mesma água.
 * 2. A régua que não serve para aviso automático diz isso, com o motivo da
 *    fonte. É a régua de maré: ela cruza a cota de atenção num dia de sol.
 * 3. Nada é somado, convertido ou eleito como o nível da cidade.
 *
 * `agrupadoPorCurso` acrescenta a quarta: em Itajaí, foz de dois rios com dois
 * ribeirões, as réguas saem sob o SEU curso e na ordem da descida (montante →
 * foz), como no `/rios` do bot — não numa lista plana onde a de Limoeiro, 26 km
 * rio acima, encosta na do estuário. As co-locadas (DC-04 × DC-06, braços
 * paralelos) ficam lado a lado, sem fila, porque a fonte não distingue qual vem
 * antes.
 *
 * Tudo é `<span>` porque o item da cidade no diagrama é um `<button>`, que só
 * aceita conteúdo de frase — uma `<ul>` aqui dentro é HTML inválido.
 */
export default function ReguasDaCidade({
  reguas,
  cidade,
  /** A tela de Itajaí já tem o título em `<h2>`; aqui ele seria repetição. */
  comTitulo = true,
  /** Agrupa por curso e ordena pela descida do rio (só faz sentido na foz). */
  agrupadoPorCurso = false,
}: {
  reguas: ReguaComCota[]
  cidade: string
  comTitulo?: boolean
  agrupadoPorCurso?: boolean
}) {
  if (reguas.length === 0) return null

  const comMare = reguas.filter((r) => !r.alertaAutomatico)
  // Só agrupa quando há mais de um curso; com um curso só, um subtítulo único
  // seria ruído.
  const grupos = agrupadoPorCurso ? agruparPorCurso(reguas) : null
  const mostrarGrupos = grupos != null && grupos.length > 1

  return (
    <span className={estilos.bloco}>
      {comTitulo ? (
        <span className={estilos.titulo}>
          {reguas.length === 1
            ? 'Cota oficial da régua de '
            : `Cotas oficiais das ${reguas.length} réguas de `}
          {cidade}
        </span>
      ) : null}
      <span className={estilos.aviso}>
        Cada régua tem seu próprio zero: os metros de uma não se comparam com os de outra.
      </span>

      {mostrarGrupos ? (
        grupos!.map((g) => (
          <span key={g.rio} className={estilos.grupo}>
            <span className={estilos.curso}>{g.nome}, da nascente para o mar</span>
            <ListaDeReguas reguas={g.reguas} destacarPar />
          </span>
        ))
      ) : (
        <ListaDeReguas reguas={reguas} destacarPar={false} />
      )}

      {comMare.length > 0 ? (
        <span className={estilos.explicacao}>
          {comMare.length === reguas.length
            ? 'Estas réguas ficam no estuário'
            : `${comMare.length} destas réguas ficam no estuário`}
          : a maré as faz passar da cota de atenção em dia sem chuva, e baixar meio metro em três
          horas. A cota está aqui porque é a oficial, mas cruzá-la não significa, sozinha, que há
          cheia chegando.
        </span>
      ) : null}
    </span>
  )
}

/**
 * A lista de réguas de um bloco. Quando `destacarPar`, as que compartilham a
 * mesma `ordemDescida` (co-locadas em braços paralelos) saem juntas, com a
 * ressalva de que não há ordem entre elas — nunca em fila, que sugeriria uma
 * ordem que a fonte não tem.
 */
function ListaDeReguas({
  reguas,
  destacarPar,
}: {
  reguas: ReguaComCota[]
  destacarPar: boolean
}) {
  const blocos = destacarPar ? emParesColocados(reguas) : reguas.map((r) => [r])
  return (
    <span className={estilos.lista}>
      {blocos.map((bloco) =>
        bloco.length > 1 ? (
          <span key={bloco[0]!.id} className={estilos.par}>
            <span className={estilos.parNota}>
              {bloco[0]!.ordemNota ??
                'Lado a lado, em braços paralelos: a fonte não distingue qual vem antes.'}
            </span>
            {bloco.map((r) => (
              <Regua key={r.id} regua={r} />
            ))}
          </span>
        ) : (
          <Regua key={bloco[0]!.id} regua={bloco[0]!} />
        ),
      )}
    </span>
  )
}

/** Uma régua: nome, cotas e a ressalva de maré quando não serve para aviso. */
function Regua({ regua }: { regua: ReguaComCota }) {
  return (
    <span className={estilos.regua}>
      <span className={estilos.nome}>{regua.nome}</span>
      <span className={estilos.cotas}>
        {regua.cotas.map(([chave, valor]) => (
          <span key={chave} className={estilos.cota}>
            {rotuloCota(chave)}: <strong>{metros(valor)}</strong>
          </span>
        ))}
      </span>
      {!regua.alertaAutomatico ? (
        <span className={estilos.mare}>sobe e desce com a maré — ver abaixo</span>
      ) : null}
    </span>
  )
}

/**
 * Junta réguas consecutivas que têm a MESMA `ordemDescida` (> 1 régua) num só
 * bloco — as co-locadas. As demais saem sozinhas. Preserva a ordem de entrada,
 * que já vem da descida do rio.
 */
function emParesColocados(reguas: ReguaComCota[]): ReguaComCota[][] {
  const blocos: ReguaComCota[][] = []
  for (const r of reguas) {
    const ultimo = blocos[blocos.length - 1]
    if (
      ultimo &&
      r.ordemDescida != null &&
      ultimo[0]!.ordemDescida === r.ordemDescida
    ) {
      ultimo.push(r)
    } else {
      blocos.push([r])
    }
  }
  return blocos
}
