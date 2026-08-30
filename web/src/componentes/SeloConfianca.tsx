import type { Confianca } from '../dados/tipos'
import { ROTULO_CONFIANCA } from '../logica/formato'
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
export default function SeloConfianca({ nivel, fonte }: { nivel: Confianca; fonte?: string }) {
  const titulo = fonte ? `${ROTULO_CONFIANCA[nivel]} — ${fonte}` : ROTULO_CONFIANCA[nivel]
  return (
    <span className={`${estilos.selo} ${CLASSE[nivel] ?? ''}`} title={titulo}>
      {TEXTO[nivel]}
    </span>
  )
}
