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
          Este site mostra <strong>medições observadas e referências históricas</strong>. Ele{' '}
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
          Camadas históricas são referências de eventos passados; não confirmam alagamento atual.
        </li>
        <li>
          Em emergência, <strong>ligue 199</strong>. Consulte os comunicados da Defesa Civil.
        </li>
      </ul>
    </section>
  )
}
