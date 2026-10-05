import { lazy, Suspense } from 'react'
import { Link } from 'react-router-dom'
import { useCidadesSeguidas } from '../dados/usarPreferencias'
import { useAoVivo } from '../dados/usarAoVivo'
import estilos from './TelaPerguntas.module.css'

/**
 * O chat do histórico numa página só dele (pedido do Jefferson, 04/10/2026).
 *
 * Ele morava só no fim da aba Histórico de cada cidade, e quem não sabia não o
 * achava. A tela inicial ganhou um botão que traz aqui — e esta página funciona
 * para qualquer pessoa: com Itajaí como cidade (a foz não tem aba Histórico), ou
 * sem cidade escolhida. O motor responde sobre qualquer cidade; o rio só escolhe
 * as sugestões de partida, e vem da cidade da pessoa quando há.
 *
 * O chat carrega à parte, como na aba Histórico: quem abriu o site para ver o
 * nível do rio não baixa os dados do chat.
 */
const ChatLocal = lazy(() => import('../chat-local/ChatLocal'))

export default function TelaPerguntas() {
  const { cidades } = useCidadesSeguidas()
  const rio = cidades[0]?.rio === 'mirim' ? 'itajai-mirim' : 'itajai-acu'
  // O nível e a chuva de agora, para "como está Blumenau?" (05/10/2026).
  const aoVivo = useAoVivo()
  return (
    <>
      <p className={estilos.voltar}>
        <Link to="/">← Início</Link>
      </p>
      <h1>Perguntas sobre as cheias</h1>
      <p className={estilos.intro}>
        Pergunte sobre enchentes que já aconteceram: a maior cheia de uma cidade, as cheias de um ano, quantas
        passaram de um nível, quanto tempo a água leva entre duas cidades ou quantas cheias chegaram à cota da sua
        rua. Cada resposta sai dos dados deste site, com a fonte.
      </p>
      <Suspense fallback={<p className={estilos.intro}>Carregando as perguntas sobre o histórico…</p>}>
        <ChatLocal rio={rio} aoVivo={aoVivo} />
      </Suspense>
    </>
  )
}
