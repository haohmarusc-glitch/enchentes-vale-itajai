import { Component, type ErrorInfo, type ReactNode } from 'react'
import estilos from './LimiteDeErro.module.css'

interface Props {
  children: ReactNode
  /** Onde o erro aconteceu, para a mensagem dizer o que caiu. */
  oQue: string
}

interface Estado {
  erro: Error | null
}

/**
 * Impede que um componente quebrado leve o site inteiro junto.
 *
 * POR QUE ISTO É SEGURANÇA, E NÃO POLIMENTO. Sem limite de erro, o React
 * desmonta a árvore TODA quando qualquer componente lança — e a árvore toda
 * inclui a `FaixaEmergencia`, cujo comentário diz o que está em jogo: *"se
 * alguém abrir o site em pânico e ler uma coisa só, que seja esta: o número da
 * Defesa Civil"*. Um gráfico do recharts com dado inesperado, um canvas sem
 * contexto 2D, um JSON que mudou de forma — qualquer um deles apagava o 199 da
 * tela.
 *
 * Por isso o limite fica em volta do CONTEÚDO, nunca em volta da faixa. O que
 * cai é a tela que deu erro; o telefone da Defesa Civil continua lá.
 *
 * A mensagem não pede desculpa nem explica stack: diz o que deixou de
 * funcionar, que o resto do site continua valendo, e manda para a fonte
 * oficial. Quem está com o rio subindo não vai depurar nada.
 */
export default class LimiteDeErro extends Component<Props, Estado> {
  state: Estado = { erro: null }

  static getDerivedStateFromError(erro: Error): Estado {
    return { erro }
  }

  componentDidCatch(erro: Error, info: ErrorInfo) {
    // Sem serviço de telemetria neste projeto: o console é o que há, e é o que
    // o Jefferson consegue ler pedindo um print a quem reportou.
    console.error(`[${this.props.oQue}]`, erro, info.componentStack)
  }

  render() {
    if (!this.state.erro) return this.props.children
    return (
      <div className={estilos.caixa} role="alert">
        <h2 className={estilos.titulo}>Esta parte do site falhou</h2>
        <p>
          Não foi possível mostrar {this.props.oQue}. O problema é do site, não do seu aparelho —
          e o resto das telas continua funcionando.
        </p>
        <p className={estilos.oficial}>
          <strong>Se você precisa saber o nível do rio agora</strong>, use as fontes oficiais:{' '}
          <a href="https://alertablu.blumenau.sc.gov.br/" target="_blank" rel="noreferrer">
            AlertaBlu
          </a>
          ,{' '}
          <a href="https://defesacivil.itajai.sc.gov.br/monitoramento/nivel-rios" target="_blank" rel="noreferrer">
            Defesa Civil de Itajaí
          </a>{' '}
          ou{' '}
          <a href="https://monitoramento.defesacivil.sc.gov.br/" target="_blank" rel="noreferrer">
            Defesa Civil de SC
          </a>
          . Emergência: <strong>199</strong>.
        </p>
        <button type="button" className={estilos.botao} onClick={() => this.setState({ erro: null })}>
          Tentar mostrar de novo
        </button>
      </div>
    )
  }
}
