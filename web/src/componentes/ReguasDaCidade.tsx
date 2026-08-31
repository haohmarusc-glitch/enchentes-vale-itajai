import type { ReguaComCota } from '../logica/reguas'
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
 * Tudo é `<span>` porque o item da cidade no diagrama é um `<button>`, que só
 * aceita conteúdo de frase — uma `<ul>` aqui dentro é HTML inválido.
 */
export default function ReguasDaCidade({
  reguas,
  cidade,
  /** A tela de Itajaí já tem o título em `<h2>`; aqui ele seria repetição. */
  comTitulo = true,
}: {
  reguas: ReguaComCota[]
  cidade: string
  comTitulo?: boolean
}) {
  if (reguas.length === 0) return null

  const comMare = reguas.filter((r) => !r.alertaAutomatico)

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

      <span className={estilos.lista}>
        {reguas.map((r) => (
          <span key={r.id} className={estilos.regua}>
            <span className={estilos.nome}>{r.nome}</span>
            <span className={estilos.cotas}>
              {r.cotas.map(([chave, valor]) => (
                <span key={chave} className={estilos.cota}>
                  {rotuloCota(chave)}: <strong>{metros(valor)}</strong>
                </span>
              ))}
            </span>
            {!r.alertaAutomatico ? (
              <span className={estilos.mare}>sobe e desce com a maré — ver abaixo</span>
            ) : null}
          </span>
        ))}
      </span>

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
