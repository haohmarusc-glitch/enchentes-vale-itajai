import type { Cidade } from '../dados/tipos'
import { useCidadesSeguidas, useLetra } from '../dados/usarPreferencias'
import estilos from './BotoesPreferencia.module.css'

/**
 * "★ Minha cidade": a página abre por esta cidade no Início deste aparelho.
 * Tocar de novo desfaz. Nada sai do aparelho — é `localStorage`, e sem ele o
 * botão funciona só nesta visita.
 */
export function BotaoMinhaCidade({ cidade, rio }: { cidade: Cidade; rio: 'acu' | 'mirim' }) {
  const { cidades, tornarMinha, deixarDeSeguir } = useCidadesSeguidas()
  const ehMinha = cidades[0]?.id === cidade.id
  return (
    <button
      type="button"
      className={`${estilos.botao} ${ehMinha ? estilos.ligado : ''}`}
      aria-pressed={ehMinha}
      onClick={() => (ehMinha ? deixarDeSeguir(cidade.id) : tornarMinha({ id: cidade.id, rio }))}
    >
      <span aria-hidden="true">{ehMinha ? '★' : '☆'}</span> Minha cidade
    </button>
  )
}

/** "A A": letra maior em todo o site, lembrada neste aparelho. */
export function BotaoLetra() {
  const [letra, trocar] = useLetra()
  const grande = letra === 'grande'
  return (
    <button
      type="button"
      className={`${estilos.botao} ${estilos.letra} ${grande ? estilos.ligado : ''}`}
      aria-pressed={grande}
      aria-label={grande ? 'Voltar a letra ao tamanho normal' : 'Aumentar a letra'}
      title={grande ? 'Letra normal' : 'Letra maior'}
      onClick={() => trocar(grande ? 'normal' : 'grande')}
    >
      <span className={estilos.aPequeno} aria-hidden="true">A</span>
      <span className={estilos.aGrande} aria-hidden="true">A</span>
    </button>
  )
}
