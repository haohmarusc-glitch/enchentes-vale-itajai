import { Fragment, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { Cidade, Topologia } from '../dados/tipos'
import { trechos } from '../dados/carregar'
import { estadoDaCidade, type AoVivo } from '../dados/usarAoVivo'
import { tendenciaDaLeitura, textoTendencia } from '../logica/agora'
import { metros, numero } from '../logica/formato'
import { frescorDaCidade, idadeMin, textoIdade } from '../logica/tempoReal'
import { caminho, faixaHoras } from '../logica/transito'
import { ChipFaixa } from './CartaoAgora'
import { rioDaUrl } from './CartoesDaCidade'
import estilos from './ListaRio.module.css'
import { situacaoDaLinha } from '../logica/linhaDaCidade'

/**
 * O RIO COMO LISTA COMPACTA (versão 2, 03/10/2026) — uma linha por cidade:
 * faixa, número, tendência e idade. O detalhe de cada uma está a um toque, na
 * página dela. A tela do Açu caía de ~25 mil px no celular para uma lista.
 *
 * A ordem respeita a árvore (`docs/TOPOLOGIA-CANONICA.md`): cabeceiras
 * paralelas, tronco e afluentes laterais em grupos separados, e o tempo de
 * descida aparece SÓ entre cidades do tronco — cabeceira e afluente não são
 * elos da fila, e encadear tempo por elas afirmaria um caminho de água que não
 * existe.
 */
/** Para onde vai o toque numa cidade. Padrão: a página da cidade; o Monitor manda para o mapa dele. */
export type DestinoDaCidade = (cidade: Cidade, rioId: string) => string

const paginaDaCidade: DestinoDaCidade = (cidade, rioId) =>
  cidade.id === 'itajai' ? '/itajai' : `/${rioDaUrl(rioId)}/${cidade.id}`

export default function ListaRio({
  rioId,
  cidades,
  topologia,
  aoVivo,
  destino = paginaDaCidade,
}: {
  rioId: string
  cidades: Cidade[]
  topologia?: Topologia
  aoVivo: AoVivo
  destino?: DestinoDaCidade
}) {
  const porId = new Map(cidades.map((c) => [c.id, c]))
  const pegar = (ids: string[]) => ids.map((id) => porId.get(id)).filter((c): c is Cidade => Boolean(c))

  if (!topologia) {
    return (
      <Grupo titulo="A água desce nesta ordem">
        <Fila cidades={cidades} rioId={rioId} aoVivo={aoVivo} destino={destino} comTempo />
      </Grupo>
    )
  }

  const cabeceiras = pegar(topologia.cabeceiras_paralelas)
  const tronco = pegar(topologia.tronco_sequencia)
  const afluentes = pegar(topologia.afluentes_laterais.map((a) => a.id))
  const mostradas = new Set([...cabeceiras, ...tronco, ...afluentes].map((c) => c.id))
  // Rede de segurança: cidade fora da árvore não some da tela em silêncio.
  const resto = cidades.filter((c) => !mostradas.has(c.id))
  return (
    <>
      {cabeceiras.length > 0 ? (
        <Grupo titulo="Cabeceiras — correm em paralelo" nota={`Juntam-se em ${tronco[0]?.nome ?? 'Rio do Sul'}, onde nasce o Itajaí-Açu.`}>
          <Fila cidades={cabeceiras} rioId={rioId} aoVivo={aoVivo} destino={destino} />
        </Grupo>
      ) : null}
      <Grupo titulo="Tronco — a água desce nesta ordem">
        <Fila cidades={tronco} rioId={rioId} aoVivo={aoVivo} destino={destino} comTempo />
      </Grupo>
      {afluentes.length > 0 ? (
        <Grupo titulo="Afluentes laterais" nota="Entram no tronco de lado — não são elos da fila.">
          <Fila cidades={afluentes} rioId={rioId} aoVivo={aoVivo} destino={destino} />
        </Grupo>
      ) : null}
      {resto.length > 0 ? (
        <Grupo titulo="Outros pontos" nota="Ainda sem posição definida na árvore do rio.">
          <Fila cidades={resto} rioId={rioId} aoVivo={aoVivo} destino={destino} />
        </Grupo>
      ) : null}
    </>
  )
}

function Grupo({ titulo, nota, children }: { titulo: string; nota?: string; children: ReactNode }) {
  return (
    <section className={estilos.grupo}>
      <h2 className={estilos.tituloGrupo}>{titulo}</h2>
      {nota ? <p className={estilos.nota}>{nota}</p> : null}
      {children}
    </section>
  )
}

function Fila({
  cidades,
  rioId,
  aoVivo,
  destino,
  comTempo = false,
}: {
  cidades: Cidade[]
  rioId: string
  aoVivo: AoVivo
  destino: DestinoDaCidade
  comTempo?: boolean
}) {
  return (
    <ol className={estilos.fila}>
      {cidades.map((c, i) => {
        const proxima = cidades[i + 1]
        const trecho = comTempo && proxima ? caminho(trechos, rioId, c.id, proxima.id) : null
        return (
          <Fragment key={c.id}>
            <li>
              <Linha cidade={c} rioId={rioId} aoVivo={aoVivo} destino={destino} />
            </li>
            {trecho && proxima ? (
              <li className={estilos.tempo} aria-label={`a cheia leva ${faixaHoras(trecho)} até ${proxima.nome}`}>
                <span aria-hidden="true">↓</span> {faixaHoras(trecho)} até {proxima.nome}
              </li>
            ) : null}
          </Fragment>
        )
      })}
    </ol>
  )
}

function Linha({ cidade, rioId, aoVivo, destino }: { cidade: Cidade; rioId: string; aoVivo: AoVivo; destino: DestinoDaCidade }) {
  const estado = estadoDaCidade(cidade, rioId, aoVivo)
  const { leitura, faixa } = estado
  const idade = leitura?.medidoEm ? idadeMin(leitura.medidoEm, aoVivo.agora) : null
  const valida = leitura && idade !== null && frescorDaCidade(idade, cidade.id) !== 'velha'
  const seta = valida ? tendenciaDaLeitura(estado.serie, leitura, aoVivo.agora) : null
  // Auditoria de 03/10/2026, item 5: leitura estadual sem faixa não é "sem leitura".
  const linha = situacaoDaLinha(estado, cidade.id, aoVivo.agora)
  const para = destino(cidade, rioId)
  return (
    <Link to={para} className={estilos.linha}>
      <span className={`${estilos.marcador} ${estilos[`m_${faixa}`] ?? ''}`} aria-hidden="true" />
      <span className={estilos.corpo}>
        <span className={estilos.nome}>{cidade.nome}</span>
        <span className={estilos.sub}>
          {valida ? (
            <>
              {seta && seta.rotulo !== 'estável' ? (
                <>
                  <span aria-hidden="true">{seta.rotulo === 'subindo' ? '▴' : '▾'}</span> {textoTendencia(seta)} ·{' '}
                </>
              ) : null}
              {textoIdade(idade!)}
            </>
          ) : estado.varias ? (
            <>{estado.todas.length} réguas, uma por uma</>
          ) : linha.tipo === 'estadual' ? (
            <>
              rede estadual (zero próprio): {metros(linha.nivel)}
              {linha.comFaixa ? '' : ' · sem faixa publicada'} · {textoIdade(linha.idade)}
            </>
          ) : (
            <>sem leitura recente</>
          )}
        </span>
      </span>
      {/* Sem leitura, o marcador tracejado e o "sem leitura recente" já dizem
          tudo; o chip repetiria a frase em cada linha. Com leitura e sem cota,
          o chip fica — é ele que diz "sem cota". */}
      {valida || estado.varias || faixa !== 'sem-dado' ? (
        <ChipFaixa faixa={faixa} cidade={cidade} compacto />
      ) : estado.faixaEstadual ? (
        <ChipFaixa faixa={estado.faixaEstadual} cidade={cidade} compacto estadual />
      ) : null}
      <span className={estilos.valor}>
        {valida ? (
          <>
            {numero(leitura!.nivel_m)}
            <small> m</small>
          </>
        ) : (
          <span aria-label="sem número">—</span>
        )}
      </span>
    </Link>
  )
}
