/**
 * O contexto do SGB para a "minha rua" (`data/sgb-ruas.json`), carregado à parte: são ~700 KB que só a busca de rua
 * usa, e só em cidade que o SGB cobre. Quem abre o site para ver o nível do rio não paga por isto.
 */
import { useEffect, useState } from 'react'
import type { CidadeSgb, SgbRuas } from '../logica/sgbRuas'

let promessa: Promise<SgbRuas | null> | null = null

export function carregarSgbRuas(): Promise<SgbRuas | null> {
  if (!promessa) {
    promessa = import('@dados/sgb-ruas.json')
      .then((m) => (m.default ?? m) as unknown as SgbRuas)
      .then((d) => (d && typeof d === 'object' && d.cidades && typeof d.cidades === 'object' ? d : null))
      .catch(() => null)
  }
  return promessa
}

/** "04/11/2026" a partir do `_meta.acesso.quando` (ISO, UTC); null quando o arquivo não diz. */
export function dataDoAcesso(quando: string | undefined | null): string | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(quando ?? '')
  return m ? `${m[3]}/${m[2]}/${m[1]}` : null
}

interface EstadoSgb {
  cidade: CidadeSgb | null
  /** Quando os GeoJSON foram lidos do geoportal (dd/mm/aaaa), para a tela dizer a data do dado. */
  lidoEm: string | null
  carregado: boolean
}

/** O bloco da cidade, ou null enquanto carrega, se falhar ou se o SGB não a cobre. `carregado` separa os três. */
export function useSgbDaCidade(cidadeId: string): EstadoSgb {
  const [estado, setEstado] = useState<EstadoSgb>({ cidade: null, lidoEm: null, carregado: false })
  useEffect(() => {
    let vivo = true
    setEstado({ cidade: null, lidoEm: null, carregado: false })
    void carregarSgbRuas().then((d) => {
      if (!vivo) return
      setEstado({ cidade: d?.cidades[cidadeId] ?? null, lidoEm: dataDoAcesso(d?._meta?.acesso?.quando), carregado: true })
    })
    return () => {
      vivo = false
    }
  }, [cidadeId])
  return estado
}
