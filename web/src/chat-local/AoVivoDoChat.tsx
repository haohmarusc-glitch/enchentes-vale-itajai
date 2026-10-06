import { useEffect } from 'react'
import { useAoVivo, type AoVivo } from '../dados/usarAoVivo'

/**
 * O nível e a chuva de agora para "como está Blumenau?", montado SÓ quando a pessoa toca no chat compacto:
 * a barra do topo está em toda página, e não deve pedir leituras ao vivo sem ninguém perguntar nada.
 *
 * `useAoVivo` devolve um objeto NOVO a cada desenho. Depender dele no efeito fazia um laço (efeito → estado
 * → desenho → objeto novo → efeito), e esse laço de prioridade alta nunca deixava a navegação terminar: o
 * endereço mudava para o Monitor e a tela continuava no Início (06/10/2026). Por isso as dependências são
 * as peças, que só mudam quando o dado muda.
 */
export default function AoVivoDoChat({ aoMudar }: { aoMudar: (a: AoVivo) => void }) {
  const { tempoReal, nivelSc, serie, agora } = useAoVivo()
  useEffect(() => aoMudar({ tempoReal, nivelSc, serie, agora }), [tempoReal, nivelSc, serie, agora, aoMudar])
  return null
}
