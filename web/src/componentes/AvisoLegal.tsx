import estilos from './AvisoLegal.module.css'

/**
 * Aviso obrigatório em toda tela (CLAUDE.md). O público não é técnico: o texto
 * precisa dizer, sem rodeio, o que o site é e o que ele não é.
 */
export default function AvisoLegal() {
  return (
    <section className={estilos.aviso} aria-labelledby="aviso-titulo">
      <h2 id="aviso-titulo" className={estilos.titulo}>
        Leia antes de usar
      </h2>
      <ul className={estilos.lista}>
        <li>
          Este site mostra <strong>dados históricos</strong> e estimativas empíricas. Ele{' '}
          <strong>não substitui</strong> o{' '}
          <a href="https://alertablu.blumenau.sc.gov.br/" target="_blank" rel="noreferrer">
            AlertaBlu
          </a>
          , a{' '}
          <a href="https://monitoramento.defesacivil.sc.gov.br/" target="_blank" rel="noreferrer">
            Defesa Civil de SC
          </a>{' '}
          nem a Defesa Civil do seu município.
        </li>
        <li>
          <strong>Cada cidade tem sua própria régua</strong>, com zero em altura diferente. 8 m em
          Blumenau e 8 m em Brusque não significam a mesma coisa. Nunca compare os metros de uma
          cidade com os de outra.
        </li>
        <li>
          Tempos de chegada da cheia são <strong>faixas estimadas</strong>, não horários.
          Chuva forte a jusante, maré alta e barragens mudam tudo.
        </li>
        <li>
          Em emergência, <strong>ligue 199</strong>. Não espere a confirmação de nenhum número desta
          tela para sair de área de risco.
        </li>
      </ul>
    </section>
  )
}
