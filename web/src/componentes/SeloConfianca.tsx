import type { Confianca } from '../dados/tipos'
import { ROTULO_CONFIANCA, ROTULO_CONFIANCA_TRECHO, type TipoConfianca } from '../logica/formato'
import estilos from './SeloConfianca.module.css'

// `noUncheckedIndexedAccess` faz o CSS Module devolver `string | undefined`.
const CLASSE: Record<Confianca, string | undefined> = {
  alta: estilos.alta,
  media: estilos.media,
  baixa: estilos.baixa,
}

const TEXTO: Record<Confianca, string> = {
  alta: 'confiança alta',
  media: 'confiança média',
  baixa: 'confiança baixa',
}

/** Todo número na tela carrega de onde veio. Dado sem procedência não é dado. */
export default function SeloConfianca({
  nivel,
  fonte,
  tipo = 'registro',
}: {
  nivel: Confianca
  fonte?: string
  /** O que está sendo qualificado: um registro histórico ou um trecho de tempo de descida. */
  tipo?: TipoConfianca
}) {
  const escala = tipo === 'trecho' ? ROTULO_CONFIANCA_TRECHO : ROTULO_CONFIANCA
  const titulo = fonte ? `${escala[nivel]} — ${fonte}` : escala[nivel]
  return (
    <span className={`${estilos.selo} ${CLASSE[nivel] ?? ''}`} title={titulo}>
      {TEXTO[nivel]}
    </span>
  )
}
