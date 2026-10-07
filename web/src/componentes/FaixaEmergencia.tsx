import estilos from './FaixaEmergencia.module.css'

/**
 * Sempre visível, em todas as telas. Se alguém abrir o site em pânico e ler uma
 * coisa só, que seja esta: o número da Defesa Civil.
 */
export default function FaixaEmergencia() {
  return (
    <div className={estilos.faixa} role="note">
      {/* Dois textos, um só visível: o completo no computador; no celular, uma linha (redesenho do
          Monitor, 07/10/2026). Os dois dizem o mesmo: 199, 193 e "não é alerta oficial". */}
      <span className={estilos.completo}>
        <strong>Emergência: ligue 199</strong> (Defesa Civil) ou 193 (Bombeiros). Este site{' '}
        <strong>não é</strong> sistema oficial de alerta.
      </span>
      <span className={estilos.compacto}>
        <strong>Defesa Civil: 199</strong> · <strong>Bombeiros: 193</strong> · Não é alerta oficial
      </span>
    </div>
  )
}
