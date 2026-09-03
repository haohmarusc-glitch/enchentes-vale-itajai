import type { ReguaComCota, GrupoDeCurso } from '../logica/reguas'
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
  // O SUBTÍTULO do curso só aparece com mais de um curso — com um só, ele é
  // ruído. Mas a ORDEM (montante → foz), os braços paralelos e o par co-locado
  // valem sempre: é o que a tela de rio precisa, onde as réguas já vêm filtradas
  // por um curso só e antes saíam em fila achatada, sem ordem nenhuma.
  const grupos = agrupadoPorCurso ? agruparPorCurso(reguas) : null
  const mostrarNomeDoCurso = grupos != null && grupos.length > 1

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

      {grupos ? (
        grupos.map((g) => (
          <span key={g.rio} className={estilos.grupo}>
            {mostrarNomeDoCurso ? (
              <span className={estilos.curso}>{g.nome}, da nascente para o mar</span>
            ) : null}
            {g.divisao ? <CursoComBracos divisao={g.divisao} /> : <ListaDeReguas reguas={g.reguas} destacarPar />}
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
 * Um curso que se divide em braços paralelos (o Mirim em Itajaí): as réguas de
 * antes da bifurcação, depois cada braço sob o seu nome, e a ressalva de onde os
 * braços se reencontram. Assim curso antigo e canal não entram intercalados numa
 * fila — que faria o morador ler o nível de um braço achando que é do outro.
 */
function CursoComBracos({ divisao }: { divisao: NonNullable<GrupoDeCurso['divisao']> }) {
  const nomesReencontro = divisao.reencontro
    .map((r) => r.nome.split(' ')[0])
    .filter((n): n is string => !!n)
  return (
    <span className={estilos.lista}>
      {divisao.antes.map((r) => (
        <Regua key={r.id} regua={r} />
      ))}
      {divisao.antes.length > 0 ? (
        <span className={estilos.notaDivisao}>Daqui para baixo o rio se divide em dois braços paralelos:</span>
      ) : null}
      {divisao.bracos.map((b) => (
        <span key={b.chave} className={estilos.braco}>
          <span className={estilos.bracoNome}>{b.nome}</span>
          {b.reguas.map((r) => (
            <Regua key={r.id} regua={r} />
          ))}
        </span>
      ))}
      {nomesReencontro.length > 1 ? (
        <span className={estilos.reencontro}>
          {nomesReencontro.join(' e ')} ficam no mesmo ponto, onde os dois braços se reúnem perto da
          foz — não há ordem entre elas.
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
