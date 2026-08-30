import estilos from './FaixaEmergencia.module.css'

/**
 * Sempre visível, em todas as telas. Se alguém abrir o site em pânico e ler uma
 * coisa só, que seja esta: o número da Defesa Civil.
 */
export default function FaixaEmergencia() {
  return (
    <div className={estilos.faixa} role="note">
      <strong>Emergência: ligue 199</strong> (Defesa Civil) ou 193 (Bombeiros). Este site{' '}
      <strong>não é</strong> sistema oficial de alerta.
    </div>
  )
}
